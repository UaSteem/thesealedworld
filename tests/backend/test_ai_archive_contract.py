"""Historical retirement copies remain byte-identical and outside live src."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_ai_retirement_archive_preserves_original_files_and_paths():
    manifest = json.loads((ROOT / "archive/ai_retirement_manifest.json").read_text(encoding="utf-8"))
    records = manifest["files"]
    assert records
    destinations = set()
    for record in records:
        source = Path(record["source"])
        target = Path(record["archive"])
        expected = Path("archive") / Path(*source.parts[1:]) if source.parts[0] == "src" else Path("archive") / source
        assert target == expected
        assert target not in destinations
        destinations.add(target)
        archived = (ROOT / target).resolve()
        assert archived.is_relative_to(ROOT / "archive")
        assert hashlib.sha256(archived.read_bytes()).hexdigest() == record["sha256"]
        if record["action"] == "moved":
            assert not (ROOT / source).exists()
        else:
            assert record["action"] == "split"
            assert (ROOT / source).is_file()
