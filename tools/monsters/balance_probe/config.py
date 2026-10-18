"""Explicit command-line configuration; no content or database access."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class ProbeConfig:
    mode: str = "encounter"
    family: str = "goblin_tribe"
    tier: int = 0
    players: tuple[str, ...] = ("starter_dual_blades_01",)
    player_input: Path | None = None
    player_keys: tuple[str, ...] = ()
    player_tier: int | None = None
    mastery: float | None = None
    encounters: tuple[str, ...] = ("ordinary",)
    difficulties: tuple[str, ...] = ("easy",)
    members: tuple[tuple[str, int], ...] = ()
    battles: int = 50
    seed: int = 0
    max_rounds: int = 100
    feints: str = "both"
    workers: int = 1
    output: Path | None = None
    replay: Path | None = None
    allow_source_drift: bool = False

    def to_dict(self) -> dict:
        data = asdict(self)
        for key in ("player_input", "output", "replay"):
            data[key] = str(data[key]) if data[key] is not None else None
        return data

    @classmethod
    def from_dict(cls, data: dict) -> ProbeConfig:
        data = dict(data)
        for key in ("players", "player_keys", "encounters", "difficulties"):
            if key in data:
                data[key] = tuple(data[key])
        if "members" in data:
            data["members"] = tuple((str(k), int(v)) for k, v in data["members"])
        for key in ("player_input", "output", "replay"):
            if data.get(key) is not None:
                data[key] = Path(data[key])
        return cls(**data)


def _positive(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def _member(value: str) -> tuple[str, int]:
    try:
        identity, count = value.rsplit("=", 1)
        count = _positive(count)
        if not identity or "." not in identity:
            raise ValueError
        return identity, count
    except (ValueError, argparse.ArgumentTypeError) as exc:
        raise argparse.ArgumentTypeError("use full.member.id=COUNT, with a positive count") from exc


def parse_config(argv: list[str] | None = None) -> ProbeConfig:
    parser = argparse.ArgumentParser(description="Read-only reproducible Monsters/Combat balance probe.")
    parser.add_argument("--mode", choices=("encounter", "fixed"), default="encounter")
    parser.add_argument("--family", default="goblin_tribe")
    parser.add_argument("--tier", type=int, choices=range(8), default=0)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--player", nargs="+", action="extend", dest="players")
    source.add_argument("--player-input", type=Path)
    parser.add_argument("--player-key", action="append", default=[], dest="player_keys")
    parser.add_argument("--player-tier", type=int, choices=range(8))
    parser.add_argument("--mastery", type=float)
    parser.add_argument(
        "--encounters", nargs="+", choices=("ordinary", "patrol", "guard", "leader"), default=["ordinary"]
    )
    parser.add_argument(
        "--difficulty", nargs="+", choices=("easy", "normal", "hard"), default=["easy"], dest="difficulties"
    )
    parser.add_argument("--member", action="append", type=_member, default=[], dest="members")
    parser.add_argument("--battles", type=_positive, default=50)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-rounds", type=_positive, default=100)
    parser.add_argument("--feints", choices=("both", "none", "player", "monsters"), default="both")
    parser.add_argument("--workers", type=_positive, default=1)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--replay", type=Path)
    parser.add_argument("--allow-source-drift", action="store_true")
    args = parser.parse_args(argv)
    if args.mastery is not None and not 0 <= args.mastery <= 1:
        parser.error("--mastery must be finite and between 0 and 1")
    if args.player_keys and args.player_input is None:
        parser.error("--player-key requires --player-input")
    if args.mode == "fixed" and not args.members and not args.replay:
        parser.error("--mode fixed requires --member full.member.id=COUNT")
    if args.members and args.mode != "fixed":
        parser.error("--member is only valid in fixed mode")
    if sum(count for _, count in args.members) > 8:
        parser.error("fixed squad must contain between 1 and 8 monsters")
    if len({identity for identity, _ in args.members}) != len(args.members):
        parser.error("duplicate --member identities are not allowed; specify their total count")
    if args.player_input is None and args.player_tier not in (None, 0):
        parser.error("live starter imprints remain T0; --player-tier cannot upgrade them")
    if args.replay:
        import sys

        raw = argv if argv is not None else sys.argv[1:]
        allowed = {"--replay", "--output", "--allow-source-drift"}
        if any(token.startswith("--") and token.split("=", 1)[0] not in allowed for token in raw):
            parser.error("--replay accepts only --output and --allow-source-drift overrides")
        try:
            manifest = json.loads(args.replay.read_text(encoding="utf-8"))
            resolved = ProbeConfig.from_dict(manifest["config"])
        except (OSError, ValueError, KeyError, TypeError) as exc:
            parser.error(f"invalid replay manifest: {exc}")
        from dataclasses import replace

        return replace(
            resolved,
            replay=args.replay,
            output=args.output or _default_output(),
            allow_source_drift=args.allow_source_drift,
        )
    data = vars(args)
    for key in ("players", "player_keys", "encounters", "difficulties", "members"):
        data[key] = tuple(data[key] or ())
    if not data["players"] and data["player_input"] is None:
        data["players"] = ("starter_dual_blades_01",)
    data["output"] = data["output"] or _default_output()
    return ProbeConfig(**data)


def _default_output() -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return Path("var/balance-probe") / f"{stamp}-{uuid4().hex[:8]}"
