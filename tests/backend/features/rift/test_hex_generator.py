import inspect
from pathlib import Path

from src.backend.features.rift.resources.layout_presets import (
    RIFT_GEOMETRY_PATTERNS,
    RIFT_LAYOUT_SCALES,
    RIFT_LAYOUT_SCHEMES,
    active_geometry_pattern_schemes,
    available_geometry_pattern_keys,
    resolve_layout_preset,
)
from src.backend.features.rift.runtime.hex.generation import builder as hex_generator
from src.backend.features.rift.runtime.hex.generation.builder import (
    build_hex_build_plan,
    build_hex_layout,
    build_hex_rift_state,
    generate_hex_rift,
    get_hex_direction,
    get_hex_neighbors,
    load_hex_tile_set,
)


def test_get_hex_neighbors_even_row():
    # Odd-r layout, row 0 is even
    neighbors = get_hex_neighbors(2, 0, width=5, height=5)
    expected = [None, (3, 0), (2, 1), (1, 1), (1, 0), None]

    assert neighbors == expected

def test_get_hex_neighbors_odd_row():
    # Row 1 is odd
    neighbors = get_hex_neighbors(2, 1, width=5, height=5)
    expected = [(3, 0), (3, 1), (3, 2), (2, 2), (1, 1), (2, 0)]

    assert neighbors == expected

def test_generate_hex_rift_valid_path():
    walkable, start, finish = generate_hex_rift(seed="test-seed-1", width=12, height=12)

    # The dev harness keeps one hex border around generated paths.
    assert start[0] == 1
    assert finish[0] == 10

    # Start and finish must be in walkable
    assert start in walkable
    assert finish in walkable
    assert len(walkable) >= 12

    # Path connectivity: there must be a path from start to finish
    # simple BFS search through walkable to verify path is connected
    visited = {start}
    queue = [start]
    while queue:
        curr = queue.pop(0)
        if curr == finish:
            break
        for n in get_hex_neighbors(curr[0], curr[1], width=12, height=12):
            if n in walkable and n not in visited:
                visited.add(n)
                queue.append(n)

    assert finish in visited


def test_generate_hex_rift_avoids_triangles_and_long_straights():
    for i in range(20):
        layout = build_hex_layout(seed=f"shape-seed-{i}")
        preset = resolve_layout_preset(scale_key=layout.scale_key, scheme_key=layout.scheme_key)
        walkable = [node.coord for node in layout.nodes if node.path_layer != "hidden_shortcut"]
        walkable_set = set(walkable)
        main_path = layout.main_path

        for coord in walkable:
            walkable_neighbors = [
                neighbor
                for neighbor in get_hex_neighbors(coord[0], coord[1], width=layout.width, height=layout.height)
                if neighbor in walkable_set
            ]
            for first_index, first in enumerate(walkable_neighbors):
                for second in walkable_neighbors[first_index + 1 :]:
                    assert second not in get_hex_neighbors(first[0], first[1], width=layout.width, height=layout.height)

        straight_run = 1
        previous_direction = None
        for source, target in zip(main_path, main_path[1:], strict=False):
            direction = get_hex_direction(source, target, width=layout.width, height=layout.height)
            if direction == previous_direction:
                straight_run += 1
            else:
                straight_run = 1
            previous_direction = direction
            assert straight_run <= preset.max_straight_run


def test_generate_hex_rift_places_branches_only_on_bends():
    for i in range(20):
        layout = build_hex_layout(seed=f"branch-seed-{i}")
        main_path = layout.main_path
        branch_nodes = [node.coord for node in layout.nodes if node.path_layer == "branch"]
        if not branch_nodes:
            continue

        main_path_set = set(main_path)
        first_branch = branch_nodes[0]
        junctions = [
            node
            for node in get_hex_neighbors(first_branch[0], first_branch[1], width=12, height=12)
            if node in main_path_set
        ]

        assert len(junctions) == 1
        junction = junctions[0]
        junction_index = main_path.index(junction)
        assert 0 < junction_index < len(main_path) - 1
        in_direction = get_hex_direction(main_path[junction_index - 1], junction, width=layout.width, height=layout.height)
        out_direction = get_hex_direction(junction, main_path[junction_index + 1], width=layout.width, height=layout.height)
        assert in_direction != out_direction


def _hex_distance(start, finish, *, width, height):
    visited = {start}
    queue = [(start, 0)]
    while queue:
        coord, distance = queue.pop(0)
        if coord == finish:
            return distance
        for neighbor in get_hex_neighbors(coord[0], coord[1], width=width, height=height):
            if neighbor is not None and neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, distance + 1))
    raise AssertionError("finish is unreachable on the grid")


def test_layout_scale_only_declares_grid_levels_and_scheme_keys():
    solo = RIFT_LAYOUT_SCALES["solo"]
    group = RIFT_LAYOUT_SCALES["group"]

    assert set(RIFT_LAYOUT_SCALES) == {"solo", "group"}
    assert solo["grid"] == {"width": 12, "height": 12, "border": 1}
    assert group["grid"] == {"width": 15, "height": 15, "border": 1}
    assert solo["difficulties"] == {
        "easy": {"level_count": {"min": 1, "max": 2}},
        "medium": {"level_count": {"min": 3, "max": 5}},
        "hard": {"level_count": {"min": 6, "max": 10}},
    }
    assert group["difficulties"] == solo["difficulties"]
    assert "scheme_keys" in solo
    assert solo["scheme_keys"] == [
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
    ]
    assert group["scheme_keys"] == [
        "double_fork",
        "branch_toward_finish",
        "short_detour",
        "long_winding_path",
        "hidden_shortcut",
        "flower_weave",
        "flower_weave_plus_ring",
        "dev_half_ring_poi",
        "dev_resource_pocket",
    ]
    assert "side_spurs" not in group["scheme_keys"]
    assert "dev_switch_gate" not in group["scheme_keys"]
    assert solo["random_scheme_keys"] == [
        "flower_weave",
        "flower_weave_plus_ring",
        "dev_half_ring_poi",
        "dev_resource_pocket",
    ]
    assert group["random_scheme_keys"] == ["flower_weave"]
    assert set(solo["random_scheme_keys"]) <= set(solo["scheme_keys"])
    assert set(group["random_scheme_keys"]) <= set(group["scheme_keys"])
    assert "active_nodes" not in solo
    assert "forks" not in solo
    assert "active_nodes" not in group
    assert "forks" not in group


