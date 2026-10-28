import copy

import pytest

from src.backend.core.calculators.stats_waterfall_calculator import StatsWaterfallCalculator
from src.backend.features.character.runtime import CharacterCombatMathModelBuilder
from src.backend.features.character.runtime.vitals import CharacterVitalsCalculator
from src.backend.features.character.schemas.session import CharacterSessionAttributesDTO
from src.backend.features.inventory.services.projection import belt_capacity, belt_inventory_cell_bonus
from src.backend.features.items.dto.instance import ItemGenerationRequestDTO
from src.backend.features.items.resources.support_progression import support_bonus_at_tier
from src.backend.features.items.runtime.accessory_bonuses import resolve_accessory_bonuses
from src.backend.features.items.runtime.item_factory import ItemFactory
from src.shared.schemas.inventory import InventoryRuntimeSessionDTO


@pytest.mark.unit
@pytest.mark.parametrize("base_id,category,key,attribute", [
    ("gloves", "leathers", "anti_dodge_chance", "perception"),
    ("gloves", "cloths", "anti_dodge_chance", "perception"),
    ("ring", "ingots", "mental_resistance", "mental"),
    ("earring", "ingots", "initiative", "agility"),
])
def test_t7_rebalanced_base_matches_full_attribute_twenty(base_id, category, key, attribute):
    factory = ItemFactory()
    attributes = {name: 20 for name in CharacterSessionAttributesDTO.model_fields}
    baseline_raw = CharacterCombatMathModelBuilder().build_raw(attributes=attributes, skills={})
    baseline, _ = StatsWaterfallCalculator.calculate_waterfall(baseline_raw)
    targets = []
    for attribute_value in (0, 20):
        target_raw = CharacterCombatMathModelBuilder().build_raw(
            attributes={**attributes, attribute: attribute_value}, skills={}
        )
        target, _ = StatsWaterfallCalculator.calculate_waterfall(target_raw)
        targets.append(target[key] - baseline[key])
    material = factory.catalog.get_material_for_tier(category, 7)
    item = factory.generate(ItemGenerationRequestDTO(base_id=base_id, material_id=material.id, rarity_tier=0))
    equipped = item.model_dump(mode="json")
    equipped.update(item_id="bonus", item_type=item.item_type)
    equipped["mechanics"]["power"] = item.power
    raw = CharacterCombatMathModelBuilder().build_raw(
        attributes=attributes, skills={},
        items={"layout": {"equipment": {item.slot: "bonus"}}, "by_id": {"bonus": equipped}},
    )
    values, _ = StatsWaterfallCalculator.calculate_waterfall(raw)
    delta = values[key] - baseline[key]
    assert delta == pytest.approx(round(targets[1] - targets[0], 1 if key == "initiative" else 3), abs=0.0001)
    assert delta == pytest.approx(item.implicit_bonuses[key], abs=0.0001)


@pytest.mark.unit
@pytest.mark.parametrize("base_id,category,key", [
    ("gloves", "leathers", "anti_dodge_chance"),
    ("gloves", "cloths", "anti_dodge_chance"),
    ("ring", "ingots", "mental_resistance"),
    ("earring", "ingots", "initiative"),
])
def test_rebalanced_bases_keep_positive_tier_curve_at_every_tier(base_id, category, key):
    factory = ItemFactory()
    previous = 0
    for tier in range(8):
        material = factory.catalog.get_material_for_tier(category, tier)
        assert material.tier == tier
        item = factory.generate(ItemGenerationRequestDTO(base_id=base_id, material_id=material.id, rarity_tier=0))
        assert item.implicit_bonuses[key] == pytest.approx(support_bonus_at_tier(base_id, key, tier))
        assert item.implicit_bonuses[key] >= previous
        assert item.implicit_bonuses[key] > 0
        assert item.mechanics["affixes"] == []
        previous = item.implicit_bonuses[key]


