from __future__ import annotations

import inspect

from src.backend.features.rift.api import hex_test_router
from src.backend.features.rift.runtime.hex.generation.builder import HexRiftStateDTO
from src.backend.features.rift.services import hex_runtime_service
from src.backend.features.rift.services.hex_runtime_service import HexRiftRuntimeService


def test_hex_runtime_service_starts_state_from_new_hex_generation_layer() -> None:
    service = HexRiftRuntimeService()

    state = service.start(
        instance_id="hex-runtime-service",
        seed="hex-runtime-service-seed",
        scale_key="solo",
        difficulty_key="easy",
        scheme_key="flower_weave",
    )

    assert isinstance(state, HexRiftStateDTO)
    assert service.get("hex-runtime-service") is state
    assert state.scheme_key == "flower_weave"
    assert state.layout_template_debug["geometry_pattern"] == "spike_comb"


def test_hex_runtime_service_retries_auto_seed_when_layout_attempt_fails(monkeypatch) -> None:
    service = HexRiftRuntimeService()
    original_build = hex_runtime_service.build_hex_rift_state
    attempts = 0

    def flaky_build(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("Could not build rift graph for scheme 'side_spurs'")
        return original_build(
            args[0],
            args[1],
            scale_key="solo",
            difficulty_key="easy",
            scheme_key="flower_weave",
        )

    monkeypatch.setattr(hex_runtime_service, "build_hex_rift_state", flaky_build)

    state = service.start(
        instance_id="hex-runtime-auto-retry",
        seed=None,
        scale_key="group",
        difficulty_key="easy",
        scheme_key="side_spurs",
    )

    assert isinstance(state, HexRiftStateDTO)
    assert attempts == 2
    assert service.get("hex-runtime-auto-retry") is state


def test_hex_runtime_service_moves_only_to_neighbor_walkable_node() -> None:
    service = HexRiftRuntimeService()
    state = service.start(
        instance_id="hex-runtime-move",
        seed="hex-runtime-move-seed",
        scale_key="solo",
        difficulty_key="easy",
        scheme_key="flower_weave",
    )
    current = (state.current_x, state.current_y)
    target = next(
        node
        for node in state.nodes
        if node.is_walkable
        and node.x != state.current_x
        and node.y != state.current_y
        and sum(node.edges) > 0
        and current in service.neighbors(node.x, node.y, state.width, state.height)
    )

    moved = service.move("hex-runtime-move", target_x=target.x, target_y=target.y)

    assert moved.current_x == target.x
    assert moved.current_y == target.y
    assert current == (moved.previous_x, moved.previous_y)
    assert (target.x, target.y) in moved.visited


def test_hex_runtime_service_client_view_hides_unrevealed_nodes_until_requested() -> None:
    service = HexRiftRuntimeService()
    state = service.start(
        instance_id="hex-runtime-client-view",
        seed="hex-runtime-client-view-seed",
        scale_key="solo",
        difficulty_key="easy",
        scheme_key="flower_weave",
    )

    hidden_view = service.client_view(state)
    full_view = service.client_view(state, show_all_map=True)

    assert len(hidden_view.nodes) == len(set(state.revealed))
    assert len(hidden_view.nodes) < len(state.nodes)
    assert {(node.x, node.y) for node in hidden_view.nodes} == set(state.revealed)
    assert full_view is state
    assert len(full_view.nodes) == len(state.nodes)


def test_hex_dev_router_is_thin_over_runtime_service() -> None:
    source = inspect.getsource(hex_test_router)

    assert "HexRiftRuntimeService" in source
    assert "build_hex_rift_state(" not in source
    assert "get_hex_neighbors(" not in source
