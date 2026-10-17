"""Saved natural equipment uses ItemService projections without persistence."""

import pytest

from src.backend.features.monsters.catalog.families.wolf_catalog.family import WOLF_FAMILY
from src.backend.features.monsters.catalog.nested_contracts import resolve_family
from src.backend.features.monsters.catalog.prepared_equipment import get_prepared_equipment, list_prepared_equipment
from src.backend.features.monsters.catalog.resources.equipment_mapping import get_natural_equipment_mapping


def test_all_wolf_sets_preserve_roles_slots_tiers_and_natural_texts():
    refs = list_prepared_equipment(family_id="wolf_pack")
    assert len(refs) == len(set(refs)) == 66
    members = {member.variant_id: member for member in resolve_family(WOLF_FAMILY)[2]}
    count = 0
    for variant, tier in refs:
        member = members[variant]
        equipment = get_prepared_equipment(family_id="wolf_pack", variant_id=variant, tier=tier)
        assert equipment.family_id == "wolf_pack"
        assert equipment.role == member.role
        assert equipment.equipment_set_id == f"wolf_pack.{member.base_id}"
        assert member.min_tier <= tier <= member.max_tier
        assert set(equipment.to_items_projection().layout.equipment) == {
            slot for slot, key in member.fixed_loadout.items() if key
        }
        assert len(equipment.items) == 4
        for item in equipment.items:
            mapping = get_natural_equipment_mapping(member.fixed_loadout[item.slot])
            assert item.base_id == mapping.base_id
            assert item.generation.natural_key == mapping.natural_key
            assert set(mapping.tags).issubset(item.combat.tags)
            assert mapping.name_ru and mapping.description_ru
            assert item.generation.rarity_tier == tier
            assert item.owner_key == f"{member.id}:tier:{tier}"
        count += len(equipment.items)
    assert count == 264


def test_saved_wolf_load_returns_independent_objects():
    args = dict(family_id="wolf_pack", variant_id="cub", tier=0)
    first, second = get_prepared_equipment(**args), get_prepared_equipment(**args)
    assert first == second
    assert first.items[0] is not second.items[0]


@pytest.mark.parametrize(
    "family,variant,tier,error",
    [
        ("missing", "cub", 0, LookupError),
        ("wolf_pack", "cub", 6, LookupError),
        ("wolf_pack", "../unsafe", 0, ValueError),
        ("wolf_pack", "cub", True, ValueError),
    ],
)
def test_invalid_saved_equipment_is_rejected(family, variant, tier, error):
    with pytest.raises(error):
        get_prepared_equipment(family_id=family, variant_id=variant, tier=tier)


def test_manifest_records_natural_itemservice_inputs():
    import json
    from pathlib import Path

    from tools.monsters.prepare_wolf_equipment import DEFAULT_OUTPUT, validate

    manifest = json.loads((DEFAULT_OUTPUT / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["inputs"]) == 66
    for entry in manifest["inputs"]:
        for request in entry["requests"]:
            mapping = get_natural_equipment_mapping(request["runtime_metadata"]["natural_key"])
            assert request["presentation_name_ru"] == mapping.name_ru
            assert request["presentation_description"] == mapping.description_ru
            assert request["generation_mode"] == "runtime"
    assert validate(Path(DEFAULT_OUTPUT)) == {"sets": 66, "items": 264}


def test_loader_never_calls_itemservice(monkeypatch):
    from src.backend.features.items.services.generation_service import ItemGenerationService

    def forbidden(*args, **kwargs):
        raise AssertionError("Saved equipment must not generate items")

    monkeypatch.setattr(ItemGenerationService, "__init__", forbidden)
    assert len(get_prepared_equipment(family_id="wolf_pack", variant_id="cub", tier=5).items) == 4


def test_facade_rejects_cross_family_equipment(monkeypatch):
    from src.backend.features.monsters.catalog import prepared_equipment

    wolf = get_prepared_equipment(family_id="wolf_pack", variant_id="cub", tier=0)

    class WrongLoader:
        def get_prepared_equipment(self, variant_id, tier):
            return wolf

    monkeypatch.setattr(prepared_equipment, "_loader", lambda family_id: WrongLoader())
    with pytest.raises(ValueError, match="different family"):
        get_prepared_equipment(family_id="goblin_tribe", variant_id="cub", tier=0)


def test_writer_rejects_existing_directory_before_any_generation():
    from tools.monsters.prepare_wolf_equipment import DEFAULT_OUTPUT, write_prepared

    coroutine = write_prepared(DEFAULT_OUTPUT)
    try:
        with pytest.raises(FileExistsError, match="Refusing to overwrite"):
            coroutine.send(None)
    finally:
        coroutine.close()