@pytest.mark.unit
@pytest.mark.parametrize(
    "base_id,expected",
    [
        ("belt", {"hp": 10.0, "quick_slot_capacity": 1.0}),
        ("boots", {"stamina": 10.0, "stamina_regen": 1.5}),
        ("gloves", {"anti_dodge_chance": 0.04, "physical_crit_chance": 0.01}),
        ("cloak", {"hp_regen": 0.5}),
    ],
)
def test_bonus_equipment_factory_to_actor(base_id, expected):
    factory = ItemFactory()
    item = factory.generate(ItemGenerationRequestDTO(base_id=base_id, rarity_tier=0))
    assert item.power == (2 if base_id == "belt" else 0)
    assert all(value > 0 for value in item.implicit_bonuses.values())
    for key, value in expected.items():
        assert item.mechanics["implicit_bonuses_base"][key] == value
    equipped = item.model_dump(mode="json")
    equipped.update(item_id="bonus", item_type=item.item_type)
    equipped["mechanics"]["power"] = item.power
    raw = CharacterCombatMathModelBuilder().build_raw(
        attributes={}, items={"layout": {"equipment": {item.slot: "bonus"}}, "by_id": {"bonus": equipped}}
    )
    baseline = CharacterCombatMathModelBuilder().build_raw(attributes={})
    aliases = {"physical_crit_chance": "crit_chance"}
    for key in expected:
        actor_key = aliases.get(key, key)
        if key != "quick_slot_capacity":
            assert actor_key in raw["modifiers"]
            assert raw["modifiers"][actor_key]["base"] - baseline["modifiers"][actor_key]["base"] == pytest.approx(
                item.implicit_bonuses[key]
            )
    assert raw["modifiers"]["armor"] == baseline["modifiers"]["armor"]
    assert raw["modifiers"]["crit_power"] == baseline["modifiers"]["crit_power"]
    attributes = CharacterSessionAttributesDTO(**{key: 20 for key in CharacterSessionAttributesDTO.model_fields})
    items = {"layout": {"equipment": {item.slot: "bonus"}}, "by_id": {"bonus": equipped}}
    vitals = CharacterVitalsCalculator.calculate_max_vitals(attributes, items=items)
    naked = CharacterVitalsCalculator.calculate_max_vitals(attributes)
    if base_id == "belt":
        assert vitals.hp.max - naked.hp.max == round(item.implicit_bonuses["hp"])
        session = InventoryRuntimeSessionDTO.model_validate({"char_id": 1, **items})
        assert belt_capacity(session) == item.implicit_bonuses["quick_slot_capacity"]
        assert belt_inventory_cell_bonus(session) == 2
    elif base_id == "boots":
        assert vitals.stamina.max - naked.stamina.max == round(item.implicit_bonuses["stamina"])
        assert vitals.stamina.regen - naked.stamina.regen == pytest.approx(item.implicit_bonuses["stamina_regen"])
    elif base_id == "cloak":
        assert vitals.hp.regen - naked.hp.regen == pytest.approx(item.implicit_bonuses["hp_regen"])
    combat_values, _ = StatsWaterfallCalculator.calculate_waterfall(raw)
    naked_values, _ = StatsWaterfallCalculator.calculate_waterfall(baseline)
    for resource in ("hp", "stamina"):
        if f"{resource}_regen" not in item.implicit_bonuses:
            continue
        for mode in ("combat", "outside"):
            key = f"{mode}_{resource}_regen"
            expected_regen = item.implicit_bonuses.get(f"{resource}_regen", 0)
            assert combat_values[key] - naked_values[key] == pytest.approx(expected_regen)


@pytest.mark.unit
@pytest.mark.parametrize("base_id,retired", [("ring", "hp_regen"), ("earring", "stamina_regen")])
def test_jewelry_retires_only_intrinsic_regeneration(base_id, retired):
    item = ItemFactory().generate(ItemGenerationRequestDTO(base_id=base_id, rarity_tier=0))
    assert retired not in item.implicit_bonuses
    mechanics = {"implicit_bonuses": {retired: 3, "control_resistance": 0.007}, "affixes": [{"value": 7}]}
    original = copy.deepcopy(mechanics)
    result = resolve_accessory_bonuses({"base_id": base_id}, mechanics)
    assert retired not in result
    assert result["control_resistance"] == 0.007
    key, value = ("mental_resistance", 0.024) if base_id == "ring" else ("initiative", 0.6)
    assert result[key] == value
    assert resolve_accessory_bonuses({"base_id": base_id}, {**mechanics, "implicit_bonuses": result}) == result
    assert mechanics == original


@pytest.mark.parametrize("base_id,changed,retired", [
    ("boots", {"stamina": 127.0, "stamina_regen": 10.9}, None),
    ("gloves", {"anti_dodge_chance": 1.091, "physical_crit_chance": 0.20}, None),
    ("cloak", {"hp_regen": 4.2}, "environment_heat_resistance"),
    ("ring", {"mental_resistance": 0.727}, "hp_regen"),
    ("earring", {"initiative": 18.2}, "stamina_regen"),
])
def test_saved_bonus_equipment_refresh_is_bounded_and_idempotent(base_id, changed, retired):
    mechanics = {
        "material": {"tier_mult": 2.0, "tier": 7},
        "implicit_bonuses": {
            "environment_bio_resistance": 3.5, "environment_heat_resistance": -4,
            "hp_regen": 1, "stamina_regen": 2, "mental_resistance": 0.007, "initiative": 0.5,
        },
        "affixes": [{"affix_id": "hp_regen_bonus", "value": 7}],
    }
    original = copy.deepcopy(mechanics)
    result = resolve_accessory_bonuses({"base_id": base_id}, mechanics)
    for key, value in changed.items():
        assert result[key] == value
    if retired:
        assert retired not in result
    if base_id == "gloves":
        assert "environment_bio_resistance" not in result
    else:
        assert result["environment_bio_resistance"] == 3.5
    assert resolve_accessory_bonuses({"base_id": base_id}, {**mechanics, "implicit_bonuses": result}) == result
    assert mechanics == original
