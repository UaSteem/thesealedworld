"""Opt-in contracts against explicitly supplied disposable stores.

Set RUN_COMBAT_FINALIZATION_ADAPTER_TESTS=1, TEST_COMBAT_REDIS_URL (RedisJSON),
and TEST_COMBAT_POSTGRES_URL (local database named test_*). No app store URL is
read. The SQL fixture creates/drops only its unique schema; Redis uses one key.
"""

import asyncio
import copy
import importlib
import os
from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from codex_platform.redis_service import RedisService
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline
from sqlalchemy import Column, Integer, MetaData, String, Table, insert, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.backend.features.character.models import CharacterProgression, SkillProgress
from src.backend.features.character.services.combat_progression import checkpoint_combat_progression
from src.backend.features.combat.services.finalization_journal import CombatFinalizationJournal
from src.backend.features.expedition.models import CharacterExpedition
from src.backend.features.expedition.service import ExpeditionService
from src.backend.infrastructure.actor_state.managers.session import CharacterSessionManager
from src.backend.infrastructure.combat.models import CombatFinalization

pytestmark = [
    pytest.mark.integration,
    pytest.mark.external,
    pytest.mark.skipif(
        os.environ.get("RUN_COMBAT_FINALIZATION_ADAPTER_TESTS") != "1",
        reason="Requires explicitly selected disposable combat finalization stores",
    ),
]


@pytest.fixture
async def redis_adapter():
    url = os.environ.get("TEST_COMBAT_REDIS_URL")
    if not url:
        pytest.skip("TEST_COMBAT_REDIS_URL is unset")
    async with Redis.from_url(url, decode_responses=True) as raw:
        manager = CharacterSessionManager(RedisService(raw))
        char_id = uuid4().int % 1_000_000_000
        key = manager.build_key(char_id)
        await raw.json().set(key, "$", {"skills": {}, "progression": {"free_xp": 1}, "metrics": {}})
        try:
            yield manager, raw, char_id
        finally:
            await raw.delete(key)


@pytest.fixture
async def sql_adapter(monkeypatch):
    url = os.environ.get("TEST_COMBAT_POSTGRES_URL")
    if not url:
        pytest.skip("TEST_COMBAT_POSTGRES_URL is unset")
    parsed = make_url(url)
    if parsed.host not in {"localhost", "127.0.0.1", "::1"} or not (parsed.database or "").startswith("test_"):
        pytest.fail("Combat adapter tests require a local disposable test_* database")
    schema = "combat_test_" + uuid4().hex
    engine = create_async_engine(url, execution_options={"schema_translate_map": {None: schema}})
    metadata = MetaData()
    characters = Table("characters", metadata, Column("character_id", Integer, primary_key=True))
    for model in (CombatFinalization, CharacterExpedition, CharacterProgression, SkillProgress):
        table = model.__table__.to_metadata(metadata)
        if model is SkillProgress:
            table.c.progress_state.type = String(10)  # No shared PostgreSQL enum objects.
    async with engine.begin() as connection:
        await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        await connection.run_sync(metadata.create_all)
        await connection.execute(insert(characters).values(character_id=7))
    factory = async_sessionmaker(engine, expire_on_commit=False)

    @asynccontextmanager
    async def unit_of_work():
        async with factory() as session, session.begin():
            yield session

    for module in (
        "src.backend.features.combat.services.finalization_journal",
        "src.backend.features.character.services.combat_progression",
    ):
        monkeypatch.setattr(importlib.import_module(module), "get_session_context", unit_of_work)
    try:
        yield factory
    finally:
        async with engine.begin() as connection:
            await connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        await engine.dispose()


