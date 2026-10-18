"""Eligibility results; no combat snapshots or squad selection decisions."""

from dataclasses import dataclass
from typing import Literal

from src.backend.features.monsters.catalog.contracts import MemberDefinition
from src.backend.features.monsters.catalog.search import MonsterSearchFilters
from src.backend.features.monsters.instances.dto.build_readiness import MonsterBuildReadinessDTO


@dataclass(frozen=True, slots=True)
class MonsterCandidateSearchResultDTO:
    tier: int
    filters: MonsterSearchFilters
    candidates: tuple[MemberDefinition, ...]
    excluded: tuple[MonsterBuildReadinessDTO, ...]
    # IDs not matched under these filters, not necessarily nonexistent IDs.
    unmatched_member_ids: tuple[str, ...]

    @property
    def matched_count(self) -> int:
        return len(self.candidates) + len(self.excluded)

    @property
    def empty_reason(self) -> Literal["no_catalog_matches", "no_ready_candidates"] | None:
        if self.candidates:
            return None
        return "no_catalog_matches" if self.matched_count == 0 else "no_ready_candidates"
