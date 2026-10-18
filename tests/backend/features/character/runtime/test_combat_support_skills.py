"""Behavior contracts for support skills; all inputs stay in memory.

Anatomy regeneration uses the approved outside x4/combat x2 mastery caps.
"""

from copy import deepcopy

import pytest

from src.backend.core.calculators.stats_waterfall_calculator import StatsWaterfallCalculator
from src.backend.features.character.runtime.combat_math_model import CharacterCombatMathModelBuilder
from src.backend.features.character.runtime.experimental_gear_score import ExperimentalGearScoreCalculator
from src.backend.features.combat.dto.actor import ActorMetaDTO, ActorRawDTO, ActorSnapshot
from src.backend.features.combat.runtime.engine.stats_engine import StatsEngine
from src.backend.features.monsters.instances.runtime.combat_math_model import MonsterCombatMathModelBuilder

LEVELS = (0.0, 0.25, 0.5, 1.0)
LAYOUT = {"layout": {"main_hand": "skill_unarmed", "body": "skill_light_armor"}}
ITEMS = {
    "layout": {"equipment": {"ring_1": "support-probe-ring"}},
    "by_id": {
        "support-probe-ring": {
            "item_id": "support-probe-ring",
            "item_type": "accessory",
            "mechanics": {
                "bonuses": {
                    "hp": "+100",
                    "hp_regen": "+2",
                    "en_regen": "+3",
                    "stamina_regen": "+4",
                    "evasion": "+0.2",
                    "anti_dodge_chance": "+0.05",
                    "counter_attack_chance": "+0.1",
                    "received_healing_bonus": "+0.1",
                    "armor": "+7",
                    "magical_damage": "+9",
                }
            },
        }
    },
}


def _build(skill, level, *, monster=False, attributes=None):
    skills = {"skill_unarmed": 0.6, "skill_light_armor": 0.4, "skill_parrying": 0.2, skill: level}
    kwargs = {"attributes": attributes or {}, "items": deepcopy(ITEMS), "skills": skills}
    if monster:
        raw = MonsterCombatMathModelBuilder().build_raw(
            **kwargs, monster_meta={"family_id": "goblin_tribe", "archetype": "humanoid", "role": "veteran"}
        )
    else:
        raw = CharacterCombatMathModelBuilder().build_raw(**kwargs)
    stats, _ = StatsEngine.build_stats(raw=raw, skills=skills, loadout=LAYOUT)
    return raw, skills, stats


@pytest.mark.parametrize("level", LEVELS)
@pytest.mark.parametrize("monster", [False, True], ids=["player", "monster"])
def test_anatomy_preserves_unrelated_fields_and_monster_hp_regen_guard(level, monster):
    _, _, stats = _build("skill_anatomy", level, monster=monster)
    assert stats.mods.hp == 100
    _, _, baseline = _build("skill_anatomy", 0, monster=monster)
    for field in ("stamina_regen", "outside_stamina_regen", "combat_stamina_regen", "armor", "magical_damage"):
        assert getattr(stats.mods, field) == getattr(baseline.mods, field)
    if monster:
        assert stats.mods.hp_regen == 0
        assert stats.mods.outside_hp_regen == 0
        assert stats.mods.combat_hp_regen == 0


@pytest.mark.parametrize("skill", ["skill_tactics", "skill_anatomy"])
def test_zero_support_skill_preserves_existing_item_and_regen_values(skill):
    _, _, stats = _build(skill, 0)
    assert stats.mods.hp_regen == 2.5
    assert stats.mods.outside_hp_regen == 2.5
    assert stats.mods.combat_hp_regen == 2.5
    assert stats.mods.en_regen == 3
    assert stats.mods.combat_en_regen == 3
    assert stats.mods.evasion == pytest.approx(0.2)
    assert stats.mods.anti_dodge_chance == pytest.approx(0.05)
    assert stats.mods.received_healing_bonus == pytest.approx(0.1)


def test_support_skill_rebuild_and_dirty_stats_do_not_accumulate_bonus_or_mutate_raw():
    raw, skills, _ = _build("skill_anatomy", 0.5)
    original = deepcopy(raw)
    actor = ActorSnapshot(
        meta=ActorMetaDTO(id="support-test", name="Support test", type="player", team="blue"),
        raw=ActorRawDTO.model_validate(raw),
        skills=skills,
    )
    StatsEngine.ensure_stats(actor)
    first = actor.stats.mods.model_dump()
    for _ in range(3):
        actor.dirty_stats = {"support-test"}
        StatsEngine.ensure_stats(actor)
        assert actor.stats.mods.model_dump() == first
    assert raw == original
    rebuilt, _, stats = _build("skill_anatomy", 0.5)
    assert rebuilt == original
    assert stats.mods.model_dump() == first


@pytest.mark.parametrize("skill", ["skill_tactics", "skill_anatomy"])
def test_monster_experimental_gs_values_assembled_bonuses_once_without_separate_skill_score(skill):
    calculator = ExperimentalGearScoreCalculator()
    raw, skills, _ = _build(skill, 1, monster=True)
    actual = calculator.calculate_from_raw(raw, skills=skills, loadout=LAYOUT)
    values, _ = StatsWaterfallCalculator.calculate_waterfall(raw)
    neutral_skills = {**skills, skill: 0}
    replay = calculator.calculate_from_calculated(values, skills=neutral_skills, loadout=LAYOUT)
    assert actual == replay


