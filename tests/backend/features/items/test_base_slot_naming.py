import pytest

from src.backend.features.items.dto.instance import ItemGenerationRequestDTO
from src.backend.features.items.runtime.item_factory import ItemFactory
from src.backend.features.items.services.catalog_service import ItemCatalogService

RENAMED_BASES = {
    "hood": ("light_hood", "Лёгкий капюшон"),
    "leather_armor": ("light_chest_armor", "Лёгкий нагрудник"),
    "soft_bracers": ("light_bracers", "Лёгкие наручи"),
    "scout_leggings": ("light_leg_armor", "Лёгкие поножи"),
    "leather_cap": ("medium_helmet", "Средний шлем"),
    "jerkin": ("medium_chest_armor", "Средний нагрудник"),
    "reinforced_gloves": ("medium_bracers", "Средние наручи"),
    "breeches": ("medium_leg_armor", "Средние поножи"),
    "helmet": ("heavy_helmet", "Тяжёлый шлем"),
    "plate_chest": ("heavy_chest_armor", "Тяжёлый нагрудник"),
    "gauntlets": ("heavy_bracers", "Тяжёлые наручи"),
    "greaves": ("heavy_leg_armor", "Тяжёлые поножи"),
    "travel_boots": ("boots", "Ботинки"),
    "work_gloves": ("gloves", "Перчатки"),
    "winter_cloak": ("cloak", "Плащ"),
    "quiver_training": ("quiver_standard", "Колчан со стрелами"),
}


@pytest.mark.unit
@pytest.mark.parametrize("old_id,new_id,name", [(old, *target) for old, target in RENAMED_BASES.items()])
def test_catalog_and_tier_zero_generation_use_structural_base_identity(old_id, new_id, name):
    catalog = ItemCatalogService.load_default()
    base = catalog.get_base_item(new_id)
    assert base is not None
    assert base.name_ru == name
    assert catalog.get_base_item(old_id) is None
    material = catalog.get_material_for_tier(base.allowed_materials[0], 0)
    request = ItemGenerationRequestDTO(base_id=new_id, material_id=material.id, rarity_tier=0)
    first = ItemFactory().generate(request)
    second = ItemFactory().generate(request)
    assert first.base_id == new_id
    assert first.name == second.name
    assert name.lower() in first.name.lower()
    assert first.description == second.description == base.narrative_description
    assert first.mechanics["affixes"] == []


@pytest.mark.unit
def test_armor_bracers_cover_forearms_and_are_distinct_from_garment_gloves():
    catalog = ItemCatalogService.load_default()
    for armor_class in ("light", "medium", "heavy"):
        bracers = catalog.get_base_item(f"{armor_class}_bracers")
        assert bracers is not None
        assert bracers.slot == "arms_armor"
        assert "предплеч" in bracers.narrative_description.lower()
        assert not {"hands", "gloves", "gauntlets"}.intersection(bracers.narrative_tags)
    gloves = catalog.get_base_item("gloves")
    assert gloves.slot == "gloves_garment"
