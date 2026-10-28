"""Presentation-only interior projection; no fabricated city operations or queues."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

from pydantic import ValidationError

from src.frontend.game_features.scenario.view_models.client import scenario_plain_text
from src.shared.schemas.arena import ArenaUIPayloadDTO
from src.shared.schemas.city_services import CityServiceUIPayloadDTO

_ARENA_ACTIONS = {
    "menu_main",
    "menu_mode",
    "join_queue",
    "start_shadow",
    "check_match",
    "accept_shadow",
    "continue_search",
    "check_combat_ready",
    "cancel_queue",
    "leave",
}
_ART = {"market": "trading-quarter", "town_hall": "administrative-quarter", "workshop.blacksmith": "crafting-quarter"}
_UNAVAILABLE = "Сейчас находится на ремонте."


def _typed(value, model):
    if isinstance(value, model):
        return value
    if isinstance(value, dict):
        try:
            return model.model_validate(value)
        except ValidationError:
            pass
    return None


def _text(value):
    return scenario_plain_text(value) if isinstance(value, str) else value


def _scalar(value):
    return isinstance(value, (str, int, float, bool)) and not (isinstance(value, float) and not math.isfinite(value))


def _action(label, action, params, endpoint, *, enabled=True, mode=None, section_id=None, hidden_poll=False):
    signature = json.dumps([endpoint, params], sort_keys=True, ensure_ascii=True)
    return {
        "id": "place-" + hashlib.sha256(signature.encode()).hexdigest()[:20],
        "label": _text(label),
        "enabled": enabled,
        "endpoint": endpoint,
        "params": params,
        "action": action,
        "mode": mode,
        "section_id": section_id,
        "hidden_poll": hidden_poll,
    }


def _base(kind, place, model):
    return {
        "kind": kind,
        "place": place,
        "title": _text(model.title),
        "description": _text(model.description),
        "screen": str(model.screen),
        "notice": None,
        "background_url": None,
        "details": [],
        "sections": [],
        "npc": None,
        "actions": [],
        "unavailable": None,
        "poll": None,
    }


def _arena(model, char_id):
    result = _base("arena", "arena", model)
    result["background_url"] = "/static/images/game-client/places/arena-hall.webp"
    unsupported_mode = model.mode not in (None, "one_vs_one")
    if unsupported_mode:
        result["unavailable"] = _UNAVAILABLE
    for button in model.buttons:
        action, mode = str(button.action), button.mode
        enabled = action in _ARENA_ACTIONS and button.variant != "disabled"
        if (
            (action == "menu_mode" and mode != "one_vs_one")
            or mode not in (None, "one_vs_one")
            or (unsupported_mode and action not in {"leave", "menu_main"})
        ):
            enabled = False
        params = {"char_id": char_id, "action": action}
        if mode:
            params["mode"] = mode
        value = button.value if isinstance(button.value, dict) else {}
        for key, expected in (("arena_session_id", str), ("wait_limit_sec", int), ("confirm", bool)):
            if type(value.get(key)) is expected:
                params[key] = value[key]
        result["actions"].append(_action(button.text, action, params, "/game/arena/action", enabled=enabled, mode=mode))
    fields = [("gs", "Сила"), ("opponent_name", "Противник"), ("wait_time_sec", "Ожидание, сек")]
    for key, label in fields:
        value = getattr(model, key)
        if value is not None and _scalar(value):
            result["details"].append({"label": label, "value": _text(value)})
    if not unsupported_mode:
        for key, label in [
            ("queue_waiting_count", "В очереди"),
            ("wait_limit_sec", "Лимит поиска, сек"),
            ("max_wait_limit_sec", "Максимальный поиск, сек"),
            ("rating", "Рейтинг"),
            ("league_name", "Лига"),
            ("wins", "Победы"),
            ("losses", "Поражения"),
        ]:
            value = model.metadata.get(key)
            if value is not None and _scalar(value):
                result["details"].append({"label": label, "value": _text(value)})
        poll_action = None
        if str(model.screen) == "searching":
            poll_action = "check_match"
        elif str(model.screen) == "combat_pending" and model.arena_session_id and model.metadata.get("polling"):
            poll_action = "check_combat_ready"
        if poll_action:
            params = {"char_id": char_id, "action": poll_action}
            if model.mode:
                params["mode"] = model.mode
            if poll_action == "check_combat_ready":
                params["arena_session_id"] = model.arena_session_id
            action = _action("Проверить", poll_action, params, "/game/arena/action", mode=model.mode, hidden_poll=True)
            result["actions"].append(action)
            result["poll"] = {"id": action["id"], "interval_ms": max(250, model.poll_after_ms)}
    return result


def _city(model, char_id):
    place = {"market": "trading", "town_hall": "administrative", "workshop.blacksmith": "crafting"}.get(
        model.service_type, model.service_type if model.service_type in {"tavern", "portal"} else "unknown"
    )
    result = _base("service", place, model)
    result["notice"] = _text(model.notice)
    art = _ART.get(model.service_type)
    result["background_url"] = f"/static/images/game-client/places/{art}.webp" if art else model.background_url
    result["sections"] = [
        {"id": section.id, "title": _text(section.title), "description": _text(section.description)}
        for section in model.sections
    ]

    def command(label, action, section_id=None, enabled=True):
        params = {"char_id": char_id, "action": action, "service_id": model.service_id, "screen": str(model.screen)}
        section_id = section_id or model.section_id
        if section_id:
            params["section_id"] = section_id
        if model.location_id:
            params["location_id"] = model.location_id
        item = _action(label, action, params, "/game/city-services/action", enabled=enabled, section_id=section_id)
        existing = next((candidate for candidate in result["actions"] if candidate["id"] == item["id"]), None)
        if existing is not None:
            return existing
        result["actions"].append(item)
        return item

    for button in model.buttons:
        command(button.label, str(button.action), button.section_id, not button.is_disabled)
    npc = model.metadata.get("npc")
    if isinstance(npc, dict):
        item = command(
            "Поговорить", "start_dialogue", npc.get("section_id") if isinstance(npc.get("section_id"), str) else None
        )
        result["npc"] = {
            key: _text(npc.get(key)) if isinstance(npc.get(key), str) else None
            for key in ("name", "role", "portrait_url")
        }
        result["npc"]["action_id"] = item["id"]
    room = model.metadata.get("room")
    if isinstance(room, dict):
        for key, label in [("is_owned", "Комната закреплена"), ("can_rest", "Отдых доступен")]:
            if type(room.get(key)) is bool:
                result["details"].append({"label": label, "value": room[key]})
    if model.service_type in _ART:
        result["unavailable"] = _UNAVAILABLE
    return result


def build_places_client_payload(*, arena: Any = None, city_service: Any = None, char_id: int = 0) -> dict | None:
    model = _typed(arena, ArenaUIPayloadDTO)
    if model is not None:
        result = _arena(model, char_id)
        result["char_id"] = char_id
        return result
    model = _typed(city_service, CityServiceUIPayloadDTO)
    if model is None:
        return None
    result = _city(model, char_id)
    result["char_id"] = char_id
    return result
