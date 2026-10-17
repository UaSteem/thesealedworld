"""Shared authored item mechanics, isolated bindings and useful goblin sets."""

import pytest

from src.backend.features.monsters.catalog import get_catalog
from src.backend.features.monsters.catalog.families.goblin_catalog.equipment.prepared_loader import (
    get_prepared_equipment,
)


def test_shared_items_are_reused_with_unique_bound_instances():
    first = get_prepared_equipment("goblin_sneak", 3)
    second = get_prepared_equipment("goblin_cutter", 3)
    left = next(i for i in first.items if i.slot == "off_hand")
    right = next(i for i in second.items if i.slot == "off_hand")
    assert (
        left.generation.source_context["equipment_catalog_id"]
        == right.generation.source_context["equipment_catalog_id"]
    )
    assert left.combat == right.combat
    assert left.item_id != right.item_id
    assert left.owner_key != right.owner_key


def test_every_goblin_tier_uses_shared_references_and_preserves_bases():
    forbidden = {
        "control_chance_bonus",
        "control_resistance_bonus",
        "thorns_damage_bonus",
        "heat_resistance_bonus",
        "bio_resistance_bonus",
        "en_bonus",
        "luck_bonus",
    }
    for member in get_catalog().members.values():
        if member.family_id != "goblin_tribe":
            continue
        for tier in range(6):
            gear = get_prepared_equipment(member.variant_id, tier)
            assert {i.slot: i.base_id for i in gear.items} == {
                slot: base for slot, base in member.fixed_loadout.items() if base
            }
            for item in gear.items:
                assert item.generation.source_context["equipment_catalog_id"]
                ids = {a["affix_id"] for a in item.generation.affixes}
                assert not ids & forbidden
                assert len(ids) <= 4
                if member.role in {"minion", "veteran"}:
                    assert "hp_regen_bonus" not in ids
                if item.slot == "off_hand" and item.item_type == "weapon":
                    assert "weapon_accuracy" not in ids
                    assert "off_hand_accuracy" in ids
                if item.slot == "quiver":
                    assert not ids


def test_reference_resolution_rejects_wrong_tier_and_mutation_does_not_leak():
    from src.backend.features.monsters.catalog.equipment_library import get_equipment_item

    gear = get_prepared_equipment("goblin_sneak", 2)
    item = gear.items[0]
    key = item.generation.source_context["equipment_catalog_id"]
    original = get_equipment_item(key)
    item.combat.power = -100
    assert get_equipment_item(key) == original
    with pytest.raises(LookupError):
        get_equipment_item("unknown-item")


def test_catalog_resolution_never_generates_items(monkeypatch):
    from src.backend.features.items.runtime.item_factory import ItemFactory

    def forbidden(*args, **kwargs):
        raise AssertionError("Prepared catalog must not generate items")

    monkeypatch.setattr(ItemFactory, "generate_runtime_item", forbidden)
    assert get_prepared_equipment("scrap_king", 5).items


def test_binding_checks_slot_and_tier_and_preserves_shared_definition():
    from src.backend.features.monsters.catalog.equipment_library import (
        EquipmentItemReferenceDTO,
        bind_equipment_item,
    )

    key = "knife.main_hand.precision.t2"
    with pytest.raises(ValueError, match="slot/tier"):
        bind_equipment_item(EquipmentItemReferenceDTO(slot="main_hand", item_id=key), owner_key="x", tier=3)
    with pytest.raises(ValueError, match="slot/tier"):
        bind_equipment_item(EquipmentItemReferenceDTO(slot="off_hand", item_id=key), owner_key="x", tier=2)


def test_profiles_have_positive_median_rolls_with_existing_tick_policy():
    from src.backend.features.monsters.catalog.equipment_library import get_equipment_item, list_equipment_items
    from src.backend.features.monsters.catalog.resources.item_affix_profiles import get_monster_affix_step_count

    for key in list_equipment_items():
        definition = get_equipment_item(key)
        for affix in definition.item.generation.affixes:
            assert float(affix["value"]) > 0
            assert affix["roll_quality"] == 0.5
            assert affix["roll"]["step_count"] == get_monster_affix_step_count(definition.tier)


def test_shared_items_keep_archery_and_native_quiver_data():
    from src.backend.features.monsters.inspection.services.catalog_view_service import CatalogMonsterViewService

    for variant in ("goblin_slinger", "goblin_bomber"):
        view = CatalogMonsterViewService().equipment(member_id=f"goblin_tribe.base.{variant}", tier=5)
        trace = view.stats_preview.technical["equipped_trace"]
        assert trace["loadout"]["layout"]["main_hand"] == "skill_archery"
        assert next(i for i in view.items if i.slot == "quiver").generation.affixes == []
        if variant == "goblin_bomber":
            assert trace["loadout"]["ammo_charges"]["main_hand"] > 0
            assert trace["loadout"]["ammo_effects"]["main_hand"]["effects"]
