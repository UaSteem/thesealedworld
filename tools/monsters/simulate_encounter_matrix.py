"""Read-only, reproducible encounter-contract balance matrix using real Combat."""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import html
import json
import multiprocessing
import random
import statistics
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from loguru import logger  # noqa: E402
from tools.monsters.simulate_balance_chain import (  # noqa: E402
    build_chain_inputs,
    digest,
    source_fingerprint,
    write_json,
)
from tools.monsters.simulate_catalog_duel import build_actor  # noqa: E402

from src.backend.core.calculators.stats_waterfall_calculator import StatsWaterfallCalculator  # noqa: E402
from src.backend.features.character.runtime.combat_actor_input import CharacterCombatActorInputBuilder  # noqa: E402
from src.backend.features.character.runtime.combat_math_model import CharacterCombatMathModelBuilder  # noqa: E402
from src.backend.features.character.runtime.gear_score import CharacterGearScoreCalculator  # noqa: E402
from src.backend.features.character.runtime.rules.base_power_assembler import BasePowerAssembler  # noqa: E402
from src.backend.features.combat.dto import FeintHandDTO  # noqa: E402
from src.backend.features.combat.dto.action import CombatMoveDTO  # noqa: E402
from src.backend.features.combat.dto.payloads import ExchangePayload  # noqa: E402
from src.backend.features.combat.runtime.simulation import (  # noqa: E402
    InMemoryBattleFactory,
    InMemoryBattleLimits,
    InMemoryCombatSimulator,
)
from src.backend.features.combat.runtime.simulation.intent_provider import AiSimulationIntentProvider  # noqa: E402
from src.backend.features.items.dto.instance import GeneratedItemDTO  # noqa: E402
from src.backend.features.items.services.catalog_service import ItemCatalogService  # noqa: E402
from src.backend.features.monsters.catalog import get_catalog  # noqa: E402
from src.backend.features.monsters.catalog.prepared_equipment import get_member_prepared_equipment  # noqa: E402
from src.backend.features.monsters.encounters.dto.selection import MonsterEncounterOrderDTO  # noqa: E402
from src.backend.features.monsters.encounters.services.squad_selection_service import (  # noqa: E402
    MonsterEncounterSelectionService,
)
from src.backend.features.monsters.instances.services.instance_builder import MonsterInstanceBuilder  # noqa: E402

ENCOUNTERS = ("ordinary", "patrol", "guard", "leader")
DIFFICULTIES = ("easy", "normal", "hard")


class BasicAttackIntentProvider(AiSimulationIntentProvider):
    """Keep simulator target ordering/count; submit only plain exchanges."""

    def choose_moves(self, state, actor):
        return [
            CombatMoveDTO(
                move_id=f"basic-{state.round_index}-{actor.meta.id}-{index}",
                char_id=actor.meta.id,
                strategy="exchange",
                payload=ExchangePayload(target_id=target.meta.id),
            )
            for index, target in enumerate(self._candidate_targets(state, actor))
        ]


def build_player(tier, player_input=None):
    if player_input is None:
        player = build_chain_inputs("goblin_tribe.base.goblin_sneak", tier, tier, 0.2)["player"]
    else:
        saved = json.loads(player_input.read_text(encoding="utf-8"))
        if saved.get("tier", saved.get("player_tier")) != tier:
            raise ValueError("Saved player input tier differs from requested tier")
        player = saved["player"]
        skills = {key: 0.2 for key in player["skills"]}
        catalog = ItemCatalogService.load_default()
        items = {"layout": {"equipment": {}}, "by_id": {}}
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
            attributes=player["input_attributes"], items=items, skills=skills, symbiote={"gift_rank": max(1, tier + 1)}
        )
        values, _ = StatsWaterfallCalculator.calculate_waterfall(raw)
        loadout = CharacterCombatActorInputBuilder._loadout(items, skills, include_basic_gift_abilities=False)
        BasePowerAssembler.apply_to_values(values, loadout_layout=loadout["layout"], skills=skills)
        player.update(raw=raw, skills=skills, loadout=loadout, preview_values=values)
    slots = [item["slot"] for item in player["equipment"]]
    if len(slots) != 16 or len(set(slots)) != 16:
        raise ValueError("Reference player must have sixteen distinct equipment slots")
    if not {"ring_1", "ring_2", "amulet", "earring", "main_hand", "off_hand"} <= set(slots):
        raise ValueError("Full dual-blades reference equipment is required")
    return player


