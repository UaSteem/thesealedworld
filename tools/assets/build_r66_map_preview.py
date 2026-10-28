"""Export geometry-only material-study data from the existing reviewed Rift fixture."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from rift_lab.border_ring import build_border  # noqa: E402


def terrain_data(source: dict) -> dict:
    """Keep only geometry; gameplay actors, POIs and progression never reach the preview."""
    floor = sorted({(c["q"], c["r"]) for c in source["cells"]})
    border = build_border(set(floor))

    def rank(cell: dict) -> int:
        value = 2166136261
        for char in f"artist-v5-mountain:{source['seed']}:{cell['q']}:{cell['r']}":
            value = ((value ^ ord(char)) * 16777619) & 0xFFFFFFFF
        return value

    eligible = sorted((c for c in border if c["void_mask"] == 0), key=rank)
    mountains = eligible[: min(6, max(3, (len(eligible) + 3) // 4))]
    return {
        "schema_version": 1,
        "source": "tests/rift_lab/fixtures/population-r60-live-layout.json",
        "description": "Existing Rift footprint; cartographic symbol study only. No gameplay population.",
        "seed": source["seed"],
        "floor": [{"q": q, "r": r} for q, r in floor],
        "forest": [{"q": c["q"], "r": c["r"]} for c in border],
        "mountain_symbols": [{"q": c["q"], "r": c["r"]} for c in mountains],
        "mountain_note": "Illustrative mountain glyphs at the artist's interior-border candidate positions; no terrain is added.",
        "river_note": "No river in this Rift. River symbol appears only in the separate legend.",
    }


def main() -> None:
    source = ROOT / "tests/rift_lab/fixtures/population-r60-live-layout.json"
    target = ROOT / "rift_lab/static/concepts/r66-map-paper/terrain.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    data = terrain_data(json.loads(source.read_text("utf-8")))
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(f"{len(data['floor'])} floor + {len(data['forest'])} border cells; geometry-only preview exported")


if __name__ == "__main__":
    main()
