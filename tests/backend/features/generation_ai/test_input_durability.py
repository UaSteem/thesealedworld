from __future__ import annotations

import os
import subprocess
import time
from typing import cast
from uuid import uuid4

import pytest
from pymongo import AsyncMongoClient
from sqlalchemy import Table, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.backend.features.generation_ai.dto import AIGenerationTaskSpecDTO
from src.backend.features.generation_ai.identity import build_generation_task_identity_key
from src.backend.features.generation_ai.integrations.task_payload_store import AIGenerationTaskPayloadStore
from src.backend.features.generation_ai.models import AIGenerationTask
from src.backend.features.generation_ai.registry import AIGenerationTaskRegistry
from src.backend.features.generation_ai.repositories import AIGenerationTaskRepository
from src.backend.features.generation_ai.services import GenerationAIService
from src.backend.infrastructure.generation_ai.task_documents import AIGenerationTaskDocumentRepository


@pytest.fixture(scope="module")
def input_databases():
    if os.environ.get("RUN_GENERATION_INPUT_STORE_TESTS") != "1":
        pytest.skip("Set RUN_GENERATION_INPUT_STORE_TESTS=1 for isolated SQL/Mongo tests")
    names = [f"generation-input-{uuid4().hex}" for _ in range(2)]

    def docker(*args):
        return subprocess.check_output(["docker", *args], text=True, timeout=60).strip()

    try:
        docker(
            "run",
            "-d",
            "--rm",
            "--name",
            names[0],
            "-p",
            "127.0.0.1::5432",
            "-e",
            "POSTGRES_PASSWORD=input-test",
            "-e",
            "POSTGRES_DB=input_test",
            "postgres:16-alpine",
        )
        docker("run", "-d", "--rm", "--name", names[1], "-p", "127.0.0.1::27017", "mongo:8")
        for _ in range(60):
            ready = subprocess.run(
                ["docker", "exec", names[0], "pg_isready", "-U", "postgres"], capture_output=True, timeout=10
            )
            if ready.returncode == 0:
                break
            time.sleep(0.5)
        else:
            pytest.fail("Isolated PostgreSQL startup failed")
        pg_port = docker("port", names[0], "5432/tcp").rsplit(":", 1)[1]
        mongo_port = docker("port", names[1], "27017/tcp").rsplit(":", 1)[1]
        yield (
            f"postgresql+asyncpg://postgres:input-test@127.0.0.1:{pg_port}/input_test",  # pragma: allowlist secret
            f"mongodb://127.0.0.1:{mongo_port}",
        )
    finally:
        for name in names:
            subprocess.run(["docker", "rm", "--force", "--volumes", name], capture_output=True, timeout=60)


@pytest.fixture
async def stores(input_databases):
    pg_url, mongo_url = input_databases
    engine = create_async_engine(pg_url)
    client = AsyncMongoClient(mongo_url, serverSelectionTimeoutMS=5000)
    database = client[f"input_{uuid4().hex}"]
    await client.admin.command("ping")
    async with engine.begin() as connection:
        await connection.run_sync(cast("Table", AIGenerationTask.__table__).create, checkfirst=True)
    try:
        yield async_sessionmaker(engine, expire_on_commit=False), database, mongo_url
    finally:
        await client.drop_database(database.name)
        await client.close()
        await engine.dispose()


def spec():
    return AIGenerationTaskSpecDTO(
        task_type="items.text",
        entity_type="item",
        entity_id=str(uuid4()),
        output_kind="json",
        input_payload={"request": {"base_id": "sword"}},
    )


def store(database):
    return AIGenerationTaskPayloadStore(AIGenerationTaskDocumentRepository(database))


class Handler:
    task_type = "items.text"

    async def build_request(self, task):
        raise AssertionError("Invalid input must never reach the handler/provider")


class FailingStore(AIGenerationTaskPayloadStore):
    async def create_task_document(self, **kwargs):
        raise ConnectionError("injected initial Mongo denial")


