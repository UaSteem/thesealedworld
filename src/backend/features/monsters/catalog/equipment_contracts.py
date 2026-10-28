"""Family-owned references to the existing item catalog; no item mechanics."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from src.backend.features.items.services import ItemCatalogService


@dataclass(frozen=True, slots=True)
class EquipmentEntryDTO:
    id: str
    base_id: str

    def __post_init__(self):
        if any(not isinstance(value, str) or not value for value in (self.id, self.base_id)):
            raise ValueError("Equipment entry requires identity and item base")


@dataclass(frozen=True, slots=True)
class EquipmentSetDTO:
    id: str
    slots: Mapping[str, str]

    def __post_init__(self):
        if not isinstance(self.id, str) or not self.id:
            raise ValueError("Equipment set requires identity")
        if any(
            not isinstance(key, str) or not key or not isinstance(value, str) or not value
            for key, value in self.slots.items()
        ):
            raise ValueError("Equipment slots require slot and entry IDs")
        object.__setattr__(self, "slots", MappingProxyType(dict(self.slots)))


@dataclass(frozen=True, slots=True)
class FamilyEquipmentDTO:
    entries: tuple[EquipmentEntryDTO, ...]
    sets: tuple[EquipmentSetDTO, ...]

    def __post_init__(self):
        object.__setattr__(self, "entries", tuple(self.entries))
        object.__setattr__(self, "sets", tuple(self.sets))
        if any(not isinstance(entry, EquipmentEntryDTO) for entry in self.entries):
            raise TypeError("Family equipment requires typed entries")
        if any(not isinstance(equipment_set, EquipmentSetDTO) for equipment_set in self.sets):
            raise TypeError("Family equipment requires typed sets")
        catalog = ItemCatalogService.load_default()
        entries = {entry.id: entry for entry in self.entries}
        if len(entries) != len(self.entries) or len({item.id for item in self.sets}) != len(self.sets):
            raise ValueError("Duplicate equipment entry or set ID")
        for entry in self.entries:
            if catalog.get_base_item(entry.base_id) is None:
                raise ValueError(f"Unknown item base: {entry.base_id}")
        for equipment_set in self.sets:
            two_entry = entries.get(equipment_set.slots.get("two_hand", ""))
            off_entry = entries.get(equipment_set.slots.get("off_hand", ""))
            bow_ammunition = bool(
                two_entry
                and off_entry
                and two_entry.base_id in {"shortbow", "longbow", "composite_bow"}
                and catalog.get_base_item(off_entry.base_id).type == "ammo"
            )
            if two_entry and ("main_hand" in equipment_set.slots or (off_entry and not bow_ammunition)):
                raise ValueError("Two-hand slot conflicts with hand slots")
            for slot, entry_id in equipment_set.slots.items():
                if entry_id not in entries:
                    raise ValueError(f"Unknown equipment entry: {entry_id}")
                item = catalog.get_base_item(entries[entry_id].base_id)
                if slot not in {item.slot, *item.extra_slots}:
                    raise ValueError(f"Item {entries[entry_id].base_id} is incompatible with slot {slot}")

    def get_set(self, set_id: str) -> EquipmentSetDTO:
        for equipment_set in self.sets:
            if equipment_set.id == set_id:
                return equipment_set
        raise ValueError(f"Unknown equipment set: {set_id}")

    def resolve(self, set_id: str) -> dict[str, str]:
        entries = {entry.id: entry for entry in self.entries}
        return {slot: entries[entry_id].base_id for slot, entry_id in self.get_set(set_id).slots.items()}
