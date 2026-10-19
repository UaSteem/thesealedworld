from copy import deepcopy

import pytest

from src.backend.features.character.runtime.experimental_gear_score import (
    ExperimentalGearScoreCalculator,
    ExperimentalGearScoreConfig,
)


def project(values, skills=None, layout=None, config=None):
    # Formula tests use an explicit zero-antidodge reference unless overridden.
    return ExperimentalGearScoreCalculator(config or ExperimentalGearScoreConfig(reference_anti_dodge=0)).calculate_from_calculated(
        values, skills=skills, loadout={"layout": layout or {}}
    )


def test_armor_percent_formula_and_no_ehp_double_count():
    result = project({"hp": 100, "armor": 20}, {"skill_heavy_armor": 1})
    assert result["components"]["base_ehp"]["value"] == pytest.approx(154)
    assert result["components"]["extra_ehp"]["value"] == 0
    assert result["total"] == pytest.approx(15.4)


def test_parry_mastery_and_sequential_avoidance():
    result = project({"hp": 100, "evasion": 0.2, "parry": 0.1}, {"skill_parrying": 1})
    assert result["effective"]["parry_chance"] == 0.5
    assert result["effective"]["damage_pass_fraction"] == pytest.approx(0.8 * 0.5)
    assert result["components"]["extra_ehp"]["value"] == pytest.approx(60)


def test_reference_antidodge_neutralizes_dodge_not_parry():
    result = project(
        {"hp": 100, "evasion": 0.2, "parry": 0.1}, config=ExperimentalGearScoreConfig(reference_anti_dodge=0.3)
    )
    assert result["effective"]["dodge_chance"] == 0
    assert result["effective"]["parry_chance"] == 0.1


def test_shield_disables_dodge_and_absorbs_only_fraction():
    result = project(
        {"hp": 100, "armor": 10, "shield_guard_power": 20, "evasion": 0.2},
        {"skill_shield_mastery": 1},
        {"off_hand": "skill_shield_mastery"},
    )
    assert result["effective"]["dodge_chance"] == 0
    assert 0 < result["effective"]["block_chance"] < 1
    assert result["effective"]["blocked_armor_reduction"] > result["effective"]["armor_reduction"]
    # Block adds armor rather than cancelling its entire hit.
    assert result["effective"]["damage_pass_fraction"] > 1 - result["effective"]["block_chance"]


def test_resistance_and_suppression_never_contribute():
    base = project({"hp": 100})
    modified = project(
        {
            "hp": 100,
            "physical_resistance": 999,
            "physical_suppression": 999,
            "magical_penetration": 999,
            "fire_resistance": 999,
        }
    )
    assert modified == base


def test_dual_followup_is_base_not_chance_bonus_and_input_not_mutated():
    values = {"hp": 100, "main_hand_damage_base": 10, "off_hand_damage_base": 8}
    original = deepcopy(values)
    layout = {"main_hand": "skill_fencing", "off_hand": "skill_fencing", "tactical_style": "skill_dual_wield"}
    result = project(values, layout=layout)
    assert len(result["effective"]["hands"]) == 2
    assert result["components"]["base_offense"]["value"] > project(values)["components"]["base_offense"]["value"]
    assert result["components"]["extra_offense"]["value"] == 0
    assert values == original


def test_crit_mastery_uses_cap_and_known_trigger_multiplier():
    result = project(
        {"main_hand_damage_base": 10, "main_hand_crit_chance": 0.5},
        {"skill_macing": 1},
        {"main_hand": "skill_macing", "main_hand_trigger": "crit.weapon_heavy_crit"},
    )
    hand = result["effective"]["hands"]["main_hand"]
    assert hand["crit_chance"] == 0.75
    assert hand["expected_crit_multiplier"] == 2
    assert result["components"]["extra_offense"]["value"] == pytest.approx(hand["base_expected_damage"] * 0.75)


def test_support_direct_sum_not_added_to_ehp():
    result = project(
        {
            "hp": 100,
            "hp_regen": 99,
            "en_regen": 99,
            "stamina_regen": 99,
            "combat_hp_regen": 2,
            "combat_en_regen": 3,
            "combat_stamina_regen": 4,
        }
    )
    assert result["components"]["support"]["score"] == 9
    assert result["components"]["base_ehp"]["value"] == 100
    assert result["components"]["extra_ehp"]["value"] == 0


def test_configuration_validation():
    with pytest.raises(ValueError):
        ExperimentalGearScoreConfig(armor_cap=1)
    with pytest.raises(ValueError):
        ExperimentalGearScoreConfig(base_ehp_weight=float("nan"))


