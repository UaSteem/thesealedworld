from __future__ import annotations

from dataclasses import dataclass

RIFT_LAYOUT_SCALE_ORDER: tuple[str, ...] = ("solo", "group", "raid")

RIFT_GEOMETRY_PATTERNS: dict[str, dict[str, object]] = {
    "spike_comb": {
        "status": "implemented",
        "min_scale": "solo",
        "shape_layers": ["main_path", "spike_spurs"],
        "description": "Main path with short 2-3 node movement spurs on suitable bends.",
    },
    "ring_detour": {
        "status": "implemented",
        "min_scale": "solo",
        "shape_layers": ["main_path", "flower_loops"],
        "description": "Main path plus a loop around a void pocket.",
    },
    "ring_spikes": {
        "status": "planned",
        "min_scale": "group",
        "shape_layers": ["main_path", "flower_loops", "spike_spurs"],
        "description": "Loop geometry with short movement spurs on useful bends.",
    },
    "switch_gate": {
        "status": "planned",
        "min_scale": "solo",
        "shape_layers": ["main_path", "required_branch"],
        "description": "Main path with one far required geometry branch for a future gate/switch purpose.",
    },
    "half_ring_poi": {
        "status": "planned",
        "min_scale": "solo",
        "shape_layers": ["main_path", "half_loop_branch"],
        "description": "Required side branch bends around a void pocket as a half ring.",
    },
    "double_poi": {
        "status": "planned",
        "min_scale": "group",
        "shape_layers": ["main_path", "required_branch"],
        "description": "Two required side branches separated across the route.",
    },
    "figure_eight": {
        "status": "planned",
        "min_scale": "group",
        "shape_layers": ["main_path", "loop", "loop"],
        "description": "Two loops sharing or nearly sharing a central junction.",
    },
    "braid": {
        "status": "planned",
        "min_scale": "group",
        "shape_layers": ["main_path", "parallel_path"],
        "description": "Two paths split and merge while keeping spacing readable.",
    },
    "web_core": {
        "status": "planned",
        "min_scale": "group",
        "shape_layers": ["center_start", "radial_spokes", "web_links"],
        "description": "Center start with 3-4 radial paths and optional links between spokes.",
    },
    "hub_spokes": {
        "status": "planned",
        "min_scale": "group",
        "shape_layers": ["central_hub", "radial_spokes"],
        "description": "Central hub with several spokes, where one spoke continues toward the finish.",
    },
    "crescent": {
        "status": "planned",
        "min_scale": "group",
        "shape_layers": ["main_path", "large_void_arc"],
        "description": "A broad arc around a larger void pocket.",
    },
    "lock_shortcut": {
        "status": "planned",
        "min_scale": "group",
        "shape_layers": ["main_path", "shortcut_path"],
        "description": "Long path plus a separate shortcut shape. Runtime lock logic is not part of this layer.",
    },
    "resource_pocket": {
        "status": "planned",
        "min_scale": "solo",
        "shape_layers": ["main_path", "side_pockets"],
        "description": "Several small movement-only side pockets.",
    },
}


def available_geometry_pattern_keys(scale_key: str) -> list[str]:
    if scale_key not in RIFT_LAYOUT_SCALE_ORDER:
        raise ValueError(f"Unknown rift layout scale: {scale_key}")
    scale_index = RIFT_LAYOUT_SCALE_ORDER.index(scale_key)
    return [
        key
        for key, pattern in RIFT_GEOMETRY_PATTERNS.items()
        if RIFT_LAYOUT_SCALE_ORDER.index(str(pattern["min_scale"])) <= scale_index
    ]


def active_geometry_pattern_schemes(scale_key: str) -> dict[str, str]:
    if scale_key not in RIFT_LAYOUT_SCALES:
        raise ValueError(f"Unknown rift layout scale: {scale_key}")

    pattern_schemes: dict[str, str] = {}
    for scheme_key in [str(value) for value in RIFT_LAYOUT_SCALES[scale_key].get("scheme_keys") or []]:
        scheme = RIFT_LAYOUT_SCHEMES[scheme_key]
        pattern_key = scheme.get("geometry_pattern")
        if not pattern_key:
            continue
        pattern_key = str(pattern_key)
        if pattern_key in available_geometry_pattern_keys(scale_key):
            pattern_schemes.setdefault(pattern_key, scheme_key)
    return pattern_schemes


