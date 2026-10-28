"""Retired node Rift storage boundary; original implementation is archived."""

from typing import Any

from src.backend.features.rift.retirement import LegacyRiftRetiredError


class RiftInstanceNotFoundError(RuntimeError):
    pass


class RiftInstanceStore:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def build_instance_key(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def save_instance(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def get_instance(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def exists(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def require_instance(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def patch_node_event(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def mark_node_cleared(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def set_gate_state(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def set_heart_state(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()
