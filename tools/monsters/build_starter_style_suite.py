"""Offline starter style proposals. No battles, persistence or production edits."""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.backend.features.character.resources.starting_imprints import ATTRIBUTE_KEYS  # noqa: E402
from src.backend.features.character.runtime.combat_actor_input import CharacterCombatActorInputBuilder  # noqa: E402
from src.backend.features.character.runtime.experimental_gear_score import ExperimentalGearScoreCalculator  # noqa: E402
from src.backend.features.items.dto.instance import ItemGenerationRequestDTO, ItemOriginRefDTO  # noqa: E402
from src.backend.features.items.runtime.item_factory import ItemFactory  # noqa: E402

ATTRS = {
    "shield_swords": (17, 14, 20, 12, 16, 13, 16, 13, 14),
    "shield_macing": (19, 13, 20, 12, 15, 14, 16, 12, 14),
    "two_handed_swords": (18, 16, 19, 12, 15, 13, 16, 12, 14),
    "two_handed_macing": (20, 13, 19, 12, 14, 13, 18, 12, 14),
    "two_handed_polearms": (19, 15, 18, 12, 14, 13, 17, 12, 15),
    "dual_fencing": (12, 20, 18, 12, 16, 13, 17, 13, 14),
    "dual_swords": (16, 19, 17, 12, 16, 13, 16, 12, 14),
    "dual_macing": (19, 16, 18, 12, 15, 13, 16, 12, 14),
    "shortbow": (12, 20, 17, 12, 16, 13, 18, 13, 14),
    "longbow": (13, 19, 17, 12, 15, 14, 18, 13, 14),
}
ARMOR = {"light": "light_chest_armor", "medium": "medium_chest_armor", "heavy": "heavy_chest_armor"}
TACTICS = {
    "shield": "skill_shield_mastery",
    "two_handed": "skill_two_handed",
    "dual": "skill_dual_wield",
    "ranged": "skill_ranged_combat",
}


def definitions():
    rows = []
    for tactic, weapons, armors in (
        ("shield", (("swords", "sword"), ("macing", "mace")), ("medium", "heavy")),
        (
            "two_handed",
            (("swords", "flamberge"), ("macing", "warhammer"), ("polearms", "halberd")),
            ("medium", "heavy"),
        ),
        ("dual", (("swords", "sword"), ("fencing", "stiletto"), ("macing", "mace")), ("light", "medium")),
        ("ranged", (("archery", "shortbow"), ("archery", "longbow")), ("light",)),
    ):
        for weapon, base in weapons:
            for armor in armors:
                archetype = base if tactic == "ranged" else f"{tactic}_{weapon}"
                rows.append(
                    dict(
                        id=f"test18.{tactic}.{base}.{armor}",
                        tactic=tactic,
                        weapon=weapon,
                        base=base,
                        armor=armor,
                        attributes=dict(zip(ATTRIBUTE_KEYS, ATTRS[archetype], strict=True)),
                    )
                )
    return rows


def validate_attributes(attributes):
    values = [attributes[k] for k in ATTRIBUTE_KEYS]
    if sum(values) != 135 or max(values) - min(values) > 8:
        raise ValueError("Attribute budget/spread violated")
    if any(len(set(values[i : i + 3])) != 3 for i in (0, 3, 6)):
        raise ValueError("Repeated attributes within a triple")


