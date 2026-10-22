from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from arq.jobs import Job
from sqlalchemy import delete, select
from tests.backend.features.generation_ai import test_input_durability as input_contract
from tests.backend.features.generation_ai import test_schedule_recovery as schedule_contract
from tests.backend.features.generation_ai.test_input_durability import spec, store

from src.backend.features.generation_ai.identity import build_generation_task_identity_key
from src.backend.features.generation_ai.models import AIGenerationTask
from src.backend.features.generation_ai.repositories import AIGenerationTaskRepository

input_databases = input_contract.input_databases
base_stores = input_contract.stores
recovery_redis_port = schedule_contract.recovery_redis_port
recovery_queue = schedule_contract.recovery_queue


@pytest.fixture
async def stores(base_stores):
    sessions, _, _ = base_stores
    # This fixture owns its disposable database; isolate rows between lease tests.
    async with sessions.begin() as session:
        await session.execute(delete(AIGenerationTask))
    return base_stores


async def abandoned(sessions, database, *, budget=3):
    request = spec().model_copy(update={"max_attempts": budget})
    async with sessions() as session:
        repository = AIGenerationTaskRepository(session, payload_store=store(database))
        task = await repository.create(
            request, batch_id=str(uuid4()), identity_key=build_generation_task_identity_key(request)
        )
        task_id = task.id
        await repository.claim_by_id(task_id, now=datetime.now(UTC) - timedelta(hours=1))
        token = await repository.commit_claim_for_provider(task)
    return task_id, token


@pytest.mark.external
@pytest.mark.integration
async def test_abandoned_committed_claim_becomes_pending_without_resetting_attempts(stores):
    sessions, database, _ = stores
    task_id, token = await abandoned(sessions, database)
    async with sessions.begin() as session:
        repository = AIGenerationTaskRepository(session, payload_store=store(database))
        assert (await repository.recover_expired_running())["requeued"] == 1
    async with sessions() as session:
        repository = AIGenerationTaskRepository(session, payload_store=store(database))
        row = await session.get(AIGenerationTask, task_id)
        assert (row.status, row.attempts) == ("pending", 1)
        assert row.claimed_at is None
        assert await repository.reacquire_claim(token) is None


@pytest.mark.external
@pytest.mark.integration
async def test_unexpired_claim_is_preserved_and_expired_token_refused_before_sweep(stores):
    from src.backend.features.generation_ai.leases import RUNNING_LEASE

    sessions, database, _ = stores
    task_id, token = await abandoned(sessions, database)
    async with sessions() as session:
        repository = AIGenerationTaskRepository(session, payload_store=store(database))
        assert (
            await repository.reacquire_claim(token, now=token.claimed_at + RUNNING_LEASE - timedelta(microseconds=1))
            is not None
        )
        await session.rollback()
        assert await repository.reacquire_claim(token, now=token.claimed_at + RUNNING_LEASE) is None
        await session.rollback()
        assert (await repository.recover_expired_running(now=token.claimed_at + RUNNING_LEASE - timedelta(seconds=1)))[
            "scanned"
        ] == 0
        await session.commit()
        assert await repository.reacquire_claim(token) is None


@pytest.mark.external
@pytest.mark.integration
@pytest.mark.parametrize(
    "fault, reason",
    [
        ("budget", "LeaseAttemptsExhausted"),
        ("missing", "InvalidDurableInput"),
        ("corrupt", "InvalidDurableInput"),
        ("result", "StoredResultNeedsReview"),
        ("malformed_result", "StoredResultNeedsReview"),
        ("timestamp", "MissingClaimTimestamp"),
    ],
)
async def test_unsafe_replay_becomes_actionable_failure_without_destroying_payload(stores, fault, reason):
    from src.backend.features.generation_ai.api import _task_view

    sessions, database, _ = stores
    task_id, _ = await abandoned(sessions, database, budget=1 if fault == "budget" else 3)
    collection = database.ai_generation_task_documents
    if fault == "missing":
        await collection.delete_one({"task_id": task_id})
    elif fault == "corrupt":
        await collection.update_one({"task_id": task_id}, {"$set": {"input_payload": {"request": {}}}})
    elif fault in {"result", "malformed_result"}:
        await collection.update_one(
            {"task_id": task_id},
            {"$set": {"output_payload": {"name": "Saved", "description": "Text"} if fault == "result" else []}},
        )
    elif fault == "timestamp":
        async with sessions.begin() as session:
            row = await session.get(AIGenerationTask, task_id)
            row.claimed_at = None
            row.created_at = datetime.now(UTC) - timedelta(hours=2)
    await collection.update_one(
        {"task_id": task_id}, {"$set": {"error": {"type": "OldProviderError", "message": "older attempt"}}}
    )
    before = await collection.find_one({"task_id": task_id})
    async with sessions.begin() as session:
        result = await AIGenerationTaskRepository(session, payload_store=store(database)).recover_expired_running()
        assert result == {"scanned": 1, "requeued": 0, "failed": 1}
    async with sessions() as session:
        row = await AIGenerationTaskRepository(session, payload_store=store(database)).get(task_id)
        assert (row.status, row.attempts, row.last_error_type) == ("failed", 1, reason)
        assert row.completed_at is not None
        assert _task_view(row).error["type"] == reason
    assert await collection.find_one({"task_id": task_id}) == before


