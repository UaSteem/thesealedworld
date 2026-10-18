"""Prepare monster-owned policy and buildable candidates; no roster selection."""

from typing import Literal

from src.backend.features.monsters.catalog.search import MonsterSearchFilters
from src.backend.features.monsters.encounters.dto.preparation import (
    MonsterEncounterPreparationDTO,
    MonsterPreparationReasonDTO,
    MonsterPreparationStageDTO,
)
from src.backend.features.monsters.encounters.dto.selection import MonsterEncounterOrderDTO, MonsterSquadMemberDTO
from src.backend.features.monsters.encounters.policies.admission import MonsterAdmissionPolicyResolver
from src.backend.features.monsters.encounters.policies.composition import MonsterCompositionPolicyResolver

from .candidate_search_service import MonsterCandidateSearchService


class MonsterEncounterPreparationService:
    def __init__(
        self,
        *,
        candidate_search: MonsterCandidateSearchService | None = None,
        admission: MonsterAdmissionPolicyResolver | None = None,
        composition: MonsterCompositionPolicyResolver | None = None,
    ):
        self._search = candidate_search if candidate_search is not None else MonsterCandidateSearchService()
        self._admission = admission if admission is not None else MonsterAdmissionPolicyResolver()
        self._composition = composition if composition is not None else MonsterCompositionPolicyResolver()

    def prepare(self, order: MonsterEncounterOrderDTO) -> MonsterEncounterPreparationDTO:
        if not isinstance(order, MonsterEncounterOrderDTO):
            raise TypeError("order must be MonsterEncounterOrderDTO")
        stages = [
            MonsterPreparationStageDTO(
                name="order", status="completed", detail="Order validated; seed recorded without random selection."
            )
        ]

        def stage(name, status, detail):
            stages.append(MonsterPreparationStageDTO(name=name, status=status, detail=detail))

        if order.party_mode == "group":
            stage("admission", "rejected", "Group profiles are not implemented.")
            stage("candidates", "skipped", "Group profile unavailable.")
            stage("composition", "skipped", "Group profile unavailable.")
            return MonsterEncounterPreparationDTO(
                status="rejected",
                order=order,
                stages=tuple(stages),
                reasons=(
                    MonsterPreparationReasonDTO(
                        stage="admission",
                        code="group_profile_unavailable",
                        path="order.party_mode",
                        message="Групповой профиль пока не разработан. Соло-профиль не подставляется.",
                    ),
                ),
            )
        if order.profile_override is None and not self._composition.supports(order.encounter_type):
            stage("admission", "rejected", "Unknown encounter type.")
            stage("candidates", "skipped", "No admission policy resolved.")
            stage("composition", "skipped", "Unknown encounter type.")
            return MonsterEncounterPreparationDTO(
                status="rejected",
                order=order,
                stages=tuple(stages),
                reasons=(
                    MonsterPreparationReasonDTO(
                        stage="admission",
                        code="unknown_encounter_type",
                        path="order.encounter_type",
                        message="Unknown encounter type.",
                    ),
                ),
            )
        profile = self._composition.profile(order)
        if (
            profile is not None
            and order.player_gear_score is None
            and any(getattr(profile, name).mode == "relative_gs" for name in ("minions", "seniors"))
        ):
            stage("composition", "rejected", "Relative budget requires player GS.")
            return MonsterEncounterPreparationDTO(
                status="rejected",
                order=order,
                profile=profile,
                profile_source="external" if order.profile_override else "builtin",
                stages=tuple(stages),
                reasons=(
                    MonsterPreparationReasonDTO(
                        stage="order",
                        code="player_gear_score_required",
                        path="order.player_gear_score",
                        message="Для относительного бюджета требуется GS игрока.",
                    ),
                ),
            )
        admission = self._admission.resolve(order.location_tier)
        stage("admission", "completed", "Monster-owned location admission resolved.")
        filters = MonsterSearchFilters(family_ids=order.family_ids)
        candidates, excluded = [], []
        matched = 0
        tiers = sorted({tier for rule in admission.roles for tier in range(rule.min_tier, rule.max_tier + 1)})
        for tier in tiers:
            eligible_roles = {rule.role for rule in admission.roles if rule.min_tier <= tier <= rule.max_tier}
            result = self._search.search(tier=tier, filters=filters)
            for member in result.candidates:
                if member.role not in eligible_roles:
                    continue
                matched += 1
                candidates.append(
                    MonsterSquadMemberDTO(
                        member_id=member.id,
                        family_id=member.family_id,
                        clan_id=member.clan_id,
                        variant_id=member.variant_id,
                        role=member.role,
                        tier=tier,
                        name=member.name,
                        assembly_cost=member.assembly_cost,
                    )
                )
            # Resolve exclusion roles through the same catalog without a second eligibility search.
            if result.excluded:
                for report in result.excluded:
                    if self._search.get_member(report.member_id).role in eligible_roles:
                        matched += 1
                        excluded.append(report)
        if not candidates:
            code: Literal["no_candidates", "no_ready_candidates"] = (
                "no_candidates" if matched == 0 else "no_ready_candidates"
            )
            stage("candidates", "rejected", "No eligible buildable candidates.")
            stage("composition", "skipped", "No ready candidate pool.")
            return MonsterEncounterPreparationDTO(
                status="rejected",
                order=order,
                admission=admission,
                excluded=tuple(excluded),
                stages=tuple(stages),
                reasons=(
                    MonsterPreparationReasonDTO(
                        stage="candidates",
                        code=code,
                        path="candidates",
                        message="No catalog matches." if matched == 0 else "All eligible candidates failed readiness.",
                    ),
                ),
            )
        stage("candidates", "completed", f"{len(candidates)} ready candidate entries; {len(excluded)} exclusions.")
        configurations = self._composition.resolve(order=order, profile=profile) if profile is not None else ()
        if not configurations:
            stage("composition", "rejected", "No composition configuration for the available families.")
            return MonsterEncounterPreparationDTO(
                status="rejected",
                order=order,
                admission=admission,
                candidates=tuple(candidates),
                excluded=tuple(excluded),
                stages=tuple(stages),
                reasons=(
                    MonsterPreparationReasonDTO(
                        stage="composition",
                        code="configuration_unavailable",
                        path="configurations",
                        message="No composition configuration for the available families.",
                    ),
                ),
            )
        stage(
            "composition", "completed", "Configurations resolved; roster feasibility and selection are not performed."
        )
        return MonsterEncounterPreparationDTO(
            status="prepared",
            order=order,
            admission=admission,
            candidates=tuple(candidates),
            excluded=tuple(excluded),
            configurations=configurations,
            profile=profile,
            profile_source="external" if order.profile_override is not None else "builtin",
            stages=tuple(stages),
        )
