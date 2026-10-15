"""Immutable in-memory lookup and tag indices; no persistence dependency."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from src.backend.features.monsters.catalog.contracts import ClanDefinition, FamilyDefinition, MemberDefinition
from src.backend.features.monsters.catalog.validation import validate_catalog


@dataclass(frozen=True, slots=True)
class MonsterCatalog:
    families: Mapping[str, FamilyDefinition]
    clans: Mapping[str, ClanDefinition]
    members: Mapping[str, MemberDefinition]
    clans_by_tag: Mapping[str, frozenset[str]] = field(init=False)

    def __post_init__(self):
        validate_catalog(tuple(self.families.values()), tuple(self.clans.values()), tuple(self.members.values()))
        for label in ("families", "clans", "members"):
            entries = getattr(self, label)
            if any(key != value.id for key, value in entries.items()):
                raise ValueError(f"Catalog {label} key/id mismatch")
            object.__setattr__(self, label, MappingProxyType(dict(entries)))
        tag_index: dict[str, set[str]] = {}
        for clan in self.clans.values():
            for tag in clan.tags:
                tag_index.setdefault(tag, set()).add(clan.id)
        object.__setattr__(self, "clans_by_tag", MappingProxyType({k: frozenset(v) for k, v in tag_index.items()}))

    def find_clans(
        self,
        *,
        tags: Iterable[str] = (),
        family_id: str | None = None,
        tier: int | None = None,
        include_system: bool = False,
    ) -> tuple[ClanDefinition, ...]:
        """Require all tags; eligibility only, never random selection or clan creation."""
        ids = set(self.clans)
        for tag in tags:
            ids.intersection_update(self.clans_by_tag.get(tag, frozenset()))
        return tuple(
            clan
            for clan in self.clans.values()
            if clan.id in ids
            and (include_system or clan.normal_spawn)
            and (family_id is None or clan.family_id == family_id)
            and (
                tier is None
                or any(self.members[mid].min_tier <= tier <= self.members[mid].max_tier for mid in clan.member_ids)
            )
        )
