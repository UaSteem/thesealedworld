"""Monster attribute tier policy, formerly declared in encounter spawn config."""

from collections.abc import Mapping

TIER_SCALING_CONFIG: dict[int, dict[str, float]] = {
    0: {"stat_mult": 1.0},
    1: {"stat_mult": 1.1},
    2: {"stat_mult": 1.1},
    3: {"stat_mult": 1.3},
    4: {"stat_mult": 1.4},
    5: {"stat_mult": 1.6},
    6: {"stat_mult": 6.5},
    7: {"stat_mult": 10.0},
}


def scale_monster_attributes(attributes: Mapping[str, int], tier: int) -> dict[str, int]:
    if type(tier) is not int or tier not in TIER_SCALING_CONFIG:
        raise ValueError("Monster attribute tier must be between 0 and 7")
    multiplier = TIER_SCALING_CONFIG[tier]["stat_mult"]
    return {key: max(0, int(round(value * multiplier))) for key, value in attributes.items()}
