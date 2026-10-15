from __future__ import annotations

import pytest

from src.backend.features.rift.runtime.hex.generation.builder import build_hex_rift_state
from src.backend.infrastructure.rift.managers import HexRiftWorldNotFoundError, HexRiftWorldStore


@pytest.mark.unit
async def test_hex_rift_world_store_owns_hex_world_keyspace(fake_redis_service, fake_redis_client) -> None:
    store = HexRiftWorldStore(fake_redis_service)
    state = build_hex_rift_state(
        "hex-rift-redis-1",
        "hex-redis-store-check",
        scale_key="solo",
        difficulty_key="easy",
        scheme_key="flower_weave",
    )

    document = await store.save_world(state, seed="hex-redis-store-check")
    loaded = await store.require_world(state.instance_id)

    key = f"game:rift:hex_world:{state.instance_id}"
    finish_key = f"{state.finish_x}:{state.finish_y}"
    assert f"game:rift:instance:{state.instance_id}" not in fake_redis_client.store
    assert key in fake_redis_client.store
    assert fake_redis_client.ttls[key] == HexRiftWorldStore.DEFAULT_TTL_SECONDS
    assert loaded == document
    assert loaded["schema_version"] == HexRiftWorldStore.SCHEMA_VERSION
    assert loaded["instance_id"] == state.instance_id
    assert loaded["layout_pattern_catalog"] == state.layout_pattern_catalog
    assert loaded["layout_template_debug"] == state.layout_template_debug
    assert loaded["world"]["grid"] == {"width": 12, "height": 12}
    assert len(loaded["world"]["nodes_by_coord"]) == state.width * state.height
    assert loaded["world"]["nodes_by_coord"][finish_key]["content_slot"] == "rift_heart_room"
    assert loaded["world"]["nodes_by_coord"][finish_key]["asset_path"]


@pytest.mark.unit
async def test_hex_rift_world_client_view_hides_unvisited_world_content(fake_redis_service) -> None:
    store = HexRiftWorldStore(fake_redis_service)
    state = build_hex_rift_state(
        "hex-rift-client-view",
        "hex-client-view-check",
        scale_key="solo",
        difficulty_key="easy",
        scheme_key="flower_weave",
    )
    document = await store.save_world(state)

    view = store.build_client_view(document)

    assert "world" not in view
    assert "finish" not in view
    assert view["grid"] == {"width": state.width, "height": state.height}
    assert view["layout_pattern_catalog"] == state.layout_pattern_catalog
    assert view["layout_template_debug"] == state.layout_template_debug
    assert view["start"] == {"x": state.start_x, "y": state.start_y}
    assert view["current"] == {"x": state.current_x, "y": state.current_y}
    assert {f'{node["x"]}:{node["y"]}' for node in view["nodes"]} == {
        f'{coord["x"]}:{coord["y"]}' for coord in view["revealed"]
    }

    visited = {f'{coord["x"]}:{coord["y"]}' for coord in view["visited"]}
    hidden_shells = [node for node in view["nodes"] if f'{node["x"]}:{node["y"]}' not in visited]
    assert hidden_shells
    assert all(node["content_slot"] == "unknown" for node in hidden_shells)
    assert all(node["asset_path"] == "" for node in hidden_shells)
    assert all(node["tile_index"] is None for node in hidden_shells)
    assert all(node["overlay_key"] == "" for node in hidden_shells)


@pytest.mark.unit
async def test_hex_rift_world_store_can_record_player_visibility(fake_redis_service) -> None:
    store = HexRiftWorldStore(fake_redis_service)
    state = build_hex_rift_state(
        "hex-rift-visibility",
        "hex-visibility-check",
        scale_key="solo",
        difficulty_key="easy",
        scheme_key="flower_weave",
    )
    await store.save_world(state)
    target = state.revealed[-1]

    await store.record_player_position(
        state.instance_id,
        current=(target[0], target[1]),
        previous=(state.current_x, state.current_y),
        reveal=[(target[0], target[1])],
    )
    loaded = await store.require_world(state.instance_id)

    assert loaded["player"]["current"] == {"x": target[0], "y": target[1]}
    assert loaded["player"]["previous"] == {"x": state.current_x, "y": state.current_y}
    assert {"x": target[0], "y": target[1]} in loaded["player"]["visited"]
    assert loaded["history"][-1]["type"] == "node_entered"


@pytest.mark.unit
async def test_hex_rift_world_store_requires_existing_world(fake_redis_service) -> None:
    store = HexRiftWorldStore(fake_redis_service)

    with pytest.raises(HexRiftWorldNotFoundError):
        await store.require_world("missing-rift")
