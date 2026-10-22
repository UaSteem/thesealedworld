from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from tests.backend.features.generation_ai import test_input_durability as input_contract
from tests.backend.features.generation_ai.test_input_durability import spec, store

from src.backend.features.generation_ai.identity import build_generation_task_identity_key
from src.backend.features.generation_ai.repositories import AIGenerationTaskRepository

input_databases = input_contract.input_databases
stores = input_contract.stores


@pytest.mark.external
@pytest.mark.integration
async def test_sql_rollback_orphan_is_retained_and_classified(stores):
    from src.backend.features.generation_ai.reconciliation import reconcile_document

    sessions, database, _ = stores
    request = spec()
    async with sessions() as session:
        task = await AIGenerationTaskRepository(session, payload_store=store(database)).create(
            request, batch_id=str(uuid4()), identity_key=build_generation_task_identity_key(request)
        )
        task_id = task.id
        await session.rollback()
    await age(database, task_id)
    document = await database.ai_generation_task_documents.find_one({"task_id": task_id})
    async with sessions.begin() as session:
        state = await reconcile_document(AIGenerationTaskRepository(session, payload_store=store(database)), document)
    assert state == "orphan"
    stored = await database.ai_generation_task_documents.find_one({"task_id": task_id})
    assert stored["input_payload"] == request.input_payload
    assert stored["reconciliation"]["state"] == "orphan"


async def age(database, task_id):
    await database.ai_generation_task_documents.update_one(
        {"task_id": task_id}, {"$set": {"updated_at": datetime.now(UTC) - timedelta(hours=2)}}
    )


async def seed(sessions, database, *, pointer=None, status="pending", output=None):
    request = spec()
    async with sessions.begin() as session:
        task = await AIGenerationTaskRepository(session, payload_store=store(database)).create(
            request, batch_id=str(uuid4()), identity_key=build_generation_task_identity_key(request)
        )
        task_id, document_id = task.id, task.mongo_document_id
        task.mongo_document_id = pointer
        task.status = status
    if output is not None:
        await database.ai_generation_task_documents.update_one(
            {"task_id": task_id}, {"$set": {"output_payload": output}}
        )
    await age(database, task_id)
    return task_id, document_id


@pytest.mark.external
@pytest.mark.integration
@pytest.mark.parametrize(
    "status, output, expected",
    [
        ("pending", {}, "repaired"),
        ("done", {"name": "Name", "description": "Text"}, "repaired"),
        ("running", {"name": "Name", "description": "Text"}, "repaired_result_pending_review"),
        ("done", {}, "conflict"),
        ("done", {"bad": "output"}, "conflict"),
    ],
)
async def test_missing_pointer_repair_never_applies_or_changes_execution_state(stores, status, output, expected):
    from src.backend.features.generation_ai.models import AIGenerationTask
    from src.backend.features.generation_ai.reconciliation import reconcile_document

    sessions, database, _ = stores
    task_id, pointer = await seed(sessions, database, status=status, output=output)
    document = await database.ai_generation_task_documents.find_one({"task_id": task_id})
    async with sessions.begin() as session:
        assert (
            await reconcile_document(AIGenerationTaskRepository(session, payload_store=store(database)), document)
            == expected
        )
    async with sessions() as session:
        task = await session.get(AIGenerationTask, task_id)
        assert task.mongo_document_id == (None if expected == "conflict" else pointer)
        assert task.status == status
        assert task.attempts == 0
    stored = await database.ai_generation_task_documents.find_one({"task_id": task_id})
    assert stored["output_payload"] == output
    assert stored["input_payload"] == document["input_payload"]


