import asyncio
import time
from collections.abc import Awaitable
from typing import Any, cast

from loguru import logger as log

from src.backend.features.combat.dto.action import CombatActionDTO, CombatMoveDTO
from src.backend.features.combat.dto.actor import ActorSnapshot
from src.backend.features.combat.dto.ids import ActorId, ActorIdLike, normalize_actor_id
from src.backend.features.combat.dto.pipeline import (
    CombatEffectFactDTO,
    CombatEventDTO,
    CombatResourceApplicationDTO,
    InteractionResultDTO,
    PipelineContextDTO,
    TacticalTransitionFactDTO,
)
from src.backend.features.combat.dto.session import BattleContext, TargetReturnDTO
from src.backend.features.combat.integrations import CombatCatalogIntegrator
from src.backend.features.combat.runtime.ai.ai_memory import record_exchange_outcome
from src.backend.features.combat.runtime.engine.ability_service import AbilityService
from src.backend.features.combat.runtime.engine.execution import StrikeExecution
from src.backend.features.combat.runtime.engine.feint_service import FeintService
from src.backend.features.combat.runtime.engine.pipeline import CombatPipeline
from src.backend.features.combat.runtime.engine.ranged_position import RangedPositionService
from src.backend.features.combat.runtime.engine.stats_engine import StatsEngine
from src.backend.features.combat.runtime.engine.tactical_state import TacticalStateService
from src.backend.features.combat.runtime.engine.target_resolver import TargetResolver
from src.backend.features.combat.runtime.support import (
    CombatAnalyticsFactBuilder,
    CombatLogBuilder,
    CombatResultSupportTaskDTO,
)
from src.backend.features.game_catalog.combat.resources.common.targeting import TargetType

InteractionPair = tuple[ActorSnapshot, ActorSnapshot | None, InteractionResultDTO]


