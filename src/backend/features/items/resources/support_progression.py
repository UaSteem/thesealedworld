"""Selected support implicits: preserved R46 T0 and full attribute-20 T7.

This explicit catalog is an exception to normal material-multiplier scaling.
Endpoints were audited against StatsWaterfallCalculator's player profile with
support skills zero; glove crit instead has an explicit independent 20% target. Regeneration references exclude generic base regeneration;
energy uses outside regeneration, HP includes endurance's natural HP component.
"""

from __future__ import annotations

from math import isfinite

# (base_id, implicit_key): (actual T0 anchor, T7 endpoint, reference attribute)
SUPPORT_PROGRESSION = {
    ("belt", "hp"): (8.0, 109.0909, "endurance"),
    ("boots", "stamina"): (8.0, 127.2727, "projection"),
    ("boots", "stamina_regen"): (1.2, 10.9091, "projection"),
    ("gloves", "anti_dodge_chance"): (0.032, 1.0909, "perception"),
    ("gloves", "physical_crit_chance"): (0.008, 0.20, None),
    ("cloak", "hp_regen"): (0.4, 4.1819, "endurance"),
    ("ring", "mental_resistance"): (0.024, 0.7273, "mental"),
    ("amulet", "en_regen"): (0.8, 9.0909, "mental"),
    ("earring", "initiative"): (0.56, 18.1818, "agility"),
}


def support_bonus_at_tier(base_id: str, key: str, tier: int | float) -> float | None:
    """Return one geometric bonus, or None for ordinary material-scaled keys."""
    curve = SUPPORT_PROGRESSION.get((base_id, key))
    if curve is None:
        return None
    numeric_tier = float(tier)
    if not isfinite(numeric_tier) or not numeric_tier.is_integer():
        raise ValueError("Support material tier must be a finite integer")
    bounded_tier = min(7, max(0, int(numeric_tier)))
    start, end, _attribute = curve
    precision = (
        0 if key in {"hp", "stamina"} else 1 if key in {"hp_regen", "stamina_regen", "en_regen", "initiative"} else 3
    )
    return round(start * (end / start) ** (bounded_tier / 7), precision)
