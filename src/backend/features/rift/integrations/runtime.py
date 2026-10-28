"""Retirement facade: no storage construction or legacy gameplay execution."""

from typing import Any

from src.backend.features.rift.retirement import LEGACY_RIFT_RETIRED_DETAIL, LegacyRiftRetiredError


class RiftRuntimeNotFoundError(RuntimeError):
    pass


class RiftRuntimeIntegration:
    def __init__(self, **wiring: Any) -> None:
        # Accept existing injection during the caller retirement transition.
        pass

    async def save_instance(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def save_instance_runtime(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def require_instance(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def patch_node_event(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def mark_node_cleared(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def set_gate_state(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def set_heart_state(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def create_run_session(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def create_portal(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def mark_portal_status(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def mark_portal_status_by_session(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def archive_due_portals(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def save_run_session(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def save_run_session_runtime(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def get_run_session(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def require_run_session(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def flush_runtime_snapshot(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def restore_participant_rift(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def restore_rift_instance(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def scan_dirty_run_sessions(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def flush_dirty_run_session(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def set_run_position(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def set_run_visited(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def set_run_discovered(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def start_run_travel(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def interrupt_run_travel(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def complete_run_travel(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def set_run_active_encounter(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def clear_run_active_encounter(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def delete_run_session(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def abandon_run_for_deleted_character(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def apply_combat_result(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def enter_node_presence(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def leave_node_presence(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def move_presence(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def get_node_occupants(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def join_transition_travel(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def leave_transition_travel(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def get_transition_travel_participants(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def join_transition_encounter(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def leave_transition_encounter(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def get_transition_encounter_participants(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def clear_node_presence(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def clear_transition_travel_presence(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)

    async def clear_transition_encounter_presence(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError(LEGACY_RIFT_RETIRED_DETAIL)
