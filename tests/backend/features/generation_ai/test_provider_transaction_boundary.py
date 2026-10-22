from __future__ import annotations

import asyncio
from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select
from tests.backend.features.generation_ai import test_input_durability as input_contract
from tests.backend.features.generation_ai.test_input_durability import spec, store

from src.backend.features.generation_ai.dto import AIGenerationTaskResultDTO
from src.backend.features.generation_ai.identity import build_generation_task_identity_key
from src.backend.features.generation_ai.models import AIGenerationTask
from src.backend.features.generation_ai.registry import AIGenerationTaskRegistry
from src.backend.features.generation_ai.repositories import AIGenerationTaskRepository
from src.backend.features.generation_ai.services import GenerationAIService

input_databases = input_contract.input_databases
stores = input_contract.stores


class Handler:
    task_type = "items.text"

    async def build_request(self, task):
        return {"kind": "json", "schema": dict}

    async def apply_result(self, task, result):
        pass


@pytest.mark.external
@pytest.mark.integration
@pytest.mark.parametrize("expire", [False, True])
async def test_provider_wait_has_no_transaction_or_claim_lock(stores, expire):
    sessions, database, _ = stores
    request = spec()
    async with sessions.begin() as session:
        task = await AIGenerationTaskRepository(session, payload_store=store(database)).create(
            request, batch_id=str(uuid4()), identity_key=build_generation_task_identity_key(request)
        )
        task_id = task.id
    registry = AIGenerationTaskRegistry()
    registry.register(Handler())
    async with sessions(expire_on_commit=expire) as processing:

        class Executor:
            async def generate(self, detached_task, request):
                assert not processing.in_transaction(), "SQL transaction held while waiting for AI"
                assert processing.bind.pool.checkedout() == 0, "SQL connection was not returned to pool"
                assert detached_task.input_payload["request"]["base_id"] == "sword"
                async with sessions.begin() as observer:
                    visible = await observer.scalar(
                        select(AIGenerationTask).where(AIGenerationTask.id == task_id).with_for_update(nowait=True)
                    )
                    assert visible.status == "running"
                    assert visible.attempts == 1
                return AIGenerationTaskResultDTO(output_payload={"name": "Name", "description": "Text"})

        service = GenerationAIService(
            repository=AIGenerationTaskRepository(processing, payload_store=store(database)),
            registry=registry,
            executor=Executor(),
            auto_schedule=False,
        )
        result = await service.process_task(task_id)
        assert result is not None
        await processing.commit()
    async with sessions() as observer:
        assert (await observer.get(AIGenerationTask, task_id)).status == "done"


async def seed(sessions, database, *, max_attempts=3):
    request = spec().model_copy(update={"max_attempts": max_attempts})
    async with sessions.begin() as session:
        task = await AIGenerationTaskRepository(session, payload_store=store(database)).create(
            request, batch_id=str(uuid4()), identity_key=build_generation_task_identity_key(request)
        )
        task_id = task.id
    return task_id


def registry(handler=None):
    result = AIGenerationTaskRegistry()
    result.register(handler or Handler())
    return result


@pytest.mark.external
@pytest.mark.integration
@pytest.mark.parametrize("change", ["status", "revision", "attempts", "claimed_at", "identity_key"])
@pytest.mark.parametrize("failed", [False, True])
async def test_stale_provider_response_or_failure_cannot_finalize(stores, change, failed):
    sessions, database, _ = stores
    task_id = await seed(sessions, database)
    applied = []

    class RecordingHandler(Handler):
        async def apply_result(self, task, result):
            applied.append(task.id)

    class Executor:
        async def generate(self, task, request):
            async with sessions.begin() as other:
                row = await other.get(AIGenerationTask, task_id)
                if change == "status":
                    row.status = "cancelled"
                elif change == "revision":
                    row.bump_revision()
                elif change == "attempts":
                    row.attempts += 1
                elif change == "claimed_at":
                    row.claimed_at += timedelta(seconds=1)
                else:
                    row.identity_key = f"changed:{task_id}"
            if failed:
                raise RuntimeError("provider failed after claim ownership changed")
            return AIGenerationTaskResultDTO(output_payload={"name": "Stale", "description": "Text"})

    async with sessions() as session:
        service = GenerationAIService(
            repository=AIGenerationTaskRepository(session, payload_store=store(database)),
            registry=registry(RecordingHandler()),
            executor=Executor(),
            auto_schedule=False,
        )
        assert await service.process_task(task_id) is None
        await session.commit()
    assert applied == []
    async with sessions() as session:
        row = await session.get(AIGenerationTask, task_id)
        assert row.status == ("cancelled" if change == "status" else "running")
        assert row.last_error_type is None
    doc = await database.ai_generation_task_documents.find_one({"task_id": task_id})
    assert doc["output_payload"] == {}


