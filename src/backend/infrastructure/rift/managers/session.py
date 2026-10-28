"""Retired node Rift storage boundary; original implementation is archived."""

from typing import Any

from src.backend.features.rift.retirement import LegacyRiftRetiredError


class RiftRunSessionNotFoundError(RuntimeError):
    pass


class RiftRunSessionStore:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def build_session_key(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def create_session(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def save_session(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def get_session(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def require_session(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def set_position(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def set_visited(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def set_discovered(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def start_travel(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def interrupt_travel(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def complete_travel(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def set_active_encounter(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def clear_active_encounter(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def mark_dirty(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def clear_dirty(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def scan_dirty(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def list_by_instance(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def delete_session(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()