def test_geometry_pattern_library_keeps_planned_shapes_out_of_active_schemes():
    expected_min_scales = {
        "spike_comb": "solo",
        "ring_detour": "solo",
        "ring_spikes": "group",
        "switch_gate": "solo",
        "half_ring_poi": "solo",
        "double_poi": "group",
        "figure_eight": "group",
        "braid": "group",
        "web_core": "group",
        "hub_spokes": "group",
        "crescent": "group",
        "lock_shortcut": "group",
        "resource_pocket": "solo",
    }

    assert set(expected_min_scales) <= set(RIFT_GEOMETRY_PATTERNS)
    for pattern_key, min_scale in expected_min_scales.items():
        pattern = RIFT_GEOMETRY_PATTERNS[pattern_key]
        assert pattern["min_scale"] == min_scale
        assert pattern["shape_layers"]
        assert pattern["description"]

    assert RIFT_GEOMETRY_PATTERNS["spike_comb"]["status"] == "implemented"
    assert RIFT_GEOMETRY_PATTERNS["ring_detour"]["status"] == "implemented"
    planned_patterns = set(expected_min_scales) - {"spike_comb", "ring_detour"}
    assert all(RIFT_GEOMETRY_PATTERNS[pattern_key]["status"] == "planned" for pattern_key in planned_patterns)
    active_scheme_keys = set(RIFT_LAYOUT_SCALES["solo"]["scheme_keys"]) | set(RIFT_LAYOUT_SCALES["group"]["scheme_keys"])
    for pattern_key in planned_patterns:
        assert pattern_key not in active_scheme_keys


def test_solo_dev_layout_schemes_preview_planned_geometry_patterns():
    expected_patterns = {
        "dev_switch_gate": "switch_gate",
        "dev_half_ring_poi": "half_ring_poi",
        "dev_resource_pocket": "resource_pocket",
    }

    assert set(expected_patterns) <= set(RIFT_LAYOUT_SCALES["solo"]["scheme_keys"])
    for scheme_key, pattern_key in expected_patterns.items():
        preset = resolve_layout_preset(scale_key="solo", difficulty_key="easy", scheme_key=scheme_key)
        layout = build_hex_layout(seed=f"dev-template-{scheme_key}", scheme_key=scheme_key)

        assert preset.scheme["geometry_pattern"] == pattern_key
        assert RIFT_GEOMETRY_PATTERNS[pattern_key]["status"] == "planned"
        assert layout.scheme_key == scheme_key
        assert layout.builder_debug["geometry_pattern"] == pattern_key


def test_geometry_pattern_availability_is_scale_gated():
    solo_patterns = available_geometry_pattern_keys("solo")
    group_patterns = available_geometry_pattern_keys("group")

    assert {
        "spike_comb",
        "ring_detour",
        "switch_gate",
        "half_ring_poi",
        "resource_pocket",
    } <= set(solo_patterns)
    assert {
        "ring_spikes",
        "double_poi",
        "figure_eight",
        "braid",
        "web_core",
        "hub_spokes",
        "crescent",
        "lock_shortcut",
    }.isdisjoint(solo_patterns)
    assert {
        "ring_spikes",
        "double_poi",
        "figure_eight",
        "braid",
        "web_core",
        "hub_spokes",
        "crescent",
        "lock_shortcut",
    } <= set(group_patterns)
    assert set(solo_patterns) < set(group_patterns)


def test_layout_scheme_owns_ratios_forks_hidden_and_interest_distribution():
    scheme = RIFT_LAYOUT_SCHEMES["side_spurs"]
    path_graph = scheme["path_graph"]
    branches = scheme["branches"]

    assert "active_node_ratio" not in scheme
    assert "path_graph" in scheme
    assert "interest_distribution" not in scheme
    assert "interest_slots" not in scheme
    assert "main_path_nodes" not in path_graph
    assert "main_path_node_ratio" in path_graph
    assert "forks" not in path_graph
    assert "fork_ratio" in path_graph
    assert "length" not in branches
    assert "length_ratio" in branches
    assert path_graph["max_straight_run"] == 2
    assert path_graph["min_distance_from_start_ratio"]["min"] == 0.16
    assert branches["first_steps_away_from_main"]["min"] == 1


def test_flower_weave_template_uses_ratios_not_absolute_counts():
    scheme = RIFT_LAYOUT_SCHEMES["flower_weave"]
    path_graph = scheme["path_graph"]
    branches = scheme["branches"]
    spike_spurs = scheme["spike_spurs"]

    assert scheme["geometry_pattern"] == "spike_comb"
    assert "main_path_nodes" not in path_graph
    assert "main_path_node_ratio" in path_graph
    assert path_graph["main_path_node_ratio"] == {"min": 0.17, "target": 0.17, "max": 0.17}
    assert path_graph["main_path_odd"] is True
    assert "forks" not in path_graph
    assert "fork_ratio" in path_graph
    assert path_graph["min_straight_run"] == 2
    assert path_graph["max_straight_run"] == 3
    assert "min_distance_from_start" not in path_graph
    assert "min_distance_from_start_ratio" in path_graph
    assert "min_distance_from_finish" not in path_graph
    assert "min_distance_from_finish_ratio" in path_graph
    assert "min_distance_between_forks" not in path_graph
    assert "min_distance_between_forks_ratio" in path_graph
    assert "length" not in branches
    assert "length_ratio" in branches
    assert "main_path_slots" not in scheme
    assert "flower_loops" not in scheme
    assert scheme["secondary_path"]["enabled"] is False
    assert spike_spurs["enabled"] is True
    assert "max_count" not in spike_spurs
    assert spike_spurs["node_budget_ratio"] == {"min": 0.0, "target": 0.08, "max": 0.24}
    assert spike_spurs["node_slot"] == "movement"
    assert "terminal_slot" not in spike_spurs
    assert spike_spurs["path_length"] == {"min": 2, "target": 2, "max": 3}
    assert spike_spurs["path_length_three_chance"] == 0.5
    assert spike_spurs["path_layer"] == "spike_spur"