@pytest.mark.external
@pytest.mark.integration
async def test_storage_outage_and_sql_rollback_leave_running_intact(stores, monkeypatch):
    sessions, database, _ = stores
    task_id, token = await abandoned(sessions, database)
    payload_store = store(database)

    async def denied(task_id):
        raise ConnectionError("injected Mongo outage")

    monkeypatch.setattr(payload_store, "fetch_task_document", denied)
    async with sessions() as session:
        with pytest.raises(ConnectionError):
            await AIGenerationTaskRepository(session, payload_store=payload_store).recover_expired_running()
        await session.rollback()
    async with sessions() as session:
        await AIGenerationTaskRepository(session, payload_store=store(database)).recover_expired_running()
        await session.rollback()
    async with sessions() as session:
        row = await session.get(AIGenerationTask, task_id)
        assert (row.status, row.attempts, row.revision) == ("running", 1, token.revision)


@pytest.mark.external
@pytest.mark.integration
async def test_concurrent_sweep_and_row_lock_are_safe(stores):
    sessions, database, _ = stores
    task_id, _ = await abandoned(sessions, database)
    async with sessions() as locker:
        await locker.scalar(select(AIGenerationTask).where(AIGenerationTask.id == task_id).with_for_update())
        async with sessions.begin() as other:
            assert (await AIGenerationTaskRepository(other, payload_store=store(database)).recover_expired_running())[
                "scanned"
            ] == 0
        await locker.rollback()

    async def sweep():
        async with sessions.begin() as session:
            return await AIGenerationTaskRepository(session, payload_store=store(database)).recover_expired_running()

    results = await asyncio.gather(sweep(), sweep())
    assert sum(r["requeued"] for r in results) == 1
    async with sessions() as session:
        assert (await session.get(AIGenerationTask, task_id)).attempts == 1


@pytest.mark.external
@pytest.mark.integration
async def test_recovery_commit_queues_new_attempt_and_fences_old_owner(stores, recovery_queue, monkeypatch):
    from src.backend.features.generation_ai.leases import RUNNING_LEASE
    from src.backend.features.generation_ai.scheduling import replay_scheduling_page
    from src.backend.features.generation_ai.workers import tasks
    from src.backend.features.generation_ai.workers.arq import GenerationAIArqSettings

    sessions, database, _ = stores
    task_id, old = await abandoned(sessions, database)
    monkeypatch.setattr(tasks, "get_manual_session_context", sessions)
    monkeypatch.setattr(
        tasks,
        "AIGenerationTaskRepository",
        lambda session: AIGenerationTaskRepository(session, payload_store=store(database)),
    )
    assert (await tasks.generation_ai_recover_running({}))["requeued"] == 1
    async with sessions() as session:
        ids = await AIGenerationTaskRepository(session).list_schedulable_ids()
    assert ids == [task_id]
    assert await replay_scheduling_page(ids, recovery_queue) == 1
    info = await Job(f"generation-ai-recovery:{task_id}", recovery_queue).info()
    assert info.args == (task_id,)
    async with sessions() as session:
        repository = AIGenerationTaskRepository(session, payload_store=store(database))
        task = await repository.claim_by_id(task_id)
        current = await repository.commit_claim_for_provider(task)
        assert current.attempts == 2
        assert await repository.reacquire_claim(old) is None
        assert await repository.reacquire_claim(current) is not None
        await session.rollback()
    cron = next(j for j in GenerationAIArqSettings.cron_jobs if j.coroutine is tasks.generation_ai_recover_running)
    assert cron.run_at_startup and cron.second == 0 and cron.minute is None
    assert RUNNING_LEASE.total_seconds() > 2 * GenerationAIArqSettings.job_timeout


