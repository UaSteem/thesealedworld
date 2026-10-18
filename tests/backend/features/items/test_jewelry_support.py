import copy

import pytest

from src.backend.features.items.dto.instance import ItemGenerationRequestDTO
from src.backend.features.items.runtime.accessory_bonuses import resolve_accessory_bonuses
from src.backend.features.items.runtime.item_factory import ItemFactory


@pytest.mark.unit
@pytest.mark.parametrize(
    "base_id,key,value", [("ring", "hp_regen", 0.5), ("amulet", "en_regen", 1.0), ("earring", "stamina_regen", 1.0)]
)
@pytest.mark.parametrize("material_id", ["mat_iron_ingot", "mat_mithril_ingot"])
def test_jewelry_support_is_intrinsic_and_uses_material_scale(base_id, key, value, material_id):
    factory = ItemFactory()
    item = factory.generate(ItemGenerationRequestDTO(base_id=base_id, material_id=material_id, rarity_tier=0))
    scale = factory.catalog.get_material(material_id).tier_mult
    assert item.implicit_bonuses[key] == pytest.approx(value * scale)
    assert item.mechanics["implicit_bonuses_base"][key] == value
    assert item.mechanics["implicit_bonuses"][key] == pytest.approx(value * scale)
    assert item.mechanics["affixes"] == []


@pytest.mark.unit
def test_saved_jewelry_support_refresh_preserves_rolls_and_is_idempotent():
    item = {"base_id": "ring", "instance_id": "authored-ring"}
    mechanics = {
        "material": {"tier_mult": 2.0},
        "implicit_bonuses": {"mental_resistance": 0.007, "hp_regen": 0.1},
        "affixes": [{"affix_id": "hp_regen_bonus", "value": 7}],
    }
    original = copy.deepcopy(mechanics)
    projected = resolve_accessory_bonuses(item, mechanics)
    assert projected == {"mental_resistance": 0.007, "hp_regen": 1.0}
    assert resolve_accessory_bonuses(item, {**mechanics, "implicit_bonuses": projected}) == projected
    assert mechanics == original


@pytest.mark.unit
def test_saved_jewelry_support_uses_catalog_material_when_scale_not_embedded():
    item = {"base_id": "amulet", "metadata": {"material_id": "mat_mithril_ingot"}}
    projected = resolve_accessory_bonuses(item, {"implicit_bonuses": {"debuff_avoidance": 0.019}})
    scale = ItemFactory().catalog.get_material("mat_mithril_ingot").tier_mult
    assert projected == {"debuff_avoidance": 0.019, "en_regen": scale}


@pytest.mark.unit
def test_non_jewelry_support_is_unchanged():
    assert resolve_accessory_bonuses({"base_id": "winter_cloak"}, {"implicit_bonuses": {"stamina_regen": 2}}) == {
        "stamina_regen": 2
    }


def test_saved_belt_gains_scaled_hp_without_losing_quick_slots_or_stacking():
    item = {"base_id": "belt"}
    mechanics = {"material": {"tier_mult": 0.8}, "implicit_bonuses": {"quick_slot_capacity": 1.0}}
    result = resolve_accessory_bonuses(item, mechanics)
    assert result == {"quick_slot_capacity": 1.0, "hp": 8.0}
    assert resolve_accessory_bonuses(item, {**mechanics, "implicit_bonuses": result}) == result
    generated = ItemFactory().generate(ItemGenerationRequestDTO(base_id="belt", rarity_tier=0))
    assert generated.mechanics["implicit_bonuses_base"]["hp"] == 10.0
    assert generated.implicit_bonuses["hp"] > 0
    assert generated.implicit_bonuses["quick_slot_capacity"] == 1.0


@pytest.mark.unit
def test_runtime_projection_refreshes_saved_support_without_rerolling_affixes():
    item = ItemFactory().generate(
        ItemGenerationRequestDTO(base_id="ring", material_id="mat_iron_ingot", item_grade="uncommon")
    )
    outdated = item.model_copy(deep=True)
    outdated.implicit_bonuses.pop("hp_regen")
    outdated.mechanics["implicit_bonuses"].pop("hp_regen")
    projection = ItemFactory.project_runtime_item(outdated)
    assert projection.combat.implicit_bonuses["hp_regen"] == 0.5
    assert projection.generation.affixes == item.mechanics["affixes"]
    assert "hp_regen" not in outdated.mechanics["implicit_bonuses"]