def monster_payload(member, catalog):
    definition = catalog.members[member.member_id]
    prepared = get_member_prepared_equipment(member=definition, tier=member.tier)
    build = MonsterInstanceBuilder().build(
        member=definition, family=catalog.families[definition.family_id], prepared=prepared
    )
    return {
        "name": definition.name,
        "role": definition.role,
        "raw": build.equipped.raw,
        "skills": build.skills,
        "loadout": build.equipped.loadout,
        "equipment": prepared.model_dump(mode="json"),
        "preview_values": build.equipped.values,
    }


async def run_case(config, player, encounter_type, difficulty):
    catalog = get_catalog()
    selector = MonsterEncounterSelectionService()
    simulator = InMemoryCombatSimulator(
        intent_provider=AiSimulationIntentProvider() if config["feints"] else BasicAttackIntentProvider()
    )
    payloads, fights, rosters = {}, [], {}
    previous_random = random.getstate()
    try:
        for index in range(config["battles"]):
            seed = config["seed"] + index
            order = MonsterEncounterOrderDTO(
                encounter_type=encounter_type,
                difficulty=difficulty,
                party_mode="solo",
                location_tier=config["tier"],
                family_ids=("goblin_tribe",),
                seed=seed,
                player_gear_score=config["player_gear_score"],
            )
            selected = selector.select(order)
            if selected.status != "selected":
                fights.append(
                    {
                        "seed": seed,
                        "status": "rejected",
                        "order": order.model_dump(mode="json"),
                        "reasons": [r.model_dump(mode="json") for r in selected.reasons],
                    }
                )
                continue
            members = selected.selection.members
            roster_id = digest(sorted((m.member_id, m.tier) for m in members))
            rosters.setdefault(roster_id, selected.model_dump(mode="json"))
            player_id = "z_player" if index % 2 else "a_player"
            actors = [build_actor(player, actor_id=player_id, team="player", kind="player")]
            actors[0].meta.feints = FeintHandDTO(
                arsenal=list(player["loadout"].get("known_feints", [])) if config["feints"] else [], hand={}
            )
            for number, member in enumerate(members):
                key = (member.member_id, member.tier)
                if key not in payloads:
                    payloads[key] = monster_payload(member, catalog)
                actors.append(build_actor(payloads[key], actor_id=f"m_{number:03}", team="monster", kind="monster"))
                actors[-1].meta.feints = FeintHandDTO(
                    arsenal=list(payloads[key]["loadout"].get("known_feints", [])) if config["feints"] else [], hand={}
                )
            initial_hp = {str(a.meta.id): a.meta.hp for a in actors}
            random.seed(seed)
            state = InMemoryBattleFactory.from_actors(
                actors,
                seed=seed,
                session_id=f"contract-{seed}",
                limits=InMemoryBattleLimits(max_rounds=config["max_rounds"]),
            )
            result = await simulator.run(state)
            if not config["feints"] and result.telemetry.feint_pick_count:
                raise AssertionError("A feint was selected in a basic-attack diagnostic")
            alive = {str(a.meta.id): a.is_alive and not a.meta.is_dead for a in state.ctx.actors.values()}
            fights.append(
                {
                    "seed": seed,
                    "status": "completed",
                    "roster_id": roster_id,
                    "winner": result.winner,
                    "rounds": result.rounds_completed,
                    "completion_reason": result.completion_reason,
                    "player_id": player_id,
                    "initial_hp": initial_hp,
                    "final_hp": result.final_hp_by_actor,
                    "alive": alive,
                    "player_hp_fraction": (result.final_hp_by_actor[player_id] / initial_hp[player_id])
                    if alive[player_id]
                    else 0,
                    "monster_count": len(members),
                    "budget": selected.budget_effective,
                    "spent": selected.budget_spent,
                    "feint_pick_count": result.telemetry.feint_pick_count,
                }
            )
    finally:
        random.setstate(previous_random)
    return (
        summarize(encounter_type, difficulty, fights),
        fights,
        rosters,
        {f"{key[0]}@{key[1]}": value for key, value in payloads.items()},
    )


