"""Disposable RedisJSON contracts; opt in with RUN_REDISJSON_CONTRACT_TESTS=1."""

import asyncio
import json
import os
import subprocess
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import redis as sync_redis
from codex_platform.redis_service import RedisService
from redis.asyncio import Redis

from src.backend.features.combat.dto.action import CombatActionDTO, CombatMoveDTO, ExchangePayload
from src.backend.features.combat.dto.pipeline import InteractionResultDTO
from src.backend.features.combat.dto.session import SessionDataDTO
from src.backend.features.combat.integrations.session_integration import CombatSessionIntegration
from src.backend.features.combat.orchestrators.creation_orchestrator import CombatCreationOrchestrator
from src.backend.features.combat.runtime.support import CombatAnalyticsFactBuilder, CombatResultSupportTaskDTO
from src.backend.features.combat.services.lifecycle_service import CombatLifecycleService
from src.backend.infrastructure.combat.managers.session import CombatSessionManager

pytestmark = [
    pytest.mark.integration,
    pytest.mark.external,
    pytest.mark.skipif(
        os.environ.get("RUN_REDISJSON_CONTRACT_TESTS") != "1",
        reason="Set RUN_REDISJSON_CONTRACT_TESTS=1 for disposable Docker Redis Stack",
    ),
]


