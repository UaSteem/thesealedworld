"""Bounded real Combat simulations using public Monsters preparation/selection."""

from __future__ import annotations

import asyncio
import json
import multiprocessing
import random
import re
import statistics
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .config import ProbeConfig
from .players import _validate_payload, resolve_players

ROOT = Path(__file__).resolve().parents[3]


def digest(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def source_fingerprint() -> str:
    files = sorted(
        {*ROOT.glob("src/backend/**/*.py"), *ROOT.glob("src/shared/**/*.py"), *ROOT.glob("tools/monsters/**/*.py")}
    )
    return digest([(p.relative_to(ROOT).as_posix(), sha256(p.read_bytes()).hexdigest()) for p in files])


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def validate_catalog(config: ProbeConfig) -> None:
    from src.backend.features.monsters.catalog import get_catalog

    catalog = get_catalog()
    if config.family not in catalog.families:
        raise ValueError(f"Unknown family: {config.family}")
    for identity, _ in config.members:
        member = catalog.members.get(identity)
        if member is None:
            raise ValueError(f"Unknown member: {identity}")
        if member.family_id != config.family:
            raise ValueError(f"{identity} does not belong to {config.family}")


def _monster_payload(member, tier: int, catalog) -> dict:
    from src.backend.features.monsters.catalog.prepared_equipment import get_member_prepared_equipment
    from src.backend.features.monsters.instances.services.instance_builder import MonsterInstanceBuilder

    prepared = get_member_prepared_equipment(member=member, tier=tier)
    built = MonsterInstanceBuilder().build(member=member, family=catalog.families[member.family_id], prepared=prepared)
    return {
        "name": member.name,
        "role": member.role,
        "raw": built.equipped.raw,
        "skills": built.skills,
        "loadout": built.equipped.loadout,
        "equipment": prepared.model_dump(mode="json"),
        "preview_values": built.equipped.values,
    }


def _actor(payload: dict, *, identity: str, kind: str):
    from copy import deepcopy

    from src.backend.features.combat.dto import ActorLoadoutDTO, ActorMetaDTO, ActorRawDTO, ActorSnapshot
    from src.backend.features.combat.runtime.engine.stats_engine import StatsEngine

    actor = ActorSnapshot(
        meta=ActorMetaDTO(
            id=identity,
            name=payload["name"],
            type=kind,
            role=payload.get("role") if kind == "monster" else None,
            team="monster" if kind == "monster" else "player",
            is_ai=True,
            ai_archetype="balanced",
            ai_behavior_profile="balanced",
        ),
        raw=ActorRawDTO.model_validate(deepcopy(payload["raw"])),
        skills=deepcopy(payload["skills"]),
        loadout=ActorLoadoutDTO.model_validate(deepcopy(payload["loadout"])),
    )
    StatsEngine.ensure_stats(actor)
    for field in ("hp", "en", "stamina"):
        value = max(1, int(round(float(getattr(actor.stats.mods, field)))))
        setattr(actor.meta, field, value)
        setattr(actor.meta, f"max_{field}", value)
    return actor


async def run_case(
    config: ProbeConfig,
    player_key: str,
    player: dict,
    encounter_type: str,
    difficulty: str,
    *,
    saved_rosters: dict[int, dict] | None = None,
) -> dict:
    from src.backend.features.combat.dto import FeintHandDTO
    from src.backend.features.combat.dto.action import CombatMoveDTO
    from src.backend.features.combat.dto.payloads import ExchangePayload
    from src.backend.features.combat.runtime.simulation import (
        InMemoryBattleFactory,
        InMemoryBattleLimits,
        InMemoryCombatSimulator,
    )
    from src.backend.features.combat.runtime.simulation.intent_provider import AiSimulationIntentProvider
    from src.backend.features.monsters.catalog import get_catalog
    from src.backend.features.monsters.encounters.dto.selection import MonsterEncounterOrderDTO
    from src.backend.features.monsters.encounters.policies.admission import MonsterAdmissionPolicyResolver
    from src.backend.features.monsters.encounters.services.squad_selection_service import (
        MonsterEncounterSelectionService,
    )
    from src.backend.features.monsters.instances.services.build_readiness import MonsterBuildReadinessService

    class IntentProvider(AiSimulationIntentProvider):
        def __init__(self):
            super().__init__()
            self.feint_picks_by_team = Counter()

        def choose_moves(self, state, actor):
            enabled = config.feints == "both" or config.feints == (
                "monsters" if actor.meta.team == "monster" else "player"
            )
            if enabled:
                moves = super().choose_moves(state, actor)
                self.feint_picks_by_team[actor.meta.team] += sum(
                    bool(getattr(move.payload, "feint_id", None)) for move in moves
                )
                return moves
            return [
                CombatMoveDTO(
                    move_id=f"basic-{state.round_index}-{actor.meta.id}-{i}",
                    char_id=actor.meta.id,
                    strategy="exchange",
                    payload=ExchangePayload(target_id=target.meta.id),
                )
                for i, target in enumerate(self._candidate_targets(state, actor))
            ]

    catalog = get_catalog()
    selector = MonsterEncounterSelectionService()
    intent_provider = IntentProvider()
    simulator = InMemoryCombatSimulator(intent_provider=intent_provider)
    artifact = None
    fights, rosters, monsters = [], {}, {}
    previous = random.getstate()
    fixed_reasons = []
    fixed_members = []
    if config.mode == "fixed":
        admission = MonsterAdmissionPolicyResolver().resolve(config.tier)
        for identity, count in config.members:
            member = catalog.members[identity]
            allowed = next(
                (
                    rule
                    for rule in admission.roles
                    if rule.role == member.role and rule.min_tier <= config.tier <= rule.max_tier
                ),
                None,
            )
            readiness = MonsterBuildReadinessService().check(
                member=member, family=catalog.families[config.family], tier=config.tier
            )
            if allowed is None:
                fixed_reasons.append({"code": "tier_not_admitted", "member_id": identity, "tier": config.tier})
            fixed_reasons.extend({"member_id": identity, **asdict(issue)} for issue in readiness.issues)
            fixed_members.extend(
                [
                    {
                        "member_id": identity,
                        "tier": config.tier,
                        "role": member.role,
                        "assembly_cost": member.assembly_cost,
                    }
                ]
                * count
            )
    try:
        for seed in range(config.seed, config.seed + config.battles):
            order = None
            pools = {}
            if saved_rosters is not None:
                saved = saved_rosters[seed]
                members = saved["members"]
                pools = saved.get("pools", {})
            elif config.mode == "encounter":
                order = MonsterEncounterOrderDTO(
                    encounter_type=encounter_type,
                    difficulty=difficulty,
                    party_mode="solo",
                    location_tier=config.tier,
                    family_ids=(config.family,),
                    seed=seed,
                    player_gear_score=player["gear_score"],
                )
                if artifact is None:
                    artifact = selector.build_pool(order)
                selected = selector.select_from_pool(order, artifact)
                if selected.status != "selected":
                    fights.append(
                        {
                            "seed": seed,
                            "status": "rejected",
                            "order": order.model_dump(mode="json"),
                            "reasons": [r.model_dump(mode="json") for r in selected.reasons],
                            "attempts": [a.model_dump(mode="json") for a in selected.attempts],
                        }
                    )
                    continue
                members = [m.model_dump(mode="json") for m in selected.selection.members]
                pools = {name: getattr(selected, name).model_dump(mode="json") for name in ("minions", "seniors")}
            else:
                if fixed_reasons:
                    fights.append({"seed": seed, "status": "rejected", "reasons": fixed_reasons})
                    continue
                members = fixed_members
            roster_id = digest(members)
            rosters.setdefault(roster_id, {"members": members, "pools": pools})
            pid = "a_player" if seed % 2 == 0 else "z_player"
            actors = [_actor(player, identity=pid, kind="player")]
            payloads = [player]
            for index, member in enumerate(members):
                key = f"{member['member_id']}@{member['tier']}"
                if key not in monsters:
                    monsters[key] = _monster_payload(catalog.members[member["member_id"]], member["tier"], catalog)
                payload = monsters[key]
                actors.append(_actor(payload, identity=f"m_{index:03}", kind="monster"))
                payloads.append(payload)
            for actor, payload in zip(actors, payloads, strict=True):
                enabled = config.feints == "both" or config.feints == (
                    "monsters" if actor.meta.team == "monster" else "player"
                )
                actor.meta.feints = FeintHandDTO(
                    arsenal=list(payload["loadout"].get("known_feints", [])) if enabled else [], hand={}
                )
            initial_arsenal_counts = {str(actor.meta.id): len(actor.meta.feints.arsenal) for actor in actors}
            intent_provider.feint_picks_by_team.clear()
            initial_hp = actors[0].meta.hp
            random.seed(seed)
            state = InMemoryBattleFactory.from_actors(
                actors, seed=seed, session_id=f"probe-{seed}", limits=InMemoryBattleLimits(max_rounds=config.max_rounds)
            )
            result = await simulator.run(state)
            player_actor = state.ctx.actors[pid]
            alive = player_actor.is_alive and not player_actor.meta.is_dead
            fights.append(
                {
                    "seed": seed,
                    "status": "completed",
                    "order": order.model_dump(mode="json") if order else None,
                    "roster_id": roster_id,
                    "members": members,
                    "pools": pools,
                    "winner": result.winner,
                    "completion_reason": result.completion_reason,
                    "rounds": result.rounds_completed,
                    "player_id": pid,
                    "alive": alive,
                    "initial_hp": initial_hp,
                    "final_hp": result.final_hp_by_actor,
                    "player_hp_fraction": result.final_hp_by_actor[pid] / initial_hp if alive else 0,
                    "monster_count": len(members),
                    "feint_pick_count": result.telemetry.feint_pick_count,
                    "initial_arsenal_counts": initial_arsenal_counts,
                    "feint_picks_by_team": dict(intent_provider.feint_picks_by_team),
                }
            )
    finally:
        random.setstate(previous)
    completed = [f for f in fights if f["status"] == "completed"]
    wins = Counter(f["winner"] for f in completed)
    ranks = Counter(
        ", ".join(f"{n} {role}" for role, n in sorted(Counter(m["role"] for m in f["members"]).items()))
        for f in completed
    )
    count = len(completed)
    survived = sum(f["alive"] for f in completed)
    summary = {
        "player_key": player_key,
        "mode": config.mode,
        "encounter_type": encounter_type,
        "difficulty": difficulty,
        "tier": config.tier,
        "requested": len(fights),
        "completed": count,
        "rejected": len(fights) - count,
        "player_wins": wins["player"],
        "monster_wins": wins["monster"],
        "draws": wins["draw"],
        "survived": survived,
        "survival_percent": round(100 * survived / count, 2) if count else None,
        "player_win_percent": round(100 * wins["player"] / count, 2) if count else None,
        "mean_player_hp_percent": round(100 * statistics.mean(f["player_hp_fraction"] for f in completed), 2)
        if count
        else None,
        "mean_rounds": statistics.mean(f["rounds"] for f in completed) if count else None,
        "median_rounds": statistics.median(f["rounds"] for f in completed) if count else None,
        "min_count": min((f["monster_count"] for f in completed), default=None),
        "max_count": max((f["monster_count"] for f in completed), default=None),
        "rank_distribution": dict(ranks),
        "feints_selected": sum(sum(f["feint_pick_count"].values()) for f in completed),
        "feint_picks_by_team": {
            team: sum(f["feint_picks_by_team"].get(team, 0) for f in completed) for team in ("player", "monster")
        },
        "artifact_variant_count": sum(len(g.variants) for g in artifact.groups) if artifact else None,
        "gear_score": player["gear_score"],
    }
    return {
        "summary": summary,
        "fights": fights,
        "rosters": rosters,
        "monsters": monsters,
        "artifact": artifact.model_dump(mode="json") if artifact else None,
    }


def _worker(config, key, player, kind, difficulty):
    from loguru import logger

    logger.remove()
    return asyncio.run(run_case(config, key, player, kind, difficulty))


def run_probe(config: ProbeConfig) -> dict:
    from src.backend.core.calculators.stats_waterfall_calculator import COMBAT_MATH_VERSION

    from .report import write_report

    before = source_fingerprint()
    if config.output is None:
        raise ValueError("Output directory is required")
    output = config.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError("Output directory must be empty; historical results are never overwritten")
    validate_catalog(config)
    if config.replay:
        manifest = json.loads(config.replay.read_text(encoding="utf-8"))
        if manifest["source_fingerprint"] != before and not config.allow_source_drift:
            raise ValueError(
                "Replay source fingerprint differs; --allow-source-drift makes this a new-source comparison, not an exact replay"
            )
        if digest(manifest["resolved_players"]) != manifest["players_sha256"]:
            raise ValueError("Replay resolved player checksum differs")
        players = {key: _validate_payload(payload, name=key) for key, payload in manifest["resolved_players"].items()}
    else:
        players = resolve_players(config)
    if not players:
        raise ValueError("At least one player is required")
    report = {
        "schema_version": 1,
        "metadata": {
            "status": "running",
            "started_at": datetime.now(UTC).isoformat(),
            "source_before": before,
            "combat_math_version": COMBAT_MATH_VERSION,
            "skills_comparable": len({digest(p["skills"]) for p in players.values()}) == 1,
            "limitations": [
                "Automatic balanced AI; no manual feint tactics.",
                "Finite seeded sample; not a guarantee of survival.",
                "Saved snapshots preserve raw/loadout; live starters are current T0 only.",
            ],
            "replay_origin": str(config.replay) if config.replay else None,
            "allow_source_drift": config.allow_source_drift,
        },
        "config": config.to_dict(),
        "players": {
            key: {
                field: p.get(field) for field in ("name", "source", "skills", "gear_score", "equipment_count", "regen")
            }
            for key, p in players.items()
        },
        "cases": [],
    }
    output.mkdir(parents=True, exist_ok=True)
    write_json(
        output / "manifest.json",
        {
            "schema_version": 1,
            "config": config.to_dict(),
            "source_fingerprint": before,
            "combat_math_version": COMBAT_MATH_VERSION,
            "resolved_players": players,
            "players_sha256": digest(players),
        },
    )
    write_json(output / "players.json", players)
    write_json(output / "summary.json", report)
    specifications = [
        (key, player, kind, difficulty)
        for key, player in players.items()
        for kind in (config.encounters if config.mode == "encounter" else ("fixed",))
        for difficulty in (config.difficulties if config.mode == "encounter" else ("fixed",))
    ]

    def save(index: int, result: dict) -> None:
        summary = result["summary"]
        slug = re.sub(r"[^a-zA-Z0-9_.-]", "_", summary["player_key"])[:50]
        identity = f"{index:03}-{slug}-{summary['encounter_type']}-{summary['difficulty']}"
        folder = output / identity
        files = {}
        for name in ("fights", "rosters", "monsters", "artifact"):
            if result[name] is not None:
                write_json(folder / f"{name}.json", result[name])
                files[name] = f"{identity}/{name}.json"
        summary.update(id=identity, files=files)
        report["cases"].append(summary)
        report["cases"].sort(key=lambda c: c["id"])
        write_json(output / "summary.json", report)
        write_report(output, report)
        print(
            f"{identity}: {summary['player_wins']}/{summary['completed']} wins; {summary['rejected']} rejected",
            flush=True,
        )

    if config.workers == 1:
        for index, (key, player, kind, difficulty) in enumerate(specifications):
            save(index, _worker(config, key, player, kind, difficulty))
    else:
        with ProcessPoolExecutor(max_workers=config.workers, mp_context=multiprocessing.get_context("spawn")) as pool:
            pending = {
                pool.submit(_worker, config, key, player, kind, difficulty): index
                for index, (key, player, kind, difficulty) in enumerate(specifications)
            }
            for future in as_completed(pending):
                save(pending[future], future.result())
    report["metadata"]["completed_at"] = datetime.now(UTC).isoformat()
    report["metadata"]["source_after"] = source_fingerprint()
    report["metadata"]["status"] = "completed" if before == report["metadata"]["source_after"] else "source_changed"
    write_json(output / "summary.json", report)
    write_report(output, report)
    return report