@pytest.mark.external
@pytest.mark.integration
@pytest.mark.parametrize("fault", ["pointer", "schema", "identity", "input", "metadata", "output"])
async def test_conflicts_are_retained_without_repair(stores, fault):
    from src.backend.features.generation_ai.models import AIGenerationTask
    from src.backend.features.generation_ai.reconciliation import reconcile_document

    sessions, database, _ = stores
    task_id, _ = await seed(sessions, database, pointer="conflicting" if fault == "pointer" else None)
    if fault != "pointer":
        field = {
            "schema": "schema_version",
            "identity": "identity_key",
            "input": "input_payload",
            "metadata": "metadata",
            "output": "output_payload",
        }[fault]
        await database.ai_generation_task_documents.update_one({"task_id": task_id}, {"$set": {field: "invalid"}})
    document = await database.ai_generation_task_documents.find_one({"task_id": task_id})
    async with sessions.begin() as session:
        assert (
            await reconcile_document(AIGenerationTaskRepository(session, payload_store=store(database)), document)
            == "conflict"
        )
    async with sessions() as session:
        task = await session.get(AIGenerationTask, task_id)
        assert task.mongo_document_id == ("conflicting" if fault == "pointer" else None)
    assert await database.ai_generation_task_documents.count_documents({"task_id": task_id}) == 1


@pytest.mark.external
@pytest.mark.integration
async def test_cas_and_busy_row_defer_repair(stores):
    from src.backend.features.generation_ai.models import AIGenerationTask
    from src.backend.features.generation_ai.reconciliation import reconcile_document

    sessions, database, _ = stores
    task_id, _ = await seed(sessions, database)
    document = await database.ai_generation_task_documents.find_one({"task_id": task_id})
    async with sessions() as locker:
        await AIGenerationTaskRepository(locker).lock_for_reconciliation(task_id)
        async with sessions.begin() as session:
            assert (
                await reconcile_document(AIGenerationTaskRepository(session, payload_store=store(database)), document)
                == "busy"
            )
        await locker.rollback()
    await database.ai_generation_task_documents.update_one(
        {"task_id": task_id}, {"$set": {"output_payload": {"name": "Changed", "description": "New"}}}
    )
    async with sessions.begin() as session:
        assert (
            await reconcile_document(AIGenerationTaskRepository(session, payload_store=store(database)), document)
            == "stale"
        )
    async with sessions() as session:
        assert (await session.get(AIGenerationTask, task_id)).mongo_document_id is None


@pytest.mark.external
@pytest.mark.integration
async def test_repair_rollback_and_repeat_are_safe(stores):
    from src.backend.features.generation_ai.models import AIGenerationTask
    from src.backend.features.generation_ai.reconciliation import reconcile_document

    sessions, database, _ = stores
    task_id, pointer = await seed(sessions, database)
    document = await database.ai_generation_task_documents.find_one({"task_id": task_id})
    async with sessions() as session:
        assert (
            await reconcile_document(AIGenerationTaskRepository(session, payload_store=store(database)), document)
            == "repaired"
        )
        await session.rollback()
    async with sessions() as session:
        assert (await session.get(AIGenerationTask, task_id)).mongo_document_id is None
    for expected in ["repaired", "linked"]:
        fresh = await database.ai_generation_task_documents.find_one({"task_id": task_id})
        async with sessions.begin() as session:
            assert (
                await reconcile_document(AIGenerationTaskRepository(session, payload_store=store(database)), fresh)
                == expected
            )
    async with sessions() as session:
        assert (await session.get(AIGenerationTask, task_id)).mongo_document_id == pointer


