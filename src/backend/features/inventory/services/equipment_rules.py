from __future__ import annotations

from typing import TYPE_CHECKING

from src.shared.enums.item_enums import EquippedSlot

if TYPE_CHECKING:
    from src.shared.schemas.inventory import InventoryRuntimeItemDTO, InventoryRuntimeSessionDTO

RETIRED_BASE_IDS = frozenset({"apron", "shirt", "tunic", "pants", "linen_shirt", "wool_tunic", "fur_pants"})
BOW_BASE_IDS = frozenset({"shortbow", "longbow", "composite_bow"})
QUIVER_BASE_IDS = frozenset(
    {"quiver_standard", "quiver_fire", "quiver_poison", "quiver_broadhead", "quiver_frost", "quiver_bodkin"}
)
ACTIVE_SLOTS = frozenset(slot.value for slot in EquippedSlot)


def is_bow(item: InventoryRuntimeItemDTO | None) -> bool:
    return bool(item and item.item_type == "weapon" and item.base_id in BOW_BASE_IDS)


def is_quiver(item: InventoryRuntimeItemDTO | None) -> bool:
    return bool(item and item.item_type == "ammo" and item.base_id in QUIVER_BASE_IDS)


def equipped_bow(session: InventoryRuntimeSessionDTO) -> bool:
    return is_bow(session.by_id.get(session.layout.equipment.get("two_hand") or ""))


def compatible_with_slot(item: InventoryRuntimeItemDTO, slot_id: str) -> bool:
    if slot_id not in ACTIVE_SLOTS or item.base_id in RETIRED_BASE_IDS:
        return False
    if item.item_type == "ammo" and not is_quiver(item):
        return False
    if is_bow(item) and slot_id != "two_hand":
        return False
    if is_quiver(item):
        return slot_id == "off_hand" and slot_id in item.valid_slots
    # Placement is not an authority for compatibility: a stale saved placement
    # must never turn an item into a weapon or make retired gear equippable.
    return slot_id in item.valid_slots or (not item.valid_slots and item.mechanics.get("slot") == slot_id)


def can_equip(session: InventoryRuntimeSessionDTO, item: InventoryRuntimeItemDTO, slot_id: str) -> bool:
    return compatible_with_slot(item, slot_id) and (not is_quiver(item) or equipped_bow(session))


class EquipmentMigrationRequiredError(ValueError):
    """A saved document must be migrated explicitly before gameplay writes."""


def ensure_current_equipment_contract(session: InventoryRuntimeSessionDTO) -> None:
    if any(slot not in ACTIVE_SLOTS for slot in session.layout.equipment):
        raise EquipmentMigrationRequiredError("Saved equipment layout requires equipment-slots migration")
    for item in session.by_id.values():
        if is_quiver(item) and (item.valid_slots != ["off_hand"] or item.mechanics.get("slot") != "off_hand"):
            raise EquipmentMigrationRequiredError("Saved quiver mechanics require equipment-slots migration")
        if item.placement == "equipped" and (item.slot not in ACTIVE_SLOTS or item.base_id in RETIRED_BASE_IDS):
            raise EquipmentMigrationRequiredError("Saved item placement requires equipment-slots migration")
    two_id = session.layout.equipment.get("two_hand")
    off_id = session.layout.equipment.get("off_hand")
    if two_id and (
        session.layout.equipment.get("main_hand")
        or (off_id and not (is_bow(session.by_id.get(two_id)) and is_quiver(session.by_id.get(off_id))))
    ):
        raise EquipmentMigrationRequiredError("Saved two-hand layout requires equipment-slots migration")
    if off_id and is_quiver(session.by_id.get(off_id)) and not equipped_bow(session):
        raise EquipmentMigrationRequiredError("Saved quiver needs an equipped bow")
    for slot, item_id in session.layout.equipment.items():
        if item_id and (item_id not in session.by_id or not compatible_with_slot(session.by_id[item_id], slot)):
            raise EquipmentMigrationRequiredError("Saved equipped item is incompatible with its slot")
