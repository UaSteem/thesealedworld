"""Normalized support-skill rules shared by combat and outside vitals."""

from __future__ import annotations

from math import isfinite
from typing import Any


def _normalized(value: Any) -> float:
    if isinstance(value, dict):
        value = value.get("value", value.get("level", value.get("total_xp", value.get("xp", 0.0))))
    try:
        normalized = float(value or 0.0)
    except (TypeError, ValueError, OverflowError):
        normalized = 0.0
    if not isfinite(normalized):
        normalized = 0.0
    return max(0.0, min(1.0, normalized))


def build_support_skill_rules(skills: dict[str, Any] | None) -> dict[str, Any]:
    anatomy = _normalized((skills or {}).get("skill_anatomy", 0.0))
    tactics = _normalized((skills or {}).get("skill_tactics", 0.0))
    rules: dict[str, Any] = {}
    if anatomy:
        rules["anatomy_regen_mult"] = {"outside": 1.0 + 3.0 * anatomy, "combat": 1.0 + anatomy}
        # Incoming-healing sensitivity is the explicit anatomy bonus, distinct
        # from amplification of attribute-derived regeneration/tactics bases.
        rules["anatomy_received_healing_bonus"] = anatomy
    if tactics:
        rules["tactics_attribute_mult"] = {
            "evasion": 1.0 + tactics,
            "anti_dodge_chance": 1.0 + 3.0 * tactics,
            "counter_attack_chance": 1.0 + 4.0 * tactics,
        }
    return rules
