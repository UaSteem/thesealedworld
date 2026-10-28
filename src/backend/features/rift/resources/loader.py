"""Disk resource access for the preserved Hex generation prototype."""

import json
from pathlib import Path
from typing import Any

_RESOURCE_DIR = Path(__file__).resolve().parent / "json"


class RiftResourceLoader:
    def __init__(self, resource_dir: Path = _RESOURCE_DIR) -> None:
        self.resource_dir = resource_dir

    def load_tile_set(self, tile_set_key: str) -> dict[str, Any]:
        path = self.resource_dir / "tile_sets" / tile_set_key / "tileset_data.json"
        with path.open(encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, dict):
            raise ValueError("Rift tile set must be a JSON object")
        return data
