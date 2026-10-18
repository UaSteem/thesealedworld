"""Experimental starter allocations; production imprints and combat stay untouched."""

from __future__ import annotations

import argparse
import html
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

from .config import ProbeConfig
from .players import _live_player, _validate_payload
from .runner import run_probe, source_fingerprint, write_json

ATTRIBUTES = (
    "strength",
    "agility",
    "endurance",
    "intellect",
    "memory",
    "mental",
    "perception",
    "projection",
    "prediction",
)
ROSTERS = {
    "ordinary": (("goblin_scavenger", 2), ("goblin_sparkpick", 1)),
    "patrol": (("goblin_spearman", 1), ("goblin_scavenger", 1), ("goblin_sneak", 1)),
    "guard": (("goblin_trapmaster", 1), ("goblin_scavenger", 2)),
    "leader": (("scrap_king", 1), ("goblin_sneak", 2)),
}


def validate_allocation(attributes):
    if set(attributes) != set(ATTRIBUTES) or any(type(v) is not int or v < 0 for v in attributes.values()):
        raise ValueError("All nine attributes must be nonnegative integers")
    if sum(attributes.values()) != 135 or max(attributes.values()) - min(attributes.values()) > 8:
        raise ValueError("Allocation requires sum 135 and maximum spread 8")


def replace_attributes(player, attributes, *, label):
    from src.backend.features.character.runtime.combat_math_model import CharacterCombatMathModelBuilder

    validate_allocation(attributes)
    result = deepcopy(player)
    context = result["input_context"]
    context["attributes"] = dict(attributes)
    result["raw"] = CharacterCombatMathModelBuilder().build_raw(**context, skills=result["skills"])
    result["name"] += f" · {label}"
    result["source"] = {
        "mode": "experimental_attribute_allocation",
        "label": label,
        "attributes": attributes,
        "budget": 135,
        "spread": max(attributes.values()) - min(attributes.values()),
    }
    return _validate_payload(result, name=result["name"])


def build_variants(plans):
    variants = {}
    for identity, attributes in plans.items():
        native = _live_player(identity, SimpleNamespace(mastery=None))
        variants[f"{identity}.original"] = native
        variants[f"{identity}.uniform135"] = replace_attributes(native, dict.fromkeys(ATTRIBUTES, 15), label="15 each")
        variants[f"{identity}.tailored135"] = replace_attributes(native, attributes, label="tailored135")
    return variants


def write_overview(output, state, players):
    def esc(value):
        return html.escape(str(value), quote=True)

    records = {}
    for batch in state["batches"]:
        for case in batch["report"]["cases"]:
            records[(batch["id"], case["player_key"], case["encounter_type"])] = case
    rows = []
    for key, player in players.items():
        attrs = player["input_context"]["attributes"]
        v = player["preview_values"]
        cells = []
        for kind in ROSTERS:
            c = records.get((f"fixed-{kind}", key, "fixed"))
            cells.append("—" if c is None else f"{c['player_wins']}/{c['completed']} ({c['survival_percent']}%)")
        rows.append(
            f"<tr><th>{esc(key)}</th><td>{esc('/'.join(str(attrs[a]) for a in ATTRIBUTES))}</td>"
            f"<td>{player['gear_score']:.3f}</td><td>{v['hp']:.1f}</td>"
            + "".join(f"<td>{esc(cell)}</td>" for cell in cells)
            + "</tr>"
        )
    links = " · ".join(f"<a href='{b['id']}/report.html'>{esc(b['id'])}</a>" for b in state["batches"])
    doc = f"""<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Атрибуты старта: 135 очков</title><style>body{{background:#101722;color:#e4edf8;font:14px/1.5 system-ui;padding:24px}}
a{{color:#9cf}}table{{border-collapse:collapse}}td,th{{padding:9px;border:1px solid #354357;text-align:left}}.scroll{{overflow:auto}}</style>
<h1>Тестовые атрибуты стартовых слепков</h1><p>Состояние: {esc(state["status"])}. Рабочие слепки не изменены.</p>
<p>Три варианта: исходные 117 очков, равномерные 135 и подобранные 135. Разрыв новых распределений ≤8.
Экипировка, навыки, симбиот и loadout каждого старта неизменны. Финты включены у обеих сторон, balanced AI.</p>
<p>Сначала контроль: четыре фиксированные тройки, ранее реально выданные лёгкими профилями гоблинов Т0.
Это выбранные представители типов встречи, а не все варианты профилей. Одинаковые seed и противники у всех билдов.
Затем actual-selector проверяет только новые распределения через настоящий контракт easy; там новый GS может менять составы.</p>
<p>Порядок атрибутов: сила / ловкость / выносливость / интеллект / память / ментальность / восприятие / проекция / предсказание.</p>
<p>В клетках победы/бои и выживаемость. 50 seed — предварительный тест; подбор по формулам, не доказанный глобальный оптимум.</p>
<p>{links}</p><p><a href='allocations.json'>Распределения</a> · <a href='players.json'>Входные слепки</a> · <a href='summary.json'>Полные результаты</a></p>
<div class='scroll'><table><thead><tr><th>Вариант</th><th>Атрибуты</th><th>GS</th><th>HP</th><th>Миньоны</th><th>Ветеран</th><th>Элита</th><th>Босс</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table></div></html>"""
    (output / "index.html").write_text(doc, encoding="utf-8")
    write_json(output / "summary.json", state)


def main(argv=None):
    from loguru import logger

    from .attribute_profiles import ALLOCATIONS

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--battles", type=int, default=50)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--players", nargs="+")
    args = parser.parse_args(argv)
    if args.battles < 1 or args.workers < 1:
        parser.error("battles/workers must be positive")
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error("output must be new or empty")
    logger.remove()
    plans = {key: value for key, value in ALLOCATIONS.items() if not args.players or key in args.players}
    if not plans or (args.players and set(args.players) != set(plans)):
        parser.error("Unknown player")
    before = source_fingerprint()
    players = build_variants(plans)
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "players.json", players)
    write_json(output / "allocations.json", plans)
    state = {
        "status": "running",
        "source_before": before,
        "started_at": datetime.now(UTC).isoformat(),
        "battles": args.battles,
        "fixed_rosters": ROSTERS,
        "batches": [],
    }
    write_overview(output, state, players)
    for kind, roster in ROSTERS.items():
        report = run_probe(
            ProbeConfig(
                mode="fixed",
                players=(),
                player_input=output / "players.json",
                player_keys=tuple(players),
                members=tuple((f"goblin_tribe.base.{key}", n) for key, n in roster),
                battles=args.battles,
                workers=args.workers,
                output=output / f"fixed-{kind}",
            )
        )
        state["batches"].append({"id": f"fixed-{kind}", "report": report})
        write_overview(output, state, players)
    report = run_probe(
        ProbeConfig(
            players=(),
            player_input=output / "players.json",
            player_keys=tuple(k for k in players if k.endswith(".tailored135")),
            encounters=tuple(ROSTERS),
            battles=args.battles,
            workers=args.workers,
            output=output / "actual-selector",
        )
    )
    state["batches"].append({"id": "actual-selector", "report": report})
    state["source_after"] = source_fingerprint()
    state["status"] = "completed" if before == state["source_after"] else "source_changed"
    state["completed_at"] = datetime.now(UTC).isoformat()
    write_overview(output, state, players)
    print(f"Report: {output / 'index.html'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
