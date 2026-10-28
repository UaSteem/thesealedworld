from __future__ import annotations

from src.backend.features.inventory.services.equipment_rules import (
    EquipmentMigrationRequiredError,
    ensure_current_equipment_contract,
)
from src.backend.features.inventory.services.equipment_rules import (
    compatible_with_slot as compatible_with_slot,
)
from src.backend.features.items.runtime.item_factory import ItemFactory
from src.shared.enums.item_enums import EquippedSlot, ItemType
from src.shared.schemas.inventory import (
    ActiveCharacterItemsProjectionDTO,
    InventoryLayoutDTO,
    InventoryRuntimeItemDTO,
    InventoryRuntimeSessionDTO,
)

EQUIPMENT_STORAGE = "equipped"
BELT_STORAGE = "belt"
BACKPACK_STORAGE = "backpack"


def build_runtime_session(
    char_id: int,
    items: list[InventoryRuntimeItemDTO],
    *,
    risk_run_id: str | None = None,
) -> InventoryRuntimeSessionDTO:
    layout = InventoryLayoutDTO()
    by_id: dict[str, InventoryRuntimeItemDTO] = {}

    for item in items:
        if item.item_id in by_id:
            raise EquipmentMigrationRequiredError("Duplicate saved item identity")
        by_id[item.item_id] = item
        if item.placement == EQUIPMENT_STORAGE and item.slot:
            if layout.equipment.get(item.slot):
                raise EquipmentMigrationRequiredError("Multiple saved items occupy one equipment slot")
            layout.equipment[item.slot] = item.item_id
        elif item.placement == BELT_STORAGE and item.slot:
            layout.belt[item.slot] = item.item_id
        elif item.placement == BACKPACK_STORAGE:
            layout.backpack.append(item.item_id)

    session = InventoryRuntimeSessionDTO(char_id=char_id, layout=layout, by_id=by_id, risk_run_id=risk_run_id)
    ensure_current_equipment_contract(session)
    return session


def build_active_character_projection(session: InventoryRuntimeSessionDTO) -> ActiveCharacterItemsProjectionDTO:
    ensure_current_equipment_contract(session)
    active_ids = {item_id for item_id in [*session.layout.equipment.values(), *session.layout.belt.values()] if item_id}
    layout = InventoryLayoutDTO(
        equipment=session.layout.equipment,
        belt=session.layout.belt,
        backpack=[],
    )
    by_id = {item_id: item for item_id, item in session.by_id.items() if item_id in active_ids}
    for item in by_id.values():
        mechanics = dict(item.mechanics or {})
        bonuses = dict(mechanics.get("bonuses") or {})
        affixes = mechanics.get("affixes")
        if not bonuses and isinstance(affixes, list):
            item.mechanics["bonuses"] = bonuses = ItemFactory._compile_affix_bonuses(affixes)
    return ActiveCharacterItemsProjectionDTO(layout=layout, by_id=by_id)


def belt_capacity(session: InventoryRuntimeSessionDTO) -> int:
    belt_id = session.layout.equipment.get(EquippedSlot.BELT_ACCESSORY.value)
    if not belt_id:
        return 0
    belt = session.by_id.get(belt_id)
    if belt is None:
        return 0
    bonuses = belt.mechanics.get("implicit_bonuses") or {}
    raw = bonuses.get("quick_slot_capacity") or belt.mechanics.get("quick_slot_capacity") or 0
    try:
        return max(0, min(8, int(float(raw))))
    except (TypeError, ValueError):
        return 0


def inventory_cell_capacity(session: InventoryRuntimeSessionDTO, *, strength: int = 0) -> int:
    return max(0, 30 + int(strength or 0) + belt_inventory_cell_bonus(session))


def belt_inventory_cell_bonus(session: InventoryRuntimeSessionDTO) -> int:
    belt_id = session.layout.equipment.get(EquippedSlot.BELT_ACCESSORY.value)
    if not belt_id:
        return 0
    belt = session.by_id.get(belt_id)
    if belt is None:
        return 0

    bonuses = belt.mechanics.get("implicit_bonuses") or {}
    raw = (
        belt.mechanics.get("power")
        or bonuses.get("inventory_cell_capacity")
        or bonuses.get("inventory_slot_capacity")
        or bonuses.get("inventory_slots")
        or belt.mechanics.get("inventory_cell_capacity")
        or belt.mechanics.get("inventory_slot_capacity")
        or belt.mechanics.get("inventory_slots")
    )
    if raw is None:
        return 4
    try:
        return max(0, int(float(raw)))
    except (TypeError, ValueError):
        return 4


def is_quick_slot_compatible(item: InventoryRuntimeItemDTO) -> bool:
    if item.item_type != ItemType.CONSUMABLE.value:
        return False
    return bool(item.mechanics.get("is_quick_slot_compatible"))
