"""Live character GS using the accepted physical combat-value model."""

from __future__ import annotations

from typing import Any

from src.backend.features.character.runtime.combat_actor_input import CharacterCombatActorInputBuilder
from src.backend.features.character.runtime.combat_math_model import CharacterCombatMathModelBuilder
from src.backend.features.character.runtime.gear_score_model import GEAR_SCORE_VERSION, GearScoreModel


class CharacterGearScoreCalculator:
    """One canonical calculation for game sessions and diagnostic probes."""

    def __init__(self, math_model: CharacterCombatMathModelBuilder | None = None) -> None:
        self.math_model = math_model or CharacterCombatMathModelBuilder()

    def calculate_from_active_character(self, active_character: dict[str, Any]) -> float:
        return float(self.calculate_breakdown_from_active_character(active_character)["total"])

    def calculate_breakdown_from_active_character(self, active_character: dict[str, Any]) -> dict[str, float]:
        actor = CharacterCombatActorInputBuilder(self.math_model).build_input(active_character)
        return self.calculate_breakdown_from_raw(actor["raw"], skills=actor["skills"], loadout=actor["loadout"])

    @staticmethod
    def calculate_from_raw(
        raw: dict[str, Any], *, skills: dict[str, Any] | None = None, loadout: dict[str, Any] | None = None
    ) -> float:
        return float(GearScoreModel().calculate_from_raw(raw, skills=skills, loadout=loadout)["total"])

    @staticmethod
    def calculate_from_calculated(
        calculated: dict[str, Any], *, skills: dict[str, Any] | None = None, loadout: dict[str, Any] | None = None
    ) -> float:
        """Accept waterfall values before base-power projection, like the canonical model."""
        return float(GearScoreModel().calculate_from_calculated(calculated, skills=skills, loadout=loadout)["total"])

    @staticmethod
    def calculate_breakdown_from_raw(
        raw: dict[str, Any], *, skills: dict[str, Any] | None = None, loadout: dict[str, Any] | None = None
    ) -> dict[str, float]:
        result = GearScoreModel().calculate_from_raw(raw, skills=skills, loadout=loadout)
        return CharacterGearScoreCalculator._breakdown(result)

    @staticmethod
    def calculate_breakdown_from_calculated(
        calculated: dict[str, Any], *, skills: dict[str, Any] | None = None, loadout: dict[str, Any] | None = None
    ) -> dict[str, float]:
        result = GearScoreModel().calculate_from_calculated(calculated, skills=skills, loadout=loadout)
        return CharacterGearScoreCalculator._breakdown(result)

    @staticmethod
    def _breakdown(result: dict[str, Any]) -> dict[str, float]:
        components = result["components"]
        scores = {name: float(part["score"]) for name, part in components.items()}
        scores.update(
            {
                name: float(part["score"])
                for key in ("extra_ehp", "extra_offense")
                for name, part in components[key]["parts"].items()
            }
        )
        return {
            **scores,
            "total": float(result["total"]),
            "offense": scores["base_offense"] + scores["extra_offense"],
            "defense": scores["base_ehp"] + scores["extra_ehp"],
            "resources": scores["support"],
            "skills": 0.0,
            "utility": 0.0,
        }


__all__ = ["CharacterGearScoreCalculator", "GEAR_SCORE_VERSION"]