def test_flower_weave_plus_ring_template_keeps_ring_as_separate_pattern():
    scheme = RIFT_LAYOUT_SCHEMES["flower_weave_plus_ring"]
    flower_loops = scheme["flower_loops"]

    assert scheme["geometry_pattern"] == "ring_detour"
    assert "spike_spurs" not in scheme
    assert flower_loops["enabled"] is True
    assert "max_count" not in flower_loops
    assert flower_loops["count_ratio"] == {"min": 0.0, "target": 0.01, "max": 0.015}
    assert flower_loops["node_budget_ratio"] == {"min": 0.04, "target": 0.07, "max": 0.1}
    assert flower_loops["required"] is True
    assert flower_loops["path_layer"] == "flower_loop"


def test_resolve_layout_preset_derives_counts_from_usable_grid():
    preset = resolve_layout_preset(scale_key="solo", difficulty_key="easy", scheme_key="side_spurs")
    group_preset = resolve_layout_preset(scale_key="group", difficulty_key="medium", scheme_key="double_fork")
    hard_preset = resolve_layout_preset(scale_key="solo", difficulty_key="hard", scheme_key="side_spurs")

    assert preset.scale_key == "solo"
    assert preset.difficulty_key == "easy"
    assert preset.scheme_key == "side_spurs"
    assert preset.width == 12
    assert preset.height == 12
    assert preset.border == 1
    assert preset.usable_capacity == 100
    assert preset.level_count.min == 1
    assert preset.level_count.max == 2
    assert preset.main_path_nodes.min >= 14
    assert preset.main_path_nodes.max <= 19
    assert preset.forks.min >= 2
    assert preset.forks.max >= 3
    assert preset.branch_length.max == 1
    assert group_preset.scale_key == "group"
    assert group_preset.difficulty_key == "medium"
    assert group_preset.width == 15
    assert group_preset.height == 15
    assert group_preset.usable_capacity == 169
    assert group_preset.level_count.min == 3
    assert group_preset.level_count.max == 5
    assert group_preset.main_path_nodes.min > preset.main_path_nodes.min
    assert group_preset.forks.min >= preset.forks.min
    assert group_preset.forks.target >= preset.forks.target
    assert hard_preset.scale_key == "solo"
    assert hard_preset.difficulty_key == "hard"
    assert hard_preset.width == 12
    assert hard_preset.level_count.min == 6
    assert hard_preset.level_count.max == 10


def test_flower_weave_counts_scale_from_usable_grid_ratios():
    preset = resolve_layout_preset(scale_key="solo", difficulty_key="easy", scheme_key="flower_weave")
    group_preset = resolve_layout_preset(scale_key="group", difficulty_key="hard", scheme_key="flower_weave")

    assert preset.usable_capacity == 100
    assert preset.main_path_nodes.min == 17
    assert preset.main_path_nodes.target == 17
    assert preset.main_path_nodes.max == 17
    assert preset.main_path_nodes.target % 2 == 1
    assert preset.forks.min == 0
    assert preset.forks.target == 4
    assert preset.forks.max == 8
    assert preset.active_nodes.target > preset.main_path_nodes.target
    assert preset.min_distance_from_start == 2
    assert preset.min_distance_from_finish == 2
    assert preset.min_distance_between_forks == 3
    assert group_preset.usable_capacity == 169
    assert group_preset.main_path_nodes.min == 29
    assert group_preset.main_path_nodes.target == 29
    assert group_preset.main_path_nodes.max == 29
    assert group_preset.main_path_nodes.min > preset.main_path_nodes.min
    assert group_preset.main_path_nodes.target > preset.main_path_nodes.target
    assert group_preset.main_path_nodes.max > preset.main_path_nodes.max
    assert group_preset.main_path_nodes.min % 2 == 1
    assert group_preset.main_path_nodes.target % 2 == 1
    assert group_preset.main_path_nodes.max % 2 == 1
    assert group_preset.forks.target > preset.forks.target
    assert group_preset.active_nodes.target > preset.active_nodes.target
    assert group_preset.level_count.min == 6
    assert group_preset.level_count.max == 10


def test_build_hex_layout_randomizes_allowed_solo_scheme_by_seed():
    scheme_keys = {
        build_hex_layout(seed=f"scheme-random-{index}", scheme_key=None).scheme_key
        for index in range(24)
    }

    assert scheme_keys <= set(RIFT_LAYOUT_SCALES["solo"]["scheme_keys"])
    assert len(scheme_keys) >= 3


def test_build_hex_layout_defaults_to_current_dev_harness_scheme():
    layout = build_hex_layout(seed="current-dev-harness")

    assert layout.scheme_key == "flower_weave"


def test_hex_layout_builds_through_flagged_pipeline_plan():
    preset = resolve_layout_preset(scale_key="solo", difficulty_key="easy", scheme_key="flower_weave")
    plan = build_hex_build_plan(seed="pipeline-contract", preset=preset)
    layout = build_hex_layout(seed="pipeline-contract", scheme_key="flower_weave")

    assert plan.build_flower_pressure is True
    assert plan.build_main_path is True
    assert plan.build_branches is False
    assert plan.build_flower_loops is False
    assert plan.build_spike_spurs is True
    assert plan.build_hidden_shortcuts is False
    assert plan.place_required_slots is True
    assert plan.place_alternating_slots is False
    assert plan.layer_keys == [
        "choose_flower_weave_endpoints",
        "place_flower_pressure",
        "build_main_path",
        "build_spike_spurs",
        "place_required_slots",
    ]
    assert layout.builder_debug["pipeline_layers"] == plan.layer_keys
    assert layout.builder_debug["pipeline_plan"]["build_flower_pressure"] is True
    assert layout.builder_debug["pipeline_plan"]["build_hidden_shortcuts"] is False


