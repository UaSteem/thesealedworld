"""Per-source read-only Redis client factory.

Holds one `redis.asyncio.Redis` per `SourceKind`, lazily constructed.
Closed in the FastAPI shutdown handler.

The wrapper allowlists analytical commands and exposes no mutators/pipelines.
Server-side least-privilege credentials remain an operational requirement;
this factory does not inspect or change existing Redis ACLs.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    from src.studio.features.sources.models import Source, SourceKind


class ReadOnlyRedis:
    """Allow only analytical Redis commands; never expose pipeline/raw client."""

    _COMMANDS = frozenset(
        {
            "GET",
            "MGET",
            "EXISTS",
            "TYPE",
            "TTL",
            "PTTL",
            "STRLEN",
            "HGET",
            "HMGET",
            "HGETALL",
            "HLEN",
            "HKEYS",
            "HVALS",
            "SCAN",
            "SSCAN",
            "HSCAN",
            "ZSCAN",
            "SCARD",
            "SMEMBERS",
            "SISMEMBER",
            "LRANGE",
            "LLEN",
            "ZRANGE",
            "ZREVRANGE",
            "ZCARD",
            "ZSCORE",
            "XRANGE",
            "XREVRANGE",
            "XLEN",
            "XINFO",
            "XPENDING",
            "JSON.GET",
            "JSON.MGET",
            "JSON.TYPE",
            "JSON.OBJKEYS",
            "JSON.OBJLEN",
            "JSON.ARRLEN",
            "PING",
            "INFO",
            "DBSIZE",
            "TIME",
        }
    )

    def __init__(self, client: Any) -> None:
        self._client = client

    async def execute_command(self, command: str, *args: Any, **kwargs: Any) -> Any:
        if command.upper() not in self._COMMANDS:
            raise PermissionError("Studio Redis mutation denied")
        return await self._client.execute_command(command, *args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        command = name.upper()
        if command not in self._COMMANDS:
            raise AttributeError("Studio Redis exposes read commands only")

        async def read(*args: Any, **kwargs: Any) -> Any:
            method = getattr(self._client, name, None)
            if callable(method):
                return await method(*args, **kwargs)
            return await self.execute_command(command, *args, **kwargs)

        return read

    def json(self) -> ReadOnlyRedisJson:
        return ReadOnlyRedisJson(self)

    async def aclose(self) -> None:
        await self._client.aclose()


class ReadOnlyRedisJson:
    def __init__(self, client: ReadOnlyRedis) -> None:
        self._client = client

    async def get(self, name: str, *paths: str) -> Any:
        value = await self._client.execute_command("JSON.GET", name, *paths)
        return json.loads(value) if isinstance(value, (str, bytes)) else value


class RedisClientRegistry:
    """Lazy client-per-source registry, lifetime-bound to the FastAPI app.

    Lives on `app.state.redis_clients`. Repository code does:

        client = await app.state.redis_clients.get(request.state.source)
        value = await client.get("game:metrics:online")
    """

    def __init__(self) -> None:
        self._clients: dict[SourceKind, ReadOnlyRedis] = {}

    async def get(self, source: Source) -> ReadOnlyRedis:
        from redis.asyncio import Redis as AsyncRedis

        existing = self._clients.get(source.kind)
        if existing is not None:
            return existing

        logger.bind(source=source.kind).info("StudioRedisClientCreating")
        client = ReadOnlyRedis(AsyncRedis.from_url(source.redis_url, decode_responses=True))
        self._clients[source.kind] = client
        return client

    async def close_all(self) -> None:
        for kind, client in list(self._clients.items()):
            logger.bind(source=kind).info("StudioRedisClientClosing")
            try:
                await client.aclose()
            except Exception:  # noqa: BLE001
                logger.bind(source=kind).opt(exception=True).warning("StudioRedisClientCloseFailed")
            self._clients.pop(kind, None)
