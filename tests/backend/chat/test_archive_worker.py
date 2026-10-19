import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.backend.chat.workers import archive


@pytest.mark.asyncio
async def test_cursor_stops_before_failed_message_and_retries(monkeypatch):
    redis = SimpleNamespace(
        scan=AsyncMock(return_value=(0, ["chat:buffer:global"])), get=AsyncMock(return_value="0-0"), set=AsyncMock()
    )
    records = [
        ("1-0", {"data": "bad private payload"}),
        ("2-0", {"data": json.dumps({"content": "first"})}),
        ("3-0", {"data": json.dumps({"content": "second"})}),
    ]
    redis.xread = AsyncMock(return_value=[("chat:buffer:global", records)])
    store = AsyncMock(side_effect=["write_failed", "stored", "stored"])
    monkeypatch.setattr(archive, "get_mongo_provider", lambda: SimpleNamespace(database=lambda: None))
    monkeypatch.setattr(archive, "_archive_payload", store)
    await archive.archive_chat_buffers({"redis": redis})
    redis.set.assert_awaited_once_with("chat:archive:cursor:chat:buffer:global", "1-0")
    first = store.call_args.args[0].copy()
    redis.get.return_value = "1-0"
    redis.xread.return_value = [("chat:buffer:global", records[1:])]
    await archive.archive_chat_buffers({"redis": redis})
    assert store.call_args_list[1].args[0] == first
    assert redis.set.await_args.args[1] == "3-0"


@pytest.mark.asyncio
async def test_exception_on_first_record_does_not_advance_cursor(monkeypatch):
    redis = SimpleNamespace(
        scan=AsyncMock(return_value=(0, ["chat:buffer:global"])),
        get=AsyncMock(return_value="0-0"),
        set=AsyncMock(),
        xread=AsyncMock(return_value=[("chat:buffer:global", [("1-0", {"data": "{}"})])]),
    )
    monkeypatch.setattr(archive, "get_mongo_provider", lambda: SimpleNamespace(database=lambda: None))
    monkeypatch.setattr(archive, "_archive_payload", AsyncMock(side_effect=RuntimeError("offline")))
    await archive.archive_chat_buffers({"redis": redis})
    redis.set.assert_not_awaited()


@pytest.mark.asyncio
async def test_malformed_entries_skip_without_logging_the_payload(monkeypatch):
    from loguru import logger

    records = []
    sink = logger.add(lambda message: records.append(message.record), format="{message}")
    redis = SimpleNamespace(
        scan=AsyncMock(return_value=(0, ["chat:buffer:global"])),
        get=AsyncMock(return_value="0-0"),
        set=AsyncMock(),
        xread=AsyncMock(
            return_value=[
                ("chat:buffer:global", [("1-0", {"data": "private malformed content"}), ("2-0", {"data": "[]"})])
            ]
        ),
    )
    monkeypatch.setattr(archive, "get_mongo_provider", lambda: SimpleNamespace(database=lambda: None))
    store = AsyncMock()
    monkeypatch.setattr(archive, "_archive_payload", store)
    try:
        await archive.archive_chat_buffers({"redis": redis})
    finally:
        logger.remove(sink)
    store.assert_not_awaited()
    redis.set.assert_awaited_once_with("chat:archive:cursor:chat:buffer:global", "2-0")
    warnings = [row for row in records if row["message"] == "ChatBufferMalformedEntrySkipped"]
    assert len(warnings) == 2
    assert all(row["exception"] is None and "private" not in str(row["extra"]) for row in warnings)


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["flush", "commit"])
async def test_mongo_success_sql_rollback_replays_same_thread_and_body(monkeypatch, failure):
    from contextlib import asynccontextmanager
    from uuid import uuid4

    from src.backend.infrastructure.mongo.chat_buckets import ChatBucketRef

    durable = {"thread": None, "index": None}
    fail_once = True
    bodies = {}

    @asynccontextmanager
    async def session_context():
        nonlocal fail_once
        session = SimpleNamespace(thread=durable["thread"], index=None)
        yield session
        if session.index is not None and fail_once and failure == "commit":
            fail_once = False
            raise RuntimeError("SQL commit failed")
        durable["thread"] = session.thread
        if session.index is not None:
            durable["index"] = session.index

    class Repository:
        def __init__(self, session):
            self.session = session

        async def get_or_create_thread(self, **kwargs):
            if self.session.thread is None:
                self.session.thread = SimpleNamespace(id=uuid4())
            return self.session.thread

        async def add_message_index(self, **kwargs):
            nonlocal fail_once
            if fail_once and failure == "flush":
                fail_once = False
                raise RuntimeError("SQL flush failed")
            self.session.index = kwargs

    async def append(**kwargs):
        # Mongo is externally committed and cannot be undone by SQL rollback.
        key = (kwargs["thread_id"], kwargs["message"]["id"])
        bodies.setdefault(key, ChatBucketRef("chat_world_buckets", f"bucket:{key[0]}", 1))
        return bodies[key]

    monkeypatch.setattr(archive, "get_session_context", session_context)
    monkeypatch.setattr(archive, "ChatThreadRepository", Repository)
    mongo = SimpleNamespace(append_message=AsyncMock(side_effect=append))
    payload = {
        "id": str(uuid4()),
        "sender_id": str(uuid4()),
        "channel": "global",
        "content": "persist me",
        "created_at": "2026-06-04T10:03:00+00:00",
    }
    with pytest.raises(RuntimeError, match=f"SQL {failure} failed"):
        await archive._archive_payload(payload, mongo_repo=mongo)
    assert durable["thread"] is not None
    assert durable["index"] is None
    assert await archive._archive_payload(payload, mongo_repo=mongo) == "stored"
    assert len(bodies) == 1
    ref = next(iter(bodies.values()))
    assert durable["index"]["mongo_bucket_id"] == ref.bucket_id
    assert durable["index"]["bucket_seq"] == ref.seq
    assert mongo.append_message.await_count == 2
