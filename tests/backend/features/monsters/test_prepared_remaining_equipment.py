"""Saved rat and bandit sets preserve authored loadouts and generation policy."""

from importlib import import_module

import pytest
from tools.monsters.prepare_family_equipment import FAMILIES, default_output, validate, write_prepared

from src.backend.features.monsters.catalog.nested_contracts import resolve_family
from src.backend.features.monsters.catalog.resources.equipment_mapping import get_natural_equipment_mapping


@pytest.mark.parametrize("family_id", tuple(FAMILIES))
def test_complete_prepared_equipment_matches_authored_members(family_id):
    family, package = FAMILIES[family_id]
    loader = import_module(f"src.backend.features.monsters.catalog.families.{package}.equipment.prepared_loader")
    members = {member.variant_id: member for member in resolve_family(family)[2]}
    refs = loader.list_prepared_equipment()
    expected = {
        (member.variant_id, tier) for member in members.values() for tier in range(member.min_tier, member.max_tier + 1)
    }
    assert len(refs) == len(expected)
    assert set(refs) == expected
    for variant, tier in refs:
        member = members[variant]
        saved = loader.get_prepared_equipment(variant, tier)
        assert saved.family_id == family_id
        assert saved.role == member.role
        assert set(saved.to_items_projection().layout.equipment) == {
            s for s, key in member.fixed_loadout.items() if key
        }
        for item in saved.items:
            key = member.fixed_loadout[item.slot]
            if family_id == "rat_swarm":
                mapping = get_natural_equipment_mapping(key)
                assert mapping.description_ru
                assert item.base_id == mapping.base_id
                assert item.generation.natural_key == key
                assert set(mapping.tags).issubset(item.combat.tags)
            else:
                assert item.base_id == key
                assert not item.generation.natural_key
            assert item.generation.rarity_tier == tier
            assert item.owner_key == f"{member.id}:tier:{tier}"
        copy = loader.get_prepared_equipment(variant, tier)
        assert saved == copy
        assert saved.items[0] is not copy.items[0]
    result = validate(default_output(family_id), family_id)
    assert result["sets"] == len(expected)


@pytest.mark.parametrize("family_id", tuple(FAMILIES))
def test_writer_refuses_existing_saved_equipment(family_id):
    coroutine = write_prepared(default_output(family_id), family_id)
    try:
        with pytest.raises(FileExistsError, match="Refusing to overwrite"):
            coroutine.send(None)
    finally:
        coroutine.close()


@pytest.mark.parametrize("family_id", tuple(FAMILIES))
def test_saved_loader_rejects_invalid_identity_and_does_not_generate(family_id, monkeypatch):
    from src.backend.features.items.services.generation_service import ItemGenerationService

    def forbidden(*args, **kwargs):
        raise AssertionError("Prepared catalog must not generate")

    monkeypatch.setattr(ItemGenerationService, "__init__", forbidden)
    package = FAMILIES[family_id][1]
    loader = import_module(f"src.backend.features.monsters.catalog.families.{package}.equipment.prepared_loader")
    variant, tier = loader.list_prepared_equipment()[0]
    assert loader.get_prepared_equipment(variant, tier).items
    with pytest.raises(ValueError):
        loader.get_prepared_equipment("../unsafe", tier)
    with pytest.raises(ValueError):
        loader.get_prepared_equipment(variant, True)
    with pytest.raises(LookupError):
        loader.get_prepared_equipment(variant, 7)
