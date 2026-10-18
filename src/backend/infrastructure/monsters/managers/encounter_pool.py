"""Ephemeral, fenced Redis storage for lazily prepared encounter pools."""

import asyncio
from collections.abc import Awaitable, Callable
from contextlib import suppress
from hashlib import sha256
from inspect import isawaitable
from time import monotonic
from uuid import uuid4

from redis.exceptions import RedisError


class EncounterPoolCacheUnavailable(RuntimeError):  # noqa: N818 - public availability signal
    """Redis is unavailable or a builder did not finish within the wait limit."""


class EncounterPoolCacheManager:
    TTL_SECONDS = 86400
    _RELEASE = "if redis.call('get',KEYS[1]) == ARGV[1] then return redis.call('del',KEYS[1]) end return 0"
    _RENEW = "if redis.call('get',KEYS[1]) == ARGV[1] then return redis.call('pexpire',KEYS[1],ARGV[2]) end return 0"
    _EVICT = "if redis.call('get',KEYS[1]) == ARGV[1] then return redis.call('del',KEYS[1]) end return 0"
    _PUBLISH = """
if redis.call('get',KEYS[1]) ~= ARGV[1] then return 0 end
redis.call('set',KEYS[2],ARGV[2],'EX',ARGV[3])
redis.call('del',KEYS[1])
return 1
"""

    def __init__(self, redis, *, namespace="game:monsters:encounter-pool:v1", wait_seconds=30.0, lease_ms=30000):
        self.client = redis.string.client
        self.namespace = namespace
        self.wait_seconds = wait_seconds
        self.lease_ms = lease_ms

    def keys(self, identity: str) -> tuple[str, str]:
        digest = sha256(identity.encode()).hexdigest()
        # Shared hash tag permits the fenced publish on Redis Cluster too.
        base = f"{self.namespace}:{{{digest}}}"
        return f"{base}:value", f"{base}:lock"

    async def _call(self, awaitable):
        try:
            async with asyncio.timeout(2):
                return await awaitable
        except (RedisError, TimeoutError, OSError) as exc:
            raise EncounterPoolCacheUnavailable("Monster encounter pool cache is unavailable") from exc

    async def get_or_build(
        self,
        identity: str,
        build: Callable[[], Awaitable[str]],
        valid: Callable[[str], bool],
    ) -> tuple[str, str]:
        value_key, lock_key = self.keys(identity)
        deadline = monotonic() + self.wait_seconds
        waited = False
        while monotonic() < deadline:
            raw = await self._call(self.client.get(value_key))
            if raw is not None:
                if isinstance(raw, bytes):
                    raw = raw.decode()
                if await self._valid(valid, raw):
                    return raw, "wait" if waited else "hit"
                await self._call(self.client.eval(self._EVICT, 1, value_key, raw))
            token = uuid4().hex
            acquired = await self._call(self.client.set(lock_key, token, nx=True, px=self.lease_ms))
            if not acquired:
                waited = True
                await asyncio.sleep(0.025)
                continue
            renew = asyncio.create_task(self._renew(lock_key, token))
            try:
                # A preceding builder can publish between GET and SET NX.
                existing = await self._call(self.client.get(value_key))
                if existing is not None:
                    existing = existing.decode() if isinstance(existing, bytes) else existing
                    if await self._valid(valid, existing):
                        return existing, "wait"
                payload = await build()
                if not await self._valid(valid, payload):
                    raise ValueError("Builder produced an invalid monster pool")
                published = await self._call(
                    self.client.eval(self._PUBLISH, 2, lock_key, value_key, token, payload, self.TTL_SECONDS)
                )
                if published:
                    return payload, "miss"
                waited = True
            finally:
                renew.cancel()
                with suppress(asyncio.CancelledError, EncounterPoolCacheUnavailable):
                    await renew
                # Shield cleanup from request cancellation; token fencing prevents
                # deleting a lease that has already been reassigned.
                with suppress(EncounterPoolCacheUnavailable):
                    await asyncio.shield(self._call(self.client.eval(self._RELEASE, 1, lock_key, token)))
        raise EncounterPoolCacheUnavailable("Monster encounter pool cache build timed out")

    @staticmethod
    async def _valid(valid, raw):
        result = valid(raw)
        return await result if isawaitable(result) else result

    async def _renew(self, lock_key: str, token: str) -> None:
        while True:
            await asyncio.sleep(self.lease_ms / 3000)
            if not await self._call(self.client.eval(self._RENEW, 1, lock_key, token, self.lease_ms)):
                return