def test_hex_layout_generator_has_no_legacy_path_fallback():
    source = inspect.getsource(hex_generator)

    assert "_fallback_main_path" not in source
    assert ":fallback" not in source


def test_build_hex_rift_state_exposes_layout_debug_contract():
    state = build_hex_rift_state(instance_id="test-id", seed="layout-debug")
    fork_count = sum(1 for node in state.nodes if node.graph_role == "fork")
    branch_count = sum(1 for node in state.nodes if node.path_layer == "branch")

    assert state.scale_key == "solo"
    assert state.difficulty_key == "easy"
    assert state.scheme_key in RIFT_LAYOUT_SCALES["solo"]["scheme_keys"]
    assert state.available_scheme_keys == list(active_geometry_pattern_schemes("solo").values())
    assert "side_spurs" not in state.available_scheme_keys
    assert state.pattern_key in state.available_pattern_keys
    assert "legacy_path_graph" not in state.available_pattern_keys
    assert state.layout_debug["scheme_key"] == state.scheme_key
    assert state.layout_debug["usable_cells"] == 100
    assert state.layout_debug["walkable_nodes"] == state.layout_debug["active_nodes"]
    assert state.layout_debug["walkable_percent"] > 0
    assert state.layout_debug["reachable_nodes"] == state.layout_debug["walkable_nodes"]
    assert state.layout_debug["unreachable_walkable_nodes"] == 0
    assert state.layout_debug["extra_nodes"] == state.layout_debug["walkable_nodes"] - state.layout_debug["main_path_nodes"]
    assert state.layout_debug["layer_counts"]
    assert state.layout_debug["slot_counts"]
    assert state.layout_debug["role_counts"]
    assert state.layout_debug["fork_nodes"] == fork_count
    assert state.layout_debug["branch_nodes"] == branch_count
    assert "hidden_shortcut_nodes" in state.layout_debug


def test_build_hex_rift_state_exposes_geometry_pattern_catalog_by_scale():
    solo_state = build_hex_rift_state(instance_id="test-id", seed="pattern-catalog-solo", scale_key="solo")
    group_state = build_hex_rift_state(instance_id="test-id", seed="pattern-catalog-group", scale_key="group")

    solo_catalog = {pattern["key"]: pattern for pattern in solo_state.layout_pattern_catalog}
    group_catalog = {pattern["key"]: pattern for pattern in group_state.layout_pattern_catalog}

    assert set(solo_catalog) == set(solo_state.available_pattern_keys)
    assert set(group_catalog) == set(group_state.available_pattern_keys)
    assert "legacy_path_graph" not in solo_catalog
    assert "legacy_path_graph" not in group_catalog
    assert solo_catalog["spike_comb"]["status"] == "implemented"
    assert solo_catalog["spike_comb"]["available_for_current_scale"] is True
    assert solo_catalog["spike_comb"]["active_scheme_keys"] == ["flower_weave"]
    assert solo_catalog["spike_comb"]["dev_enabled"] is False
    assert solo_catalog["switch_gate"]["available_for_current_scale"] is True
    assert solo_catalog["switch_gate"]["status"] == "planned"
    assert solo_catalog["switch_gate"]["active_scheme_keys"] == ["dev_switch_gate"]
    assert solo_catalog["switch_gate"]["dev_enabled"] is True
    assert solo_catalog["half_ring_poi"]["active_scheme_keys"] == ["dev_half_ring_poi"]
    assert solo_catalog["resource_pocket"]["active_scheme_keys"] == ["dev_resource_pocket"]
    assert "web_core" not in solo_catalog
    assert "web_core" not in group_catalog
    assert "hub_spokes" not in group_catalog
    assert group_catalog["resource_pocket"]["min_scale"] == "solo"


def test_build_hex_rift_state_exposes_active_template_debug_rules():
    state = build_hex_rift_state(
        instance_id="test-id",
        seed="template-debug",
        scale_key="solo",
        scheme_key="flower_weave",
    )

    template_debug = state.layout_template_debug

    assert template_debug["scheme_key"] == "flower_weave"
    assert template_debug["geometry_pattern"] == "spike_comb"
    assert template_debug["status"] == "implemented"
    assert template_debug["pipeline_layers"] == state.layout_debug["pipeline_layers"]
    assert template_debug["pipeline_plan"]["build_spike_spurs"] is True
    assert template_debug["pipeline_plan"]["build_flower_loops"] is False
    assert template_debug["rules"]["main_path"] == {
        "target_nodes": 17,
        "min_nodes": 17,
        "max_nodes": 17,
        "odd": True,
        "straight_run": {"min": 2, "max": 3},
        "avoid_triangles": True,
    }
    assert template_debug["rules"]["spike_spurs"]["enabled"] is True
    assert template_debug["rules"]["spike_spurs"]["path_length"] == {"min": 2, "target": 2, "max": 3}
    assert template_debug["rules"]["spike_spurs"]["target_count"] >= 0
    assert template_debug["rules"]["spike_spurs"]["actual_count"] >= 0
    assert template_debug["rules"]["spike_spurs"]["candidate_count"] >= 0
    assert template_debug["rules"]["spike_spurs"]["rejected_candidates"] >= 0
    assert template_debug["rules"]["flower_loops"]["enabled"] is False
    assert template_debug["shape_layers"] == ["main_path", "spike_spurs"]


