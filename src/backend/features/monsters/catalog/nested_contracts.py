"""Typed authored composition: one reusable mechanical basis, explicit clan variants.

This authoring layer resolves into the existing read contracts. It never loads a
database and deliberately supports only one reference hop, not inheritance chains.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import Any

from pydantic import ConfigDict

from src.backend.features.monsters.catalog.authoring import define_base_clan
from src.backend.features.monsters.catalog.contracts import (
    ClanDefinition,
    FamilyDefinition,
    ImageAssetReference,
    MemberDefinition,
    MonsterArchetype,
    MonsterLoadoutDTO,
    MonsterLootProfileDTO,
    MonsterRole,
    MonsterStatsDTO,
    MonsterTierRangeDTO,
    OrganizationType,
    freeze_catalog_value,
    thaw_catalog_value,
)
from src.backend.features.monsters.catalog.equipment_contracts import FamilyEquipmentDTO


class BaseStatsDTO(MonsterStatsDTO):
    model_config = ConfigDict(frozen=True, strict=True)


class BaseLoadoutDTO(MonsterLoadoutDTO):
    model_config = ConfigDict(frozen=True, strict=True)


class TierAvailabilityDTO(MonsterTierRangeDTO):
    model_config = ConfigDict(frozen=True, strict=True)


class LootProfileDTO(MonsterLootProfileDTO):
    model_config = ConfigDict(frozen=True, strict=True)
    materials: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FamilyTraitsDTO:
    archetype: MonsterArchetype
    organization_type: OrganizationType
    resource_version: float = 1.0
    default_tags: tuple[str, ...] = ()
    loot_profile: LootProfileDTO | None = None

    def __post_init__(self):
        object.__setattr__(self, "default_tags", tuple(self.default_tags))

    def legacy_payload(self):
        return {
            "resource_version": self.resource_version,
            "archetype": self.archetype,
            "organization_type": self.organization_type,
            "default_tags": list(self.default_tags),
            "loot_profile": self.loot_profile.model_dump(mode="json") if self.loot_profile else None,
        }


@dataclass(frozen=True, slots=True)
class MemberBaseDTO:
    id: str
    role: MonsterRole
    stats: BaseStatsDTO
    tiers: TierAvailabilityDTO
    spawn_weight: int
    assembly_cost: int
    loadout: BaseLoadoutDTO | None = None
    equipment_set_id: str | None = None
    member_model: Mapping[str, Any] | None = None
    default_image: ImageAssetReference | None = None

    def __post_init__(self):
        if not self.id or self.role not in ("minion", "veteran", "elite", "boss"):
            raise ValueError("Member basis requires an ID and a valid role")
        if type(self.assembly_cost) is not int or self.assembly_cost <= 0:
            raise ValueError("Assembly cost must be a positive integer")
        if type(self.spawn_weight) is not int or self.spawn_weight <= 0:
            raise ValueError("Spawn weight must be a positive integer")
        if not isinstance(self.stats, BaseStatsDTO):
            raise TypeError("Member basis requires typed stats")
        if (self.loadout is None) == (self.equipment_set_id is None):
            raise ValueError("Member basis requires exactly one loadout or equipment set")
        if self.loadout is not None and not isinstance(self.loadout, BaseLoadoutDTO):
            raise TypeError("Member basis requires typed loadout")
        if self.equipment_set_id is not None and (
            not isinstance(self.equipment_set_id, str) or not self.equipment_set_id
        ):
            raise ValueError("Equipment set ID must not be empty")
        if not isinstance(self.tiers, TierAvailabilityDTO):
            raise TypeError("Member basis requires typed tiers")
        object.__setattr__(self, "member_model", freeze_catalog_value(self.member_model))


@dataclass(frozen=True, slots=True)
class MemberVariantDTO:
    id: str
    base_id: str
    skills: tuple[str, ...]
    text_id: str | None = None
    name: str = ""
    description: str = ""
    image: ImageAssetReference | None = None
    tags: tuple[str, ...] = ()
    ability_ids: tuple[str, ...] = ()
    assembly_cost: int | None = None

    def __post_init__(self):
        if not self.id or not self.base_id or not (self.name or self.text_id):
            raise ValueError("Variant requires identity, basis and display name")
        if self.assembly_cost is not None and (type(self.assembly_cost) is not int or self.assembly_cost <= 0):
            raise ValueError("Assembly cost override must be a positive integer")
        for key in ("skills", "tags", "ability_ids"):
            values = tuple(getattr(self, key))
            if any(not isinstance(value, str) or not value for value in values):
                raise ValueError(f"Invalid {key}")
            if len(set(values)) != len(values):
                raise ValueError(f"Duplicate {key}")
            object.__setattr__(self, key, values)


@dataclass(frozen=True, slots=True)
class ClanDTO:
    id: str
    members: tuple[MemberVariantDTO, ...]
    text_id: str | None = None
    name: str = ""
    normal_spawn: bool = True
    description: str = ""
    tags: tuple[str, ...] = ()
    features: tuple[str, ...] = ()
    equipment_overrides: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if any(
            not isinstance(key, str) or not key or not isinstance(value, str) or not value
            for key, value in self.equipment_overrides.items()
        ):
            raise ValueError("Equipment overrides require basis and set IDs")
        object.__setattr__(self, "equipment_overrides", freeze_catalog_value(self.equipment_overrides))
        for key in ("members", "tags", "features"):
            object.__setattr__(self, key, tuple(getattr(self, key)))
        if not self.id or not (self.name or self.text_id):
            raise ValueError("Clan requires identity and name")
        _unique((member.id for member in self.members), "clan member")


@dataclass(frozen=True, slots=True)
class FamilyDTO:
    id: str
    bases: tuple[MemberBaseDTO, ...]
    clans: tuple[ClanDTO, ...]
    traits: FamilyTraitsDTO
    equipment: FamilyEquipmentDTO | None = None
    text_id: str | None = None
    name: str = ""
    description: str = ""

    def __post_init__(self):
        object.__setattr__(self, "bases", tuple(self.bases))
        object.__setattr__(self, "clans", tuple(self.clans))
        if self.equipment is not None and not isinstance(self.equipment, FamilyEquipmentDTO):
            raise TypeError("Family requires typed equipment catalog")
        if not isinstance(self.traits, FamilyTraitsDTO):
            raise TypeError("Family requires typed traits")
        if not self.id or not (self.name or self.text_id):
            raise ValueError("Family requires identity and name")
        _unique((basis.id for basis in self.bases), "member basis")
        _unique((clan.id for clan in self.clans), "clan")
        base_ids = {basis.id for basis in self.bases}
        for basis in self.bases:
            if basis.equipment_set_id is not None:
                if self.equipment is None:
                    raise ValueError("Family equipment set catalog is required")
                self.equipment.get_set(basis.equipment_set_id)
        for clan in self.clans:
            for basis_id, set_id in clan.equipment_overrides.items():
                if basis_id not in base_ids:
                    raise ValueError(f"Unknown equipment override basis: {basis_id}")
                if basis_id not in {member.base_id for member in clan.members}:
                    raise ValueError(f"Equipment override basis is not in clan: {basis_id}")
                if self.equipment is None:
                    raise ValueError("Family equipment set catalog is required")
                self.equipment.get_set(set_id)
            for member in clan.members:
                if member.base_id not in base_ids:
                    raise ValueError(f"Unknown member basis: {member.base_id}")


def _unique(values, label):
    values = tuple(values)
    if len(set(values)) != len(values):
        raise ValueError(f"Duplicate {label} IDs")


def resolve_family(
    data: FamilyDTO,
) -> tuple[FamilyDefinition, tuple[ClanDefinition, ...], tuple[MemberDefinition, ...]]:
    """Resolve references once; keep variants' skills and abilities independent."""
    from .texts import resolve_text

    family_text = resolve_text(data.text_id) if data.text_id else data
    bases = {basis.id: basis for basis in data.bases}
    clans, members = [], []
    family = None
    for clan in data.clans:
        clan_text = resolve_text(clan.text_id) if clan.text_id else clan
        payload = data.traits.legacy_payload()
        payload["id"] = data.id
        payload["variants"] = {}
        presentation = {}
        for variant in clan.members:
            basis = bases[variant.base_id]
            equipment_set_id = clan.equipment_overrides.get(basis.id, basis.equipment_set_id)
            loadout = (
                BaseLoadoutDTO(**data.equipment.resolve(equipment_set_id))
                if equipment_set_id is not None
                else basis.loadout
            )
            text = resolve_text(variant.text_id) if variant.text_id else variant
            effective_image = variant.image if variant.image is not None else basis.default_image
            payload["variants"][variant.id] = {
                "id": variant.id,
                "role": basis.role,
                "narrative_hint": text.description,
                "spawn_weight": basis.spawn_weight,
                "extra_tags": list(variant.tags),
                **basis.tiers.model_dump(),
                "base_stats": basis.stats.model_dump(),
                "fixed_loadout": loadout.model_dump(),
                "skills": list(variant.skills),
                "member_model": thaw_catalog_value(basis.member_model),
            }
            presentation[variant.id] = {"name": text.name}
            if effective_image is not None:
                presentation[variant.id]["image"] = {
                    key: getattr(effective_image, key)
                    for key in ("asset_id", "source_path", "review_status", "display_mirror")
                }
        # Each concrete clan has its own role roster; family metadata is shared.
        payload["hierarchy"] = {
            key: [variant.id for variant in clan.members if bases[variant.base_id].role == role]
            for key, role in (("minions", "minion"), ("veterans", "veteran"), ("elites", "elite"), ("boss", "boss"))
        }
        resolved_family, resolved_clan, resolved_members = define_base_clan(
            payload,
            family_name=family_text.name,
            clan_id=clan.id,
            clan_name=clan_text.name,
            normal_spawn=clan.normal_spawn,
            presentation=presentation,
            assembly_costs={
                variant.id: variant.assembly_cost
                if variant.assembly_cost is not None
                else bases[variant.base_id].assembly_cost
                for variant in clan.members
            },
        )
        family = resolved_family if family is None else family
        clans.append(
            replace(
                resolved_clan,
                description=clan_text.description,
                text_id=clan.text_id,
                tags=resolved_clan.tags | frozenset(clan.tags),
                features=clan.features,
            )
        )
        members.extend(
            replace(
                member,
                tags=member.tags | frozenset(clan.tags),
                ability_ids=variant.ability_ids,
                base_id=variant.base_id,
                equipment_set_id=clan.equipment_overrides.get(variant.base_id, bases[variant.base_id].equipment_set_id),
                equipment_source="clan_override"
                if variant.base_id in clan.equipment_overrides
                else ("base_set" if bases[variant.base_id].equipment_set_id else None),
                text_id=variant.text_id,
                image_source="variant_override"
                if variant.image is not None
                else ("default_base" if bases[variant.base_id].default_image else None),
            )
            for member, variant in zip(resolved_members, clan.members, strict=True)
        )
    if family is None:
        raise ValueError("Family requires at least one clan")
    mechanics = thaw_catalog_value(family.mechanics)
    mechanics["hierarchy"] = {
        key: list(dict.fromkeys(member.variant_id for member in members if member.role == role))
        for key, role in (("minions", "minion"), ("veterans", "veteran"), ("elites", "elite"), ("boss", "boss"))
    }
    family = replace(
        family,
        description=family_text.description,
        text_id=data.text_id,
        clan_ids=tuple(clan.id for clan in clans),
        mechanics=mechanics,
    )
    return family, tuple(clans), tuple(members)
