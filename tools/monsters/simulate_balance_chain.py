"""Resumable catalog balance frontier: player tier P against minion tiers P..5.

Each case uses the real pressure simulator. An all-loss entire sweep stops monster
tier advancement after completing that tier's count sweep, then player tier
advances. This is a diagnostic, not the encounter assembler or a balance rule.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import multiprocessing
import sys
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from loguru import logger  # noqa: E402
from tools.monsters.simulate_catalog_duel import build_reference_inputs  # noqa: E402
from tools.monsters.simulate_catalog_pressure import run_pressure_batch  # noqa: E402

from src.backend.core.calculators.stats_waterfall_calculator import StatsWaterfallCalculator  # noqa: E402
from src.backend.features.character.runtime.combat_actor_input import CharacterCombatActorInputBuilder  # noqa: E402
from src.backend.features.character.runtime.combat_math_model import CharacterCombatMathModelBuilder  # noqa: E402
from src.backend.features.character.runtime.rules.base_power_assembler import BasePowerAssembler  # noqa: E402
from src.backend.features.items.dto.instance import GeneratedItemDTO  # noqa: E402
from src.backend.features.items.services.catalog_service import ItemCatalogService  # noqa: E402
from src.backend.features.monsters.encounters.policies.encounter_profiles import (  # noqa: E402
    MONSTER_ENCOUNTER_PROFILES,
)
from src.backend.features.monsters.encounters.policies.group_assembler import GROUP_ASSEMBLY_CONFIG  # noqa: E402

SCHEMA_VERSION = 1


def digest(payload) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def source_fingerprint() -> str:
    files = sorted(
        {*ROOT.glob("src/backend/**/*.py"), *ROOT.glob("src/shared/**/*.py"), *ROOT.glob("tools/monsters/*.py")}
    )
    return digest(
        [(path.relative_to(ROOT).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()) for path in files]
    )


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def build_chain_inputs(member_id: str, player_tier: int, monster_tier: int, mastery: float) -> dict:
    if not 0 <= mastery <= 1:
        raise ValueError("Mastery must be normalized 0..1")
    inputs = deepcopy(build_reference_inputs(member_id, player_tier))
    if monster_tier != player_tier:
        inputs["monster"] = deepcopy(build_reference_inputs(member_id, monster_tier)["monster"])
    player = inputs["player"]
    skills = {key: mastery for key in player["skills"]}
    items = {"layout": {"equipment": {}}, "by_id": {}}
    catalog = ItemCatalogService.load_default()
    for payload in player["equipment"]:
        item = GeneratedItemDTO.model_validate(payload)
        data = item.model_dump(mode="json")
        data["item_id"] = item.instance_id
        base = catalog.get_base_item(item.base_id)
        data["mechanics"] = {
            **item.mechanics,
            "power": item.power,
            "bonuses": dict(item.bonuses),
            "damage_spread": item.damage_spread,
            "triggers": list(item.triggers),
            "related_skill": item.metadata.get("related_skill"),
            "armor_class": base.armor_class if base else None,
        }
        items["layout"]["equipment"][item.slot] = item.instance_id
        items["by_id"][item.instance_id] = data
    raw = CharacterCombatMathModelBuilder().build_raw(
        attributes=player["input_attributes"],
        items=items,
        skills=skills,
        symbiote={"gift_rank": max(1, player_tier + 1)},
    )
    values, _ = StatsWaterfallCalculator.calculate_waterfall(raw)
    loadout = CharacterCombatActorInputBuilder._loadout(items, skills, include_basic_gift_abilities=False)
    BasePowerAssembler.apply_to_values(values, loadout_layout=loadout["layout"], skills=skills)
    player.update(raw=raw, skills=skills, loadout=loadout, preview_values=values)
    inputs.update(player_tier=player_tier, monster_tier=monster_tier, player_mastery=mastery)
    return inputs


def formation_reference():
    ordinary = deepcopy(MONSTER_ENCOUNTER_PROFILES["goblin_tribe"]["ordinary"])
    return {
        "source": "src/backend/features/monsters/encounters/policies/encounter_profiles.py",
        "goblin_ordinary_profiles": ordinary,
        "official_minion_count_range": [ordinary["easy"]["min_units"], ordinary["easy"]["max_units"]],
        "role_weights": deepcopy(GROUP_ASSEMBLY_CONFIG["role_weights"]),
        "action_economy": json.loads(json.dumps(GROUP_ASSEMBLY_CONFIG["action_economy"])),
        "note": "Counts 1 and 6 are diagnostic; ordinary goblin easy/normal use 2..5. Hard forbids minions. No gear-score budget is applied to these clone sweeps.",
    }


def worker_case(inputs, *, monsters, battles, seed, max_rounds):
    logger.remove()
    return asyncio.run(run_pressure_batch(inputs, monsters=monsters, battles=battles, seed=seed, max_rounds=max_rounds))


def make_config(args):
    if not 0 <= args.min_player_tier <= args.max_player_tier <= args.max_monster_tier <= 5:
        raise ValueError("Require 0 <= min-player-tier <= max-player-tier <= max-monster-tier <= 5")
    if not 1 <= args.max_count <= 100 or args.battles < 1 or args.max_rounds < 1 or not 1 <= args.workers <= 6:
        raise ValueError("Positive battle/count/round limits and 1..6 workers required")
    masteries = [round(args.mastery_start + tier * args.mastery_step, 8) for tier in range(args.max_player_tier + 1)]
    if any(not 0 <= value <= 1 for value in masteries):
        raise ValueError("Every configured player mastery must remain normalized 0..1")
    return {
        "schema_version": SCHEMA_VERSION,
        "source_fingerprint": source_fingerprint(),
        "member_id": args.member_id,
        "min_player_tier": args.min_player_tier,
        "max_player_tier": args.max_player_tier,
        "max_monster_tier": args.max_monster_tier,
        "max_count": args.max_count,
        "battles": args.battles,
        "max_rounds": args.max_rounds,
        "seed": args.seed,
        "mastery_start": args.mastery_start,
        "mastery_step": args.mastery_step,
        "skill_policy": "existing_player_build_keys_only",
        "player_mastery_by_tier": masteries,
        "stop_policy": "complete_count_sweep_then_stop_monster_advancement_if_all_counts_all_losses",
    }


async def run_chain(args):
    config = make_config(args)
    config_hash = digest(config)
    summary_path = args.output / "summary.json"
    if summary_path.exists():
        report = json.loads(summary_path.read_text(encoding="utf-8"))
        if report.get("config_hash") != config_hash:
            raise ValueError(
                "Output already contains another configuration/source version; choose a fresh output folder"
            )
    else:
        if args.output.exists() and any(args.output.iterdir()):
            raise ValueError("Output must be empty or contain a compatible balance-chain summary")
        report = {
            "config": config,
            "config_hash": config_hash,
            "formation_reference": formation_reference(),
            "cases": [],
            "transitions": [],
            "status": "running",
        }
        write_json(summary_path, report)
    report["status"] = "running"
    pool = (
        ProcessPoolExecutor(max_workers=args.workers, mp_context=multiprocessing.get_context("spawn"))
        if args.workers > 1
        else None
    )
    try:
        for player_tier in range(args.min_player_tier, args.max_player_tier + 1):
            for monster_tier in range(player_tier, args.max_monster_tier + 1):
                mastery = config["player_mastery_by_tier"][player_tier]
                inputs = build_chain_inputs(args.member_id, player_tier, monster_tier, mastery)
                inputs_hash = digest(inputs)
                pair_rows = {}

                async def execute_case(
                    count,
                    player_tier=player_tier,
                    monster_tier=monster_tier,
                    inputs=inputs,
                    inputs_hash=inputs_hash,
                    mastery=mastery,
                ):
                    case_id = f"p{player_tier}-m{monster_tier}-n{count}"
                    folder = args.output / case_id
                    path = folder / "summary.json"
                    if path.exists():
                        summary = json.loads(path.read_text(encoding="utf-8"))
                        stored_inputs = json.loads((folder / "inputs.json").read_text(encoding="utf-8"))
                        if (
                            summary.get("config_hash") != config_hash
                            or summary.get("inputs_hash") != inputs_hash
                            or digest(stored_inputs) != inputs_hash
                        ):
                            raise ValueError(f"Case configuration/input mismatch: {case_id}")
                        return summary
                    write_json(folder / "inputs.json", inputs)
                    kwargs = {
                        "monsters": count,
                        "battles": args.battles,
                        "seed": args.seed
                        + ((player_tier * 6 + monster_tier) * args.max_count + count - 1) * args.battles,
                        "max_rounds": args.max_rounds,
                    }
                    if pool:
                        from functools import partial

                        result, sample = await asyncio.get_running_loop().run_in_executor(
                            pool, partial(worker_case, inputs, **kwargs)
                        )
                    else:
                        result, sample = await run_pressure_batch(inputs, **kwargs)
                    result.update(
                        config_hash=config_hash,
                        inputs_hash=inputs_hash,
                        case_id=case_id,
                        player_tier=player_tier,
                        monster_tier=monster_tier,
                        player_mastery=mastery,
                        official_squad_range=2 <= count <= 5,
                        case_path=case_id,
                    )
                    write_json(folder / "sample-combat-log.json", sample)
                    write_json(path, result)
                    return result

                pending = [execute_case(count) for count in range(1, args.max_count + 1)]
                for finished in asyncio.as_completed(pending):
                    result = await finished
                    pair_rows[result["monster_count"]] = result
                    row = {key: value for key, value in result.items() if key != "fights"}
                    report["cases"] = [old for old in report["cases"] if old["case_id"] != row["case_id"]] + [row]
                    report["cases"].sort(
                        key=lambda value: (value["player_tier"], value["monster_tier"], value["monster_count"])
                    )
                    write_json(summary_path, report)
                    print(
                        json.dumps({key: row[key] for key in ("case_id", "player_mastery", "wins", "median_rounds")}),
                        flush=True,
                    )
                dry_counts = sorted(count for count, row in pair_rows.items() if row["wins"]["monster"] == args.battles)
                blocked = len(dry_counts) == args.max_count
                reached_limit = monster_tier == args.max_monster_tier
                transition = {
                    "player_tier": player_tier,
                    "monster_tier": monster_tier,
                    "solo_all_losses": 1 in dry_counts,
                    "all_counts_all_losses": blocked,
                    "first_dry_loss_count": min(dry_counts, default=None),
                    "first_official_dry_loss_count": min(
                        (count for count in dry_counts if 2 <= count <= 5), default=None
                    ),
                    "action": "advance_player" if blocked or reached_limit else "advance_monster",
                    "reason": "all_counts_all_losses"
                    if blocked
                    else ("max_monster_tier_reached" if reached_limit else "some_counts_not_all_losses"),
                }
                report["transitions"] = [
                    old
                    for old in report["transitions"]
                    if (old["player_tier"], old["monster_tier"]) != (player_tier, monster_tier)
                ] + [transition]
                write_json(summary_path, report)
                if blocked:
                    break
        report["status"] = "complete"
        write_json(summary_path, report)
    finally:
        if pool:
            pool.shutdown(wait=True, cancel_futures=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--member-id", default="goblin_tribe.base.goblin_sneak")
    parser.add_argument("--min-player-tier", type=int, default=0)
    parser.add_argument("--max-player-tier", type=int, default=5)
    parser.add_argument("--max-monster-tier", type=int, default=5)
    parser.add_argument("--mastery-start", type=float, default=0.2)
    parser.add_argument("--mastery-step", type=float, default=0.1)
    parser.add_argument("--max-count", type=int, default=6)
    parser.add_argument("--battles", type=int, default=100)
    parser.add_argument("--max-rounds", type=int, default=100)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--seed", type=int, default=17000)
    parser.add_argument("--output", type=Path, default=ROOT / "var/balance-chain")
    args = parser.parse_args()
    logger.remove()
    asyncio.run(run_chain(args))


if __name__ == "__main__":
    main()