class CombatExecutor:
    """Execute runnable combat actions inside an in-memory battle context.

    The executor is the runtime stage that owns combat action routing after
    collector matchmaking has already happened. It resolves exchange and
    unidirectional actions through ``CombatPipeline``, accumulates logs/support
    payloads, marks dead actors, and prepares target returns for commit.

    It does not fetch Redis state, acquire locks, or enqueue ARQ jobs directly.
    Those concerns stay in the executor task and integration layers.
    """

    def __init__(self):
        self.pipeline = CombatPipeline()
        self.target_resolver = TargetResolver()

    async def process_batch(self, ctx: BattleContext, actions: list[CombatActionDTO]) -> list[str]:
        """Process one executor batch against a loaded battle context.

        Args:
            ctx: Mutable in-memory battle context for the current executor run.
            actions: Runnable combat actions already prepared by the collector.

        Returns:
            List of move ids that were consumed from the action queue, even when
            individual actions failed after validation.
        """
        processed_ids = []

        for action in actions:
            try:
                await self._process_single_action(ctx, action)
                processed_ids.append(action.move.move_id)
            except Exception:  # noqa: BLE001
                log.bind(move_id=action.move.move_id).exception("ExecutorActionFailed")
                processed_ids.append(action.move.move_id)

        # Сбор мертвых акторов после обработки батча
        self._collect_dead_actors(ctx)

        return processed_ids

    async def _process_single_action(self, ctx: BattleContext, action: CombatActionDTO) -> None:
        """Route one runnable combat action into the correct executor branch."""
        if not action.move:
            log.warning("ExecutorActionMissingMoveData")
            return

        # Routing Logic
        # payload is object, use getattr
        target_id = getattr(action.move.payload, "target_id", None)

        if self._skip_stale_action_if_dead(ctx, action):
            return

        if action.action_type == "exchange" or (action.is_forced and target_id):
            await self._handle_exchange(ctx, action)
        else:
            # Instant / Item (Одностороннее воздействие)
            log.bind(
                session_id=ctx.session_id,
                move_id=action.move.move_id,
                action_type=action.action_type,
                char_id=str(action.move.char_id),
                ability_id=getattr(action.move.payload, "ability_id", None),
                target_id=str(target_id) if target_id else None,
            ).info("ExecutorHandleUnidirectional")
            await self._handle_unidirectional(ctx, action)

    def _skip_stale_action_if_dead(self, ctx: BattleContext, action: CombatActionDTO) -> bool:
        checked = [("source", action.move.char_id), ("target", getattr(action.move.payload, "target_id", None))]
        if action.partner_move:
            checked.extend(
                [
                    ("source", action.partner_move.char_id),
                    ("target", getattr(action.partner_move.payload, "target_id", None)),
                ]
            )

        for role, actor_id in checked:
            if actor_id is None:
                continue
            actor = ctx.get_actor(cast("ActorIdLike", actor_id))
            if actor and not actor.is_alive:
                self._append_stale_action_log(ctx, action, actor=actor, reason=f"{role}_dead")
                return True

        return False

    @staticmethod
    def _append_stale_action_log(
        ctx: BattleContext, action: CombatActionDTO, *, actor: ActorSnapshot, reason: str
    ) -> None:
        actor_name = actor.meta.name or str(actor.meta.id)
        text = f"{actor_name}: цель уже мертва." if reason == "target_dead" else f"{actor_name} уже мертв."
        ctx.pending_logs.append(
            {
                "type": "LOG",
                "kind": "stale_action",
                "reason": reason,
                "text": text,
                "timestamp": time.time(),
                "global_turn": ctx.meta.step_counter,
                "source_id": str(action.move.char_id),
                "target_id": str(getattr(action.move.payload, "target_id", "")),
                "actor": {
                    "id": str(actor.meta.id),
                    "name": actor_name,
                    "team": actor.meta.team,
                    "actor_type": actor.meta.type,
                },
                "tags": ["runtime", "stale_action", "dead_actor"],
            }
        )

    # ==========================================================================
    # 🌿 BRANCHES (Logic Flow)
    # ==========================================================================

    async def _handle_exchange(self, ctx: BattleContext, action: CombatActionDTO) -> None:
        """Resolve one paired or forced exchange.

        Args:
            ctx: Mutable in-memory battle context for the current batch.
            action: Exchange action that may include a partner move or be forced.

        Side Effects:
            - Applies periodic turn-start effects.
            - Resolves one or more combat waves through the pipeline.
            - Appends combat logs and support payloads.
            - Collects target returns and advances global step state.

        Runtime Contract:
            - Collector already decided pairing/force-attack semantics.
            - No Redis I/O is allowed inside this method.
        """
        source = ctx.get_actor(action.move.char_id)
        target_id = getattr(action.move.payload, "target_id", None)
        target = ctx.get_actor(cast("ActorIdLike", target_id)) if target_id else None

        if not source or not target:
            log.bind(char_id=action.move.char_id, target_id=target_id).warning("ExecutorExchangeParticipantsMissing")
            return

        if action.partner_move and action.partner_move.char_id != target.char_id:
            raise ValueError("Partner intent owner must match exchange target")
        StatsEngine.sync_effect_modifiers(list(ctx.actors.values()))
        self._process_periodic_effects(ctx, [source, target], action=action, wave=0)

        # An exchange owns all strike waves; generated reactions never select
        # or activate another actor's intent.
        pending_tasks: list[tuple[StrikeExecution, dict[str, Any]]] = [
            (StrikeExecution.primary(action.move, target.char_id), {"action_mode": "exchange"})
        ]
        if action.partner_move:
            pending_tasks.append(
                (StrikeExecution.primary(action.partner_move, source.char_id), {"action_mode": "exchange"})
            )
        elif not action.is_forced:
            log.error("ExecutorExchangePartnerMissing")
            return

        max_waves = 3
        wave = 0
        used_feints: dict[tuple[str, str], ActorSnapshot] = {}
        all_pairs: list[InteractionPair] = []
        deferred_pairs = []
        incrementing_ids = {str(source.char_id), str(target.char_id)}
        while pending_tasks and wave < max_waves:
            wave += 1
            runnable: list[
                tuple[Awaitable[InteractionResultDTO], ActorSnapshot, ActorSnapshot | None, StrikeExecution]
            ] = []
            for strike, mods in pending_tasks:
                real_source = ctx.get_actor(strike.owner_id)
                real_target = ctx.get_actor(strike.target_id) if strike.target_id is not None else None
                if not real_source or (strike.target_id is not None and not real_target):
                    continue
                runnable.append(
                    (
                        self._create_task(
                            real_source.model_copy(deep=True),
                            real_target.model_copy(deep=True) if real_target else None,
                            strike,
                            mods={**mods, "incrementing_actor_ids": incrementing_ids, "defer_queued_statuses": True},
                        ),
                        real_source,
                        real_target,
                        strike,
                    )
                )
            results = list(await asyncio.gather(*(task for task, *_rest in runnable)))
            pending_tasks = []

            # Project explicit area hits only after the owner's activation
            # succeeded. They still use the same pre-commit wave snapshots, so
            # neither participant's primary result cancels the other's attack.
            secondary_runs = []
            for result, (_task, real_source, _real_target, strike) in zip(results, runnable, strict=True):
                activation = strike.activation
                if not activation or not activation.applied_to(result) or strike.target_id is None:
                    continue
                secondary_targets, damage_mult = self._secondary_feint_plan(
                    ctx,
                    CombatActionDTO(action_type="exchange", move=strike.log_move()),
                    primary_target_id=strike.target_id,
                )
                for secondary_target in secondary_targets:
                    secondary = strike.child("secondary", owner_id=strike.owner_id, target_id=secondary_target.char_id)
                    secondary_runs.append(
                        (
                            self._create_task(
                                real_source.model_copy(deep=True),
                                secondary_target.model_copy(deep=True),
                                secondary,
                                mods={
                                    "action_mode": "unidirectional",
                                    "incrementing_actor_ids": incrementing_ids,
                                    "defer_queued_statuses": True,
                                    "damage_mult": damage_mult,
                                    "feint_role": "secondary",
                                    "pay_cost": False,
                                    "generate_feints": False,
                                },
                            ),
                            real_source,
                            secondary_target,
                            secondary,
                        )
                    )
            if secondary_runs:
                results.extend(await asyncio.gather(*(task for task, *_rest in secondary_runs)))
                runnable.extend(secondary_runs)

            for result, (_task, real_source, real_target, strike) in zip(results, runnable, strict=True):
                if strike.origin != "secondary":
                    self._append_cleave_splash(ctx, result, real_source, real_target)

            commit_pairs = [
                (real_source, real_target, result)
                for result, (_task, real_source, real_target, _strike) in zip(results, runnable, strict=True)
            ]
            all_pairs.extend(commit_pairs)
            for real_source, real_target, result in commit_pairs:
                deferred_pairs.append(self._extract_deferred_statuses(real_source, real_target, result))
            commit_ctx = PipelineContextDTO()
            commit_ctx.flags.meta.action_mode = "exchange"
            commit_ctx.flags.meta.grant_exchange_gift = True
            self.pipeline.mechanics_service.apply_exchange_results(
                commit_ctx,
                commit_pairs,
                actors_by_id={str(actor_id): actor for actor_id, actor in ctx.actors.items()},
            )
            StatsEngine.sync_effect_modifiers(list(ctx.actors.values()))

            for result, (_task, real_source, real_target, strike) in zip(results, runnable, strict=True):
                # Keep support schema stable while preserving provenance in facts.
                result.action_facts["execution"] = strike.provenance()
                result_action = self._action_for_move(action, strike.log_move(), result=result)
                s_id, t_id = result.source_id, result.target_id
                self._append_result_logs(ctx, result, action=result_action, wave=wave)
                self._append_result_support_payload(ctx, result, action=result_action, wave=wave)
                self._log_result_info(ctx, result, wave=wave)
                activation = strike.activation
                if activation:
                    assert strike.intent is not None
                    self._refund_feint_cost_if_needed(ctx, result, strike.intent.move)
                    if activation.applied_to(result):
                        used_feints[(str(real_source.char_id), activation.feint_id)] = real_source
                if s_id is None or t_id is None:
                    log.warning("ExecutorResultActorIdsMissing")
                    continue
                if strike.origin != "secondary":
                    record_exchange_outcome(
                        ctx,
                        s_id,
                        t_id,
                        self._result_outcome(result),
                        activation.feint_id if activation else None,
                    )
                else:
                    continue
                if not real_source.is_alive or not real_target or not real_target.is_alive:
                    continue
                if result.chain_events.trigger_counter_attack:
                    pending_tasks.append(
                        (
                            strike.child("counter", owner_id=t_id, target_id=s_id),
                            {"is_counter_attack": True, "action_mode": "exchange"},
                        )
                    )
                if result.chain_events.trigger_offhand_attack:
                    pending_tasks.append(
                        (
                            strike.child("offhand", owner_id=s_id, target_id=t_id),
                            {"hand": "off", "action_mode": "exchange"},
                        )
                    )

        # --- FINALIZE ---
        regen_result = self.pipeline.mechanics_service.apply_exchange_regen(
            source, target, grant_xp=commit_ctx.flags.mechanics.grant_xp
        )
        if regen_result.resource_facts:
            ctx.pending_logs.append(
                CombatLogBuilder.build_exchange_regen_entry(
                    ctx=ctx, result=regen_result, wave=wave, timestamp=time.time()
                )
            )
            self._append_result_support_payload(ctx, regen_result, action=action, wave=wave)
            self._log_result_info(ctx, regen_result, wave=wave)

        self._finalize_statuses_and_positions(ctx, action, deferred_pairs, all_pairs, (source, target), wave)
        source.meta.exchange_counter += 1
        target.meta.exchange_counter += 1
        ctx.meta.step_counter += 1
        StatsEngine.sync_effect_modifiers(list(ctx.actors.values()))
        self._cleanup_finished_control_effects(ctx, [source, target], action=action, wave=wave)

        self._apply_used_feint_cooldowns(used_feints)
        self._reroll_exchange_feints(source)
        self._reroll_exchange_feints(target)

        # НОВОЕ: Собираем пары для возврата целей
        self._collect_target_returns(ctx, action)

        log.bind(wave_count=wave, global_step=ctx.meta.step_counter).trace("ExecutorExchangeCompleted")

    @staticmethod
    def _action_for_move(
        action: CombatActionDTO,
        move: CombatMoveDTO,
        *,
        result: InteractionResultDTO | None = None,
    ) -> CombatActionDTO:
        result_targets = [result.target_id] if result and result.target_id is not None else move.targets
        move_for_log = move.model_copy(update={"targets": result_targets})
        return CombatActionDTO(
            action_type=action.action_type,
            move=move_for_log,
            partner_move=None,
            is_forced=action.is_forced,
        )

    async def _handle_unidirectional(self, ctx: BattleContext, action: CombatActionDTO) -> None:
        """Resolve an item/instant/system-style one-way action."""
        source = ctx.get_actor(action.move.char_id)
        if not source:
            return

        StatsEngine.sync_effect_modifiers(list(ctx.actors.values()))

        target_ids = action.move.targets or []
        if not target_ids:
            target_ids = self._resolve_unidirectional_targets(ctx, action)
            action.move.targets = list(target_ids)

        # Check for self target in payload
        payload_target = getattr(action.move.payload, "target_id", None)
        if action.move.strategy == "item" and payload_target == "self":
            target_ids = [source.char_id]

        tasks: list[Awaitable[InteractionResultDTO]] = []
        task_sources: list[tuple[ActorSnapshot, ActorSnapshot, CombatMoveDTO, dict[str, Any]]] = []
        mods = {**self._unidirectional_mods(action), "incrementing_actor_ids": set(), "defer_queued_statuses": True}
        for tid in target_ids:
            target = ctx.get_actor(tid)
            if target:
                tasks.append(self._create_task(source, target, action.move, mods=mods))
                task_sources.append((source, target, action.move, mods))

        if tasks:
            results = await asyncio.gather(*tasks)
            deferred_pairs = []
            is_grouped_area_log = CombatLogBuilder._is_area_action(action) and len(results) > 1
            for result, (_source, target_snapshot, _move, _mods) in zip(results, task_sources, strict=False):
                target = ctx.get_actor(result.target_id) if result.target_id is not None else None
                self._append_cleave_splash(ctx, result, source, target_snapshot)
                deferred_pairs.append(self._extract_deferred_statuses(source, target, result))
                commit_ctx = PipelineContextDTO()
                commit_ctx.flags.meta.action_mode = "unidirectional"
                commit_ctx.flags.meta.grant_exchange_gift = False
                self.pipeline.mechanics_service.apply_interaction_result(
                    commit_ctx,
                    source,
                    target,
                    result,
                    actors_by_id={str(actor_id): actor for actor_id, actor in ctx.actors.items()},
                )
                if not is_grouped_area_log:
                    self._append_result_logs(ctx, result, action=action, wave=1)
                self._append_result_support_payload(ctx, result, action=action, wave=1)
                self._log_result_info(ctx, result, wave=1)
            if is_grouped_area_log:
                self._append_area_result_log(ctx, results, action=action, wave=1)
            all_pairs: list[InteractionPair] = [
                (source, target, result)
                for result, (_source, target, _move, _mods) in zip(results, task_sources, strict=True)
            ]
            self._finalize_statuses_and_positions(ctx, action, deferred_pairs, all_pairs, None, 1)
            self._apply_unidirectional_ability_cooldown(source, action, results)
            log.bind(target_count=len(tasks)).info("ExecutorUnidirectionalCompleted")

    # ==========================================================================
    # 🛠️ HELPERS
    # ==========================================================================

    @staticmethod
    def _extract_deferred_statuses(
        source: ActorSnapshot,
        target: ActorSnapshot | None,
        result: InteractionResultDTO,
    ) -> InteractionPair:
        deferred = InteractionResultDTO(
            source_id=result.source_id, target_id=result.target_id, action_facts=dict(result.action_facts)
        )
        deferred.status_applications = [app for app in result.status_applications if app.at_action_end]
        result.status_applications = [app for app in result.status_applications if not app.at_action_end]
        # Position facts describe final persisted state, never a speculative wave roll.
        position_ids = {"ranged_position", "force_ranged_close"}
        deferred.effect_facts = [fact for fact in result.effect_facts if fact.effect_id in position_ids]
        result.effect_facts = [fact for fact in result.effect_facts if fact.effect_id not in position_ids]
        deferred.events = [event for event in result.events if event.action_id == "force_ranged_close"]
        result.events = [event for event in result.events if event.action_id != "force_ranged_close"]
        return source, target, deferred

    def _finalize_statuses_and_positions(
        self,
        ctx: BattleContext,
        action: CombatActionDTO,
        deferred_pairs: list[InteractionPair],
        all_pairs: list[InteractionPair],
        participants: tuple[ActorSnapshot, ActorSnapshot] | None,
        wave: int,
    ) -> None:
        commit_ctx = PipelineContextDTO()
        commit_ctx.flags.meta.action_mode = "exchange" if participants else "unidirectional"
        actors = {str(key): actor for key, actor in ctx.actors.items()}
        initial_positions = {
            key: RangedPositionService.current_position(actor)
            for key, actor in actors.items()
            if RangedPositionService.is_ranged_actor(actor)
        }
        # A status-only commit must not replay damage, cost, tokens, or hand refill.
        mechanics = self.pipeline.mechanics_service
        consumed = {
            (str(removal.actor_id), removal.effect_uid)
            for _source, _target, result in all_pairs
            for removal in result.status_removals
            if removal.effect_uid is not None
        }
        for _source, _target, result in deferred_pairs:
            result.status_applications = [
                app
                for app in result.status_applications
                if not app.active_effect.get("params", {}).get("forced_close")
                or (actors.get(str(app.actor_id)) is not None and actors[str(app.actor_id)].is_alive)
            ]
        mechanics.apply_status_results(commit_ctx, deferred_pairs, actors_by_id=actors, consumed_uids=consumed)
        final = InteractionResultDTO(
            source_id=action.move.char_id, target_id=getattr(action.move.payload, "target_id", None)
        )
        final.action_facts["phase"] = "status_position_finalize"
        for _source, _target, result in deferred_pairs:
            accepted_positions = {
                str(app.actor_id)
                for app in result.status_applications
                if app.effect_id == "ranged_position"
                and any(
                    effect.uid == app.active_effect.get("uid") and effect.params.get("forced_close")
                    for effect in actors[str(app.actor_id)].statuses.effects
                )
            }
            final.status_applications.extend(result.status_applications)
            final.effect_facts.extend(fact for fact in result.effect_facts if str(fact.actor_id) in accepted_positions)
            final.events.extend(event for event in result.events if str(event.target_id) in accepted_positions)
        if participants:
            for participant in participants:
                StatsEngine.ensure_stats(participant)
            TacticalStateService.update_after_exchange(
                all_pairs,
                participants=participants,
                final_result=final,
                seed=f"{ctx.session_id}:{ctx.meta.step_counter}:{action.move.move_id}",
            )
        else:
            # Existing instant force-close is an explicit archer exception: it
            # commits at action end without granting a tactical initiative roll.
            for actor_id, before in initial_positions.items():
                actor = actors[actor_id]
                after = RangedPositionService.current_position(actor)
                if before == after or not actor.is_alive:
                    continue
                effect = next(
                    (
                        e
                        for e in actor.statuses.effects
                        if e.effect_id == "ranged_position"
                        and e.params.get("forced_close")
                        and e.active_from_exchange == actor.meta.exchange_counter
                    ),
                    None,
                )
                if effect is not None:
                    final.tactical_transitions.append(
                        TacticalTransitionFactDTO(
                            actor_id=actor.char_id,
                            style="skill_ranged_combat",
                            before=before,
                            after=after,
                            reason="feint_dislodge",
                            source_action_id=effect.params.get("source_action_id"),
                            source_feint_id=effect.params.get("source_feint_id"),
                        )
                    )
        StatsEngine.sync_effect_modifiers(list(ctx.actors.values()))
        if final.effect_facts or final.tactical_transitions:
            ctx.pending_logs.extend(
                CombatLogBuilder.build_effect_fact_entries(
                    ctx=ctx, result=final, action=action, wave=wave, timestamp=time.time()
                )
            )
            self._append_result_support_payload(ctx, final, action=action, wave=wave)

    def _resolve_unidirectional_targets(self, ctx: BattleContext, action: CombatActionDTO) -> list[ActorId]:
        raw_target = getattr(action.move.payload, "target_id", None)
        ability_id = getattr(action.move.payload, "ability_id", None)
        if ability_id:
            entry = CombatCatalogIntegrator.get_ability_catalog_entry(str(ability_id))
            if entry is not None:
                ability = entry.technical
                target_count = max(1, int(getattr(ability, "target_count", 1) or 1))
                if str(ability.target) == "random_enemy" and target_count > 1:
                    raw_target = f"random_enemy_{target_count}"
                elif str(ability.target) == "all_enemies":
                    raw_target = "all_enemies"
                elif str(ability.target) == "self":
                    raw_target = "self"
        return self.target_resolver.resolve(action.move.char_id, raw_target, ctx.meta)

    def _create_task(
        self,
        source: ActorSnapshot,
        target: ActorSnapshot | None,
        move: CombatMoveDTO | StrikeExecution,
        mods: dict[str, Any] | None = None,
    ) -> Awaitable[InteractionResultDTO]:
        """Create one pipeline calculation task for a concrete source/target pair."""
        return self.pipeline.calculate(
            source=source,
            target=target,
            move=move,
            external_mods=mods,
            exchange_count=source.meta.exchange_counter,
        )

    def _secondary_feint_plan(
        self, ctx: BattleContext, action: CombatActionDTO, *, primary_target_id: ActorId
    ) -> tuple[list[ActorSnapshot], float]:
        feint_id = getattr(action.move.payload, "feint_id", None)
        if not feint_id:
            return [], 0.5

        feint_entry = CombatCatalogIntegrator.get_feint_catalog_entry(str(feint_id))
        if not feint_entry:
            return [], 0.5
        feint_config = feint_entry.technical
        if feint_config.target != TargetType.ALL_ENEMIES or feint_config.target_count <= 1:
            return [], 0.5

        resolved = self.target_resolver.resolve(action.move.char_id, feint_config.target.value, ctx.meta)
        limit = max(0, int(feint_config.target_count) - 1)
        selected: list[ActorSnapshot] = []
        for target_id in resolved:
            if target_id in {action.move.char_id, primary_target_id}:
                continue
            actor = ctx.get_actor(target_id)
            if actor and actor.is_alive:
                selected.append(actor)
            if len(selected) >= limit:
                break
        return selected, max(0.0, float(getattr(feint_config, "secondary_damage_mult", 0.5) or 0.5))

    @staticmethod
    def _unidirectional_mods(action: CombatActionDTO) -> dict[str, Any]:
        mods: dict[str, Any] = {"action_mode": "unidirectional"}
        ability_id = getattr(action.move.payload, "ability_id", None)
        if not ability_id:
            return mods
        entry = CombatCatalogIntegrator.get_ability_catalog_entry(str(ability_id))
        if entry is None:
            return mods
        ability = entry.technical
        if int(getattr(ability, "target_count", 1) or 1) > 1:
            mods["damage_mult"] = max(0.0, float(getattr(ability, "secondary_damage_mult", 1.0) or 1.0))
        return mods

    @staticmethod
    def _apply_unidirectional_ability_cooldown(
        source: ActorSnapshot,
        action: CombatActionDTO,
        results: list[InteractionResultDTO],
    ) -> None:
        ability_id = getattr(action.move.payload, "ability_id", None)
        if not ability_id:
            return
        if any(result.action_facts.get("id") == ability_id and not result.skip_reason for result in results):
            AbilityService.apply_ability_cooldown(source, str(ability_id))

    def _append_cleave_splash(
        self,
        ctx: BattleContext,
        result: InteractionResultDTO,
        source: ActorSnapshot,
        primary_target: ActorSnapshot | None,
    ) -> None:
        if not source.is_alive:
            return
        if not result.is_hit or result.damage_final <= 0:
            return

        StatsEngine.ensure_stats(source)
        if source.stats is None:
            return
        damage_mult = max(0.0, float(source.stats.mods.cleave_damage_mult or 0.0))
        target_count = max(0, int(source.stats.mods.cleave_target_count or 0))
        if damage_mult <= 0 or target_count <= 0:
            return

        damage = int(result.damage_final * damage_mult)
        if damage <= 0:
            return

        excluded = {str(source.char_id)}
        if primary_target is not None:
            excluded.add(str(primary_target.char_id))
        selected: list[ActorSnapshot] = []
        for target_id in self.target_resolver.resolve(source.char_id, TargetType.ALL_ENEMIES.value, ctx.meta):
            if str(target_id) in excluded:
                continue
            target = ctx.get_actor(target_id)
            if target and target.is_alive:
                selected.append(target)
            if len(selected) >= target_count:
                break

        for target in selected:
            result.resource_applications.append(
                CombatResourceApplicationDTO(
                    actor_id=target.char_id,
                    owner="other",
                    resource="hp",
                    reason="cleave_splash",
                    value=f"-{damage}",
                    source_effect_id="cleave",
                    tags=["cleave", "splash"],
                )
            )
            result.events.append(
                CombatEventDTO(
                    type="HIT",
                    source_id=source.char_id,
                    target_id=target.char_id,
                    value=damage,
                    resource="hp",
                    action_id="cleave_splash",
                    tags=["CLEAVE", "SPLASH"],
                )
            )

    def _process_periodic_effects(
        self, ctx: BattleContext, actors: list[Any], *, action: CombatActionDTO, wave: int
    ) -> None:
        """Apply turn-start periodic effects before the main action branch resolves."""
        seen: set[ActorId] = set()
        for actor in actors:
            actor_id = actor.char_id
            if actor_id in seen:
                continue
            seen.add(actor_id)

            tick_ctx = PipelineContextDTO()
            tick_ctx.flags.mechanics.apply_periodic = True
            self.pipeline.mechanics_service.process_turn_start(tick_ctx, actor)
            if tick_ctx.result.events:
                self._append_result_logs(ctx, tick_ctx.result, action=action, wave=wave)
                self._append_result_support_payload(ctx, tick_ctx.result, action=action, wave=wave)
                self._log_result_info(ctx, tick_ctx.result, wave=wave)

    def _cleanup_finished_control_effects(
        self, ctx: BattleContext, actors: list[ActorSnapshot], *, action: CombatActionDTO, wave: int
    ) -> None:
        """Remove effects that expired on the actor's own exchange counter."""
        seen: set[ActorId] = set()
        for actor in actors:
            actor_id = actor.char_id
            if actor_id in seen:
                continue
            seen.add(actor_id)
            expired = [
                effect for effect in actor.statuses.effects if effect.expire_at_exchange <= actor.meta.exchange_counter
            ]
            if not expired:
                continue
            AbilityService._cleanup_expired_effects_pre_calc(actor)
            result = InteractionResultDTO(source_id=action.move.char_id, target_id=actor.char_id)
            for effect in expired:
                effect_entry = CombatCatalogIntegrator.get_effect_catalog_entry(effect.effect_id)
                tags = set(effect_entry.technical.tags) if effect_entry else set()
                result.effect_facts.append(
                    CombatEffectFactDTO(
                        actor_id=actor.char_id,
                        owner="target",
                        effect_id=effect.effect_id,
                        action="expire",
                        source_effect_id=effect.effect_id,
                        tags=sorted(tags),
                    )
                )
            ctx.pending_logs.extend(
                CombatLogBuilder.build_effect_fact_entries(
                    ctx=ctx,
                    result=result,
                    action=action,
                    wave=wave,
                    timestamp=time.time(),
                )
            )

    @staticmethod
    def _refund_feint_cost_if_needed(ctx: BattleContext, result: InteractionResultDTO, move: CombatMoveDTO) -> None:
        if not result.chain_events.preserve_feint:
            return

        feint_id = getattr(move.payload, "feint_id", None)
        if not feint_id:
            return

        source = ctx.get_actor(move.char_id)
        if not source:
            return

        feint_entry = CombatCatalogIntegrator.get_feint_catalog_entry(feint_id)
        if not feint_entry:
            log.bind(feint_id=feint_id).warning("ExecutorFeintRefundFailed")
            return

        feint_config = feint_entry.technical
        FeintService.refund_cost(source.meta, dict(feint_config.cost.tactics))

    @staticmethod
    def _reroll_exchange_feints(actor) -> None:
        hand_size = actor.stats.mods.hand_size if actor.stats else 3
        active_effect_ids = {
            effect.effect_id
            for effect in actor.statuses.effects
            if effect.active_from_exchange <= actor.meta.exchange_counter < effect.expire_at_exchange
        }
        FeintService.reroll_hand(actor.meta, hand_size=hand_size, active_effect_ids=active_effect_ids)

    @staticmethod
    def _apply_used_feint_cooldowns(used_feints: dict[tuple[str, str], ActorSnapshot]) -> None:
        for (_actor_id, feint_id), actor in used_feints.items():
            feint_entry = CombatCatalogIntegrator.get_feint_catalog_entry(feint_id)
            if feint_entry is None:
                continue
            cooldown = sum(max(0, int(amount)) for amount in feint_entry.technical.cost.tactics.values())
            FeintService.apply_cooldown(actor.meta, feint_id, cooldown)

    def _append_result_logs(
        self, ctx: BattleContext, result: InteractionResultDTO, *, action: CombatActionDTO, wave: int
    ) -> None:
        """
        Переносит полный результат резольвера и pipeline events в боевой log buffer.
        """
        ctx.pending_logs.extend(
            CombatLogBuilder.build_result_entries(
                ctx=ctx,
                result=result,
                action=action,
                wave=wave,
                timestamp=time.time(),
            )
        )

    def _append_area_result_log(
        self, ctx: BattleContext, results: list[InteractionResultDTO], *, action: CombatActionDTO, wave: int
    ) -> None:
        entry = CombatLogBuilder.build_area_result_entry(
            ctx=ctx,
            results=results,
            action=action,
            wave=wave,
            timestamp=time.time(),
        )
        if entry is not None:
            ctx.pending_logs.append(entry)

    def _append_result_support_payload(
        self, ctx: BattleContext, result: InteractionResultDTO, *, action: CombatActionDTO, wave: int
    ) -> None:
        ctx.pending_result_support_tasks.append(
            self._result_support_payload(
                ctx=ctx,
                result=result,
                action=action,
                wave=wave,
            )
        )

    @staticmethod
    def _result_support_payload(
        ctx: BattleContext,
        result: InteractionResultDTO,
        *,
        action: CombatActionDTO,
        wave: int,
    ) -> dict[str, Any]:
        return CombatResultSupportTaskDTO.from_context(
            ctx=ctx,
            result=result,
            action=action,
            wave=wave,
            seq=len(ctx.pending_result_support_tasks),
            timestamp=time.time(),
        ).model_dump(mode="json")

    @staticmethod
    def _log_result_info(ctx: BattleContext, result: InteractionResultDTO, *, wave: int) -> None:
        checks = " ".join(
            f"{CombatAnalyticsFactBuilder.STAGES.get(check.stage, check.stage)}{'✓' if check.passed else '×'}"
            for check in result.checks
        )
        log.bind(
            session_id=ctx.session_id,
            turn=ctx.meta.step_counter + 1,
            wave=wave,
            source_id=result.source_id,
            target_id=result.target_id,
            outcome=CombatAnalyticsFactBuilder.OUTCOMES.get(CombatAnalyticsFactBuilder._outcome(result), "N"),
            checks=checks or "-",
            damage=result.damage_final,
            healing=result.healing_final,
            events=[event.type for event in result.events],
        ).trace("CombatExchange")

    def _collect_target_returns(self, ctx: BattleContext, action: CombatActionDTO) -> None:
        """Collect target queue return pairs after a resolved exchange.

        Source regains the target when both survive. The defending target also
        regains the source only when a partner move existed.
        """
        source_id = action.move.char_id
        target_id_raw = getattr(action.move.payload, "target_id", None)

        if not target_id_raw:
            return

        target_id = normalize_actor_id(cast("ActorIdLike", target_id_raw))

        if self._can_return_target(ctx, source_id, target_id):
            ctx.pending_target_returns.append(self._target_return(source_id, target_id))

        # Target -> Source (только если был ответ)
        if action.partner_move and self._can_return_target(ctx, target_id, source_id):
            ctx.pending_target_returns.append(self._target_return(target_id, source_id))

    @staticmethod
    def _target_return(source_id: ActorIdLike, target_id: ActorIdLike) -> TargetReturnDTO:
        return {"source_id": normalize_actor_id(source_id), "target_id": normalize_actor_id(target_id)}

    @staticmethod
    def _can_return_target(ctx: BattleContext, source_id: ActorIdLike, target_id: ActorIdLike) -> bool:
        source = ctx.get_actor(source_id)
        target = ctx.get_actor(target_id)
        return bool(source and source.is_alive and target and target.is_alive)

    def _collect_dead_actors(self, ctx: BattleContext) -> None:
        """Collect newly dead actors so commit can update battle meta."""
        for char_id, actor in ctx.actors.items():
            if actor.meta.hp <= 0:
                actor.meta.is_dead = True
            # Проверяем, что актор мертв и еще не в списке мертвых
            if actor.meta.is_dead and char_id not in ctx.meta.dead_actors and char_id not in ctx.pending_dead_actors:
                ctx.pending_dead_actors.append(char_id)

    @staticmethod
    def _result_outcome(result: InteractionResultDTO) -> str:
        if result.skip_reason:
            return result.skip_reason.lower()
        if result.is_miss:
            return "miss"
        if result.is_dodged:
            return "dodge"
        if result.is_parried:
            return "parry"
        if result.is_blocked:
            return "block"
        if result.is_hit:
            return "crit" if result.is_crit else "hit"
        if result.healing_final > 0:
            return "heal"
        return "none"
