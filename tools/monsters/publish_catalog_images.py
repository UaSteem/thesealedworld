"""Publish linked local catalogue images without generation, database or S3."""
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.backend.features.monsters.catalog.registry import get_catalog  # noqa: E402


def main() -> None:
    source_root = (ROOT / "assets/monster_defaults").resolve()
    destination = ROOT / "src/frontend/static/images/monsters/catalog"
    destination.mkdir(parents=True, exist_ok=True)
    refs = {m.image.asset_id: m.image for m in get_catalog().members.values() if m.image}
    for asset_id, ref in refs.items():
        source = (ROOT / ref.source_path).resolve()
        if not source.is_relative_to(source_root) or not re.fullmatch(r"[a-zA-Z0-9_.-]+", asset_id):
            raise ValueError("Catalogue image must use a safe asset ID and source root")
        if source.suffix.lower() not in {".png", ".svg", ".webp", ".jpg", ".jpeg"}:
            raise ValueError("Unsupported catalogue image format")
        shutil.copyfile(source, destination / f"{asset_id}{source.suffix}")
    print(f"Published {len(refs)} catalogue images locally")


if __name__ == "__main__":
    main()
