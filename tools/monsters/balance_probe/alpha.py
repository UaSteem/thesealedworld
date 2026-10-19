"""Portable alpha matrix over preserved heavy-guard inputs and current Monsters.

This is a new-current-source comparison, never an exact replay of historical runs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .config import ProbeConfig

DATA = Path(__file__).with_name("data") / "alpha"
FAMILIES = {"rat_swarm": 0, "goblin_tribe": 0, "wolf_pack": 1, "bandit_gang": 1, "golem_foundry": 2}


def scenario_configs(*, families, tiers, battles, workers, seed, output):
    """Named historical benchmark; tier gates are the accepted scenario, not runtime rules."""
    for family in families:
        for tier in tiers:
            if tier < FAMILIES[family]:
                continue
            yield ProbeConfig(
                family=family,
                tier=tier,
                players=(),
                player_input=DATA / "heavy_guard_players.json",
                player_keys=(f"starter_heavy_guard_01.t{tier}",),
                player_tier=tier,
                encounters=("ordinary", "patrol", "guard", "leader"),
                difficulties=("easy", "normal", "hard"),
                battles=battles,
                workers=workers,
                seed=seed,
                feints="both",
                output=output / family / f"t{tier}",
            )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--families", nargs="+", choices=tuple(FAMILIES), default=list(FAMILIES))
    parser.add_argument("--tiers", nargs="+", type=int, choices=range(6), default=list(range(6)))
    parser.add_argument("--battles", type=int, default=10)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true", help="Validate preserved players and plan; no battles")
    args = parser.parse_args(argv)
    if args.battles < 1 or args.workers < 1:
        parser.error("battles and workers must be positive")
    from .players import resolve_players
    from .runner import digest, run_probe, source_fingerprint, validate_catalog, write_json

    configs = list(
        scenario_configs(**{k: getattr(args, k) for k in ("families", "tiers", "battles", "workers", "seed", "output")})
    )
    if not configs:
        parser.error("No scenarios remain after the accepted tier gates")
    if args.output.exists() and any(args.output.iterdir()):
        parser.error("output must be new or empty")
    records = []
    for config in configs:
        validate_catalog(config)
        players = resolve_players(config)
        key = config.player_keys[0]
        records.append(
            {
                "family": config.family,
                "tier": config.tier,
                "cases": 12,
                "requested": 12 * config.battles,
                "player_key": key,
                "gear_score": players[key]["gear_score"],
                "players_sha256": digest(players),
                "config": config.to_dict(),
            }
        )
    write_json(
        args.output / "plan.json",
        {
            "schema_version": 1,
            "preset": "alpha-heavy-guard-v1",
            "comparison_mode": "preserved-player/current-monsters-and-combat",
            "source_fingerprint": source_fingerprint(),
            "seed_start": args.seed,
            "seed_end": args.seed + args.battles - 1,
            "dry_run": args.dry_run,
            "scenarios": records,
            "limitations": [
                "No symbiote bonuses; automatic feints.",
                "Saved equipment is historical, not regenerated from current item catalog.",
                "GS and waterfall are recalculated by current code; historical evidence is immutable.",
            ],
        },
    )
    if not args.dry_run:
        summaries: list[dict[str, Any]] = []
        for config in configs:
            report = run_probe(config)
            summaries.extend(dict(family=config.family, **case) for case in report["cases"])
        write_json(args.output / "matrix.json", {"schema_version": 1, "cases": summaries})
    print(
        json.dumps(
            {
                "tiers": len(configs),
                "cases": len(configs) * 12,
                "requested": sum(r["requested"] for r in records),
                "dry_run": args.dry_run,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
