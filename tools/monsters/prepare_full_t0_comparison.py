"""Offline paired native/full T0 inputs; never connects to persistence or combat."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from tools.monsters.balance_probe.config import ProbeConfig
from tools.monsters.balance_probe.equipment import build_full_players
from tools.monsters.balance_probe.players import _live_player

from src.backend.features.combat.runtime.simulation.starting_imprint_actors import DEFAULT_STARTER_SIMULATION_IMPRINTS


def prepare_pairs() -> tuple[dict, dict]:
    identities = DEFAULT_STARTER_SIMULATION_IMPRINTS
    full_players = build_full_players(identities, (0,))
    players, pairs = {}, []
    for identity in identities:
        starter = _live_player(identity, ProbeConfig())
        full = full_players[f"{identity}.t0"]
        for field in ("attributes", "symbiote"):
            assert starter["input_context"][field] == full["input_context"][field]
        assert starter["skills"] == full["skills"]
        assert starter["loadout"]["known_feints"]
        assert set(starter["loadout"]["known_feints"]) == set(full["loadout"]["known_feints"])
        starter_key, full_key = f"{identity}.start", f"{identity}.full"
        players[starter_key], players[full_key] = starter, full
        pairs.append(
            {
                "imprint_id": identity,
                "starter_key": starter_key,
                "full_key": full_key,
                "starter": _summary(starter),
                "full": _summary(full),
            }
        )
    return {"tier": 0, "resolved_players": players}, {
        "pairs": pairs,
        "pair_count": len(pairs),
        "policy": "Equipment only; identical attributes, skills, symbiote and explicit feint arsenal. T0 has zero affixes.",
    }


def _summary(player: dict) -> dict:
    return {
        "gs": player["gear_score"],
        "hp": player["preview_values"].get("hp_max", player["preview_values"].get("hp")),
        "regen": player["regen"],
        "equipment_count": player["equipment_count"],
        "feint_count": len(player["loadout"]["known_feints"]),
    }


def save(output: Path) -> None:
    inputs, preparation = prepare_pairs()
    output.mkdir(parents=True, exist_ok=True)
    for name, data in (("inputs.json", inputs), ("preparation.json", preparation)):
        (output / name).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    rows = []
    players = inputs["resolved_players"]
    for pair in preparation["pairs"]:
        rows.append(
            f"<h2>{html.escape(pair['imprint_id'])}</h2><p>GS {pair['starter']['gs']:.3f} → {pair['full']['gs']:.3f}</p>"
        )
        for label, key in (("Старт", pair["starter_key"]), ("Полный Т0", pair["full_key"])):
            player = players[key]
            rows.append(
                f"<h3>{label}</h3><pre>{html.escape(json.dumps(player['input_context']['attributes'], ensure_ascii=False))}</pre><ul>"
            )
            for slot, item_id in player["equipment"]["layout"]["equipment"].items():
                item = player["equipment"]["by_id"][item_id]
                rows.append(f"<li>{html.escape(slot)}: {html.escape(item['base_id'])}</li>")
            rows.append("</ul>")
    document = (
        '<!doctype html><meta charset="utf-8"><title>Старт и полный Т0 — 14 пар</title><style>body{font:16px system-ui;max-width:1100px;margin:32px auto;background:#151923;color:#e5e9f1}h2{border-top:1px solid #586070;padding-top:20px}</style><h1>14 стартов и полные комплекты Т0</h1><p>Атрибуты, навыки, симбиот и арсеналы финтов сохранены. База и бой не изменены.</p>'
        + "".join(rows)
    )
    (output / "equipment.html").write_text(document, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("var/starter-full-t0-current-14"))
    save(parser.parse_args().output)
