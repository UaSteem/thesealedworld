import copy

import pytest

from src.backend.core.calculators.stats_waterfall_calculator import StatsWaterfallCalculator
from src.backend.features.character.runtime import CharacterCombatMathModelBuilder
from src.backend.features.items.dto.instance import ItemGenerationRequestDTO
from src.backend.features.items.runtime.accessory_bonuses import resolve_accessory_bonuses
from src.backend.features.items.runtime.item_factory import ItemFactory

PRECISION = {"hp": 0, "stamina": 0, "stamina_regen": 1, "hp_regen": 1, "en_regen": 1, "initiative": 1}

# T0 anchors are captured from the accepted R46 catalog, before the curve change.
CASES = [
    ("belt", "hp", "endurance", 8.0),
    ("boots", "stamina", "projection", 8.0),
    ("boots", "stamina_regen", "projection", 1.2),
    ("gloves", "anti_dodge_chance", "perception", 0.032),
    ("cloak", "hp_regen", "endurance", 0.4),
    ("ring", "mental_resistance", "mental", 0.024),
    ("amulet", "en_regen", "mental", 0.8),
    ("earring", "initiative", "agility", 0.56),
]


def attribute_twenty_contribution(key, attribute):
    values = []
    for amount in (0, 20):
        calculated, _ = StatsWaterfallCalculator.calculate_waterfall({
            "attributes": {attribute: {"base": amount}},
            "modifiers": {}, "rules": {"attribute_profile": "player"},
        })
        values.append(calculated.get(key, 0))
    return values[1] - values[0]


@pytest.mark.unit
@pytest.mark.parametrize("base_id,key,attribute,anchor", CASES)
def test_core_support_curve_rounds_anchors_and_matches_attribute20_at_t7(base_id, key, attribute, anchor):
    factory = ItemFactory()
    target = attribute_twenty_contribution(key, attribute)
    for category in factory.catalog.get_base_item(base_id).allowed_materials:
        previous = 0
        increments = []
        for tier in range(8):
            material = factory.catalog.get_material_for_tier(category, tier)
            item = factory.generate(ItemGenerationRequestDTO(base_id=base_id, material_id=material.id, rarity_tier=0))
            actual = item.implicit_bonuses[key]
            expected = round(anchor * (target / anchor) ** (tier / 7), PRECISION.get(key, 3))
            assert actual == pytest.approx(expected, abs=0.0001)
            assert actual > previous
            if tier:
                increments.append(actual - previous)
            previous = actual
            if tier == 7:
                equipped = item.model_dump(mode="json")
                equipped.update(item_id="support", item_type=item.item_type)
                raw = CharacterCombatMathModelBuilder().build_raw(
                    attributes={}, skills={},
                    items={"layout": {"equipment": {item.slot: "support"}}, "by_id": {"support": equipped}},
                )
                naked = CharacterCombatMathModelBuilder().build_raw(attributes={}, skills={})
                values, _ = StatsWaterfallCalculator.calculate_waterfall(raw)
                baseline, _ = StatsWaterfallCalculator.calculate_waterfall(naked)
                # HP regen includes natural HP from endurance in its reference;
                # energy uses outside contribution because player combat attribute regen is zero.
                output_key = f"outside_{key}" if key.endswith("_regen") else key
                assert values[output_key] - baseline[output_key] == pytest.approx(round(target, PRECISION.get(key, 3)), abs=0.0001)
        assert all(later >= earlier for earlier, later in zip(increments, increments[1:], strict=False))


@pytest.mark.unit
@pytest.mark.parametrize("tier_source", ["embedded", "material_id", "item_tier", "generation", "mechanics", "metadata"])
def test_saved_support_uses_actual_tier_and_preserves_other_sources(tier_source):
    factory = ItemFactory()
    material = factory.catalog.get_material_for_tier("ingots", 7)
    item = {"base_id": "ring"}
    mechanics = {
        "implicit_bonuses": {"mental_resistance": 0.007, "control_resistance": 0.123, "hp_regen": 4},
        "affixes": [{"affix_id": "hp_regen_bonus", "value": 2}],
    }
    if tier_source == "embedded":
        mechanics["material"] = {"tier": 7, "tier_mult": 0.1}
    elif tier_source == "material_id":
        item["material_id"] = material.id
    elif tier_source == "item_tier":
        item["item_tier"] = 7
    elif tier_source == "generation":
        item["generation"] = {"item_tier": 7}
    elif tier_source == "mechanics":
        mechanics["tier"] = 7
    else:
        item["metadata"] = {"tier": 7}
    original = copy.deepcopy(mechanics)
    result = resolve_accessory_bonuses(item, mechanics)
    assert result == {"mental_resistance": 0.727, "control_resistance": 0.123}
    assert resolve_accessory_bonuses(item, {**mechanics, "implicit_bonuses": result}) == result
    assert mechanics == original


