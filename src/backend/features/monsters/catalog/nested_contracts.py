"""Typed authored composition: one reusable mechanical basis, explicit clan variants.

This authoring layer resolves into the existing read contracts. It never loads a
database and deliberately supports only one reference hop, not inheritance chains.
"""

from collections.abc import Mapping
from dataclasses import dataclass, replace
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
    loadout: BaseLoadoutDTO
    tiers: TierAvailabilityDTO
    spawn_weight: int
    member_model: Mapping[str, Any] | None = None

    def __post_init__(self):
        if not self.id or self.role not in ("minion", "veteran", "elite", "boss"):
            raise ValueError("Member basis requires an ID and a valid role")
        if type(self.spawn_weight) is not int or self.spawn_weight <= 0:
            raise ValueError("Spawn weight must be a positive integer")
        if not isinstance(self.stats, BaseStatsDTO) or not isinstance(self.loadout, BaseLoadoutDTO):
            raise TypeError("Member basis requires typed stats and loadout")
        if not isinstance(self.tiers, TierAvailabilityDTO):
            raise TypeError("Member basis requires typed tiers")
        object.__setattr__(self, "member_model", freeze_catalog_value(self.member_model))


@dataclass(frozen=True, slots=True)
class MemberVariantDTO:
    id: str
    base_id: str
    name: str
    description: str
    skills: tuple[str, ...]
    image: ImageAssetReference | None = None
    tags: tuple[str, ...] = ()
    ability_ids: tuple[str, ...] = ()

    def __post_init__(self):
        if not self.id or not self.base_id or not self.name:
            raise ValueError("Variant requires identity, basis and display name")
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
    name: str
    members: tuple[MemberVariantDTO, ...]
    normal_spawn: bool = True
    description: str = ""
    tags: tuple[str, ...] = ()
    features: tuple[str, ...] = ()

    def __post_init__(self):
        for key in ("members", "tags", "features"):
            object.__setattr__(self, key, tuple(getattr(self, key)))
        if not self.id or not self.name:
            raise ValueError("Clan requires identity and name")
        _unique((member.id for member in self.members), "clan member")


@dataclass(frozen=True, slots=True)
class FamilyDTO:
    id: str
    name: str
    bases: tuple[MemberBaseDTO, ...]
    clans: tuple[ClanDTO, ...]
    traits: FamilyTraitsDTO
    description: str = ""

    def __post_init__(self):
        object.__setattr__(self, "bases", tuple(self.bases))
        object.__setattr__(self, "clans", tuple(self.clans))
        if not isinstance(self.traits, FamilyTraitsDTO):
            raise TypeError("Family requires typed traits")
        if not self.id or not self.name:
            raise ValueError("Family requires identity and name")
        _unique((basis.id for basis in self.bases), "member basis")
        _unique((clan.id for clan in self.clans), "clan")
        base_ids = {basis.id for basis in self.bases}
        for clan in self.clans:
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
    bases = {basis.id: basis for basis in data.bases}
    clans, members = [], []
    family = None
    for clan in data.clans:
        payload = data.traits.legacy_payload()
        payload["id"] = data.id
        payload["variants"] = {}
        presentation = {}
        for variant in clan.members:
            basis = bases[variant.base_id]
            payload["variants"][variant.id] = {
                "id": variant.id,
                "role": basis.role,
                "narrative_hint": variant.description,
                "spawn_weight": basis.spawn_weight,
                "extra_tags": list(variant.tags),
                **basis.tiers.model_dump(),
                "base_stats": basis.stats.model_dump(),
                "fixed_loadout": basis.loadout.model_dump(),
                "skills": list(variant.skills),
                "member_model": thaw_catalog_value(basis.member_model),
            }
            presentation[variant.id] = {"name": variant.name}
            if variant.image is not None:
                presentation[variant.id]["image"] = {
                    key: getattr(variant.image, key)
                    for key in ("asset_id", "source_path", "review_status", "display_mirror")
                }
        # Each concrete clan has its own role roster; family metadata is shared.
        payload["hierarchy"] = {
            key: [variant.id for variant in clan.members if bases[variant.base_id].role == role]
            for key, role in (("minions", "minion"), ("veterans", "veteran"), ("elites", "elite"), ("boss", "boss"))
        }
        resolved_family, resolved_clan, resolved_members = define_base_clan(
            payload,
            family_name=data.name,
            clan_id=clan.id,
            clan_name=clan.name,
            normal_spawn=clan.normal_spawn,
            presentation=presentation,
        )
        family = resolved_family if family is None else family
        clans.append(
            replace(
                resolved_clan,
                description=clan.description,
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
        family, description=data.description, clan_ids=tuple(clan.id for clan in clans), mechanics=mechanics
    )
    return family, tuple(clans), tuple(members)