def active_geometry_pattern_keys(scale_key: str) -> list[str]:
    active_schemes = active_geometry_pattern_schemes(scale_key)
    return [pattern_key for pattern_key in RIFT_GEOMETRY_PATTERNS if pattern_key in active_schemes]


def resolve_scheme_for_geometry_pattern(scale_key: str, pattern_key: str) -> str:
    active_schemes = active_geometry_pattern_schemes(scale_key)
    try:
        return active_schemes[pattern_key]
    except KeyError as exc:
        raise ValueError(f"Geometry pattern '{pattern_key}' is not active for scale '{scale_key}'") from exc


RIFT_LAYOUT_SCALES: dict[str, dict[str, object]] = {
    "solo": {
        "grid": {"width": 12, "height": 12, "border": 1},
        "difficulties": {
            "easy": {"level_count": {"min": 1, "max": 2}},
            "medium": {"level_count": {"min": 3, "max": 5}},
            "hard": {"level_count": {"min": 6, "max": 10}},
        },
        "scheme_keys": [
            "side_spurs",
            "double_fork",
            "branch_toward_finish",
            "short_detour",
            "long_winding_path",
            "hidden_shortcut",
            "flower_weave",
            "flower_weave_plus_ring",
            "dev_switch_gate",
            "dev_half_ring_poi",
            "dev_resource_pocket",
        ],
        "random_scheme_keys": [
            "flower_weave",
            "flower_weave_plus_ring",
            "dev_half_ring_poi",
            "dev_resource_pocket",
        ],
    },
    "group": {
        "grid": {"width": 15, "height": 15, "border": 1},
        "difficulties": {
            "easy": {"level_count": {"min": 1, "max": 2}},
            "medium": {"level_count": {"min": 3, "max": 5}},
            "hard": {"level_count": {"min": 6, "max": 10}},
        },
        "scheme_keys": [
            "double_fork",
            "branch_toward_finish",
            "short_detour",
            "long_winding_path",
            "hidden_shortcut",
            "flower_weave",
            "flower_weave_plus_ring",
            "dev_half_ring_poi",
            "dev_resource_pocket",
        ],
        "random_scheme_keys": [
            "flower_weave",
        ],
    },
}


