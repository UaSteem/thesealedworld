"""Compare one current Studio player with 1..N identical fresh catalog monsters.

Read-only local combat diagnostic. Does not change the single-duel CLI or any
catalog/runtime rules. Run serially because combat math uses process random.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import statistics
import sys
from collections import Counter
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from loguru import logger  # noqa: E402
from tools.monsters.simulate_catalog_duel import (  # noqa: E402
    RecordingTelemetry,
    build_actor,
    build_reference_inputs,
)

from src.backend.features.combat.runtime.simulation import (  # noqa: E402
    InMemoryBattleFactory,
    InMemoryBattleLimits,
    InMemoryCombatSimulator,
)

METRICS = ("damage", "damage_taken", "hit", "miss", "dodge", "parry", "block", "crit")


def build_roster(inputs: dict, *, monsters: int, swapped: bool):
    if type(monsters) is not int or not 1 <= monsters <= 100:
        raise ValueError("Monster count must be an integer from 1 to 100")
    player_id = "z_player" if swapped else "a_player"
    monster_ids = [f"m_{index:03d}" for index in range(monsters)]
    actors = [build_actor(inputs["player"], actor_id=player_id, team="player", kind="player")]
    actors.extend(
        build_actor(inputs["monster"], actor_id=actor_id, team="monster", kind="monster") for actor_id in monster_ids
    )
    return actors, {"player": [player_id], "monster": monster_ids}


async def run_pressure_batch(inputs: dict, *, monsters: int, battles: int, seed: int, max_rounds: int):
    if type(battles) is not int or battles < 1 or type(max_rounds) is not int or max_rounds < 1:
        raise ValueError("Positive integer battle and round counts are required")
    fights, sample = [], {}
    totals = {team: Counter() for team in ("player", "monster")}
    random_state = random.getstate()
    try:
        for index in range(battles):
            fight_seed = seed + index
            random.seed(fight_seed)
            actors, ids = build_roster(inputs, monsters=monsters, swapped=bool(index % 2))
            initial_hp = {str(actor.meta.id): actor.meta.hp for actor in actors}
            state = InMemoryBattleFactory.from_actors(
                actors,
                seed=fight_seed,
                session_id=f"catalog-pressure-{monsters}-{fight_seed}",
                limits=InMemoryBattleLimits(max_rounds=max_rounds),
            )
            if index == 0:
                state.telemetry = RecordingTelemetry()
            result = await InMemoryCombatSimulator().run(state)
            metrics = {}
            for team, actor_ids in ids.items():
                metrics[team] = {
                    metric: sum(
                        getattr(result.telemetry, f"{metric}_by_actor").get(actor_id, 0) for actor_id in actor_ids
                    )
                    for metric in METRICS
                }
                totals[team].update(metrics[team])
            dead_ids = (
                {str(actor.meta.id) for actor in state.ctx.actors.values() if actor.meta.is_dead or not actor.is_alive}
                | set(map(str, state.ctx.meta.dead_actors))
                | set(result.telemetry.deaths)
            )
            fight = {
                "seed": fight_seed,
                "actor_ids": ids,
                "winner": result.winner,
                "rounds": result.rounds_completed,
                "completion_reason": result.completion_reason,
                "initial_hp_by_actor": initial_hp,
                "remaining_hp_by_actor": result.final_hp_by_actor,
                "remaining_hp": {
                    team: sum(result.final_hp_by_actor[actor_id] for actor_id in actor_ids)
                    for team, actor_ids in ids.items()
                },
                "deaths": {
                    team: sum(actor_id in dead_ids for actor_id in actor_ids) for team, actor_ids in ids.items()
                },
                "dead_actor_ids": sorted(dead_ids),
                "metrics": metrics,
            }
            fights.append(fight)
            if index == 0:
                sample = {
                    "fight": fight,
                    "telemetry": asdict(result.telemetry),
                    "resolver_results": state.telemetry.result_facts,
                }
    finally:
        random.setstate(random_state)
    summary = {
        "monster_count": monsters,
        "battles": battles,
        "seed_start": seed,
        "max_rounds": max_rounds,
        "wins": {
            winner: sum(fight["winner"] == winner for fight in fights) for winner in ("player", "monster", "draw")
        },
        "completion_reasons": dict(Counter(fight["completion_reason"] for fight in fights)),
        "median_rounds": statistics.median(fight["rounds"] for fight in fights),
        "mean_remaining_hp": {team: statistics.mean(fight["remaining_hp"][team] for fight in fights) for team in ids},
        "mean_deaths": {team: statistics.mean(fight["deaths"][team] for fight in fights) for team in ids},
        "telemetry_totals": {team: dict(counts) for team, counts in totals.items()},
        "fights": fights,
    }
    return summary, sample


async def run_series(args):
    if not 1 <= args.min_monsters <= args.max_monsters <= 100:
        raise ValueError("Require 1 <= min-monsters <= max-monsters <= 100")
    inputs = build_reference_inputs(args.member_id, args.tier)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "inputs.json").write_text(json.dumps(inputs, ensure_ascii=False, indent=2), encoding="utf-8")
    table = []
    for count in range(args.min_monsters, args.max_monsters + 1):
        summary, sample = await run_pressure_batch(
            inputs,
            monsters=count,
            battles=args.battles,
            seed=args.seed + count * 100_000,
            max_rounds=args.max_rounds,
        )
        folder = args.output / f"monsters-{count:02d}"
        folder.mkdir(exist_ok=True)
        for name, data in (("summary.json", summary), ("sample-combat-log.json", sample)):
            (folder / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        row = {key: value for key, value in summary.items() if key != "fights"}
        table.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
        report = {
            "member_id": args.member_id,
            "tier": args.tier,
            "battles_per_count": args.battles,
            "assumptions": [
                "Exact current Studio reference player with starter attributes and tier/7 mastery.",
                "Identical independent fresh goblin clones with current prepared equipment; no new item rolls.",
                "Real existing in-memory simulator/executor/resolver and local balanced AI for both teams.",
                "Fresh full resources, zero starting tactical tokens, no invented active abilities or feints.",
                "Player sorts first/last on alternating fights; normal existing target selection and team grouping.",
                "Sequential globally seeded MathCore randomness; seed = base + monster_count * 100000 + fight_index.",
                "Deaths use runtime flags/facts, not remaining HP, because later regeneration may leave corpse HP.",
                "Round-bound draws stay draws; no formulas, caps, runtime rules or DB contents changed.",
            ],
            "series": table,
        }
        (args.output / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--member-id", default="goblin_tribe.base.goblin_spearman")
    parser.add_argument("--tier", type=int, default=5)
    parser.add_argument("--min-monsters", type=int, default=1)
    parser.add_argument("--max-monsters", type=int, default=10)
    parser.add_argument("--battles", type=int, default=100)
    parser.add_argument("--seed", type=int, default=17000)
    parser.add_argument("--max-rounds", type=int, default=100)
    parser.add_argument("--output", type=Path, default=ROOT / "var/catalog-pressure-tier5")
    args = parser.parse_args()
    logger.remove()
    asyncio.run(run_series(args))


if __name__ == "__main__":
    main()
