"""Material describes/scales an item; the item base owns affix eligibility."""

import pytest

from src.backend.features.items.dto.instance import ItemGenerationRequestDTO, ItemOriginRefDTO
from src.backend.features.items.runtime.item_factory import ItemFactory


@pytest.mark.unit
@pytest.mark.parametrize("mode", ["player", "runtime"])
@pytest.mark.parametrize("material_id", ["mat_iron_ingot", "mat_mithril_ingot"])
def test_material_weight_tags_do_not_remove_ring_attribute_affixes(mode, material_id):
    factory = ItemFactory()
    request = ItemGenerationRequestDTO(
        base_id="ring",
        target_slot="ring_1",
        material_id=material_id,
        rarity_tier=3,
        forced_affix_ids=["attribute_agility"],
        allowed_affix_ids=["attribute_agility"],
        affix_count=1,
        origin_ref=ItemOriginRefDTO(seed="material-independent-ring"),
    )
    item = getattr(factory, f"generate_{mode}_item")(request)

    assert [a["affix_id"] for a in item.mechanics["affixes"]] == ["attribute_agility"]
    assert set(factory.catalog.get_material(material_id).narrative_tags) <= set(item.narrative_tags)


@pytest.mark.unit
def test_runtime_extra_narrative_tags_do_not_change_affix_selection():
    factory = ItemFactory()
    request = ItemGenerationRequestDTO(
        base_id="ring",
        target_slot="ring_1",
        material_id="mat_cobalt_ingot",
        rarity_tier=3,
        forced_affix_ids=["attribute_agility"],
        allowed_affix_ids=["attribute_agility"],
        affix_count=1,
        origin_ref=ItemOriginRefDTO(seed="narrative-independent-ring"),
    )
    plain = factory.generate_runtime_item(request)
    described = factory.generate_runtime_item(request.model_copy(update={"extra_narrative_tags": ["heavy"]}))

    assert plain.mechanics["affixes"] == described.mechanics["affixes"]
    assert "heavy" in described.narrative_tags


@pytest.mark.unit
@pytest.mark.parametrize("mode", ["player", "runtime"])
def test_material_still_scales_weapon_and_same_affix(mode):
    factory = ItemFactory()
    request = ItemGenerationRequestDTO(
        base_id="stiletto",
        target_slot="main_hand",
        rarity_tier=3,
        forced_affix_ids=["crit_chance"],
        allowed_affix_ids=["crit_chance"],
        affix_count=1,
        origin_ref=ItemOriginRefDTO(seed="material-independent-weapon"),
    )
    generate = getattr(factory, f"generate_{mode}_item")
    low = generate(request.model_copy(update={"material_id": "mat_iron_ingot"}))
    high = generate(request.model_copy(update={"material_id": "mat_mithril_ingot"}))
    assert [a["affix_id"] for a in low.mechanics["affixes"]] == ["crit_chance"]
    assert [a["affix_id"] for a in high.mechanics["affixes"]] == ["crit_chance"]
    ratio = factory.catalog.get_material("mat_mithril_ingot").tier_mult
    ratio /= factory.catalog.get_material("mat_iron_ingot").tier_mult
    assert high.power == pytest.approx(low.power * ratio, abs=0.01)
    assert high.durability_max == pytest.approx(low.durability_max * ratio, abs=0.01)
    assert high.mechanics["affixes"][0]["value"] == pytest.approx(
        low.mechanics["affixes"][0]["value"] * ratio, abs=0.0002
    )
