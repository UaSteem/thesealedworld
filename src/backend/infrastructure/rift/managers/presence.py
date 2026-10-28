"""Retired node Rift storage boundary; original implementation is archived."""

from typing import Any

from src.backend.features.rift.retirement import LegacyRiftRetiredError


class RiftPresenceStore:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def build_node_key(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    def build_travel_key(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    def build_encounter_key(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def enter_node(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def leave_node(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def move_node(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def get_node_occupants(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def join_travel(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def leave_travel(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def get_travel_participants(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def join_encounter(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def leave_encounter(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def get_encounter_participants(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def clear_node_presence(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def clear_travel_presence(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def clear_encounter_presence(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def snapshot_instance_presence(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def rebuild_node_presence_from_sessions(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()
