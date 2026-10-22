from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import time
from importlib import import_module
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.backend.core.database import model_imports as model_imports
from src.backend.features.inventory.repositories import items as inventory_repository
from src.backend.features.inventory.repositories.items import InventoryItemRepository
from src.backend.features.items.models import ItemGeneratedTemplate, ItemInstance, ItemPlacement
from src.backend.infrastructure.inventory.models import DurabilityApplication


@pytest.fixture(scope="module")
def durability_postgres_url():
    """Own one disposable database; never use configured application databases."""
    if os.environ.get("RUN_DURABILITY_POSTGRES_TESTS") != "1":
        pytest.skip("Set RUN_DURABILITY_POSTGRES_TESTS=1 to run disposable PostgreSQL retry tests")
    if shutil.which("docker") is None:
        pytest.skip("Docker is required for the isolated PostgreSQL durability contract")
    name = f"durability-{uuid4().hex}"

    def docker(*args: str) -> str:
        return subprocess.check_output(["docker", *args], text=True, timeout=60).strip()

    try:
        docker(
            "run",
            "--detach",
            "--rm",
            "--name",
            name,
            "--publish",
            "127.0.0.1::5432",
            "--env",
            "POSTGRES_PASSWORD=retry-test",
            "--env",
            "POSTGRES_DB=retry_test",
            "postgres:16-alpine",
        )
        for _ in range(60):
            ready = subprocess.run(
                # The image's initialization server accepts Unix sockets before
                # restarting; wait for the final TCP listener used by asyncpg.
                ["docker", "exec", name, "pg_isready", "-h", "127.0.0.1", "-U", "postgres", "-d", "retry_test"],
                capture_output=True,
                timeout=10,
            )
            if ready.returncode == 0:
                break
            time.sleep(0.5)
        else:
            pytest.fail("Disposable PostgreSQL did not become ready")
        port = docker("port", name, "5432/tcp").rsplit(":", 1)[1]
        yield f"postgresql+asyncpg://postgres:retry-test@127.0.0.1:{port}/retry_test"  # pragma: allowlist secret
    finally:
        subprocess.run(["docker", "rm", "--force", name], capture_output=True, timeout=60)


@pytest.fixture
async def durability_db(durability_postgres_url):
    engine = create_async_engine(durability_postgres_url)
    try:
        async with engine.begin() as connection:
            for model in (ItemGeneratedTemplate, ItemInstance, ItemPlacement, DurabilityApplication):
                await connection.run_sync(model.__table__.create, checkfirst=True)
        sessions = async_sessionmaker(engine, expire_on_commit=False)
        item_id = str(uuid4())
        async with sessions.begin() as session:
            session.add(
                ItemInstance(
                    id=item_id,
                    base_id="sword",
                    item_type="weapon",
                    rarity="common",
                    rarity_tier=1,
                    name="Sword",
                    description="",
                    mechanics={"durability_current": 10, "durability_max": 12, "power": 42},
                )
            )
            await session.flush()
            session.add(
                ItemPlacement(
                    item_id=item_id, holder_type="character", holder_id="7", storage_type="equipped", slot="main_hand"
                )
            )
        yield sessions, item_id
    finally:
        await engine.dispose()


def operation(item_id, key=None, amount=0.1):
    return {
        "char_id": 7,
        "idempotency_key": key or str(uuid4()),
        "payload": {
            "amount": amount,
            "scope": "equipped",
            "reason": "combat_completed",
            "source": "combat_finalization",
            "combat_id": "c",
            "metadata": {},
        },
        "item_ids": [item_id],
    }


@pytest.mark.external
@pytest.mark.integration
@pytest.mark.parametrize("same_key", [True, False])
async def test_concurrent_same_and_distinct_events(durability_db, same_key):
    sessions, item_id = durability_db
    first = operation(item_id)
    second = first if same_key else operation(item_id)

    async def run(args):
        async with sessions() as session:
            return await InventoryItemRepository(session).apply_durability_damage(**args)

    results = await asyncio.gather(run(first), run(second))
    async with sessions() as session:
        item = await session.get(ItemInstance, item_id)
        assert item.mechanics["durability_current"] == (9.9 if same_key else 9.8)
        assert item.mechanics["power"] == 42
        if same_key:
            assert sorted(result["duplicate"] for result in results) == [False, True]


