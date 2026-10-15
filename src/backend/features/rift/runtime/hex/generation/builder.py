from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

from src.backend.features.rift.dto.screen import RiftCombatPromptDTO  # noqa: TC001
from src.backend.features.rift.resources.layout_presets import (
    RIFT_GEOMETRY_PATTERNS,
    RIFT_LAYOUT_SCALES,
    RIFT_LAYOUT_SCHEMES,
    CountRange,
    LayoutPreset,
    active_geometry_pattern_keys,
    active_geometry_pattern_schemes,
    available_geometry_pattern_keys,
    resolve_layout_preset,
)
from src.backend.features.rift.resources.loader import RiftResourceLoader

DEFAULT_TILE_SET_KEY = "void_temple"
DEFAULT_LAYOUT_SCALE_KEY = "solo"
DEFAULT_LAYOUT_DIFFICULTY_KEY = "easy"
DEFAULT_LAYOUT_SCHEME_KEY: str | None = "flower_weave"
RANDOM_LAYOUT_SCHEME_KEY = "__random__"
FIRST_LAYER_MOVEMENT_EDGE_MASKS = {
    (1, 0, 1, 0, 0, 0),
    (0, 1, 0, 1, 0, 0),
    (0, 0, 1, 0, 1, 0),
    (0, 0, 0, 1, 0, 1),
    (1, 0, 0, 0, 1, 0),
    (0, 1, 0, 0, 0, 1),
    (1, 0, 0, 1, 0, 0),
    (0, 1, 0, 0, 1, 0),
    (0, 0, 1, 0, 0, 1),
    (1, 0, 1, 0, 0, 0),
    (0, 1, 0, 1, 0, 1),
    (1, 0, 1, 0, 1, 0),
}
FIRST_LAYER_FORK_EDGE_MASKS = {
    (0, 1, 0, 1, 0, 1),
    (1, 0, 1, 0, 1, 0),
}
FIRST_LAYER_TERMINAL_EDGE_MASKS = {
    (0, 1, 0, 0, 0, 0),
    (0, 0, 0, 0, 1, 0),
}


class HexNodeDTO(BaseModel):
    x: int
    y: int
    tile_index: int
    asset_path: str
    edges: list[int]
    is_walkable: bool
    title: str
    description: str
    graph_role: str = ""
    path_layer: str = ""
    visibility: str = "visible"
    content_slot: str = ""
    content_subtype: str = ""
    overlay_key: str = ""


class HexRiftStateDTO(BaseModel):
    instance_id: str
    theme: str
    scale_key: str = ""
    difficulty_key: str = ""
    scheme_key: str = ""
    available_scheme_keys: list[str] = []
    pattern_key: str = ""
    available_pattern_keys: list[str] = []
    layout_pattern_catalog: list[dict[str, Any]] = []
    layout_template_debug: dict[str, Any] = {}
    layout_debug: dict[str, Any] = {}
    width: int
    height: int
    start_x: int
    start_y: int
    finish_x: int
    finish_y: int
    current_x: int
    current_y: int
    previous_x: int | None = None
    previous_y: int | None = None
    floor: int = 1
    nodes: list[HexNodeDTO]
    visited: list[tuple[int, int]]
    revealed: list[tuple[int, int]]
    combat_prompt: RiftCombatPromptDTO | None = None


class HexLayoutNodeDTO(BaseModel):
    coord: tuple[int, int]
    edges: list[int]
    graph_role: str
    path_layer: str
    visibility: str = "visible"
    content_slot: str = "movement"


class HexLayoutDTO(BaseModel):
    scale_key: str
    difficulty_key: str
    scheme_key: str
    width: int
    height: int
    border: int
    start: tuple[int, int]
    finish: tuple[int, int]
    main_path: list[tuple[int, int]]
    nodes: list[HexLayoutNodeDTO]
    builder_debug: dict[str, Any] = {}


@dataclass
class _GraphDraft:
    start: tuple[int, int]
    finish: tuple[int, int]
    main_path: list[tuple[int, int]]
    layers: dict[tuple[int, int], str]
    adjacency: dict[tuple[int, int], set[tuple[int, int]]] = field(default_factory=dict)
    slots: dict[tuple[int, int], str] = field(default_factory=dict)
    builder_debug: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class HexBuildPlan:
    seed: str
    preset: LayoutPreset
    layer_keys: list[str]
    build_flower_pressure: bool
    build_main_path: bool
    build_branches: bool
    build_flower_loops: bool
    build_spike_spurs: bool
    build_hidden_shortcuts: bool
    build_secondary_path: bool
    place_required_slots: bool
    place_alternating_slots: bool
    place_interest_slots: bool

    def debug_flags(self) -> dict[str, bool]:
        return {
            "build_flower_pressure": self.build_flower_pressure,
            "build_main_path": self.build_main_path,
            "build_branches": self.build_branches,
            "build_flower_loops": self.build_flower_loops,
            "build_spike_spurs": self.build_spike_spurs,
            "build_hidden_shortcuts": self.build_hidden_shortcuts,
            "build_secondary_path": self.build_secondary_path,
            "place_required_slots": self.place_required_slots,
            "place_alternating_slots": self.place_alternating_slots,
            "place_interest_slots": self.place_interest_slots,
        }


@dataclass
class _HexBuildContext:
    seed: str
    rng: random.Random
    preset: LayoutPreset
    plan: HexBuildPlan
    start: tuple[int, int] | None = None
    finish: tuple[int, int] | None = None
    pressure_map: dict[tuple[int, int], int] = field(default_factory=dict)
    builder_debug: dict[str, Any] = field(default_factory=dict)
    draft: _GraphDraft | None = None


def get_hex_neighbors(x: int, y: int, width: int = 10, height: int = 10) -> list[tuple[int, int] | None]:
    """Get coordinates of adjacent hexes in an odd-r pointy-top hexagonal grid."""
    if y % 2 == 0:
        offsets = [
            (0, -1),  # NE
            (1, 0),  # E
            (0, 1),  # SE
            (-1, 1),  # SW
            (-1, 0),  # W
            (-1, -1),  # NW
        ]
    else:
        offsets = [
            (1, -1),  # NE
            (1, 0),  # E
            (1, 1),  # SE
            (0, 1),  # SW
            (-1, 0),  # W
            (0, -1),  # NW
        ]
    neighbors: list[tuple[int, int] | None] = []
    for dx, dy in offsets:
        nx, ny = x + dx, y + dy
        if 0 <= nx < width and 0 <= ny < height:
            neighbors.append((nx, ny))
        else:
            neighbors.append(None)
    return neighbors


def get_hex_direction(
    source: tuple[int, int],
    target: tuple[int, int],
    width: int = 10,
    height: int = 10,
) -> int | None:
    neighbors = get_hex_neighbors(source[0], source[1], width, height)
    for index, neighbor in enumerate(neighbors):
        if neighbor == target:
            return index
    return None


def load_hex_tile_set(tile_set_key: str = DEFAULT_TILE_SET_KEY) -> dict[str, object]:
    raw_tile_set = RiftResourceLoader().load_tile_set(tile_set_key)
    tiles = raw_tile_set.get("tiles")
    if not isinstance(tiles, list) or not tiles:
        raise ValueError(f"Rift tile set '{tile_set_key}' has no tiles")
    return raw_tile_set


def build_hex_build_plan(*, seed: str, preset: LayoutPreset) -> HexBuildPlan:
    has_flower_fields = bool(dict(preset.scheme.get("void_flowers") or {}))
    flower_loop_config = dict(preset.scheme.get("flower_loops") or {})
    spike_spur_config = dict(preset.scheme.get("spike_spurs") or {})
    has_hidden_shortcuts = bool(dict(preset.scheme.get("hidden_shortcut") or {}))
    secondary_config = dict(preset.scheme.get("secondary_path") or {})
    main_path_slots = dict(preset.scheme.get("main_path_slots") or {})
    build_secondary_path = has_flower_fields and bool(secondary_config.get("enabled"))
    build_flower_loops = bool(flower_loop_config.get("enabled"))
    build_spike_spurs = bool(spike_spur_config.get("enabled"))
    build_branches = not has_flower_fields and not has_hidden_shortcuts
    place_alternating_slots = bool(main_path_slots.get("alternate"))
    place_interest_slots = bool(dict(preset.scheme.get("interest_distribution") or {}))

    layer_keys = ["choose_flower_weave_endpoints" if has_flower_fields else "choose_anchors"]
    if has_flower_fields:
        layer_keys.append("place_flower_pressure")
    layer_keys.append("build_main_path")
    if build_flower_loops:
        layer_keys.append("build_flower_loops")
    if build_spike_spurs:
        layer_keys.append("build_spike_spurs")
    if build_branches:
        layer_keys.append("place_branches")
    if has_hidden_shortcuts:
        layer_keys.append("place_hidden_shortcuts")
    if build_secondary_path:
        layer_keys.append("place_secondary_path")
    layer_keys.append("place_required_slots")
    if place_alternating_slots:
        layer_keys.append("place_alternating_slots")
    if place_interest_slots:
        layer_keys.append("place_interest_slots")

    return HexBuildPlan(
        seed=seed,
        preset=preset,
        layer_keys=layer_keys,
        build_flower_pressure=has_flower_fields,
        build_main_path=True,
        build_branches=build_branches,
        build_flower_loops=build_flower_loops,
        build_spike_spurs=build_spike_spurs,
        build_hidden_shortcuts=has_hidden_shortcuts,
        build_secondary_path=build_secondary_path,
        place_required_slots=True,
        place_alternating_slots=place_alternating_slots,
        place_interest_slots=place_interest_slots,
    )


def build_hex_layout(
    seed: str,
    *,
    scale_key: str = DEFAULT_LAYOUT_SCALE_KEY,
    difficulty_key: str = DEFAULT_LAYOUT_DIFFICULTY_KEY,
    scheme_key: str | None = DEFAULT_LAYOUT_SCHEME_KEY,
) -> HexLayoutDTO:
    scheme_key = _resolve_layout_scheme_key(seed=seed, scale_key=scale_key, scheme_key=scheme_key)
    preset = resolve_layout_preset(scale_key=scale_key, difficulty_key=difficulty_key, scheme_key=scheme_key)
    plan = build_hex_build_plan(seed=seed, preset=preset)
    draft = _run_hex_build_pipeline(plan)
    return _draft_to_layout(draft=draft, preset=preset)


def generate_hex_rift(
    seed: str,
    width: int = 12,
    height: int = 12,
) -> tuple[list[tuple[int, int]], tuple[int, int], tuple[int, int]]:
    scale_key = "solo" if width <= 12 and height <= 12 else "group"
    layout = build_hex_layout(seed=seed, scale_key=scale_key)
    walkable = [node.coord for node in layout.nodes]
    return walkable, layout.start, layout.finish


def build_hex_rift_state(
    instance_id: str,
    seed: str,
    tile_set_key: str = DEFAULT_TILE_SET_KEY,
    *,
    scale_key: str = DEFAULT_LAYOUT_SCALE_KEY,
    difficulty_key: str = DEFAULT_LAYOUT_DIFFICULTY_KEY,
    scheme_key: str | None = DEFAULT_LAYOUT_SCHEME_KEY,
) -> HexRiftStateDTO:
    scheme_key = _resolve_layout_scheme_key(seed=seed, scale_key=scale_key, scheme_key=scheme_key)
    preset = resolve_layout_preset(scale_key=scale_key, difficulty_key=difficulty_key, scheme_key=scheme_key)
    layout = build_hex_layout(seed=seed, scale_key=scale_key, difficulty_key=difficulty_key, scheme_key=scheme_key)
    walkable_set = {node.coord for node in layout.nodes}
    layout_by_coord = {node.coord: node for node in layout.nodes}

    tile_set = load_hex_tile_set(tile_set_key)
    tiles_info = tile_set["tiles"]
    if not isinstance(tiles_info, list):
        raise ValueError(f"Rift tile set '{tile_set_key}' has invalid tiles")

    catalog = _TileCatalog(tiles_info, dict(tile_set.get("catalog") or {}))

    rng = random.Random(f"{seed}:tiles")
    void_decor_coords = _select_void_decor_coords(
        rng=rng,
        layout=layout,
        walkable_set=walkable_set,
        fill_ratio=preset.void_decor_fill_ratio,
    )
    nodes: list[HexNodeDTO] = []
    for y in range(layout.height):
        for x in range(layout.width):
            coord = (x, y)
            layout_node = layout_by_coord.get(coord)
            is_walkable = coord in walkable_set

            if layout_node is not None:
                selected_tile = catalog.select_walkable(layout_node, rng)
                graph_role = layout_node.graph_role
                path_layer = layout_node.path_layer
                visibility = layout_node.visibility
                content_slot = layout_node.content_slot
                content_subtype = _tile_content_subtype(selected_tile, content_slot)
                overlay_key = _tile_overlay_key(content_slot, content_subtype)
                edges = layout_node.edges
            elif _touches_walkable(coord, walkable_set, layout.width, layout.height):
                selected_tile = catalog.select_blocker(coord, walkable_set, layout.width, layout.height)
                graph_role = "void"
                path_layer = ""
                visibility = "visible"
                content_slot = "contour"
                content_subtype = content_slot
                overlay_key = ""
                edges = _tile_edges(selected_tile)
            elif coord in void_decor_coords:
                selected_tile = catalog.select_void_decor(rng)
                graph_role = "void"
                path_layer = ""
                visibility = "visible"
                content_slot = "void_decor"
                content_subtype = "void_decor"
                overlay_key = ""
                edges = _tile_edges(selected_tile)
            else:
                selected_tile = catalog.select_blocker(coord, walkable_set, layout.width, layout.height)
                graph_role = "void"
                path_layer = ""
                visibility = "visible"
                content_slot = "void"
                content_subtype = content_slot
                overlay_key = ""
                edges = _tile_edges(selected_tile)

            nodes.append(
                HexNodeDTO(
                    x=x,
                    y=y,
                    tile_index=int(selected_tile["id"]),
                    asset_path=_tile_asset_path(selected_tile),
                    edges=edges,
                    is_walkable=is_walkable,
                    title=_node_title(coord, layout.start, layout.finish, is_walkable, content_slot),
                    description=_node_description(is_walkable, content_slot),
                    graph_role=graph_role,
                    path_layer=path_layer,
                    visibility=visibility,
                    content_slot=content_slot,
                    content_subtype=content_subtype,
                    overlay_key=overlay_key,
                )
            )

    visited = [layout.start]
    revealed_set = {layout.start}
    for neighbor in get_hex_neighbors(layout.start[0], layout.start[1], layout.width, layout.height):
        if neighbor is not None:
            revealed_set.add(neighbor)

    return HexRiftStateDTO(
        instance_id=instance_id,
        theme=tile_set_key,
        scale_key=layout.scale_key,
        difficulty_key=layout.difficulty_key,
        scheme_key=layout.scheme_key,
        pattern_key=str(preset.scheme.get("geometry_pattern") or ""),
        available_scheme_keys=list(active_geometry_pattern_schemes(layout.scale_key).values()),
        available_pattern_keys=active_geometry_pattern_keys(layout.scale_key),
        layout_pattern_catalog=_layout_pattern_catalog(layout.scale_key),
        layout_template_debug=_layout_template_debug(layout=layout, preset=preset),
        layout_debug=_layout_debug(layout),
        width=layout.width,
        height=layout.height,
        start_x=layout.start[0],
        start_y=layout.start[1],
        finish_x=layout.finish[0],
        finish_y=layout.finish[1],
        current_x=layout.start[0],
        current_y=layout.start[1],
        nodes=nodes,
        visited=list(visited),
        revealed=list(revealed_set),
    )