@pytest.mark.external
@pytest.mark.integration
async def test_worker_pages_grace_and_failure_cursor(stores, monkeypatch):
    from src.backend.features.generation_ai.workers import tasks
    from src.backend.features.generation_ai.workers.arq import GenerationAIArqSettings

    sessions, database, _ = stores
    payload_store = store(database)
    ids = [await seed(sessions, database) for _ in range(3)]
    # Fresh documents are never candidates, even if their pointer is missing.
    await database.ai_generation_task_documents.update_one(
        {"task_id": ids[-1][0]}, {"$set": {"updated_at": datetime.now(UTC)}}
    )
    monkeypatch.setattr(tasks, "AIGenerationTaskPayloadStore", lambda: payload_store)
    monkeypatch.setattr(tasks, "get_manual_session_context", sessions)
    monkeypatch.setattr(tasks, "RECONCILIATION_PAGE_SIZE", 1)
    ctx = {}
    states = []
    for _ in range(10):
        states.append(await tasks.generation_ai_reconcile_documents(ctx))
        if ctx["generation_ai_reconciliation_cursor"] is None:
            break
    assert sum(item.get("repaired", 0) for item in states) == 2
    assert next(
        j for j in GenerationAIArqSettings.cron_jobs if j.coroutine is tasks.generation_ai_reconcile_documents
    ).run_at_startup
    old_cursor = ctx["generation_ai_reconciliation_cursor"]

    async def denied(**kwargs):
        raise ConnectionError("injected Mongo denial")

    monkeypatch.setattr(payload_store, "reconciliation_page", denied)
    with pytest.raises(ConnectionError):
        await tasks.generation_ai_reconcile_documents(ctx)
    assert ctx["generation_ai_reconciliation_cursor"] == old_cursor


@pytest.mark.parametrize("limit", [0, 1001])
async def test_invalid_page_bound_is_rejected(limit):
    from src.backend.infrastructure.generation_ai.task_documents import AIGenerationTaskDocumentRepository

    with pytest.raises(ValueError):
        await AIGenerationTaskDocumentRepository().reconciliation_page(before=datetime.now(UTC), limit=limit)


@pytest.mark.external
@pytest.mark.integration
async def test_late_commit_clears_advisory_orphan_mark(stores):
    from src.backend.features.generation_ai.reconciliation import reconcile_document

    sessions, database, _ = stores
    request = spec()
    async with sessions() as original:
        task = await AIGenerationTaskRepository(original, payload_store=store(database)).create(
            request, batch_id=str(uuid4()), identity_key=build_generation_task_identity_key(request)
        )
        task_id = task.id
        await age(database, task_id)
        document = await database.ai_generation_task_documents.find_one({"task_id": task_id})
        async with sessions.begin() as recovery:
            assert (
                await reconcile_document(AIGenerationTaskRepository(recovery, payload_store=store(database)), document)
                == "orphan"
            )
        await original.commit()
    fresh = await database.ai_generation_task_documents.find_one({"task_id": task_id})
    assert fresh["reconciliation"]["state"] == "orphan"
    async with sessions.begin() as recovery:
        repository = AIGenerationTaskRepository(recovery, payload_store=store(database))
        assert await reconcile_document(repository, fresh) == "linked"
        # The advisory mark never blocks ordinary claim or hides input.
        assert await repository.claim_by_id(task_id) is not None
    stored = await database.ai_generation_task_documents.find_one({"task_id": task_id})
    assert stored["reconciliation"]["state"] == "linked"


@pytest.mark.external
@pytest.mark.integration
@pytest.mark.parametrize("fault", ["outage", "unacknowledged"])
async def test_failed_mark_never_repairs_sql_pointer(stores, monkeypatch, fault):
    from pymongo.results import UpdateResult

    from src.backend.features.generation_ai.models import AIGenerationTask
    from src.backend.features.generation_ai.reconciliation import reconcile_document

    sessions, database, _ = stores
    task_id, _ = await seed(sessions, database)
    document = await database.ai_generation_task_documents.find_one({"task_id": task_id})
    payload_store = store(database)

    async def denied(*args, **kwargs):
        if fault == "outage":
            raise ConnectionError("injected Mongo mark denial")
        return UpdateResult({}, acknowledged=False)

    monkeypatch.setattr(payload_store.repository.collection, "update_one", denied)
    async with sessions() as session:
        with pytest.raises((ConnectionError, ValueError)):
            await reconcile_document(AIGenerationTaskRepository(session, payload_store=payload_store), document)
        await session.commit()
    async with sessions() as session:
        assert (await session.get(AIGenerationTask, task_id)).mongo_document_id is None
