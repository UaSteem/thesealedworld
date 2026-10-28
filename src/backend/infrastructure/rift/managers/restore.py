"""Retired node Rift storage boundary; original implementation is archived."""

from typing import Any

from src.backend.features.rift.retirement import LegacyRiftRetiredError


class RiftRestoreLock:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def build_lock_key(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def run_once(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()