def build_suite():
    factory = ItemFactory()
    players, rows = {}, []
    for definition in definitions():
        d = dict(definition)
        validate_attributes(d["attributes"])
        skill = {f"skill_{d['weapon']}": 0.10, TACTICS[d["tactic"]]: 0.075, f"skill_{d['armor']}_armor": 0.05}
        d["skills"] = skill
        plan = {
            "feetwear": "boots",
            "belt_accessory": "belt",
            "chest_armor": ARMOR[d["armor"]],
        }
        plan["two_hand" if d["tactic"] in ("two_handed", "ranged") else "main_hand"] = d["base"]
        if d["tactic"] == "shield":
            plan["off_hand"] = "shield"
        elif d["tactic"] == "dual":
            plan["off_hand"] = "main_gauche" if d["weapon"] == "fencing" else d["base"]
        elif d["tactic"] == "ranged":
            plan["off_hand"] = "quiver_frost" if d["base"] == "shortbow" else "quiver_fire"
        d["plan"] = plan
        invalid = [
            f"{base_id}/{slot}"
            for slot, base_id in plan.items()
            if slot
            not in {factory.catalog.get_base_item(base_id).slot, *factory.catalog.get_base_item(base_id).extra_slots}
        ]
        if invalid:
            d.update(status="blocked", reason="Catalog does not permit slots: " + ", ".join(invalid))
            rows.append(d)
            continue
        items = {"layout": {"equipment": {}, "belt": {}}, "by_id": {}}
        gear = []
        for slot, base_id in plan.items():
            base = factory.catalog.get_base_item(base_id)
            material = factory._resolve_material(base.allowed_materials, None, 0)
            item = factory.generate_runtime_item(
                ItemGenerationRequestDTO(
                    generation_mode="runtime",
                    base_id=base_id,
                    target_slot=slot,
                    material_id=material.id,
                    rarity_tier=0,
                    affix_count=0,
                    request_ai_text=False,
                    origin_ref=ItemOriginRefDTO(seed=f"starter-style18:{base_id}:{slot}"),
                )
            )
            iid = f"{d['id']}:{slot}"
            data = item.model_dump(mode="json")
            data.update(
                instance_id=iid,
                item_id=iid,
                related_skill=item.metadata.get("related_skill"),
                armor_class=base.armor_class,
                tags=list(item.narrative_tags),
            )
            data["mechanics"] = {
                **item.mechanics,
                "power": item.power,
                "bonuses": dict(item.bonuses),
                "damage_spread": item.damage_spread,
                "triggers": list(item.triggers),
                "related_skill": item.metadata.get("related_skill"),
                "armor_class": base.armor_class,
            }
            items["layout"]["equipment"][slot] = iid
            items["by_id"][iid] = data
            gear.append(dict(slot=slot, base_id=base_id, name=item.name, material_id=material.id, tier=material.tier))
        context = dict(attributes=d["attributes"], items=items, symbiote={"name": "TEST", "tier": 0})
        active = dict(context, char_id=d["id"], bio={"name": d["id"]}, skills=skill)
        actor_input = CharacterCombatActorInputBuilder().build_input(active)
        assert actor_input["skills"] == skill
        loadout = actor_input["loadout"]
        assert loadout["layout"]["tactical_style"] == TACTICS[d["tactic"]]
        assert loadout["layout"]["body"] == f"skill_{d['armor']}_armor"
        assert loadout["layout"]["main_hand"] == f"skill_{d['weapon']}"
        if d["tactic"] == "dual":
            assert loadout["layout"]["off_hand"] == f"skill_{d['weapon']}"
        known = list(loadout["known_feints"])
        actor_input["meta"]["feints"] = {"arsenal": known, "hand": {}}
        score = ExperimentalGearScoreCalculator().calculate_from_raw(
            actor_input["raw"], skills=actor_input["skills"], loadout=loadout
        )
        payload = dict(
            actor_input,
            name=d["id"],
            known_feints=known,
            equipment=items,
            input_context=context,
            gear_score=score["total"],
            gear_score_breakdown=score,
            source={"mode": "experimental_starter_style_suite", "tier": 0},
        )
        players[d["id"]] = payload
        d.update(
            status="built",
            gs=score["total"],
            components=score["components"],
            gear=gear,
            known_feints=len(known),
        )
        rows.append(d)
    return dict(rows=rows, resolved_players=players, excluded=[r for r in rows if r["status"] == "blocked"], battles=0)