def _layout_pattern_catalog(scale_key: str) -> list[dict[str, Any]]:
    available_keys = set(available_geometry_pattern_keys(scale_key))
    scale = RIFT_LAYOUT_SCALES[scale_key]
    active_pattern_schemes: dict[str, list[str]] = {}
    for scheme_key in [str(value) for value in scale.get("scheme_keys") or []]:
        scheme = RIFT_LAYOUT_SCHEMES[scheme_key]
        pattern_key = str(scheme.get("geometry_pattern") or "legacy_path_graph")
        active_pattern_schemes.setdefault(pattern_key, []).append(scheme_key)

    catalog: list[dict[str, Any]] = []
    for key, pattern in RIFT_GEOMETRY_PATTERNS.items():
        active_scheme_keys = active_pattern_schemes.get(key, [])
        if key not in available_keys or not active_scheme_keys:
            continue
        status = str(pattern["status"])
        catalog.append(
            {
                "key": key,
                "status": status,
                "min_scale": str(pattern["min_scale"]),
                "available_for_current_scale": key in available_keys,
                "active_scheme_keys": active_scheme_keys,
                "dev_enabled": status == "planned" and bool(active_scheme_keys),
                "shape_layers": list(pattern["shape_layers"]),
                "description": str(pattern["description"]),
            }
        )
    return catalog


def _layout_template_debug(*, layout: HexLayoutDTO, preset: LayoutPreset) -> dict[str, Any]:
    scheme = preset.scheme
    pattern_key = str(scheme.get("geometry_pattern") or "legacy_path_graph")
    pattern = dict(RIFT_GEOMETRY_PATTERNS.get(pattern_key) or {})
    path_graph = dict(scheme.get("path_graph") or {})
    spike_spurs = dict(scheme.get("spike_spurs") or {})
    flower_loops = dict(scheme.get("flower_loops") or {})
    void_flowers = dict(scheme.get("void_flowers") or {})
    spike_spur_forks = (
        _raw_ratio_count_range(
            dict(spike_spurs.get("fork_ratio") or {}),
            preset.usable_capacity,
            minimum_floor=0,
        )
        if bool(spike_spurs.get("enabled"))
        else CountRange(min=0, target=0, max=0)
    )
    spike_spur_nodes = (
        _raw_ratio_count_range(
            dict(spike_spurs.get("node_budget_ratio") or {}),
            preset.usable_capacity,
            minimum_floor=0,
        )
        if bool(spike_spurs.get("enabled"))
        else CountRange(min=0, target=0, max=0)
    )
    flower_loop_forks = (
        _raw_ratio_count_range(
            dict(flower_loops.get("count_ratio") or {}),
            preset.usable_capacity,
            minimum_floor=0,
        )
        if bool(flower_loops.get("enabled"))
        else CountRange(min=0, target=0, max=0)
    )
    flower_loop_nodes = (
        _raw_ratio_count_range(
            dict(flower_loops.get("node_budget_ratio") or {}),
            preset.usable_capacity,
            minimum_floor=0,
        )
        if bool(flower_loops.get("enabled"))
        else CountRange(min=0, target=0, max=0)
    )

    return {
        "scheme_key": preset.scheme_key,
        "geometry_pattern": pattern_key,
        "status": str(pattern.get("status") or "implemented"),
        "min_scale": str(pattern.get("min_scale") or layout.scale_key),
        "description": str(pattern.get("description") or ""),
        "shape_layers": list(pattern.get("shape_layers") or []),
        "pipeline_layers": list(layout.builder_debug.get("pipeline_layers") or []),
        "pipeline_plan": dict(layout.builder_debug.get("pipeline_plan") or {}),
        "rules": {
            "main_path": {
                "target_nodes": len(layout.main_path),
                "min_nodes": preset.main_path_nodes.min,
                "max_nodes": preset.main_path_nodes.max,
                "odd": bool(path_graph.get("main_path_odd", False)),
                "straight_run": {
                    "min": path_graph.get("min_straight_run"),
                    "max": path_graph.get("max_straight_run"),
                },
                "avoid_triangles": bool(path_graph.get("avoid_triangles", False)),
            },
            "branches": {
                "target_count": preset.forks.target,
                "min_count": preset.forks.min,
                "max_count": preset.forks.max,
                "allowed_on": list(path_graph.get("fork_allowed_on") or []),
                "target_length": preset.branch_length.target,
            },
            "spike_spurs": {
                "enabled": bool(spike_spurs.get("enabled", False)),
                "target_count": layout.builder_debug.get("spike_spur_target_count", spike_spur_forks.target),
                "actual_count": layout.builder_debug.get("spike_spur_count", 0),
                "candidate_count": layout.builder_debug.get("spike_spur_candidate_count", 0),
                "attempted_candidates": layout.builder_debug.get("spike_spur_attempted_candidates", 0),
                "rejected_candidates": layout.builder_debug.get("spike_spur_rejected_candidates", 0),
                "actual_nodes": layout.builder_debug.get("spike_spur_nodes", 0),
                "node_budget": {
                    "min": spike_spur_nodes.min,
                    "target": spike_spur_nodes.target,
                    "max": spike_spur_nodes.max,
                },
                "path_length": dict(spike_spurs.get("path_length") or {}),
                "path_layer": str(spike_spurs.get("path_layer") or ""),
                "node_slot": str(spike_spurs.get("node_slot") or ""),
            },
            "flower_loops": {
                "enabled": bool(flower_loops.get("enabled", False)),
                "target_count": flower_loop_forks.target,
                "actual_count": layout.builder_debug.get("flower_loop_count", 0),
                "node_budget": {
                    "min": flower_loop_nodes.min,
                    "target": flower_loop_nodes.target,
                    "max": flower_loop_nodes.max,
                },
                "contact_count": flower_loops.get("contact_count"),
                "path_layer": str(flower_loops.get("path_layer") or ""),
                "required": bool(flower_loops.get("required", False)),
            },
            "void_flowers": {
                "enabled": bool(void_flowers),
                "soft_flower_count": layout.builder_debug.get("soft_flower_count", 0),
                "soft_center_policy": str(void_flowers.get("soft_center_policy") or ""),
            },
        },
    }


def _layout_debug(layout: HexLayoutDTO) -> dict[str, Any]:
    usable_cells = max(1, (layout.width - layout.border * 2) * (layout.height - layout.border * 2))
    active_nodes = len(layout.nodes)
    reachable_nodes = _reachable_layout_node_count(layout)
    layer_counts = _count_layout_node_values(layout.nodes, "path_layer")
    slot_counts = _count_layout_node_values(layout.nodes, "content_slot")
    role_counts = _count_layout_node_values(layout.nodes, "graph_role")
    debug = {
        "scale_key": layout.scale_key,
        "difficulty_key": layout.difficulty_key,
        "scheme_key": layout.scheme_key,
        "width": layout.width,
        "height": layout.height,
        "border": layout.border,
        "usable_cells": usable_cells,
        "main_path_nodes": len(layout.main_path),
        "extra_nodes": max(0, active_nodes - len(layout.main_path)),
        "fork_nodes": sum(1 for node in layout.nodes if node.graph_role == "fork"),
        "branch_nodes": sum(1 for node in layout.nodes if node.path_layer == "branch"),
        "hidden_shortcut_nodes": sum(1 for node in layout.nodes if node.path_layer == "hidden_shortcut"),
        "active_nodes": active_nodes,
        "walkable_nodes": active_nodes,
        "walkable_percent": round(active_nodes / usable_cells * 100, 1),
        "reachable_nodes": reachable_nodes,
        "unreachable_walkable_nodes": max(0, active_nodes - reachable_nodes),
        "reachable_percent": round(reachable_nodes / active_nodes * 100, 1) if active_nodes else 0,
        "layer_counts": layer_counts,
        "slot_counts": slot_counts,
        "role_counts": role_counts,
    }
    debug.update(layout.builder_debug)
    return debug


def _reachable_layout_node_count(layout: HexLayoutDTO) -> int:
    nodes_by_coord = {node.coord: node for node in layout.nodes}
    if layout.start not in nodes_by_coord:
        return 0

    seen = {layout.start}
    queue = [layout.start]
    while queue:
        coord = queue.pop(0)
        node = nodes_by_coord[coord]
        for edge, neighbor in enumerate(get_hex_neighbors(coord[0], coord[1], layout.width, layout.height)):
            if node.edges[edge] != 1 or neighbor is None or neighbor not in nodes_by_coord or neighbor in seen:
                continue
            seen.add(neighbor)
            queue.append(neighbor)
    return len(seen)


