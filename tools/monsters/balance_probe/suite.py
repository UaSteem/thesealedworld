"""Repeatable starter/full-equipment comparison through the balance probe."""

from __future__ import annotations

import argparse
import csv
import html
from datetime import UTC, datetime
from pathlib import Path

from .config import ProbeConfig
from .runner import run_probe, source_fingerprint, write_json

ENCOUNTERS = ("ordinary", "patrol", "guard", "leader")
LABELS = {"ordinary": "Встреча", "patrol": "Патруль", "guard": "Охрана", "leader": "Главарь"}


def _escape(value):
    return html.escape(str(value), quote=True)


def _percent(value):
    return "—" if value is None else f"{value:.1f}%"


def suite_rows(batches):
    rows = []
    for batch in batches:
        for case in batch["report"]["cases"]:
            player = batch["report"]["players"][case["player_key"]]
            rows.append(
                {
                    "batch": batch["id"],
                    "player": case["player_key"],
                    "name": player["name"],
                    "tier": case["tier"],
                    "encounter": case["encounter_type"],
                    "gs": player["gear_score"],
                    "equipment_count": player["equipment_count"],
                    **{
                        key: case[key]
                        for key in (
                            "requested",
                            "completed",
                            "rejected",
                            "player_wins",
                            "monster_wins",
                            "draws",
                            "survival_percent",
                            "mean_player_hp_percent",
                            "mean_rounds",
                            "min_count",
                            "max_count",
                        )
                    },
                    "rank_distribution": case["rank_distribution"],
                    "report": f"{batch['id']}/report.html",
                }
            )
    return rows


