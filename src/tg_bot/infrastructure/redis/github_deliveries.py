"""Redis ownership for GitHub delivery leases and PR message coordinates.

All state-changing Lua operations validate the random owner token. A lease is
longer than the bounded Telegram request; Redis cannot fence Telegram itself.
"""

from hashlib import sha256
from typing import Any
from uuid import uuid4

from redis.asyncio import Redis

LEASE_SECONDS = 60
DELIVERY_TTL = 7 * 24 * 3600
ENTITY_TTL = 180 * 24 * 3600

_CLAIM = """
if redis.call('GET', KEYS[1]) == 'done' then return 2 end
if redis.call('EXISTS', KEYS[1]) == 1 or redis.call('EXISTS', KEYS[2]) == 1 then return 0 end
redis.call('SET', KEYS[1], ARGV[1], 'EX', ARGV[2])
redis.call('SET', KEYS[2], ARGV[1], 'EX', ARGV[2])
return 1
"""
_COMMIT = """
if redis.call('GET', KEYS[1]) ~= ARGV[1] or redis.call('GET', KEYS[2]) ~= ARGV[1] then return 0 end
if ARGV[2] ~= '' then
  redis.call('HSET', KEYS[3], 'message_id', ARGV[2], 'version', ARGV[3], 'merged', ARGV[4])
  redis.call('EXPIRE', KEYS[3], ARGV[6])
end
redis.call('SET', KEYS[1], 'done', 'EX', ARGV[5])
redis.call('DEL', KEYS[2])
return 1
"""
_RELEASE = """
for _, key in ipairs(KEYS) do
  if redis.call('GET', key) == ARGV[1] then redis.call('DEL', key) end
end
return 1
"""
_OWNS = """
if redis.call('GET', KEYS[1]) == ARGV[1] and redis.call('GET', KEYS[2]) == ARGV[1] then return 1 end
return 0
"""


class DeliveryLease:
    def __init__(self, redis: Redis, namespace: str, delivery: str, entity: str) -> None:
        prefix = f"tg:github:{sha256(namespace.encode()).hexdigest()[:16]}:"
        # redis-py 5 mixes sync/async command annotations; the runtime client is
        # exclusively redis.asyncio.Redis, supplied by the codex_bot runner.
        self.redis: Any = redis
        self.delivery_key = prefix + "delivery:" + sha256(delivery.encode()).hexdigest()
        self.entity_key = prefix + "entity:" + sha256((entity or delivery).encode()).hexdigest()
        self.lock_key = self.entity_key + ":lock"
        self.token = uuid4().hex

    async def claim(self) -> int:
        """0 busy, 1 owned, 2 already committed."""
        return int(await self.redis.eval(_CLAIM, 2, self.delivery_key, self.lock_key, self.token, LEASE_SECONDS))

    async def entity_state(self) -> dict[str, int]:
        raw = await self.redis.hgetall(self.entity_key)
        return {(key.decode() if isinstance(key, bytes) else key): int(value) for key, value in raw.items()}

    async def owns(self) -> bool:
        return bool(await self.redis.eval(_OWNS, 2, self.delivery_key, self.lock_key, self.token))

    async def commit(self, message_id: int | None = None, version: int = 0, merged: bool = False) -> None:
        result = await self.redis.eval(
            _COMMIT,
            3,
            self.delivery_key,
            self.lock_key,
            self.entity_key,
            self.token,
            str(message_id) if message_id else "",
            version,
            int(merged),
            DELIVERY_TTL,
            ENTITY_TTL,
        )
        if not result:
            raise RuntimeError("GitHub delivery lease lost before commit")

    async def release(self) -> None:
        await self.redis.eval(_RELEASE, 2, self.delivery_key, self.lock_key, self.token)