def test_hidden_shortcut_scheme_adds_hidden_loop_path():
    layout = build_hex_layout(seed="hidden-shortcut-contract", scheme_key="hidden_shortcut")
    hidden_nodes = [node for node in layout.nodes if node.path_layer == "hidden_shortcut"]
    edge_count = sum(sum(node.edges) for node in layout.nodes) // 2

    assert len(hidden_nodes) >= 2
    assert all(node.visibility == "visible" for node in hidden_nodes)
    assert edge_count >= len(layout.nodes)
    assert any(node.graph_role == "fork" for node in layout.nodes if node.coord in layout.main_path)


def test_flower_weave_scheme_uses_build_only_void_flowers():
    layout = build_hex_layout(seed="flower-weave-contract", scheme_key="flower_weave")
    soft_flower_centers = {tuple(coord) for coord in layout.builder_debug["soft_flower_centers"]}
    structural_anchors = {tuple(coord) for coord in layout.builder_debug["structural_flower_anchors"]}
    pressure_cells = {tuple(coord) for coord in layout.builder_debug["soft_flower_pressure_cells"]}

    assert layout.scheme_key == "flower_weave"
    assert len(soft_flower_centers) == 2
    assert structural_anchors
    assert pressure_cells
    assert all(node.content_slot != "void_flower" for node in layout.nodes)
    assert layout.builder_debug["path_candidate_strategy"] == "weighted_pressure_search"
    assert layout.builder_debug["soft_flower_center_policy"] == "high_cost"


def test_flower_weave_builds_fixed_base_path_without_secondary_squiggle():
    layout = build_hex_layout(seed="flower-secondary-contract", scheme_key="flower_weave")
    debug = layout.builder_debug
    hidden_nodes = [node for node in layout.nodes if node.path_layer == "hidden_shortcut"]

    assert debug["path_candidate_strategy"] == "weighted_pressure_search"
    assert len(layout.main_path) == 17
    assert not hidden_nodes
    assert {node.path_layer for node in layout.nodes} <= {"main", "spike_spur"}
    internal_slots = [node.content_slot for coord in layout.main_path[1:-1] for node in layout.nodes if node.coord == coord]
    spike_slots = [node.content_slot for node in layout.nodes if node.path_layer == "spike_spur"]
    assert internal_slots == ["movement"] * len(internal_slots)
    assert set(spike_slots) == {"movement"}
    assert all(node.content_slot != "event_room" for node in layout.nodes)
    _assert_main_path_has_straight_run_rhythm(layout, min_run=2, max_run=3)
    _assert_main_path_has_no_sixty_degree_turns(layout)


def test_flower_weave_plus_ring_builds_visible_flower_loop_layer():
    layouts = [
        build_hex_layout(seed=f"flower-loop-contract-{index}", scheme_key="flower_weave_plus_ring")
        for index in range(32)
    ]
    layout = next(layout for layout in layouts if layout.builder_debug["flower_loop_count"] > 0)
    loop_nodes = [node for node in layout.nodes if node.path_layer == "flower_loop"]
    fork_nodes = [node for node in layout.nodes if node.graph_role == "fork"]

    assert loop_nodes
    assert all(node.visibility == "visible" for node in loop_nodes)
    assert all(node.coord not in layout.main_path for node in loop_nodes)
    assert len(fork_nodes) >= 2
    assert layout.builder_debug["flower_loop_path_layer"] == "flower_loop"
    assert layout.builder_debug["flower_loop_candidate_count"] >= layout.builder_debug["flower_loop_count"]
    assert layout.builder_debug["flower_loop_protected_voids"]
    _assert_no_triangle_clusters(layout)


def test_flower_weave_plus_ring_places_loop_on_every_sampled_dev_map():
    layouts = [
        build_hex_layout(seed=f"flower-loop-stability-{index}", scheme_key="flower_weave_plus_ring")
        for index in range(16)
    ]

    assert all(layout.builder_debug["flower_loop_count"] >= 1 for layout in layouts)


def test_flower_weave_builds_spike_spur_layer_from_bends():
    layouts = [
        build_hex_layout(seed=f"spike-spur-contract-{index}", scheme_key="flower_weave")
        for index in range(16)
    ]
    layout = next(layout for layout in layouts if layout.builder_debug["spike_spur_count"] > 0)
    spike_nodes = [node for node in layout.nodes if node.path_layer == "spike_spur"]

    assert spike_nodes
    assert all(node.visibility == "visible" for node in spike_nodes)
    assert all(node.coord not in layout.main_path for node in spike_nodes)
    assert {node.content_slot for node in spike_nodes} == {"movement"}
    assert layout.builder_debug["spike_spur_path_length_three_chance"] == 0.5
    _assert_no_triangle_clusters(layout)


def test_flower_weave_spike_spurs_can_use_every_possible_bend():
    source = inspect.getsource(hex_generator._add_spike_spurs)

    assert "min_distance_from_start" not in source
    assert "min_distance_from_finish" not in source
    assert "min_distance_between_forks" not in source


def test_flower_weave_soft_flower_count_scales_with_map_size():
    solo_layout = build_hex_layout(seed="flower-count-solo", scale_key="solo", scheme_key="flower_weave")
    group_layout = build_hex_layout(seed="flower-count-group", scale_key="group", scheme_key="flower_weave")
    flower_counts = RIFT_LAYOUT_SCHEMES["flower_weave"]["void_flowers"]["soft_flower_count_by_scale"]

    assert solo_layout.builder_debug["soft_flower_count"] == 2
    assert group_layout.builder_debug["soft_flower_count"] == 3
    assert flower_counts["solo"] == {"min": 2, "target": 2, "max": 2}
    assert flower_counts["group"] == {"min": 3, "target": 3, "max": 3}


def test_all_solo_layout_schemes_build_first_layer_contract():
    for scheme_key in RIFT_LAYOUT_SCALES["solo"]["scheme_keys"]:
        layout = build_hex_layout(seed=f"scheme-contract-{scheme_key}", scheme_key=scheme_key)
        preset = resolve_layout_preset(scale_key="solo", scheme_key=scheme_key)
        fork_nodes = [node for node in layout.nodes if node.graph_role == "fork"]

        assert layout.scheme_key == scheme_key
        assert len(layout.nodes) <= preset.active_nodes.max
        assert preset.main_path_nodes.min <= len(layout.main_path) <= preset.main_path_nodes.max
        assert preset.forks.min <= len(fork_nodes) <= preset.forks.max
        assert layout.main_path[0] == layout.start
        assert layout.main_path[-1] == layout.finish
        assert any(node.content_slot == "rift_heart_room" for node in layout.nodes)


