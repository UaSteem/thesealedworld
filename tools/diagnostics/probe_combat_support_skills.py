"""Read-only support-skill diagnosis. Run from the repository root with python -m.

This records observed behavior; it intentionally does not enforce missing effects
as a permanent regression contract. No database or external services are used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from loguru import logger

from src.backend.core.calculators.stats_waterfall_calculator import StatsWaterfallCalculator
from src.backend.features.character.runtime.combat_actor_input import CharacterCombatActorInputBuilder
from src.backend.features.character.runtime.experimental_gear_score import ExperimentalGearScoreCalculator
from src.backend.features.combat.dto.actor import ActorLoadoutDTO, ActorMetaDTO, ActorRawDTO, ActorSnapshot, ActorStats
from src.backend.features.combat.dto.pipeline import InteractionResultDTO, PipelineContextDTO
from src.backend.features.combat.runtime.engine.math_core import MathCore
from src.backend.features.combat.runtime.engine.resolver import CombatResolver
from src.backend.features.combat.runtime.engine.resolver.steps.counter_check import counter_check_step
from src.backend.features.combat.runtime.engine.resolver.steps.evasion import evasion_step
from src.backend.features.combat.runtime.engine.stats_engine import StatsEngine

logger.remove()

SKILLS = ("skill_tactics", "skill_anatomy")
LEVELS = (0.0, 0.25, 0.5, 1.0)


def consumers(stats: ActorStats) -> dict:
    """Exercise offensive/defensive exchanges with repeatable RNG and open gates."""
    opponent = ActorStats()
    opponent.mods.evasion = 0.35
    opponent.mods.dodge_cap = 0.9
    opponent.mods.anti_dodge_chance = 0.01
    opponent.mods.main_hand_damage_base = 40
    opponent.mods.main_hand_accuracy = 1
    opponent.skills.skill_unarmed = 1
    results = {}
    for role, attacker, defender in (("attack", stats, opponent), ("defend", opponent, stats)):
        exchanges = []
        for seed in range(8):
            random.seed(seed)
            ctx = PipelineContextDTO()
            ctx.flags.meta.source_type = "main_hand"
            ctx.flags.meta.weapon_class = "unarmed"
            ctx.flags.mastery.light_armor = True
            # Open conditional counter gate explicitly, independent of loadout.
            ctx.flags.state.check_counter = True
            exchanges.append(CombatResolver.resolve_exchange(attacker, defender, ctx).model_dump(mode="json"))
        results[role] = exchanges
    # Direct step probes prove the relevant conditional code executes, even if
    # a profile's armor/accuracy prevents it in an ordinary exchange.
    chances = []
    ctx = PipelineContextDTO()
    ctx.flags.state.check_counter = True
    with patch.object(MathCore, "check_chance", side_effect=lambda chance: chances.append(chance) or True):
        counter_check_step.run(opponent, stats, ctx, InteractionResultDTO(is_parried=True))
    results["counter_chances"] = chances
    ctx = PipelineContextDTO()
    res = InteractionResultDTO()
    with patch.object(MathCore, "roll_chance", side_effect=lambda chance: (0.0, True)):
        evasion_step.run(opponent, stats, ctx, res)
    results["evasion_trace"] = res.model_dump(mode="json")
    ctx = PipelineContextDTO()
    ctx.stages.calculate_healing = True
    ctx.stages.calculate_damage = False
    ctx.stages.check_accuracy = False
    ctx.stages.check_evasion = False
    ctx.stages.check_parry = False
    ctx.stages.check_block = False
    ctx.stages.check_crit = False
    ctx.override_damage = (100, 100)
    results["received_heal"] = CombatResolver.resolve_exchange(opponent, stats, ctx).healing_final
    return results


def positive_controls() -> dict:
    attacker, defender = ActorStats(), ActorStats()
    defender.mods.evasion = 0.4
    defender.mods.dodge_cap = 0.9
    traces = []
    for anti in (0.0, 0.2):
        attacker.mods.anti_dodge_chance = anti
        res = InteractionResultDTO()
        evasion_step.run(attacker, defender, PipelineContextDTO(), res)
        traces.append(res.checks[0].chance)
    assert traces == [0.4, 0.2], traces
    counters = []
    for chance in (0.1, 0.3):
        defender.mods.counter_attack_chance = chance
        ctx = PipelineContextDTO()
        ctx.flags.state.check_counter = True
        with patch.object(MathCore, "check_chance", side_effect=lambda value: counters.append(value) or True):
            counter_check_step.run(attacker, defender, ctx, InteractionResultDTO(is_parried=True))
    assert counters == [0.1, 0.3], counters
    return {"evasion_after_anti_dodge": traces, "counter_chances": counters}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profiles", type=Path, nargs="+")
    args = parser.parse_args()
    rows, inputs = [], []
    builder = CharacterCombatActorInputBuilder()
    for path in args.profiles:
        inputs.append({"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        for identity, profile in data["resolved_players"].items():
            context = profile["input_context"]
            for skill in SKILLS:
                baseline = None
                for level in LEVELS:
                    skills = deepcopy(profile["skills"])
                    skills[skill] = level
                    active = {**deepcopy(context), "char_id": "probe", "skills": skills}
                    actor_input = builder.build_input(active)
                    nested = deepcopy(active)
                    nested["skills"] = {key: {"xp": value, "unlocked": True} for key, value in skills.items()}
                    assert builder.build_input(nested) == actor_input
                    pending = deepcopy(active)
                    pending["skills"][skill] = 0.0
                    pending["pending_progress"] = {"skills": {skill: level}}
                    assert builder.build_input(pending) == actor_input
                    snapshot = ActorSnapshot(
                        meta=ActorMetaDTO(id="probe", name=identity, type="player", team="blue"),
                        raw=ActorRawDTO.model_validate(actor_input["raw"]),
                        skills=actor_input["skills"],
                        loadout=ActorLoadoutDTO.model_validate(actor_input["loadout"]),
                    )
                    StatsEngine.ensure_stats(snapshot)
                    assert getattr(snapshot.stats.skills, skill) == level
                    waterfall, _ = StatsWaterfallCalculator.calculate_waterfall(actor_input["raw"])
                    observed = {
                        "raw": actor_input["raw"],
                        "waterfall": waterfall,
                        "mods": snapshot.stats.mods.model_dump(),
                        "loadout": actor_input["loadout"],
                        "gs": ExperimentalGearScoreCalculator().calculate_from_raw(
                            actor_input["raw"], skills=actor_input["skills"], loadout=actor_input["loadout"]
                        ),
                        "consumers": consumers(snapshot.stats),
                    }
                    if baseline is None:
                        baseline = observed
                    rows.append(
                        {
                            "profile": str(path),
                            "actor": identity,
                            "skill": skill,
                            "level": level,
                            "changed": [key for key in observed if observed[key] != baseline[key]],
                            "heal": observed["consumers"]["received_heal"],
                        }
                    )
    print(json.dumps({"inputs": inputs, "positive_controls": positive_controls(), "rows": rows}, indent=2))


if __name__ == "__main__":
    main()
