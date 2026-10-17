"""Run Studio's exact reference builds through the real in-memory combat executor.

No persistence or external inference is used. This is a bounded diagnostic, not
a balance model: the reference player's attributes are still starter values.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import statistics
import sys
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from loguru import logger  # noqa: E402

from src.backend.features.combat.dto import ActorLoadoutDTO, ActorMetaDTO, ActorRawDTO, ActorSnapshot  # noqa: E402
from src.backend.features.combat.runtime.engine.stats_engine import StatsEngine  # noqa: E402
from src.backend.features.combat.runtime.simulation import (  # noqa: E402
    CombatTelemetry,
    InMemoryBattleFactory,
    InMemoryBattleLimits,
    InMemoryCombatSimulator,
)
from src.backend.features.monsters.catalog import get_catalog  # noqa: E402
from src.backend.features.monsters.catalog.prepared_equipment import (  # noqa: E402
    get_prepared_equipment,
)
from src.backend.features.monsters.inspection.services.equipment_stats_service import (  # noqa: E402
    MonsterEquipmentStatsService,
)
from src.backend.features.monsters.inspection.services.player_comparison_service import (  # noqa: E402
    PlayerComparisonService,
)
from src.backend.features.monsters.instances.services.instance_builder import MonsterInstanceBuilder  # noqa: E402


class RecordingTelemetry(CombatTelemetry):
    """Keep original resolver facts as well as the existing aggregated telemetry."""

    def __init__(self):
        super().__init__()
        self.result_facts = []

    def record_executor_context(self, ctx, *, round_index=None):
        self.result_facts.extend(
            {"round": round_index, **deepcopy(payload)} for payload in ctx.pending_result_support_tasks
        )
        super().record_executor_context(ctx, round_index=round_index)


def build_reference_inputs(member_id: str, tier: int) -> dict:
    catalog = get_catalog()
    member = catalog.members[member_id]
    family = catalog.families[member.family_id]
    prepared = get_prepared_equipment(family_id=family.id, variant_id=member.variant_id, tier=tier)
    monster = MonsterInstanceBuilder().build(member=member, family=family, prepared=prepared)
    player = PlayerComparisonService().preview(tier=tier, monster=MonsterEquipmentStatsService.present(monster))
    return {
        "member_id": member_id,
        "tier": tier,
        "player": {
            "name": player.label,
            "raw": player.technical["raw"],
            "skills": player.technical["skills"],
            "loadout": player.technical["loadout"],
            "equipment": player.technical["equipment"],
            "input_attributes": player.input_attributes,
            "preview_values": player.technical["equipped"],
        },
        "monster": {
            "name": member.name,
            "role": member.role,
            "raw": monster.equipped.raw,
            "skills": monster.skills,
            "loadout": monster.equipped.loadout,
            "equipment": prepared.model_dump(mode="json"),
            "input_attributes": monster.tier_attributes,
            "preview_values": monster.equipped.values,
        },
    }


def build_actor(payload: dict, *, actor_id: str, team: str, kind: str) -> ActorSnapshot:
    actor = ActorSnapshot(
        meta=ActorMetaDTO(
            id=actor_id,
            name=payload["name"],
            type=kind,
            role=(payload.get("role") or payload["raw"].get("pipeline", {}).get("role")) if kind == "monster" else None,
            team=team,
            is_ai=True,
            ai_archetype="balanced",
            ai_behavior_profile="balanced",
        ),
        raw=ActorRawDTO.model_validate(deepcopy(payload["raw"])),
        skills=deepcopy(payload["skills"]),
        loadout=ActorLoadoutDTO.model_validate(deepcopy(payload["loadout"])),
    )
    StatsEngine.ensure_stats(actor)
    # Match the existing simulator actor builder's resource hydration rule.
    for field in ("hp", "en", "stamina"):
        value = max(1, int(round(float(getattr(actor.stats.mods, field)))))
        setattr(actor.meta, field, value)
        setattr(actor.meta, f"max_{field}", value)
    return actor


async def run_batch(inputs: dict, *, battles: int, seed: int, max_rounds: int) -> tuple[dict, dict]:
    if battles < 1 or max_rounds < 1:
        raise ValueError("Positive battle and round counts are required")
    fights, sample, initial = [], {}, {}
    totals = {kind: Counter() for kind in ("player", "monster")}
    random_state = random.getstate()
    try:
        for index in range(battles):
            fight_seed = seed + index
            # MathCore/FeintService use process random, not InMemoryBattleState.seed.
            # Run serially and restore process state after the diagnostic.
            random.seed(fight_seed)
            swapped = bool(index % 2)
            ids = {"player": "b" if swapped else "a", "monster": "a" if swapped else "b"}
            actors = [
                build_actor(inputs[kind], actor_id=ids[kind], team=kind, kind=kind) for kind in ("player", "monster")
            ]
            if not initial:
                initial = {
                    kind: actor.model_dump(mode="json")
                    for kind, actor in zip(("player", "monster"), actors, strict=True)
                }
            state = InMemoryBattleFactory.from_actors(
                actors,
                seed=fight_seed,
                session_id=f"catalog-duel-{fight_seed}",
                limits=InMemoryBattleLimits(max_rounds=max_rounds),
            )
            if index == 0:
                state.telemetry = RecordingTelemetry()
            result = await InMemoryCombatSimulator().run(state)
            metrics = {}
            for kind, actor_id in ids.items():
                actor_metrics = {}
                for metric in ("damage", "damage_taken", "hit", "miss", "dodge", "parry", "block", "crit"):
                    value = getattr(result.telemetry, f"{metric}_by_actor").get(actor_id, 0)
                    actor_metrics[metric] = value
                    totals[kind][metric] += value
                metrics[kind] = actor_metrics
            fights.append(
                {
                    "seed": fight_seed,
                    "actor_ids": ids,
                    "winner": result.winner,
                    "rounds": result.rounds_completed,
                    "completion_reason": result.completion_reason,
                    "remaining_hp": {kind: result.final_hp_by_actor[actor_id] for kind, actor_id in ids.items()},
                    "metrics": metrics,
                }
            )
            if index == 0:
                sample = {
                    "fight": fights[-1],
                    "telemetry": asdict(result.telemetry),
                    "resolver_results": state.telemetry.result_facts,
                }
    finally:
        random.setstate(random_state)
    summary = {
        "battles": battles,
        "seed_start": seed,
        "max_rounds": max_rounds,
        "wins": dict(Counter(fight["winner"] for fight in fights)),
        "completion_reasons": dict(Counter(fight["completion_reason"] for fight in fights)),
        "median_rounds": statistics.median(fight["rounds"] for fight in fights),
        "mean_remaining_hp": {
            kind: statistics.mean(fight["remaining_hp"][kind] for fight in fights) for kind in ("player", "monster")
        },
        "telemetry_totals": {kind: dict(values) for kind, values in totals.items()},
        "assumptions": [
            "Exact current Studio reference raw stats, skills, loadout and prepared equipment.",
            "Player starter attributes; tier/7 weapon, dual-wield and light-armor mastery, no invented training.",
            "Both actors use the existing local balanced MonsterCombatBrain; this is not human play.",
            "Fresh full integer resources each fight; zero initial tactical tokens and empty feint hands.",
            "No added abilities or feints; retain mapper-provided known abilities and equipment triggers.",
            "Alternate actor IDs each fight to expose ordering bias; teams retain actor identity.",
            "Serial global random seed controls real MathCore rolls; battle seed alone does not.",
            "Existing formulas and unresolved resistance cap issue are preserved, not repaired.",
            "Round safety limits are reported as draws, never scored as wins.",
        ],
        "inputs": inputs,
        "initial_actor_snapshots": initial,
        "fights": fights,
    }
    return summary, sample


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--member-id", default="goblin_tribe.base.goblin_spearman")
    parser.add_argument("--tier", type=int, default=5)
    parser.add_argument("--battles", type=int, default=100)
    parser.add_argument("--seed", type=int, default=16000)
    parser.add_argument("--max-rounds", type=int, default=100)
    parser.add_argument("--output", type=Path, default=ROOT / "var/catalog-duel-tier5")
    args = parser.parse_args()
    logger.remove()
    inputs = build_reference_inputs(args.member_id, args.tier)
    summary, sample = asyncio.run(run_batch(inputs, battles=args.battles, seed=args.seed, max_rounds=args.max_rounds))
    args.output.mkdir(parents=True, exist_ok=True)
    for name, payload in (("summary.json", summary), ("sample-combat-log.json", sample)):
        (args.output / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                key: value
                for key, value in summary.items()
                if key not in {"inputs", "initial_actor_snapshots", "fights"}
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