def test_build_hex_layout_first_layer_contains_only_path_forks_and_branches():
    layout = build_hex_layout(seed="layout-contract", scheme_key="side_spurs")
    nodes_by_coord = {node.coord: node for node in layout.nodes}
    fork_nodes = [node for node in layout.nodes if node.graph_role == "fork"]
    path_slots = {"movement", "entrance_room", "rift_heart_room", "branch_end"}

    assert layout.width == 12
    assert layout.height == 12
    assert fork_nodes
    assert all(node.content_slot == "movement" for node in fork_nodes)
    assert {node.content_slot for node in layout.nodes} <= path_slots
    assert any(node.content_slot == "rift_heart_room" for node in layout.nodes)

    for node in layout.nodes:
        linked_neighbors = [
            neighbor
            for edge, neighbor in enumerate(get_hex_neighbors(node.coord[0], node.coord[1], layout.width, layout.height))
            if node.edges[edge] == 1
        ]
        assert all(neighbor in nodes_by_coord for neighbor in linked_neighbors)


def test_build_hex_layout_main_path_is_longer_than_shortest_route():
    for i in range(12):
        layout = build_hex_layout(seed=f"main-path-length-{i}", scheme_key="side_spurs")
        shortest = _hex_distance(layout.start, layout.finish, width=layout.width, height=layout.height)

        assert len(layout.main_path) >= round(shortest * 1.35)
        assert len(layout.main_path) <= round(shortest * 2.0)


def test_flower_weave_allows_longer_pressure_routes_inside_template_bounds():
    for i in range(8):
        layout = build_hex_layout(seed=f"flower-route-length-{i}", scheme_key="flower_weave")
        preset = resolve_layout_preset(scale_key=layout.scale_key, scheme_key=layout.scheme_key)

        assert preset.main_path_nodes.min <= len(layout.main_path) <= preset.main_path_nodes.max
        assert layout.builder_debug["path_candidate_strategy"] == "weighted_pressure_search"


def test_build_hex_layout_places_forks_with_spacing_rules():
    for i in range(12):
        layout = build_hex_layout(seed=f"fork-spacing-{i}", scheme_key="side_spurs")
        preset = resolve_layout_preset(scale_key=layout.scale_key, scheme_key=layout.scheme_key)
        main_index = {coord: index for index, coord in enumerate(layout.main_path)}
        fork_nodes = [node for node in layout.nodes if node.graph_role == "fork"]

        assert preset.forks.min <= len(fork_nodes) <= preset.forks.max
        for node in fork_nodes:
            assert node.coord in main_index
            index = main_index[node.coord]
            assert index >= preset.min_distance_from_start
            assert len(layout.main_path) - index - 1 >= preset.min_distance_from_finish
            assert node.content_slot == "movement"

        ordered_indexes = sorted(main_index[node.coord] for node in fork_nodes)
        for left, right in zip(ordered_indexes, ordered_indexes[1:], strict=False):
            assert right - left >= preset.min_distance_between_forks


def test_build_hex_layout_avoids_one_hex_gaps_between_unlinked_paths():
    for i in range(24):
        layout = build_hex_layout(seed=f"one-hex-gap-{i}")
        nodes_by_coord = {node.coord: node for node in layout.nodes if node.path_layer != "hidden_shortcut"}
        graph_links = {
            node.coord: {
                neighbor
                for edge, neighbor in enumerate(get_hex_neighbors(node.coord[0], node.coord[1], width=layout.width, height=layout.height))
                if node.edges[edge] == 1 and neighbor in nodes_by_coord
            }
            for node in layout.nodes
            if node.path_layer != "hidden_shortcut"
        }

        for y in range(layout.height):
            for x in range(layout.width):
                coord = (x, y)
                if coord in nodes_by_coord:
                    continue
                touching = [
                    neighbor
                    for neighbor in get_hex_neighbors(x, y, width=layout.width, height=layout.height)
                    if neighbor in nodes_by_coord
                ]
                for first_index, first in enumerate(touching):
                    first_node = nodes_by_coord[first]
                    first_links = {
                        neighbor
                        for edge, neighbor in enumerate(get_hex_neighbors(first[0], first[1], width=layout.width, height=layout.height))
                        if first_node.edges[edge] == 1
                    }
                    for second in touching[first_index + 1 :]:
                        if _layout_graph_distance(first, second, graph_links) <= 2:
                            continue
                        assert second in first_links


def test_build_hex_layout_rejects_triangle_clusters_in_full_graph():
    for scheme_key in RIFT_LAYOUT_SCALES["solo"]["scheme_keys"]:
        for index in range(16):
            layout = build_hex_layout(seed=f"triangle-cluster-{scheme_key}-{index}", scheme_key=scheme_key)
            _assert_no_triangle_clusters(layout)


def _assert_no_triangle_clusters(layout):
    walkable_set = {node.coord for node in layout.nodes}
    for coord in walkable_set:
        active_neighbors = [
            neighbor
            for neighbor in get_hex_neighbors(coord[0], coord[1], width=layout.width, height=layout.height)
            if neighbor in walkable_set
        ]
        for first_index, first in enumerate(active_neighbors):
            for second in active_neighbors[first_index + 1 :]:
                assert second not in get_hex_neighbors(first[0], first[1], width=layout.width, height=layout.height)


def _assert_main_path_has_no_sixty_degree_turns(layout):
    for index, coord in enumerate(layout.main_path[1:-1], start=1):
        previous_direction = get_hex_direction(coord, layout.main_path[index - 1], width=layout.width, height=layout.height)
        next_direction = get_hex_direction(coord, layout.main_path[index + 1], width=layout.width, height=layout.height)
        assert previous_direction is not None
        assert next_direction is not None
        delta = abs(previous_direction - next_direction)
        turn = min(delta, 6 - delta)
        assert turn in {2, 3}