@pytest.mark.parametrize("level", LEVELS)
@pytest.mark.parametrize("monster", [False, True], ids=["player", "monster"])
def test_anatomy_scales_hp_energy_by_approved_mode_once(level, monster):
    raw, _, stats = _build("skill_anatomy", level, monster=monster, attributes={"endurance": 11, "mental": 11})
    outside = 1 + 3 * level
    combat = 1 + level
    hp_base = 0 if monster else 2 + 1.1 + 133 * 0.005
    natural_hp = 0 if monster else 1.1 + 33 * 0.005
    assert stats.mods.hp_regen == pytest.approx(round(hp_base + natural_hp * (outside - 1), 4))
    assert stats.mods.outside_hp_regen == pytest.approx(round(hp_base + natural_hp * (outside - 1), 4))
    assert stats.mods.combat_hp_regen == pytest.approx(round(hp_base + natural_hp * (combat - 1), 4))
    assert stats.mods.en_regen == pytest.approx(3 + 2.75 * outside)
    assert stats.mods.outside_en_regen == pytest.approx(3 + 2.75 * outside)
    assert stats.mods.combat_en_regen == pytest.approx(3 + (2.75 * combat if monster else 0))
    values, explanation = StatsWaterfallCalculator.calculate_waterfall(raw)
    assert values["hp_regen"] == values["outside_hp_regen"]
    if level:
        assert "skill_anatomy" in explanation["outside_en_regen"]


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, 0),
        ("invalid", 0),
        (float("nan"), 0),
        (float("inf"), 0),
        (-1, 0),
        (2, 1),
        ({"value": 0.25}, 0.25),
        ({"level": 0.5}, 0.5),
        ({"total_xp": 1}, 1),
        ({"xp": 0.25}, 0.25),
    ],
)
def test_support_rule_normalizes_nested_and_invalid_skill_values(value, expected):
    from src.backend.features.character.runtime.rules.support_skills import build_support_skill_rules

    rules = build_support_skill_rules({"skill_anatomy": value})
    assert rules.get("anatomy_regen_mult", {}) == (
        {"outside": 1 + 3 * expected, "combat": 1 + expected} if expected else {}
    )
    assert build_support_skill_rules(None) == {}


def test_monster_gs_counts_anatomy_combat_energy_only_once():
    calculator = ExperimentalGearScoreCalculator()
    projections = []
    for level in (0, 1):
        raw, skills, _ = _build("skill_anatomy", level, monster=True, attributes={"mental": 12})
        projections.append(calculator.calculate_from_raw(raw, skills=skills, loadout=LAYOUT))
    base, actual = projections
    assert actual["components"]["support"]["score"] - base["components"]["support"]["score"] == pytest.approx(3)
    assert actual["components"]["base_ehp"] == base["components"]["base_ehp"]
    assert actual["total"] - base["total"] == pytest.approx(3)


@pytest.mark.parametrize("monster", [False, True])
@pytest.mark.parametrize("level", LEVELS)
def test_tactics_scales_only_attribute_portions_not_direct_item_modifiers(level, monster):
    attrs = {"agility": 11, "perception": 11, "memory": 11, "prediction": 11}
    raw, _, stats = _build("skill_tactics", level, monster=monster, attributes=attrs)
    assert stats.mods.evasion == pytest.approx(0.2 + 0.22 * (1 + level))
    assert stats.mods.anti_dodge_chance == pytest.approx(0.05 + 0.33 * (1 + 3 * level))
    assert stats.mods.counter_attack_chance == pytest.approx(0.1 + 0.044 * (1 + 4 * level))
    assert raw["modifiers"]["evasion"]["source"]["item:support-probe-ring"] == "+0.2"


@pytest.mark.parametrize("level", LEVELS)
def test_anatomy_leaves_item_only_regeneration_and_item_hp_floor_unscaled(level):
    _, _, stats = _build("skill_anatomy", level)
    assert stats.mods.hp_regen == 2.5
    assert stats.mods.outside_hp_regen == 2.5
    assert stats.mods.combat_hp_regen == 2.5
    assert stats.mods.en_regen == 3
    assert stats.mods.combat_en_regen == 3


def test_tactics_counts_attribute_bonuses_from_items_as_attributes():
    items = deepcopy(ITEMS)
    items["by_id"]["support-probe-ring"]["mechanics"]["bonuses"]["agility"] = "+11"
    raw = CharacterCombatMathModelBuilder().build_raw(
        attributes={"agility": 0}, items=items, skills={"skill_tactics": 1}
    )
    values, _ = StatsWaterfallCalculator.calculate_waterfall(raw)
    assert values["evasion"] == pytest.approx(0.2 + 0.22 * 2)


@pytest.mark.parametrize("level", LEVELS)
@pytest.mark.parametrize("monster", [False, True])
def test_anatomy_adds_explicit_incoming_sensitivity_to_item_bonus(level, monster):
    # This is the explicit biology bonus, not a multiplier of item bonuses.
    _, _, stats = _build("skill_anatomy", level, monster=monster)
    assert stats.mods.received_healing_bonus == pytest.approx(0.1 + level)


def test_support_skills_preserve_existing_item_multiplier_and_temp_order():
    raw, _, _ = _build("skill_tactics", 0.5, attributes={"agility": 11})
    raw["modifiers"]["evasion"]["source"]["item:multiplier"] = "*1.5"
    raw["modifiers"]["evasion"]["temp"]["spell"] = "+0.1"
    values, _ = StatsWaterfallCalculator.calculate_waterfall(raw)
    assert values["evasion"] == pytest.approx((0.22 * 1.5 + 0.2 + 0.1) * 1.5)
