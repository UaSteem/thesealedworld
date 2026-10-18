"""Bridge catalog eligibility and instance readiness without selecting a squad."""

from src.backend.features.monsters.catalog.contracts import MemberDefinition
from src.backend.features.monsters.catalog.indexes import MonsterCatalog
from src.backend.features.monsters.catalog.search import CatalogSearchService, MonsterSearchFilters
from src.backend.features.monsters.encounters.dto.candidate_search import MonsterCandidateSearchResultDTO
from src.backend.features.monsters.instances.runtime.tier_scaling import TIER_SCALING_CONFIG
from src.backend.features.monsters.instances.services.build_readiness import MonsterBuildReadinessService


class MonsterCandidateSearchService:
    def __init__(
        self,
        catalog: MonsterCatalog | None = None,
        readiness: MonsterBuildReadinessService | None = None,
    ) -> None:
        self._catalog = catalog
        self._readiness = readiness if readiness is not None else MonsterBuildReadinessService()

    def get_member(self, member_id: str) -> MemberDefinition:
        """Resolve an exclusion identity against the exact catalog used by search."""
        if self._catalog is not None:
            return self._catalog.members[member_id]
        from src.backend.features.monsters.catalog.registry import get_catalog

        return get_catalog().members[member_id]

    def search(self, *, tier: int, filters: MonsterSearchFilters | None = None) -> MonsterCandidateSearchResultDTO:
        if type(tier) is not int or tier not in TIER_SCALING_CONFIG:
            raise ValueError(f"Unsupported instance tier: {tier!r}")
        filters = filters if filters is not None else MonsterSearchFilters()
        if not isinstance(filters, MonsterSearchFilters):
            raise TypeError("filters must be MonsterSearchFilters")
        catalog = self._catalog
        if catalog is None:
            from src.backend.features.monsters.catalog.registry import get_catalog

            catalog = get_catalog()
        matches = CatalogSearchService(catalog).search(filters)
        candidates = []
        excluded = []
        for member in matches:
            report = self._readiness.check(member=member, family=catalog.families[member.family_id], tier=tier)
            if report.ready:
                candidates.append(member)
            else:
                excluded.append(report)
        matched_ids = {member.id for member in matches}
        unmatched = tuple(dict.fromkeys(member_id for member_id in filters.member_ids if member_id not in matched_ids))
        return MonsterCandidateSearchResultDTO(tier, filters, tuple(candidates), tuple(excluded), unmatched)
