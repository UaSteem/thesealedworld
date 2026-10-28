"""Whitelist Exploration data; map artwork never grants a movement command."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

from pydantic import ValidationError

from src.frontend.game_features.scenario.view_models.client import scenario_plain_text
from src.shared.schemas.exploration import EncounterDTO, ExplorationLocalMapDTO, WorldNavigationDTO


def _public(source: dict, keys: str) -> dict:
    result = {}
    for key in keys.split():
        if key not in source:
            continue
        value = source[key]
        if isinstance(value, float) and not math.isfinite(value):
            continue
        if value is None or isinstance(value, (str, int, float, bool)):
            result[key] = scenario_plain_text(value) if isinstance(value, str) else value
    return result


def _enemy(enemy) -> dict:
    raw = enemy.model_dump()
    result = _public(raw, "name level member_tier threat_rating hp_percent image description role variant_key")
    if not result.get("image") and isinstance(enemy.visual.get("image_url"), str):
        result["image"] = enemy.visual["image_url"]
    intel = raw.get("intel")
    if isinstance(intel, dict):
        safe_intel = _public(intel, "danger_band")
        vitals = intel.get("vitals")
        if isinstance(vitals, dict):
            safe_intel["vitals"] = {
                key: _public(value, "label percent")
                for key in ("hp", "energy", "concentration")
                if isinstance((value := vitals.get(key)), dict)
            }
        result["intel"] = safe_intel
    return result


def _typed(value: Any, model: type):
    if isinstance(value, model):
        return value
    if isinstance(value, dict):
        try:
            return model.model_validate(value)
        except ValidationError:
            pass
    return None


def _action(button, char_id: int, *, encounter: bool = False) -> dict:
    parts = button.action.split(":")
    kind = parts[0]
    params = {"char_id": char_id}
    endpoint = None
    duration = 0.0
    if not encounter and kind == "move" and len(parts) in (2, 3) and parts[1]:
        params["target_id"] = parts[1]
        endpoint = "/game/exploration/move"
        if len(parts) == 3:
            try:
                duration = float(parts[2])
                if not math.isfinite(duration) or duration < 0:
                    endpoint = None
                    duration = 0.0
            except ValueError:
                endpoint = None
    elif not encounter and kind == "service" and len(parts) == 2 and parts[1]:
        params["service_id"] = parts[1]
        endpoint = "/game/exploration/use-service"
    elif kind == "interact" and len(parts) in (2, 3):
        allowed = {"attack", "bypass", "continue"} if encounter else {"search", "battles", "look_around"}
        if parts[1] in allowed:
            params["action"] = parts[1]
            if len(parts) == 3 and parts[2]:
                params["target_id"] = parts[2]
            endpoint = "/game/exploration/interact"
    signature = json.dumps(
        [endpoint, params, button.action if endpoint is None else None], sort_keys=True, ensure_ascii=True
    )
    return {
        "id": "exploration-" + hashlib.sha256(signature.encode()).hexdigest()[:20],
        "kind": kind,
        "label": scenario_plain_text(button.label),
        "enabled": bool(button.is_active and endpoint),
        "endpoint": endpoint,
        "params": params if endpoint else {},
        "move_duration": duration,
        "tooltip": scenario_plain_text(button.tooltip or ("" if endpoint else "Сейчас недоступно")),
    }


def _city_map(raw: dict) -> dict | None:
    if raw.get("mode") != "viewport_7x7" or not isinstance(raw.get("rows"), list):
        return None
    result = _public(raw, "mode region_id source_region_id loc_id size tile_size")
    for key in ("current", "viewport"):
        value = raw.get(key)
        result[key] = (
            _public(value, "visual_x visual_y local_x local_y max_visual_x max_visual_y")
            if isinstance(value, dict)
            else {}
        )
    result["rows"] = []
    for row in raw["rows"][:7]:
        if not isinstance(row, list):
            continue
        cells = []
        for cell in row[:7]:
            if not isinstance(cell, dict):
                continue
            public = _public(cell, "tile_url visual_x visual_y world_x world_y local_x local_y is_current")
            x, y = cell.get("world_x"), cell.get("world_y")
            if type(x) is int and type(y) is int:
                public["loc_id"] = f"{x}_{y}"  # Inspection address only; no command is inferred.
            public["service_markers"] = [
                _public(marker, "service_id service_type label icon_url corner")
                for marker in cell.get("service_markers", [])
                if isinstance(marker, dict)
            ]
            cells.append(public)
        result["rows"].append(cells)
    return result


def _local_map(value: Any) -> dict | None:
    model = _typed(value, ExplorationLocalMapDTO)
    if model is None:
        return None
    result = _public(model.model_dump(), "char_id current_loc_id radius size")
    result["rows"] = []
    for row in model.rows:
        cells = []
        for cell in row:
            public = _public(
                cell.model_dump(),
                "loc_id x y dx dy is_current is_known title description zone_id terrain node_type is_safe_zone system_connect threat threat_tier dominant_anchor service_count players_count battles_count corpse_count background_available",
            )
            public["tags"] = [scenario_plain_text(tag) for tag in cell.tags]
            public["service_labels"] = [scenario_plain_text(label) for label in cell.service_labels]
            for field in ("edges", "render_edges"):
                public[field] = {
                    key: _public(edge.model_dump(), "direction state target_loc_id label travel_time tooltip")
                    for key, edge in getattr(cell, field).items()
                }
            cells.append(public)
        result["rows"].append(cells)
    return result


def build_exploration_client_payload(
    exploration: Any, encounter: Any = None, local_map: Any = None, char_id: int = 0
) -> dict | None:
    navigation = _typed(exploration, WorldNavigationDTO)
    if navigation is None:
        return None
    active = _typed(encounter, EncounterDTO)
    result = _public(
        navigation.model_dump(), "loc_id title description background_url terrain node_type threat_tier is_safe_zone"
    )
    result["char_id"] = char_id
    result["hud"] = (
        _public(
            navigation.hud.model_dump(),
            "type threat threat_tier players_count battles_count is_safe_zone system_connect risk_state pending_free_xp pending_skill_count carried_resource_count carried_item_count dominant_anchor message style",
        )
        if navigation.hud
        else None
    )
    result["city_map"] = _city_map(navigation.city_map)
    result["local_map"] = _local_map(local_map)
    result["objects"] = [scenario_plain_text(item) for item in navigation.visual_objects]
    result["actions"] = []
    result["encounter"] = None
    if active:
        from src.shared.schemas.exploration import GridButtonDTO

        data = _public(active.model_dump(), "id type status title description image info_level")
        data["enemies"] = [_enemy(enemy) for enemy in active.enemies]
        data["options"] = []
        chance = active.metadata.get("bypass_chance_percent")
        if type(chance) in (int, float) and math.isfinite(chance):
            data["bypass_chance_percent"] = chance
        for option in active.options:
            action = _action(
                GridButtonDTO(id=option.id, label=option.label, action="interact:" + option.id, is_active=True),
                char_id,
                encounter=True,
            )
            data["options"].append(
                {
                    "id": option.id,
                    "label": scenario_plain_text(option.label),
                    "style": option.style,
                    "action_id": action["id"],
                    "inspection_only": option.id == "inspect",
                }
            )
            result["actions"].append(action)
        result["encounter"] = data
    else:
        buttons = []
        if navigation.navigation:
            for field in ("movement", "exploration", "services", "auto_routes"):
                buttons.extend(getattr(navigation.navigation, field).values())
        for field in ("n", "s", "w", "e", "nw", "ne", "sw", "se", "center"):
            button = getattr(navigation.grid, field)
            if button:
                buttons.append(button)
        buttons.extend(navigation.grid.services)
        seen = set()
        for button in buttons:
            action = _action(button, char_id)
            if action["id"] not in seen:
                result["actions"].append(action)
                seen.add(action["id"])
    return result