def _assert_main_path_has_straight_run_rhythm(layout, *, min_run: int, max_run: int):
    runs = []
    run = 1
    previous_direction = get_hex_direction(layout.main_path[0], layout.main_path[1], width=layout.width, height=layout.height)
    for source, target in zip(layout.main_path[1:-1], layout.main_path[2:], strict=False):
        direction = get_hex_direction(source, target, width=layout.width, height=layout.height)
        if direction == previous_direction:
            run += 1
        else:
            runs.append(run)
            run = 1
        previous_direction = direction
    runs.append(run)
    assert runs
    internal_runs = runs[1:-1]
    assert all(min_run <= run <= max_run for run in internal_runs)
    assert all(run <= max_run for run in runs)


def _layout_graph_distance(start, finish, graph_links):
    visited = {start}
    queue = [(start, 0)]
    while queue:
        coord, distance = queue.pop(0)
        if coord == finish:
            return distance
        for neighbor in graph_links.get(coord, set()):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, distance + 1))
    return 999


def test_build_hex_rift_state_uses_exact_movement_tile_masks():
    seed = "movement-mask-contract"
    tile_set = load_hex_tile_set("void_temple")
    movement_masks = {
        tuple(tile["edges"])
        for tile in tile_set["tiles"]
        if tile.get("kind") == "movement"
        or str(tile.get("structure", {}).get("variant_group", "")).startswith("hidden_dead_end")
    }
    layout = build_hex_layout(seed=seed)
    layout_by_coord = {node.coord: node for node in layout.nodes}
    state = build_hex_rift_state(instance_id="test-id", seed=seed)

    for node in state.nodes:
        if node.content_slot == "movement":
            layout_node = layout_by_coord[(node.x, node.y)]
            assert node.edges == layout_node.edges
            assert tuple(node.edges) in movement_masks


def test_build_hex_rift_state_uses_layout_edges_not_visual_tile_edges():
    tile_set = load_hex_tile_set("void_temple")
    tiles_by_id = {tile["id"]: tile for tile in tile_set["tiles"]}
    seed = "seed-passport"
    layout = build_hex_layout(seed=seed)
    layout_by_coord = {node.coord: node for node in layout.nodes}
    state = build_hex_rift_state(instance_id="test-id", seed=seed)

    assert state.theme == "void_temple"
    for node in state.nodes:
        tile = tiles_by_id[node.tile_index]
        assert node.asset_path == f"tiles/{tile['file']}"
        if (node.x, node.y) in layout_by_coord:
            assert node.edges == layout_by_coord[(node.x, node.y)].edges
            assert node.is_walkable
        else:
            assert node.edges == tile["edges"]
            assert node.is_walkable == bool(tile["walkable"])


def test_build_hex_rift_state_uses_heart_room_for_single_floor_finish():
    tile_set = load_hex_tile_set("void_temple")
    level_transition_ids = set(tile_set["catalog"]["level_transitions"]["all"])
    rift_heart_ids = {
        tile["id"]
        for tile in tile_set["tiles"]
        if {"rift_heart", "pre_destroyed"} <= set((tile.get("placement") or {}).get("event_tags", []))
    }
    empty_room_ids = set(tile_set["catalog"]["empty_rooms"]["all"])
    state = build_hex_rift_state(instance_id="test-id", seed="initial-portal-room")
    nodes_by_coord = {(node.x, node.y): node for node in state.nodes}

    start_node = nodes_by_coord[(state.start_x, state.start_y)]
    finish_node = nodes_by_coord[(state.finish_x, state.finish_y)]

    assert start_node.content_slot == "entrance_room"
    assert start_node.content_subtype == "initial_portal_floor"
    assert start_node.overlay_key == "rift_portal"
    assert start_node.tile_index in empty_room_ids
    assert start_node.tile_index not in level_transition_ids

    assert finish_node.content_slot == "rift_heart_room"
    assert finish_node.content_subtype == "rift_heart_alive"
    assert finish_node.overlay_key == "rift_crystal"
    assert finish_node.tile_index in rift_heart_ids
    assert finish_node.tile_index not in level_transition_ids


def test_hex_map_scene_renders_crystal_only_from_overlay_contract():
    source = Path("src/frontend/static/js/game/scenes/hex_map_scene.js").read_text(encoding="utf-8")

    assert 'node.overlay_key === "rift_crystal"' in source
    assert "node.x === this.riftState.finish_x && node.y === this.riftState.finish_y" not in source


def test_hex_map_scene_keeps_dev_harness_hidden_shortcuts_visible():
    source = Path("src/frontend/static/js/game/scenes/hex_map_scene.js").read_text(encoding="utf-8")

    assert 'visitedCoords.has(key) || revealedCoords.has(key)' in source
    assert 'node.visibility !== "hidden" && isRevealed && isAdjacent && node.is_walkable' not in source


def test_hex_map_scene_shows_full_labyrinth_as_gray_fog_plan():
    source = Path("src/frontend/static/js/game/scenes/hex_map_scene.js").read_text(encoding="utf-8")

    assert "this.initialZoom = 1.42;" in source
    assert "this.minZoom = 0.16;" in source
    assert "this.showAllMap = parent.getAttribute(\"data-show-all-map\") === \"true\";" in source
    assert "const isDiscovered = this.showAllMap || visitedCoords.has(key) || revealedCoords.has(key);" in source
    assert "const isVisible = this.showAllMap || isDiscovered || node.is_walkable || node.content_slot === 'void_decor';" in source
    assert "const displayTextureKey = node.is_walkable && !isDiscovered ? this.getFogPlanTextureKey() : textureKey;" in source
    assert "sprite.setTexture(displayTextureKey);" in source
    assert "sprite.setAlpha(0.36);" in source
    assert "sprite.setTint(0x777a88);" in source
    assert "const isClickable = !this.isLocked && isRevealed && isAdjacent && node.is_walkable;" in source
    assert "this.fitMapToViewport();" in source


