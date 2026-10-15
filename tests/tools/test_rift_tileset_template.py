from __future__ import annotations

import json
from collections import Counter

from PIL import Image
from tools.tileset_builder.rift_template import (
    BLOCKER_TILE_COUNT,
    CELL_SIZE,
    EVENT_TILE_COUNT,
    GRID_SIZE,
    HEX_H,
    HEX_W,
    LEVEL_TRANSITION_TILE_COUNT,
    MOOD_TILE_COUNT,
    MOVEMENT_TILE_COUNT,
    SLICE_HEX_H,
    SLICE_HEX_W,
    TILE_COUNT,
    blocker_edge_configs,
    build_tile_specs,
    build_tileset_data,
    generate_template,
    movement_edge_configs,
)


def test_blocker_edge_configs_have_no_empty_blocker_and_cover_expected_counts() -> None:
    configs = blocker_edge_configs()

    assert len(configs) == BLOCKER_TILE_COUNT
    assert () not in configs
    assert tuple(range(6)) not in configs
    assert Counter(len(config) for config in configs) == {1: 6, 2: 6, 3: 6, 4: 6, 5: 6}


def test_movement_edge_configs_cover_straights_turns_and_two_y_shapes() -> None:
    assert movement_edge_configs() == [
        (0, 3),
        (1, 4),
        (2, 5),
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 4),
        (4, 5),
        (5, 0),
        (0, 2, 4),
        (1, 3, 5),
    ]


def test_build_tile_specs_keep_blockers_and_locations_in_fixed_slots() -> None:
    specs = build_tile_specs()

    assert len(specs) == TILE_COUNT
    assert sum(1 for spec in specs if spec.role == "blocker") == BLOCKER_TILE_COUNT
    assert sum(1 for spec in specs if spec.role == "movement") == MOVEMENT_TILE_COUNT
    assert sum(1 for spec in specs if spec.role == "level_transition") == LEVEL_TRANSITION_TILE_COUNT
    assert sum(1 for spec in specs if spec.role == "event") == EVENT_TILE_COUNT
    assert sum(1 for spec in specs if spec.role == "mood") == MOOD_TILE_COUNT
    assert specs[0].closed_edges == (0,)
    assert specs[0].edges == (0, 1, 1, 1, 1, 1)
    assert specs[29].closed_edges == (5, 0, 1, 2, 3)
    assert specs[29].edges == (0, 0, 0, 0, 1, 0)
    assert specs[30].walkable is True
    assert specs[30].role == "movement"
    assert specs[30].edges == (1, 0, 0, 1, 0, 0)
    assert specs[33].edges == (1, 1, 0, 0, 0, 0)
    assert specs[39].edges == (1, 0, 1, 0, 1, 0)
    assert specs[40].edges == (0, 1, 0, 1, 0, 1)
    assert specs[41].role == "level_transition"
    assert specs[41].edges == (1, 1, 1, 1, 1, 1)
    assert specs[45].role == "event"
    assert specs[57].role == "mood"


def test_build_tileset_data_matches_backend_resource_shape() -> None:
    data = build_tileset_data("void_temple")

    assert list(data) == ["tiles"]
    assert data["tiles"][0] == {
        "id": 1,
        "file": "tile_01.png",
        "walkable": 0,
        "biome": "void_temple",
        "edges": [0, 1, 1, 1, 1, 1],
        "event": "",
    }
    assert data["tiles"][29]["edges"] == [0, 0, 0, 0, 1, 0]
    assert data["tiles"][30] == {
        "id": 31,
        "file": "tile_31.png",
        "walkable": 1,
        "biome": "void_temple",
        "edges": [1, 0, 0, 1, 0, 0],
        "event": "",
    }
    assert data["tiles"][35] == {
        "id": 36,
        "file": "tile_36.png",
        "walkable": 1,
        "biome": "void_temple",
        "edges": [0, 0, 1, 1, 0, 0],
        "event": "",
    }
    assert data["tiles"][41]["id"] == 42
    assert data["tiles"][41]["edges"] == [1, 1, 1, 1, 1, 1]
    assert data["tiles"][57]["id"] == 58
    assert data["tiles"][57]["edges"] == [1, 1, 1, 1, 1, 1]


def test_generate_template_writes_png_and_manifest(tmp_path) -> None:
    output_path = tmp_path / "ai_master_template.png"
    manifest_path = tmp_path / "rift_template_spec.json"

    generate_template(output_path=output_path, manifest_path=manifest_path)

    image = Image.open(output_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert image.size == (GRID_SIZE * CELL_SIZE, GRID_SIZE * CELL_SIZE)
    assert manifest["schema"] == "turnbasedmmorpg.rift.ai_master_template.v1"
    assert manifest["hex_w"] == HEX_W == 380.0
    assert manifest["hex_h"] == HEX_H == 440.0
    assert SLICE_HEX_W == 378.0
    assert SLICE_HEX_H == 438.0
    assert manifest["blocker_tile_count"] == BLOCKER_TILE_COUNT
    assert manifest["movement_tile_count"] == MOVEMENT_TILE_COUNT
    assert manifest["level_transition_tile_count"] == LEVEL_TRANSITION_TILE_COUNT
    assert manifest["event_tile_count"] == EVENT_TILE_COUNT
    assert manifest["mood_tile_count"] == MOOD_TILE_COUNT
    assert len(manifest["tiles"]) == TILE_COUNT
