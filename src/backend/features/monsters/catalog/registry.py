from src.backend.features.monsters.catalog.authoring import legacy_family_payload
from src.backend.features.monsters.catalog.contracts import (
    ClanDefinition,
    FamilyDefinition,
    MemberDefinition,
    MonsterFamilyDTO,
    MonsterVariantDTO,
    thaw_catalog_value,
)
from src.backend.features.monsters.catalog.indexes import MonsterCatalog
from src.backend.features.monsters.catalog.prepared import PREPARED_FAMILIES
from src.backend.features.monsters.catalog.validation import validate_catalog

STARTER_FAMILY_IDS: tuple[str, ...] = ("rat_swarm", "wolf_pack", "bandit_gang", "goblin_tribe")


def _build_catalog() -> MonsterCatalog:
    families = tuple(family for family, _, _ in PREPARED_FAMILIES)
    clans = tuple(clan for _, clan, _ in PREPARED_FAMILIES)
    members = tuple(member for _, _, roster in PREPARED_FAMILIES for member in roster)
    # Validate sequences before indexing: dict construction must not conceal duplicates.
    validate_catalog(families, clans, members)
    return MonsterCatalog(
        {family.id: family for family in families},
        {clan.id: clan for clan in clans},
        {member.id: member for member in members},
    )


_CATALOG = _build_catalog()
# Transitional mutable copies, not another authored mechanics source.
ALL_FAMILIES_RAW = [legacy_family_payload(family, members) for family, _, members in PREPARED_FAMILIES]


def get_catalog() -> MonsterCatalog:
    return _CATALOG


def get_catalog_family(family_id: str) -> FamilyDefinition | None:
    return _CATALOG.families.get(family_id)


def get_catalog_clan(clan_id: str) -> ClanDefinition | None:
    return _CATALOG.clans.get(clan_id)


def get_catalog_member(member_id: str) -> MemberDefinition | None:
    return _CATALOG.members.get(member_id)


def get_family_config(family_id: str) -> MonsterFamilyDTO | None:
    family = get_catalog_family(family_id)
    if family is None:
        return None
    # Legacy reads have an explicit base-clan scope. Additional authored clans
    # must be queried by catalog ID rather than collapsing their variants here.
    clan = _CATALOG.clans[f"{family_id}.base"]
    members = tuple(_CATALOG.members[member_id] for member_id in clan.member_ids)
    return MonsterFamilyDTO.model_validate(legacy_family_payload(family, members))


def get_monster_template(variant_id: str) -> MonsterVariantDTO | None:
    matches = [
        member
        for member in _CATALOG.members.values()
        if member.variant_id == variant_id and member.clan_id == f"{member.family_id}.base"
    ]
    if len(matches) > 1:
        raise ValueError(f"Ambiguous legacy variant ID: {variant_id}; use qualified catalog member ID")
    if not matches:
        return None
    return MonsterVariantDTO.model_validate(thaw_catalog_value(matches[0].mechanics))


def get_available_variants_for_tier(family_id: str, tier: int) -> list[str]:
    family = get_family_config(family_id)
    if not family:
        return []

    # Работаем с DTO через точку
    return [var.id for var in family.variants.values() if var.min_tier <= tier <= var.max_tier]


def get_available_variants_for_tier_window(family_id: str, tier: int, radius: int = 1) -> list[str]:
    family = get_family_config(family_id)
    if not family:
        return []

    min_tier = max(0, tier - radius)
    max_tier = min(7, tier + radius)
    return [var.id for var in family.variants.values() if var.min_tier <= max_tier and var.max_tier >= min_tier]


def get_starter_family_ids() -> tuple[str, ...]:
    return STARTER_FAMILY_IDS


def get_all_family_configs() -> dict[str, MonsterFamilyDTO]:
    result = {}
    for family_id in _CATALOG.families:
        config = get_family_config(family_id)
        if config is None:
            raise RuntimeError(f"Catalog family disappeared: {family_id}")
        result[family_id] = config
    return result