RIFT_LAYOUT_SCHEMES: dict[str, dict[str, object]] = {
    "side_spurs": {
        "difficulty": "easy",
        "path_graph": {
            "main_path_node_ratio": {"min": 0.15, "target": 0.17, "max": 0.19},
            "fork_ratio": {"min": 0.025, "target": 0.03, "max": 0.035},
            "max_straight_run": 2,
            "avoid_triangles": True,
            "fork_allowed_on": ["main_path_bend"],
            "min_distance_from_start_ratio": {"min": 0.16, "target": 0.18, "max": 0.2},
            "min_distance_from_finish_ratio": {"min": 0.16, "target": 0.18, "max": 0.2},
            "min_distance_between_forks_ratio": {"min": 0.14, "target": 0.16, "max": 0.18},
        },
        "branches": {
            "length_ratio": {"min": 0.01, "target": 0.01, "max": 0.01},
            "first_steps_away_from_main": {"min": 1, "target": 1, "max": 1},
        },
        "void_decor": {"fill_ratio": 0.35},
    },
    "double_fork": {
        "difficulty": "medium",
        "path_graph": {
            "main_path_node_ratio": {"min": 0.15, "target": 0.17, "max": 0.19},
            "fork_ratio": {"min": 0.01, "target": 0.02, "max": 0.02},
            "max_straight_run": 2,
            "avoid_triangles": True,
            "fork_allowed_on": ["main_path_bend"],
            "min_distance_from_start_ratio": {"min": 0.16, "target": 0.18, "max": 0.2},
            "min_distance_from_finish_ratio": {"min": 0.16, "target": 0.18, "max": 0.2},
            "min_distance_between_forks_ratio": {"min": 0.18, "target": 0.2, "max": 0.24},
        },
        "branches": {
            "length_ratio": {"min": 0.03, "target": 0.04, "max": 0.05},
            "first_steps_away_from_main": {"min": 2, "target": 2, "max": 3},
        },
        "void_decor": {"fill_ratio": 0.35},
    },
    "branch_toward_finish": {
        "difficulty": "medium",
        "path_graph": {
            "main_path_node_ratio": {"min": 0.15, "target": 0.16, "max": 0.18},
            "fork_ratio": {"min": 0.01, "target": 0.01, "max": 0.02},
            "max_straight_run": 2,
            "avoid_triangles": True,
            "fork_allowed_on": ["main_path_bend"],
            "min_distance_from_start_ratio": {"min": 0.16, "target": 0.18, "max": 0.2},
            "min_distance_from_finish_ratio": {"min": 0.16, "target": 0.18, "max": 0.2},
            "min_distance_between_forks_ratio": {"min": 0.18, "target": 0.2, "max": 0.24},
        },
        "branches": {
            "length_ratio": {"min": 0.04, "target": 0.05, "max": 0.06},
            "first_steps_away_from_main": {"min": 2, "target": 3, "max": 3},
            "prefer_toward_finish": True,
        },
        "void_decor": {"fill_ratio": 0.35},
    },
    "short_detour": {
        "difficulty": "easy",
        "path_graph": {
            "main_path_node_ratio": {"min": 0.14, "target": 0.15, "max": 0.17},
            "fork_ratio": {"min": 0.01, "target": 0.01, "max": 0.02},
            "max_straight_run": 2,
            "avoid_triangles": True,
            "fork_allowed_on": ["main_path_bend"],
            "min_distance_from_start_ratio": {"min": 0.16, "target": 0.18, "max": 0.2},
            "min_distance_from_finish_ratio": {"min": 0.16, "target": 0.18, "max": 0.2},
            "min_distance_between_forks_ratio": {"min": 0.22, "target": 0.24, "max": 0.26},
        },
        "branches": {
            "length_ratio": {"min": 0.02, "target": 0.03, "max": 0.03},
            "first_steps_away_from_main": {"min": 2, "target": 2, "max": 2},
        },
        "void_decor": {"fill_ratio": 0.4},
    },
    "long_winding_path": {
        "difficulty": "medium",
        "path_graph": {
            "main_path_node_ratio": {"min": 0.17, "target": 0.18, "max": 0.19},
            "fork_ratio": {"min": 0.01, "target": 0.01, "max": 0.01},
            "max_straight_run": 2,
            "avoid_triangles": True,
            "fork_allowed_on": ["main_path_bend"],
            "min_distance_from_start_ratio": {"min": 0.2, "target": 0.22, "max": 0.24},
            "min_distance_from_finish_ratio": {"min": 0.16, "target": 0.18, "max": 0.2},
            "min_distance_between_forks_ratio": {"min": 0.22, "target": 0.24, "max": 0.26},
        },
        "branches": {
            "length_ratio": {"min": 0.03, "target": 0.04, "max": 0.05},
            "first_steps_away_from_main": {"min": 2, "target": 3, "max": 3},
        },
        "void_decor": {"fill_ratio": 0.3},
    },
    "hidden_shortcut": {
        "difficulty": "medium",
        "path_graph": {
            "main_path_node_ratio": {"min": 0.15, "target": 0.16, "max": 0.17},
            "fork_ratio": {"min": 0.01, "target": 0.01, "max": 0.02},
            "max_straight_run": 2,
            "avoid_triangles": True,
            "fork_allowed_on": ["main_path_bend"],
            "min_distance_from_start_ratio": {"min": 0.16, "target": 0.18, "max": 0.2},
            "min_distance_from_finish_ratio": {"min": 0.16, "target": 0.18, "max": 0.2},
            "min_distance_between_forks_ratio": {"min": 0.18, "target": 0.2, "max": 0.24},
        },
        "branches": {
            "length_ratio": {"min": 0.02, "target": 0.03, "max": 0.04},
            "first_steps_away_from_main": {"min": 2, "target": 2, "max": 3},
        },
        "hidden_shortcut": {
            "count": {"min": 1, "target": 1, "max": 1},
            "length_ratio": {"min": 0.02, "target": 0.04, "max": 0.06},
            "main_gap_ratio": {"min": 0.18, "target": 0.26, "max": 0.34},
            "hidden_prefix_nodes": 2,
        },
        "void_decor": {"fill_ratio": 0.32},
    },
    "flower_weave": {
        "geometry_pattern": "spike_comb",
        "difficulty": "medium",
        "path_graph": {
            "main_path_node_ratio": {"min": 0.17, "target": 0.17, "max": 0.17},
            "main_path_odd": True,
            "fork_ratio": {"min": 0.0, "target": 0.0, "max": 0.0},
            "min_straight_run": 2,
            "max_straight_run": 3,
            "avoid_triangles": True,
            "fork_allowed_on": ["main_path_bend"],
            "min_distance_from_start_ratio": {"min": 0.14, "target": 0.14, "max": 0.14},
            "min_distance_from_finish_ratio": {"min": 0.14, "target": 0.14, "max": 0.14},
            "min_distance_between_forks_ratio": {"min": 0.18, "target": 0.18, "max": 0.18},
        },
        "branches": {
            "length_ratio": {"min": 0.0, "target": 0.0, "max": 0.0},
            "first_steps_away_from_main": {"min": 1, "target": 1, "max": 1},
        },
        "secondary_path": {
            "enabled": False,
            "starts_from": "finish",
            "length_ratio": {"min": 0.04, "target": 0.12, "max": 0.20},
            "min_cut_main_nodes_ratio": {"min": 0.07, "target": 0.07, "max": 0.07},
        },
        "spike_spurs": {
            "enabled": True,
            "fork_ratio": {"min": 0.0, "target": 0.04, "max": 0.08},
            "node_budget_ratio": {"min": 0.0, "target": 0.08, "max": 0.24},
            "path_layer": "spike_spur",
            "node_slot": "movement",
            "path_length": {"min": 2, "target": 2, "max": 3},
            "path_length_three_chance": 0.5,
        },
        "void_flowers": {
            "structural_anchor_start": 1,
            "structural_anchor_step": 4,
            "soft_flower_count_by_scale": {
                "solo": {"min": 2, "target": 2, "max": 2},
                "group": {"min": 3, "target": 3, "max": 3},
            },
            "soft_center_policy": "high_cost",
            "soft_center_cost": 36,
            "soft_petal_cost": 12,
            "soft_outer_cost": 3,
            "soft_min_center_gap": 2,
        },
        "void_decor": {"fill_ratio": 0.35},
    },
    "flower_weave_plus_ring": {
        "geometry_pattern": "ring_detour",
        "difficulty": "medium",
        "path_graph": {
            "main_path_node_ratio": {"min": 0.17, "target": 0.17, "max": 0.17},
            "main_path_odd": True,
            "fork_ratio": {"min": 0.0, "target": 0.0, "max": 0.0},
            "min_straight_run": 2,
            "max_straight_run": 3,
            "avoid_triangles": True,
            "fork_allowed_on": ["main_path_bend"],
            "min_distance_from_start_ratio": {"min": 0.14, "target": 0.14, "max": 0.14},
            "min_distance_from_finish_ratio": {"min": 0.14, "target": 0.14, "max": 0.14},
            "min_distance_between_forks_ratio": {"min": 0.18, "target": 0.18, "max": 0.18},
        },
        "branches": {
            "length_ratio": {"min": 0.0, "target": 0.0, "max": 0.0},
            "first_steps_away_from_main": {"min": 1, "target": 1, "max": 1},
        },
        "secondary_path": {
            "enabled": False,
            "starts_from": "finish",
            "length_ratio": {"min": 0.04, "target": 0.12, "max": 0.20},
            "min_cut_main_nodes_ratio": {"min": 0.07, "target": 0.07, "max": 0.07},
        },
        "flower_loops": {
            "enabled": True,
            "count_ratio": {"min": 0.0, "target": 0.01, "max": 0.015},
            "node_budget_ratio": {"min": 0.04, "target": 0.07, "max": 0.1},
            "average_added_nodes": 6,
            "inner_radius": 1,
            "ring_radius": 2,
            "min_added_nodes": 4,
            "max_added_nodes": 9,
            "min_main_path_gap_ratio": {"min": 0.22, "target": 0.24, "max": 0.28},
            "contact_count": 2,
            "required": True,
            "visibility": "visible",
            "path_layer": "flower_loop",
        },
        "void_flowers": {
            "structural_anchor_start": 1,
            "structural_anchor_step": 4,
            "soft_flower_count_by_scale": {
                "solo": {"min": 2, "target": 2, "max": 2},
                "group": {"min": 3, "target": 3, "max": 3},
            },
            "soft_center_policy": "high_cost",
            "soft_center_cost": 36,
            "soft_petal_cost": 12,
            "soft_outer_cost": 3,
            "soft_min_center_gap": 2,
        },
        "void_decor": {"fill_ratio": 0.35},
    },
    "dev_switch_gate": {
        "geometry_pattern": "switch_gate",
        "difficulty": "medium",
        "path_graph": {
            "main_path_node_ratio": {"min": 0.17, "target": 0.17, "max": 0.17},
            "main_path_odd": True,
            "fork_ratio": {"min": 0.01, "target": 0.02, "max": 0.03},
            "min_straight_run": 2,
            "max_straight_run": 3,
            "avoid_triangles": True,
            "fork_allowed_on": ["main_path_bend"],
            "min_distance_from_start_ratio": {"min": 0.14, "target": 0.14, "max": 0.14},
            "min_distance_from_finish_ratio": {"min": 0.14, "target": 0.14, "max": 0.14},
            "min_distance_between_forks_ratio": {"min": 0.18, "target": 0.18, "max": 0.18},
        },
        "branches": {
            "length_ratio": {"min": 0.02, "target": 0.03, "max": 0.04},
            "first_steps_away_from_main": {"min": 2, "target": 2, "max": 3},
        },
        "void_decor": {"fill_ratio": 0.35},
    },
    "dev_half_ring_poi": {
        "geometry_pattern": "half_ring_poi",
        "difficulty": "medium",
        "path_graph": {
            "main_path_node_ratio": {"min": 0.17, "target": 0.17, "max": 0.17},
            "main_path_odd": True,
            "fork_ratio": {"min": 0.0, "target": 0.0, "max": 0.0},
            "min_straight_run": 2,
            "max_straight_run": 3,
            "avoid_triangles": True,
            "fork_allowed_on": ["main_path_bend"],
            "min_distance_from_start_ratio": {"min": 0.14, "target": 0.14, "max": 0.14},
            "min_distance_from_finish_ratio": {"min": 0.14, "target": 0.14, "max": 0.14},
            "min_distance_between_forks_ratio": {"min": 0.18, "target": 0.18, "max": 0.18},
        },
        "branches": {
            "length_ratio": {"min": 0.0, "target": 0.0, "max": 0.0},
            "first_steps_away_from_main": {"min": 1, "target": 1, "max": 1},
        },
        "flower_loops": {
            "enabled": True,
            "count_ratio": {"min": 0.0, "target": 0.01, "max": 0.015},
            "node_budget_ratio": {"min": 0.04, "target": 0.07, "max": 0.1},
            "average_added_nodes": 6,
            "inner_radius": 1,
            "ring_radius": 2,
            "min_added_nodes": 4,
            "max_added_nodes": 7,
            "min_main_path_gap_ratio": {"min": 0.22, "target": 0.24, "max": 0.28},
            "contact_count": 2,
            "required": True,
            "visibility": "visible",
            "path_layer": "half_ring_poi",
        },
        "void_flowers": {
            "structural_anchor_start": 1,
            "structural_anchor_step": 4,
            "soft_flower_count_by_scale": {
                "solo": {"min": 2, "target": 2, "max": 2},
                "group": {"min": 3, "target": 3, "max": 3},
            },
            "soft_center_policy": "high_cost",
            "soft_center_cost": 36,
            "soft_petal_cost": 12,
            "soft_outer_cost": 3,
            "soft_min_center_gap": 2,
        },
        "void_decor": {"fill_ratio": 0.35},
    },
    "dev_resource_pocket": {
        "geometry_pattern": "resource_pocket",
        "difficulty": "medium",
        "path_graph": {
            "main_path_node_ratio": {"min": 0.17, "target": 0.17, "max": 0.17},
            "main_path_odd": True,
            "fork_ratio": {"min": 0.0, "target": 0.0, "max": 0.0},
            "min_straight_run": 2,
            "max_straight_run": 3,
            "avoid_triangles": True,
            "fork_allowed_on": ["main_path_bend"],
            "min_distance_from_start_ratio": {"min": 0.14, "target": 0.14, "max": 0.14},
            "min_distance_from_finish_ratio": {"min": 0.14, "target": 0.14, "max": 0.14},
            "min_distance_between_forks_ratio": {"min": 0.18, "target": 0.18, "max": 0.18},
        },
        "branches": {
            "length_ratio": {"min": 0.0, "target": 0.0, "max": 0.0},
            "first_steps_away_from_main": {"min": 1, "target": 1, "max": 1},
        },
        "spike_spurs": {
            "enabled": True,
            "fork_ratio": {"min": 0.02, "target": 0.05, "max": 0.1},
            "node_budget_ratio": {"min": 0.04, "target": 0.12, "max": 0.24},
            "path_layer": "resource_pocket",
            "node_slot": "movement",
            "path_length": {"min": 2, "target": 2, "max": 3},
            "path_length_three_chance": 0.5,
        },
        "void_flowers": {
            "structural_anchor_start": 1,
            "structural_anchor_step": 4,
            "soft_flower_count_by_scale": {
                "solo": {"min": 2, "target": 2, "max": 2},
                "group": {"min": 3, "target": 3, "max": 3},
            },
            "soft_center_policy": "high_cost",
            "soft_center_cost": 36,
            "soft_petal_cost": 12,
            "soft_outer_cost": 3,
            "soft_min_center_gap": 2,
        },
        "void_decor": {"fill_ratio": 0.35},
    },
}


