"""Monster attribute tier policy, formerly declared in encounter spawn config."""

from collections.abc import Mapping

# Provisional alpha curve: T1 starts at 1.2; every following tier adds 0.5.
# The shared curve affects all families/ranks; late tiers remain uncalibrated.
TIER_SCALING_CONFIG: dict[int, dict[str, float]] = {
    0: {"stat_mult": 1.0},
    1: {"stat_mult": 1.2},
    2: {"stat_mult": 1.7},
    3: {"stat_mult": 2.2},
    4: {"stat_mult": 2.7},
    5: {"stat_mult": 3.2},
    6: {"stat_mult": 3.7},
    7: {"stat_mult": 4.2},
}


def scale_monster_attributes(attributes: Mapping[str, int], tier: int) -> dict[str, int]:
    if type(tier) is not int or tier not in TIER_SCALING_CONFIG:
        raise ValueError("Monster attribute tier must be between 0 and 7")
    multiplier = TIER_SCALING_CONFIG[tier]["stat_mult"]
    return {key: max(0, int(round(value * multiplier))) for key, value in attributes.items()}
