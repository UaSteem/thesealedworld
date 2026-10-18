"""Stone bodies reuse shared mechanics; the family owns their natural presentation."""

from src.backend.features.monsters.catalog.equipment_library import EquipmentItemReferenceDTO
from src.backend.features.monsters.catalog.equipment_library.profiles import equipment_id
from src.backend.features.monsters.catalog.resources.equipment_mapping import get_natural_equipment_mapping


def references_for(member, tier: int) -> tuple[EquipmentItemReferenceDTO, ...]:
    if type(tier) is not int or not member.min_tier <= tier <= member.max_tier:
        raise LookupError("No prepared golem equipment at this member tier")
    references = []
    for slot, natural_key in sorted(member.fixed_loadout.items()):
        if not natural_key:
            continue
        mapping = get_natural_equipment_mapping(natural_key)
        if mapping.default_slot != slot:
            raise ValueError("Golem natural equipment uses an unsupported slot")
        if slot == "amulet":
            profile = "bruiser"
        elif slot == "chest_armor":
            profile = "fortified"
        elif slot == "quiver":
            profile = "ammunition"
        elif slot == "off_hand":
            profile = "guard" if mapping.item_kind == "shield" else "offhand"
        else:
            profile = "precision" if natural_key == "golem_stone_throw" else "impact"
        references.append(
            EquipmentItemReferenceDTO(
                slot=slot,
                item_id=equipment_id(base_id=mapping.base_id, slot=slot, profile_id=profile, tier=tier),
                natural_key=natural_key,
                name_ru=mapping.name_ru,
                description_ru=mapping.description_ru,
            )
        )
    return tuple(references)
