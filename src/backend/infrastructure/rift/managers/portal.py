"""Retired node Rift storage boundary; original implementation is archived."""

from typing import Any

from src.backend.features.rift.retirement import LegacyRiftRetiredError


class RiftPortalStore:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def build_portal_key(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def save_portal(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def get_portal(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def find_by_rift_session(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def mark_status(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def scan(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def archive_due(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()
