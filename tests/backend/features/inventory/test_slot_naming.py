from src.backend.features.inventory.services.view import InventoryViewService
from src.backend.features.items.resources.presentation_texts import TEXTS
from src.frontend.game_features.game_lobby.view_models.lobby import _slot_label
from src.frontend.game_features.inventory.view_models.window import build_inventory_window_vm
from src.shared.schemas.inventory import InventoryRuntimeSessionDTO


def test_inventory_and_item_cards_name_separate_armor_and_clothing_layers():
    runtime = InventoryViewService().build_window(InventoryRuntimeSessionDTO(char_id=1), can_act=True)
    placeholder = build_inventory_window_vm()
    expected = {
        "head_armor": ("Броня головы", "armor"),
        "chest_armor": ("Броня корпуса", "armor"),
        "arms_armor": ("Наручи", "armor"),
        "gloves_garment": ("Перчатки", "accessory"),
        "legs_armor": ("Броня ног", "armor"),
    }
    for window in (runtime, placeholder):
        slots = {
            slot.slot_id: slot
            for zone in window.body_zones
            for slot in (zone.primary_slot, zone.secondary_slot)
            if slot is not None
        }
        for slot_id, (label, layer) in expected.items():
            assert (slots[slot_id].label, slots[slot_id].layer) == (label, layer)
            assert TEXTS["ru"]["slots"][slot_id] == label
            assert _slot_label(slot_id) == label
