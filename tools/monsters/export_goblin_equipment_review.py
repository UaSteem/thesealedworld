"""Export a read-only, offline review of the goblin equipment catalog."""

from __future__ import annotations

import argparse
import csv
import html
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.backend.features.items.services.presentation_service import ItemPresentationService  # noqa: E402
from src.backend.features.monsters.catalog.prepared_equipment import get_prepared_equipment  # noqa: E402
from src.backend.features.monsters.catalog.registry import get_catalog  # noqa: E402
from src.backend.features.monsters.catalog.texts import localized_definition  # noqa: E402
from src.backend.features.monsters.inspection.services.equipment_stats_service import (  # noqa: E402
    MonsterEquipmentStatsService,
)

ROLES = {"minion": "Миньон", "veteran": "Ветеран", "elite": "Элита", "boss": "Босс"}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def export(output: Path) -> dict:
    catalog = get_catalog()
    family = catalog.families["goblin_tribe"]
    members = [member for member in catalog.members.values() if member.clan_id == "goblin_tribe.base"]
    presentation = ItemPresentationService()
    calculator = MonsterEquipmentStatsService()
    sections, summaries, references = [], [], []
    for tier in range(6):
        for member in members:
            prepared = get_prepared_equipment(family_id=family.id, variant_id=member.variant_id, tier=tier)
            preview = calculator.preview(member=member, family=family, prepared=prepared)
            values = preview.technical["equipped"]
            name = localized_definition(member, "ru")["name"]
            summaries.append(
                {
                    "tier": tier,
                    "member_id": member.id,
                    "name": name,
                    "role": member.role,
                    "hp": values.get("hp", 0),
                    "main_hand_damage": values.get("main_hand_damage_base", 0),
                    "off_hand_damage": values.get("off_hand_damage_base", 0),
                    "physical_armor": values.get("armor", 0),
                    "items": len(prepared.items),
                    "affixes": sum(len(item.generation.affixes) for item in prepared.items),
                }
            )
            cards = []
            for item in prepared.items:
                card = presentation.present(item)
                context = item.generation.source_context or {}
                card = card.model_copy(
                    update={
                        "title": context.get("presentation_name_ru") or card.title,
                        "description": context.get("presentation_description_ru") or card.description,
                    }
                )
                reference = context.get("equipment_catalog_id", "")
                references.append(
                    {
                        "tier": tier,
                        "member_id": member.id,
                        "slot": item.slot,
                        "equipment_catalog_id": reference,
                        "item_id": str(item.item_id),
                        "base_id": item.base_id,
                        "name": card.title,
                    }
                )
                bonuses = "".join(f"<li>{esc(row.label)} <b>{esc(row.value)}</b></li>" for row in card.bonuses)
                properties = "".join(f"<li>{esc(row.label)} <b>{esc(row.value)}</b></li>" for row in card.properties)
                effects = "".join(f"<li>{esc(effect)}</li>" for effect in card.effects)
                technical = json.dumps(card.technical, ensure_ascii=False, indent=2)
                cards.append(
                    f'<article class="item"><small>{esc(card.slot_label)} · {esc(card.rarity_label)}</small>'
                    f"<h3>{esc(card.title)}</h3><p>{esc(card.material_label)}</p>"
                    f"<p>{esc(card.power_label)}: <b>{esc(card.power_value)}</b></p>"
                    f"<ul>{bonuses or '<li>Без аффиксов</li>'}</ul>"
                    f"<details><summary>Основа и эффекты</summary><ul>{properties}{effects}</ul></details>"
                    f"<details><summary>Ссылка и технические данные</summary><p>{esc(reference or 'Нет общей ссылки')}</p>"
                    f"<pre>{esc(technical)}</pre></details></article>"
                )
            groups = ""
            for group in preview.groups:
                rows = "".join(
                    f"<tr><td>{esc(row.label)}</td><td>{esc(row.base_value)}</td>"
                    f"<td>{esc(row.equipped_value)}</td><td>{esc(row.delta_value)}</td></tr>"
                    for row in group.rows
                )
                groups += f"<h4>{esc(group.label)}</h4><table><thead><tr><th>Параметр</th><th>Без вещей</th><th>Итог</th><th>От вещей</th></tr></thead><tbody>{rows}</tbody></table>"
            sections.append(
                f'<section data-tier="{tier}"><h2>{esc(name)} <small>Т{tier} · {ROLES[member.role]}</small></h2>'
                f"<p>HP <b>{values.get('hp', 0):.1f}</b> · База удара <b>{values.get('main_hand_damage_base', 0):.2f}</b>"
                f" · Броня <b>{values.get('armor', 0):.2f}</b> · Аффиксов <b>{summaries[-1]['affixes']}</b></p>"
                f'<div class="cards">{"".join(cards)}</div>'
                f"<details><summary>Все итоговые характеристики</summary>{groups}</details></section>"
            )
    counts = Counter(row["equipment_catalog_id"] for row in references if row["equipment_catalog_id"])
    report = {
        "sets": len(summaries),
        "members": len(members),
        "tiers": list(range(6)),
        "item_assignments": len(references),
        "unique_catalog_items": len(counts),
        "missing_catalog_references": sum(not row["equipment_catalog_id"] for row in references),
        "catalog_item_use_counts": dict(sorted(counts.items())),
        "notes": [
            "Read-only export; no generation, battles or database writes.",
            "Current runtime tier scaling is unchanged.",
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "summary.csv", summaries)
    write_csv(output / "references.csv", references)
    (output / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    document = """<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Комплекты гоблинов Т0–Т5</title>
<style>body{font:16px system-ui;background:#101722;color:#e4eaf2;margin:0 auto;padding:28px;max-width:1500px}h1,h2,h3{line-height:1.25}small,p{color:#aebed0}header{position:sticky;top:0;background:#101722ef;padding:12px 0;z-index:1}select{font:inherit;padding:8px;background:#26344a;color:white;border-radius:8px}section{border-top:1px solid #3c4d66;padding:22px 0}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:14px}.item{background:#1c2839;border:1px solid #354862;border-radius:12px;padding:18px}li{margin:8px 0}details{margin:15px 0}summary{cursor:pointer;color:#a6d4ff}pre{overflow:auto;max-height:360px;font-size:12px;white-space:pre-wrap;overflow-wrap:anywhere}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:9px;border-bottom:1px solid #354862}section[hidden]{display:none}</style>
<header><h1>Гоблины · готовые комплекты Т0–Т5</h1><label>Показать тир <select id="tier"><option value="0">Т0</option>"""
    document += "".join(f'<option value="{tier}">Т{tier}</option>' for tier in range(1, 6))
    document += f"""<option value="all">Все тиры</option></select></label><p>{len(summaries)} комплектов · {len(references)} назначений · {len(counts)} общих предметов. Характеристики рассчитаны действующими формулами; бои не запускались.</p></header>"""
    document += "<p>Профили: точность, ударная сила, вторая рука, подвижность, укреплённая защита, щит; украшения — ловкость, сила или баланс двух клинков. Средние броски аффиксов; действующее усиление монстров от 2 до 9 тиков сохранено.</p>"
    document += "".join(sections)
    document += """<script>const select=document.querySelector('#tier');function filter(){document.querySelectorAll('section[data-tier]').forEach(s=>s.hidden=select.value!=='all'&&s.dataset.tier!==select.value)}select.addEventListener('change',filter);filter();</script></html>"""
    (output / "equipment.html").write_text(document, encoding="utf-8")
    assert len(summaries) == 72, f"Expected 72 goblin sets, found {len(summaries)}"
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "var/goblin-equipment-review")
    args = parser.parse_args()
    print(json.dumps(export(args.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
