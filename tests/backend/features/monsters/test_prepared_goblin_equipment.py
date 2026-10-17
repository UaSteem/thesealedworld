import pytest

from src.backend.features.monsters.catalog.families.goblin_catalog.equipment.prepared_loader import (
    get_prepared_equipment,
    list_prepared_equipment,
)


def test_all_prepared_sets_load_and_build_item_projections():
    references = list_prepared_equipment()
    assert len(references) == len(set(references)) == 72
    assert {tier for _, tier in references} == set(range(6))
    total = 0
    for variant, tier in references:
        equipment = get_prepared_equipment(variant, tier)
        projection = equipment.to_items_projection()
        assert len(projection.by_id) == len(equipment.items)
        assert all(item.generation.rarity_tier == tier for item in equipment.items)
        total += len(equipment.items)
    assert total == 282


def test_unknown_set_is_rejected():
    with pytest.raises(LookupError):
        get_prepared_equipment("goblin_sneak", 7)
    with pytest.raises(ValueError):
        get_prepared_equipment("../unsafe", 0)


def test_loading_returns_independent_item_objects():
    first = get_prepared_equipment("goblin_sneak", 0)
    second = get_prepared_equipment("goblin_sneak", 0)
    assert first == second
    assert first.items[0] is not second.items[0]
