"""Explicit offline boundary for exported full inventory runtime documents.

No DB/Redis imports and no automatic live migration. Unknown fields survive.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.backend.features.inventory.services.equipment_rules import (
    ACTIVE_SLOTS,
    BOW_BASE_IDS,
    QUIVER_BASE_IDS,
    RETIRED_BASE_IDS,
    ensure_current_equipment_contract,
)
from src.shared.schemas.inventory import InventoryRuntimeSessionDTO

RETIRED_SLOTS = frozenset({"chest_garment", "legs_garment"})


def migrate_inventory_snapshot(source: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return a new document and review report; never mutate the input.

    Layout is the placement authority. Reject ambiguous ownership/references,
    preserve every item and quantity, and recover unreferenced carried items.
    """
    if not isinstance(source, dict) or "char_id" not in source or "layout" not in source or "by_id" not in source:
        raise ValueError("Expected a full inventory runtime snapshot with char_id/layout/by_id")
    InventoryRuntimeSessionDTO.model_validate(source)
    result = deepcopy(source)
    items = result["by_id"]
    layout = result["layout"]
    equipment = layout.setdefault("equipment", {})
    belt = layout.setdefault("belt", {})
    backpack = layout.setdefault("backpack", [])
    unknown_slots = set(equipment) - ACTIVE_SLOTS - RETIRED_SLOTS - {"quiver"}
    if unknown_slots:
        raise ValueError(f"Unsupported equipment slots: {sorted(unknown_slots)}")
    references = (
        [value for value in equipment.values() if value] + [value for value in belt.values() if value] + list(backpack)
    )
    if len(references) != len(set(references)):
        raise ValueError("Duplicate item references; resolve the saved layout before migration")
    if any(value not in items for value in references):
        raise ValueError("Dangling item references; migration refuses to hide missing items")
    for key, item in items.items():
        if key != item["item_id"]:
            raise ValueError("by_id key does not match item_id")
        if item.get("placement", "backpack") not in {"equipped", "belt", "backpack"}:
            raise ValueError("Snapshot includes non-carried storage; export full carried inventory only")
    changes = []

    def to_backpack(item_id: str, reason: str) -> None:
        for slot, value in equipment.items():
            if value == item_id:
                equipment[slot] = None
        for slot, value in belt.items():
            if value == item_id:
                belt[slot] = None
        if item_id not in backpack:
            backpack.append(item_id)
        items[item_id]["placement"] = "backpack"
        items[item_id]["slot"] = None
        changes.append({"item_id": item_id, "reason": reason, "placement": "backpack"})

    legacy_quiver = equipment.pop("quiver", None)
    for slot in RETIRED_SLOTS:
        item_id = equipment.pop(slot, None)
        if item_id:
            to_backpack(item_id, "retired_slot")
    for item_id, item in items.items():
        mechanics = item.setdefault("mechanics", {})
        base_id = item["base_id"]
        if base_id == "quiver_training":
            item["base_id"] = base_id = "quiver_standard"
        if base_id in QUIVER_BASE_IDS:
            if item.get("item_type") != "ammo":
                raise ValueError("Known quiver has unexpected type")
            item["valid_slots"] = ["off_hand"]
            mechanics["slot"] = "off_hand"
            if "valid_slots" in mechanics:
                mechanics["valid_slots"] = ["off_hand"]
        if base_id in BOW_BASE_IDS:
            item["valid_slots"] = ["two_hand"]
            mechanics["slot"] = "two_hand"
            if "valid_slots" in mechanics:
                mechanics["valid_slots"] = ["two_hand"]
        if base_id in RETIRED_BASE_IDS:
            item["valid_slots"] = []
            to_backpack(item_id, "retired_base")
    main_id = equipment.get("main_hand")
    if main_id and items[main_id]["base_id"] in BOW_BASE_IDS:
        if equipment.get("two_hand"):
            to_backpack(main_id, "bow_conflicts_with_two_hand")
        else:
            equipment["two_hand"] = main_id
            equipment["main_hand"] = None
    two_id = equipment.get("two_hand")
    bow_equipped = bool(two_id and items[two_id]["base_id"] in BOW_BASE_IDS)
    if legacy_quiver:
        if items[legacy_quiver]["base_id"] not in QUIVER_BASE_IDS:
            raise ValueError("Legacy quiver slot contains an unsupported item")
        if bow_equipped and not equipment.get("off_hand"):
            equipment["off_hand"] = legacy_quiver
        else:
            to_backpack(legacy_quiver, "legacy_quiver_conflict_or_no_bow")
    if two_id:
        main_id = equipment.get("main_hand")
        if main_id:
            to_backpack(main_id, "two_hand_conflict")
        off_id = equipment.get("off_hand")
        if off_id and not (bow_equipped and items[off_id]["base_id"] in QUIVER_BASE_IDS):
            to_backpack(off_id, "two_hand_conflict")
    off_id = equipment.get("off_hand")
    if off_id and items[off_id]["base_id"] in QUIVER_BASE_IDS and not bow_equipped:
        to_backpack(off_id, "quiver_requires_bow")
    for slot, item_id in equipment.items():
        if item_id:
            items[item_id]["placement"] = "equipped"
            items[item_id]["slot"] = slot
    for slot, item_id in belt.items():
        if item_id:
            items[item_id]["placement"] = "belt"
            items[item_id]["slot"] = slot
    referenced = {value for value in equipment.values() if value} | {value for value in belt.values() if value}
    for item_id in items:
        if item_id not in referenced:
            to_backpack(item_id, "backpack_or_unreferenced")
    # Canonical backpack order is stable and all equipment keys are current.
    layout["backpack"] = list(dict.fromkeys(backpack))
    parsed = InventoryRuntimeSessionDTO.model_validate(result)
    ensure_current_equipment_contract(parsed)
    if set(items) != set(source["by_id"]) or any(
        item.get("quantity", 1) != source["by_id"][key].get("quantity", 1) for key, item in items.items()
    ):
        raise AssertionError("Inventory conservation failed")
    return result, {
        "char_id": source["char_id"],
        "changed": result != source,
        "item_count": len(items),
        "changes": changes,
        "scope": "offline full inventory snapshot only; no SQL/Redis writes",
    }
