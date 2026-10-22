"""Preserve abandoned deliveries without replaying effects of unknown outcome.

Quarantine is an operator reconciliation queue, not an automatic retry queue.
Even a live, unusually slow handler may finish after its delivery is quarantined.
The source stream and quarantine must not be trimmed without reconciliation.
"""

from collections.abc import Awaitable
from typing import Any, cast

from codex_platform.streams import StreamRuntime, StreamRuntimeConfig
from codex_platform.streams.dispatcher import RetrySchedulerProtocol
from codex_platform.streams.processor import StreamStorageProtocol
from loguru import logger
from redis.asyncio import Redis

_QUARANTINE = """
local pending = redis.call('XPENDING', KEYS[1], ARGV[1], ARGV[2], ARGV[2], 1)
if #pending == 0 or pending[1][3] < tonumber(ARGV[3]) then return 0 end
local entry = redis.call('XRANGE', KEYS[1], ARGV[2], ARGV[2])
local payload = {}
local reason = 'delivery_outcome_unknown'
if #entry == 0 then
    reason = 'payload_missing'
else
    local fields = entry[1][2]
    for i = 1, #fields, 2 do payload[fields[i]] = fields[i + 1] end
end
local record = cjson.encode({source_stream=KEYS[1], source_group=ARGV[1],
    source_id=ARGV[2], source_consumer=pending[1][2], delivery_count=pending[1][4],
    reason=reason, payload=payload})
-- Redis scripts do not roll back earlier writes on command errors. HSETNX
-- makes a retry after a failed XACK preserve the original quarantine record.
redis.call('HSETNX', KEYS[2], ARGV[2], record)
redis.call('XACK', KEYS[1], ARGV[1], ARGV[2])
return 1
"""


class PendingQuarantineStorage:
    """Bounded PEL sweep before each normal read; never dispatch recovered data."""

    def __init__(
        self,
        client: Redis,
        delegate: StreamStorageProtocol,
        *,
        min_idle_ms: int,
        scan_count: int = 100,
    ) -> None:
        if min_idle_ms <= 0 or scan_count <= 0:
            raise ValueError("Pending quarantine idle time and scan count must be positive")
        self.client = client
        self.delegate = delegate
        self.min_idle_ms = min_idle_ms
        self.scan_count = scan_count
        self._cursor = "-"

    async def create_group(self, stream_name: str, group_name: str) -> None:
        await self.delegate.create_group(stream_name, group_name)

    async def ack_event(self, stream_name: str, group_name: str, message_id: str) -> None:
        await self.delegate.ack_event(stream_name, group_name, message_id)

    async def read_events(
        self,
        stream_name: str,
        group_name: str,
        consumer_name: str,
        count: int,
        block_ms: int | None = 1000,
    ) -> list[tuple[str, dict[str, Any]]]:
        try:
            await self.quarantine_pending(stream_name, group_name)
        except Exception as exc:
            # Do not log exception messages: Redis errors may echo payloads.
            logger.bind(stream=stream_name, group=group_name, error_type=type(exc).__name__).error(
                "StreamPendingScanFailed"
            )
        return await self.delegate.read_events(stream_name, group_name, consumer_name, count, block_ms)

    async def quarantine_pending(self, stream_name: str, group_name: str) -> int:
        pending = await self.client.xpending_range(
            stream_name, group_name, min=self._cursor, max="+", count=self.scan_count
        )
        moved = 0
        for delivery in pending:
            message_id = str(delivery["message_id"])
            # Advance even on write failure, so a broken entry cannot starve the tail.
            self._cursor = f"({message_id}"
            try:
                result = await cast(
                    "Awaitable[Any]",
                    self.client.eval(
                        _QUARANTINE,
                        2,
                        stream_name,
                        f"{stream_name}:quarantine:{group_name}",
                        group_name,
                        message_id,
                        str(self.min_idle_ms),
                    ),
                )
                moved += int(result)
            except Exception as exc:
                logger.bind(
                    stream=stream_name, group=group_name, message_id=message_id, error_type=type(exc).__name__
                ).error("StreamPendingQuarantineFailed")
        if len(pending) < self.scan_count:
            self._cursor = "-"
        if moved:
            logger.bind(stream=stream_name, group=group_name, count=moved).warning("StreamPendingQuarantined")
        return moved


class GameStreamRuntime(StreamRuntime):
    """Keep library dispatch/ACK semantics and add a project-owned storage adapter."""

    def __init__(
        self,
        redis: Redis,
        config: StreamRuntimeConfig,
        *,
        min_idle_ms: int = 300_000,
        scan_count: int = 100,
        retry_scheduler: RetrySchedulerProtocol | None = None,
    ) -> None:
        super().__init__(redis, config, retry_scheduler=retry_scheduler)
        self.processor.storage = PendingQuarantineStorage(
            self.redis, self.consumer, min_idle_ms=min_idle_ms, scan_count=scan_count
        )