def _count_layout_node_values(nodes: list[HexLayoutNodeDTO], field_name: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for node in nodes:
        value = str(getattr(node, field_name) or "none")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def is_outer_frame_coord(x: int, y: int, width: int, height: int) -> bool:
    return x == 0 or y == 0 or x == width - 1 or y == height - 1


def _resolve_layout_scheme_key(*, seed: str, scale_key: str, scheme_key: str | None) -> str:
    if scheme_key:
        return scheme_key
    scale = RIFT_LAYOUT_SCALES[scale_key]
    scheme_keys = [str(value) for value in scale.get("random_scheme_keys") or scale.get("scheme_keys") or []]
    if not scheme_keys:
        raise ValueError(f"Rift layout scale '{scale_key}' has no scheme keys")
    return random.Random(f"{seed}:layout-scheme").choice(scheme_keys)


def _run_hex_build_pipeline(plan: HexBuildPlan) -> _GraphDraft:
    max_attempts = int(plan.preset.scheme.get("pipeline_attempts") or 12)
    for attempt in range(max_attempts):
        attempt_seed = plan.seed if attempt == 0 else f"{plan.seed}:layout-attempt:{attempt}"
        attempt_plan = build_hex_build_plan(seed=attempt_seed, preset=plan.preset)
        context = _HexBuildContext(
            seed=attempt_seed,
            rng=random.Random(attempt_seed),
            preset=plan.preset,
            plan=attempt_plan,
            builder_debug={
                "geometry_pattern": str(plan.preset.scheme.get("geometry_pattern") or "legacy_path_graph"),
            },
        )
        try:
            for layer_key in attempt_plan.layer_keys:
                _HEX_BUILD_LAYERS[layer_key](context)
            draft = _require_draft(context)
        except RuntimeError:
            continue
        if _draft_meets_preset(draft, plan.preset):
            draft.builder_debug["pipeline_layers"] = list(plan.layer_keys)
            draft.builder_debug["pipeline_plan"] = plan.debug_flags()
            return draft
    raise RuntimeError(
        f"Could not build rift graph for scheme '{plan.preset.scheme_key}' after {max_attempts} attempts"
    )


def _choose_anchors_layer(context: _HexBuildContext) -> None:
    context.start, context.finish = _choose_anchors(context.rng, context.preset)


def _choose_flower_weave_endpoints_layer(context: _HexBuildContext) -> None:
    context.start, context.finish = _choose_flower_weave_endpoints(context.rng, context.preset)


def _place_flower_pressure_layer(context: _HexBuildContext) -> None:
    start, finish = _require_endpoints(context)
    structural_anchors = _structural_flower_anchors(context.preset)
    soft_flower_centers = _select_soft_flower_centers(
        rng=context.rng,
        preset=context.preset,
        structural_anchors=structural_anchors,
        start=start,
        finish=finish,
    )
    pressure_map = _soft_flower_pressure_map(soft_flower_centers, context.preset)
    pressure_map.pop(start, None)
    pressure_map.pop(finish, None)
    config = dict(context.preset.scheme.get("void_flowers") or {})
    context.pressure_map = pressure_map
    context.builder_debug.update(
        {
            "structural_flower_anchors": sorted(structural_anchors),
            "soft_flower_centers": sorted(soft_flower_centers),
            "soft_flower_pressure_cells": sorted(pressure_map),
            "soft_flower_count": len(soft_flower_centers),
            "soft_flower_center_policy": str(config.get("soft_center_policy") or "high_cost"),
            "path_candidate_strategy": "weighted_pressure_search",
        }
    )


def _build_main_path_layer(context: _HexBuildContext) -> None:
    start, finish = _require_endpoints(context)
    if context.plan.build_flower_pressure:
        main_path = _find_flower_weave_path(
            seed=context.seed,
            rng=context.rng,
            preset=context.preset,
            start=start,
            finish=finish,
            pressure_map=context.pressure_map,
        )
    else:
        main_path = _find_main_path(
            seed=context.seed,
            rng=context.rng,
            preset=context.preset,
            start=start,
            finish=finish,
        )
    adjacency = _path_adjacency(main_path)
    context.draft = _GraphDraft(
        start=start,
        finish=finish,
        main_path=main_path,
        layers={coord: "main" for coord in main_path},
        adjacency=adjacency,
        builder_debug=dict(context.builder_debug),
    )


def _place_branches_layer(context: _HexBuildContext) -> None:
    _add_branches(draft=_require_draft(context), rng=context.rng, preset=context.preset)


def _build_flower_loops_layer(context: _HexBuildContext) -> None:
    _add_flower_loops(draft=_require_draft(context), rng=context.rng, preset=context.preset)


def _build_spike_spurs_layer(context: _HexBuildContext) -> None:
    _add_spike_spurs(draft=_require_draft(context), rng=context.rng, preset=context.preset)


def _place_hidden_shortcuts_layer(context: _HexBuildContext) -> None:
    _add_hidden_shortcuts(draft=_require_draft(context), rng=context.rng, preset=context.preset)


def _place_secondary_path_layer(context: _HexBuildContext) -> None:
    _add_flower_weave_secondary_path(draft=_require_draft(context), rng=context.rng, preset=context.preset)


def _place_required_slots_layer(context: _HexBuildContext) -> None:
    _place_required_slots(
        draft=_require_draft(context), preset=context.preset, rng=random.Random(f"{context.seed}:slots")
    )


def _place_alternating_slots_layer(context: _HexBuildContext) -> None:
    _place_alternating_base_slots(_require_draft(context), context.preset)


def _place_interest_slots_layer(context: _HexBuildContext) -> None:
    _place_interest_slots(draft=_require_draft(context), preset=context.preset, rng=context.rng)


def _require_endpoints(context: _HexBuildContext) -> tuple[tuple[int, int], tuple[int, int]]:
    if context.start is None or context.finish is None:
        raise RuntimeError("Hex build pipeline endpoints were not selected")
    return context.start, context.finish


def _require_draft(context: _HexBuildContext) -> _GraphDraft:
    if context.draft is None:
        raise RuntimeError("Hex build pipeline graph draft was not built")
    return context.draft


_HEX_BUILD_LAYERS = {
    "choose_anchors": _choose_anchors_layer,
    "choose_flower_weave_endpoints": _choose_flower_weave_endpoints_layer,
    "place_flower_pressure": _place_flower_pressure_layer,
    "build_main_path": _build_main_path_layer,
    "build_flower_loops": _build_flower_loops_layer,
    "build_spike_spurs": _build_spike_spurs_layer,
    "place_branches": _place_branches_layer,
    "place_hidden_shortcuts": _place_hidden_shortcuts_layer,
    "place_secondary_path": _place_secondary_path_layer,
    "place_required_slots": _place_required_slots_layer,
    "place_alternating_slots": _place_alternating_slots_layer,
    "place_interest_slots": _place_interest_slots_layer,
}


def _draft_meets_preset(draft: _GraphDraft, preset: LayoutPreset) -> bool:
    if preset.avoid_triangles and _has_triangle_cluster(set(draft.adjacency), preset.width, preset.height):
        return False
    fork_count = sum(1 for coord in draft.adjacency if _graph_role(coord, draft) == "fork")
    if not preset.forks.min <= fork_count <= preset.forks.max:
        return False
    shortcut_config = dict(preset.scheme.get("hidden_shortcut") or {})
    if shortcut_config:
        return any(layer == "hidden_shortcut" for layer in draft.layers.values())
    secondary_config = dict(preset.scheme.get("secondary_path") or {})
    if bool(secondary_config.get("enabled")):
        return any(layer == "hidden_shortcut" for layer in draft.layers.values())
    return True


def _choose_anchors(rng: random.Random, preset: LayoutPreset) -> tuple[tuple[int, int], tuple[int, int]]:
    min_y = preset.border + 1
    max_y = preset.height - preset.border - 2
    start_y = rng.randint(min_y + 1, max_y - 1) if max_y - min_y > 2 else rng.randint(min_y, max_y)
    finish_offset = rng.choice([-2, -1, 1, 2])
    finish_y = max(min_y, min(max_y, start_y + finish_offset))
    return (preset.border, start_y), (preset.width - preset.border - 1, finish_y)


def _void_flower_axis_anchors(size: int, *, start: int = 1, step: int = 4) -> list[int]:
    return list(range(start, size, step))


def _choose_flower_weave_endpoints(rng: random.Random, preset: LayoutPreset) -> tuple[tuple[int, int], tuple[int, int]]:
    config = dict(preset.scheme.get("void_flowers") or {})
    axis_y = _void_flower_axis_anchors(
        preset.height,
        start=int(config.get("structural_anchor_start") or 1),
        step=int(config.get("structural_anchor_step") or 4),
    )
    start_y = rng.choice(axis_y)
    finish_options = [value for value in axis_y if value != start_y] or axis_y
    finish_y = rng.choice(finish_options)
    return (preset.border, start_y), (preset.width - preset.border - 1, finish_y)


def _nearest_axis_anchor(value: int, anchors: list[int]) -> int:
    return min(anchors, key=lambda anchor: (abs(anchor - value), anchor))


def _structural_flower_anchors(preset: LayoutPreset) -> set[tuple[int, int]]:
    config = dict(preset.scheme.get("void_flowers") or {})
    axis_x = _void_flower_axis_anchors(
        preset.width,
        start=int(config.get("structural_anchor_start") or 1),
        step=int(config.get("structural_anchor_step") or 4),
    )
    axis_y = _void_flower_axis_anchors(
        preset.height,
        start=int(config.get("structural_anchor_start") or 1),
        step=int(config.get("structural_anchor_step") or 4),
    )
    return {(x, y) for x in axis_x for y in axis_y}


def _select_soft_flower_centers(
    *,
    rng: random.Random,
    preset: LayoutPreset,
    structural_anchors: set[tuple[int, int]],
    start: tuple[int, int],
    finish: tuple[int, int],
) -> set[tuple[int, int]]:
    config = dict(preset.scheme.get("void_flowers") or {})
    count = _soft_flower_count_range(config, preset.scale_key)
    target_count = rng.randint(count.min, max(count.min, count.max))
    min_gap = max(1, int(config.get("soft_min_center_gap") or 1))
    protected = {start, finish, *structural_anchors}
    candidates = [
        (x, y)
        for y in range(preset.border, preset.height - preset.border)
        for x in range(preset.border, preset.width - preset.border)
        if (x, y) not in protected
    ]
    rng.shuffle(candidates)
    selected: set[tuple[int, int]] = set()
    for candidate in candidates:
        if any(_grid_distance(candidate, existing) < min_gap for existing in selected):
            continue
        selected.add(candidate)
        if len(selected) >= target_count:
            break
    return selected


def _soft_flower_count_range(config: dict[str, object], scale_key: str) -> CountRange:
    by_scale = dict(config.get("soft_flower_count_by_scale") or {})
    if scale_key in by_scale:
        return _raw_count_range(dict(by_scale[scale_key] or {}))
    if "soft_flower_count" in config:
        return _raw_count_range(dict(config.get("soft_flower_count") or {}))
    return _raw_count_range({"min": 0, "target": 0, "max": 0})


def _soft_flower_pressure_map(centers: set[tuple[int, int]], preset: LayoutPreset) -> dict[tuple[int, int], int]:
    config = dict(preset.scheme.get("void_flowers") or {})
    center_cost = int(config.get("soft_center_cost") or 0)
    petal_cost = int(config.get("soft_petal_cost") or 0)
    outer_cost = int(config.get("soft_outer_cost") or 0)
    pressure: dict[tuple[int, int], int] = {}
    for center in centers:
        _add_pressure(pressure, center, center_cost, preset)
        petals = {
            neighbor
            for neighbor in get_hex_neighbors(center[0], center[1], preset.width, preset.height)
            if neighbor is not None and _inside_usable(neighbor, preset)
        }
        for petal in petals:
            _add_pressure(pressure, petal, petal_cost, preset)
        for petal in petals:
            for outer in get_hex_neighbors(petal[0], petal[1], preset.width, preset.height):
                if outer is not None and _inside_usable(outer, preset) and outer != center and outer not in petals:
                    _add_pressure(pressure, outer, outer_cost, preset)
    return pressure


def _add_pressure(
    pressure: dict[tuple[int, int], int],
    coord: tuple[int, int],
    value: int,
    preset: LayoutPreset,
) -> None:
    if value <= 0 or not _inside_usable(coord, preset):
        return
    pressure[coord] = pressure.get(coord, 0) + value


def _hex_flower(center: tuple[int, int], width: int, height: int) -> set[tuple[int, int]]:
    return {
        center,
        *{neighbor for neighbor in get_hex_neighbors(center[0], center[1], width, height) if neighbor is not None},
    }


def _find_flower_weave_path(
    *,
    seed: str,
    rng: random.Random,
    preset: LayoutPreset,
    start: tuple[int, int],
    finish: tuple[int, int],
    pressure_map: dict[tuple[int, int], int],
) -> list[tuple[int, int]]:
    return _find_supported_path_with_pressure(
        seed=seed,
        rng=random.Random(f"{seed}:flower-pressure"),
        preset=preset,
        start=start,
        finish=finish,
        pressure_map=pressure_map,
    )


def _bidirectional_bfs_path_candidates(
    *,
    rng: random.Random,
    preset: LayoutPreset,
    start: tuple[int, int],
    finish: tuple[int, int],
    blocked: set[tuple[int, int]],
) -> list[list[tuple[int, int]]]:
    start_front = {start}
    finish_front = {finish}
    start_parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    finish_parent: dict[tuple[int, int], tuple[int, int] | None] = {finish: None}
    meetings: list[tuple[int, int]] = []
    max_steps = max(20, preset.width * preset.height)

    for _ in range(max_steps):
        if not start_front or not finish_front:
            break
        if len(start_front) <= len(finish_front):
            start_front = _expand_bfs_front(
                rng=rng,
                front=start_front,
                own_parent=start_parent,
                blocked=blocked,
                preset=preset,
            )
            meetings.extend(coord for coord in start_front if coord in finish_parent)
        else:
            finish_front = _expand_bfs_front(
                rng=rng,
                front=finish_front,
                own_parent=finish_parent,
                blocked=blocked,
                preset=preset,
            )
            meetings.extend(coord for coord in finish_front if coord in start_parent)
        if len(set(meetings)) >= 18:
            break

    candidates: list[list[tuple[int, int]]] = []
    for meeting in dict.fromkeys(meetings):
        start_half = _reconstruct_parent_path(meeting, start_parent)
        finish_half = _reconstruct_parent_path(meeting, finish_parent)
        if not start_half or not finish_half:
            continue
        full_path = start_half + list(reversed(finish_half))[1:]
        if full_path[0] == start and full_path[-1] == finish:
            candidates.append(full_path)
    candidates.sort(key=lambda path: (len(path), rng.random()))
    return candidates


def _expand_bfs_front(
    *,
    rng: random.Random,
    front: set[tuple[int, int]],
    own_parent: dict[tuple[int, int], tuple[int, int] | None],
    blocked: set[tuple[int, int]],
    preset: LayoutPreset,
) -> set[tuple[int, int]]:
    next_front: set[tuple[int, int]] = set()
    current_nodes = list(front)
    rng.shuffle(current_nodes)
    for coord in current_nodes:
        neighbors = [
            neighbor
            for neighbor in get_hex_neighbors(coord[0], coord[1], preset.width, preset.height)
            if neighbor is not None
            and _inside_usable(neighbor, preset)
            and neighbor not in blocked
            and neighbor not in own_parent
        ]
        rng.shuffle(neighbors)
        for neighbor in neighbors:
            own_parent[neighbor] = coord
            next_front.add(neighbor)
    return next_front


def _reconstruct_parent_path(
    coord: tuple[int, int],
    parents: dict[tuple[int, int], tuple[int, int] | None],
) -> list[tuple[int, int]]:
    if coord not in parents:
        return []
    path = [coord]
    while parents[path[-1]] is not None:
        path.append(parents[path[-1]])  # type: ignore[arg-type]
    return list(reversed(path))


def _find_supported_path_avoiding(
    *,
    seed: str,
    rng: random.Random,
    preset: LayoutPreset,
    start: tuple[int, int],
    finish: tuple[int, int],
    blocked: set[tuple[int, int]],
) -> list[tuple[int, int]]:
    stack = [[start]]
    attempts = 0
    max_attempts = max(10000, preset.usable_capacity * 260)
    while stack and attempts < max_attempts:
        attempts += 1
        current_path = stack.pop()
        current = current_path[-1]
        if current == finish:
            if _flower_weave_path_is_acceptable(current_path, preset=preset):
                return current_path
            continue
        if len(current_path) >= preset.main_path_nodes.max:
            continue
        candidates = [
            neighbor
            for neighbor in get_hex_neighbors(current[0], current[1], preset.width, preset.height)
            if neighbor is not None
            and _inside_usable(neighbor, preset)
            and neighbor not in blocked
            and neighbor not in current_path
        ]
        rng.shuffle(candidates)
        candidates.sort(key=lambda coord: (_grid_distance(coord, finish), rng.random()), reverse=True)
        for candidate in candidates:
            if (
                _straight_run_with_candidate(current_path, candidate, preset.width, preset.height)
                > preset.max_straight_run
            ):
                continue
            if preset.avoid_triangles and _walkable_neighbors(
                candidate, set(current_path), preset.width, preset.height
            ) != {current}:
                continue
            if not _candidate_keeps_path_topology(current_path, candidate, preset):
                continue
            stack.append([*current_path, candidate])
    raise RuntimeError(f"Could not build flower weave path for scheme '{preset.scheme_key}'")


def _find_supported_path_with_pressure(
    *,
    seed: str,
    rng: random.Random,
    preset: LayoutPreset,
    start: tuple[int, int],
    finish: tuple[int, int],
    pressure_map: dict[tuple[int, int], int],
) -> list[tuple[int, int]]:
    target = preset.main_path_nodes.target
    accepted: list[tuple[int, list[tuple[int, int]]]] = []
    stack: list[tuple[list[tuple[int, int]], int]] = [([start], 0)]
    attempts = 0
    max_attempts = max(4000, preset.usable_capacity * 55)
    while stack and attempts < max_attempts and len(accepted) < 4:
        attempts += 1
        path, path_cost = stack.pop()
        current = path[-1]
        if current == finish:
            if _flower_weave_path_is_acceptable(path, preset=preset):
                score = (
                    abs(len(path) - target) * 20 + path_cost - _path_turn_count(path, preset.width, preset.height) * 2
                )
                accepted.append((score, path))
            continue
        if len(path) >= preset.main_path_nodes.max:
            continue

        active = set(path)
        candidates = [
            neighbor
            for neighbor in get_hex_neighbors(current[0], current[1], preset.width, preset.height)
            if neighbor is not None and _inside_usable(neighbor, preset) and neighbor not in active
        ]
        filtered: list[tuple[int, tuple[int, int]]] = []
        for candidate in candidates:
            if candidate == finish and len(path) < preset.main_path_nodes.min - 1:
                continue
            if candidate != finish and _turns_before_min_straight_run(path, candidate, preset):
                continue
            if _straight_run_with_candidate(path, candidate, preset.width, preset.height) > preset.max_straight_run:
                continue
            if preset.avoid_triangles and _walkable_neighbors(candidate, active, preset.width, preset.height) != {
                current
            }:
                continue
            if not _candidate_keeps_path_topology(path, candidate, preset):
                continue
            if _creates_one_hex_gap(
                candidate=candidate,
                linked_to=current,
                active=active,
                adjacency=_path_adjacency(path),
                local_gap_neighbors=set(path[-2:]),
                width=preset.width,
                height=preset.height,
            ):
                continue
            step_cost = _pressure_step_cost(
                candidate=candidate,
                current=current,
                active=active,
                finish=finish,
                current_path=path,
                pressure_map=pressure_map,
                preset=preset,
            )
            length_bias = abs((len(path) + 1) - target)
            filtered.append((step_cost + _grid_distance(candidate, finish) + length_bias, candidate))

        filtered.sort(key=lambda item: (item[0], rng.random()), reverse=True)
        for step_cost, candidate in filtered:
            stack.append(([*path, candidate], path_cost + step_cost))

    if accepted:
        accepted.sort(key=lambda item: (item[0], rng.random()))
        return accepted[0][1]

    raise RuntimeError(f"Could not build pressure weighted path for scheme '{preset.scheme_key}'")


def _flower_weave_path_is_acceptable(
    path: list[tuple[int, int]],
    *,
    preset: LayoutPreset,
) -> bool:
    return (
        preset.main_path_nodes.min <= len(path) <= preset.main_path_nodes.max
        and _path_uses_supported_topology(path, preset)
        and not _has_triangle_cluster(set(path), preset.width, preset.height)
        and _path_min_internal_straight_run(path, preset.width, preset.height) >= preset.min_straight_run
        and _path_max_straight_run(path, preset.width, preset.height) <= preset.max_straight_run
    )


def _path_turn_count(path: list[tuple[int, int]], width: int, height: int) -> int:
    return sum(1 for index in range(1, len(path) - 1) if _is_bend(path, index, width, height))


def _path_max_straight_run(path: list[tuple[int, int]], width: int, height: int) -> int:
    if len(path) < 2:
        return 0
    max_run = 1
    run = 1
    previous_direction = get_hex_direction(path[0], path[1], width, height)
    for source, target in zip(path[1:-1], path[2:], strict=False):
        direction = get_hex_direction(source, target, width, height)
        if direction == previous_direction:
            run += 1
        else:
            run = 1
        previous_direction = direction
        max_run = max(max_run, run)
    return max_run


def _path_min_internal_straight_run(path: list[tuple[int, int]], width: int, height: int) -> int:
    runs = _path_straight_runs(path, width, height)
    internal_runs = runs[1:-1]
    return min(internal_runs) if internal_runs else 999


def _path_straight_runs(path: list[tuple[int, int]], width: int, height: int) -> list[int]:
    if len(path) < 2:
        return []
    runs: list[int] = []
    run = 1
    previous_direction = get_hex_direction(path[0], path[1], width, height)
    for source, target in zip(path[1:-1], path[2:], strict=False):
        direction = get_hex_direction(source, target, width, height)
        if direction == previous_direction:
            run += 1
        else:
            runs.append(run)
            run = 1
        previous_direction = direction
    runs.append(run)
    return runs


def _path_creates_one_hex_gap(path: list[tuple[int, int]], width: int, height: int) -> bool:
    active = set(path)
    adjacency = _path_adjacency(path)
    for y in range(height):
        for x in range(width):
            coord = (x, y)
            if coord in active:
                continue
            touching = [neighbor for neighbor in get_hex_neighbors(x, y, width, height) if neighbor in active]
            for first_index, first in enumerate(touching):
                first_links = adjacency.get(first, set())
                for second in touching[first_index + 1 :]:
                    if second in first_links:
                        continue
                    if _graph_distance(first, second, adjacency, max_distance=2) <= 2:
                        continue
                    return True
    return False


def _graph_distance(
    start: tuple[int, int],
    finish: tuple[int, int],
    graph: dict[tuple[int, int], set[tuple[int, int]]],
    *,
    max_distance: int,
) -> int:
    visited = {start}
    queue = [(start, 0)]
    while queue:
        coord, distance = queue.pop(0)
        if coord == finish:
            return distance
        if distance >= max_distance:
            continue
        for neighbor in graph.get(coord, set()):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, distance + 1))
    return max_distance + 1


