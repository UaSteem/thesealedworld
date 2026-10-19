"""Compare lowered starter endurance against preserved and freshly selected squads."""

from __future__ import annotations

import argparse
import asyncio
import html
import json
import multiprocessing
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.monsters.balance_probe.config import ProbeConfig  # noqa: E402
from tools.monsters.balance_probe.players import _validate_payload  # noqa: E402
from tools.monsters.balance_probe.runner import digest, run_case, source_fingerprint, write_json  # noqa: E402
from tools.monsters.build_starter_style_suite import validate_attributes  # noqa: E402

TRANSFERS = {
    "test18.dual.stiletto.light": "intellect",
    "test18.dual.stiletto.medium": "intellect",
    "test18.ranged.shortbow.light": "intellect",
    "test18.ranged.longbow.light": "mental",
}


def lowered_player(player: dict, key: str) -> dict:
    from src.backend.features.character.runtime.combat_math_model import CharacterCombatMathModelBuilder

    result = deepcopy(player)
    context = result["input_context"]
    context["attributes"]["endurance"] -= 3
    context["attributes"][TRANSFERS[key]] += 3
    validate_attributes(context["attributes"])
    result["raw"] = CharacterCombatMathModelBuilder().build_raw(
        attributes=context["attributes"], items=context["items"], skills=result["skills"], symbiote=context["symbiote"]
    )
    result["source"] = dict(result.get("source", {}), endurance_delta=-3, transfer_to=TRANSFERS[key])
    return _validate_payload(result, name=key)


def saved_rosters(fights: list[dict]) -> dict[int, dict]:
    if len(fights) != 50 or any(f["status"] != "completed" for f in fights):
        raise ValueError("Baseline must contain 50 completed fights")
    result = {f["seed"]: {"members": deepcopy(f["members"]), "pools": deepcopy(f.get("pools", {}))} for f in fights}
    if len(result) != 50:
        raise ValueError("Duplicate baseline seeds")
    return result


def worker(config, key, player, difficulty, rosters):
    from loguru import logger

    logger.remove()
    return asyncio.run(run_case(config, key, player, "ordinary", difficulty, saved_rosters=rosters))