@pytest.mark.parametrize("armor_type,mastery", [("light", 0.2), ("medium", 0.7), ("heavy", 1.0)])
def test_armor_matches_actual_resolver_helper(armor_type, mastery):
    from src.backend.features.combat.dto.actor import ActorStats
    from src.backend.features.combat.dto.pipeline import PipelineContextDTO
    from src.backend.features.combat.runtime.engine.resolver.support.armor_math import effective_armor_trace

    skills = {f"skill_{armor_type}_armor": mastery}
    ctx = PipelineContextDTO()
    setattr(ctx.flags.mastery, f"{armor_type}_armor", True) if armor_type != "heavy" else None
    _, trace = effective_armor_trace(
        ActorStats(), ActorStats.from_flat_dict({"armor": 40, **skills}), ctx, incoming_damage=100
    )
    result = project({"hp": 100, "armor": 40}, skills, {"body": f"skill_{armor_type}_armor"})
    assert result["effective"]["armor_reduction"] == pytest.approx(trace["pct"])


def test_parry_matches_resolver_roll_probability(monkeypatch):
    from src.backend.features.combat.dto.actor import ActorStats
    from src.backend.features.combat.dto.pipeline import InteractionResultDTO, PipelineContextDTO
    from src.backend.features.combat.runtime.engine.math_core import MathCore
    from src.backend.features.combat.runtime.engine.resolver.steps.parry import parry_step

    chances = []
    monkeypatch.setattr(MathCore, "roll_chance", lambda chance: (chances.append(chance) or 1.0, False))
    parry_step.run(
        ActorStats(),
        ActorStats.from_flat_dict({"parry": 0.15, "skill_parrying": 0.8}),
        PipelineContextDTO(),
        InteractionResultDTO(),
    )
    result = project({"hp": 100, "parry": 0.15}, {"skill_parrying": 0.8})
    assert chances == [result["effective"]["parry_chance"]]


def test_real_crosscut_layout_identifier_projects_probabilistic_bonus():
    result = project(
        {"main_hand_damage_base": 10, "main_hand_crit_chance": 0.2},
        {"skill_dual_wield": 0.2},
        {"tactical_style": "skill_dual_wield", "tactical_style_trigger": "crit.style_dual_cross_cut"},
    )
    assert result["effective"]["hands"]["main_hand"]["expected_crit_multiplier"] == pytest.approx(1.2)
    assert result["components"]["extra_offense"]["value"] > 0


def test_light_counter_opens_on_dodge_with_half_probability_mastery_boost():
    result = project(
        {"evasion": 0.4, "parry": 0.3, "counter_attack_chance": 0.2, "main_hand_damage_base": 10},
        {"skill_light_armor": 0.5},
        {"body": "skill_light_armor"},
    )
    counter = result["components"]["extra_offense"]["passive_counters"]
    assert counter["dodge_counter_probability"] == pytest.approx(0.4 * (0.2 + 0.3) / 2)
    assert counter["parry_counter_probability"] == 0
    assert counter["extra_expected_damage"] == pytest.approx(0.1 * result["components"]["base_offense"]["value"])


def test_medium_counter_requires_surviving_dodge_and_armor_skill_gate():
    result = project(
        {"evasion": 0.4, "parry": 0.3, "counter_attack_chance": 0.2, "main_hand_damage_base": 10},
        {"skill_medium_armor": 0.5},
        {"body": "skill_medium_armor"},
    )
    counter = result["components"]["extra_offense"]["passive_counters"]
    assert counter["parry_counter_probability"] == pytest.approx(0.6 * 0.3 * 0.5 * 0.2)
    assert counter["dodge_counter_probability"] == 0


def test_shield_counter_is_instant_partial_damage_without_accuracy_or_crit():
    result = project(
        {"parry": 0.2, "shield_guard_power": 20, "counter_attack_chance": 0.4, "main_hand_damage_base": 10},
        {"skill_shield_mastery": 1},
        {"off_hand": "skill_shield_mastery"},
    )
    counter = result["components"]["extra_offense"]["passive_counters"]
    assert counter["shield_counter_probability"] == pytest.approx(0.8 * 0.3 * 0.4)
    assert counter["shield_counter_damage"] == 5
    assert counter["extra_expected_damage"] == pytest.approx(0.8 * 0.3 * 0.4 * 5)