def _pressure_step_cost(
    *,
    candidate: tuple[int, int],
    current: tuple[int, int],
    active: set[tuple[int, int]],
    finish: tuple[int, int],
    current_path: list[tuple[int, int]],
    pressure_map: dict[tuple[int, int], int],
    preset: LayoutPreset,
) -> int:
    adjacent_active = _walkable_neighbors(candidate, active, preset.width, preset.height)
    second_ring_active = {
        second
        for neighbor in get_hex_neighbors(candidate[0], candidate[1], preset.width, preset.height)
        if neighbor is not None
        for second in get_hex_neighbors(neighbor[0], neighbor[1], preset.width, preset.height)
        if second in active and second not in adjacent_active and second != candidate
    }
    straight_run = _straight_run_with_candidate(current_path, candidate, preset.width, preset.height)
    straight_penalty = 8 if straight_run >= 2 else 0
    current_distance = _grid_distance(current, finish)
    candidate_distance = _grid_distance(candidate, finish)
    toward_finish_bonus = max(0, current_distance - candidate_distance) * 2
    raw_cost = (
        10
        + pressure_map.get(candidate, 0)
        + len(adjacent_active) * 10
        + len(second_ring_active) * 3
        + straight_penalty
        - toward_finish_bonus
    )
    return max(1, raw_cost)


def _candidate_creates_triangle_cluster(
    candidate: tuple[int, int],
    active: set[tuple[int, int]],
    width: int,
    height: int,
) -> bool:
    prospective = set(active)
    prospective.add(candidate)
    return _has_triangle_cluster(prospective, width, height)


def _has_triangle_cluster(active: set[tuple[int, int]], width: int, height: int) -> bool:
    for coord in active:
        active_neighbors = [
            neighbor for neighbor in get_hex_neighbors(coord[0], coord[1], width, height) if neighbor in active
        ]
        for first_index, first in enumerate(active_neighbors):
            for second in active_neighbors[first_index + 1 :]:
                if second in get_hex_neighbors(first[0], first[1], width, height):
                    return True
    return False


def _find_main_path(
    *,
    seed: str,
    rng: random.Random,
    preset: LayoutPreset,
    start: tuple[int, int],
    finish: tuple[int, int],
) -> list[tuple[int, int]]:
    stack = [[start]]
    attempts = 0
    max_attempts = max(10000, preset.usable_capacity * 240)

    while stack and attempts < max_attempts:
        attempts += 1
        current_path = stack.pop()
        current = current_path[-1]
        if current == finish:
            if preset.main_path_nodes.min <= len(
                current_path
            ) <= preset.main_path_nodes.max and _path_uses_supported_topology(current_path, preset):
                return current_path
            continue
        if len(current_path) >= preset.main_path_nodes.max:
            continue

        candidates = [
            neighbor
            for neighbor in get_hex_neighbors(current[0], current[1], preset.width, preset.height)
            if neighbor is not None and _inside_usable(neighbor, preset) and neighbor not in current_path
        ]
        rng.shuffle(candidates)
        candidates.sort(key=lambda coord: abs(coord[0] - finish[0]) + abs(coord[1] - finish[1]), reverse=True)

        for candidate in candidates:
            if (
                _straight_run_with_candidate(current_path, candidate, preset.width, preset.height)
                > preset.max_straight_run
            ):
                continue
            if preset.avoid_triangles and _walkable_neighbors(
                candidate, set(current_path), preset.width, preset.height
            ) != {current}:
                continue
            if not _candidate_keeps_path_topology(current_path, candidate, preset):
                continue
            if _creates_one_hex_gap(
                candidate=candidate,
                linked_to=current,
                active=set(current_path),
                adjacency=_path_adjacency(current_path),
                local_gap_neighbors=set(current_path[-2:]),
                width=preset.width,
                height=preset.height,
            ):
                continue
            stack.append(current_path + [candidate])

    raise RuntimeError(f"Could not build rift main path for scheme '{preset.scheme_key}'")


def _add_branches(*, draft: _GraphDraft, rng: random.Random, preset: LayoutPreset) -> None:
    target_forks = rng.randint(preset.forks.min, max(preset.forks.min, preset.forks.max))
    max_active = rng.randint(preset.active_nodes.target, preset.active_nodes.max)
    active = set(draft.adjacency)
    bend_junctions = [
        coord
        for index, coord in enumerate(draft.main_path)
        if coord not in (draft.start, draft.finish)
        and _is_bend(draft.main_path, index, preset.width, preset.height)
        and index >= preset.min_distance_from_start
        and len(draft.main_path) - index - 1 >= preset.min_distance_from_finish
    ]
    rng.shuffle(bend_junctions)

    placed_forks = 0
    placed_indexes: list[int] = []
    for junction in bend_junctions:
        if placed_forks >= target_forks or len(active) >= max_active:
            break
        junction_index = draft.main_path.index(junction)
        if any(abs(junction_index - existing) < preset.min_distance_between_forks for existing in placed_indexes):
            continue
        branch_length = rng.randint(preset.branch_length.min, max(preset.branch_length.min, preset.branch_length.max))
        current = junction
        branch_nodes: list[tuple[int, int]] = []
        for _ in range(branch_length):
            candidates = [
                neighbor
                for neighbor in get_hex_neighbors(current[0], current[1], preset.width, preset.height)
                if neighbor is not None
                and _inside_usable(neighbor, preset)
                and neighbor not in active
                and _walkable_neighbors(neighbor, active, preset.width, preset.height) == {current}
                and _branch_candidate_keeps_topology(draft, current, neighbor, junction, preset)
                and not _creates_one_hex_gap(
                    candidate=neighbor,
                    linked_to=current,
                    active=active,
                    adjacency=draft.adjacency,
                    local_gap_neighbors={current, *draft.adjacency.get(current, set())},
                    width=preset.width,
                    height=preset.height,
                )
            ]
            if not candidates or len(active) >= max_active:
                break
            if bool(dict(preset.scheme.get("branches") or {}).get("prefer_toward_finish")):
                candidates.sort(key=lambda coord: _grid_distance(coord, draft.finish))
            next_node = rng.choice(candidates)
            branch_nodes.append(next_node)
            _link(draft.adjacency, current, next_node)
            draft.layers[next_node] = "branch"
            active.add(next_node)
            current = next_node
        if branch_nodes:
            placed_forks += 1
            placed_indexes.append(junction_index)


def _add_hidden_shortcuts(*, draft: _GraphDraft, rng: random.Random, preset: LayoutPreset) -> None:
    config = dict(preset.scheme.get("hidden_shortcut") or {})
    if not config:
        return
    count = _raw_count_range(dict(config.get("count") or {"min": 0, "target": 0, "max": 0}))
    target_count = rng.randint(count.min, max(count.min, count.max))
    length = _raw_ratio_count_range(dict(config.get("length_ratio") or {}), preset.usable_capacity, minimum_floor=2)
    gap = _raw_ratio_count_range(dict(config.get("main_gap_ratio") or {}), len(draft.main_path), minimum_floor=4)
    active = set(draft.adjacency)
    placed = 0
    pairs = _hidden_shortcut_pairs(draft.main_path, gap, preset)
    rng.shuffle(pairs)
    for source_index, target_index in pairs:
        if placed >= target_count:
            break
        source = draft.main_path[source_index]
        target = draft.main_path[target_index]
        shortcut = _find_shortcut_path(
            source=source,
            target=target,
            active=active,
            rng=rng,
            preset=preset,
            min_nodes=length.min,
            max_nodes=length.max,
        )
        if not shortcut:
            continue
        if preset.avoid_triangles and _has_triangle_cluster(active | set(shortcut), preset.width, preset.height):
            continue
        previous = source
        for coord in shortcut:
            _link(draft.adjacency, previous, coord)
            draft.layers[coord] = "hidden_shortcut"
            active.add(coord)
            previous = coord
        _link(draft.adjacency, previous, target)
        placed += 1


def _add_spike_spurs(*, draft: _GraphDraft, rng: random.Random, preset: LayoutPreset) -> None:
    config = dict(preset.scheme.get("spike_spurs") or {})
    if not bool(config.get("enabled")):
        return

    path_layer = str(config.get("path_layer") or "spike_spur")
    node_slot = str(config.get("node_slot") or "movement")
    length_config = dict(config.get("path_length") or {})
    min_path_length = max(2, int(length_config.get("min") or 2))
    max_path_length = max(min_path_length, int(length_config.get("max") or min_path_length))
    path_length_three_chance = float(config.get("path_length_three_chance") or 0.0)
    active = set(draft.adjacency)
    max_active = preset.active_nodes.max
    bend_junctions = [
        coord
        for index, coord in enumerate(draft.main_path)
        if coord not in (draft.start, draft.finish) and _is_bend(draft.main_path, index, preset.width, preset.height)
    ]
    candidate_count = len(bend_junctions)
    rng.shuffle(bend_junctions)

    placed = 0
    placed_nodes = 0
    three_node_paths = 0
    attempted_candidates = 0
    for junction in bend_junctions:
        if len(active) >= max_active:
            break
        attempted_candidates += 1
        target_length = 3 if max_path_length >= 3 and rng.random() < path_length_three_chance else min_path_length
        path = _find_spike_spur_path(
            draft=draft,
            junction=junction,
            path_length=target_length,
            active=active,
            rng=rng,
            preset=preset,
        )
        if not path:
            continue
        if len(active) + len(path) > max_active:
            continue

        previous = junction
        for coord in path:
            _link(draft.adjacency, previous, coord)
            draft.layers[coord] = path_layer
            draft.slots[coord] = node_slot
            active.add(coord)
            previous = coord
        placed += 1
        placed_nodes += len(path)
        if len(path) == 3:
            three_node_paths += 1

    draft.builder_debug.update(
        {
            "spike_spur_target_count": candidate_count,
            "spike_spur_candidate_count": candidate_count,
            "spike_spur_attempted_candidates": attempted_candidates,
            "spike_spur_rejected_candidates": max(0, attempted_candidates - placed),
            "spike_spur_count": placed,
            "spike_spur_nodes": placed_nodes,
            "spike_spur_three_node_paths": three_node_paths,
            "spike_spur_path_length_three_chance": path_length_three_chance,
            "spike_spur_path_layer": path_layer,
        }
    )