@pytest.mark.external
@pytest.mark.integration
async def test_initial_failure_caught_then_commit_leaves_no_sql_or_schedule(stores):
    sessions, database, _ = stores
    request = spec()
    registry = AIGenerationTaskRegistry()
    registry.register(Handler())
    async with sessions() as session:
        service = GenerationAIService(
            repository=AIGenerationTaskRepository(session, payload_store=FailingStore()),
            registry=registry,
            auto_schedule=False,
        )
        with pytest.raises(ConnectionError):
            await service.enqueue_many([request])
        await session.commit()
        assert await service.schedule_pending_task_ids() == 0
    async with sessions() as session:
        assert (
            await session.scalar(
                select(AIGenerationTask).where(
                    AIGenerationTask.identity_key == build_generation_task_identity_key(request)
                )
            )
            is None
        )
    assert await database.ai_generation_task_documents.count_documents({}) == 0


@pytest.mark.external
@pytest.mark.integration
@pytest.mark.parametrize(
    "fault",
    ["missing", "outage", "schema", "identity", "entity", "type", "output", "input", "request", "tampered", "prompt"],
)
@pytest.mark.parametrize("operation", ["claim_by_id", "claim_next", "enqueue"])
async def test_bad_durable_input_does_not_advance_or_schedule(stores, fault, operation, monkeypatch):
    sessions, database, _ = stores
    request = spec()
    async with sessions.begin() as session:
        task = await AIGenerationTaskRepository(session, payload_store=store(database)).create(
            request, batch_id=str(uuid4()), identity_key=build_generation_task_identity_key(request)
        )
        task_id = task.id
    collection = database.ai_generation_task_documents
    if fault == "missing":
        await collection.delete_one({"task_id": task_id})
    elif fault != "outage":
        field, value = {
            "schema": ("schema_version", 99),
            "identity": ("identity_key", "wrong"),
            "entity": ("entity_id", "wrong"),
            "type": ("task_type", "wrong"),
            "output": ("output_kind", "text"),
            "input": ("input_payload", []),
            "request": ("input_payload", {"request": {}}),
            "tampered": ("input_payload", {"request": {"base_id": "different-valid-item"}}),
            "prompt": ("prompt_payload", {"changed": "valid dictionary"}),
        }[fault]
        await collection.update_one({"task_id": task_id}, {"$set": {field: value}})
    payload_store = store(database)
    if fault == "outage":

        async def denied(task_id):
            raise ConnectionError("injected Mongo read denial")

        monkeypatch.setattr(payload_store, "fetch_task_document", denied)
    registry = AIGenerationTaskRegistry()
    registry.register(Handler())
    async with sessions() as session:
        repository = AIGenerationTaskRepository(session, payload_store=payload_store)
        service = GenerationAIService(repository=repository, registry=registry, auto_schedule=False)
        with pytest.raises((ValueError, ConnectionError)):
            if operation == "enqueue":
                await service.enqueue_many([request])
            else:
                # The by-id production worker also checks retirement before claiming.
                if operation == "claim_by_id":
                    await service.process_task(task_id)
                else:
                    await service.claim_and_process_next()
        await session.commit()  # caller catching the error cannot commit a consumed attempt
        assert await service.schedule_pending_task_ids() == 0
    async with sessions() as session:
        task = await session.get(AIGenerationTask, task_id)
        assert (task.status, task.attempts, task.claimed_at) == ("pending", 0, None)
        await session.delete(task)
        await session.commit()


@pytest.mark.external
@pytest.mark.integration
async def test_restart_reuses_and_claims_original_document_without_sql_pointer(stores):
    sessions, database, mongo_url = stores
    request = spec()
    async with sessions.begin() as session:
        task = await AIGenerationTaskRepository(session, payload_store=store(database)).create(
            request, batch_id=str(uuid4()), identity_key=build_generation_task_identity_key(request)
        )
        task_id = task.id
        # Existing old pending metadata may have no Mongo status/pointer. Actual input is decisive.
        task.mongo_document_id = None
        task.mongo_status = "legacy"
    fresh_client = AsyncMongoClient(mongo_url)
    try:
        fresh_store = store(fresh_client[database.name])
        registry = AIGenerationTaskRegistry()
        registry.register(Handler())
        async with sessions.begin() as session:
            repository = AIGenerationTaskRepository(session, payload_store=fresh_store)
            result = await GenerationAIService(
                repository=repository, registry=registry, auto_schedule=False
            ).enqueue_many([request])
            assert (result.created, result.reused, result.task_ids) == (0, 1, [task_id])
            loaded = await repository.claim_by_id(task_id)
            assert loaded.input_payload == request.input_payload
            assert (loaded.status, loaded.attempts) == ("running", 1)
    finally:
        await fresh_client.close()