async def test_redis_concurrent_duplicates_and_ambiguous_exec(redis_adapter, monkeypatch):
    manager, raw, char_id = redis_adapter
    rewards = {"free_xp": 0.75, "skill_swords": 0.12}
    original_execute = Pipeline.execute
    crash = True

    async def uncertain_execute(pipe, *args, **kwargs):
        nonlocal crash
        result = await original_execute(pipe, *args, **kwargs)
        if crash:
            crash = False
            raise ConnectionError("lost EXEC response after reward commit")
        return result

    monkeypatch.setattr(Pipeline, "execute", uncertain_execute)
    with pytest.raises(ConnectionError):
        await manager.apply_skill_progress(char_id, rewards, combat_id="combat-1")
    await asyncio.gather(*(manager.apply_skill_progress(char_id, rewards, combat_id="combat-1") for _ in range(10)))
    document = (await raw.json().get(manager.build_key(char_id), "$"))[0]
    assert document["progression"]["free_xp"] == 1.75
    assert document["skills"]["skill_swords"]["xp"] == 0.12
    assert document["progression"]["combat_receipts"] == {"combat-1": True}
    assert document["sync_dirty"]["dirty"] is True
    assert document["sync_dirty"]["targets"]["skills"] is True


async def test_postgres_journal_concurrent_claim_rollback_and_recovery(sql_adapter):
    journal = CombatFinalizationJournal()
    facts = {"combat_id": "combat-1", "winner_team": "players", "participant_char_ids": [7], "actors": {}}
    await asyncio.gather(*(journal.freeze(facts) for _ in range(3)))
    seen = []

    async def effect(_facts):
        seen.append(1)
        await asyncio.sleep(0.01)

    await asyncio.gather(*(journal.run_step("combat-1", "vitals", effect) for _ in range(5)))
    assert seen == [1]

    async def failure(_facts):
        raise RuntimeError("crash before checkpoint")

    with pytest.raises(RuntimeError):
        await journal.run_step("combat-1", "progression", failure)
    assert await journal.pending() == [{"session_id": "combat-1", "winner": "players"}]
    assert (await CombatFinalizationJournal().load("combat-1"))["winner_team"] == "players"
    await journal.run_step("combat-1", "progression", effect)
    await journal.run_step("combat-1", "complete", effect)
    assert await journal.pending() == []
    assert await journal.pending_archives() == ["combat-1"]


async def test_expedition_reward_receipt_commits_together_and_survives_closed_run(sql_adapter):
    async with sql_adapter() as session:
        session.add(CharacterExpedition(run_id="run-1", character_id=7, status="active"))
        await session.commit()

    async def apply():
        async with sql_adapter() as session:
            return await ExpeditionService(session=session).apply_progress(7, {"free_xp": 2}, combat_id="combat-1")

    assert all(await asyncio.gather(*(apply() for _ in range(4))))
    async with sql_adapter() as session:
        run = await session.get(CharacterExpedition, "run-1")
        assert run.pending_progress_json["free_xp"] == 2
        assert "combat_progress:combat-1" in run.processed_events
        run.status = "synced"
        session.add(CharacterExpedition(run_id="run-2", character_id=7, status="active"))
        await session.commit()
    assert await apply() is True
    async with sql_adapter() as session:
        assert (await session.get(CharacterExpedition, "run-2")).pending_progress_json == {}


async def test_expedition_projection_failure_retries_committed_absolute_progress(sql_adapter):
    from unittest.mock import AsyncMock

    async with sql_adapter() as session:
        session.add(CharacterExpedition(run_id="run-1", character_id=7, status="active"))
        await session.commit()
    projection = AsyncMock()
    projection.set_pending_progress.side_effect = [ConnectionError("projection unavailable"), None]
    async with sql_adapter() as session:
        service = ExpeditionService(session=session, character_sessions=projection)
        with pytest.raises(ConnectionError):
            await service.apply_progress(7, {"free_xp": 2}, combat_id="combat-1", expedition_run_id="run-1")
    async with sql_adapter() as session:
        assert await ExpeditionService(session=session, character_sessions=projection).apply_progress(
            7, {"free_xp": 2}, combat_id="combat-1", expedition_run_id="run-1"
        )
        run = await session.get(CharacterExpedition, "run-1")
        assert run.pending_progress_json["free_xp"] == 2
    assert projection.set_pending_progress.await_count == 2


