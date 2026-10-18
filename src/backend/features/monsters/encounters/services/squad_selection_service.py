"""Bounded, seeded squad selection from monster-owned preparation policies."""

from datetime import UTC, datetime
from random import Random
from time import perf_counter
from uuid import uuid4

from loguru import logger

from src.backend.features.monsters.encounters.dto.result import (
    MonsterEncounterSelectionDTO,
    MonsterSquadSelectionAttemptDTO,
)
from src.backend.features.monsters.encounters.dto.selection import (
    MonsterEncounterOrderDTO,
    MonsterSquadAssemblyInputDTO,
    MonsterSquadMemberDTO,
    MonsterSquadRejectionReasonDTO,
    MonsterSquadSelectionDTO,
)

from .encounter_preparation_service import MonsterEncounterPreparationService
from .variant_pool import MonsterEncounterVariantPoolDTO


def _key(member: MonsterSquadMemberDTO) -> tuple:
    return member.member_id, member.tier, member.role, member.clan_id, member.family_id


def _reason(code: str, path: str, message: str) -> MonsterSquadRejectionReasonDTO:
    return MonsterSquadRejectionReasonDTO(code=code, path=path, message=message)


def _pool_rosters(*, rules, pool, min_count, max_count, budget, allow_repeated_members, rng=None):
    """Bounded dynamic program by role counts and spent points, with one witness."""
    rules = tuple(sorted(rules, key=lambda r: r.role))
    indices = {rule.role: i for i, rule in enumerate(rules)}
    choices = list(pool)
    if rng is not None:
        rng.shuffle(choices)
    states: dict[tuple[tuple[int, ...], int], tuple[MonsterSquadMemberDTO, ...]] = {((0,) * len(rules), 0): ()}
    if allow_repeated_members:
        groups = [choices] * max_count
    else:
        identities: dict[str, list[MonsterSquadMemberDTO]] = {}
        for member in choices:
            identities.setdefault(member.member_id, []).append(member)
        groups = list(identities.values())
    for group in groups:
        group = list(group)
        if rng is not None:
            rng.shuffle(group)
        updated = dict(states)
        for (counts, spent), roster in states.items():
            if sum(counts) >= max_count:
                continue
            for member in group:
                i = indices[member.role]
                if counts[i] >= rules[i].max_count or spent + member.assembly_cost > budget:
                    continue
                if not allow_repeated_members and any(m.member_id == member.member_id for m in roster):
                    continue
                following = list(counts)
                following[i] += 1
                updated.setdefault((tuple(following), spent + member.assembly_cost), (*roster, member))
        states = updated
    return {
        key: value
        for key, value in states.items()
        if min_count <= sum(key[0]) <= max_count
        and all(count >= rule.min_count for count, rule in zip(key[0], rules, strict=True))
    }


def _failure_reasons(config, pool):
    reasons = []
    for rule in config.roles:
        if rule.min_count and not any(m.role == rule.role for m in pool):
            reasons.append(
                _reason("core_unavailable", f"core.{rule.role}", f"Required {rule.role} is unavailable in this clan.")
            )
    if not reasons:
        for name in ("minions", "seniors"):
            rules = tuple(r for r in config.roles if (r.role == "minion") == (name == "minions"))
            if not rules:
                continue
            possible = _pool_rosters(
                rules=rules,
                pool=tuple(m for m in pool if (m.role == "minion") == (name == "minions")),
                min_count=sum(r.min_count for r in rules),
                max_count=config.count.max_count,
                budget=getattr(config, name).effective_points,
                allow_repeated_members=config.allow_repeated_members,
            )
            if not possible:
                reasons.append(
                    _reason(
                        "budget_insufficient",
                        name,
                        f"The {name} pool cannot fund its required minimum; points cannot transfer between pools.",
                    )
                )
        if not reasons and config.allow_repeated_members:
            reasons.append(
                _reason(
                    "squad_minimum_unaffordable",
                    "count",
                    "Independent pools cannot fill the overall minimum squad size within allowed ranks and member ceiling.",
                )
            )
    if not reasons and not config.allow_repeated_members and len({m.member_id for m in pool}) < config.count.min_count:
        reasons.append(
            _reason(
                "insufficient_distinct_members", "candidates", "Distinct candidates cannot fill the minimum squad size."
            )
        )
    if not reasons:
        reasons.append(
            _reason(
                "budget_insufficient",
                "budget",
                "Independent minion/senior pools or member ceiling cannot satisfy required ranks and accompaniment.",
            )
        )
    return tuple(reasons)


