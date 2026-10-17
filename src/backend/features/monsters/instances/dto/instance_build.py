"""Detached results of assembling a catalog member for a requested tier."""

from dataclasses import dataclass
from typing import Any

from src.backend.features.monsters.catalog.contracts import MonsterRole


@dataclass(frozen=True, slots=True)
class MonsterCombatProjectionDTO:
    """Pre-combat values and their inputs; dictionaries belong to this build."""

    values: dict[str, float]
    raw: dict[str, Any]
    formulas: dict[str, str]
    loadout: dict[str, Any]


@dataclass(frozen=True, slots=True)
class MonsterInstanceBuildDTO:
    """One catalog identity with baseline and equipped pre-combat projections."""

    family_id: str
    member_id: str
    clan_id: str
    variant_id: str
    role: MonsterRole
    tier: int
    tier_multiplier: float
    combat_math_version: str
    catalog_attributes: dict[str, int]
    tier_attributes: dict[str, int]
    skills: dict[str, float]
    baseline: MonsterCombatProjectionDTO
    equipped: MonsterCombatProjectionDTO
