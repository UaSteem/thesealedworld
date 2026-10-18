"""Read-only, in-memory monster support-skill and experimental GS probes.

Run from the repository root with ``python -m tools.diagnostics.probe_support_skills_monsters_gs``.
No persistence adapters or application containers are constructed.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

from tools.diagnostics.probe_combat_support_skills import consumers

from src.backend.features.character.runtime.experimental_gear_score import (
    ExperimentalGearScoreCalculator,
    ExperimentalGearScoreConfig,
)
from src.backend.features.character.schemas.session import CharacterSessionAttributesDTO
from src.backend.features.combat.runtime.engine.stats_engine import StatsEngine
from src.backend.features.monsters.catalog.materialization.generation_fields import build_scaled_skills
from src.backend.features.monsters.catalog.registry import get_family_config
from src.backend.features.monsters.instances.runtime.combat_actor_input import MonsterCombatActorInputBuilder
from src.backend.features.monsters.instances.runtime.combat_math_model import MonsterCombatMathModelBuilder


def probe() -> dict:
    family = get_family_config("goblin_tribe")
    assert family is not None
    variant = family.variants["goblin_chief"]
    tier_skills = build_scaled_skills(family, variant, member_tier=2).skills
    attributes = {key: 10 for key in CharacterSessionAttributesDTO.model_fields}
    builder = MonsterCombatMathModelBuilder()
    gs = ExperimentalGearScoreCalculator()
    sweep = {}
    for key in ("skill_tactics", "skill_anatomy"):
        rows = []
        baseline = None
        for value in (0.0, 0.25, 0.5, 1.0):
            skills = {**tier_skills, key: value}
            raw = builder.build_raw(
                attributes=attributes,
                skills=skills,
                monster_meta={"family_id": family.id, "archetype": family.archetype, "role": variant.role},
            )
            actor = SimpleNamespace(
                active_snapshot={
                    "combat_snapshot_input": {
                        "meta": {"role": variant.role},
                        "raw": raw,
                        "skills": skills,
                        "loadout": {
                            "layout": {
                                "main_hand": "skill_macing",
                                "off_hand": "skill_shield_mastery",
                                "body": "skill_heavy_armor",
                            }
                        },
                    }
                },
                metadata_={},
            )
            combat = MonsterCombatActorInputBuilder().build_snapshot(actor)["combat"]
            stats, _ = StatsEngine.build_stats(
                raw=combat["math_model"], skills=combat["skills"], loadout=combat["loadout"]
            )
            projection = gs.calculate_from_raw(raw, skills=skills, loadout=combat["loadout"])
            mods = stats.mods.model_dump()
            combat_results = consumers(stats)
            if baseline is None:
                baseline = (raw, mods, projection, combat_results)
            rows.append(
                {
                    "skill": value,
                    "snapshot_skill": combat["skills"][key],
                    "actor_stats_skill": getattr(stats.skills, key),
                    "raw_equal_to_zero": raw == baseline[0],
                    "all_modifiers_equal_to_zero": mods == baseline[1],
                    "entire_gs_equal_to_zero": projection == baseline[2],
                    "resolver_equal_to_zero": combat_results == baseline[3],
                    "gs_total": projection["total"],
                    "modifiers": {
                        k: mods[k]
                        for k in (
                            "evasion",
                            "anti_dodge_chance",
                            "counter_attack_chance",
                            "hp_regen",
                            "outside_hp_regen",
                            "combat_hp_regen",
                            "en_regen",
                            "combat_en_regen",
                            "received_healing_bonus",
                        )
                    },
                }
            )
        sweep[key] = rows

    # Explicit light armor and nonzero dodge supply the conditional counter window.
    calculator = ExperimentalGearScoreCalculator(ExperimentalGearScoreConfig(reference_anti_dodge=0))
    base = {"hp": 100, "evasion": 0.2, "counter_attack_chance": 0.2, "main_hand_damage_base": 10}
    skills = {"skill_light_armor": 1}
    loadout = {"layout": {"main_hand": "skill_swords", "body": "skill_light_armor"}}
    initial = calculator.calculate_from_calculated(base, skills=skills, loadout=loadout)
    controls = []
    for key, value in (
        ("evasion", 0.3),
        ("anti_dodge_chance", 0.2),
        ("counter_attack_chance", 0.4),
        ("combat_hp_regen", 2),
        ("combat_en_regen", 3),
        ("combat_stamina_regen", 4),
        ("outside_hp_regen", 99),
        ("hp_regen", 99),
        ("received_healing_bonus", 0.5),
    ):
        result = calculator.calculate_from_calculated({**base, key: value}, skills=skills, loadout=loadout)
        controls.append(
            {
                "modifier": key,
                "value": value,
                "total": result["total"],
                "delta": round(result["total"] - initial["total"], 3),
                "support_score": result["components"]["support"]["score"],
            }
        )
    return {
        "scope": "in-memory catalog, monster raw, snapshot, ActorStats, controlled resolver exchanges and experimental GS",
        "catalog_variant": variant.id,
        "tier_2_skills": tier_skills,
        "monster_sweep": sweep,
        "gs_control_baseline": initial["total"],
        "gs_controls": controls,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
