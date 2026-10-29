"""Shared local inventory fixture and an exact, fixture-owned art allowlist."""

import json
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[1]
ART_ROOT = LAB_ROOT.parent / "assets/item_art/renders"
PAYLOAD = json.loads((LAB_ROOT / "data/inventory.json").read_text(encoding="utf-8"))
ART = {}
for item in PAYLOAD["items"]:
    for kind in ("image", "thumbnail"):
        relative = item[f"{kind}_url"].removeprefix("/static/generated-assets/")
        target = (ART_ROOT / relative).resolve()
        if not target.is_relative_to(ART_ROOT.resolve()) or not target.is_file():
            raise ValueError(f"Missing fixture art: {relative}")
        ART[f"/inventory-art/{item['visual_variant_id']}/{kind}"] = target
    item["texture_url"] = f"/inventory-art/{item['visual_variant_id']}/image"