@pytest.mark.external
@pytest.mark.integration
@pytest.mark.parametrize("fault", ["unacknowledged", "missing", "identity", "schema", "input", "returned_id"])
async def test_initial_write_requires_confirmed_matching_readback(stores, fault, monkeypatch):
    from pymongo.results import UpdateResult

    sessions, database, _ = stores
    payload_store = store(database)
    collection = payload_store.repository.collection
    original_write = collection.update_one
    original_read = collection.find_one

    async def write(*args, **kwargs):
        result = await original_write(*args, **kwargs)
        return UpdateResult({}, acknowledged=False) if fault == "unacknowledged" else result

    async def read(*args, **kwargs):
        document = await original_read(*args, **kwargs)
        if fault == "missing":
            return None
        if fault in {"identity", "schema", "input"}:
            field = {"identity": "entity_id", "schema": "schema_version", "input": "input_payload"}[fault]
            document[field] = "corrupted"
        return document

    monkeypatch.setattr(collection, "update_one", write)
    monkeypatch.setattr(collection, "find_one", read)
    if fault == "returned_id":
        original_create = payload_store.create_task_document

        async def create(**kwargs):
            await original_create(**kwargs)
            return "unconfirmed-pointer"

        monkeypatch.setattr(payload_store, "create_task_document", create)
    request = spec()
    async with sessions() as session:
        repository = AIGenerationTaskRepository(session, payload_store=payload_store)
        with pytest.raises(ValueError):
            await repository.create(
                request, batch_id=str(uuid4()), identity_key=build_generation_task_identity_key(request)
            )
        await session.commit()
    async with sessions() as session:
        assert (
            await session.scalar(
                select(AIGenerationTask).where(
                    AIGenerationTask.identity_key == build_generation_task_identity_key(request)
                )
            )
            is None
        )


@pytest.mark.external
@pytest.mark.integration
async def test_cached_payload_cannot_bypass_read_denial_and_history_remains_readable(stores, monkeypatch):
    sessions, database, _ = stores
    payload_store = store(database)
    request = spec()
    async with sessions.begin() as session:
        repository = AIGenerationTaskRepository(session, payload_store=payload_store)
        task = await repository.create(
            request, batch_id=str(uuid4()), identity_key=build_generation_task_identity_key(request)
        )
        assert task.input_payload == request.input_payload

        async def denied(task_id):
            raise ConnectionError("Mongo read denied after transient hydration")

        monkeypatch.setattr(payload_store, "fetch_task_document", denied)
        assert await repository.get(task.id) is task
        with pytest.raises(ConnectionError):
            await repository.prepare_existing_for_enqueue(task, max_attempts=8)
        with pytest.raises(ConnectionError):
            await repository.claim_by_id(task.id)
        assert (task.status, task.attempts, task.max_attempts) == ("pending", 0, 3)
        # Status writes remain available even if readback cannot hydrate history.
        await repository.mark_failed(task.id, {"type": "test", "message": "metadata still writable"})
        assert task.status == "failed"


@pytest.mark.external
@pytest.mark.integration
async def test_retired_job_with_missing_input_keeps_history_and_retires_before_provider(stores):
    sessions, database, _ = stores
    task_id = str(uuid4())
    async with sessions.begin() as session:
        session.add(
            AIGenerationTask(
                id=task_id,
                batch_id=str(uuid4()),
                identity_key=task_id,
                task_type="world.zone_lore",
                entity_type="zone",
                entity_id=task_id,
                output_kind="json",
                status="pending",
                attempts=3,
                max_attempts=3,
            )
        )
    async with sessions.begin() as session:
        repository = AIGenerationTaskRepository(session, payload_store=store(database))
        assert (await repository.get(task_id)).status == "pending"
        service = GenerationAIService(repository=repository, registry=AIGenerationTaskRegistry(), auto_schedule=False)
        assert await service.process_task(task_id) is None
        task = await session.get(AIGenerationTask, task_id)
        assert (task.status, task.attempts, task.last_error_type) == ("failed", 3, "RetiredTaskType")


