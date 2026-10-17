from src.backend.features.monsters.catalog.equipment_contracts import FamilyEquipmentDTO

from .entries import ENTRIES
from .sets import SETS

GOBLIN_EQUIPMENT = FamilyEquipmentDTO(entries=ENTRIES, sets=SETS)
