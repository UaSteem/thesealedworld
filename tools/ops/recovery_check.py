"""Check local backup/restore evidence without contacting or modifying any store."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path

REQUIRED_STORES = frozenset({"site_postgres", "game_postgres", "mongo", "redis"})


def _positive(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError("invalid policy duration")
    return float(value)


def _timestamp(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("missing timestamp")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("timestamp requires timezone")
    return parsed.astimezone(UTC)


def check_evidence(document: dict, root: Path, *, now: datetime) -> list[str]:
    """Return bounded failure codes; timestamps attest a drill, not its semantics."""
    failures: list[str] = []
    if not isinstance(document, dict) or type(document.get("version")) is not int or document["version"] != 1:
        raise ValueError("unsupported manifest")
    policy = document["policy"]
    max_backup_age = _positive(policy["max_backup_age_seconds"])
    max_restore_age = _positive(policy["max_restore_age_seconds"])
    max_restore_duration = _positive(policy["max_restore_duration_seconds"])
    stores = document["stores"]
    if not isinstance(stores, dict) or not stores.keys() >= REQUIRED_STORES:
        raise ValueError("missing durable store")
    root = root.resolve(strict=True)
    # Only fixed store names are emitted, never arbitrary input or credentials.
    for name in sorted(REQUIRED_STORES):
        try:
            entry = stores[name]
            relative = Path(entry["file"])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("unsafe artifact path")
            artifact = (root / relative).resolve(strict=True)
            if not artifact.is_relative_to(root) or not artifact.is_file() or artifact.stat().st_size == 0:
                raise ValueError("invalid artifact")
            with artifact.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            if digest != entry["sha256"] or digest != entry["restore"]["backup_sha256"]:
                raise ValueError("artifact mismatch")
            backup_at = _timestamp(entry["completed_at"])
            restored_at = _timestamp(entry["restore"]["completed_at"])
            if not backup_at <= restored_at <= now:
                raise ValueError("invalid chronology")
            if (now - backup_at).total_seconds() > max_backup_age:
                failures.append(f"{name}:backup_stale")
            if (now - restored_at).total_seconds() > max_restore_age:
                failures.append(f"{name}:restore_stale")
            if _positive(entry["restore"]["duration_seconds"]) > max_restore_duration:
                failures.append(f"{name}:restore_slow")
        except (KeyError, TypeError, ValueError, OSError):
            failures.append(f"{name}:invalid_evidence")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--artifact-root", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        document = json.loads(args.manifest.read_text(encoding="utf-8"))
        failures = check_evidence(document, args.artifact_root, now=datetime.now(UTC))
    except (KeyError, TypeError, ValueError, OSError):
        print("recovery_evidence:invalid_manifest", file=sys.stderr)
        return 2
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print("recovery_evidence:local_checks_passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
