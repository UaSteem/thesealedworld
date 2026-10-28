"""Historical event names; legacy Rift has no active event handlers."""

from src.backend.core.bus import GameStreamRouter

router = GameStreamRouter()


class RiftEvents:
    ENTRY_REQUESTED = "rift.entry_requested"


def bind(app: object) -> None:
    """Retained import boundary; no runtime is bound."""


__all__ = ["RiftEvents", "bind", "router"]
