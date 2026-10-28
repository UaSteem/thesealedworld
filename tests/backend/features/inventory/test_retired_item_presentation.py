from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.backend.features.inventory.repositories.items import runtime_item_from_instance
from src.backend.features.inventory.services.equipment_migration import migrate_inventory_snapshot
from src.backend.features.inventory.services.projection import build_runtime_session
from src.backend.features.inventory.services.view import InventoryViewService
from src.backend.features.items.services.catalog_service import ItemCatalogService
from src.shared.schemas.inventory import InventoryRuntimeSessionDTO

RETIRED = [
    ("apron", "Фартук", "chest_garment"),
    ("shirt", "Рубаха", "chest_garment"),
    ("tunic", "Туника", "chest_garment"),
    ("pants", "Штаны", "legs_garment"),
    ("linen_shirt", "Рубаха", "chest_garment"),
    ("wool_tunic", "Туника", "chest_garment"),
    ("fur_pants", "Штаны", "legs_garment"),
]


@pytest.mark.parametrize("base_id,title,slot", RETIRED)
def test_migrated_retired_items_keep_public_identity_without_hidden_lore(base_id, title, slot):
    source = {
        "char_id": 7,
        "layout": {"equipment": {slot: "old"}, "backpack": []},
        "by_id": {
            "old": {
                "item_id": "old",
                "base_id": base_id,
                "item_type": "garment",
                "name": "SECRET AI NAME",
                "description": "SECRET AI LORE",
                "slot": slot,
                "placement": "equipped",
                "valid_slots": [slot],
                "text_status": "generated",
                "is_identified": False,
                "mechanics": {"slot": slot},
                "metadata": {"lore": "SECRET METADATA"},
            }
        },
    }
    migrated, _ = migrate_inventory_snapshot(source)
    session = InventoryRuntimeSessionDTO.model_validate(migrated)
    window = InventoryViewService().build_window(session, can_act=True)
    row = next(row for row in window.visible_rows if row.item_id == "old")
    assert row.name == title
    assert row.details.description and "неизвест" not in row.details.description.lower()
    assert "SECRET" not in window.model_dump_json()
    assert not any(action.action == "equip" for action in row.details.actions)
    assert ItemCatalogService.load_default().get_base_item(base_id) is None
    assert migrated["by_id"]["old"]["name"] == "SECRET AI NAME"


@pytest.mark.parametrize("base_id,title,slot", RETIRED)
@pytest.mark.parametrize(
    "identified,status,disclosed", [(False, "generated", False), (True, "pending", False), (True, "generated", True)]
)
def test_sql_rehydration_uses_retired_public_text_and_preserves_disclosure_gate(
    base_id, title, slot, identified, status, disclosed
):
    record = SimpleNamespace(
        id="old",
        base_id=base_id,
        item_type="garment",
        rarity="shared",
        rarity_tier=0,
        is_identified=identified,
        text_status=status,
        name="SECRET LEGACY NAME",
        description="SECRET LEGACY LORE",
        mechanics={"slot": slot, "valid_slots": []},
        generation={},
        appearance={},
        metadata_={"lore": "SECRET METADATA"},
        _inventory_generated_template=SimpleNamespace(
            name="SECRET AI NAME", description="SECRET AI LORE", text_status=status
        ),
    )
    placement = SimpleNamespace(holder_type="character", storage_type="backpack", slot=None)
    item = runtime_item_from_instance(record, placement)
    assert item.name == ("SECRET AI NAME" if disclosed else title)
    assert item.description and ("SECRET AI LORE" in item.description) is disclosed
    window = InventoryViewService().build_window(build_runtime_session(7, [item]), can_act=True)
    assert ("SECRET" in window.model_dump_json()) is disclosed
    assert window.visible_rows[0].name == item.name
    assert ItemCatalogService.load_default().get_base_item(base_id) is None