def summarize(encounter_type, difficulty, fights):
    completed = [f for f in fights if f["status"] == "completed"]
    wins = Counter(f["winner"] for f in completed)
    return {
        "encounter_type": encounter_type,
        "difficulty": difficulty,
        "requested": len(fights),
        "completed": len(completed),
        "rejected": len(fights) - len(completed),
        "feints_selected": sum(sum(f.get("feint_pick_count", {}).values()) for f in completed),
        "player_wins": wins["player"],
        "monster_wins": wins["monster"],
        "draws": wins["draw"],
        "player_win_percent": round(100 * wins["player"] / len(completed), 2) if completed else None,
        "median_rounds": statistics.median(f["rounds"] for f in completed) if completed else None,
        "mean_player_hp_percent": round(100 * statistics.mean(f["player_hp_fraction"] for f in completed), 2)
        if completed
        else None,
        "min_count": min((f["monster_count"] for f in completed), default=None),
        "max_count": max((f["monster_count"] for f in completed), default=None),
        "unique_rosters": len({f["roster_id"] for f in completed}),
        "completion_reasons": dict(Counter(f["completion_reason"] for f in completed)),
    }


def worker(config, player, encounter_type, difficulty):
    logger.remove()
    return asyncio.run(run_case(config, player, encounter_type, difficulty))


