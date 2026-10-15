"""Permanent boundary for the retired persisted-monster pipeline."""


class LegacyMonsterRuntimeRetired(RuntimeError):  # noqa: N818 - published retirement exception
    code = "legacy_monster_runtime_retired"

    def __init__(self) -> None:
        super().__init__(
            "Legacy monster encounters and persisted template generation are retired; catalog runtime is under development."
        )


def require_legacy_monster_runtime() -> None:
    raise LegacyMonsterRuntimeRetired()


LEGACY_MONSTER_RUNTIME_RETIRED = True
