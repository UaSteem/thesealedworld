"""Actor-global tactical lifecycle; starting values are tunable, not approved balance."""

from __future__ import annotations

import hashlib
import random

from src.backend.features.combat.dto.actor import ActiveEffectDTO, ActorSnapshot
from src.backend.features.combat.dto.pipeline import InteractionResultDTO, PipelineContextDTO, TacticalTransitionFactDTO
from src.backend.features.combat.runtime.engine.ranged_position import RangedPositionService
from src.backend.features.game_catalog.combat.resources.common.tactical_states import (
    TACTICAL_ENTRY,
    TACTICAL_INITIATIVE_SCALE,
    TACTICAL_LOSS,
    TACTICAL_POLICIES,
)

TACTICAL_EFFECT_ID = "tactical_state"


class TacticalStateService:
    @staticmethod
    def current_state(actor: ActorSnapshot) -> str:
        if RangedPositionService.is_ranged_actor(actor):
            return RangedPositionService.current_position(actor)
        style = actor.loadout.layout.get("tactical_style")
        for effect in actor.statuses.effects:
            if (
                effect.effect_id == TACTICAL_EFFECT_ID
                and effect.params.get("style") == style
                and effect.active_from_exchange <= actor.meta.exchange_counter < effect.expire_at_exchange
            ):
                return "advantage" if effect.params.get("state") == "advantage" else "normal"
        return "normal"

    @staticmethod
    def mastery(actor: ActorSnapshot) -> float:
        key = actor.loadout.layout.get("tactical_style", "")
        value = getattr(actor.stats.skills, key, 0.0) if actor.stats else actor.skills.get(key, 0.0)
        return max(0.0, min(1.0, float(value or 0.0)))

    @staticmethod
    def apply_context(ctx: PipelineContextDTO, source: ActorSnapshot, target: ActorSnapshot | None) -> None:
        # Fresh context modifiers apply to every weapon strike, including counters;
        # activation and transition checks remain exchange-owner scoped.
        if (
            ctx.flags.meta.source_type in {"main_hand", "off_hand"}
            and TacticalStateService.current_state(source) == "advantage"
        ):
            style = source.loadout.layout.get("tactical_style")
            policy = TACTICAL_POLICIES.get(style, {})
            ctx.mods.tactical_crit_bonus = policy.get("crit", 0.0) * TacticalStateService.mastery(source)
            ctx.mods.tactical_anti_dodge_bonus = policy.get("anti_dodge", 0.0) * TacticalStateService.mastery(source)
        if target is not None and TacticalStateService.current_state(target) == "advantage":
            policy = TACTICAL_POLICIES.get(target.loadout.layout.get("tactical_style"), {})
            ctx.mods.tactical_parry_bonus = policy.get("parry", 0.0) * TacticalStateService.mastery(target)

    @staticmethod
    def probabilities(initiative: float, enemy_initiative: float) -> tuple[float, float]:
        tempo = max(-1.0, min(1.0, (initiative - enemy_initiative) / TACTICAL_INITIATIVE_SCALE))
        return (max(0.05, min(0.75, TACTICAL_ENTRY + 0.20 * tempo)), max(0.05, min(0.75, TACTICAL_LOSS - 0.20 * tempo)))

    @staticmethod
    def roll(seed: str, actor: ActorSnapshot) -> float:
        key = f"{seed}:{actor.char_id}:{actor.meta.exchange_counter}:tactical-v1"
        return random.Random(int.from_bytes(hashlib.sha256(key.encode()).digest(), "big")).random()

    @staticmethod
    def set_next_state(actor: ActorSnapshot, state: str, result: InteractionResultDTO) -> None:
        active = actor.meta.exchange_counter + 1
        actor.statuses.effects = [e for e in actor.statuses.effects if e.effect_id != TACTICAL_EFFECT_ID]
        if state == "advantage":
            actor.statuses.effects.append(
                ActiveEffectDTO(
                    uid=f"{TACTICAL_EFFECT_ID}:{actor.char_id}:{active}",
                    effect_id=TACTICAL_EFFECT_ID,
                    source_id=actor.char_id,
                    active_from_exchange=active,
                    expire_at_exchange=active + 1,
                    params={"style": actor.loadout.layout.get("tactical_style"), "state": state},
                    resolved_temp_commands=[],
                )
            )

    @staticmethod
    def update_after_exchange(pairs, *, participants, final_result: InteractionResultDTO, seed: str) -> None:
        if not participants or not any(
            not r.skip_reason and r.action_facts.get("execution", {}).get("origin", "primary") == "primary"
            for _, _, r in pairs
        ):
            return
        # Freeze both owners before applying any decision. Secondary AoE targets
        # never become additional owners or initiative opponents.
        frozen = tuple(a.model_copy(deep=True) for a in participants)
        decisions = []
        for actor, enemy in ((frozen[0], frozen[1]), (frozen[1], frozen[0])):
            if not actor.is_alive:
                continue
            style = actor.loadout.layout.get("tactical_style")
            if style not in TACTICAL_POLICIES:
                continue
            own = next(
                (
                    r
                    for a, _, r in pairs
                    if a.char_id == actor.char_id
                    and r.action_facts.get("execution", {}).get("origin", "primary") == "primary"
                ),
                None,
            )
            hostile = next(
                (
                    r
                    for a, target, r in pairs
                    if a.char_id == enemy.char_id
                    and target is not None
                    and target.char_id == actor.char_id
                    and r.action_facts.get("execution", {}).get("origin", "primary") == "primary"
                ),
                None,
            )
            if own is not None and own.skip_reason:
                continue
            facts = own.action_facts if own else {}
            enemy_facts = hostile.action_facts if hostile and not hostile.skip_reason else {}
            before = TacticalStateService.current_state(actor)
            own_init = actor.stats.mods.initiative if actor.stats else 0.0
            enemy_init = enemy.stats.mods.initiative if enemy.stats else 0.0
            entry, loss = TacticalStateService.probabilities(own_init, enemy_init)
            entry = max(0.05, min(0.95, entry + float(facts.get("tactical_entry_bonus", 0))))
            loss = max(0.0, min(0.95, loss - float(facts.get("tactical_hold_bonus", 0))))
            dislodge = bool(enemy_facts.get("tactical_dislodge")) and bool(hostile and hostile.is_hit)
            protect = bool(facts.get("tactical_protect"))
            forced = bool(facts.get("tactical_force_advantage"))
            roll = TacticalStateService.roll(seed, actor)
            # Guaranteed dislodge wins, then protected hold, then forced entry,
            # finally a single entry OR loss roll (never both).
            if dislodge:
                after, reason, source = "normal", "feint_dislodge", enemy_facts
            elif before == "advantage" and protect:
                after, reason, source = "advantage", "feint_protect", facts
            elif forced:
                after, reason, source = "advantage", "feint_entry", facts
            else:
                after = (
                    ("advantage" if roll < entry else "normal")
                    if before == "normal"
                    else ("normal" if roll < loss else "advantage")
                )
                reason, source = ("initiative_entry" if after == "advantage" else "initiative_loss"), {}
                if before == "normal" and after == "advantage" and facts.get("tactical_entry_bonus"):
                    reason, source = "feint_assisted_entry", facts
            decisions.append((actor.char_id, before, after, reason, source))
        for live in participants:
            live.statuses.effects = [
                e
                for e in live.statuses.effects
                if (
                    e.effect_id != TACTICAL_EFFECT_ID
                    or (live.is_alive and e.params.get("style") == live.loadout.layout.get("tactical_style"))
                )
                and (e.effect_id != "ranged_position" or RangedPositionService.is_ranged_actor(live))
            ]
        for actor_id, before, after, reason, facts in decisions:
            live = next(a for a in participants if a.char_id == actor_id)
            TacticalStateService.set_next_state(live, after, final_result)
            if before != after:
                action_id = facts.get("id")
                final_result.tactical_transitions.append(
                    TacticalTransitionFactDTO(
                        actor_id=actor_id,
                        style=live.loadout.layout["tactical_style"],
                        before=before,
                        after=after,
                        reason=reason,
                        source_action_id=action_id,
                        source_feint_id=action_id if facts.get("role") == "feint" else None,
                    )
                )
        RangedPositionService.update_after_exchange(
            pairs, participants=participants, final_result=final_result, seed=seed
        )