def test_hex_map_scene_animates_void_decor_as_slow_position_drift():
    source = Path("src/frontend/static/js/game/scenes/hex_map_scene.js").read_text(encoding="utf-8")
    drift_start = source.index("\n    updateVoidDecorDrift(sprite, node, pixels, isVisible)")
    drift_end = source.index("\n    updateTileInteractivity", drift_start)
    drift_source = source[drift_start:drift_end]

    assert "updateVoidDecorDrift(sprite, node, pixels, isVisible);" in source
    assert "node.content_slot !== 'void_decor'" in drift_source
    assert "const xAmplitude = 8 + ((node.x + node.y) % 8);" in drift_source
    assert "const yAmplitude = 8 + ((node.x * 2 + node.y) % 8);" in drift_source
    assert "duration = 6800" in drift_source
    assert "Sine.easeInOut" in drift_source
    assert "sprite.setData('voidDecorDriftKey'" in drift_source
    assert "rotation" not in drift_source
    assert "setScale" not in drift_source


def test_build_hex_rift_state_keeps_void_decor_out_of_contour_blocker_pass():
    state = build_hex_rift_state(instance_id="test-id", seed="void-decor-layer")
    tile_set = load_hex_tile_set("void_temple")
    removed_void_decor_ids = set(range(70, 75))

    contour_nodes = [
        node
        for node in state.nodes
        if not node.is_walkable and node.content_slot == "contour"
    ]
    decor_nodes = [
        node
        for node in state.nodes
        if not node.is_walkable and node.content_slot == "void_decor"
    ]

    assert contour_nodes
    assert all(node.tile_index < 70 or node.tile_index > 99 for node in contour_nodes)
    assert all(70 <= node.tile_index <= 99 for node in decor_nodes)
    assert removed_void_decor_ids.isdisjoint({int(tile["id"]) for tile in tile_set["tiles"]})
    assert removed_void_decor_ids.isdisjoint({node.tile_index for node in decor_nodes})


def test_hex_map_scene_skips_void_before_creating_tile_sprites():
    source = Path("src/frontend/static/js/game/scenes/hex_map_scene.js").read_text(encoding="utf-8")
    draw_source = source[source.index("\n    drawMap("):source.index("\n    updateVoidDecorDrift(")]
    guard_start = draw_source.index("if (node.content_slot === 'void')")
    guard_end = draw_source.index("return;", guard_start)
    assert "this.tiles[key]?.setVisible(false);" in draw_source[guard_start:guard_end]
    assert guard_end < draw_source.index("this.getHexPixels(")


def test_build_hex_rift_state_places_only_a_few_void_decor_near_labyrinth():
    state = build_hex_rift_state(instance_id="test-id", seed="terminal-void-decor")
    nodes_by_coord = {(node.x, node.y): node for node in state.nodes}
    terminal_nodes = [
        node
        for node in state.nodes
        if node.is_walkable and node.graph_role in {"finish", "dead_end"}
    ]

    assert terminal_nodes
    assert all(
        nodes_by_coord[coord].content_slot != "void_decor"
        for node in terminal_nodes
        for coord in get_hex_neighbors(node.x, node.y, state.width, state.height)
        if coord is not None
    )
    decor_coords = {coord for coord, node in nodes_by_coord.items() if node.content_slot == "void_decor"}
    assert 2 <= len(decor_coords) <= 3
    frontier = {coord for coord, node in nodes_by_coord.items() if node.is_walkable}
    distances = {coord: 0 for coord in frontier}
    for distance in range(1, 4):
        frontier = {
            neighbor
            for coord in frontier
            for neighbor in get_hex_neighbors(*coord, state.width, state.height)
            if neighbor is not None and neighbor not in distances
        }
        distances.update({coord: distance for coord in frontier})
    assert all(distances.get(coord) in {2, 3} for coord in decor_coords)


def test_void_decor_can_be_disabled_even_with_terminal_nodes():
    layout = build_hex_layout(seed="disabled-void-decor")
    assert hex_generator._select_void_decor_coords(
        rng=hex_generator.random.Random(0),
        layout=layout,
        walkable_set={node.coord for node in layout.nodes},
        fill_ratio=0,
    ) == set()


def test_build_hex_rift_state_keeps_outer_frame_blocked():
    state = build_hex_rift_state(instance_id="test-id", seed="outer-frame")

    outer_frame_nodes = [
        node
        for node in state.nodes
        if node.x in (0, state.width - 1) or node.y in (0, state.height - 1)
    ]

    assert outer_frame_nodes
    assert all(not node.is_walkable for node in outer_frame_nodes)


def test_hex_generator_uses_backend_tile_set_resource():
    source = inspect.getsource(hex_generator.build_hex_rift_state)
    assert '"frontend"' not in source

    resource_path = (
        Path("src/backend/features/rift/resources/json/tile_sets")
        / "void_temple"
        / "tileset_data.json"
    )
    assert resource_path.is_file()

def test_build_hex_rift_state():
    state = build_hex_rift_state(instance_id="test-id", seed="test-seed")

    assert state.instance_id == "test-id"
    assert state.width == 12
    assert state.height == 12
    assert len(state.nodes) == 144

    # Start and finish coords must match
    assert (state.start_x, state.start_y) == (state.current_x, state.current_y)

    # Visited should initially contain start node
    assert len(state.visited) == 1
    assert state.visited[0] == (state.start_x, state.start_y)

    # Revealed should contain start node + its neighbors
    start_neighbors = [
        neighbor
        for neighbor in get_hex_neighbors(state.start_x, state.start_y, width=state.width, height=state.height)
        if neighbor is not None
    ]
    expected_revealed = {(state.start_x, state.start_y)} | set(start_neighbors)
    assert set(state.revealed) == expected_revealed