@pytest.fixture(scope="module")
def redisjson_url():
    name = f"tbmmorpg-redisjson-contract-{uuid4().hex}"
    try:
        subprocess.run(
            [
                "docker",
                "run",
                "--detach",
                "--name",
                name,
                "--publish",
                "127.0.0.1::6379",
                "--env",
                "REDIS_ARGS=--save '' --appendonly no",
                "redis/redis-stack-server:7.2.0-v14",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        endpoint = subprocess.run(
            ["docker", "port", name, "6379/tcp"],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        ).stdout.strip()
        url = f"redis://{endpoint}/0"
        with sync_redis.Redis.from_url(url, socket_connect_timeout=1, socket_timeout=1) as probe:
            for attempt in range(50):
                try:
                    probe.ping()
                    break
                except sync_redis.ConnectionError:
                    if attempt == 49:
                        raise
                    time.sleep(0.1)
            # Require RedisJSON itself, not just a server accepting PING.
            assert probe.execute_command("COMMAND", "INFO", "JSON.GET")
        yield url
    finally:
        subprocess.run(["docker", "rm", "--force", name], capture_output=True, timeout=20, check=False)


@pytest.fixture
async def adapter(redisjson_url):
    async with Redis.from_url(redisjson_url, decode_responses=True) as client:
        yield CombatSessionManager(RedisService(client)), client


def session_data():
    return SessionDataDTO(
        meta={
            "active": 1,
            "teams": '{"a":["1"],"b":["2"]}',
            "step_counter": 0,
            "battle_type": "arena",
            "location_id": "arena",
        },
        actors={
            actor: {"meta": {"hp": 10, "feints": {"hand": {}}}, "raw": {}, "statuses": {"effects": []}}
            for actor in ["1", "2"]
        },
        targets={"1": ["2"], "2": ["1"]},
    )


async def seed(adapter):
    manager, client = adapter
    sid = uuid4().hex
    await manager.create_session_batch(sid, session_data(), ttl=30)
    await client.rpush(manager.action_queue_key(sid), "action-one", "action-two")
    await manager.acquire_worker_lock(sid, "owner")
    return manager, client, sid


async def accept(manager, sid, **kwargs):
    options = dict(owner="owner", expected_revision=0, exchange_id="exchange-one", expected_actions=["action-one"])
    options.update(kwargs)
    return await manager.commit_battle_results(
        sid,
        {"1": {"state": {"hp": 7, "feints": {"hand": {}}}}},
        [{"global_turn": 1, "text": "hit"}],
        1,
        target_returns=[{"source_id": "1", "target_id": "2"}],
        meta_update={"step_counter": 1},
        analytics=[{"t": 1, "seq": 0, "damage": 3}],
        **options,
    )


async def test_duplicate_create_preserves_progress_and_conflict_rejects(adapter):
    manager, client, sid = await seed(adapter)
    await client.json().set(manager.actor_key(sid, "1"), "$.meta.hp", 4)
    await manager.create_session_batch(sid, session_data(), ttl=30)
    assert (await manager.get_actor(sid, "1"))["meta"]["hp"] == 4
    assert await manager.load_actions_batch(sid, 10) == ["action-one", "action-two"]
    conflict = session_data()
    conflict.actors["1"]["meta"]["hp"] = 100
    with pytest.raises(RuntimeError, match="conflict"):
        await manager.create_session_batch(sid, conflict, ttl=30)


async def test_commit_failure_on_late_wrongtype_changes_nothing_and_retries(adapter):
    manager, client, sid = await seed(adapter)
    await client.set(manager.analytics_key(sid), "wrong-type")
    before = await client.dump(manager.actor_key(sid, "1"))
    with pytest.raises(RuntimeError, match="staging"):
        await accept(manager, sid)
    assert await client.dump(manager.actor_key(sid, "1")) == before
    assert await manager.load_actions_batch(sid, 10) == ["action-one", "action-two"]
    assert await manager.get_logs_by_turn(sid) == {}
    assert (await manager.get_meta(sid))["step_counter"] == "0"
    await client.delete(manager.analytics_key(sid))
    assert await accept(manager, sid) is True
    assert (await manager.get_actor(sid, "1"))["meta"]["hp"] == 7
    assert await manager.load_actions_batch(sid, 10) == ["action-two"]
    assert (await manager.get_meta(sid))["revision"] == "1"


async def test_atomic_owner_revision_replay_and_queue_prefix(adapter):
    manager, client, sid = await seed(adapter)
    await client.set(manager.busy_lock_key(sid), "successor", ex=60)
    with pytest.raises(RuntimeError, match="owner"):
        await accept(manager, sid)
    await client.set(manager.busy_lock_key(sid), "owner", ex=60)
    await client.lpush(manager.action_queue_key(sid), "unexpected-prefix")
    with pytest.raises(RuntimeError, match="queue"):
        await accept(manager, sid)
    await client.lpop(manager.action_queue_key(sid))
    assert await accept(manager, sid) is True
    assert await accept(manager, sid) is False
    assert len(await manager.get_logs(sid)) == 1
    assert await manager.load_actions_batch(sid, 10) == ["action-two"]


async def test_concurrent_writers_accept_exactly_once(adapter):
    manager, _client, sid = await seed(adapter)
    outcomes = await asyncio.gather(accept(manager, sid), accept(manager, sid), return_exceptions=True)
    assert sorted(outcomes) == [False, True]
    assert len(await manager.get_logs(sid)) == 1


async def test_post_snapshot_actor_change_rejects_stale_commit(adapter):
    manager, client, sid = await seed(adapter)
    source = await client.execute_command("JSON.GET", manager.actor_key(sid, "1"), "$")
    await client.json().set(manager.actor_key(sid, "1"), "$.meta.feints.hand", {"new": {"en": 1}})
    with pytest.raises(RuntimeError, match="snapshot"):
        await accept(manager, sid, expected_actors={"1": source})
    assert (await manager.get_actor(sid, "1"))["meta"]["feints"]["hand"] == {"new": {"en": 1}}


async def test_concurrent_same_and_conflicting_creation(adapter):
    manager, _client = adapter
    sid = uuid4().hex
    assert sorted(
        await asyncio.gather(
            manager.create_session_batch(sid, session_data()), manager.create_session_batch(sid, session_data())
        )
    ) == [False, True]
    sid = uuid4().hex
    different = session_data()
    different.actors["2"]["meta"]["hp"] = 20
    results = await asyncio.gather(
        manager.create_session_batch(sid, session_data()),
        manager.create_session_batch(sid, different),
        return_exceptions=True,
    )
    assert sum(result is True for result in results) == 1
    assert sum(isinstance(result, RuntimeError) for result in results) == 1


async def test_creation_staging_failure_can_retry_and_legacy_partial_fails_closed(adapter):
    manager, client = adapter
    sid = uuid4().hex
    invalid = session_data()
    invalid.actors["2"]["meta"]["hp"] = float("nan")
    with pytest.raises(RuntimeError, match="staging"):
        await manager.create_session_batch(sid, invalid)
    assert await client.keys(f"combat:rbc:{sid}:*") == []
    assert await manager.create_session_batch(sid, session_data()) is True
    orphan_sid = uuid4().hex
    await client.json().set(manager.actor_key(orphan_sid, "1"), "$", {"meta": {"hp": 4}})
    with pytest.raises(RuntimeError, match="incomplete"):
        await manager.create_session_batch(orphan_sid, session_data())
    assert await manager.get_meta(orphan_sid) is None
    assert (await manager.get_actor(orphan_sid, "1"))["meta"]["hp"] == 4


async def test_late_target_error_keeps_every_live_value_and_no_stages(adapter):
    manager, client, sid = await seed(adapter)
    await client.json().set(manager.targets_key(sid), '$["1"]', 3)
    keys = await client.keys(f"combat:rbc:{sid}:*")
    before = {key: await client.dump(key) for key in keys}
    with pytest.raises(RuntimeError, match="staging"):
        await accept(manager, sid)
    assert {key: await client.dump(key) for key in keys} == before
    assert set(await client.keys(f"combat:rbc:{sid}:*")) == set(keys)
    await client.json().set(manager.targets_key(sid), '$["1"]', [])
    assert await accept(manager, sid)


async def test_expired_lease_successor_and_revision_fence(adapter):
    manager, client, sid = await seed(adapter)
    await client.pexpire(manager.busy_lock_key(sid), 30)
    while await client.exists(manager.busy_lock_key(sid)):
        await asyncio.sleep(0.01)
    assert await manager.acquire_worker_lock(sid, "successor")
    with pytest.raises(RuntimeError, match="owner"):
        await accept(manager, sid)
    await client.hset(manager.meta_key(sid), "revision", 1)
    with pytest.raises(RuntimeError, match="revision"):
        await accept(manager, sid, owner="successor")
    assert await manager.load_actions_batch(sid, 10) == ["action-one", "action-two"]


async def test_replay_after_reacquire_and_after_later_exchange(adapter):
    manager, client, sid = await seed(adapter)
    assert await accept(manager, sid)
    await client.set(manager.busy_lock_key(sid), "successor", ex=60)
    assert await accept(manager, sid, owner="successor") is False
    assert await accept(
        manager,
        sid,
        owner="successor",
        expected_revision=1,
        exchange_id="exchange-two",
        expected_actions=["action-two"],
    )
    with pytest.raises(RuntimeError, match="revision"):
        await accept(manager, sid, owner="successor")
    assert len(await manager.get_logs(sid)) == 2
    assert await manager.load_actions_batch(sid, 10) == []


async def test_snapshot_read_missing_actor_and_finalization_guard(adapter):
    manager, client, sid = await seed(adapter)
    integration = CombatSessionIntegration(manager)
    ctx = await integration.load_battle_context(sid)
    assert ctx and set(ctx.storage_actor_snapshots) == {"1", "2"}
    await manager.set_winner(sid, "a")
    with pytest.raises(RuntimeError, match="inactive"):
        await integration.commit_session(
            ctx, ["action-one"], owner="owner", exchange_id="one", expected_actions=["action-one"]
        )
    await client.hset(manager.meta_key(sid), "active", 1)
    await client.delete(manager.actor_key(sid, "2"))
    with pytest.raises(RuntimeError, match="snapshot"):
        await integration.load_battle_context(sid)
    with pytest.raises(RuntimeError, match="snapshot"):
        await integration.commit_session(
            ctx, ["action-one"], owner="owner", exchange_id="one", expected_actions=["action-one"]
        )


async def test_worker_consumes_exact_mixed_raw_prefix_and_preserves_tail(adapter):
    from src.backend.features.combat.workers.tasks.executor_task import execute_batch_task

    manager, client, sid = await seed(adapter)
    await manager.release_worker_lock_safe(sid, "owner")
    await client.delete(manager.action_queue_key(sid))
    action = CombatActionDTO(
        action_type="exchange",
        move=CombatMoveDTO(move_id="m1", char_id="1", strategy="exchange", payload=ExchangePayload(target_id="2")),
    ).model_dump_json()
    await client.rpush(manager.action_queue_key(sid), "malformed", action, "tail")

    class Executor:
        async def process_batch(self, ctx, actions):
            assert len(actions) == 1
            ctx.actors["1"].meta.hp = 6
            ctx.pending_logs.append({"global_turn": 1, "effects": [], "nested": {"empty": []}})
            # A producer can append after the worker reads its action prefix.
            await client.rpush(manager.action_queue_key(sid), "concurrent-tail")
            return [item.move.move_id for item in actions]

    await execute_batch_task(
        {"combat_executor": Executor(), "combat_data_service": CombatSessionIntegration(manager), "redis": AsyncMock()},
        {"session_id": sid, "batch_size": 2},
    )
    assert await manager.load_actions_batch(sid, 10) == ["tail", "concurrent-tail"]
    assert (await manager.get_actor(sid, "1"))["meta"]["hp"] == 6
    assert json.loads((await manager.get_logs(sid))[0])["nested"]["empty"] == []


async def test_log_appender_cannot_overwrite_an_accepted_exchange(adapter, monkeypatch):
    manager, client, sid = await seed(adapter)
    original_hset = client.hset
    accepted = False

    async def hset_with_acceptance(key, *args, **kwargs):
        nonlocal accepted
        if key == manager.log_key(sid) and not accepted:
            accepted = True
            await accept(manager, sid)
        return await original_hset(key, *args, **kwargs)

    # Reproduce acceptance between the old Python log read and its hash write.
    monkeypatch.setattr(client, "hset", hset_with_acceptance)
    await manager.append_log(sid, {"global_turn": 1, "text": "external"})
    if not accepted:
        await accept(manager, sid)
    assert {json.loads(line)["text"] for line in await manager.get_logs(sid)} == {"external", "hit"}


async def test_creation_retry_uses_persisted_actors_and_retries_post_create_delivery(adapter):
    manager, client = adapter
    sid = uuid4().hex
    request = {"combat_id": sid, "participants": {"a": [1], "b": [2]}, "battle_type": "arena"}
    lifecycle = CombatLifecycleService(store=CombatSessionIntegration(manager))
    fingerprint = lifecycle.creation_fingerprint("arena", request["participants"], request)
    data = session_data()
    data.meta["creation_fingerprint"] = fingerprint
    await manager.create_session_batch(sid, data, analytics=[{"k": "profile", "name": "original"}])
    await client.json().set(manager.actor_key(sid, "1"), "$.meta.hp", 4)
    integrator = SimpleNamespace(publish_session_ready=AsyncMock())
    loot = SimpleNamespace(enqueue=AsyncMock())
    orchestrator = CombatCreationOrchestrator(lifecycle=lifecycle, integrator=integrator, loot_preorder=loot)
    result = await orchestrator.create_from_request({**request, "timestamp": 999, "correlation_id": "retry"})
    assert result["status"] == "ready"
    assert loot.enqueue.await_args.kwargs["actors"]["1"]["meta"]["hp"] == 4
    integrator.publish_session_ready.assert_awaited_once()
    assert (await manager.get_analytics(sid))["_profile"]["name"] == "original"
    # Source commitment access is absent from this integrator: retries cannot
    # depend on still-live snapshots or trigger regeneration.
    await client.delete(manager.moves_key(sid, "2"))
    with pytest.raises(RuntimeError, match="incomplete"):
        await orchestrator.create_from_request(request)


async def test_direct_creation_target_conflict_and_incomplete_duplicate(adapter):
    manager, client, sid = await seed(adapter)
    altered = session_data()
    altered.targets["1"] = []
    with pytest.raises(RuntimeError, match="conflict"):
        await manager.create_session_batch(sid, altered)
    await client.delete(manager.actor_key(sid, "2"))
    with pytest.raises(RuntimeError, match="incomplete"):
        await manager.create_session_batch(sid, session_data())


async def test_legacy_active_session_commits_without_reset(adapter):
    manager, client, sid = await seed(adapter)
    await client.hdel(manager.meta_key(sid), "revision", "creation_complete", "creation_fingerprint")
    assert await accept(manager, sid)
    assert (await manager.get_meta(sid))["revision"] == "1"


async def test_dead_targets_and_empty_arrays_preserve_json_shape(adapter):
    manager, _client, sid = await seed(adapter)
    assert await accept(manager, sid, dead_actor_ids={"2"}, dead_actors='["2"]')
    # The executor filters dead returns. Exercise pruning separately here by
    # checking the dead actor queue and unchanged actor nested empty values.
    assert (await manager.get_targets(sid))["2"] == []
    assert (await manager.get_actor(sid, "1"))["statuses"]["effects"] == []


async def test_runtime_analytics_participate_in_acceptance_and_failed_retry(adapter):
    manager, client, sid = await seed(adapter)
    integration = CombatSessionIntegration(manager)
    ctx = await integration.load_battle_context(sid)
    assert ctx is not None
    action = CombatActionDTO(
        action_type="exchange",
        move=CombatMoveDTO(move_id="m1", char_id="1", strategy="exchange", payload=ExchangePayload(target_id="2")),
    )
    payload = CombatResultSupportTaskDTO.from_context(
        ctx=ctx,
        result=InteractionResultDTO(source_id="1", target_id="2", damage_final=3),
        action=action,
        wave=1,
        seq=0,
        timestamp=1.0,
    )
    expected_fact = CombatAnalyticsFactBuilder.build_result_fact_from_support_payload(payload)
    ctx.pending_result_support_tasks.append(payload.model_dump(mode="json"))
    ctx.pending_logs.append({"global_turn": 1, "text": "hit"})
    ctx.actors["1"].meta.hp = 7
    ctx.meta.step_counter = 1
    await client.set(manager.analytics_key(sid), "wrong-type")
    keys = await client.keys(f"combat:rbc:{sid}:*")
    before = {key: await client.dump(key) for key in keys}
    with pytest.raises(RuntimeError, match="staging"):
        await integration.commit_session(
            ctx,
            ["m1"],
            owner="owner",
            exchange_id="runtime-one",
            expected_actions=["action-one"],
        )
    assert {key: await client.dump(key) for key in keys} == before
    await client.delete(manager.analytics_key(sid))
    assert await integration.commit_session(
        ctx,
        ["m1"],
        owner="owner",
        exchange_id="runtime-one",
        expected_actions=["action-one"],
    )
    assert (await manager.get_analytics(sid))["1:0"] == expected_fact
    assert await manager.load_actions_batch(sid, 10) == ["action-two"]
    # Deferred support replay writes the exact same hash field and fact.
    await integration.append_analytics(sid, expected_fact)
    assert await manager.get_analytics(sid) == {"1:0": expected_fact}


async def test_hotjoin_after_loaded_snapshot_preserves_current_session(adapter):
    manager, client, sid = await seed(adapter)
    integration = CombatSessionIntegration(manager)
    ctx = await integration.load_battle_context(sid)
    assert ctx is not None
    await manager.universal_hot_join(sid, "3", "a", {"meta": {"hp": 10}}, is_ai=True)
    keys = await client.keys(f"combat:rbc:{sid}:*")
    joined = {key: await client.dump(key) for key in keys}
    with pytest.raises(RuntimeError, match="snapshot"):
        await integration.commit_session(
            ctx,
            ["m1"],
            owner="owner",
            exchange_id="before-hotjoin",
            expected_actions=["action-one"],
        )
    assert {key: await client.dump(key) for key in keys} == joined