def _find_spike_spur_path(
    *,
    draft: _GraphDraft,
    junction: tuple[int, int],
    path_length: int,
    active: set[tuple[int, int]],
    rng: random.Random,
    preset: LayoutPreset,
) -> list[tuple[int, int]]:
    path: list[tuple[int, int]] = []
    current = junction
    for step_index in range(path_length):
        candidates = [
            neighbor
            for neighbor in get_hex_neighbors(current[0], current[1], preset.width, preset.height)
            if neighbor is not None
            and _inside_usable(neighbor, preset)
            and neighbor not in active
            and neighbor not in path
        ]
        rng.shuffle(candidates)
        candidates.sort(key=lambda coord: (_spike_candidate_pressure(coord, active, preset), rng.random()))
        next_coord = None
        for candidate in candidates:
            if not _spike_step_supported(
                draft=draft,
                junction=junction,
                path=path,
                current=current,
                candidate=candidate,
                active=active,
                is_terminal=step_index == path_length - 1,
                preset=preset,
            ):
                continue
            next_coord = candidate
            break
        if next_coord is None:
            return []
        path.append(next_coord)
        current = next_coord
    return path


def _spike_step_supported(
    *,
    draft: _GraphDraft,
    junction: tuple[int, int],
    path: list[tuple[int, int]],
    current: tuple[int, int],
    candidate: tuple[int, int],
    active: set[tuple[int, int]],
    is_terminal: bool,
    preset: LayoutPreset,
) -> bool:
    prospective_path = [*path, candidate]
    prospective_active = active | set(prospective_path)
    current_touch = _walkable_neighbors(candidate, active | set(path), preset.width, preset.height)
    if current_touch - {current}:
        return False
    if preset.avoid_triangles and _candidate_creates_triangle_cluster(
        candidate, active | set(path), preset.width, preset.height
    ):
        return False

    adjacency = _spike_partial_adjacency(draft.adjacency, junction, prospective_path)
    if _has_unlinked_one_hex_gap(prospective_active, adjacency, preset.width, preset.height):
        return False
    if current == junction:
        junction_links = set(draft.adjacency.get(junction, set())) | {candidate}
        junction_mask = _edge_mask_for_links(junction, junction_links, preset.width, preset.height)
        if tuple(junction_mask) not in FIRST_LAYER_FORK_EDGE_MASKS:
            return False
    elif not is_terminal:
        previous = junction if len(path) == 1 else path[-2]
        current_mask = _edge_mask_for_links(current, {previous, candidate}, preset.width, preset.height)
        if tuple(current_mask) not in FIRST_LAYER_MOVEMENT_EDGE_MASKS:
            return False
    if is_terminal:
        previous = junction if not path else path[-1]
        terminal_mask = _edge_mask_for_links(candidate, {previous}, preset.width, preset.height)
        if tuple(terminal_mask) not in FIRST_LAYER_TERMINAL_EDGE_MASKS:
            return False
    return True


def _spike_partial_adjacency(
    adjacency: dict[tuple[int, int], set[tuple[int, int]]],
    junction: tuple[int, int],
    path: list[tuple[int, int]],
) -> dict[tuple[int, int], set[tuple[int, int]]]:
    result = {coord: set(links) for coord, links in adjacency.items()}
    previous = junction
    for coord in path:
        _link(result, previous, coord)
        previous = coord
    return result


def _spike_candidate_pressure(coord: tuple[int, int], active: set[tuple[int, int]], preset: LayoutPreset) -> int:
    adjacent_active = len(_walkable_neighbors(coord, active, preset.width, preset.height))
    second_ring_active = sum(
        1
        for neighbor in get_hex_neighbors(coord[0], coord[1], preset.width, preset.height)
        if neighbor is not None
        for second in get_hex_neighbors(neighbor[0], neighbor[1], preset.width, preset.height)
        if second in active
    )
    return adjacent_active * 20 + second_ring_active


def _add_flower_loops(*, draft: _GraphDraft, rng: random.Random, preset: LayoutPreset) -> None:
    config = dict(preset.scheme.get("flower_loops") or {})
    if not bool(config.get("enabled")):
        return

    path_layer = str(config.get("path_layer") or "flower_loop")
    target_count = _flower_loop_target_count(config=config, preset=preset)
    candidates = [
        *_flower_loop_candidates(draft=draft, preset=preset, config=config),
        *_flower_loop_free_arc_candidates(draft=draft, preset=preset, config=config),
    ]
    rng.shuffle(candidates)
    candidates.sort(key=lambda candidate: (len(candidate["arc"]), rng.random()))

    active = set(draft.adjacency)
    used_contacts: set[tuple[int, int]] = set()
    protected_voids: set[tuple[int, int]] = set()
    placed = 0
    for candidate in candidates:
        if placed >= target_count:
            break
        contacts = set(candidate["contacts"])
        arc = list(candidate["arc"])
        internal_nodes = arc[1:-1]
        if contacts & used_contacts or any(coord in active for coord in internal_nodes):
            continue
        if not _flower_loop_arc_supported(
            draft=draft,
            arc=arc,
            active=active,
            preset=preset,
        ):
            continue

        previous = arc[0]
        for coord in arc[1:]:
            _link(draft.adjacency, previous, coord)
            if coord not in contacts:
                draft.layers[coord] = path_layer
                active.add(coord)
            previous = coord
        used_contacts.update(contacts)
        protected_voids.update(candidate["inner_voids"])
        placed += 1

    draft.builder_debug.update(
        {
            "flower_loop_count": placed,
            "flower_loop_target_count": target_count,
            "flower_loop_candidate_count": len(candidates),
            "flower_loop_path_layer": path_layer,
            "flower_loop_protected_voids": sorted(protected_voids),
        }
    )
    if bool(config.get("required")) and placed <= 0:
        raise RuntimeError("Flower loop layer is required but no supported loop was found")


def _flower_loop_target_count(*, config: dict[str, object], preset: LayoutPreset) -> int:
    count = _raw_ratio_count_range(dict(config.get("count_ratio") or {}), preset.usable_capacity, minimum_floor=0)
    budget = _raw_ratio_count_range(
        dict(config.get("node_budget_ratio") or {}), preset.usable_capacity, minimum_floor=0
    )
    min_added_nodes = max(1, int(config.get("min_added_nodes") or 1))
    budget_count = budget.target // min_added_nodes
    if count.target > 0 and budget.target >= min_added_nodes:
        budget_count = max(1, budget_count)
    return max(count.min, min(count.max, min(count.target, budget_count)))


def _flower_loop_candidates(
    *,
    draft: _GraphDraft,
    preset: LayoutPreset,
    config: dict[str, object],
) -> list[dict[str, object]]:
    inner_radius = max(1, int(config.get("inner_radius") or 1))
    ring_radius = max(inner_radius + 1, int(config.get("ring_radius") or inner_radius + 1))
    min_added_nodes = max(1, int(config.get("min_added_nodes") or 1))
    max_added_nodes = max(min_added_nodes, int(config.get("max_added_nodes") or min_added_nodes))
    contact_count = max(2, int(config.get("contact_count") or 2))
    min_gap = _raw_ratio_count_range(
        dict(config.get("min_main_path_gap_ratio") or {}),
        len(draft.main_path),
        minimum_floor=3,
    )
    active = set(draft.adjacency)
    main_index = {coord: index for index, coord in enumerate(draft.main_path)}
    candidates: list[dict[str, object]] = []

    for y in range(preset.border, preset.height - preset.border):
        for x in range(preset.border, preset.width - preset.border):
            center = (x, y)
            inner_voids = _hex_cells_within_radius(center, inner_radius, preset)
            ring = _hex_ring_cells(center, ring_radius, preset)
            if not inner_voids or not ring or len(inner_voids) < 7 or len(ring) < 12:
                continue
            if inner_voids & active:
                continue
            contacts = [
                coord
                for coord in ring
                if coord in main_index
                and coord not in (draft.start, draft.finish)
                and main_index[coord] % 2 == 1
                and main_index[coord] >= preset.min_distance_from_start
                and len(draft.main_path) - main_index[coord] - 1 >= preset.min_distance_from_finish
            ]
            if len(contacts) < contact_count:
                continue
            for left_index, source in enumerate(contacts):
                for target in contacts[left_index + 1 :]:
                    if abs(main_index[target] - main_index[source]) < min_gap.min:
                        continue
                    for arc in _ring_arc_paths(source=source, target=target, ring=ring, preset=preset):
                        internal_nodes = arc[1:-1]
                        if not min_added_nodes <= len(internal_nodes) <= max_added_nodes:
                            continue
                        if any(coord in active for coord in internal_nodes):
                            continue
                        candidates.append(
                            {
                                "center": center,
                                "contacts": (source, target),
                                "arc": arc,
                                "inner_voids": inner_voids,
                            }
                        )
    return candidates


def _flower_loop_free_arc_candidates(
    *,
    draft: _GraphDraft,
    preset: LayoutPreset,
    config: dict[str, object],
) -> list[dict[str, object]]:
    min_added_nodes = max(1, int(config.get("min_added_nodes") or 1))
    max_added_nodes = max(min_added_nodes, int(config.get("max_added_nodes") or min_added_nodes))
    min_gap = _raw_ratio_count_range(
        dict(config.get("min_main_path_gap_ratio") or {}),
        len(draft.main_path),
        minimum_floor=3,
    )
    active = set(draft.adjacency)
    main_index = {coord: index for index, coord in enumerate(draft.main_path)}
    contacts = [
        coord
        for coord in draft.main_path
        if coord not in (draft.start, draft.finish)
        and main_index[coord] % 2 == 1
        and main_index[coord] >= preset.min_distance_from_start
        and len(draft.main_path) - main_index[coord] - 1 >= preset.min_distance_from_finish
    ]
    candidates: list[dict[str, object]] = []
    for left_index, source in enumerate(contacts):
        for target in contacts[left_index + 1 :]:
            if len(candidates) >= 32:
                return candidates
            if abs(main_index[target] - main_index[source]) < min_gap.min:
                continue
            if _grid_distance(source, target) > (max_added_nodes + 1) * 2:
                continue
            arcs = _find_flower_loop_free_arcs(
                source=source,
                target=target,
                active=active,
                adjacency=draft.adjacency,
                preset=preset,
                min_added_nodes=min_added_nodes,
                max_added_nodes=max_added_nodes,
            )
            for arc in arcs:
                candidates.append(
                    {
                        "center": _arc_midpoint(arc),
                        "contacts": (source, target),
                        "arc": arc,
                        "inner_voids": _flower_loop_inner_voids_for_arc(arc=arc, active=active, preset=preset),
                    }
                )
    return candidates


def _find_flower_loop_free_arcs(
    *,
    source: tuple[int, int],
    target: tuple[int, int],
    active: set[tuple[int, int]],
    adjacency: dict[tuple[int, int], set[tuple[int, int]]],
    preset: LayoutPreset,
    min_added_nodes: int,
    max_added_nodes: int,
) -> list[list[tuple[int, int]]]:
    arcs: list[list[tuple[int, int]]] = []
    queue: list[list[tuple[int, int]]] = [[source]]
    attempts = 0
    max_attempts = max(120, preset.usable_capacity * 3)
    while queue and len(arcs) < 4 and attempts < max_attempts:
        attempts += 1
        path = queue.pop(0)
        current = path[-1]
        internal_nodes = path[1:]
        if len(internal_nodes) > max_added_nodes + 1:
            continue
        remaining_steps = max_added_nodes + 1 - len(path)
        if _grid_distance(current, target) > max(1, remaining_steps) * 2:
            continue
        candidates = [
            neighbor
            for neighbor in get_hex_neighbors(current[0], current[1], preset.width, preset.height)
            if neighbor is not None and _inside_usable(neighbor, preset)
        ]
        candidates.sort(key=lambda coord: (_grid_distance(coord, target), coord[1], coord[0]))
        for candidate in candidates:
            if candidate == target:
                added_nodes = len(path) - 1
                arc = [*path, target]
                if min_added_nodes <= added_nodes <= max_added_nodes and _flower_loop_arc_supported_by_adjacency(
                    arc=arc,
                    adjacency=adjacency,
                    active=active,
                    preset=preset,
                ):
                    arcs.append(arc)
                continue
            if candidate in active or candidate in path:
                continue
            prospective_active = active | set(path)
            active_touch = _walkable_neighbors(candidate, prospective_active, preset.width, preset.height)
            if active_touch - {current, target}:
                continue
            if preset.avoid_triangles and _candidate_creates_triangle_cluster(
                candidate,
                prospective_active,
                preset.width,
                preset.height,
            ):
                continue
            queue.append([*path, candidate])
    return arcs


