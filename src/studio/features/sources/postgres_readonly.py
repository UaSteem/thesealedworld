"""Per-source read-only Postgres pool factory.

Holds one `asyncpg.Pool` per `SourceKind` and lazily creates it on first
request. Pools are closed in the FastAPI shutdown handler.

Every source pool uses server-side default_transaction_read_only and every
acquired connection runs inside an explicit read-only transaction. A restricted
facade exposes fetch methods only. Actual server-role grants remain operational
configuration and have not been inspected or changed here.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    from src.studio.features.sources.models import Source, SourceKind


class ReadOnlyConnection:
    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def _validate(self, query: str) -> None:
        normalized = query.strip().rstrip(";")
        if (
            not normalized
            or ";" in normalized
            or normalized.split(maxsplit=1)[0].upper() not in {"SELECT", "WITH", "EXPLAIN", "SHOW"}
        ):
            raise PermissionError("Studio PostgreSQL exposes analytical reads only")

    async def fetch(self, query: str, *args: Any, **kwargs: Any) -> Any:
        self._validate(query)
        return await self._connection.fetch(query, *args, **kwargs)

    async def fetchrow(self, query: str, *args: Any, **kwargs: Any) -> Any:
        self._validate(query)
        return await self._connection.fetchrow(query, *args, **kwargs)

    async def fetchval(self, query: str, *args: Any, **kwargs: Any) -> Any:
        self._validate(query)
        return await self._connection.fetchval(query, *args, **kwargs)


class ReadOnlyPostgresPool:
    def __init__(self, pool: Any) -> None:
        self._pool = pool

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[ReadOnlyConnection]:
        async with self._pool.acquire() as connection, connection.transaction(readonly=True):
            yield ReadOnlyConnection(connection)

    async def close(self) -> None:
        await self._pool.close()


class PostgresPoolRegistry:
    """Lazy pool-per-source registry, lifetime-bound to the FastAPI app.

    Lives on `app.state.pg_pools`. Repository code does:

        pool = await app.state.pg_pools.get(request.state.source)
        async with pool.acquire() as conn:
            ...
    """

    def __init__(self) -> None:
        self._pools: dict[SourceKind, ReadOnlyPostgresPool] = {}

    async def get(self, source: Source) -> ReadOnlyPostgresPool:
        import asyncpg

        existing = self._pools.get(source.kind)
        if existing is not None:
            return existing

        logger.bind(source=source.kind, dsn_host=_host_of(source.pg_dsn)).info("StudioPgPoolCreating")
        pool = await asyncpg.create_pool(
            dsn=source.pg_dsn,
            min_size=1,
            max_size=5,
            command_timeout=30.0,
            server_settings={"default_transaction_read_only": "on"},
        )
        wrapped = ReadOnlyPostgresPool(pool)
        self._pools[source.kind] = wrapped
        return wrapped

    async def close_all(self) -> None:
        for kind, pool in list(self._pools.items()):
            logger.bind(source=kind).info("StudioPgPoolClosing")
            try:
                await pool.close()
            except Exception:  # noqa: BLE001
                logger.bind(source=kind).opt(exception=True).warning("StudioPgPoolCloseFailed")
            self._pools.pop(kind, None)


def _host_of(dsn: str) -> str:
    """Extract host:port from a Postgres DSN for safe logging."""
    try:
        after_at = dsn.split("@", 1)[1]
        return after_at.split("/", 1)[0]
    except (IndexError, ValueError):
        return "?"
