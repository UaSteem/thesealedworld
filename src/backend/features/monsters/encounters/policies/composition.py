"""Resolve one common point profile, never legacy organization-specific profiles."""

from decimal import ROUND_FLOOR, Decimal, localcontext

from src.backend.features.monsters.encounters.dto.selection import (
    MonsterSquadConfigurationDTO,
    MonsterSquadCountDTO,
    MonsterSquadRoleRuleDTO,
)
from src.backend.features.monsters.encounters.profiles.registry import get_profile

ENCOUNTER_PROFILE_KINDS = {kind: kind for kind in ("ordinary", "patrol", "guard", "leader")}


class MonsterCompositionPolicyResolver:
    def supports(self, encounter_type: str) -> bool:
        return encounter_type in ENCOUNTER_PROFILE_KINDS

    def profile(self, order):
        if order.profile_override is not None:
            return order.profile_override
        profile = get_profile(order.party_mode, order.encounter_type, order.difficulty, order.location_tier)
        if profile is not None and order.family_ids == ("goblin_tribe",):
            profile = profile.model_copy(
                update={"min_members": max(3, profile.min_members), "max_members": min(6, profile.max_members)}
            )
        return profile

    def resolve(self, *, order, profile):
        from src.backend.features.monsters.encounters.profiles.contracts import MonsterPoolBudgetDTO

        pools = {}
        for name in ("minions", "seniors"):
            budget = getattr(profile, name)
            steps = 0
            ratio = None
            if budget.mode == "relative_gs":
                if order.player_gear_score is None:
                    raise ValueError("relative_gs budget requires player_gear_score")
                with localcontext() as context:
                    context.prec = 700
                    exact_ratio = Decimal(str(order.player_gear_score)) / Decimal(str(budget.reference_gs))
                    ratio = float(min(exact_ratio, Decimal("1.7976931348623157e308")))
                    effective = int(
                        min(
                            Decimal(budget.base_points) * exact_ratio, Decimal(budget.base_points + budget.gs_bonus_max)
                        ).to_integral_value(rounding=ROUND_FLOOR)
                    )
                scaled = min(budget.base_points, effective)
                bonus = max(0, effective - budget.base_points)
            else:
                if order.player_gear_score is not None:
                    with localcontext() as context:
                        context.prec = 700
                        growth = max(
                            Decimal(0), Decimal(str(order.player_gear_score)) - Decimal(str(budget.gs_threshold))
                        )
                        steps = int(
                            (growth / Decimal(str(budget.gs_step_size))).to_integral_value(rounding=ROUND_FLOOR)
                        )
                bonus = min(steps * budget.gs_points_per_step, budget.gs_bonus_max)
                scaled = budget.base_points
                effective = scaled + bonus
            pools[name] = MonsterPoolBudgetDTO(
                **budget.model_dump(),
                player_gs_ratio=ratio,
                scaled_points=scaled,
                gs_steps=steps,
                gs_cap_reached=budget.gs_bonus_max > 0 and bonus == budget.gs_bonus_max,
                bonus_points=bonus,
                effective_points=effective,
                remaining_points=effective,
            )
        primary = pools["minions"]
        return (
            MonsterSquadConfigurationDTO(
                id=f"{profile.id}.ranks",
                family_id=order.family_ids[0],
                encounter_type=order.encounter_type,
                count=MonsterSquadCountDTO(min_count=profile.min_members, max_count=profile.max_members),
                roles=tuple(MonsterSquadRoleRuleDTO(**rule.model_dump()) for rule in profile.roles),
                allow_repeated_members=profile.allow_repeated_members,
                difficulty=order.difficulty,
                party_mode=order.party_mode,
                profile_source="external" if order.profile_override is not None else "builtin",
                profile_id=profile.id,
                variant_id="ranks",
                **pools,
                gs_threshold=primary.gs_threshold,
                gs_step_size=primary.gs_step_size,
                gs_steps=primary.gs_steps,
                gs_points_per_step=sum(p.gs_points_per_step for p in pools.values()),
                gs_bonus_max=sum(p.gs_bonus_max for p in pools.values()),
                gs_cap_reached=all(p.gs_bonus_max == 0 or p.gs_cap_reached for p in pools.values()),
                budget_base=sum(p.base_points for p in pools.values()),
                budget_bonus=sum(p.bonus_points for p in pools.values()),
                budget_effective=sum(p.effective_points for p in pools.values()),
            ),
        )
