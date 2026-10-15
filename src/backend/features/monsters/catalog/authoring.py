"""Build validated immutable definitions from hand-authored Python literals.

No habitat input, provider, database or randomized content creation is involved.
"""

from collections.abc import Mapping
from typing import Any

from src.backend.features.monsters.catalog.contracts import (
    ClanDefinition,
    FamilyDefinition,
    ImageAssetReference,
    MemberDefinition,
    MonsterFamilyDTO,
    thaw_catalog_value,
)


def define_base_clan(
    data: Mapping[str, Any],
    *,
    family_name: str,
    clan_id: str,
    clan_name: str,
    normal_spawn: bool,
    presentation: Mapping[str, Mapping[str, Any]],
) -> tuple[FamilyDefinition, ClanDefinition, tuple[MemberDefinition, ...]]:
    validated = MonsterFamilyDTO.model_validate(data)
    payload = validated.model_dump()
    variants = payload.pop("variants")
    if set(presentation) - set(variants):
        raise ValueError(f"Presentation references unknown variants: {sorted(set(presentation) - set(variants))}")
    members = []
    for variant_id, mechanics in variants.items():
        if mechanics["id"] != variant_id:
            raise ValueError(f"Variant key/id mismatch: {variant_id}")
        display = presentation.get(variant_id, {})
        asset = display.get("image")
        image = ImageAssetReference(**asset) if asset is not None else None
        members.append(
            MemberDefinition(
                id=f"{clan_id}.{variant_id}",
                family_id=validated.id,
                clan_id=clan_id,
                variant_id=variant_id,
                # Existing variants without an authored display name retain their stable ID.
                name=display.get("name", variant_id),
                description=mechanics["narrative_hint"],
                role=mechanics["role"],
                tags=frozenset((*validated.default_tags, *mechanics["extra_tags"])),
                min_tier=mechanics["min_tier"],
                max_tier=mechanics["max_tier"],
                image=image,
                mechanics=mechanics,
            )
        )
    family = FamilyDefinition(
        id=validated.id,
        name=family_name,
        description="",
        tags=frozenset(validated.default_tags),
        clan_ids=(clan_id,),
        mechanics=payload,
    )
    clan = ClanDefinition(
        id=clan_id,
        family_id=family.id,
        name=clan_name,
        description="",
        tags=family.tags,
        member_ids=tuple(member.id for member in members),
        normal_spawn=normal_spawn,
    )
    return family, clan, tuple(members)


def legacy_family_payload(family: FamilyDefinition, members: tuple[MemberDefinition, ...]) -> dict[str, Any]:
    """Temporary read adapter for existing consumers of MonsterFamilyDTO."""
    payload = thaw_catalog_value(family.mechanics)
    keys = [member.variant_id for member in members]
    if len(set(keys)) != len(keys):
        raise ValueError(f"Legacy family adapter cannot represent duplicate variant IDs: {family.id}")
    payload["variants"] = {member.variant_id: thaw_catalog_value(member.mechanics) for member in members}
    return payload
