"""Retired node Rift storage boundary; original implementation is archived."""

from typing import Any

from src.backend.features.rift.retirement import LegacyRiftRetiredError


class UnsupportedRiftSnapshotSchemaError(RuntimeError):
    pass


class RiftRuntimeSnapshotRepository:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    async def ensure_indexes(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def upsert_snapshot(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def get_snapshot(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()