@pytest.mark.external
@pytest.mark.integration
async def test_failed_commit_rolls_back_receipt_and_damage(durability_db, monkeypatch):
    sessions, item_id = durability_db
    args = operation(item_id)
    async with sessions() as session:
        real_commit = session.commit
        monkeypatch.setattr(session, "commit", AsyncMock(side_effect=RuntimeError("commit failed")))
        with pytest.raises(RuntimeError, match="commit failed"):
            await InventoryItemRepository(session).apply_durability_damage(**args)
        monkeypatch.setattr(session, "commit", real_commit)
    async with sessions() as session:
        item = await session.get(ItemInstance, item_id)
        assert item.mechanics["durability_current"] == 10
        assert (
            await session.scalar(
                select(func.count())
                .select_from(DurabilityApplication)
                .where(DurabilityApplication.idempotency_key == args["idempotency_key"])
            )
            == 0
        )
        result = await InventoryItemRepository(session).apply_durability_damage(**args)
        assert result["changed"][0]["after"] == 9.9


@pytest.mark.external
@pytest.mark.integration
async def test_no_items_receipt_conflict_and_latest_projection_read(durability_db):
    sessions, item_id = durability_db
    args = operation(item_id)
    async with sessions() as session:
        repository = InventoryItemRepository(session)
        empty = {**args, "item_ids": []}
        assert (await repository.apply_durability_damage(**empty))["changed"] == []
        assert (await repository.apply_durability_damage(**args))["duplicate"]
        with pytest.raises(ValueError, match="conflict"):
            await repository.apply_durability_damage(**{**args, "payload": {**args["payload"], "amount": 0}})
        await repository.list_character_items(7)  # Populate this session's identity map.
        async with sessions() as other:
            await InventoryItemRepository(other).apply_durability_damage(**operation(item_id))
        rows = await repository.list_character_items(7)
        item = next(instance for instance, _ in rows if instance.id == item_id)
        assert item.mechanics["durability_current"] == 9.9


@pytest.mark.external
@pytest.mark.integration
async def test_receipt_and_effect_survive_connection_loss_after_commit(durability_db, monkeypatch):
    sessions, item_id = durability_db
    args = operation(item_id)
    async with sessions() as session:
        commit = session.commit

        async def ambiguous_commit():
            await commit()
            raise RuntimeError("connection lost after commit")

        monkeypatch.setattr(session, "commit", ambiguous_commit)
        with pytest.raises(RuntimeError, match="connection lost"):
            await InventoryItemRepository(session).apply_durability_damage(**args)
    async with sessions() as session:
        assert (await InventoryItemRepository(session).apply_durability_damage(**args))["duplicate"]
        assert (await session.get(ItemInstance, item_id)).mechanics["durability_current"] == 9.9


@pytest.mark.external
@pytest.mark.integration
async def test_migration_handles_baseline_created_table_and_recreation(durability_postgres_url, monkeypatch):
    migration = import_module("src.backend.alembic.versions.0002_inventory_durability")
    engine = create_async_engine(durability_postgres_url)
    try:
        async with engine.begin() as connection:

            def run(sync_connection):
                monkeypatch.setattr(migration.op, "get_bind", lambda: sync_connection)
                migration.upgrade()
                migration.upgrade()
                migration.downgrade()
                migration.upgrade()

            await connection.run_sync(run)
    finally:
        await engine.dispose()


@pytest.mark.external
@pytest.mark.integration
@pytest.mark.parametrize(
    ("mechanics", "amount", "expected"),
    [
        ({"durability_max": 12, "power": 42}, 0.1, 11.9),
        ({"durability_current": 0.03, "power": 42}, 0.1, 0),
        ({"durability_current": 10, "power": 42}, 0.123456, 9.8765),
    ],
)
async def test_sql_formula_preserves_other_mechanics(durability_db, mechanics, amount, expected):
    sessions, item_id = durability_db
    async with sessions.begin() as session:
        item = await session.get(ItemInstance, item_id)
        item.mechanics = mechanics
    async with sessions() as session:
        result = await InventoryItemRepository(session).apply_durability_damage(**operation(item_id, amount=amount))
        assert result["changed"][0]["after"] == expected
    async with sessions() as session:
        item = await session.get(ItemInstance, item_id)
        assert item.mechanics["durability_current"] == expected
        assert item.mechanics["power"] == 42


