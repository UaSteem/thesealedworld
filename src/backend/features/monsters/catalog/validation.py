"""Cross-reference validation for the complete authored catalog."""

from pydantic import ValidationError

from src.backend.features.monsters.catalog.contracts import (
    ClanDefinition,
    FamilyDefinition,
    MemberDefinition,
    MonsterFamilyDTO,
    MonsterVariantDTO,
    thaw_catalog_value,
)


class CatalogValidationError(ValueError):
    pass


def _unique(values, label):
    result = {}
    for value in values:
        if not value.id or value.id in result:
            raise CatalogValidationError(f"duplicate {label} or empty ID: {value.id}")
        result[value.id] = value
    return result


def validate_catalog(
    families: tuple[FamilyDefinition, ...],
    clans: tuple[ClanDefinition, ...],
    members: tuple[MemberDefinition, ...],
) -> None:
    family_map = _unique(families, "family")
    clan_map = _unique(clans, "clan")
    member_map = _unique(members, "member")
    for family in families:
        if family.mechanics["id"] != family.id or frozenset(family.mechanics["default_tags"]) != family.tags:
            raise CatalogValidationError(f"invalid family mechanics identity or tags: {family.id}")
        if not family.clan_ids or len(set(family.clan_ids)) != len(family.clan_ids):
            raise CatalogValidationError(f"invalid family clan membership: {family.id}")
        for clan_id in family.clan_ids:
            clan = clan_map.get(clan_id)
            if clan is None or clan.family_id != family.id:
                raise CatalogValidationError(f"missing clan or family mismatch: {clan_id}")
    for clan in clans:
        family = family_map.get(clan.family_id)
        if family is None or clan.id not in family.clan_ids:
            raise CatalogValidationError(f"invalid family membership: {clan.id}")
        if not clan.member_ids or len(set(clan.member_ids)) != len(clan.member_ids):
            raise CatalogValidationError(f"invalid clan membership: {clan.id}")
        variant_ids = [member_map[mid].variant_id for mid in clan.member_ids if mid in member_map]
        if len(set(variant_ids)) != len(variant_ids):
            raise CatalogValidationError(f"duplicate clan variant: {clan.id}")
        for member_id in clan.member_ids:
            if member_id not in member_map:
                raise CatalogValidationError(f"missing member: {member_id}")
            member = member_map[member_id]
            if member.clan_id != clan.id or member.family_id != clan.family_id:
                raise CatalogValidationError(f"invalid clan membership: {member_id}")
    for member in members:
        clan = clan_map.get(member.clan_id)
        if clan is None or member.id not in clan.member_ids:
            raise CatalogValidationError(f"invalid clan membership: {member.id}")
        if not member.name or member.min_tier > member.max_tier:
            raise CatalogValidationError(f"invalid member presentation or tier: {member.id}")
        if member.variant_id != member.mechanics["id"] or member.role != member.mechanics["role"]:
            raise CatalogValidationError(f"invalid member mechanics identity: {member.id}")
        if member.min_tier != member.mechanics["min_tier"] or member.max_tier != member.mechanics["max_tier"]:
            raise CatalogValidationError(f"invalid member tier: {member.id}")
        expected_tags = family_map[member.family_id].tags | clan.tags | frozenset(member.mechanics["extra_tags"])
        if member.tags != expected_tags:
            raise CatalogValidationError(f"invalid member tags: {member.id}")
        try:
            MonsterVariantDTO.model_validate(thaw_catalog_value(member.mechanics))
        except ValidationError as error:
            raise CatalogValidationError(f"invalid member mechanics: {member.id}: {error}") from error
    for family in families:
        # Family hierarchy references the family's vocabulary, not every clan's
        # roster. A subtype can deliberately contain only a subset of that roster.
        payload = thaw_catalog_value(family.mechanics)
        variants = {}
        for member in members:
            if member.family_id == family.id:
                variants.setdefault(member.variant_id, thaw_catalog_value(member.mechanics))
        payload["variants"] = variants
        try:
            MonsterFamilyDTO.model_validate(payload)
        except (ValidationError, ValueError) as error:
            raise CatalogValidationError(f"invalid family mechanics: {family.id}: {error}") from error
