from __future__ import annotations

import pytest

from src.backend.features.inventory.services.inventory_service import InventoryActionError, InventoryService
from src.backend.features.inventory.services.projection import build_runtime_session
from src.backend.features.inventory.services.view import InventoryViewService
from src.backend.features.items.services.catalog_service import ItemCatalogService
from src.shared.enums.item_enums import EquippedSlot
from src.shared.schemas.inventory import InventoryRuntimeItemDTO


def item(item_id, base, kind, slot):
    return InventoryRuntimeItemDTO(
        item_id=item_id,
        base_id=base,
        item_type=kind,
        name=base,
        valid_slots=[slot],
        mechanics={"slot": slot, "related_skill": "skill_archery" if base == "shortbow" else "skill_swords"},
    )


def service():
    return InventoryService.__new__(InventoryService)


def test_removed_slots_and_ordinary_clothing_are_not_active():
    assert not {"chest_garment", "legs_garment", "quiver"} & {s.value for s in EquippedSlot}
    catalog = ItemCatalogService.load_default()
    assert not {"apron", "shirt", "tunic", "pants"} & catalog.base_items.keys()
    assert catalog.get_base_item("medium_leg_armor").type == "armor"
    assert catalog.get_base_item("gloves").base_power == 0
    assert catalog.get_base_item("shortbow").slot == "two_hand"
    assert catalog.get_base_item("quiver_fire").slot == "off_hand"


def test_bow_quiver_weapon_changes_and_no_item_loss():
    bow = item("bow", "shortbow", "weapon", "two_hand")
    quiver = item("ammo", "quiver_fire", "ammo", "off_hand")
    sword = item("sword", "greatsword", "weapon", "two_hand")
    shield = item("shield", "round_shield", "shield", "off_hand")
    session = build_runtime_session(1, [bow, quiver, sword, shield])
    svc = service()
    with pytest.raises(InventoryActionError):
        svc._equip(session, "ammo", "off_hand")
    svc._equip(session, "bow", "two_hand")
    svc._equip(session, "ammo", "off_hand")
    assert session.layout.equipment["two_hand"] == "bow"
    svc._equip(session, "sword", "two_hand")
    assert session.by_id["ammo"].placement == "backpack"
    assert set(session.layout.backpack) == {"bow", "ammo", "shield"}
    svc._equip(session, "bow", "two_hand")
    svc._equip(session, "ammo", "off_hand")
    svc._unequip(session, "bow")
    assert session.by_id["ammo"].placement == "backpack"
    svc._equip(session, "bow", "two_hand")
    svc._equip(session, "shield", "off_hand")
    assert not session.layout.equipment.get("two_hand")
    assert set(session.by_id) == {"bow", "ammo", "sword", "shield"}


def test_inventory_has_fourteen_positions_and_quiver_in_second_hand():
    session = build_runtime_session(1, [])
    view = InventoryViewService()
    window = view.build_window(session, can_act=True)
    slots = [z.primary_slot for z in window.body_zones]
    slots += [z.secondary_slot for z in window.body_zones if z.secondary_slot]
    slots += window.weapon_slots
    slots += [s for row in window.accessory_rows for s in row.slots]
    assert len(slots) == 14
    assert {s.slot_id for s in slots} == {s.value for s in EquippedSlot if s.value != "two_hand"}
    assert all(
        s.layer == "accessory" for s in slots if s.slot_id in {"gloves_garment", "outer_garment", "belt_accessory"}
    )
    bow = item("bow", "shortbow", "weapon", "two_hand")
    quiver = item("ammo", "quiver_fire", "ammo", "off_hand")
    session = build_runtime_session(1, [bow, quiver])
    service()._equip(session, "bow", "two_hand")
    service()._equip(session, "ammo", "off_hand")
    slots = view.build_window(session, can_act=True).weapon_slots
    assert [s.slot_id for s in slots] == ["two_hand", "off_hand"]
    assert slots[1].item.item_id == "ammo"


def test_bow_to_bow_preserves_quiver_and_two_hand_rejects_shield():
    from copy import deepcopy

    bow = item("bow", "shortbow", "weapon", "two_hand")
    other = item("other", "longbow", "weapon", "two_hand")
    ammo = item("ammo", "quiver_standard", "ammo", "off_hand")
    session = build_runtime_session(1, [bow, other, ammo])
    svc = service()
    svc._equip(session, "bow", "two_hand")
    svc._equip(session, "ammo", "off_hand")
    svc._equip(session, "other", "two_hand")
    assert session.layout.equipment == {"two_hand": "other", "off_hand": "ammo", "main_hand": None}
    assert session.by_id["bow"].placement == "backpack"
    before = deepcopy(session)
    with pytest.raises(InventoryActionError):
        svc._equip(session, "ammo", "main_hand")
    assert session == before


def test_retired_instances_cannot_be_equipped_even_with_forged_placement():
    retired = item("old", "pants", "garment", "legs_armor")
    session = build_runtime_session(1, [retired])
    with pytest.raises(InventoryActionError):
        service()._equip(session, "old", "legs_armor")


def test_quiver_is_ammunition_in_combat_not_an_offhand_attack():
    from src.backend.features.character.runtime.combat_actor_input import CharacterCombatActorInputBuilder
    from src.backend.features.character.runtime.combat_math_model import CharacterCombatMathModelBuilder

    bow = item("bow", "shortbow", "weapon", "two_hand")
    bow.mechanics.update(power=10, damage_spread=0.14)
    ammo = item("ammo", "quiver_fire", "ammo", "off_hand")
    ammo.mechanics.update(
        power=3,
        damage_spread=0,
        related_skill="skill_archery",
        ammo_charge_base=12,
        ammo_effect_payload={"effects": [{"id": "burn", "params": {"power": 1}}]},
    )
    session = build_runtime_session(1, [bow, ammo])
    service()._equip(session, "bow", "two_hand")
    service()._equip(session, "ammo", "off_hand")
    data = session.model_dump(mode="json")
    loadout = CharacterCombatActorInputBuilder._loadout(data, {})
    assert loadout["hand_usage"] == {"main_hand": "two_hand"}
    assert "off_hand" not in loadout["layout"]
    assert "off_hand" not in loadout["weapon_slots"]
    assert loadout["ammo_charges"] == {"main_hand": 12}
    assert loadout["ammo_effects"]["main_hand"]["effects"][0]["params"]["power"] == 3
    with_ammo = CharacterCombatMathModelBuilder().build_raw(items=data, attributes={})
    service()._unequip(session, "ammo")
    without_ammo = CharacterCombatMathModelBuilder().build_raw(items=session.model_dump(mode="json"), attributes={})
    assert with_ammo == without_ammo


@pytest.mark.asyncio
async def test_dropping_bow_preserves_its_quiver_in_backpack():
    from unittest.mock import AsyncMock

    bow = item("bow", "shortbow", "weapon", "two_hand")
    ammo = item("ammo", "quiver_standard", "ammo", "off_hand")
    session = build_runtime_session(1, [bow, ammo])
    svc = service()
    svc._equip(session, "bow", "two_hand")
    svc._equip(session, "ammo", "off_hand")
    svc._active_run_id = AsyncMock(return_value=None)
    svc.repository = AsyncMock()
    svc.repository.discard_character_item.return_value = True
    await svc._drop(session, "bow")
    assert set(session.by_id) == {"ammo"}
    assert session.layout.backpack == ["ammo"]
    assert session.by_id["ammo"].placement == "backpack"
    from src.backend.features.inventory.services.equipment_rules import ensure_current_equipment_contract

    ensure_current_equipment_contract(session)
