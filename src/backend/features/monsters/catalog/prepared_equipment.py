"""Validated ready equipment, produced once by ItemService and editable as data."""

from pydantic import BaseModel, ConfigDict, model_validator

from src.backend.features.items.dto.instance import RuntimeItemProjectionDTO
from src.backend.features.monsters.catalog.contracts import MemberDefinition, MonsterRole
from src.backend.features.monsters.dto.generation import MonsterItemsProjectionDTO
from src.backend.features.monsters.instances.integrations.item_generation import build_member_items_projection


class PreparedEquipmentSetDTO(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: int
    family_id: str
    clan_id: str
    variant_id: str
    equipment_set_id: str
    role: MonsterRole
    tier: int
    seed_version: str
    items: tuple[RuntimeItemProjectionDTO, ...]

    @model_validator(mode="after")
    def validate_set(self):
        if self.schema_version != 1 or not self.family_id:
            raise ValueError("Unsupported prepared equipment schema/family")
        if type(self.tier) is not int or not 0 <= self.tier <= 7:
            raise ValueError("Invalid equipment tier")
        if not all((self.clan_id, self.variant_id, self.equipment_set_id, self.seed_version)) or not self.items:
            raise ValueError("Prepared equipment needs identity and items")
        if len({item.item_id for item in self.items}) != len(self.items):
            raise ValueError("Duplicate item ID in prepared equipment")
        if len({item.slot for item in self.items}) != len(self.items):
            raise ValueError("Duplicate slot in prepared equipment")
        owners = {item.owner_key for item in self.items}
        if len(owners) != 1 or None in owners:
            raise ValueError("Prepared equipment must have one explicit template owner")
        return self

    def to_items_projection(self) -> MonsterItemsProjectionDTO:
        return build_member_items_projection(self.items, self.items[0].owner_key)


def list_prepared_equipment(*, family_id: str) -> tuple[tuple[str, int], ...]:
    """Return available saved sets; no generation or persistence."""
    return _loader(family_id).list_prepared_equipment()


def get_prepared_equipment(*, family_id: str, variant_id: str, tier: int) -> PreparedEquipmentSetDTO:
    result = _loader(family_id).get_prepared_equipment(variant_id, tier)
    if result.family_id != family_id:
        raise ValueError("Prepared equipment belongs to a different family")
    return result


def get_member_prepared_equipment(*, member: MemberDefinition, tier: int) -> PreparedEquipmentSetDTO:
    """Resolve an exact member's set; family loaders must not supply another clan."""
    if type(tier) is not int or not 0 <= tier <= 7:
        raise ValueError("Expected an integer equipment tier in 0..7")
    if not all(
        isinstance(value, str) and value and all(part.isidentifier() for part in value.split("."))
        for value in (member.family_id, member.clan_id, member.variant_id)
    ):
        raise ValueError("Expected valid member family, clan and variant IDs")
    result = _loader(member.family_id).get_prepared_equipment(member.variant_id, tier)
    expected = {
        "family_id": member.family_id,
        "clan_id": member.clan_id,
        "variant_id": member.variant_id,
        "role": member.role,
        "tier": tier,
    }
    if member.equipment_set_id is not None:
        expected["equipment_set_id"] = member.equipment_set_id
    for field, value in expected.items():
        if getattr(result, field) != value:
            raise LookupError(
                f"No exact prepared equipment for {member.id}, tier {tier}: "
                f"{field} expected {value!r}, got {getattr(result, field)!r}"
            )
    return result


def _loader(family_id: str):
    from importlib import import_module

    packages = {
        "goblin_tribe": "goblin_catalog",
        "wolf_pack": "wolf_catalog",
        "rat_swarm": "rat_catalog",
        "bandit_gang": "bandit_catalog",
    }
    if family_id not in packages:
        raise LookupError(f"No prepared equipment for family: {family_id}")
    return import_module(
        f"src.backend.features.monsters.catalog.families.{packages[family_id]}.equipment.prepared_loader"
    )
