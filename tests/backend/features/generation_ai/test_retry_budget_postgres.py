from __future__ import annotations

import os
import shutil
import subprocess
import time
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import uuid4

import pytest
from sqlalchemy import Table
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.backend.features.generation_ai.models import AIGenerationTask
from src.backend.features.generation_ai.registry import AIGenerationTaskRegistry
from src.backend.features.generation_ai.repositories import AIGenerationTaskRepository
from src.backend.features.generation_ai.services import GenerationAIService


@pytest.fixture(scope="module")
def retry_postgres_url():
    """Own one disposable database; never use configured application databases."""
    if os.environ.get("RUN_GENERATION_RETRY_POSTGRES_TESTS") != "1":
        pytest.skip("Set RUN_GENERATION_RETRY_POSTGRES_TESTS=1 to run disposable PostgreSQL retry tests")
    if shutil.which("docker") is None:
        pytest.skip("Docker is required for the isolated PostgreSQL retry contract")
    name = f"generation-retry-{uuid4().hex}"

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
                ["docker", "exec", name, "pg_isready", "-U", "postgres", "-d", "retry_test"],
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


class NoMongoPayloadStore:
    async def fetch_task_document(self, task_id: str) -> None:
        return None

    async def record_error(self, *, task: AIGenerationTask, error: dict[str, Any]) -> str:
        return f"test-{task.id}"


@pytest.mark.external
@pytest.mark.integration
@pytest.mark.parametrize("claim_method", ["claim_by_id", "claim_next"])
@pytest.mark.parametrize(
    ("output_kind", "configured_limit", "message", "effective_limit"),
    [
        ("json", 3, "JSON generation failed schema validation", 8),
        ("json", 12, "JSON generation failed schema validation", 12),
        ("json", 3, "provider temporarily unavailable", 3),
        ("text", 3, "JSON generation failed schema validation", 3),
        ("image", 3, "JSON generation failed schema validation", 3),
    ],
)
async def test_retry_budget_remains_claimable_until_terminal_failure(
    retry_postgres_url,
    claim_method,
    output_kind,
    configured_limit,
    message,
    effective_limit,
):
    engine = create_async_engine(retry_postgres_url)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    task_id = str(uuid4())
    now = datetime.now(UTC) + timedelta(days=1)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(cast("Table", AIGenerationTask.__table__).create, checkfirst=True)
        async with sessions.begin() as session:
            session.add(
                AIGenerationTask(
                    id=task_id,
                    batch_id=str(uuid4()),
                    identity_key=task_id,
                    task_type="test.retry",
                    entity_type="test",
                    entity_id=task_id,
                    output_kind=output_kind,
                    status="pending",
                    attempts=0,
                    max_attempts=configured_limit,
                )
            )

        for attempt in range(1, effective_limit + 1):
            # Every attempt uses a fresh transaction/session, so ORM identity-map state
            # cannot hide a retry budget that was never persisted.
            async with sessions.begin() as session:
                repository = AIGenerationTaskRepository(session, payload_store=cast("Any", NoMongoPayloadStore()))
                if claim_method == "claim_by_id":
                    task = await repository.claim_by_id(task_id, now=now)
                else:
                    task = await repository.claim_next(now=now)
                assert task is not None, f"attempt {attempt} was stranded by the persisted budget"
                assert task.id == task_id
                assert task.attempts == attempt
                service = GenerationAIService(
                    repository=repository,
                    registry=AIGenerationTaskRegistry(),
                    auto_schedule=False,
                )
                # After a schema extension, generic errors must retain the saved budget.
                error = RuntimeError("provider temporarily unavailable" if attempt == 2 else message)
                await service._mark_retry_or_failed(task_id, error)

            async with sessions.begin() as session:
                saved = await session.get(AIGenerationTask, task_id)
                assert saved is not None
                assert saved.max_attempts == effective_limit
                assert saved.attempts == attempt
                if attempt < effective_limit:
                    assert saved.status == "cooldown"
                    assert saved.not_before is not None
                    assert saved.completed_at is None
                    repository = AIGenerationTaskRepository(session, payload_store=cast("Any", NoMongoPayloadStore()))
                    assert await repository.claim_by_id(task_id, now=saved.not_before - timedelta(seconds=1)) is None
                    assert await repository.claim_next(now=saved.not_before - timedelta(seconds=1)) is None
                else:
                    assert saved.status == "failed"
                    assert saved.completed_at is not None

        async with sessions.begin() as session:
            repository = AIGenerationTaskRepository(session, payload_store=cast("Any", NoMongoPayloadStore()))
            assert await repository.claim_by_id(task_id, now=now) is None
            assert await repository.claim_next(now=now) is None
    finally:
        await engine.dispose()