@pytest.mark.external
@pytest.mark.integration
async def test_history_and_failed_reuse_do_not_replace_sql_pointer(stores):
    sessions, database, _ = stores
    request = spec()
    async with sessions.begin() as session:
        task = await AIGenerationTaskRepository(session, payload_store=store(database)).create(
            request, batch_id=str(uuid4()), identity_key=build_generation_task_identity_key(request)
        )
        task_id, original_pointer = task.id, task.mongo_document_id
    collection = database.ai_generation_task_documents
    document = await collection.find_one({"task_id": task_id})
    await collection.delete_one({"task_id": task_id})
    document["_id"] = "different-document"
    await collection.insert_one(document)
    async with sessions() as session:
        repository = AIGenerationTaskRepository(session, payload_store=store(database))
        task = await repository.get(task_id)
        assert task.mongo_document_id == original_pointer
        task = await repository.find_by_identity_key(build_generation_task_identity_key(request))
        with pytest.raises(ValueError, match="pointer"):
            await repository.prepare_existing_for_enqueue(task, max_attempts=8)
        await session.commit()
    async with sessions() as session:
        task = await session.get(AIGenerationTask, task_id)
        assert (task.mongo_document_id, task.mongo_schema_version, task.status, task.attempts) == (
            original_pointer,
            1,
            "pending",
            0,
        )
        await session.delete(task)
        await session.commit()


@pytest.mark.external
@pytest.mark.integration
@pytest.mark.parametrize(
    "fault", ["outage", "unacknowledged", "no_match", "missing", "payload", "metadata", "pointer", "identity", "schema"]
)
async def test_result_failure_caught_then_commit_never_completes(stores, fault, monkeypatch):
    from pymongo.results import UpdateResult

    from src.backend.features.generation_ai.dto import AIGenerationTaskResultDTO

    sessions, database, _ = stores
    request = spec()
    async with sessions.begin() as session:
        repository = AIGenerationTaskRepository(session, payload_store=store(database))
        task = await repository.create(
            request, batch_id=str(uuid4()), identity_key=build_generation_task_identity_key(request)
        )
        await repository.claim_by_id(task.id)
        task_id = task.id
    payload_store = store(database)
    collection = payload_store.repository.collection
    original_write, original_read = collection.update_one, collection.find_one

    async def write(*args, **kwargs):
        if fault == "outage":
            raise ConnectionError("injected result write denial")
        if fault == "no_match":
            return UpdateResult({"n": 0, "nModified": 0}, acknowledged=True)
        written = await original_write(*args, **kwargs)
        return UpdateResult({}, acknowledged=False) if fault == "unacknowledged" else written

    async def read(*args, **kwargs):
        document = await original_read(*args, **kwargs)
        # Only corrupt result confirmation, not ordinary hydration.
        if document and document.get("output_payload") == {"name": "Saved", "description": "Text"}:
            if fault == "missing":
                return None
            field = {
                "payload": "output_payload",
                "metadata": "metadata",
                "pointer": "_id",
                "identity": "identity_key",
                "schema": "schema_version",
            }.get(fault)
            if field:
                document[field] = "corrupt"
        return document

    monkeypatch.setattr(collection, "update_one", write)
    monkeypatch.setattr(collection, "find_one", read)
    async with sessions() as session:
        repository = AIGenerationTaskRepository(session, payload_store=payload_store)
        with pytest.raises((ConnectionError, ValueError)):
            await repository.mark_done(
                task_id,
                AIGenerationTaskResultDTO(
                    output_payload={"name": "Saved", "description": "Text"}, metadata={"provider": "test"}
                ),
            )
        await session.commit()
    async with sessions() as session:
        task = await session.get(AIGenerationTask, task_id)
        assert task.status == "running"
        assert task.completed_at is None
        assert task.attempts == 1


