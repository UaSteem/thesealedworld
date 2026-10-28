"""Reusable complete loadouts; no generated item stats or tier scaling."""

from src.backend.features.monsters.catalog.equipment_contracts import EquipmentSetDTO

SETS = (
    EquipmentSetDTO(
        "sneak", {"amulet": "amulet", "chest_armor": "light_chest_armor", "main_hand": "knife", "off_hand": "knife"}
    ),
    EquipmentSetDTO(
        "scavenger",
        {"amulet": "amulet", "chest_armor": "light_chest_armor", "main_hand": "mace", "off_hand": "buckler"},
    ),
    EquipmentSetDTO(
        "cutter", {"amulet": "amulet", "chest_armor": "light_chest_armor", "main_hand": "dagger", "off_hand": "knife"}
    ),
    EquipmentSetDTO(
        "sparkpick",
        {"amulet": "amulet", "chest_armor": "light_chest_armor", "main_hand": "hatchet", "off_hand": "buckler"},
    ),
    EquipmentSetDTO(
        "spearman",
        {"amulet": "amulet", "chest_armor": "medium_chest_armor", "main_hand": "spear", "off_hand": "shield"},
    ),
    EquipmentSetDTO(
        "slinger",
        {"amulet": "amulet", "chest_armor": "light_chest_armor", "off_hand": "quiver_standard", "two_hand": "shortbow"},
    ),
    EquipmentSetDTO(
        "scrapguard",
        {"amulet": "amulet", "chest_armor": "medium_chest_armor", "main_hand": "mace", "off_hand": "shield"},
    ),
    EquipmentSetDTO(
        "tinkerer",
        {"amulet": "amulet", "chest_armor": "medium_chest_armor", "main_hand": "rapier", "off_hand": "buckler"},
    ),
    EquipmentSetDTO(
        "bomber",
        {"amulet": "amulet", "chest_armor": "medium_chest_armor", "off_hand": "quiver_fire", "two_hand": "shortbow"},
    ),
    EquipmentSetDTO(
        "trapmaster",
        {"amulet": "amulet", "chest_armor": "medium_chest_armor", "main_hand": "stiletto", "off_hand": "main_gauche"},
    ),
    EquipmentSetDTO(
        "chief",
        {"amulet": "amulet", "chest_armor": "heavy_chest_armor", "main_hand": "battle_axe", "off_hand": "kite_shield"},
    ),
    EquipmentSetDTO("scrap_king", {"amulet": "amulet", "chest_armor": "heavy_chest_armor", "two_hand": "warhammer"}),
)