async def test_frozen_expedition_never_routes_unapplied_reward_to_new_run(sql_adapter):
    async with sql_adapter() as session:
        session.add(CharacterExpedition(run_id="run-1", character_id=7, status="synced"))
        session.add(CharacterExpedition(run_id="run-2", character_id=7, status="active"))
        await session.commit()
    async with sql_adapter() as session:
        with pytest.raises(RuntimeError, match="closed before progression"):
            await ExpeditionService(session=session).apply_progress(
                7, {"free_xp": 2}, combat_id="combat-1", expedition_run_id="run-1"
            )
        assert (await session.get(CharacterExpedition, "run-2")).pending_progress_json == {}


async def test_recovery_scans_past_first_page_and_excludes_retired_work(sql_adapter):
    from src.backend.features.combat.workers.tasks.finalization_recovery_task import combat_finalization_recovery_task

    journal = CombatFinalizationJournal()
    async with sql_adapter() as session:
        # Pre-journal rows are discoverable for manual handling but cannot be
        # replayed. They must not consume the SQL page before eligible work.
        for index in range(101):
            session.add(CombatFinalization(combat_id=f"legacy-{index:03d}", status="pending", metadata_={}))
        for kind, status, count in (
            ("blocked", "blocked_retired", 101),
            ("pending", "pending", 101),
            ("archive", "finalized", 101),
        ):
            for index in range(count):
                combat_id = f"{kind}-{index:03d}"
                session.add(
                    CombatFinalization(
                        combat_id=combat_id,
                        status=status,
                        winner_team="players",
                        mongo_status="pending",
                        metadata_={"finalization_work": {"payload": {"combat_id": combat_id}, "completed": []}},
                    )
                )
        await session.commit()

    class Queue:
        def __init__(self):
            self.jobs = []

        async def enqueue_job(self, name, payload):
            self.jobs.append((name, payload))

    queue = Queue()
    await combat_finalization_recovery_task({"redis": queue, "combat_finalization_journal": journal})
    finalizers = [payload["session_id"] for name, payload in queue.jobs if name == "victory_finalizer_task"]
    archives = [payload["combat_id"] for name, payload in queue.jobs if name == "combat_finalization_persist_task"]
    assert len(finalizers) == len(set(finalizers)) == 101
    assert "pending-100" in finalizers
    assert len(archives) == len(set(archives)) == 101
    assert "archive-100" in archives
    assert not any(combat_id.startswith("blocked") for combat_id in finalizers + archives)


async def test_safe_reward_and_receipt_checkpoint_survive_session_rehydration(sql_adapter, redis_adapter):
    manager, raw, char_id = redis_adapter
    # The SQL fixture owns character 7; move the Redis fixture's isolated payload
    # to an equally isolated manager namespace to avoid any application key.
    original_key = manager.build_key(char_id)
    key = original_key + ":checkpoint"
    manager.build_key = lambda _char_id: key
    await raw.json().set(key, "$", {"skills": {}, "progression": {"free_xp": 1}, "metrics": {}})
    try:
        await manager.apply_skill_progress(7, {"free_xp": 2, "skill_swords": 0.1}, combat_id="combat-1")
        await checkpoint_combat_progression(manager, 7, "combat-1")
        async with sql_adapter() as session:
            progression = await session.get(CharacterProgression, 7)
            skills = (await session.execute(select(SkillProgress))).scalars().all()
            rebuilt = {
                "skills": {row.skill_key: {"xp": row.total_xp} for row in skills},
                "progression": {"free_xp": progression.free_xp, **copy.deepcopy(progression.metadata_)},
            }
        await raw.delete(key)
        await raw.json().set(key, "$", rebuilt)
        await manager.apply_skill_progress(7, {"free_xp": 2, "skill_swords": 0.1}, combat_id="combat-1")
        assert (await raw.json().get(key, "$"))[0] == rebuilt
    finally:
        await raw.delete(key)
