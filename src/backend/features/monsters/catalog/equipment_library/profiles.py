"""Authored monster-only mechanics; these are not ordinary player loot pools.

Only implemented combat modifiers belong here. Keep each profile reusable
across species; species names and descriptions belong to item references.
"""

from types import MappingProxyType

PROFILES = MappingProxyType(
    {
        "precision": ("weapon_accuracy", "crit_chance", "armor_penetration_pct_bonus"),
        "impact": ("weapon_accuracy", "armor_penetration_pct_bonus", "crit_chance"),
        "offhand": ("off_hand_accuracy", "crit_chance", "armor_penetration_pct_bonus"),
        "mobile": ("evasion_bonus", "armor_flat", "physical_resistance_bonus", "hp_bonus"),
        "fortified": ("armor_flat", "physical_resistance_bonus", "hp_bonus"),
        "guard": ("shield_guard_power_bonus", "physical_resistance_bonus", "hp_bonus"),
        "nimble": ("hp_bonus", "attribute_agility", "attribute_perception", "attribute_endurance"),
        "bruiser": ("hp_bonus", "attribute_strength", "attribute_endurance", "attribute_perception"),
        "duelist": ("hp_bonus", "attribute_agility", "attribute_strength", "attribute_perception"),
        "ammunition": (),
    }
)


def equipment_id(*, base_id: str, slot: str, profile_id: str, tier: int) -> str:
    if profile_id not in PROFILES or type(tier) is not int or not 0 <= tier <= 7:
        raise ValueError("Unknown equipment profile or tier")
    return f"{base_id}.{slot}.{profile_id}.t{tier}"