def write_report(output: Path, report: dict):
    rows = []
    for case in sorted(report["cases"], key=lambda c: (c["player_key"], c["difficulty"], c["comparison_mode"])):
        baseline = case["baseline"]
        rows.append(
            "<tr>"
            + "".join(
                f"<td>{html.escape(str(v))}</td>"
                for v in (
                    case["player_key"],
                    case["difficulty"],
                    case["comparison_mode"],
                    f"{baseline['gear_score']:.3f} → {case['gear_score']:.3f}",
                    f"{baseline['player_win_percent']} → {case['player_win_percent']}",
                    f"{baseline['survival_percent']} → {case['survival_percent']}",
                    f"{baseline['mean_player_hp_percent']} → {case['mean_player_hp_percent']}",
                    f"{baseline['min_count']}–{baseline['max_count']} → {case['min_count']}–{case['max_count']}",
                    case["feint_picks_by_team"],
                )
            )
            + "</tr>"
        )
    attrs = "".join(
        "<tr>"
        + "".join(
            f"<td>{html.escape(str(v))}</td>"
            for v in (
                key,
                p["before_attributes"],
                p["after_attributes"],
                p["old_hp"],
                p["new_hp"],
                p["old_gs"],
                p["new_gs"],
            )
        )
        + "</tr>"
        for key, p in report["players"].items()
    )
    page = (
        """<!doctype html><meta charset="utf-8"><title>Endurance T0 comparison</title>
<style>body{font:15px system-ui;background:#121820;color:#e5ebf2;padding:24px}table{border-collapse:collapse}td,th{padding:8px;border:1px solid #394555}a{color:#9cf}</style>
<h1>Снижение выносливости · T0 · гоблины</h1>
<p>У четырёх тестовых слепков END −3; очки перенесены в интеллект или ментальность. Пул 135, разрыв ≤8, значения внутри троек различаются. Предметы, навыки и арсеналы прежние.</p>
<p>На каждую сложность и слепок: 50 боёв против точных прежних отрядов и 50 через новый подбор. Те же seed 0–49, автоматические финты обеих сторон. Прежние результаты взяты из сохранённого отчёта. Перенос затрагивает также эффекты принимающего атрибута; это не изолированный тест одного HP.</p>
<p>Старый → новый. Остаток HP усреднён по всем боям, поражения дают 0. Победы и выживаемость показаны раздельно. Боевые формулы и база не менялись.</p>
<h2>Атрибуты и слепки</h2><table><tr><th>Слепок</th><th>До</th><th>После</th><th>HP до</th><th>HP после</th><th>GS до</th><th>GS после</th></tr>"""
        + attrs
        + """</table>
<h2>Бои</h2><table><tr><th>Слепок</th><th>Сложность</th><th>Подбор</th><th>GS</th><th>Победы %</th><th>Выжили %</th><th>Средний остаток HP %</th><th>Число врагов</th><th>Выборы финтов после</th></tr>"""
        + "".join(rows)
        + """</table><p><a href="report.json">Все результаты JSON</a> · <a href="players.json">Новые слепки</a></p>"""
    )
    (output / "report.html").write_text(page, encoding="utf-8")
    write_json(output / "report.json", report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline",
        type=Path,
        required=True,
        help="Explicit historical baseline directory; never inferred from ignored var",
    )
    parser.add_argument("--output", type=Path, default=ROOT / "var/starter-endurance-t0")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError("Output must be empty")
    baseline = json.loads((args.baseline / "summary.json").read_text(encoding="utf-8"))
    old_players = json.loads((args.baseline / "players.json").read_text(encoding="utf-8"))
    players = {key: lowered_player(old_players[key], key) for key in TRANSFERS}
    config = ProbeConfig.from_dict(baseline["config"])
    fingerprint = source_fingerprint()
    report = {
        "metadata": {
            "status": "running",
            "source_before": fingerprint,
            "baseline_source": baseline["metadata"]["source_before"],
            "baseline_path": str(args.baseline),
            "baseline_summary_digest": digest(baseline),
        },
        "players": {},
        "cases": [],
    }
    for key, player in players.items():
        old = _validate_payload(old_players[key], name=key)
        if old["gear_score"] != old_players[key]["gear_score"]:
            raise ValueError("Current GS changed from baseline")
        report["players"][key] = dict(
            before_attributes=old["input_context"]["attributes"],
            after_attributes=player["input_context"]["attributes"],
            old_hp=old["preview_values"]["hp"],
            new_hp=player["preview_values"]["hp"],
            old_gs=old["gear_score"],
            new_gs=player["gear_score"],
        )
    write_json(args.output / "players.json", players)
    write_json(
        args.output / "manifest.json",
        {
            "source_fingerprint": fingerprint,
            "config": config.to_dict(),
            "baseline_digest": digest(baseline),
            "players_sha256": digest(players),
        },
    )
    specifications = []
    for case in baseline["cases"]:
        if case["player_key"] not in players:
            continue
        fights = json.loads((args.baseline / case["files"]["fights"]).read_text(encoding="utf-8"))
        rosters = saved_rosters(fights)
        for mode in ("preserved", "new_selection"):
            specifications.append((case, mode, rosters if mode == "preserved" else None))
    with ProcessPoolExecutor(max_workers=args.workers, mp_context=multiprocessing.get_context("spawn")) as pool:
        futures = {
            pool.submit(worker, config, case["player_key"], players[case["player_key"]], case["difficulty"], rosters): (
                case,
                mode,
                rosters,
            )
            for case, mode, rosters in specifications
        }
        for future in as_completed(futures):
            old_case, mode, rosters = futures[future]
            result = future.result()
            if result["summary"]["completed"] != 50 or result["summary"]["rejected"]:
                raise ValueError("Expected 50 completed fights")
            for fight in result["fights"]:
                if not all(fight["initial_arsenal_counts"].values()):
                    raise ValueError("Missing arsenal")
                if rosters is not None and fight["members"] != rosters[fight["seed"]]["members"]:
                    raise ValueError("Preserved roster differs")
            if not all(result["summary"]["feint_picks_by_team"].values()):
                raise ValueError("Feints not used by both teams")
            case = result["summary"]
            case.update(comparison_mode=mode, baseline=old_case)
            identity = f"{case['player_key']}-{case['difficulty']}-{mode}"
            case["files"] = {}
            for name in ("fights", "rosters", "monsters", "artifact"):
                if result[name] is not None:
                    path = f"{identity}/{name}.json"
                    write_json(args.output / path, result[name])
                    case["files"][name] = path
            report["cases"].append(case)
            write_report(args.output, report)
            print(f"{identity}: {case['player_wins']}/50 wins", flush=True)
    report["metadata"].update(source_after=source_fingerprint(), status="completed")
    if report["metadata"]["source_after"] != fingerprint:
        report["metadata"]["status"] = "source_changed"
        write_report(args.output, report)
        raise ValueError("Source changed during run")
    report["metadata"]["new_battles"] = sum(c["completed"] for c in report["cases"])
    write_report(args.output, report)


if __name__ == "__main__":
    main()