def _arc_midpoint(arc: list[tuple[int, int]]) -> tuple[int, int]:
    return arc[len(arc) // 2]


def _flower_loop_inner_voids_for_arc(
    *,
    arc: list[tuple[int, int]],
    active: set[tuple[int, int]],
    preset: LayoutPreset,
) -> set[tuple[int, int]]:
    arc_set = set(arc)
    candidates = {
        neighbor
        for coord in arc
        for neighbor in get_hex_neighbors(coord[0], coord[1], preset.width, preset.height)
        if neighbor is not None
        and _inside_usable(neighbor, preset)
        and neighbor not in active
        and neighbor not in arc_set
    }
    if len(candidates) < 7:
        return candidates
    center = _arc_midpoint(arc)
    return set(sorted(candidates, key=lambda coord: (_grid_distance(coord, center), coord[1], coord[0]))[:7])


def _flower_loop_arc_supported(
    *,
    draft: _GraphDraft,
    arc: list[tuple[int, int]],
    active: set[tuple[int, int]],
    preset: LayoutPreset,
) -> bool:
    if len(arc) < 4:
        return False
    source = arc[0]
    target = arc[-1]
    internal = arc[1:-1]
    prospective_active = active | set(internal)
    if preset.avoid_triangles and _has_triangle_cluster(prospective_active, preset.width, preset.height):
        return False
    if _flower_loop_arc_creates_one_hex_gap(
        draft=draft,
        arc=arc,
        active=active,
        preset=preset,
    ):
        return False

    source_links = set(draft.adjacency.get(source, set())) | {arc[1]}
    target_links = set(draft.adjacency.get(target, set())) | {arc[-2]}
    if (
        tuple(_edge_mask_for_links(source, source_links, preset.width, preset.height))
        not in FIRST_LAYER_FORK_EDGE_MASKS
    ):
        return False
    if (
        tuple(_edge_mask_for_links(target, target_links, preset.width, preset.height))
        not in FIRST_LAYER_FORK_EDGE_MASKS
    ):
        return False

    for index, coord in enumerate(internal, start=1):
        linked = {arc[index - 1], arc[index + 1]}
        if (
            tuple(_edge_mask_for_links(coord, linked, preset.width, preset.height))
            not in FIRST_LAYER_MOVEMENT_EDGE_MASKS
        ):
            return False
        active_touch = _walkable_neighbors(coord, active, preset.width, preset.height)
        allowed_touch = {source, target} & active_touch
        if active_touch - allowed_touch:
            return False
    return True


def _flower_loop_arc_supported_by_adjacency(
    *,
    arc: list[tuple[int, int]],
    adjacency: dict[tuple[int, int], set[tuple[int, int]]],
    active: set[tuple[int, int]],
    preset: LayoutPreset,
) -> bool:
    if len(arc) < 4:
        return False
    internal = arc[1:-1]
    prospective_active = active | set(internal)
    if preset.avoid_triangles and _has_triangle_cluster(prospective_active, preset.width, preset.height):
        return False
    source_links = set(adjacency.get(arc[0], set())) | {arc[1]}
    target_links = set(adjacency.get(arc[-1], set())) | {arc[-2]}
    if (
        tuple(_edge_mask_for_links(arc[0], source_links, preset.width, preset.height))
        not in FIRST_LAYER_FORK_EDGE_MASKS
    ):
        return False
    if (
        tuple(_edge_mask_for_links(arc[-1], target_links, preset.width, preset.height))
        not in FIRST_LAYER_FORK_EDGE_MASKS
    ):
        return False
    for index, coord in enumerate(internal, start=1):
        linked = {arc[index - 1], arc[index + 1]}
        if (
            tuple(_edge_mask_for_links(coord, linked, preset.width, preset.height))
            not in FIRST_LAYER_MOVEMENT_EDGE_MASKS
        ):
            return False
    return not _has_unlinked_one_hex_gap(
        prospective_active, _flower_loop_partial_adjacency(adjacency, arc), preset.width, preset.height
    )


def _flower_loop_arc_creates_one_hex_gap(
    *,
    draft: _GraphDraft,
    arc: list[tuple[int, int]],
    active: set[tuple[int, int]],
    preset: LayoutPreset,
) -> bool:
    return not _flower_loop_arc_supported_by_adjacency(
        arc=arc,
        adjacency=draft.adjacency,
        active=active,
        preset=preset,
    )


def _flower_loop_partial_adjacency(
    adjacency: dict[tuple[int, int], set[tuple[int, int]]],
    path: list[tuple[int, int]],
) -> dict[tuple[int, int], set[tuple[int, int]]]:
    result = {coord: set(links) for coord, links in adjacency.items()}
    for source, target in zip(path, path[1:], strict=False):
        _link(result, source, target)
    return result


def _has_unlinked_one_hex_gap(
    active: set[tuple[int, int]],
    adjacency: dict[tuple[int, int], set[tuple[int, int]]],
    width: int,
    height: int,
) -> bool:
    for y in range(height):
        for x in range(width):
            coord = (x, y)
            if coord in active:
                continue
            touching = [neighbor for neighbor in get_hex_neighbors(x, y, width, height) if neighbor in active]
            for first_index, first in enumerate(touching):
                first_links = adjacency.get(first, set())
                for second in touching[first_index + 1 :]:
                    if second in first_links:
                        continue
                    if _graph_distance(first, second, adjacency, max_distance=2) <= 2:
                        continue
                    return True
    return False


def _hex_cells_within_radius(center: tuple[int, int], radius: int, preset: LayoutPreset) -> set[tuple[int, int]]:
    distances = _hex_distance_map(center=center, max_radius=radius, preset=preset)
    return {coord for coord, distance in distances.items() if distance <= radius}


def _hex_ring_cells(center: tuple[int, int], radius: int, preset: LayoutPreset) -> set[tuple[int, int]]:
    distances = _hex_distance_map(center=center, max_radius=radius, preset=preset)
    return {coord for coord, distance in distances.items() if distance == radius}


def _hex_distance_map(
    *,
    center: tuple[int, int],
    max_radius: int,
    preset: LayoutPreset,
) -> dict[tuple[int, int], int]:
    if not _inside_usable(center, preset):
        return {}
    distances = {center: 0}
    frontier = [center]
    while frontier:
        coord = frontier.pop(0)
        distance = distances[coord]
        if distance >= max_radius:
            continue
        for neighbor in get_hex_neighbors(coord[0], coord[1], preset.width, preset.height):
            if neighbor is None or not _inside_usable(neighbor, preset) or neighbor in distances:
                continue
            distances[neighbor] = distance + 1
            frontier.append(neighbor)
    return distances


def _ring_arc_paths(
    *,
    source: tuple[int, int],
    target: tuple[int, int],
    ring: set[tuple[int, int]],
    preset: LayoutPreset,
) -> list[list[tuple[int, int]]]:
    ring_links = {
        coord: {
            neighbor
            for neighbor in get_hex_neighbors(coord[0], coord[1], preset.width, preset.height)
            if neighbor in ring
        }
        for coord in ring
    }
    paths: list[list[tuple[int, int]]] = []
    stack = [[source]]
    while stack:
        path = stack.pop()
        current = path[-1]
        if current == target:
            paths.append(path)
            continue
        for neighbor in ring_links[current]:
            if neighbor in path:
                continue
            if len(path) > len(ring):
                continue
            stack.append([*path, neighbor])
    unique: dict[tuple[tuple[int, int], ...], list[tuple[int, int]]] = {}
    for path in paths:
        unique.setdefault(tuple(path), path)
    return list(unique.values())


def _add_flower_weave_secondary_path(*, draft: _GraphDraft, rng: random.Random, preset: LayoutPreset) -> None:
    config = dict(preset.scheme.get("secondary_path") or {})
    if not bool(config.get("enabled")):
        return
    length = _raw_ratio_count_range(dict(config.get("length_ratio") or {}), preset.usable_capacity, minimum_floor=2)
    min_cut = _raw_ratio_count_range(
        dict(config.get("min_cut_main_nodes_ratio") or {}),
        preset.usable_capacity,
        minimum_floor=7,
    )
    source = draft.finish
    source_index = len(draft.main_path) - 1
    min_target_index = max(1, preset.min_distance_from_start)
    target_indices = [
        index
        for index in range(min_target_index, source_index - min_cut.min + 1)
        if draft.main_path[index] not in (draft.start, draft.finish)
    ]
    rng.shuffle(target_indices)
    target_indices.sort(key=lambda index: (source_index - index, rng.random()))

    active = set(draft.adjacency)
    for target_index in target_indices:
        target = draft.main_path[target_index]
        cut_main_nodes = source_index - target_index + 1
        shortcut = _find_flower_weave_secondary_path(
            source=source,
            target=target,
            active=active,
            adjacency=draft.adjacency,
            rng=rng,
            preset=preset,
            min_nodes=length.min,
            max_nodes=min(length.max, max(length.min, cut_main_nodes - 3)),
        )
        if not shortcut:
            continue
        shortcut_total_nodes = len(shortcut) + 2
        if shortcut_total_nodes >= cut_main_nodes:
            continue
        if preset.avoid_triangles and _has_triangle_cluster(active | set(shortcut), preset.width, preset.height):
            continue

        previous = source
        for coord in shortcut:
            _link(draft.adjacency, previous, coord)
            draft.layers[coord] = "hidden_shortcut"
            active.add(coord)
            previous = coord
        _link(draft.adjacency, previous, target)
        draft.builder_debug.update(
            {
                "secondary_path_strategy": "finish_to_main_shortcut",
                "secondary_path_start": source,
                "secondary_path_target": target,
                "secondary_path_target_index": target_index,
                "secondary_path_nodes": shortcut_total_nodes,
                "secondary_cut_main_nodes": cut_main_nodes,
                "secondary_min_cut_main_nodes": min_cut.min,
            }
        )
        return


def _hidden_shortcut_pairs(
    main_path: list[tuple[int, int]],
    gap: CountRange,
    preset: LayoutPreset,
) -> list[tuple[int, int]]:
    pairs: list[tuple[int, int]] = []
    first_index = max(1, preset.min_distance_from_start)
    last_index = len(main_path) - max(2, preset.min_distance_from_finish)
    for source_index in range(first_index, last_index):
        for target_index in range(source_index + gap.min, min(last_index + 1, source_index + gap.max + 1)):
            if target_index >= len(main_path) - 1:
                continue
            pairs.append((source_index, target_index))
    return pairs


def _find_flower_weave_secondary_path(
    *,
    source: tuple[int, int],
    target: tuple[int, int],
    active: set[tuple[int, int]],
    adjacency: dict[tuple[int, int], set[tuple[int, int]]],
    rng: random.Random,
    preset: LayoutPreset,
    min_nodes: int,
    max_nodes: int,
) -> list[tuple[int, int]] | None:
    if max_nodes < min_nodes:
        return None
    queue: list[tuple[tuple[int, int], list[tuple[int, int]]]] = [(source, [])]
    attempts = 0
    while queue and attempts < max(1200, preset.usable_capacity * 16):
        attempts += 1
        current, path = queue.pop(0)
        if len(path) > max_nodes:
            continue
        candidates = [
            neighbor
            for neighbor in get_hex_neighbors(current[0], current[1], preset.width, preset.height)
            if neighbor is not None and _inside_usable(neighbor, preset)
        ]
        rng.shuffle(candidates)
        candidates.sort(key=lambda coord: (_grid_distance(coord, target), rng.random()))
        for candidate in candidates:
            if candidate == target:
                if (
                    min_nodes <= len(path) <= max_nodes
                    and _flower_weave_secondary_endpoint_supported(
                        source=source,
                        target=target,
                        path=path,
                        adjacency=adjacency,
                        preset=preset,
                    )
                    and not _secondary_path_creates_one_hex_gap(
                        source=source,
                        target=target,
                        path=path,
                        active=active,
                        adjacency=adjacency,
                        width=preset.width,
                        height=preset.height,
                    )
                ):
                    return path
                continue
            if candidate in active or candidate in path:
                continue
            prospective_active = active | set(path)
            active_touch = _walkable_neighbors(candidate, prospective_active, preset.width, preset.height)
            if not active_touch <= {current, target}:
                continue
            if preset.avoid_triangles and _candidate_creates_triangle_cluster(
                candidate, prospective_active, preset.width, preset.height
            ):
                continue
            if not _flower_weave_secondary_step_supported(
                source=source,
                current=current,
                path=path,
                candidate=candidate,
                adjacency=adjacency,
                preset=preset,
            ):
                continue
            secondary_adjacency = _secondary_path_adjacency(adjacency, source, path)
            if _creates_one_hex_gap(
                candidate=candidate,
                linked_to=current,
                active=prospective_active,
                adjacency=secondary_adjacency,
                local_gap_neighbors={current, *path[-2:]},
                width=preset.width,
                height=preset.height,
            ):
                continue
            queue.append((candidate, [*path, candidate]))
    return None


def _secondary_path_adjacency(
    adjacency: dict[tuple[int, int], set[tuple[int, int]]],
    source: tuple[int, int],
    path: list[tuple[int, int]],
) -> dict[tuple[int, int], set[tuple[int, int]]]:
    result = {coord: set(links) for coord, links in adjacency.items()}
    previous = source
    for coord in path:
        _link(result, previous, coord)
        previous = coord
    return result


def _secondary_path_creates_one_hex_gap(
    *,
    source: tuple[int, int],
    target: tuple[int, int],
    path: list[tuple[int, int]],
    active: set[tuple[int, int]],
    adjacency: dict[tuple[int, int], set[tuple[int, int]]],
    width: int,
    height: int,
) -> bool:
    secondary_adjacency = _secondary_path_adjacency(adjacency, source, path)
    secondary_active = active | set(path)
    previous = source
    for coord in [*path, target]:
        if _creates_one_hex_gap(
            candidate=coord,
            linked_to=previous,
            active=secondary_active - {coord},
            adjacency=secondary_adjacency,
            local_gap_neighbors={previous, *path[-2:]},
            width=width,
            height=height,
        ):
            return True
        previous = coord
    return False


def _flower_weave_secondary_step_supported(
    *,
    source: tuple[int, int],
    current: tuple[int, int],
    path: list[tuple[int, int]],
    candidate: tuple[int, int],
    adjacency: dict[tuple[int, int], set[tuple[int, int]]],
    preset: LayoutPreset,
) -> bool:
    if current == source:
        links = set(adjacency.get(source, set())) | {candidate}
        mask = _edge_mask_for_links(source, links, preset.width, preset.height)
        return tuple(mask) in FIRST_LAYER_MOVEMENT_EDGE_MASKS
    previous = source if len(path) == 1 else path[-2]
    mask = _edge_mask_for_links(current, {previous, candidate}, preset.width, preset.height)
    return tuple(mask) in FIRST_LAYER_MOVEMENT_EDGE_MASKS


def _flower_weave_secondary_endpoint_supported(
    *,
    source: tuple[int, int],
    target: tuple[int, int],
    path: list[tuple[int, int]],
    adjacency: dict[tuple[int, int], set[tuple[int, int]]],
    preset: LayoutPreset,
) -> bool:
    if not path:
        return False
    last = path[-1]
    previous = source if len(path) == 1 else path[-2]
    last_mask = _edge_mask_for_links(last, {previous, target}, preset.width, preset.height)
    if tuple(last_mask) not in FIRST_LAYER_MOVEMENT_EDGE_MASKS:
        return False
    target_links = set(adjacency.get(target, set())) | {last}
    target_mask = _edge_mask_for_links(target, target_links, preset.width, preset.height)
    return tuple(target_mask) in FIRST_LAYER_FORK_EDGE_MASKS


def _raw_count_range(raw: dict[str, object]) -> CountRange:
    min_value = int(raw.get("min") or 0)
    target_value = max(min_value, int(raw.get("target") or min_value))
    max_value = max(target_value, int(raw.get("max") or target_value))
    return CountRange(min=min_value, target=target_value, max=max_value)


def _raw_ratio_count_range(raw: dict[str, object], base: int, *, minimum_floor: int = 0) -> CountRange:
    def value(key: str, default: int) -> int:
        raw_value = raw.get(key)
        if isinstance(raw_value, int):
            return max(minimum_floor, raw_value)
        if isinstance(raw_value, float):
            return max(minimum_floor, round(base * raw_value))
        return default

    min_value = value("min", minimum_floor)
    target_value = max(min_value, value("target", min_value))
    max_value = max(target_value, value("max", target_value))
    return CountRange(min=min_value, target=target_value, max=max_value)


def _find_shortcut_path(
    *,
    source: tuple[int, int],
    target: tuple[int, int],
    active: set[tuple[int, int]],
    rng: random.Random,
    preset: LayoutPreset,
    min_nodes: int,
    max_nodes: int,
) -> list[tuple[int, int]] | None:
    stack: list[tuple[tuple[int, int], list[tuple[int, int]]]] = [(source, [])]
    attempts = 0
    while stack and attempts < 2000:
        attempts += 1
        current, path = stack.pop()
        if len(path) > max_nodes:
            continue
        candidates = [
            neighbor
            for neighbor in get_hex_neighbors(current[0], current[1], preset.width, preset.height)
            if neighbor is not None and _inside_usable(neighbor, preset)
        ]
        rng.shuffle(candidates)
        candidates.sort(key=lambda coord: _grid_distance(coord, target), reverse=True)
        for candidate in candidates:
            if candidate == target:
                if min_nodes <= len(path) <= max_nodes and _shortcut_endpoint_supported(source, target, path, preset):
                    return path
                continue
            if candidate in active or candidate in path:
                continue
            prospective_active = active | set(path)
            active_touch = _walkable_neighbors(candidate, prospective_active, preset.width, preset.height)
            if not active_touch <= {current, target}:
                continue
            if preset.avoid_triangles and _candidate_creates_triangle_cluster(
                candidate, prospective_active, preset.width, preset.height
            ):
                continue
            if not _shortcut_step_supported(current, path, candidate, source, preset):
                continue
            stack.append((candidate, [*path, candidate]))
    return None


def _shortcut_step_supported(
    current: tuple[int, int],
    path: list[tuple[int, int]],
    candidate: tuple[int, int],
    source: tuple[int, int],
    preset: LayoutPreset,
) -> bool:
    if current == source:
        mask = _edge_mask_for_links(source, {candidate}, preset.width, preset.height)
        return any(mask[index] == 1 for index in range(6))
    previous = source if len(path) == 1 else path[-2]
    mask = _edge_mask_for_links(current, {previous, candidate}, preset.width, preset.height)
    return tuple(mask) in FIRST_LAYER_MOVEMENT_EDGE_MASKS


def _shortcut_endpoint_supported(
    source: tuple[int, int],
    target: tuple[int, int],
    path: list[tuple[int, int]],
    preset: LayoutPreset,
) -> bool:
    if not path:
        return False
    last = path[-1]
    last_previous = source if len(path) == 1 else path[-2]
    last_mask = _edge_mask_for_links(last, {last_previous, target}, preset.width, preset.height)
    return tuple(last_mask) in FIRST_LAYER_MOVEMENT_EDGE_MASKS


def _place_required_slots(*, draft: _GraphDraft, preset: LayoutPreset, rng: random.Random) -> None:
    draft.slots[draft.start] = "entrance_room"
    draft.slots[draft.finish] = "rift_heart_room"


def _place_alternating_base_slots(draft: _GraphDraft, preset: LayoutPreset) -> None:
    config = dict(preset.scheme.get("main_path_slots") or {})
    if not bool(config.get("alternate")):
        return
    movement_slot = str(config.get("movement_slot") or "movement")
    event_slot = str(config.get("event_slot") or "event_room")
    for index, coord in enumerate(draft.main_path[1:-1], start=1):
        draft.slots.setdefault(coord, movement_slot if index % 2 == 1 else event_slot)


def _place_interest_slots(*, draft: _GraphDraft, preset: LayoutPreset, rng: random.Random) -> None:
    slots: dict[tuple[int, int], str] = getattr(draft, "slots", {})
    distribution = dict(preset.scheme.get("interest_distribution") or {})
    excluded_roles = set(distribution.get("exclude_graph_roles") or [])
    candidates = [
        coord for coord in draft.adjacency if coord not in slots and _graph_role(coord, draft) not in excluded_roles
    ]
    preferred_layers = set(distribution.get("prefer_path_layers") or [])
    candidates.sort(
        key=lambda coord: (
            draft.layers.get(coord) not in preferred_layers,
            draft.main_path.index(coord) if coord in draft.main_path else 999,
        )
    )

    interest_ratio = dict(distribution.get("interest_ratio") or {})
    target_interest = _ratio_value(interest_ratio, "target", len(candidates), 0)
    target_interest = max(0, min(len(candidates), target_interest))
    weighted_slots = _weighted_interest_slots(dict(preset.scheme.get("interest_slots") or {}))
    if not weighted_slots:
        return

    for coord in draft.adjacency:
        if coord in slots:
            continue
        if _graph_role(coord, draft) == "dead_end":
            slots[coord] = _weighted_choice(weighted_slots, rng)

    spacing = dict(distribution.get("spacing") or {})
    min_spacing = max(1, int(spacing.get("min") or 1))
    chosen: list[tuple[int, int]] = []
    for coord in candidates:
        if len(chosen) >= target_interest:
            break
        if _too_close_to_interest(coord, chosen, draft, min_spacing):
            continue
        chosen.append(coord)

    for coord in chosen:
        slots[coord] = _weighted_choice(weighted_slots, rng)
    draft.slots = slots


def _draft_to_layout(*, draft: _GraphDraft, preset: LayoutPreset) -> HexLayoutDTO:
    nodes: list[HexLayoutNodeDTO] = []
    for coord in _ordered_graph_nodes(draft):
        graph_role = _graph_role(coord, draft)
        path_layer = draft.layers.get(coord, "main")
        content_slot = draft.slots.get(coord) or (
            "branch_end" if path_layer == "branch" and graph_role == "dead_end" else "movement"
        )
        edge_mask = _open_edge_mask(coord, draft.adjacency, preset.width, preset.height)
        visibility = "visible"
        nodes.append(
            HexLayoutNodeDTO(
                coord=coord,
                edges=edge_mask,
                graph_role=graph_role,
                path_layer=path_layer,
                visibility=visibility,
                content_slot=content_slot,
            )
        )

    return HexLayoutDTO(
        scale_key=preset.scale_key,
        difficulty_key=preset.difficulty_key,
        scheme_key=preset.scheme_key,
        width=preset.width,
        height=preset.height,
        border=preset.border,
        start=draft.start,
        finish=draft.finish,
        main_path=draft.main_path,
        nodes=nodes,
        builder_debug=draft.builder_debug,
    )


def _candidate_keeps_path_topology(
    path: list[tuple[int, int]],
    candidate: tuple[int, int],
    preset: LayoutPreset,
) -> bool:
    if len(path) < 2:
        return True
    current = path[-1]
    previous = path[-2]
    current_mask = _edge_mask_for_links(current, {previous, candidate}, preset.width, preset.height)
    return tuple(current_mask) in FIRST_LAYER_MOVEMENT_EDGE_MASKS


def _path_uses_supported_topology(path: list[tuple[int, int]], preset: LayoutPreset) -> bool:
    if len(path) < 3:
        return False
    for index, coord in enumerate(path[1:-1], start=1):
        mask = _edge_mask_for_links(coord, {path[index - 1], path[index + 1]}, preset.width, preset.height)
        if tuple(mask) not in FIRST_LAYER_MOVEMENT_EDGE_MASKS:
            return False
    return True


def _branch_candidate_keeps_topology(
    draft: _GraphDraft,
    current: tuple[int, int],
    candidate: tuple[int, int],
    junction: tuple[int, int],
    preset: LayoutPreset,
) -> bool:
    links = set(draft.adjacency.get(current, set())) | {candidate}
    mask = _edge_mask_for_links(current, links, preset.width, preset.height)
    if current == junction:
        return tuple(mask) in FIRST_LAYER_FORK_EDGE_MASKS
    return tuple(mask) in FIRST_LAYER_MOVEMENT_EDGE_MASKS


def _creates_one_hex_gap(
    *,
    candidate: tuple[int, int],
    linked_to: tuple[int, int],
    active: set[tuple[int, int]],
    adjacency: dict[tuple[int, int], set[tuple[int, int]]],
    local_gap_neighbors: set[tuple[int, int]],
    width: int,
    height: int,
) -> bool:
    prospective = set(active)
    prospective.add(candidate)
    prospective_adjacency = {coord: set(links) for coord, links in adjacency.items()}
    _link(prospective_adjacency, linked_to, candidate)

    empty_neighbors = [
        neighbor
        for neighbor in get_hex_neighbors(candidate[0], candidate[1], width, height)
        if neighbor is not None and neighbor not in prospective
    ]
    for empty_coord in empty_neighbors:
        touching = [
            neighbor
            for neighbor in get_hex_neighbors(empty_coord[0], empty_coord[1], width, height)
            if neighbor in prospective
        ]
        if candidate not in touching or len(touching) < 2:
            continue
        for first_index, first in enumerate(touching):
            first_links = prospective_adjacency.get(first, set())
            for second in touching[first_index + 1 :]:
                if first in local_gap_neighbors or second in local_gap_neighbors:
                    continue
                if second not in first_links:
                    return True
    return False


def _edge_mask_for_links(
    coord: tuple[int, int],
    linked: set[tuple[int, int]],
    width: int,
    height: int,
) -> list[int]:
    return [1 if neighbor in linked else 0 for neighbor in get_hex_neighbors(coord[0], coord[1], width, height)]


def _inside_usable(coord: tuple[int, int], preset: LayoutPreset) -> bool:
    x, y = coord
    return preset.border <= x < preset.width - preset.border and preset.border <= y < preset.height - preset.border


def _path_adjacency(path: list[tuple[int, int]]) -> dict[tuple[int, int], set[tuple[int, int]]]:
    adjacency = {coord: set() for coord in path}
    for source, target in zip(path, path[1:], strict=False):
        _link(adjacency, source, target)
    return adjacency


def _link(
    adjacency: dict[tuple[int, int], set[tuple[int, int]]], source: tuple[int, int], target: tuple[int, int]
) -> None:
    adjacency.setdefault(source, set()).add(target)
    adjacency.setdefault(target, set()).add(source)


def _ordered_graph_nodes(draft: _GraphDraft) -> list[tuple[int, int]]:
    ordered = list(draft.main_path)
    for coord in draft.adjacency:
        if coord not in ordered:
            ordered.append(coord)
    return ordered


def _graph_role(coord: tuple[int, int], draft: _GraphDraft) -> str:
    if coord == draft.start:
        return "start"
    if coord == draft.finish:
        return "finish"
    degree = len(draft.adjacency.get(coord, set()))
    if degree >= 3:
        return "fork"
    if degree <= 1:
        return "dead_end"
    return "path"


def _visibility_for(
    coord: tuple[int, int],
    graph_role: str,
    path_layer: str,
    content_slot: str,
    hidden: dict[str, object],
) -> str:
    if graph_role in {"start", "finish", "fork"}:
        return "visible"
    if path_layer == "main":
        return "visible"
    chance = (
        float(hidden.get("hidden_room_chance") or 0.0)
        if content_slot != "movement"
        else float(hidden.get("hidden_branch_chance") or 0.0)
    )
    marker = (coord[0] * 37 + coord[1] * 17) % 100
    return "hidden" if marker < round(chance * 100) else "visible"


def _open_edge_mask(
    coord: tuple[int, int],
    adjacency: dict[tuple[int, int], set[tuple[int, int]]],
    width: int,
    height: int,
) -> list[int]:
    linked = adjacency.get(coord, set())
    return [1 if neighbor in linked else 0 for neighbor in get_hex_neighbors(coord[0], coord[1], width, height)]


def _straight_run_with_candidate(
    path: list[tuple[int, int]],
    candidate: tuple[int, int],
    width: int,
    height: int,
) -> int:
    if len(path) < 2:
        return 1
    direction = get_hex_direction(path[-1], candidate, width, height)
    run = 1
    for source, target in zip(reversed(path[:-1]), reversed(path[1:]), strict=False):
        if get_hex_direction(source, target, width, height) != direction:
            break
        run += 1
    return run


def _turns_before_min_straight_run(
    path: list[tuple[int, int]],
    candidate: tuple[int, int],
    preset: LayoutPreset,
) -> bool:
    if preset.min_straight_run <= 1 or len(path) < 2:
        return False
    previous_direction = get_hex_direction(path[-2], path[-1], preset.width, preset.height)
    next_direction = get_hex_direction(path[-1], candidate, preset.width, preset.height)
    if next_direction == previous_direction:
        return False
    if len(_path_straight_runs(path, preset.width, preset.height)) <= 1:
        return False
    return _current_straight_run(path, preset.width, preset.height) < preset.min_straight_run


def _current_straight_run(path: list[tuple[int, int]], width: int, height: int) -> int:
    if len(path) < 2:
        return 0
    direction = get_hex_direction(path[-2], path[-1], width, height)
    run = 1
    for source, target in zip(reversed(path[:-2]), reversed(path[1:-1]), strict=False):
        if get_hex_direction(source, target, width, height) != direction:
            break
        run += 1
    return run


def _walkable_neighbors(
    coord: tuple[int, int],
    walkable: set[tuple[int, int]],
    width: int,
    height: int,
) -> set[tuple[int, int]]:
    return {neighbor for neighbor in get_hex_neighbors(coord[0], coord[1], width, height) if neighbor in walkable}


def _touches_walkable(
    coord: tuple[int, int],
    walkable: set[tuple[int, int]],
    width: int,
    height: int,
) -> bool:
    return bool(_walkable_neighbors(coord, walkable, width, height))


def _grid_distance(source: tuple[int, int], target: tuple[int, int]) -> int:
    return abs(source[0] - target[0]) + abs(source[1] - target[1])


def _select_void_decor_coords(
    *,
    rng: random.Random,
    layout: HexLayoutDTO,
    walkable_set: set[tuple[int, int]],
    fill_ratio: float,
) -> set[tuple[int, int]]:
    if fill_ratio <= 0:
        return set()
    # Keep floating fragments near the labyrinth, beyond its adjacent contour.
    # A shared budget applies to the whole floor, including terminal rooms.
    frontier = set(walkable_set)
    seen = set(walkable_set)
    candidate_set: set[tuple[int, int]] = set()
    for distance in range(1, 4):
        frontier = {
            neighbor
            for coord in frontier
            for neighbor in get_hex_neighbors(*coord, layout.width, layout.height)
            if neighbor is not None and neighbor not in seen
        }
        seen.update(frontier)
        if distance >= 2:
            candidate_set.update(
                coord for coord in frontier if not is_outer_frame_coord(*coord, layout.width, layout.height)
            )
    candidates = sorted(candidate_set)
    rng.shuffle(candidates)
    target_count = min(3, max(2, round(len(candidates) * min(1.0, fill_ratio))))
    return set(candidates[:target_count])


def _is_bend(path: list[tuple[int, int]], index: int, width: int, height: int) -> bool:
    if index <= 0 or index >= len(path) - 1:
        return False
    in_direction = get_hex_direction(path[index - 1], path[index], width, height)
    out_direction = get_hex_direction(path[index], path[index + 1], width, height)
    return in_direction != out_direction


def _too_close_to_interest(
    coord: tuple[int, int],
    chosen: list[tuple[int, int]],
    draft: _GraphDraft,
    min_spacing: int,
) -> bool:
    if min_spacing <= 1:
        return False
    index_by_coord = {node: index for index, node in enumerate(_ordered_graph_nodes(draft))}
    coord_index = index_by_coord.get(coord, 0)
    return any(abs(coord_index - index_by_coord.get(existing, 0)) < min_spacing for existing in chosen)


def _weighted_interest_slots(slots: dict[str, object]) -> list[tuple[str, int]]:
    weighted: list[tuple[str, int]] = []
    for slot_key, raw in slots.items():
        if not isinstance(raw, dict):
            continue
        weight = int(raw.get("weight") or 0)
        if weight > 0:
            weighted.append((slot_key, weight))
    return weighted


def _weighted_choice(weighted: list[tuple[str, int]], rng: random.Random) -> str:
    total = sum(weight for _, weight in weighted)
    roll = rng.randint(1, total)
    cursor = 0
    for value, weight in weighted:
        cursor += weight
        if roll <= cursor:
            return value
    return weighted[-1][0]


def _ratio_value(ratio: dict[str, object], key: str, base: int, default: int) -> int:
    value = ratio.get(key)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return round(base * value)
    return default


def _expand_for_supported_blockers(
    *,
    walkable_set: set[tuple[int, int]],
    width: int,
    height: int,
    edge_configurations: set[tuple[int, ...]],
) -> set[tuple[int, int]]:
    result = set(walkable_set)
    changed = True
    while changed:
        changed = False
        for y in range(height):
            for x in range(width):
                coord = (x, y)
                if coord in result or is_outer_frame_coord(x, y, width, height):
                    continue
                needed_edges = [0 if neighbor in result else 1 for neighbor in get_hex_neighbors(x, y, width, height)]
                if 0 in needed_edges and tuple(needed_edges) not in edge_configurations:
                    result.add(coord)
                    changed = True
    return result


class _TileCatalog:
    def __init__(self, tiles: list[dict[str, Any]], catalog: dict[str, Any]) -> None:
        self.tiles = tiles
        self.blockers = [tile for tile in tiles if int(tile.get("walkable") or 0) == 0]
        self.contour_blockers = [
            tile
            for tile in self.blockers
            if "contour" in _tile_path_roles(tile) and "void_decor" not in _tile_path_roles(tile)
        ]
        self.void_decor_blockers = [tile for tile in self.blockers if "void_decor" in _tile_path_roles(tile)]
        self.walkable = [tile for tile in tiles if int(tile.get("walkable") or 0) == 1]
        self.movement = [tile for tile in self.walkable if tile.get("kind") == "movement"]
        self.by_blocker_edges: dict[tuple[int, ...], dict[str, Any]] = {}
        for tile in self.contour_blockers:
            self.by_blocker_edges.setdefault(tuple(_tile_edges(tile)), tile)
        self.blocker_configurations = set(self.by_blocker_edges)
        self.catalog = catalog
        if not self.contour_blockers or not self.walkable:
            raise ValueError("Rift tile set must contain blocker and walkable tiles")

    def select_walkable(self, layout_node: HexLayoutNodeDTO, rng: random.Random) -> dict[str, Any]:
        slot = layout_node.content_slot
        if slot == "transition_room":
            return self._select_level_exit_transition(rng) or self._select_any_walkable(rng)
        if slot == "rift_heart_room":
            return self._select_rift_heart_room(rng) or self._select_any_walkable(rng)
        if slot == "entrance_room":
            return self._select_entrance_room(rng)
        if slot == "guard_before_transition" or slot == "combat_room":
            return self._select_catalog("guard_rooms", rng) or self._select_any_walkable(rng)
        if slot == "resource_room":
            return self._select_catalog("resource_nodes", rng) or self._select_any_walkable(rng)
        if slot == "trap_room":
            return self._select_catalog("traps", rng) or self._select_any_walkable(rng)
        if slot == "buff_room":
            return self._select_catalog("buff_shrines", rng) or self._select_any_walkable(rng)
        if slot == "event_room":
            return self._select_catalog("empty_rooms", rng) or self._select_any_walkable(rng)
        if slot in {"empty_room", "branch_end"}:
            return self._select_catalog("empty_rooms", rng) or self._select_any_walkable(rng)
        return self._select_movement(layout_node, rng)

    def select_filler(self, rng: random.Random) -> dict[str, Any]:
        return self._select_catalog("empty_rooms", rng) or self._select_any_walkable(rng)

    def select_blocker(
        self,
        coord: tuple[int, int],
        walkable_set: set[tuple[int, int]],
        width: int,
        height: int,
    ) -> dict[str, Any]:
        needed_edges = [
            0 if neighbor in walkable_set else 1 for neighbor in get_hex_neighbors(coord[0], coord[1], width, height)
        ]
        if 0 in needed_edges and tuple(needed_edges) in self.by_blocker_edges:
            return self.by_blocker_edges[tuple(needed_edges)]
        return self.contour_blockers[0]

    def select_void_decor(self, rng: random.Random) -> dict[str, Any]:
        return rng.choice(self.void_decor_blockers or self.contour_blockers)

    def _select_movement(self, layout_node: HexLayoutNodeDTO, rng: random.Random) -> dict[str, Any]:
        exact_tiles = [tile for tile in self.movement if _tile_edges(tile) == layout_node.edges]
        if exact_tiles:
            return rng.choice(exact_tiles)
        role = layout_node.graph_role
        if role == "fork":
            fork_tiles = [tile for tile in self.movement if "fork" in str(tile.get("tile_key") or "")]
            if fork_tiles:
                return rng.choice(fork_tiles)
        if role == "dead_end":
            dead_end_tiles = [
                tile
                for tile in self.walkable
                if str(_tile_variant_group(tile)).startswith("hidden_dead_end")
                and _tile_edges(tile) == layout_node.edges
            ]
            if dead_end_tiles:
                return rng.choice(dead_end_tiles)
        path_tiles = [tile for tile in self.movement if "fork" not in str(tile.get("tile_key") or "")]
        return rng.choice(path_tiles or self.movement or self.walkable)

    def _select_catalog(self, key: str, rng: random.Random) -> dict[str, Any] | None:
        ids = list(dict(self.catalog.get(key) or {}).get("all") or [])
        candidates = [tile for tile in self.tiles if tile.get("id") in ids]
        return rng.choice(candidates) if candidates else None

    def _select_catalog_group(self, key: str, group: str, rng: random.Random) -> dict[str, Any] | None:
        ids = list(dict(self.catalog.get(key) or {}).get(group) or [])
        candidates = [tile for tile in self.tiles if tile.get("id") in ids]
        return rng.choice(candidates) if candidates else None

    def _select_entrance_room(self, rng: random.Random) -> dict[str, Any]:
        ids = list(dict(self.catalog.get("empty_rooms") or {}).get("all") or [])
        empty_candidates = [tile for tile in self.tiles if tile.get("id") in ids]
        preferred = [tile for tile in empty_candidates if {"plain_chamber", "cracked_floor"} & _tile_event_tags(tile)]
        return rng.choice(preferred or empty_candidates or self.walkable)

    def _select_level_exit_transition(self, rng: random.Random) -> dict[str, Any] | None:
        return self._select_catalog_group("level_transitions", "exit", rng)

    def _select_rift_heart_room(self, rng: random.Random) -> dict[str, Any] | None:
        event_catalog = dict(dict(self.catalog.get("events") or {}).get("by_event_tag") or {})
        ids = list(event_catalog.get("pre_destroyed") or event_catalog.get("objective") or [])
        candidates = [tile for tile in self.tiles if tile.get("id") in ids and "rift_heart" in _tile_event_tags(tile)]
        return rng.choice(candidates) if candidates else None

    def _select_any_walkable(self, rng: random.Random) -> dict[str, Any]:
        return rng.choice(self.walkable)


def _tile_asset_path(tile: dict[str, object]) -> str:
    file_name = tile.get("file")
    if not isinstance(file_name, str) or not file_name:
        raise ValueError(f"Rift tile {tile.get('id')} has no file name")
    return f"tiles/{file_name}"


def _tile_edges(tile: dict[str, object]) -> list[int]:
    edges = tile.get("edges")
    if not isinstance(edges, list) or len(edges) != 6 or any(edge not in (0, 1) for edge in edges):
        raise ValueError(f"Rift tile {tile.get('id')} has invalid edges")
    return [int(edge) for edge in edges]


def _tile_path_roles(tile: dict[str, object]) -> set[str]:
    structure = tile.get("structure")
    if not isinstance(structure, dict):
        return set()
    roles = structure.get("path_roles")
    if not isinstance(roles, list):
        return set()
    return {str(role) for role in roles}


def _tile_event_tags(tile: dict[str, object]) -> set[str]:
    placement = tile.get("placement")
    if not isinstance(placement, dict):
        return set()
    tags = placement.get("event_tags")
    if not isinstance(tags, list):
        return set()
    return {str(tag) for tag in tags}


def _tile_variant_group(tile: dict[str, object]) -> str:
    structure = tile.get("structure")
    if not isinstance(structure, dict):
        return ""
    value = structure.get("variant_group")
    return str(value) if value else ""


def _tile_content_subtype(tile: dict[str, object], content_slot: str) -> str:
    if content_slot == "entrance_room":
        return "initial_portal_floor"
    if content_slot == "transition_room":
        variant_group = _tile_variant_group(tile)
        if variant_group == "level_exit":
            return "floor_exit"
        if variant_group == "level_entry":
            return "floor_entry"
        if variant_group == "hidden_level_drop":
            return "hidden_level_drop"
        return "level_transition"
    if "rift_heart" in _tile_event_tags(tile):
        if "post_destroyed" in _tile_event_tags(tile):
            return "rift_heart_destroyed"
        return "rift_heart_alive"
    return _tile_variant_group(tile) or content_slot


def _tile_overlay_key(content_slot: str, content_subtype: str) -> str:
    if content_slot == "entrance_room":
        return "rift_portal"
    if content_subtype == "rift_heart_alive":
        return "rift_crystal"
    return ""


def _node_title(
    coord: tuple[int, int],
    start: tuple[int, int],
    finish: tuple[int, int],
    is_walkable: bool,
    content_slot: str,
) -> str:
    if coord == start:
        return "Входной портал"
    if coord == finish:
        return "Переход рифта"
    if not is_walkable:
        return "Бездна"
    return {
        "rift_heart_room": "Сердце разлома",
        "guard_before_transition": "Страж перехода",
        "resource_room": "Ресурсная комната",
        "trap_room": "Опасная комната",
        "buff_room": "Святилище",
        "combat_room": "Охраняемый зал",
        "empty_room": "Пустая камера",
    }.get(content_slot, "Осколок разлома")


def _node_description(is_walkable: bool, content_slot: str) -> str:
    if not is_walkable:
        return "Просто пустота."
    return {
        "rift_heart_room": "Здесь держится сердце этого разлома.",
        "transition_room": "Здесь можно перейти глубже в рифт.",
        "guard_before_transition": "Перед переходом стоит охрана.",
        "resource_room": "Здесь может быть источник ресурсов.",
        "trap_room": "Комната выглядит подозрительно.",
        "buff_room": "В центре заметен древний фокус силы.",
        "combat_room": "Место подходит для опасной встречи.",
        "empty_room": "Разрушенная часть рифта без явного события.",
    }.get(content_slot, "Пустошь, парящая в космосе.")
