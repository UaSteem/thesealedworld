"""python -m tools.monsters.balance_probe --help"""

from .config import parse_config


def main(argv=None) -> int:
    config = parse_config(argv)
    from loguru import logger

    logger.remove()
    from .runner import run_probe

    try:
        run_probe(config)
    except (ValueError, OSError, KeyError) as exc:
        import sys

        print(f"balance_probe: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