@pytest.mark.unit
def test_missing_tier_provenance_uses_t0_without_guessing_from_multiplier_or_rarity():
    result = resolve_accessory_bonuses(
        {"base_id": "ring", "rarity_tier": 7},
        {"material": {"tier_mult": 7}, "implicit_bonuses": {}},
    )
    assert result == {"mental_resistance": 0.024}


@pytest.mark.unit
@pytest.mark.parametrize("tier", [float("nan"), float("inf"), -float("inf"), 1.5, "invalid"])
def test_saved_nonfinite_or_noninteger_tier_is_rejected(tier):
    with pytest.raises(ValueError):
        resolve_accessory_bonuses({"base_id": "ring"}, {"material": {"tier": tier}})


@pytest.mark.unit
@pytest.mark.parametrize("tier,expected", [(-1, 0.024), (8, 0.727)])
def test_saved_integer_tier_is_bounded_to_supported_catalog(tier, expected):
    assert resolve_accessory_bonuses({"base_id": "ring"}, {"material": {"tier": tier}}) == {
        "mental_resistance": expected
    }


@pytest.mark.unit
@pytest.mark.parametrize("base_id,key", [
    ("gloves", "environment_bio_resistance"),
    ("boots", "environment_gravity_resistance"),
    ("cloak", "environment_cold_resistance"),
    ("amulet", "debuff_avoidance"),
])
def test_retired_innates_removed_from_generation_and_saved_projection(base_id, key):
    factory = ItemFactory()
    base = factory.catalog.get_base_item(base_id)
    assert key not in base.implicit_bonuses
    for category in base.allowed_materials:
        for tier in range(8):
            material = factory.catalog.get_material_for_tier(category, tier)
            item = factory.generate(ItemGenerationRequestDTO(base_id=base_id, material_id=material.id, rarity_tier=0))
            assert key not in item.implicit_bonuses
            item.implicit_bonuses[key] = 9
            item.mechanics["implicit_bonuses"][key] = 9
            item.mechanics["affixes"] = [{"affix_id": key, "value": 0.25}]
            original = item.model_dump(mode="json")
            projected = ItemFactory.project_runtime_item(item)
            assert key not in projected.combat.implicit_bonuses
            assert projected.generation.affixes == item.mechanics["affixes"]
            mechanics = item.mechanics
            mechanics["implicit_bonuses"]["unowned"] = 0.1234
            snapshot = copy.deepcopy(mechanics)
            resolved = resolve_accessory_bonuses({"base_id": base_id, "item_tier": tier}, mechanics)
            assert key not in resolved
            assert resolved["unowned"] == 0.1234
            assert resolve_accessory_bonuses({"base_id": base_id, "item_tier": tier}, {**mechanics, "implicit_bonuses": resolved}) == resolved
            assert mechanics == snapshot
            assert original["mechanics"]["implicit_bonuses"][key] == 9


@pytest.mark.unit
def test_gloves_crit_curve_reaches_independent_twenty_percent_bonus():
    factory = ItemFactory()
    for category in ("cloths", "leathers"):
        for tier in range(8):
            material = factory.catalog.get_material_for_tier(category, tier)
            item = factory.generate(ItemGenerationRequestDTO(base_id="gloves", material_id=material.id, rarity_tier=0))
            expected = round(0.008 * (0.20 / 0.008) ** (tier / 7), 3)
            assert item.implicit_bonuses["physical_crit_chance"] == pytest.approx(expected)
            saved = {"base_id": "gloves", "item_tier": tier}
            mechanics = {"implicit_bonuses": {"physical_crit_chance": 0.001}, "affixes": []}
            original = copy.deepcopy(mechanics)
            projected = resolve_accessory_bonuses(saved, mechanics)
            assert projected["physical_crit_chance"] == pytest.approx(expected)
            assert resolve_accessory_bonuses(saved, {**mechanics, "implicit_bonuses": projected}) == projected
            assert mechanics == original
