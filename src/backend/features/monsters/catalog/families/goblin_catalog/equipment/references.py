"""Goblins choose shared mechanics; no generated item payloads live here."""

from types import MappingProxyType

from src.backend.features.monsters.catalog.equipment_library import EquipmentItemReferenceDTO
from src.backend.features.monsters.catalog.equipment_library.profiles import equipment_id

AMULET_PROFILES = MappingProxyType(
    {
        "goblin_sneak": "nimble",
        "goblin_scavenger": "bruiser",
        "goblin_cutter": "duelist",
        "goblin_sparkpick": "bruiser",
        "goblin_spearman": "bruiser",
        "goblin_slinger": "nimble",
        "goblin_scrapguard": "bruiser",
        "goblin_tinkerer": "nimble",
        "goblin_bomber": "nimble",
        "goblin_trapmaster": "nimble",
        "goblin_chief": "bruiser",
        "scrap_king": "bruiser",
    }
)


def profile_for(member, slot: str, base_id: str) -> str:
    if slot == "amulet":
        return AMULET_PROFILES[member.variant_id]
    if slot == "quiver":
        return "ammunition"
    if slot == "chest_armor":
        return "fortified" if base_id == "plate_chest" else "mobile"
    if slot == "off_hand":
        return "guard" if base_id in {"buckler", "shield", "kite_shield"} else "offhand"
    if slot in {"main_hand", "two_hand"}:
        return "impact" if "skill_macing" in member.skills else "precision"
    raise ValueError(f"No authored goblin equipment profile for slot: {slot}")


def references_for(member, tier: int) -> tuple[EquipmentItemReferenceDTO, ...]:
    if type(tier) is not int or not member.min_tier <= tier <= member.max_tier:
        raise LookupError("No prepared equipment at this member tier")
    return tuple(
        EquipmentItemReferenceDTO(
            slot=slot,
            item_id=equipment_id(base_id=base_id, slot=slot, profile_id=profile_for(member, slot, base_id), tier=tier),
        )
        for slot, base_id in sorted(member.fixed_loadout.items())
        if base_id
    )
