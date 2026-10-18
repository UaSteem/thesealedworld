"""Current support skills are projected from stored monster snapshots in memory."""

from copy import deepcopy
from types import SimpleNamespace

import pytest

from src.backend.features.character.runtime.rules.support_skills import build_support_skill_rules
from src.backend.features.combat.runtime.engine.stats_engine import StatsEngine
from src.backend.features.monsters.instances.runtime.combat_actor_input import MonsterCombatActorInputBuilder


def _monster(skills, rules=None):
    raw = {
        "attributes": {
            "agility": {"base": 11},
            "perception": {"base": 11},
            "mental": {"base": 11},
        },
        "modifiers": {"hp": {"base": 100}, "evasion": {"source": {"clan_trait:probe": "+0.1"}}},
        "pipeline": {"family_id": "goblin_tribe", "actor_kind": "monster"},
    }
    if rules is not None:
        raw["rules"] = rules
    return SimpleNamespace(
        role="veteran",
        metadata_={},
        active_snapshot={
            "combat_snapshot_input": {
                "meta": {"role": "veteran"},
                "raw": raw,
                "skills": skills,
                "loadout": {"layout": {"main_hand": "skill_unarmed"}},
                "source": {"monster_id": "stored-probe"},
                "status": {"hp": {"current": 50, "max": 100}},
            }
        },
    )


def test_existing_monster_without_support_rules_receives_effects_without_persisted_mutation():
    monster = _monster(
        {"skill_tactics": 1, "skill_anatomy": 1},
        {"attribute_profile": "monster:humanoid", "unrelated": {"keep": True}},
    )
    before = deepcopy(monster.active_snapshot)
    combat = MonsterCombatActorInputBuilder().build_snapshot(monster)["combat"]
    stats, _ = StatsEngine.build_stats(raw=combat["math_model"], skills=combat["skills"], loadout=combat["loadout"])
    assert stats.mods.evasion == pytest.approx(0.1 + 0.22 * 2)
    assert stats.mods.anti_dodge_chance == pytest.approx(0.33 * 4)
    assert stats.mods.combat_en_regen == 5.5
    assert stats.mods.received_healing_bonus == 1
    assert stats.mods.combat_hp_regen == 0
    assert combat["math_model"]["rules"]["unrelated"] == {"keep": True}
    assert combat["math_model"]["modifiers"] == before["combat_snapshot_input"]["raw"]["modifiers"]
    assert monster.active_snapshot == before


@pytest.mark.parametrize("skills", [{}, {"skill_tactics": 0, "skill_anatomy": 0}])
def test_zero_current_skills_remove_stale_positive_support_rules_only(skills):
    monster = _monster(
        skills,
        {
            "attribute_profile": "monster:beast",
            **build_support_skill_rules(
                {
                    "skill_tactics": 1,
                    "skill_anatomy": 1,
                }
            ),
            "other": 7,
        },
    )
    before = deepcopy(monster.active_snapshot)
    result = MonsterCombatActorInputBuilder().build_input(monster)
    assert result["raw"]["rules"] == {"attribute_profile": "monster:beast", "other": 7}
    assert monster.active_snapshot == before


def test_current_support_rules_are_replaced_without_double_application():
    skills = {"skill_anatomy": 0.5, "skill_tactics": 0.25}
    rules = {"attribute_profile": "monster:humanoid", **build_support_skill_rules(skills)}
    monster = _monster(skills, rules)
    before = deepcopy(monster.active_snapshot)
    builder = MonsterCombatActorInputBuilder()
    first = builder.build_input(monster)
    second = builder.build_input(monster)
    assert first["raw"]["rules"] == second["raw"]["rules"] == rules
    first_stats, _ = StatsEngine.build_stats(raw=first["raw"], skills=skills, loadout=first["loadout"])
    assert first_stats.mods.evasion == pytest.approx(0.1 + 0.22 * 1.25)
    assert first_stats.mods.combat_en_regen == 4.125
    assert first_stats.mods.received_healing_bonus == 0.5
    assert monster.active_snapshot == before


def test_absent_support_skills_do_not_add_empty_rules_to_old_raw():
    monster = _monster({"skill_unarmed": 0.5})
    before = deepcopy(monster.active_snapshot)
    result = MonsterCombatActorInputBuilder().build_input(monster)
    assert "rules" not in result["raw"]
    assert result["raw"] == before["combat_snapshot_input"]["raw"]
    assert monster.active_snapshot == before
