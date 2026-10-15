from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from src.backend.features.rift.api.hex_test_router import HEX_RIFT_INSTANCES, start_hex_rift
from src.backend.features.rift.api.router import build_rift_router, router
from src.backend.features.rift.resources.layout_presets import RIFT_LAYOUT_SCALES
from src.backend.features.rift.runtime.hex.generation.builder import RANDOM_LAYOUT_SCHEME_KEY
from src.backend.infrastructure.rift.managers import HexRiftWorldStore


@pytest.mark.unit
def test_dev_rift_router_exposes_rebuild_endpoint_without_blocker_route() -> None:
    paths = {route.path for route in router.routes}

    assert "/api/game/rift/{char_id}/view" in paths
    assert "/api/game/rift/{char_id}/leave" in paths
    assert "/api/game/rift/{char_id}/complete" in paths
    assert "/api/dev/rift/{rift_instance_id}/rebuild" in paths
    assert "/api/dev/rift/{rift_instance_id}/travel/start" in paths
    assert "/api/dev/rift/{rift_instance_id}/travel/tick" in paths
    assert "/api/dev/rift/{rift_instance_id}/action" in paths
    assert "/api/dev/rift/{rift_instance_id}/combat/resolve" not in paths
    assert "/api/dev/rift/{rift_instance_id}/node-event/resolve" not in paths
    assert "/api/dev/rift/{rift_instance_id}/move" not in paths
    assert "/api/dev/rift/{rift_instance_id}/reroll-blockers" not in paths


@pytest.mark.unit
def test_dev_rift_router_can_be_disabled_for_production() -> None:
    paths = {route.path for route in build_rift_router(enable_dev_routes=False).routes}

    assert "/api/game/rift/{char_id}/view" in paths
    assert "/api/dev/rift/starter-rift/start" not in paths
    assert "/api/dev/rift/{rift_instance_id}/rebuild" not in paths


@pytest.mark.unit
async def test_hex_dev_start_builds_state_from_backend_tile_set() -> None:
    HEX_RIFT_INSTANCES.clear()

    state = await start_hex_rift(_request(), seed="smoke")

    assert state.theme == "void_temple"
    assert state.nodes
    assert all(node.asset_path.startswith("tiles/") for node in state.nodes)
    assert state.instance_id in HEX_RIFT_INSTANCES
    assert len(state.nodes) < len(HEX_RIFT_INSTANCES[state.instance_id].nodes)


@pytest.mark.unit
async def test_hex_dev_start_can_return_full_map_for_debug() -> None:
    HEX_RIFT_INSTANCES.clear()

    state = await start_hex_rift(_request(), seed="smoke-full-map", show_all_map=True)

    assert state.instance_id in HEX_RIFT_INSTANCES
    assert len(state.nodes) == len(HEX_RIFT_INSTANCES[state.instance_id].nodes)


@pytest.mark.unit
async def test_hex_dev_start_accepts_layout_scale_key() -> None:
    HEX_RIFT_INSTANCES.clear()

    state = await start_hex_rift(
        _request(),
        seed="group-smoke",
        scale_key="group",
        difficulty_key="hard",
        scheme_key="flower_weave",
    )

    assert state.scale_key == "group"
    assert state.difficulty_key == "hard"
    assert state.width == 15
    assert state.height == 15
    assert state.layout_debug["main_path_nodes"] == 29
    assert state.layout_debug["difficulty_key"] == "hard"


@pytest.mark.unit
async def test_hex_dev_start_accepts_geometry_pattern_key() -> None:
    HEX_RIFT_INSTANCES.clear()

    state = await start_hex_rift(
        _request(),
        seed="pattern-ring-detour",
        scale_key="solo",
        pattern_key="ring_detour",
        show_all_map=True,
    )

    assert state.pattern_key == "ring_detour"
    assert state.scheme_key == "flower_weave_plus_ring"
    assert state.layout_template_debug["geometry_pattern"] == "ring_detour"
    assert "legacy_path_graph" not in state.available_pattern_keys


@pytest.mark.unit
async def test_hex_dev_start_accepts_random_layout_scheme_key() -> None:
    HEX_RIFT_INSTANCES.clear()

    states = [
        await start_hex_rift(_request(), seed=f"random-scheme-{index}", scheme_key=RANDOM_LAYOUT_SCHEME_KEY)
        for index in range(12)
    ]
    scheme_keys = {state.scheme_key for state in states}

    assert scheme_keys <= set(RIFT_LAYOUT_SCALES["solo"]["scheme_keys"])
    assert len(scheme_keys) >= 3


@pytest.mark.unit
async def test_hex_dev_group_random_scheme_uses_group_allowed_schemes() -> None:
    HEX_RIFT_INSTANCES.clear()

    states = [
        await start_hex_rift(
            _request(),
            seed=f"group-random-scheme-{index}",
            scale_key="group",
            scheme_key=RANDOM_LAYOUT_SCHEME_KEY,
        )
        for index in range(8)
    ]
    scheme_keys = {state.scheme_key for state in states}

    assert scheme_keys <= set(RIFT_LAYOUT_SCALES["group"]["random_scheme_keys"])
    assert scheme_keys == {"flower_weave"}
    assert "side_spurs" not in scheme_keys
    assert "dev_switch_gate" not in scheme_keys


@pytest.mark.unit
async def test_hex_dev_start_rejects_scheme_not_allowed_for_scale() -> None:
    HEX_RIFT_INSTANCES.clear()

    with pytest.raises(HTTPException) as exc:
        await start_hex_rift(
            _request(),
            seed="invalid-group-scheme",
            scale_key="group",
            scheme_key="side_spurs",
        )

    assert exc.value.status_code == 400
    assert "not allowed for scale 'group'" in str(exc.value.detail)


@pytest.mark.unit
async def test_hex_dev_start_persists_full_world_when_hex_store_is_available(
    fake_redis_service,
    fake_redis_client,
) -> None:
    HEX_RIFT_INSTANCES.clear()
    request = _request(hex_rift_worlds=HexRiftWorldStore(fake_redis_service))

    state = await start_hex_rift(request, seed="redis-dev-start", scheme_key="flower_weave")

    key = f"game:rift:hex_world:{state.instance_id}"
    assert key in fake_redis_client.store
    assert fake_redis_client.store[key]["world"]["nodes_by_coord"]
    assert fake_redis_client.store[key]["player"]["current"] == {"x": state.current_x, "y": state.current_y}


def _request(**managers: object) -> SimpleNamespace:
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(redis_managers=SimpleNamespace(**managers))))