def write_report(suite, directory):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "players.json").write_text(
        json.dumps(suite["resolved_players"], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    report = {k: v for k, v in suite.items() if k != "resolved_players"}
    (directory / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    cells = []
    for row in suite["rows"]:
        if row["status"] != "built":
            continue
        attrs = list(row["attributes"].values())
        groups = [" / ".join(map(str, attrs[i : i + 3])) for i in (0, 3, 6)]
        components = row.get("components", {})
        scores = [
            f"{components[k]['score']:.3f}" if k in components else "—"
            for k in ("base_ehp", "extra_ehp", "base_offense", "extra_offense", "support")
        ]
        detail = html.escape(
            json.dumps(
                {
                    "skills": row["skills"],
                    "equipment": row.get("gear", row["plan"]),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        title = (
            {"shield": "Щитовик", "two_handed": "Двуручное", "dual": "Два оружия", "ranged": "Лук"}[row["tactic"]]
            + " · "
            + {
                "sword": "меч",
                "mace": "булава",
                "flamberge": "фламберг",
                "warhammer": "молот",
                "halberd": "алебарда",
                "stiletto": "стилет + дага",
                "shortbow": "короткий",
                "longbow": "длинный",
            }[row["base"]]
            + " · "
            + {"light": "лёгкая", "medium": "средняя", "heavy": "тяжёлая"}[row["armor"]]
        )
        cells.append(
            "<tr>"
            + "".join(
                f"<td>{html.escape(str(v))}</td>"
                for v in [
                    title + " (" + row["id"] + ")",
                    *groups,
                    f"{row['gs']:.3f}" if "gs" in row else row["reason"],
                    *scores,
                ]
            )
            + f"<td><details><summary>Предметы, навыки</summary><pre>{detail}</pre></details></td></tr>"
        )
    limitations = next(iter(suite["resolved_players"].values()))["gear_score_breakdown"]["limitations"]
    body = (
        '<!doctype html><meta charset="utf-8"><title>14 тестовых стартовых слепков</title><style>body{font:15px system-ui;background:#121820;color:#e5ebf2;padding:24px}table{border-collapse:collapse}td,th{padding:9px;border:1px solid #394555;vertical-align:top}pre{white-space:pre-wrap;max-width:480px}summary{cursor:pointer}</style><h1>14 тестовых стартовых слепков · T0</h1><p>Только предложения: 135 очков, разрыв ≤8, внутри каждой тройки значения различаются. Навыки: оружие 10%, тактика 7,5%, броня 5%. Никаких боёв или записи в базу.</p><p>Одинаковые вспомогательные слоты: рубаха, штаны, сапоги, пояс. Один нагрудник, без бижутерии и аффиксов. У луков разные колчаны как у исходных стартовых прототипов. Внешние слепки не нормализованы через DTO: арсенал финтов сохранён явно.</p><p>GS — экспериментальная оценка, не доказательство равной силы. Четыре сочетания с запрещённой второй рукой исключены: два меча и две булавы в лёгкой/средней броне. Запрет каталога сохранён.</p><table><tr><th>Слепок</th><th>СИЛ / ЛОВ / ВЫН</th><th>ИНТ / ПАМ / МЕН</th><th>ВОС / ПРО / ПРЕД</th><th>GS</th><th>EHP</th><th>Шансовая защита</th><th>Атака</th><th>Шансовая атака</th><th>Поддержка</th><th>Состав</th></tr>'
        + "".join(cells)
        + "</table><h2>Исключённые сочетания</h2><ul>"
        + "".join("<li>" + html.escape(r["id"] + ": " + r["reason"]) + "</li>" for r in suite["excluded"])
        + "</ul><h2>Ограничения оценки</h2><ul>"
        + "".join("<li>" + html.escape(v) + "</li>" for v in limitations)
        + "</ul>"
    )
    (directory / "report.html").write_text(body, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "var/starter-style-suite-18")
    args = parser.parse_args()
    suite = build_suite()
    write_report(suite, args.output)
    print(
        json.dumps(
            {
                "built": len(suite["resolved_players"]),
                "defined": len(suite["rows"]),
                "report": str(args.output / "report.html"),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
