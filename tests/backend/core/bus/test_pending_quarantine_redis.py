"""Opt-in tests using a disposable Redis, never application connection settings.

Run with RUN_STREAM_RECOVERY_REDIS_TESTS=1 and Docker available. No volumes,
random loopback port, no persistence, unique container, unconditional cleanup.
"""

import asyncio
import json
import os
import subprocess
import time
import uuid
from unittest.mock import AsyncMock

import pytest
import redis as sync_redis
import redis.asyncio as redis
from codex_platform.streams import StreamRuntimeConfig

from src.backend.core.bus.producer import GameEventProducer
from src.backend.core.bus.recovery import GameStreamRuntime, PendingQuarantineStorage
from src.backend.realtime.integrations.notice_publisher import RawStreamNoticeProducer

_service_opt_in = pytest.mark.skipif(
    os.environ.get("RUN_STREAM_RECOVERY_REDIS_TESTS") != "1",
    reason="Set RUN_STREAM_RECOVERY_REDIS_TESTS=1 for disposable Docker Redis tests",
)
pytestmark = [_service_opt_in, pytest.mark.external]


@pytest.fixture(scope="module")
def isolated_redis_url():
    name = f"tbmmorpg-stream-recovery-test-{uuid.uuid4().hex}"
    try:
        subprocess.run(
            [
                "docker",
                "run",
                "--detach",
                "--name",
                name,
                "--publish",
                "127.0.0.1::6379",
                "redis:7-alpine",
                "redis-server",
                "--save",
                "",
                "--appendonly",
                "no",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        endpoint = subprocess.run(
            ["docker", "port", name, "6379/tcp"], check=True, capture_output=True, text=True, timeout=15
        ).stdout.strip()
        url = f"redis://{endpoint}/0"
        with sync_redis.Redis.from_url(url, socket_connect_timeout=1, socket_timeout=1) as client:
            for attempt in range(40):
                try:
                    client.ping()
                    break
                except sync_redis.ConnectionError:
                    if attempt == 39:
                        raise
                    time.sleep(0.1)
        yield url
    finally:
        subprocess.run(["docker", "rm", "--force", name], capture_output=True, timeout=20, check=False)


@pytest.fixture
async def client(isolated_redis_url):
    async with redis.Redis.from_url(isolated_redis_url, decode_responses=True) as connection:
        yield connection


async def pending(client, stream, group="game"):
    await client.xgroup_create(stream, group, "0", mkstream=True)
    message_id = await client.xadd(stream, {"type": "reward", "payload": "private-payload"})
    await client.xreadgroup(group, "crashed-worker", {stream: ">"})
    await client.xclaim(stream, group, "crashed-worker", 0, [message_id], idle=10_000)
    return message_id


@pytest.mark.asyncio
@pytest.mark.parametrize("after_effect", [False, True])
async def test_crash_recovery_never_replays_effect(client, after_effect):
    stream = f"events:{uuid.uuid4().hex}"
    message_id = await pending(client, stream)
    effects = f"{stream}:effects"
    if after_effect:
        await client.incr(effects)
    runtime = GameStreamRuntime(client, StreamRuntimeConfig(stream, "game", "restarted"), min_idle_ms=100)
    callback = AsyncMock()
    runtime.processor.set_callback(callback)
    # Same path used by the processor after restart. Old deliveries are never returned.
    assert await runtime.processor.storage.read_events(stream, "game", "restarted", 10, None) == []
    callback.assert_not_called()
    assert int(await client.get(effects) or 0) == int(after_effect)
    assert (await client.xpending(stream, "game"))["pending"] == 0
    record = json.loads(await client.hget(f"{stream}:quarantine:game", message_id))
    assert record["source_id"] == message_id
    assert record["source_group"] == "game"
    assert record["payload"] == {"type": "reward", "payload": "private-payload"}
    assert record["reason"] == "delivery_outcome_unknown"


@pytest.mark.asyncio
@pytest.mark.parametrize("after_effect", [False, True])
async def test_runtime_cancel_restart_preserves_unknown_delivery_without_replay(client, after_effect):
    stream = f"events:{uuid.uuid4().hex}"
    entered = asyncio.Event()
    never_finish = asyncio.Event()
    effects = f"{stream}:effects"

    async def interrupted_handler(payload):
        if after_effect:
            await client.incr(effects)
        entered.set()
        await never_finish.wait()

    old = GameStreamRuntime(
        client, StreamRuntimeConfig(stream, "game", "old", block_ms=10, poll_interval=0.01), min_idle_ms=100
    )
    old.processor.set_callback(interrupted_handler)
    await old.start()
    try:
        message_id = await client.xadd(stream, {"type": "reward"})
        await asyncio.wait_for(entered.wait(), timeout=2)
    finally:
        await old.stop()
    assert (await client.xpending(stream, "game"))["pending"] == 1
    await client.xclaim(stream, "game", "old", 0, [message_id], idle=10_000)

    received = asyncio.Event()
    calls = []

    async def restarted_handler(payload):
        calls.append(payload)
        received.set()

    restarted = GameStreamRuntime(
        client, StreamRuntimeConfig(stream, "game", "new", block_ms=10, poll_interval=0.01), min_idle_ms=100
    )
    restarted.processor.set_callback(restarted_handler)
    await restarted.start()
    try:
        async with asyncio.timeout(2):
            while (await client.xpending(stream, "game"))["pending"]:
                await asyncio.sleep(0.01)
        assert calls == []
        assert int(await client.get(effects) or 0) == int(after_effect)
        assert await client.hget(f"{stream}:quarantine:game", message_id)
        await client.xadd(stream, {"type": "fresh"})
        await asyncio.wait_for(received.wait(), timeout=2)
        assert calls == [{"type": "fresh"}]
    finally:
        await restarted.stop()


@pytest.mark.asyncio
async def test_concurrent_scanners_group_isolation_and_new_delivery(client):
    stream = f"events:{uuid.uuid4().hex}"
    old_id = await pending(client, stream)
    await client.xgroup_create(stream, "other", "0")
    await client.xreadgroup("other", "worker", {stream: ">"})
    storages = [PendingQuarantineStorage(client, AsyncMock(), min_idle_ms=100) for _ in range(3)]
    assert sum(await asyncio.gather(*(item.quarantine_pending(stream, "game") for item in storages))) == 1
    assert await client.hlen(f"{stream}:quarantine:game") == 1
    assert (await client.xpending(stream, "other"))["pending"] == 1
    assert await client.xrange(stream, old_id, old_id)
    runtime = GameStreamRuntime(client, StreamRuntimeConfig(stream, "game", "new-worker"), min_idle_ms=100)
    new_id = await client.xadd(stream, {"type": "new"})
    deliveries = await runtime.processor.storage.read_events(stream, "game", "new-worker", 10, None)
    assert deliveries == [(new_id, {"type": "new"})]
    callback = AsyncMock()
    runtime.processor.set_callback(callback)
    await runtime.processor._process_one(*deliveries[0])
    callback.assert_awaited_once_with({"type": "new"})
    assert (await client.xpending(stream, "game"))["pending"] == 0


@pytest.mark.asyncio
async def test_idle_threshold_and_missing_payload_tombstone(client):
    stream = f"events:{uuid.uuid4().hex}"
    message_id = await pending(client, stream)
    storage = PendingQuarantineStorage(client, AsyncMock(), min_idle_ms=60_000)
    assert await storage.quarantine_pending(stream, "game") == 0
    assert (await client.xpending(stream, "game"))["pending"] == 1
    await client.xdel(stream, message_id)
    storage.min_idle_ms = 100
    assert await storage.quarantine_pending(stream, "game") == 1
    record = json.loads(await client.hget(f"{stream}:quarantine:game", message_id))
    assert record["reason"] == "payload_missing"
    assert record["payload"] == {}


@pytest.mark.asyncio
async def test_wrong_quarantine_type_keeps_pending_then_recovers(client):
    stream = f"events:{uuid.uuid4().hex}"
    message_id = await pending(client, stream)
    key = f"{stream}:quarantine:game"
    await client.set(key, "wrong type")
    storage = PendingQuarantineStorage(client, AsyncMock(), min_idle_ms=100)
    assert await storage.quarantine_pending(stream, "game") == 0
    assert (await client.xpending(stream, "game"))["pending"] == 1
    assert await client.xrange(stream, message_id, message_id)
    await client.delete(key)
    assert await storage.quarantine_pending(stream, "game") == 1


@pytest.mark.asyncio
async def test_ack_denial_retry_keeps_single_original_quarantine(client, isolated_redis_url):
    stream = f"events:{uuid.uuid4().hex}"
    message_id = await pending(client, stream)
    username = f"quarantine-{uuid.uuid4().hex}"
    password = uuid.uuid4().hex
    await client.execute_command("ACL", "SETUSER", username, "on", f">{password}", "~*", "+@all", "-xack")
    try:
        async with redis.Redis.from_url(
            isolated_redis_url, username=username, password=password, decode_responses=True
        ) as restricted:
            storage = PendingQuarantineStorage(restricted, AsyncMock(), min_idle_ms=100)
            assert await storage.quarantine_pending(stream, "game") == 0
            key = f"{stream}:quarantine:game"
            original = await client.hget(key, message_id)
            assert original is not None
            assert (await client.xpending(stream, "game"))["pending"] == 1
            assert await storage.quarantine_pending(stream, "game") == 0
            assert await client.hlen(key) == 1
            await client.execute_command("ACL", "SETUSER", username, "+xack")
            assert await storage.quarantine_pending(stream, "game") == 1
            assert await client.hget(key, message_id) == original
            assert (await client.xpending(stream, "game"))["pending"] == 0
    finally:
        await client.execute_command("ACL", "DELUSER", username)


@pytest.mark.asyncio
async def test_publishers_preserve_pending_and_unread_above_old_maxlen(client, monkeypatch):
    from codex_platform.streams.producer import StreamProducer

    stream = f"events:{uuid.uuid4().hex}"
    first_id = await pending(client, stream)
    await client.xgroup_create(stream, "unread", "0")
    producer = GameEventProducer(StreamProducer(client, stream), maxlen=2)
    for _ in range(150):
        await producer.publish("new", {"value": "preserve"})
    from src.backend.realtime.integrations import notice_publisher

    monkeypatch.setattr(notice_publisher.settings, "game_stream_name", stream)
    monkeypatch.setattr(notice_publisher.settings, "game_stream_maxlen", 2)
    notices = RawStreamNoticeProducer(client)
    for _ in range(150):
        await notices.publish("player.notice", {"value": "preserve"})
    assert await client.xlen(stream) == 301
    assert await client.xrange(stream, first_id, first_id)
    assert (await client.xpending(stream, "game"))["pending"] == 1
    assert len((await client.xreadgroup("unread", "worker", {stream: ">"}))[0][1]) == 301
