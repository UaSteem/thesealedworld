from __future__ import annotations

from copy import deepcopy

import pytest

from src.backend.features.inventory.services.equipment_migration import migrate_inventory_snapshot
from src.backend.features.inventory.services.equipment_rules import (
    EquipmentMigrationRequiredError,
    ensure_current_equipment_contract,
)
from src.shared.schemas.inventory import InventoryRuntimeSessionDTO


def snapshot():
    def item(key, base, kind, slot):
        return {
            "item_id": key,
            "base_id": base,
            "item_type": kind,
            "name": base,
            "slot": slot,
            "placement": "equipped",
            "valid_slots": [slot],
            "quantity": 2,
            "mechanics": {"slot": slot, "power": 3},
            "unknown_extension": {"preserve": True},
        }

    return {
        "char_id": 7,
        "is_dirty": True,
        "extension": "preserved",
        "layout": {
            "equipment": {"two_hand": "bow", "quiver": "ammo", "chest_garment": "shirt", "legs_garment": "pants"},
            "belt": {},
            "backpack": [],
        },
        "by_id": {
            "bow": item("bow", "shortbow", "weapon", "two_hand"),
            "ammo": item("ammo", "quiver_training", "ammo", "quiver"),
            "shirt": item("shirt", "linen_shirt", "garment", "chest_garment"),
            "pants": item("pants", "pants", "garment", "legs_garment"),
        },
    }


def test_offline_migration_is_lossless_pure_and_idempotent():
    old = snapshot()
    original = deepcopy(old)
    migrated, report = migrate_inventory_snapshot(old)
    assert old == original
    assert report["changed"]
    assert migrated["layout"]["equipment"] == {"two_hand": "bow", "off_hand": "ammo"}
    assert set(migrated["layout"]["backpack"]) == {"shirt", "pants"}
    assert migrated["by_id"]["ammo"]["base_id"] == "quiver_standard"
    assert migrated["by_id"]["ammo"]["mechanics"] == {"slot": "off_hand", "power": 3}
    assert set(migrated["by_id"]) == set(old["by_id"])
    assert all(
        row["quantity"] == 2 and row["unknown_extension"] == {"preserve": True} for row in migrated["by_id"].values()
    )
    assert migrated["extension"] == "preserved"
    assert migrate_inventory_snapshot(migrated)[0] == migrated
    ensure_current_equipment_contract(InventoryRuntimeSessionDTO.model_validate(migrated))


def test_conflicting_quiver_moves_to_backpack_without_overwriting_offhand():
    old = snapshot()
    old["by_id"]["bow"]["base_id"] = "greatsword"
    migrated, _ = migrate_inventory_snapshot(old)
    assert migrated["by_id"]["ammo"]["placement"] == "backpack"
    assert migrated["by_id"]["bow"]["placement"] == "equipped"
    assert set(migrated["layout"]["backpack"]) == {"ammo", "shirt", "pants"}


@pytest.mark.parametrize("defect", ["dangling", "duplicate", "unknown_slot"])
def test_migration_rejects_ambiguous_documents_without_mutating(defect):
    old = snapshot()
    if defect == "dangling":
        old["layout"]["backpack"].append("missing")
    elif defect == "duplicate":
        old["layout"]["backpack"].append("bow")
    else:
        old["layout"]["equipment"]["unknown"] = None
    before = deepcopy(old)
    with pytest.raises(ValueError):
        migrate_inventory_snapshot(old)
    assert old == before


def test_legacy_runtime_is_blocked_until_explicit_migration():
    with pytest.raises(EquipmentMigrationRequiredError):
        ensure_current_equipment_contract(InventoryRuntimeSessionDTO.model_validate(snapshot()))


@pytest.mark.asyncio
async def test_legacy_runtime_cannot_flush_before_migration():
    from src.backend.features.inventory.services.inventory_service import InventoryService

    service = InventoryService.__new__(InventoryService)
    with pytest.raises(EquipmentMigrationRequiredError):
        await service.flush_session(InventoryRuntimeSessionDTO.model_validate(snapshot()))


def test_cli_defaults_to_dry_run_and_writes_only_new_copies(tmp_path):
    import json
    import subprocess
    import sys

    source = tmp_path / "inventory.json"
    source.write_text(json.dumps(snapshot()), encoding="utf-8")
    original = source.read_bytes()
    command = [sys.executable, "-m", "tools.inventory.migrate_equipment_slots", str(source)]
    dry_run = subprocess.run(command, capture_output=True, text=True, check=True)
    assert json.loads(dry_run.stdout)["mode"] == "dry-run"
    assert source.read_bytes() == original
    output = tmp_path / "migrated.json"
    subprocess.run([*command, "--write-output", str(output)], capture_output=True, text=True, check=True)
    migrated = json.loads(output.read_text(encoding="utf-8"))
    assert not migrate_inventory_snapshot(migrated)[1]["changed"]
    overwrite = subprocess.run([*command, "--write-output", str(source)], capture_output=True, text=True)
    assert overwrite.returncode != 0
    assert source.read_bytes() == original