@pytest.mark.external
@pytest.mark.integration
async def test_committed_running_claim_blocks_duplicate_provider(stores):
    sessions, database, _ = stores
    task_id = await seed(sessions, database)
    calls = []

    class Executor:
        async def generate(self, task, request):
            calls.append(task.id)
            async with sessions() as duplicate:
                service = GenerationAIService(
                    repository=AIGenerationTaskRepository(duplicate, payload_store=store(database)),
                    registry=registry(),
                    executor=self,
                    auto_schedule=False,
                )
                assert await service.process_task(task_id) is None
                await duplicate.commit()
            return AIGenerationTaskResultDTO(output_payload={"name": "Name", "description": "Text"})

    async with sessions() as session:
        service = GenerationAIService(
            repository=AIGenerationTaskRepository(session, payload_store=store(database)),
            registry=registry(),
            executor=Executor(),
            auto_schedule=False,
        )
        assert await service.process_task(task_id) is not None
        await session.commit()
    assert calls == [task_id]
    async with sessions() as session:
        row = await session.get(AIGenerationTask, task_id)
        assert (row.status, row.attempts) == ("done", 1)


@pytest.mark.external
@pytest.mark.integration
async def test_claim_commit_failure_never_calls_provider(stores, monkeypatch):
    sessions, database, _ = stores
    task_id = await seed(sessions, database)
    called = []

    class Executor:
        async def generate(self, task, request):
            called.append(task.id)
            raise AssertionError("Provider must not run")

    async def denied():
        raise RuntimeError("injected SQL claim commit failure")

    async with sessions() as session:
        monkeypatch.setattr(session, "commit", denied)
        service = GenerationAIService(
            repository=AIGenerationTaskRepository(session, payload_store=store(database)),
            registry=registry(),
            executor=Executor(),
            auto_schedule=False,
        )
        with pytest.raises(RuntimeError, match="claim commit failure"):
            await service.process_task(task_id)
        await session.rollback()
    assert called == []
    async with sessions() as session:
        row = await session.get(AIGenerationTask, task_id)
        assert (row.status, row.attempts) == ("pending", 0)


@pytest.mark.external
@pytest.mark.integration
@pytest.mark.parametrize(
    "budget, message, expected, limit",
    [
        (3, "provider unavailable", "cooldown", 3),
        (1, "provider unavailable", "failed", 1),
        (3, "JSON generation failed schema validation", "cooldown", 8),
    ],
)
async def test_provider_failure_uses_new_owned_transaction_and_retry_budget(stores, budget, message, expected, limit):
    sessions, database, _ = stores
    task_id = await seed(sessions, database, max_attempts=budget)
    async with sessions() as processing:

        class Executor:
            async def generate(self, task, request):
                assert not processing.in_transaction()
                raise RuntimeError(message)

        service = GenerationAIService(
            repository=AIGenerationTaskRepository(processing, payload_store=store(database)),
            registry=registry(),
            executor=Executor(),
            auto_schedule=False,
        )
        assert await service.process_task(task_id) is None
        await processing.commit()
    async with sessions() as session:
        row = await session.get(AIGenerationTask, task_id)
        assert (row.status, row.attempts, row.max_attempts) == (expected, 1, limit)
        assert row.last_error_type == "RuntimeError"


@pytest.mark.external
@pytest.mark.integration
async def test_actual_worker_commits_finalization_after_provider_without_sql(stores, monkeypatch):
    from src.backend.features.generation_ai.workers import tasks

    sessions, database, _ = stores
    task_id = await seed(sessions, database)
    opened = []

    def context():
        session = sessions()
        opened.append(session)
        return session

    class Executor:
        async def generate(self, task, request):
            assert not opened[0].in_transaction()
            assert opened[0].bind.pool.checkedout() == 0
            return AIGenerationTaskResultDTO(output_payload={"name": "Name", "description": "Text"})

    monkeypatch.setattr(tasks, "get_manual_session_context", context)
    monkeypatch.setattr(
        tasks,
        "AIGenerationTaskRepository",
        lambda session: AIGenerationTaskRepository(session, payload_store=store(database)),
    )
    monkeypatch.setattr(tasks, "build_generation_ai_registry", lambda **kwargs: registry())
    monkeypatch.setattr(tasks, "CodexAIExecutor", lambda ai: Executor())
    assert (await tasks.generation_ai_process_task({"ai": object()}, task_id))["status"] == "ok"
    async with sessions() as observer:
        row = await observer.get(AIGenerationTask, task_id)
        assert (row.status, row.attempts) == ("done", 1)
    assert (await database.ai_generation_task_documents.find_one({"task_id": task_id}))["output_payload"][
        "name"
    ] == "Name"


@pytest.mark.external
@pytest.mark.integration
async def test_provider_cancellation_leaves_committed_running_claim_for_separate_recovery(stores):
    sessions, database, _ = stores
    task_id = await seed(sessions, database)

    class Executor:
        async def generate(self, task, request):
            raise asyncio.CancelledError()

    async with sessions() as session:
        service = GenerationAIService(
            repository=AIGenerationTaskRepository(session, payload_store=store(database)),
            registry=registry(),
            executor=Executor(),
            auto_schedule=False,
        )
        with pytest.raises(asyncio.CancelledError):
            await service.process_task(task_id)
    async with sessions() as session:
        row = await session.get(AIGenerationTask, task_id)
        assert (row.status, row.attempts) == ("running", 1)