class MonsterEncounterSelectionService:
    def __init__(self, *, preparation: MonsterEncounterPreparationService | None = None):
        self._preparation = preparation if preparation is not None else MonsterEncounterPreparationService()

    def select(self, order: MonsterEncounterOrderDTO) -> MonsterEncounterSelectionDTO:
        if not isinstance(order, MonsterEncounterOrderDTO):
            raise TypeError("order must be MonsterEncounterOrderDTO")
        started = perf_counter()
        # Operational identity is independent of the seeded selection RNG.
        operation_log = logger.bind(
            selection_id=str(uuid4()),
            requested_at=datetime.now(UTC).isoformat(),
            encounter_type=order.encounter_type,
            location_tier=order.location_tier,
            family_ids=list(order.family_ids),
            seed=order.seed,
            difficulty=order.difficulty,
            party_mode=order.party_mode,
            player_gear_score=order.player_gear_score,
            profile_override=order.profile_override.model_dump() if order.profile_override else None,
        )
        operation_log.debug("MonsterEncounterSelectionRequested")
        try:
            result = self._select(order)
        except Exception:
            operation_log.bind(
                completed_at=datetime.now(UTC).isoformat(),
                duration_ms=(perf_counter() - started) * 1000,
                status="failed",
            ).exception("MonsterEncounterSelectionFailed")
            raise
        operation_log.bind(
            completed_at=datetime.now(UTC).isoformat(),
            duration_ms=(perf_counter() - started) * 1000,
            status=result.status,
            configuration_id=result.selection.assembly_input.configuration.id if result.selection else None,
            members=[member.model_dump(mode="json", exclude={"name"}) for member in result.selection.members]
            if result.selection
            else [],
            reason_codes=[reason.code for reason in result.reasons],
            selection_strategy=result.selection_strategy,
            profile_source=result.profile_source,
            profile_id=result.profile_id,
            variant_id=result.variant_id,
            minions=result.minions.model_dump() if result.minions else None,
            seniors=result.seniors.model_dump() if result.seniors else None,
            budget_base=result.budget_base,
            budget_bonus=result.budget_bonus,
            budget_effective=result.budget_effective,
            budget_spent=result.budget_spent,
            budget_remaining=result.budget_remaining,
        ).info("MonsterEncounterSelectionCompleted")
        return result

    def cache_identity(self, order: MonsterEncounterOrderDTO) -> str:
        """Resolve only small policy data; never checks equipment readiness."""
        import json
        from hashlib import sha256

        from src.backend.features.monsters.encounters.policies.composition import MonsterCompositionPolicyResolver

        from .variant_pool import semantic_revision

        resolver = MonsterCompositionPolicyResolver()
        profile = resolver.profile(order)
        budgets = None
        if profile is not None and (
            order.player_gear_score is not None
            or all(getattr(profile, n).mode == "fixed" for n in ("minions", "seniors"))
        ):
            configs = resolver.resolve(order=order, profile=profile)
            budgets = [(c.minions.effective_points, c.seniors.effective_points) for c in configs]
        payload = {
            "revision": semantic_revision(),
            "family_ids": order.family_ids,
            "tier": order.location_tier,
            "mode": order.party_mode,
            "difficulty": order.difficulty,
            "type": order.encounter_type,
            "profile": profile.model_dump(mode="json") if profile else None,
            "budgets": budgets,
            "missing_relative_gs": profile is not None and budgets is None,
        }
        return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def build_pool(self, order: MonsterEncounterOrderDTO) -> MonsterEncounterVariantPoolDTO:
        from .variant_pool import MonsterEncounterVariantPoolDTO, VariantGroupDTO, canonical_variants

        prepared = self._preparation.prepare(order)
        common = dict(
            key_identity=self.cache_identity(order),
            status=prepared.status,
            admission=prepared.admission,
            candidates=prepared.candidates,
            excluded=prepared.excluded,
            reasons=prepared.reasons,
            stages=prepared.stages,
        )
        if prepared.status == "rejected":
            return MonsterEncounterVariantPoolDTO(**common)
        attempts = []
        groups = []
        indices = {(m.member_id, m.tier): i for i, m in enumerate(prepared.candidates)}
        for config in sorted(prepared.configurations, key=lambda c: c.id):
            allowed = {r.role for r in config.roles}
            family_pool = tuple(
                sorted(
                    (m for m in prepared.candidates if m.family_id == config.family_id and m.role in allowed), key=_key
                )
            )
            clans = sorted({m.clan_id for m in family_pool}) if config.same_clan else [None]
            for clan in clans or [None]:
                candidates = tuple(m for m in family_pool if clan is None or m.clan_id == clan)
                variants = canonical_variants(config, candidates)
                reasons = () if variants else _failure_reasons(config, candidates)
                attempts.append(
                    MonsterSquadSelectionAttemptDTO(
                        configuration_id=config.id, clan_id=clan, feasible=bool(variants), reasons=reasons
                    )
                )
                if variants:
                    groups.append(
                        VariantGroupDTO(
                            configuration_id=config.id,
                            clan_id=clan,
                            candidates=tuple(indices[(m.member_id, m.tier)] for m in candidates),
                            variants=tuple(tuple(indices[ref] for ref in roster) for roster in variants),
                        )
                    )
        return MonsterEncounterVariantPoolDTO(**common, groups=tuple(groups), attempts=tuple(attempts))

    def select_from_pool(
        self, order: MonsterEncounterOrderDTO, artifact: MonsterEncounterVariantPoolDTO
    ) -> MonsterEncounterSelectionDTO:
        from src.backend.features.monsters.encounters.dto.preparation import MonsterEncounterPreparationDTO
        from src.backend.features.monsters.encounters.policies.composition import MonsterCompositionPolicyResolver

        if artifact.key_identity != self.cache_identity(order):
            raise ValueError("variant pool identity differs from current order policy/budgets")
        resolver = MonsterCompositionPolicyResolver()
        profile = resolver.profile(order)
        configurations = (
            resolver.resolve(order=order, profile=profile)
            if artifact.status == "prepared" and profile is not None
            else ()
        )
        prepared = MonsterEncounterPreparationDTO(
            status=artifact.status,
            order=order,
            profile=profile,
            profile_source="external" if order.profile_override else "builtin",
            admission=artifact.admission,
            configurations=configurations,
            candidates=artifact.candidates,
            excluded=artifact.excluded,
            reasons=artifact.reasons,
            stages=artifact.stages,
        )
        if prepared.status == "rejected":
            return MonsterEncounterSelectionDTO(
                status="rejected",
                preparation=prepared,
                reasons=tuple(_reason(r.code, r.path, r.message) for r in prepared.reasons),
            )
        if not artifact.groups:
            config = configurations[0]
            return MonsterEncounterSelectionDTO(
                status="rejected",
                preparation=prepared,
                attempts=artifact.attempts,
                profile_source=prepared.profile_source,
                profile_id=profile.id,
                minions=config.minions,
                seniors=config.seniors,
                budget_base=config.budget_base,
                budget_bonus=config.budget_bonus,
                budget_effective=config.budget_effective,
                reasons=(
                    _reason(
                        "constraints_unsatisfiable",
                        "configurations",
                        "No configuration and clan can form a complete squad; see attempts.",
                    ),
                ),
            )
        rng = Random(order.seed)
        group = rng.choice(artifact.groups)
        config = next(c for c in configurations if c.id == group.configuration_id)
        members = tuple(
            sorted(
                (artifact.candidates[i] for i in rng.choice(group.variants)),
                key=lambda member: (member.role == "minion", member.member_id, member.tier),
            )
        )
        candidates = tuple(artifact.candidates[i] for i in group.candidates)
        selection = MonsterSquadSelectionDTO(
            assembly_input=MonsterSquadAssemblyInputDTO(
                order=order, admission=prepared.admission, configuration=config, candidates=candidates
            ),
            members=members,
        )
        spent = sum(m.assembly_cost for m in members)
        diagnostics = {}
        for name in ("minions", "seniors"):
            budget = getattr(config, name)
            used = sum(m.assembly_cost for m in members if (m.role == "minion") == (name == "minions"))
            diagnostics[name] = budget.model_copy(
                update={"spent_points": used, "remaining_points": budget.effective_points - used}
            )
        return MonsterEncounterSelectionDTO(
            status="selected",
            preparation=prepared,
            selection=selection,
            attempts=artifact.attempts,
            selection_strategy="point_budget",
            profile_source=config.profile_source,
            profile_id=config.profile_id,
            variant_id=config.variant_id,
            budget_base=config.budget_base,
            budget_bonus=config.budget_bonus,
            budget_effective=config.budget_effective,
            **diagnostics,
            budget_spent=spent,
            budget_remaining=config.budget_effective - spent,
        )

    def _select(self, order: MonsterEncounterOrderDTO) -> MonsterEncounterSelectionDTO:
        return self.select_from_pool(order, self.build_pool(order))