@pytest.mark.external
@pytest.mark.integration
async def test_result_survives_new_clients_and_keeps_original_input(stores):
    from src.backend.features.generation_ai.dto import AIGenerationTaskResultDTO

    sessions, database, mongo_url = stores
    request = spec()
    result = AIGenerationTaskResultDTO(
        output_payload={"name": "Saved", "description": "Text"}, metadata={"provider": "test"}
    )
    async with sessions.begin() as session:
        repository = AIGenerationTaskRepository(session, payload_store=store(database))
        task = await repository.create(
            request, batch_id=str(uuid4()), identity_key=build_generation_task_identity_key(request)
        )
        task_id, pointer = task.id, task.mongo_document_id
        await repository.claim_by_id(task_id)
        await repository.mark_done(task_id, result)
    fresh_client = AsyncMongoClient(mongo_url, serverSelectionTimeoutMS=5000)
    try:
        async with sessions() as session:
            repository = AIGenerationTaskRepository(session, payload_store=store(fresh_client[database.name]))
            task = await repository.get(task_id)
            assert task.status == "done"
            assert task.mongo_document_id == pointer
            assert task.output_payload == result.output_payload
            assert task.input_payload == request.input_payload
            assert task.metadata_["provider"] == "test"
            assert task.completed_at is not None
            assert task.last_error_type is None
    finally:
        await fresh_client.close()


@pytest.mark.external
@pytest.mark.integration
@pytest.mark.parametrize("max_attempts, expected_status", [(3, "cooldown"), (1, "failed")])
async def test_service_result_write_denial_after_apply_cannot_commit_done(
    stores, monkeypatch, max_attempts, expected_status
):
    from src.backend.features.generation_ai.dto import AIGenerationTaskResultDTO

    sessions, database, _ = stores
    request = spec().model_copy(update={"max_attempts": max_attempts})
    applied = []

    class ResultHandler:
        task_type = "items.text"

        async def build_request(self, task):
            return {"kind": "json", "schema": dict}

        async def apply_result(self, task, result):
            applied.append(result.output_payload)

    class Executor:
        async def generate(self, task, request):
            return AIGenerationTaskResultDTO(output_payload={"name": "Saved", "description": "Text"})

    async with sessions.begin() as session:
        repository = AIGenerationTaskRepository(session, payload_store=store(database))
        task = await repository.create(
            request, batch_id=str(uuid4()), identity_key=build_generation_task_identity_key(request)
        )
        task_id = task.id
    payload_store = store(database)

    async def denied(**kwargs):
        raise ConnectionError("injected result persistence denial")

    monkeypatch.setattr(payload_store.repository, "record_result", denied)
    registry = AIGenerationTaskRegistry()
    registry.register(ResultHandler())
    async with sessions() as session:
        service = GenerationAIService(
            repository=AIGenerationTaskRepository(session, payload_store=payload_store),
            registry=registry,
            executor=Executor(),
            auto_schedule=False,
        )
        assert await service.process_task(task_id) is None
        await session.commit()
    async with sessions() as session:
        task = await session.get(AIGenerationTask, task_id)
        assert task.status == expected_status
        assert task.attempts == 1
        assert task.last_error_type == "ConnectionError"
        assert task.mongo_status == "stored"
    assert applied == [{"name": "Saved", "description": "Text"}]
    document = await database.ai_generation_task_documents.find_one({"task_id": task_id})
    assert document["output_payload"] == {}
    assert document["error"]["type"] == "ConnectionError"


@pytest.mark.external
@pytest.mark.integration
async def test_deleted_input_is_not_recreated_from_cached_task_on_completion(stores):
    from src.backend.features.generation_ai.dto import AIGenerationTaskResultDTO

    sessions, database, _ = stores
    request = spec()
    async with sessions.begin() as session:
        repository = AIGenerationTaskRepository(session, payload_store=store(database))
        task = await repository.create(
            request, batch_id=str(uuid4()), identity_key=build_generation_task_identity_key(request)
        )
        task_id = task.id
    async with sessions() as session:
        repository = AIGenerationTaskRepository(session, payload_store=store(database))
        await repository.claim_by_id(task_id)
        await database.ai_generation_task_documents.delete_one({"task_id": task_id})
        with pytest.raises(ValueError):
            await repository.mark_done(task_id, AIGenerationTaskResultDTO(output_payload={"name": "Lost"}))
        await session.commit()
    async with sessions() as session:
        task = await session.get(AIGenerationTask, task_id)
        assert task.status == "running"
    assert await database.ai_generation_task_documents.count_documents({"task_id": task_id}) == 0
