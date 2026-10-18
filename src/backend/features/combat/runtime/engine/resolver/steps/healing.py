"""Healing step."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.backend.features.combat.dto.pipeline import CombatEventDTO, CombatResourceApplicationDTO
from src.backend.features.combat.runtime.engine.math_core import MathCore
from src.backend.features.combat.runtime.engine.received_healing import received_healing_amount

from ._base import ResolverStep

if TYPE_CHECKING:
    from src.backend.features.combat.dto.actor import ActorStats
    from src.backend.features.combat.dto.pipeline import InteractionResultDTO, PipelineContextDTO


class HealingStep(ResolverStep):
    __slots__ = ()

    def is_enabled(self, ctx: PipelineContextDTO) -> bool:
        return ctx.stages.calculate_healing

    def run(
        self,
        atk: ActorStats,
        def_: ActorStats,
        ctx: PipelineContextDTO,
        res: InteractionResultDTO,
    ) -> float:
        if not ctx.stages.calculate_healing:
            return 0.0

        source_id = res.source_id if res.source_id is not None else "0"
        target_id = res.target_id if res.target_id is not None else "0"

        if ctx.override_damage:
            min_h, max_h = ctx.override_damage
        else:
            base = atk.mods.magical_damage
            min_h = base * 0.9
            max_h = base * 1.1

        raw_healing = MathCore.random_range(min_h, max_h)

        if res.is_crit:
            raw_healing *= 1.5
            res.crit_mult = 1.5

        final_healing = received_healing_amount(raw_healing, def_)
        res.healing_final = final_healing
        res.resource_applications.append(
            CombatResourceApplicationDTO(
                actor_id=target_id,
                owner="source" if source_id == target_id else "target",
                resource="hp",
                reason="heal",
                value=f"+{final_healing}",
                tags=["heal"],
            )
        )

        tags = []
        if res.is_crit:
            tags.append("CRIT")
        res.events.append(
            CombatEventDTO(
                type="HEAL",
                source_id=source_id,
                target_id=target_id,
                value=final_healing,
                resource="hp",
                tags=tags,
            )
        )

        return float(final_healing)


healing_step = HealingStep()