@dataclass(frozen=True)
class CountRange:
    min: int
    target: int
    max: int


@dataclass(frozen=True)
class LayoutPreset:
    scale_key: str
    difficulty_key: str
    scheme_key: str
    width: int
    height: int
    border: int
    usable_capacity: int
    active_nodes: CountRange
    main_path_nodes: CountRange
    forks: CountRange
    branch_length: CountRange
    level_count: CountRange
    min_straight_run: int
    max_straight_run: int
    avoid_triangles: bool
    min_distance_from_start: int
    min_distance_from_finish: int
    min_distance_between_forks: int
    branch_first_steps_away_from_main: CountRange
    void_decor_fill_ratio: float
    scheme: dict[str, object]


def resolve_layout_preset(
    *,
    scale_key: str = "solo",
    difficulty_key: str = "easy",
    scheme_key: str | None = None,
) -> LayoutPreset:
    scale = RIFT_LAYOUT_SCALES[scale_key]
    difficulties = dict(scale.get("difficulties") or {})
    if difficulty_key not in difficulties:
        raise ValueError(f"Rift layout difficulty '{difficulty_key}' is not allowed for scale '{scale_key}'")
    scheme_keys = list(scale.get("scheme_keys") or [])
    resolved_scheme_key = scheme_key or str(scheme_keys[0])
    if resolved_scheme_key not in scheme_keys:
        raise ValueError(f"Layout scheme '{resolved_scheme_key}' is not allowed for scale '{scale_key}'")

    scheme = RIFT_LAYOUT_SCHEMES[resolved_scheme_key]
    grid = dict(scale["grid"])  # type: ignore[index]
    width = int(grid["width"])
    height = int(grid["height"])
    border = int(grid.get("border") or 0)
    usable_width = width - border * 2
    usable_height = height - border * 2
    usable_capacity = max(1, usable_width * usable_height)

    path_graph = dict(scheme["path_graph"])  # type: ignore[index]
    branches = dict(scheme.get("branches") or {})
    difficulty = dict(difficulties[difficulty_key])
    level_count = _count_range(
        dict(difficulty.get("level_count") or {"min": 1, "target": 1, "max": 1}), minimum_floor=1
    )
    main_path_nodes = _count_or_ratio_range(
        path_graph,
        count_key="main_path_nodes",
        ratio_key="main_path_node_ratio",
        base=usable_capacity,
        minimum_floor=2,
    )
    if bool(path_graph.get("main_path_odd")):
        main_path_nodes = _odd_count_range(main_path_nodes)
    forks = _count_or_ratio_range(
        path_graph,
        count_key="forks",
        ratio_key="fork_ratio",
        base=usable_capacity,
        minimum_floor=0,
    )
    branch_length = _count_or_ratio_range(
        branches,
        count_key="length",
        ratio_key="length_ratio",
        base=usable_capacity,
        minimum_floor=0,
    )
    branch_first_steps = _count_range(
        dict(branches.get("first_steps_away_from_main") or {"min": 1, "target": 1, "max": 1}),
        minimum_floor=1,
    )
    secondary_path = dict(scheme.get("secondary_path") or {})
    secondary_length = (
        _count_or_ratio_range(
            secondary_path,
            count_key="length",
            ratio_key="length_ratio",
            base=usable_capacity,
            minimum_floor=0,
        )
        if bool(secondary_path.get("enabled"))
        else CountRange(min=0, target=0, max=0)
    )
    flower_loop_node_budget = _flower_loop_node_budget(scheme=scheme, usable_capacity=usable_capacity)
    flower_loop_forks = _flower_loop_forks(scheme=scheme, usable_capacity=usable_capacity)
    spike_spur_node_budget = _spike_spur_node_budget(scheme=scheme, usable_capacity=usable_capacity)
    spike_spur_forks = _spike_spur_forks(scheme=scheme, usable_capacity=usable_capacity)
    forks = CountRange(
        min=forks.min + flower_loop_forks.min + spike_spur_forks.min,
        target=forks.target + flower_loop_forks.target + spike_spur_forks.target,
        max=forks.max + flower_loop_forks.max + spike_spur_forks.max,
    )
    min_distance_from_start = _count_or_ratio_value(
        path_graph,
        count_key="min_distance_from_start",
        ratio_key="min_distance_from_start_ratio",
        base=main_path_nodes.target,
    )
    min_distance_from_finish = _count_or_ratio_value(
        path_graph,
        count_key="min_distance_from_finish",
        ratio_key="min_distance_from_finish_ratio",
        base=main_path_nodes.target,
    )
    min_distance_between_forks = _count_or_ratio_value(
        path_graph,
        count_key="min_distance_between_forks",
        ratio_key="min_distance_between_forks_ratio",
        base=main_path_nodes.target,
    )
    active_nodes = CountRange(
        min=main_path_nodes.min
        + forks.min * branch_length.min
        + secondary_length.min
        + flower_loop_node_budget.min
        + spike_spur_node_budget.min,
        target=main_path_nodes.target
        + forks.target * branch_length.target
        + secondary_length.target
        + flower_loop_node_budget.target
        + spike_spur_node_budget.target,
        max=min(
            usable_capacity,
            main_path_nodes.max
            + forks.max * branch_length.max
            + secondary_length.max
            + flower_loop_node_budget.max
            + spike_spur_node_budget.max,
        ),
    )
    void_decor = dict(scheme.get("void_decor") or {})

    return LayoutPreset(
        scale_key=scale_key,
        difficulty_key=difficulty_key,
        scheme_key=resolved_scheme_key,
        width=width,
        height=height,
        border=border,
        usable_capacity=usable_capacity,
        active_nodes=active_nodes,
        main_path_nodes=main_path_nodes,
        forks=forks,
        branch_length=branch_length,
        level_count=level_count,
        min_straight_run=max(1, int(path_graph.get("min_straight_run") or 1)),
        max_straight_run=int(path_graph.get("max_straight_run") or 2),
        avoid_triangles=bool(path_graph.get("avoid_triangles", True)),
        min_distance_from_start=min_distance_from_start,
        min_distance_from_finish=min_distance_from_finish,
        min_distance_between_forks=min_distance_between_forks,
        branch_first_steps_away_from_main=branch_first_steps,
        void_decor_fill_ratio=float(void_decor.get("fill_ratio") or 0.0),
        scheme=scheme,
    )


