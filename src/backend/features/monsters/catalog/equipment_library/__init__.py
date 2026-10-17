"""Read-only shared monster items. Generation runs only in the authoring tool."""

from copy import deepcopy
from uuid import NAMESPACE_URL, uuid5

from src.backend.features.items.dto.instance import RuntimeItemProjectionDTO

from .contracts import EquipmentItemDefinitionDTO, EquipmentItemReferenceDTO


def list_equipment_items() -> tuple[str, ...]:
    from .prepared.index import DATA

    return tuple(sorted(DATA))


def get_equipment_item(item_id: str) -> EquipmentItemDefinitionDTO:
    from .prepared.index import DATA

    if item_id not in DATA:
        raise LookupError(f"Unknown shared monster equipment: {item_id}")
    from importlib import import_module

    payload = import_module(f"{__name__}.prepared.{DATA[item_id]}").DATA
    result = EquipmentItemDefinitionDTO.model_validate(deepcopy(payload))
    if result.id != item_id:
        raise ValueError("Shared equipment identity differs from catalog key")
    return result


def bind_equipment_item(reference: EquipmentItemReferenceDTO, *, owner_key: str, tier: int) -> RuntimeItemProjectionDTO:
    if not owner_key:
        raise ValueError("Bound equipment needs an owner")
    definition = get_equipment_item(reference.item_id)
    if type(tier) is not int or definition.tier != tier or definition.item.slot != reference.slot:
        raise ValueError("Equipment reference slot/tier does not match definition")
    item = definition.item.model_copy(deep=True)
    item.item_id = str(uuid5(NAMESPACE_URL, f"{owner_key}:{reference.slot}:{definition.id}"))
    item.owner_key = owner_key
    item.generation.source_context.update(equipment_catalog_id=definition.id, profile_id=definition.profile_id)
    if reference.name_ru:
        item.generation.source_context["presentation_name_ru"] = reference.name_ru
    if reference.description_ru:
        item.generation.source_context["presentation_description_ru"] = reference.description_ru
    if reference.natural_key:
        from src.backend.features.monsters.catalog.resources.equipment_mapping import get_natural_equipment_mapping

        mapping = get_natural_equipment_mapping(reference.natural_key)
        if mapping is None or mapping.base_id != item.base_id:
            raise ValueError("Natural presentation must use the same mechanical item base")
        item.generation.natural_key = reference.natural_key
    return item


__all__ = [
    "EquipmentItemDefinitionDTO",
    "EquipmentItemReferenceDTO",
    "bind_equipment_item",
    "get_equipment_item",
    "list_equipment_items",
]
