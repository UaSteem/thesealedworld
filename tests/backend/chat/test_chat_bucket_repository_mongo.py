"""Opt-in checks against an explicitly provided disposable MongoDB instance."""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pymongo import AsyncMongoClient

from src.backend.infrastructure.mongo.chat_buckets import ChatBucketRepository


@pytest.mark.external
@pytest.mark.asyncio
async def test_disposable_mongo_concurrent_replay_and_capacity() -> None:
    url = os.environ.get("TEST_MONGO_URL")
    if not url:
        pytest.skip("requires disposable TEST_MONGO_URL, never production")
    client = AsyncMongoClient(url)
    name = f"tbmmorpg_platform_validation_{uuid4().hex}"
    database = client[name]
    repo = ChatBucketRepository(database, max_bucket_messages=3)
    at = datetime(2026, 6, 4, tzinfo=UTC)

    async def append(index):
        return await repo.append_message(
            thread_id="t",
            thread_type="world",
            scope_id="global",
            created_at=at,
            message={"id": str(index), "content": f"body-{index}"},
        )

    try:
        refs = await asyncio.gather(*(append(index) for index in range(24)))
        replay = await asyncio.gather(*(append(index) for index in range(24)))
        assert replay == refs
        messages = await repo.get_messages([(ref.collection, ref.bucket_id, ref.seq) for ref in refs])
        for index, ref in enumerate(refs):
            assert messages[(ref.collection, ref.bucket_id, ref.seq)]["content"] == f"body-{index}"
        docs = await database[refs[0].collection].find({}).to_list(length=None)
        assert sum(doc["message_count"] for doc in docs) == 24
        assert all(doc["message_count"] <= 3 for doc in docs)
        duplicate_refs = await asyncio.gather(*(append(24) for _ in range(24)))
        assert len(set(duplicate_refs)) == 1
        docs = await database[refs[0].collection].find({}).to_list(length=None)
        assert sum(doc["message_count"] for doc in docs) == 25
        assert all(doc["message_count"] <= 3 for doc in docs)
        for doc in docs:
            assert [message["seq"] for message in doc["messages"]] == list(range(1, doc["message_count"] + 1))
        # A restarted worker has no local repository state, including index cache.
        repo = ChatBucketRepository(database, max_bucket_messages=3)
        assert await asyncio.gather(*(append(index) for index in range(24))) == refs
        docs = await database[refs[0].collection].find({}).to_list(length=None)
        assert sum(doc["message_count"] for doc in docs) == 25
    finally:
        await client.drop_database(name)
        await client.close()
