"""Explicit accepted alpha deltas applied to frozen migration snapshots.

Historical fixtures stay unchanged; every unlisted mechanic remains compared.
"""

from copy import deepcopy

ATTRIBUTES = (
    "strength",
    "agility",
    "endurance",
    "intellect",
    "memory",
    "mental",
    "perception",
    "projection",
    "prediction",
)
RAT_STATS = {
    "sewer_rat": (7, 10, 7, 3, 4, 6, 8, 3, 5),
    "scavenger_rat": (9, 10, 8, 4, 4, 6, 8, 3, 5),
    "swarm_rat": (8, 12, 8, 4, 6, 5, 9, 3, 7),
    "tunnel_rat": (13, 15, 14, 9, 8, 11, 12, 7, 10),
    "pack_rat": (14, 13, 15, 10, 8, 11, 12, 7, 9),
    "screecher": (12, 15, 13, 10, 8, 11, 14, 7, 9),
    "burrow_guard": (15, 14, 17, 11, 10, 13, 12, 9, 8),
    "ironfang": (17, 15, 14, 11, 10, 12, 13, 8, 9),
    "heavy_rat": (15, 13, 17, 11, 10, 14, 12, 9, 8),
    "rat_brute": (23, 21, 24, 16, 15, 22, 20, 19, 18),
    "brood_alpha": (22, 24, 23, 19, 16, 20, 21, 18, 15),
    "rat_king": (23, 16, 24, 19, 18, 22, 21, 20, 15),
}
GOBLIN_STATS = {
    "goblin_scavenger": (9, 11, 9, 8, 6, 6, 10, 5, 6),
    "goblin_sparkpick": (10, 12, 10, 8, 6, 7, 9, 6, 6),
    "goblin_sneak": (9, 14, 9, 8, 6, 7, 12, 5, 7),
    "goblin_cutter": (11, 13, 11, 8, 6, 8, 11, 5, 7),
}
GOLEM_STATS = {
    "stone_worker": (22, 8, 24, 7, 8, 12, 9, 6, 8),
    "stone_sentry": (20, 10, 23, 9, 10, 13, 15, 7, 12),
    "stone_thrower": (19, 12, 20, 8, 9, 12, 18, 9, 14),
    "stone_ram": (25, 7, 25, 6, 7, 13, 10, 6, 9),
    "stone_crusher": (32, 10, 31, 9, 10, 17, 13, 9, 13),
    "stone_bulwark": (28, 10, 35, 11, 13, 20, 15, 9, 15),
    "stone_catcher": (29, 15, 30, 11, 12, 18, 19, 10, 17),
    "rune_guardian": (32, 12, 40, 16, 18, 25, 18, 17, 20),
    "rune_punisher": (38, 16, 34, 14, 15, 23, 22, 15, 22),
    "rune_resonator": (29, 13, 35, 23, 22, 26, 20, 24, 21),
    "quarry_overseer": (39, 17, 42, 24, 25, 31, 26, 23, 26),
    "stone_colossus": (46, 11, 48, 14, 17, 30, 20, 16, 19),
}
WOLF_SINGLE_HAND = {"cub", "runner", "mangy_biter", "stalker", "flanker", "snapper"}


def approved_mechanics(family_id, variant_id, historical):
    expected = deepcopy(historical)
    stats = {"rat_swarm": RAT_STATS, "goblin_tribe": GOBLIN_STATS}.get(family_id, {})
    if variant_id in stats:
        expected["base_stats"] = dict(zip(ATTRIBUTES, stats[variant_id], strict=True))
    if family_id in {"wolf_pack", "bandit_gang", "golem_foundry"}:
        expected["min_tier"] = 2 if family_id == "golem_foundry" else 1
    single = family_id == "rat_swarm" and variant_id in {"sewer_rat", "scavenger_rat", "swarm_rat"}
    single |= family_id == "wolf_pack" and variant_id in WOLF_SINGLE_HAND
    if single:
        expected["fixed_loadout"]["off_hand"] = None
        expected["skills"].remove("skill_dual_wield")
    return expected
