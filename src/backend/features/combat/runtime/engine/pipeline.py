from typing import Any

from src.backend.features.combat.dto import (
    ActorSnapshot,
    CombatMoveDTO,
    InteractionResultDTO,
    PipelineContextDTO,
)
from src.backend.features.combat.dto.pipeline import FeintActivationOutcomeDTO
from src.backend.features.combat.runtime.engine.ability_service import AbilityService
from src.backend.features.combat.runtime.engine.context_builder import ContextBuilder
from src.backend.features.combat.runtime.engine.execution import StrikeExecution, normalize_execution
from src.backend.features.combat.runtime.engine.mechanics_service import (
    MechanicsService,
)
from src.backend.features.combat.runtime.engine.resolver import CombatResolver
from src.backend.features.combat.runtime.engine.stats_engine import StatsEngine


class CombatPipeline:
    """Resolve one combat interaction through the inner combat pipeline.

    The pipeline is the semantic core of a single interaction. It builds the
    pipeline context, lets abilities mutate pre/post-calculation state, ensures
    actor stats exist, delegates pure hit/damage math to the resolver, and then
    applies concrete runtime consequences through the mechanics layer.
    """

    def __init__(self):
        self.ability_service = AbilityService()
        self.mechanics_service = MechanicsService()
        # Resolver и ContextBuilder - статические/без состояния

    async def calculate(
        self,
        source: ActorSnapshot,
        target: ActorSnapshot | None,
        move: CombatMoveDTO | StrikeExecution,
        exchange_count: int = 0,
        external_mods: dict[str, Any] | None = None,
    ) -> InteractionResultDTO:
        """Run the full interaction pipeline for one source-target pair.

        Args:
            source: Acting combat snapshot.
            target: Target combat snapshot, when the interaction has one.
            move: Runtime move DTO being resolved.
            exchange_count: Current exchange counter for the acting snapshot.
            external_mods: Runtime-only branch modifiers injected by the executor.

        Returns:
            A fully populated interaction result with checks, events, and applied
            outcome data.
        """
        # Remove expired/future raw contributions before pre-calc can clean their owners.
        StatsEngine.sync_effect_modifiers([actor for actor in (source, target) if actor is not None])

        # 0. Context Build
        # ContextBuilder создает ctx и инициализирует ctx.result (заполняет ID и hand)
        execution = normalize_execution(
            move,
            source_id=source.char_id,
            target_id=target.char_id if target else None,
            external_mods=external_mods,
        )
        ctx = ContextBuilder.build_context(source, target, execution, execution.context_mods(external_mods))
        ctx.result.action_facts["execution"] = execution.provenance()

        # 1. Pre-Calculation (Ability Service)
        if ctx.phases.run_pre_calc:
            # AbilityService теперь берет result из ctx.result
            self.ability_service.pre_process(ctx, execution, source, target, feint_mode=execution.feint_mode)
        if execution.activation and ctx.result.feint_activation is None:
            activation = execution.activation
            ctx.result.feint_activation = FeintActivationOutcomeDTO(
                owner_id=activation.owner_id,
                intent_id=activation.intent_id,
                feint_id=activation.feint_id,
                state="rejected",
                reason=ctx.result.skip_reason or "NOT_ACTIVATED",
            )

        # 1.5. Liveness Check (Управление флагами)
        if ctx.phases.run_calculator:
            self._check_liveness(ctx, source, target)

        # 2. Stats Calculation (Stats Engine)
        if ctx.phases.run_calculator:
            StatsEngine.ensure_stats(source)
            if target:
                StatsEngine.ensure_stats(target)

        # 3. Calculator (Resolver)
        if ctx.phases.run_calculator and target and source.stats and target.stats:
            # Resolver работает напрямую с ctx.result
            CombatResolver.resolve_exchange(source.stats, target.stats, ctx)

        # 4. Post-Calculation (Ability Service)
        if ctx.phases.run_post_calc:
            # AbilityService использует ctx.result
            self.ability_service.post_process(ctx, source, target, execution)

        if (
            ctx.result.feint_activation
            and ctx.result.chain_events.preserve_feint
            and ctx.result.feint_activation.state == "activated"
        ):
            ctx.result.feint_activation.state = "preserved"
            ctx.result.feint_activation.reason = ctx.result.skip_reason
        return ctx.result

    def _check_liveness(self, ctx: PipelineContextDTO, source: ActorSnapshot, target: ActorSnapshot | None) -> None:
        """Disable expensive phases when either side is already dead."""
        if not source.is_alive:
            ctx.phases.run_calculator = False
            ctx.phases.run_post_calc = False
            return

        if target and not target.is_alive:
            ctx.phases.run_calculator = False
            ctx.phases.run_post_calc = False
