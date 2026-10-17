"""Resolve goblin references to shared ready item definitions. No generation."""

from src.backend.features.monsters.catalog.equipment_library import bind_equipment_item
from src.backend.features.monsters.catalog.registry import get_catalog

from .prepared_contracts import PreparedEquipmentSetDTO
from .references import references_for


def list_prepared_equipment() -> tuple[tuple[str, int], ...]:
    return tuple(
        (member.variant_id, tier)
        for member in get_catalog().members.values()
        if member.family_id == "goblin_tribe"
        for tier in range(member.min_tier, member.max_tier + 1)
    )


def get_prepared_equipment(variant_id: str, tier: int) -> PreparedEquipmentSetDTO:
    if not isinstance(variant_id, str) or not variant_id.isidentifier() or type(tier) is not int:
        raise ValueError("Expected a variant ID and integer tier")
    member = get_catalog().members.get(f"goblin_tribe.base.{variant_id}")
    if member is None:
        raise LookupError(f"No prepared goblin equipment: {variant_id}, tier {tier}")
    owner = f"{member.id}:tier:{tier}"
    return PreparedEquipmentSetDTO(
        schema_version=1,
        family_id=member.family_id,
        clan_id=member.clan_id,
        variant_id=member.variant_id,
        equipment_set_id=member.equipment_set_id,
        role=member.role,
        tier=tier,
        seed_version="shared-monster-equipment-v1",
        items=tuple(bind_equipment_item(ref, owner_key=owner, tier=tier) for ref in references_for(member, tier)),
    )
