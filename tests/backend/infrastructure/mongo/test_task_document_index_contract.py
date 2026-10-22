"""Real Mongo index/BSON contracts; RUN_GENERATION_INPUT_STORE_TESTS=1 opt-in.

Reuses only disposable PostgreSQL/Mongo fixtures; never reads application URLs.
"""

import asyncio
from datetime import datetime
from uuid import uuid4

import pytest
from pymongo.errors import DuplicateKeyError
from tests.backend.features.generation_ai import test_input_durability as input_contract

from src.backend.features.generation_ai.identity import build_generation_task_identity_key
from src.backend.features.generation_ai.repositories import AIGenerationTaskRepository
from src.backend.infrastructure.generation_ai.task_documents import (
    AI_GENERATION_TASK_DOCUMENT_KIND,
    AIGenerationTaskDocumentRepository,
)

input_databases = input_contract.input_databases
stores = input_contract.stores
pytestmark = [pytest.mark.external, pytest.mark.integration]


async def test_document_bootstrap_is_idempotent_and_bson_roundtrip_survives_new_repository(stores):
    sessions, database, _ = stores
    request = input_contract.spec()
    request.input_payload["wire"] = {"label": "Описание ☃", "values": [True, None, 1.25]}
    identity = build_generation_task_identity_key(request)
    async with sessions.begin() as session:
        task = await AIGenerationTaskRepository(session, payload_store=input_contract.store(database)).create(
            request, batch_id=str(uuid4()), identity_key=identity
        )
        task_id = str(task.id)
    documents = AIGenerationTaskDocumentRepository(database)
    await documents.ensure_indexes()
    await documents.ensure_indexes()
    loaded = await documents.fetch_by_task_id(task_id)
    assert loaded["input_payload"] == request.input_payload
    assert loaded["identity_key"] == identity
    assert isinstance(loaded["created_at"], datetime)
    assert loaded["created_at"].microsecond % 1000 == 0
    assert await documents.collection.count_documents({"task_id": task_id}) == 1
    duplicate = {**loaded, "_id": str(uuid4())}
    with pytest.raises(DuplicateKeyError):
        await documents.collection.insert_one(duplicate)
    assert await documents.fetch_by_task_id(task_id) == loaded


async def test_server_unique_index_allows_only_one_concurrent_task_document(stores):
    _, database, _ = stores
    documents = AIGenerationTaskDocumentRepository(database)
    await documents.ensure_indexes()
    task_id = str(uuid4())
    identity = {"document_kind": AI_GENERATION_TASK_DOCUMENT_KIND, "task_id": task_id}
    results = await asyncio.gather(
        *(documents.collection.insert_one({"_id": str(uuid4()), **identity}) for _ in range(2)),
        return_exceptions=True,
    )
    assert sum(isinstance(result, DuplicateKeyError) for result in results) == 1
    assert sum(not isinstance(result, Exception) for result in results) == 1
    assert await documents.collection.count_documents(identity) == 1
    # The compound key is task-scoped, not a global singleton collection.
    await documents.collection.insert_one({"_id": str(uuid4()), **identity, "task_id": str(uuid4())})
    assert await documents.collection.count_documents({}) == 2
