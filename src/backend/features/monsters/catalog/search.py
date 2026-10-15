"""Deterministic catalog eligibility search, without selection or encounter policy."""

from dataclasses import dataclass

from src.backend.features.monsters.catalog.contracts import MemberDefinition
from src.backend.features.monsters.catalog.indexes import MonsterCatalog


@dataclass(frozen=True, slots=True)
class MonsterSearchFilters:
    """Categories intersect; IDs within a category are alternatives.

    Empty collections impose no restriction. All required tags must match,
    and any excluded tag rejects a member. Tags include family and clan tags.
    System clans remain excluded unless explicitly enabled, including ID reads.
    """

    family_ids: tuple[str, ...] = ()
    clan_ids: tuple[str, ...] = ()
    member_ids: tuple[str, ...] = ()
    required_tags: tuple[str, ...] = ()
    excluded_tags: tuple[str, ...] = ()
    include_system: bool = False

    def __post_init__(self) -> None:
        for field in ("family_ids", "clan_ids", "member_ids", "required_tags", "excluded_tags"):
            values = getattr(self, field)
            if isinstance(values, (str, bytes)):
                raise TypeError(f"{field} must be a collection of strings, not a bare string")
            normalized = tuple(values)
            if any(not isinstance(value, str) for value in normalized):
                raise TypeError(f"{field} entries must be strings")
            if any(not value.strip() for value in normalized):
                raise ValueError(f"{field} entries must be nonempty")
            object.__setattr__(self, field, normalized)
        if not isinstance(self.include_system, bool):
            raise TypeError("include_system must be a boolean")
        if set(self.required_tags).intersection(self.excluded_tags):
            raise ValueError("A tag cannot be both required and excluded")


class CatalogSearchService:
    """Search immutable definitions; consumers own random choice and grouping."""

    def __init__(self, catalog: MonsterCatalog | None = None) -> None:
        self._catalog = catalog

    def search(self, filters: MonsterSearchFilters | None = None) -> tuple[MemberDefinition, ...]:
        filters = filters if filters is not None else MonsterSearchFilters()
        if not isinstance(filters, MonsterSearchFilters):
            raise TypeError("filters must be MonsterSearchFilters")
        catalog = self._catalog
        if catalog is None:
            from src.backend.features.monsters.catalog.registry import get_catalog

            catalog = get_catalog()

        # Reuse the catalog's existing normal-spawn eligibility rule. Tags must
        # be matched on the complete family/clan/member union, not clans alone.
        eligible_clans = {clan.id for clan in catalog.find_clans(include_system=filters.include_system)}
        required = frozenset(filters.required_tags)
        excluded = frozenset(filters.excluded_tags)
        matches = []
        for member in catalog.members.values():
            if member.clan_id not in eligible_clans:
                continue
            if filters.family_ids and member.family_id not in filters.family_ids:
                continue
            if filters.clan_ids and member.clan_id not in filters.clan_ids:
                continue
            if filters.member_ids and member.id not in filters.member_ids:
                continue
            tags = member.tags | catalog.clans[member.clan_id].tags | catalog.families[member.family_id].tags
            if not required.issubset(tags) or excluded.intersection(tags):
                continue
            matches.append(member)
        return tuple(matches)