@pytest.mark.external
@pytest.mark.integration
async def test_explicit_raised_enqueue_budget_recovers_preexisting_stranded_cooldown(retry_postgres_url):
    engine = create_async_engine(retry_postgres_url)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    task_id = str(uuid4())
    now = datetime.now(UTC)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(cast("Table", AIGenerationTask.__table__).create, checkfirst=True)
        async with sessions.begin() as session:
            session.add(
                AIGenerationTask(
                    id=task_id,
                    batch_id=str(uuid4()),
                    identity_key=task_id,
                    task_type="test.retry",
                    entity_type="test",
                    entity_id=task_id,
                    output_kind="json",
                    status="cooldown",
                    attempts=3,
                    max_attempts=3,
                    not_before=now - timedelta(seconds=1),
                )
            )
        async with sessions.begin() as session:
            repository = AIGenerationTaskRepository(session, payload_store=cast("Any", NoMongoPayloadStore()))
            assert await repository.claim_by_id(task_id, now=now) is None
            assert await repository.claim_next(now=now) is None
            task = await repository.get(task_id)
            assert task is not None
            await repository.prepare_existing_for_enqueue(task, max_attempts=8)
        async with sessions.begin() as session:
            repository = AIGenerationTaskRepository(session, payload_store=cast("Any", NoMongoPayloadStore()))
            claimed = await repository.claim_by_id(task_id, now=now)
            assert claimed is not None
            assert claimed.max_attempts == 8
            assert claimed.attempts == 4
            assert claimed.status == "running"
    finally:
        await engine.dispose()


@pytest.mark.external
@pytest.mark.integration
@pytest.mark.parametrize(
    "task_type,kind,status,retired",
    [
        ("world.zone_lore", "json", "pending", True),
        ("news.cover_image", "image", "cooldown", True),
        ("items.text", "image", "pending", True),
        ("items.text", "json", "cooldown", False),
        ("world.zone_lore", "json", "done", False),
        ("world.zone_lore", "json", "failed", False),
        ("world.zone_lore", "json", "cancelled", False),
        ("world.zone_lore", "json", "running", False),
    ],
)
async def test_retirement_ignores_retry_and_time_gates_but_preserves_history(
    retry_postgres_url, task_type, kind, status, retired
):
    engine = create_async_engine(retry_postgres_url)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    task_id = str(uuid4())
    try:
        async with engine.begin() as connection:
            await connection.run_sync(cast("Table", AIGenerationTask.__table__).create, checkfirst=True)
        async with sessions.begin() as session:
            session.add(
                AIGenerationTask(
                    id=task_id,
                    batch_id=str(uuid4()),
                    identity_key=task_id,
                    task_type=task_type,
                    entity_type="test",
                    entity_id=task_id,
                    output_kind=kind,
                    status=status,
                    attempts=3,
                    max_attempts=3,
                    not_before=datetime.now(UTC) + timedelta(days=1),
                )
            )
        async with sessions.begin() as session:
            repository = AIGenerationTaskRepository(session, payload_store=cast("Any", NoMongoPayloadStore()))
            assert await repository.retire_unsupported_by_id(task_id) is retired
        async with sessions.begin() as session:
            saved = await session.get(AIGenerationTask, task_id)
            assert saved.status == ("failed" if retired else status)
            assert saved.attempts == 3
            if retired:
                assert saved.last_error_type == "RetiredTaskType"
                assert saved.completed_at is not None
    finally:
        await engine.dispose()


@pytest.mark.external
@pytest.mark.integration
async def test_retirement_skips_row_locked_by_another_worker(retry_postgres_url):
    from sqlalchemy import select

    engine = create_async_engine(retry_postgres_url)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    task_id = str(uuid4())
    try:
        async with engine.begin() as connection:
            await connection.run_sync(cast("Table", AIGenerationTask.__table__).create, checkfirst=True)
        async with sessions.begin() as session:
            session.add(
                AIGenerationTask(
                    id=task_id,
                    batch_id=str(uuid4()),
                    identity_key=task_id,
                    task_type="news.cover_image",
                    entity_type="test",
                    entity_id=task_id,
                    output_kind="image",
                    status="pending",
                    attempts=3,
                    max_attempts=3,
                )
            )
        async with sessions.begin() as owner:
            await owner.scalar(select(AIGenerationTask).where(AIGenerationTask.id == task_id).with_for_update())
            async with sessions.begin() as contender:
                repository = AIGenerationTaskRepository(contender, payload_store=cast("Any", NoMongoPayloadStore()))
                assert await repository.retire_unsupported_by_id(task_id) is False
        async with sessions.begin() as session:
            repository = AIGenerationTaskRepository(session, payload_store=cast("Any", NoMongoPayloadStore()))
            assert await repository.retire_unsupported_by_id(task_id) is True
    finally:
        await engine.dispose()
