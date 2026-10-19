"""Inspect canonical physical GS components and resource regeneration."""

from __future__ import annotations

import argparse
import html
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from loguru import logger  # noqa: E402
from tools.monsters.simulate_encounter_matrix import build_player  # noqa: E402

from src.backend.core.calculators.stats_waterfall_calculator import StatsWaterfallCalculator  # noqa: E402
from src.backend.features.character.runtime.experimental_gear_score import ExperimentalGearScoreCalculator  # noqa: E402
from src.backend.features.character.runtime.gear_score import CharacterGearScoreCalculator  # noqa: E402
from src.backend.features.combat.runtime.simulation.starting_imprint_actors import (  # noqa: E402
    DEFAULT_STARTER_SIMULATION_IMPRINTS,
    StartingImprintSimulationActorBuilder,
)
from src.backend.features.monsters.catalog import get_catalog  # noqa: E402
from src.backend.features.monsters.catalog.prepared_equipment import get_member_prepared_equipment  # noqa: E402
from src.backend.features.monsters.instances.services.instance_builder import MonsterInstanceBuilder  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--player-input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--comparison-player-input", type=Path)
    args = parser.parse_args()
    logger.remove()
    random.seed(0)
    calculator = ExperimentalGearScoreCalculator()
    rows = []

    def append(label, group, raw, skills, loadout):
        calculated, _ = StatsWaterfallCalculator.calculate_waterfall(raw)
        rows.append(
            {
                "label": label,
                "group": group,
                "live_gs": CharacterGearScoreCalculator.calculate_from_raw(raw, skills=skills, loadout=loadout),
                "experimental": calculator.calculate_from_raw(raw, skills=skills, loadout=loadout),
                "regeneration": {
                    mode: {resource: calculated[f"{prefix}{resource}_regen"] for resource in ("hp", "en", "stamina")}
                    for mode, prefix in (("combat", "combat_"), ("outside", ""))
                },
                "inputs": {"raw": raw, "skills": skills, "loadout": loadout},
            }
        )

    player = build_player(0, args.player_input)
    append("Полный комплект Т0: два клинка", "Тестовый игрок", player["raw"], player["skills"], player["loadout"])
    if args.comparison_player_input:
        saved = json.loads(args.comparison_player_input.read_text(encoding="utf-8"))
        tier = saved.get("player_tier", saved["tier"])
        comparison = build_player(tier, args.comparison_player_input)
        append(
            f"Полный комплект Т{tier}: два клинка (навыки 20%)",
            "Контроль роста",
            comparison["raw"],
            comparison["skills"],
            comparison["loadout"],
        )
    builder = StartingImprintSimulationActorBuilder()
    for key in DEFAULT_STARTER_SIMULATION_IMPRINTS:
        actor = builder.build_actor(key, actor_id=key, team="blue").actor
        append(
            key,
            "Стартовый слепок",
            actor.raw.model_dump(mode="json"),
            actor.skills,
            actor.loadout.model_dump(mode="json"),
        )
    catalog = get_catalog()
    for member in catalog.members.values():
        if member.family_id != "goblin_tribe":
            continue
        prepared = get_member_prepared_equipment(member=member, tier=0)
        build = MonsterInstanceBuilder().build(
            member=member, family=catalog.families[member.family_id], prepared=prepared
        )
        append(member.id, "Гоблин Т0", build.equipped.raw, build.skills, build.equipped.loadout)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    keys = ("base_ehp", "extra_ehp", "base_offense", "extra_offense", "support")
    body = ""
    for row in rows:
        exp = row["experimental"]
        cells = [row["label"], row["live_gs"], exp["total"]]
        cells.extend(f"{exp['components'][k]['value']:.2f} → {exp['components'][k]['score']:.2f}" for k in keys)
        cells.extend(
            " · ".join(
                f"{name}: {row['regeneration'][mode][resource]:.2f}"
                for name, resource in (("HP", "hp"), ("Э", "en"), ("С", "stamina"))
            )
            for mode in ("combat", "outside")
        )
        body += "<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in cells) + "</tr>"
    first = rows[0]["experimental"]
    notes = html.escape(json.dumps({k: first[k] for k in ("assumptions", "limitations")}, ensure_ascii=False, indent=2))
    headers = (
        "Сборка",
        "Рабочий GS",
        "Проверка общей модели GS",
        "Базовый EHP → GS",
        "Доп. EHP → GS",
        "Базовая атака → GS",
        "Доп. атака → GS",
        "Поддержка → GS",
        "Реген в бою: HP / энергия / стамина",
        "Реген вне боя: HP / энергия / стамина",
    )
    page = '<!doctype html><html lang="ru"><meta charset="utf-8"><title>Экспериментальный GS</title>'
    page += "<style>body{font:15px system-ui;margin:28px;background:#f4f6fa;color:#172033}table{border-collapse:collapse;background:white}td,th{padding:10px;border:1px solid #ddd}pre{white-space:pre-wrap}.scroll{overflow:auto}</style>"
    page += "<h1>Физический GS и регенерация</h1><p>Рабочий калькулятор и аналитическая проекция используют одну модель physical-v5. Физическая проекция относительно фиксированных условий; это не прогноз победы. Поддержка учитывает только боевое восстановление. Реген от бижутерии работает в обоих режимах; энергия игрока от атрибутов — только вне боя. Боевое восстановление HP монстров равно нулю.</p>"
    page += (
        '<div class="scroll"><table><tr>'
        + "".join(f"<th>{h}</th>" for h in headers)
        + "</tr>"
        + body
        + "</table></div>"
    )
    page += "<h2>Условия и ограничения</h2><pre>" + notes + "</pre></html>"
    (args.output / "report.html").write_text(page, encoding="utf-8")
    print(
        json.dumps(
            {"rows": len(rows), "player_live": rows[0]["live_gs"], "player_model": first}, ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()