def render_report(output, report):
    rows = report["cases"]
    if not rows:
        return
    fields = [k for k in rows[0] if k != "completion_reasons"]
    with (output / "summary.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    labels = {
        "ordinary": "Обычная",
        "patrol": "Патруль",
        "guard": "Охрана",
        "leader": "Главарь",
        "easy": "Лёгкая",
        "normal": "Средняя",
        "hard": "Тяжёлая",
    }
    body = "".join(
        "<tr>"
        + "".join(
            f"<td>{html.escape(str(value))}</td>"
            for value in (
                labels[row["encounter_type"]],
                labels[row["difficulty"]],
                row["completed"],
                row["rejected"],
                row["player_wins"],
                row["monster_wins"],
                row["draws"],
                row["player_win_percent"],
                row["mean_player_hp_percent"],
                row["median_rounds"],
                f"{row['min_count']}–{row['max_count']}",
                row["unique_rosters"],
            )
        )
        + "</tr>"
        for row in rows
    )
    page = f"""<!doctype html><html lang="ru"><meta charset="utf-8"><title>Гоблины: базовый замер</title>
<style>body{{font:15px system-ui;margin:30px;color:#172033;background:#f4f6fa}}table{{border-collapse:collapse;background:white}}td,th{{padding:10px;border:1px solid #d9dfeb;text-align:left}}.scroll{{overflow:auto}}p{{max-width:1000px}}</style>
<h1>Гоблины Т{report["config"]["tier"]}: базовый замер</h1>
<p>Полный комплект под два клинка: 16 предметов, 4 украшения. Боевые навыки 20%. {"Автоматические финты у обеих сторон" if report["config"]["feints"] else "Только обычные удары у обеих сторон"}; пассивные эффекты экипировки и регенерация сохранены. Составы получены через текущий контракт Monsters. Формулы, баланс и база не менялись.</p>
<p>GS игрока: {report["config"]["player_gear_score"]}. Seed: {report["config"]["seed"]}–{report["config"]["seed"] + report["config"]["battles"] - 1}. Лимит боя: {report["config"]["max_rounds"]} раундов. Отказы не считаются поражениями. Остаток HP — средний по всем завершённым боям, погибшему игроку засчитывается 0.</p>
<div class="scroll"><table><tr>{"".join("<th>" + v + "</th>" for v in ("Встреча", "Сложность", "Бои", "Отказы", "Победы игрока", "Победы монстров", "Ничьи", "Победы, %", "Остаток HP, %", "Раунды, медиана", "Бойцов", "Разных составов"))}</tr>{body}</table></div>
<p>Состояние: {html.escape(report["status"])}. Это проверка одной сборки и выбранных seed, не общий вывод о балансе.</p></html>"""
    (output / "report.html").write_text(page, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feints", action="store_true", help="Use automatic AI feints for both teams")
    parser.add_argument("--tier", type=int, choices=range(6), default=0)
    parser.add_argument("--battles", type=int, default=50)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-rounds", type=int, default=100)
    parser.add_argument("--workers", type=int, choices=range(1, 4), default=2)
    parser.add_argument("--player-input", type=Path, help="Saved curated player inputs; current math is rebuilt")
    parser.add_argument("--output", type=Path, default=ROOT / "var/goblin-encounter-t0-baseline")
    args = parser.parse_args()
    if args.battles < 1 or args.max_rounds < 1:
        parser.error("battles and max-rounds must be positive")
    logger.remove()
    player = build_player(args.tier, args.player_input)
    config = {
        "schema_version": 1,
        "source_fingerprint": source_fingerprint(),
        "tier": args.tier,
        "battles": args.battles,
        "seed": args.seed,
        "max_rounds": args.max_rounds,
        "player_mastery": 0.2,
        "player_digest": digest(player),
        "feints": args.feints,
        "player_source": "current Studio full reference gear; current Character math; mastery 20%",
        "saved_player_path": str(args.player_input.resolve()) if args.player_input else None,
        "saved_player_sha256": hashlib.sha256(args.player_input.read_bytes()).hexdigest()
        if args.player_input
        else None,
        "equipment_sha256": digest(player["equipment"]),
        "player_gear_score": CharacterGearScoreCalculator.calculate_from_raw(
            player["raw"], skills=player["skills"], loadout=player["loadout"]
        ),
    }
    fingerprint = digest(config)
    path = args.output / "summary.json"
    if path.exists():
        report = json.loads(path.read_text(encoding="utf-8"))
        if report["config_hash"] != fingerprint:
            raise ValueError("Output belongs to different inputs/source; choose a fresh directory")
    else:
        if args.output.exists() and any(args.output.iterdir()):
            raise ValueError("Output must be empty or a compatible matrix report")
        report = {"config": config, "config_hash": fingerprint, "status": "running", "cases": []}
    write_json(args.output / "player-inputs.json", player)
    with ProcessPoolExecutor(max_workers=args.workers, mp_context=multiprocessing.get_context("spawn")) as pool:
        pending = []
        done = {(r["encounter_type"], r["difficulty"]) for r in report["cases"]}
        for encounter_type in ENCOUNTERS:
            for difficulty in DIFFICULTIES:
                if (encounter_type, difficulty) not in done:
                    pending.append(pool.submit(worker, config, player, encounter_type, difficulty))
        for future in pending:
            summary, fights, rosters, monsters = future.result()
            folder = args.output / f"{summary['encounter_type']}-{summary['difficulty']}"
            for name, data in (("fights", fights), ("rosters", rosters), ("monsters", monsters), ("summary", summary)):
                write_json(folder / f"{name}.json", data)
            report["cases"].append(summary)
            write_json(path, report)
            render_report(args.output, report)
            print(json.dumps(summary, ensure_ascii=False), flush=True)
    report["source_fingerprint_after"] = source_fingerprint()
    report["status"] = (
        "completed" if report["source_fingerprint_after"] == config["source_fingerprint"] else "invalid_source_changed"
    )
    write_json(path, report)
    render_report(args.output, report)


if __name__ == "__main__":
    main()
