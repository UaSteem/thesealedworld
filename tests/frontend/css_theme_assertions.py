"""Resolve static geometry/Classic art when testing pre-migration CSS contracts.

Palette and typography references deliberately remain references: these checks
must not mistake an inactive Classic palette for the default Adventure UI.
"""

import re
from pathlib import Path

CSS = Path(__file__).resolve().parents[2] / "src/frontend/static/css/game"


def resolve_geometry_and_classic_art(source: str) -> str:
    definitions = dict(
        re.findall(
            r"(--(?:sp|space|size|texture)-[\w-]+)\s*:\s*([^;{}]+)",
            (CSS / "core/scales.css").read_text(encoding="utf-8")
            + (CSS / "themes/classic.css").read_text(encoding="utf-8"),
        )
    )

    def replace(match):
        name = match[1]
        assert name in definitions, f"Undefined geometry/art token {name}"
        return definitions[name].strip()

    return re.sub(r"var\((--(?:sp|space|size|texture)-[\w-]+)\)", replace, source)