def test_dual_counter_includes_offhand_once_without_recursion():
    result = project(
        {"evasion": 0.4, "counter_attack_chance": 0.2, "main_hand_damage_base": 10, "off_hand_damage_base": 8},
        {"skill_light_armor": 0.5},
        {"body": "skill_light_armor", "tactical_style": "skill_dual_wield", "off_hand": "skill_fencing"},
    )
    counter = result["components"]["extra_offense"]["passive_counters"]
    pair_damage = sum(hand["base_expected_damage"] for hand in result["effective"]["hands"].values())
    assert counter["counter_sequence_expected_damage"] == pytest.approx(pair_damage)
    assert counter["extra_expected_damage"] == pytest.approx(0.1 * pair_damage)


@pytest.mark.parametrize("ranged,opportunities", [(True, 1), (False, 0)])
def test_passive_counter_offense_disabled_for_ranged_or_zero_reference_attacks(ranged, opportunities):
    result = project(
        {"evasion": 0.4, "counter_attack_chance": 0.2, "main_hand_damage_base": 10},
        {"skill_light_armor": 0.5},
        {"body": "skill_light_armor", "tactical_style": "skill_ranged_combat" if ranged else ""},
        ExperimentalGearScoreConfig(reference_incoming_melee_opportunities=opportunities),
    )
    assert result["components"]["extra_offense"]["value"] == 0


def test_default_reference_subtracts_thirty_points_and_floors_dodge():
    calculator = ExperimentalGearScoreCalculator()
    result = calculator.calculate_from_calculated({"hp": 100, "evasion": 0.6})
    assert result["effective"]["dodge_chance"] == pytest.approx(0.3)
    assert result["components"]["extra_ehp"]["value"] == pytest.approx(30)
    low = calculator.calculate_from_calculated({"hp": 100, "evasion": 0.2})
    assert low["effective"]["dodge_chance"] == 0


def test_linear_defense_parts_scale_with_armored_ehp_and_sum_once():
    result = project({"hp": 100, "armor": 20, "evasion": 0.6, "parry": 0.5}, {"skill_heavy_armor": 1})
    parts = result["components"]["extra_ehp"]["parts"]
    assert parts["dodge"]["value"] == pytest.approx(154 * 0.6)
    assert parts["parry"]["value"] == pytest.approx(154 * 0.4 * 0.5)
    assert result["components"]["extra_ehp"]["value"] == pytest.approx(154 * 0.8)
    assert result["total"] == pytest.approx(sum(p["score"] for p in result["components"].values()), abs=0.0005)


def test_linear_block_only_credits_extra_absorption_after_parry():
    result = project({"hp": 100, "armor": 20, "shield_guard_power": 40, "parry": 0.2},
                     {"skill_heavy_armor": 1, "skill_shield_mastery": 1},
                     {"body": "skill_heavy_armor", "off_hand": "skill_shield_mastery"})
    e = result["effective"]
    parts = result["components"]["extra_ehp"]["parts"]
    fraction = (e["blocked_armor_reduction"] - e["armor_reduction"]) / (1 - e["armor_reduction"])
    assert parts["dodge"]["value"] == 0
    assert parts["block"]["value"] == pytest.approx(154 * 0.8 * e["block_chance"] * fraction)
    assert sum(p["value"] for p in parts.values()) == pytest.approx(result["components"]["extra_ehp"]["value"])


def test_chance_offense_parts_equal_aggregate_without_base_offhand_double_count():
    result = project({"evasion": 0.5, "counter_attack_chance": 0.2, "main_hand_damage_base": 10,
                      "off_hand_damage_base": 8, "main_hand_crit_chance": 0.2},
                     {"skill_light_armor": 0.5},
                     {"body": "skill_light_armor", "off_hand": "skill_fencing",
                      "tactical_style": "skill_dual_wield", "main_hand_trigger": "crit.weapon_heavy_crit"})
    component = result["components"]["extra_offense"]
    assert component["parts"]["crit"]["value"] > 0
    assert component["parts"]["counter"]["value"] > 0
    assert sum(p["value"] for p in component["parts"].values()) == pytest.approx(component["value"])