@pytest.mark.external
@pytest.mark.integration
async def test_bounded_sweeps_drain_backlog_and_preserve_nonlive_states(stores):
    sessions, database, _ = stores
    ids = [(await abandoned(sessions, database))[0] for _ in range(3)]
    async with sessions.begin() as session:
        row = await session.get(AIGenerationTask, ids[-1])
        row.task_type = "news.cover_image"
    totals = 0
    for _ in range(3):
        async with sessions.begin() as session:
            result = await AIGenerationTaskRepository(session, payload_store=store(database)).recover_expired_running(
                limit=1
            )
            assert result["scanned"] <= 1
            totals += result["requeued"]
    assert totals == 2
    async with sessions() as session:
        assert (await session.get(AIGenerationTask, ids[-1])).status == "running"


@pytest.mark.parametrize("limit", [0, 1001])
async def test_invalid_bound_is_rejected(limit):
    with pytest.raises(ValueError):
        await AIGenerationTaskRepository(None).recover_expired_running(limit=limit)


def test_execution_lease_is_longer_than_worker_timeout():
    from src.backend.features.generation_ai.leases import RUNNING_LEASE
    from src.backend.features.generation_ai.workers.arq import GenerationAIArqSettings

    assert RUNNING_LEASE.total_seconds() > 2 * GenerationAIArqSettings.job_timeout


@pytest.mark.external
@pytest.mark.integration
async def test_deadline_is_rechecked_after_lock_acquisition(stores, monkeypatch):
    from src.backend.features.generation_ai.leases import RUNNING_LEASE

    sessions, database, _ = stores
    _, token = await abandoned(sessions, database)
    times = iter(
        [
            token.claimed_at + RUNNING_LEASE - timedelta(seconds=1),
            token.claimed_at + RUNNING_LEASE + timedelta(seconds=1),
        ]
    )

    async def clock():
        return next(times)

    async with sessions() as session:
        repository = AIGenerationTaskRepository(session, payload_store=store(database))
        monkeypatch.setattr(repository, "_database_now", clock)
        assert await repository.reacquire_claim(token) is None


@pytest.mark.external
@pytest.mark.integration
async def test_late_old_provider_cannot_overwrite_recovered_attempt(stores):
    from tests.backend.features.generation_ai.test_provider_transaction_boundary import seed

    from src.backend.features.generation_ai.dto import AIGenerationTaskResultDTO
    from src.backend.features.generation_ai.registry import AIGenerationTaskRegistry
    from src.backend.features.generation_ai.services import GenerationAIService

    sessions, database, _ = stores
    task_id = await seed(sessions, database)
    applied = []
    registry = AIGenerationTaskRegistry()

    class Handler:
        task_type = "items.text"

        async def build_request(self, task):
            return {"kind": "json", "schema": dict}

        async def apply_result(self, task, result):
            applied.append(result.output_payload["name"])

    registry.register(Handler())

    class NewExecutor:
        async def generate(self, task, request):
            return AIGenerationTaskResultDTO(output_payload={"name": "New", "description": "Recovered"})

    class OldExecutor:
        async def generate(self, task, request):
            # Simulate elapsed lease while this provider response was suspended.
            async with sessions.begin() as other:
                row = await other.get(AIGenerationTask, task_id)
                row.claimed_at = datetime.now(UTC) - timedelta(hours=1)
            async with sessions.begin() as other:
                assert (
                    await AIGenerationTaskRepository(other, payload_store=store(database)).recover_expired_running()
                )["requeued"] == 1
            async with sessions() as new_session:
                service = GenerationAIService(
                    repository=AIGenerationTaskRepository(new_session, payload_store=store(database)),
                    registry=registry,
                    executor=NewExecutor(),
                    auto_schedule=False,
                )
                assert await service.process_task(task_id) is not None
                await new_session.commit()
            return AIGenerationTaskResultDTO(output_payload={"name": "Old", "description": "Stale"})

    async with sessions() as old_session:
        service = GenerationAIService(
            repository=AIGenerationTaskRepository(old_session, payload_store=store(database)),
            registry=registry,
            executor=OldExecutor(),
            auto_schedule=False,
        )
        assert await service.process_task(task_id) is None
        await old_session.commit()
    assert applied == ["New"]
    async with sessions() as session:
        row = await session.get(AIGenerationTask, task_id)
        assert (row.status, row.attempts) == ("done", 2)
    assert (await database.ai_generation_task_documents.find_one({"task_id": task_id}))["output_payload"][
        "name"
    ] == "New"
