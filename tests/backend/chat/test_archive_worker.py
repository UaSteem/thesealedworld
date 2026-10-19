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