@pytest.mark.external
@pytest.mark.integration
async def test_projection_fence_blocks_writer_and_rereads_latest_sql(durability_db, monkeypatch):
    sessions, item_id = durability_db
    async with sessions() as publishing_session, sessions() as writing_session, sessions() as observing_session:
        publisher = InventoryItemRepository(publishing_session)
        writer = InventoryItemRepository(writing_session)
        await publisher.apply_durability_damage(**operation(item_id))
        # Retain an old identity-map instance so the next fenced reread must refresh it.
        old_rows = await publisher.list_character_items(7)
        old_item = next(item for item, _ in old_rows if item.id == item_id)
        assert old_item.mechanics["durability_current"] == 9.9
        writer_pid = await writing_session.scalar(select(func.pg_backend_pid()))
        attempted = asyncio.Event()
        lock_writer = writer._lock_durability

        async def tracked_lock(char_id):
            attempted.set()
            await lock_writer(char_id)

        monkeypatch.setattr(writer, "_lock_durability", tracked_lock)
        async with publisher.durability_projection(7):
            task = asyncio.create_task(writer.apply_durability_damage(**operation(item_id)))
            try:
                await asyncio.wait_for(attempted.wait(), timeout=2)
                # Observe actual PostgreSQL lock contention, never infer blocking from timing.
                async with asyncio.timeout(2):
                    while not await observing_session.scalar(
                        text(
                            "SELECT EXISTS(SELECT 1 FROM pg_locks WHERE pid=:pid AND locktype='advisory' AND NOT granted)"
                        ),
                        {"pid": writer_pid},
                    ):
                        pass
                assert not task.done()
                rows = await publisher.list_character_items(7)
                assert next(item for item, _ in rows if item.id == item_id).mechanics["durability_current"] == 9.9
            except BaseException:
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
                raise
        await asyncio.wait_for(task, timeout=2)
        async with publisher.durability_projection(7):
            rows = await publisher.list_character_items(7)
            assert next(item for item, _ in rows if item.id == item_id).mechanics["durability_current"] == 9.8


@pytest.mark.external
@pytest.mark.integration
@pytest.mark.parametrize("failure", ["exception", "cancellation", "timeout"])
async def test_projection_failure_releases_lock_without_undoing_damage(durability_db, monkeypatch, failure):
    sessions, item_id = durability_db
    async with sessions() as session, sessions() as retry_session:
        repository = InventoryItemRepository(session)
        await repository.apply_durability_damage(**operation(item_id))
        entered = asyncio.Event()
        never = asyncio.Event()
        if failure == "timeout":
            monkeypatch.setattr(inventory_repository, "_DURABILITY_PROJECTION_TIMEOUT_SECONDS", 0.01)

        async def publish():
            async with repository.durability_projection(7):
                entered.set()
                if failure == "exception":
                    raise RuntimeError("projection failed")
                await never.wait()

        task = asyncio.create_task(publish())
        await asyncio.wait_for(entered.wait(), timeout=2)
        if failure == "cancellation":
            task.cancel()
        expected = {"exception": RuntimeError, "cancellation": asyncio.CancelledError, "timeout": TimeoutError}[failure]
        with pytest.raises(expected):
            await task
        # Another connection must acquire immediately after failed projection cleanup.
        async with asyncio.timeout(2):
            async with InventoryItemRepository(retry_session).durability_projection(7):
                item = await retry_session.get(ItemInstance, item_id)
                assert item.mechanics["durability_current"] == 9.9


@pytest.mark.external
@pytest.mark.integration
async def test_lock_wait_timeout_is_failure_and_releases_transaction(durability_db, monkeypatch):
    sessions, item_id = durability_db
    async with sessions() as owner, sessions() as waiting:
        publisher = InventoryItemRepository(owner)
        writer = InventoryItemRepository(waiting)
        args = operation(item_id)
        async with publisher.durability_projection(7):
            with monkeypatch.context() as timeout_patch:
                timeout_patch.setattr(inventory_repository, "_DURABILITY_LOCK_TIMEOUT_SECONDS", 0.01)
                with pytest.raises(TimeoutError):
                    await writer.apply_durability_damage(**args)
        # Failed lock acquisition was rolled back; the same session remains retryable.
        result = await writer.apply_durability_damage(**args)
        assert not result["duplicate"]
        assert result["changed"][0]["after"] == 9.9
