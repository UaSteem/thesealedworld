"""Review or write a migrated copy of an exported inventory snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from src.backend.features.inventory.services.equipment_migration import migrate_inventory_snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--write-output", type=Path, help="Explicitly write a NEW migrated copy; never overwrite input")
    args = parser.parse_args()
    raw = args.snapshot.read_bytes()
    migrated, report = migrate_inventory_snapshot(json.loads(raw))
    report["input_sha256"] = hashlib.sha256(raw).hexdigest()
    report["mode"] = "write-new-copy" if args.write_output else "dry-run"
    if args.write_output:
        # Exclusive creation prevents input or previously reviewed outputs being overwritten.
        with args.write_output.open("x", encoding="utf-8") as target:
            json.dump(migrated, target, ensure_ascii=False, indent=2)
            target.write("\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