def _count_range(
    raw: dict[str, object],
    *,
    minimum_floor: int = 0,
) -> CountRange:
    min_value = max(minimum_floor, int(raw.get("min") or minimum_floor))
    target_value = max(min_value, int(raw.get("target") or min_value))
    max_value = max(target_value, int(raw.get("max") or target_value))
    return CountRange(min=min_value, target=target_value, max=max_value)


def _ratio_count_range(
    ratio: dict[str, object],
    base: int,
    *,
    minimum_floor: int = 0,
) -> CountRange:
    min_value = _ratio_count(ratio, "min", base, minimum_floor)
    target_value = _ratio_count(ratio, "target", base, min_value)
    max_value = _ratio_count(ratio, "max", base, target_value)
    return CountRange(
        min=min_value,
        target=max(min_value, min(target_value, max_value)),
        max=max(max_value, target_value, min_value),
    )


def _ratio_count(ratio: dict[str, object], key: str, base: int, minimum_floor: int) -> int:
    value = ratio.get(key)
    if isinstance(value, int):
        return max(minimum_floor, value)
    if isinstance(value, float):
        return max(minimum_floor, round(base * value))
    return minimum_floor


def _odd_count_range(counts: CountRange) -> CountRange:
    min_value = _next_odd(counts.min)
    target_value = max(min_value, _next_odd(counts.target))
    max_value = max(target_value, _next_odd(counts.max))
    return CountRange(min=min_value, target=target_value, max=max_value)


