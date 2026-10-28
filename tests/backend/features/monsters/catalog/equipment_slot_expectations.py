"""Reverse only this task's approved schema delta for frozen digest checks.

This leaves every historical numerical digest untouched. New-contract tests
assert the forward slot mapping separately.
"""

from copy import deepcopy


def before_equipment_slots(value):
    value = deepcopy(value)
    if isinstance(value, dict):
        for key, part in list(value.items()):
            value[key] = before_equipment_slots(part)
        for key in ("fixed_loadout", "loadout"):
            loadout = value.get(key)
            if not isinstance(loadout, dict):
                continue
            off = loadout.get("off_hand")
            if isinstance(off, str) and (
                off.startswith("quiver_") or off in {"rat_poison_glands", "golem_stone_reserve"}
            ):
                loadout["quiver"] = off
                if key in {"fixed_loadout", "loadout"}:
                    loadout["off_hand"] = None
                else:
                    loadout.pop("off_hand")
            if key in {"fixed_loadout", "loadout"}:
                loadout.setdefault("chest_garment", None)
                loadout.setdefault("legs_garment", None)
                loadout.setdefault("quiver", None)
    elif isinstance(value, list):
        value = [before_equipment_slots(part) for part in value]
    return value