@pytest.mark.parametrize(
    "target_evasion,cap,anti_dodge,suppressed",
    [(0, 0.75, 0.3, 0), (0.3, 0.75, 0, 0), (0.3, 0.75, -0.2, 0),
     (0.3, 0.75, 0.1, 0.1), (0.3, 0.75, 2, 0.3),
     (1.2, 0.75, 0.3, 0), (1.2, 0.75, 0.6, 0.15)],
)
def test_anti_dodge_suppression_uses_actual_delta_after_cap(target_evasion, cap, anti_dodge, suppressed):
    result = project(
        {"main_hand_damage_base": 10, "anti_dodge_chance": anti_dodge},
        config=ExperimentalGearScoreConfig(reference_target_evasion=target_evasion, reference_target_dodge_cap=cap),
    )
    extra = result["components"]["extra_offense"]
    assert extra["anti_dodge"]["anti_dodge_chance"] == anti_dodge
    assert extra["anti_dodge"]["suppressed_dodge_probability"] == pytest.approx(suppressed)
    assert extra["parts"]["anti_dodge"]["value"] == pytest.approx(
        result["components"]["base_offense"]["value"] * suppressed
    )


def test_anti_dodge_preserves_accuracy_base_and_counters_and_weights_both_hands_once():
    values = {"hp": 100, "main_hand_damage_base": 10, "off_hand_damage_base": 8,
              "main_hand_crit_chance": 0.2, "evasion": 0.5, "counter_attack_chance": 0.2}
    layout = {"body": "skill_light_armor", "tactical_style": "skill_dual_wield",
              "off_hand": "skill_fencing", "main_hand_trigger": "crit.weapon_heavy_crit"}
    baseline = project(values, {"skill_light_armor": 0.5}, layout)
    result = project({**values, "anti_dodge_chance": 0.2}, {"skill_light_armor": 0.5}, layout)
    assert result["version"] == "physical-v5"
    assert result["effective"]["hands"] == baseline["effective"]["hands"]
    assert result["components"]["base_offense"] == baseline["components"]["base_offense"]
    extra = result["components"]["extra_offense"]
    assert extra["passive_counters"] == baseline["components"]["extra_offense"]["passive_counters"]
    assert extra["parts"]["crit"] == baseline["components"]["extra_offense"]["parts"]["crit"]
    pair_damage = sum(h["base_expected_damage"] for h in result["effective"]["hands"].values())
    bonus = pair_damage * 0.2
    assert extra["parts"]["anti_dodge"]["value"] == pytest.approx(bonus)
    assert extra["parts"]["anti_dodge"]["score"] == pytest.approx(bonus * 0.55)
    assert extra["parts"]["anti_dodge"]["weight"] == result["components"]["base_offense"]["weight"] / 2
    assert sum(p["value"] for p in extra["parts"].values()) == pytest.approx(extra["value"])
    assert result["total"] == pytest.approx(baseline["total"] + bonus * 0.55, abs=0.001)
    assert result["total"] == pytest.approx(sum(p["score"] for p in result["components"].values()), abs=0.0005)


def test_reference_target_dodge_cap_rejects_above_probability_range():
    with pytest.raises(ValueError):
        ExperimentalGearScoreConfig(reference_target_dodge_cap=1.1)


def test_dual_offense_discount_scales_each_attack_component_once_without_defense_change():
    values = {"hp": 100, "evasion": 0.4, "counter_attack_chance": 0.2,
              "main_hand_damage_base": 10, "off_hand_damage_base": 8,
              "anti_dodge_chance": 0.2, "main_hand_crit_chance": 0.2}
    skills = {"skill_light_armor": 0.5}
    layout = {"main_hand": "skill_fencing", "off_hand": "skill_fencing",
              "tactical_style": "skill_dual_wield", "body": "skill_light_armor",
              "main_hand_trigger": "crit.weapon_heavy_crit"}
    before = project(values, skills, layout, ExperimentalGearScoreConfig(dual_wield_offense_factor=1, reference_anti_dodge=0))
    after = project(values, skills, layout)
    for key in ("base_offense", "extra_offense"):
        assert after["components"][key]["value"] == pytest.approx(before["components"][key]["value"] * 0.8)
    for key in ("crit", "counter", "anti_dodge"):
        assert after["components"]["extra_offense"]["parts"][key]["value"] == pytest.approx(
            before["components"]["extra_offense"]["parts"][key]["value"] * 0.8)
    for key in ("base_ehp", "extra_ehp", "support"):
        assert after["components"][key] == before["components"][key]


def test_dual_discount_not_applied_to_single_weapon_or_shield():
    for layout in ({"main_hand": "skill_swords"},
                   {"main_hand": "skill_swords", "off_hand": "skill_shield_mastery", "tactical_style": "skill_shield_mastery"}):
        before = project({"main_hand_damage_base": 10}, layout=layout,
                         config=ExperimentalGearScoreConfig(dual_wield_offense_factor=1, reference_anti_dodge=0))
        after = project({"main_hand_damage_base": 10}, layout=layout)
        assert after["components"] == before["components"]