def _next_odd(value: int) -> int:
    return value if value % 2 == 1 else value + 1


def _count_or_ratio_range(
    raw: dict[str, object],
    *,
    count_key: str,
    ratio_key: str,
    base: int,
    minimum_floor: int = 0,
) -> CountRange:
    if count_key in raw:
        return _count_range(dict(raw[count_key]), minimum_floor=minimum_floor)
    return _ratio_count_range(dict(raw.get(ratio_key) or {}), base, minimum_floor=minimum_floor)


def _count_or_ratio_value(
    raw: dict[str, object],
    *,
    count_key: str,
    ratio_key: str,
    base: int,
) -> int:
    if count_key in raw:
        return int(raw.get(count_key) or 0)
    ratio = _ratio_count_range(dict(raw.get(ratio_key) or {}), base)
    return ratio.min


def _flower_loop_node_budget(*, scheme: dict[str, object], usable_capacity: int) -> CountRange:
    config = dict(scheme.get("flower_loops") or {})
    if not bool(config.get("enabled")):
        return CountRange(min=0, target=0, max=0)
    return _ratio_count_range(dict(config.get("node_budget_ratio") or {}), usable_capacity, minimum_floor=0)


def _flower_loop_forks(*, scheme: dict[str, object], usable_capacity: int) -> CountRange:
    config = dict(scheme.get("flower_loops") or {})
    if not bool(config.get("enabled")):
        return CountRange(min=0, target=0, max=0)
    contact_count = max(0, int(config.get("contact_count") or 0))
    loop_count = _ratio_count_range(dict(config.get("count_ratio") or {}), usable_capacity, minimum_floor=0)
    return CountRange(
        min=loop_count.min * contact_count,
        target=loop_count.target * contact_count,
        max=loop_count.max * contact_count,
    )


def _spike_spur_node_budget(*, scheme: dict[str, object], usable_capacity: int) -> CountRange:
    config = dict(scheme.get("spike_spurs") or {})
    if not bool(config.get("enabled")):
        return CountRange(min=0, target=0, max=0)
    return _ratio_count_range(dict(config.get("node_budget_ratio") or {}), usable_capacity, minimum_floor=0)


def _spike_spur_forks(*, scheme: dict[str, object], usable_capacity: int) -> CountRange:
    config = dict(scheme.get("spike_spurs") or {})
    if not bool(config.get("enabled")):
        return CountRange(min=0, target=0, max=0)
    return _ratio_count_range(dict(config.get("fork_ratio") or {}), usable_capacity, minimum_floor=0)