def write_suite_report(output, state):
    rows = suite_rows(state["batches"])
    write_json(output / "summary.json", {**state, "rows": rows})
    fields = (
        "batch",
        "player",
        "name",
        "tier",
        "encounter",
        "gs",
        "equipment_count",
        "requested",
        "completed",
        "rejected",
        "player_wins",
        "monster_wins",
        "draws",
        "survival_percent",
        "mean_player_hp_percent",
        "mean_rounds",
        "min_count",
        "max_count",
        "rank_distribution",
        "report",
    )
    with (output / "summary.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    body = []
    for row in rows:
        count = "—" if row["min_count"] is None else f"{row['min_count']}–{row['max_count']}"
        color = "good" if (row["survival_percent"] or 0) >= 95 else "warn"
        body.append(
            f"<tr><th>{_escape(row['name'])}</th><td>{_escape(row['batch'])}</td>"
            f"<td>{_escape(LABELS[row['encounter']])}</td><td>{row['gs']:.3f}</td>"
            f"<td>{row['equipment_count']}</td><td>{count}</td>"
            f"<td>{row['player_wins']}/{row['completed']}</td>"
            f"<td class='{color}'>{_percent(row['survival_percent'])}</td>"
            f"<td>{_percent(row['mean_player_hp_percent'])}</td>"
            f"<td>{row['rejected']}</td><td>{row['draws']}</td>"
            f"<td><a href='{row['report']}'>Подробно</a></td></tr>"
        )
    requested = sum(r["requested"] for r in rows)
    completed = sum(r["completed"] for r in rows)
    rejected = sum(r["rejected"] for r in rows)
    document = f"""<!doctype html><html lang="ru"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Стартовые билды Т0–Т4</title>
<style>body{{background:#101722;color:#e4edf8;font:15px/1.5 system-ui;padding:24px}}
a{{color:#9cf}}table{{border-collapse:collapse;width:100%}}th,td{{text-align:left;padding:9px;border-bottom:1px solid #354357}}
thead{{background:#1c293a}}.scroll{{overflow:auto}}.good{{color:#8de0a9}}.warn{{color:#f1bf73}}p{{max-width:1100px}}</style>
<h1>Стартовые билды и полные боевые комплекты Т0–Т4</h1>
<p>Состояние: {_escape(state["status"])}. Запрошено: {requested}; состоялось боёв: {completed}; отказов: {rejected}.</p>
<p>Семья: {_escape(state["family"])}; сложность лёгкая; финты у обеих сторон; {state["battles"]} seed на сценарий.
У каждого билда сохранены его родные атрибуты, симбиот и навыки на всех тирах. Это проверка роста экипировки;
прокачка навыков, ручная тактика и будущая магия не моделируются. Разные билды имеют разные навыки.</p>
<p>GS каждой сборки передаётся текущему сборщику: смена предметов может менять и состав противников.
Поэтому сравнение стартового и полного комплекта не изолирует только силу экипировки.
На высоких тирах сохранены реальные штрафы рассинхронизации предметов с начальным симбиотом и навыками.</p>
<p>Стартовые слепки проверяются на Т0, полные — против своего тира. Т4 допускает до четырёх аффиксов;
четыре обязательны на Т5. Здесь целевое число аффиксов по тирам — 0/1/2/3/4, если полезный пул позволяет. Полные наборы — полезные согласованные предметы со средними роллами,
а не доказанный глобальный максимум всех возможных билдов.</p>
<p>Отказы Monsters не являются поражениями. Проценты считаются только по состоявшимся боям.
50 боёв дают предварительную оценку: даже 50/50 не гарантирует безопасность при окончательной смерти персонажа.</p>
<p><a href="equipment.html">Предметы и характеристики всех комплектов</a> · <a href="summary.csv">CSV</a> ·
<a href="summary.json">Полный JSON</a></p>
<div class="scroll"><table><thead><tr><th>Билд</th><th>Серия</th><th>Тип</th><th>GS</th><th>Предметов</th>
<th>Противников</th><th>Победы</th><th>Выжили</th><th>Остаток HP</th><th>Отказы</th><th>Ничьи</th><th></th></tr></thead>
<tbody>{"".join(body)}</tbody></table></div><p>Начало: {_escape(state["started_at"])}.
Конец: {_escape(state.get("completed_at", "в работе"))}. Источники: {_escape(state["source_before"])}.</p></html>"""
    (output / "report.html").write_text(document, encoding="utf-8")


def write_equipment_report(output, players):
    parts = []
    for key, player in players.items():
        values = player["preview_values"]
        items = []
        for item in player.get("equipment_review", []):
            affixes = "; ".join(f"{a['affix_id']}: {a['value']}" for a in item["affixes"])
            items.append(
                "<tr>"
                + "".join(
                    f"<td>{_escape(v)}</td>"
                    for v in (
                        item["slot"],
                        item.get("name", item["base_id"]),
                        item["material_id"],
                        item["rarity_tier"],
                        affixes or "—",
                    )
                )
                + "</tr>"
            )
        parts.append(
            f"<details><summary>{_escape(key)} · GS {player['gear_score']:.3f} · "
            f"HP {values['hp']:.1f} · броня {values.get('armor', 0):.1f}</summary>"
            f"<p>Навыки: {_escape(player['skills'])}</p><p>Реген: {_escape(player['regen'])}</p>"
            f"<p>Примечания: {_escape(player.get('build_notes', []))}</p>"
            "<table><thead><tr><th>Слот</th><th>Предмет</th><th>Материал</th><th>Редкость</th><th>Аффиксы</th>"
            f"</tr></thead><tbody>{''.join(items)}</tbody></table></details>"
        )
    document = """<!doctype html><html lang="ru"><meta charset="utf-8"><title>Комплекты Т0–Т4</title>
<style>body{background:#101722;color:#e4edf8;font:15px/1.5 system-ui;padding:24px}a{color:#9cf}
details{padding:12px;border:1px solid #354357;margin:10px 0}table{border-collapse:collapse;width:100%}
td,th{text-align:left;padding:8px;border-bottom:1px solid #354357}</style><h1>Боевые комплекты</h1>
<p><a href="report.html">К результатам</a> · <a href="full-players.json">Полные входные слепки</a></p>""" + "".join(
        parts
    )
    (output / "equipment.html").write_text(document + "</html>", encoding="utf-8")


def main(argv=None):
    from loguru import logger

    from src.backend.features.combat.runtime.simulation.starting_imprint_actors import (
        DEFAULT_STARTER_SIMULATION_IMPRINTS,
    )

    from .equipment import build_full_players

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--battles", type=int, default=50)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--family", default="goblin_tribe")
    parser.add_argument("--players", nargs="+", default=DEFAULT_STARTER_SIMULATION_IMPRINTS)
    parser.add_argument("--tiers", nargs="+", type=int, default=list(range(5)))
    args = parser.parse_args(argv)
    if args.battles < 1 or args.workers < 1 or any(t not in range(5) for t in args.tiers):
        parser.error("positive battles/workers and tiers 0..4 required")
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error("output must be new or empty")
    logger.remove()
    before = source_fingerprint()
    players = build_full_players(tuple(args.players), tuple(args.tiers))
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "full-players.json", players)
    write_equipment_report(output, players)
    state = {
        "status": "running",
        "started_at": datetime.now(UTC).isoformat(),
        "source_before": before,
        "family": args.family,
        "battles": args.battles,
        "batches": [],
    }
    write_suite_report(output, state)
    batches = [("native-t0", 0, None, tuple(args.players))]
    for tier in args.tiers:
        keys = tuple(key for key, player in players.items() if player["source"]["tier"] == tier)
        path = output / f"inputs-t{tier}.json"
        write_json(path, {key: players[key] for key in keys})
        batches.append((f"full-t{tier}", tier, path, keys))
    for batch_id, tier, path, keys in batches:
        report = run_probe(
            ProbeConfig(
                family=args.family,
                tier=tier,
                players=keys if path is None else (),
                player_input=path,
                player_keys=keys if path else (),
                player_tier=tier if path else None,
                encounters=ENCOUNTERS,
                difficulties=("easy",),
                battles=args.battles,
                seed=args.seed,
                workers=args.workers,
                output=output / batch_id,
            )
        )
        state["batches"].append({"id": batch_id, "report": report})
        write_suite_report(output, state)
    state["source_after"] = source_fingerprint()
    state["status"] = "completed" if before == state["source_after"] else "source_changed"
    state["completed_at"] = datetime.now(UTC).isoformat()
    write_suite_report(output, state)
    print(f"Suite report: {output / 'report.html'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
