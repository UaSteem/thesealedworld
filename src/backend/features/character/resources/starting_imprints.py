from __future__ import annotations

from dataclasses import dataclass

ATTRIBUTE_KEYS: tuple[str, ...] = (
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

STARTING_ATTRIBUTE_BUDGET = 135
STARTING_ATTRIBUTE_MAX_SPREAD = 8


def _attribute_values(
    *,
    strength: int,
    agility: int,
    endurance: int,
    intellect: int,
    memory: int,
    mental: int,
    perception: int,
    projection: int,
    prediction: int,
) -> tuple[tuple[str, int], ...]:
    values = {
        "strength": strength,
        "agility": agility,
        "endurance": endurance,
        "intellect": intellect,
        "memory": memory,
        "mental": mental,
        "perception": perception,
        "projection": projection,
        "prediction": prediction,
    }
    if set(values) != set(ATTRIBUTE_KEYS):
        raise ValueError("Manual starting imprint attributes must cover every attribute")
    _validate_attribute_values(values)
    return tuple((key, values[key]) for key in ATTRIBUTE_KEYS)


def _validate_attribute_values(values: dict[str, int]) -> None:
    if set(values) != set(ATTRIBUTE_KEYS):
        raise ValueError("Starting attributes must cover every attribute")
    if any(type(value) is not int or value <= 0 for value in values.values()):
        raise ValueError("Starting attributes must be positive integers")
    if sum(values.values()) != STARTING_ATTRIBUTE_BUDGET:
        raise ValueError("Starting attributes must total 135")
    if max(values.values()) - min(values.values()) > STARTING_ATTRIBUTE_MAX_SPREAD:
        raise ValueError("Starting attribute spread must not exceed 8")
    for offset in range(0, len(ATTRIBUTE_KEYS), 3):
        if len({values[key] for key in ATTRIBUTE_KEYS[offset : offset + 3]}) != 3:
            raise ValueError("Starting attributes must be distinct within each triple")


@dataclass(frozen=True, slots=True)
class StartingLoadoutPack:
    item_base_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class StartingImprintDefinition:
    imprint_key: str
    title: str
    primary_stats: tuple[str, ...]
    attribute_values: tuple[tuple[str, int], ...]
    combat_style: str
    armor_pack: str
    utility_pack: str
    skill_xp: tuple[tuple[str, float], ...]
    lore_tags: tuple[str, ...] = ()
    description: str = ""


STARTING_COMBAT_STYLES: dict[str, StartingLoadoutPack] = {
    "one_handed_shield": StartingLoadoutPack(("sword", "shield")),
    "mace_shield": StartingLoadoutPack(("mace", "shield")),
    "flamberge_two_handed": StartingLoadoutPack(("flamberge",)),
    "two_handed_impact": StartingLoadoutPack(("warhammer",)),
    "polearm_reach": StartingLoadoutPack(("halberd",)),
    "dual_fencing_light": StartingLoadoutPack(("stiletto", "main_gauche")),
    "shortbow_quiver": StartingLoadoutPack(("shortbow", "quiver_frost")),
    "longbow_quiver": StartingLoadoutPack(("longbow", "quiver_fire")),
}

STARTING_ARMOR_PACKS: dict[str, StartingLoadoutPack] = {
    "heavy_full": StartingLoadoutPack(("plate_chest",)),
    "medium_full": StartingLoadoutPack(("jerkin",)),
    "light_full": StartingLoadoutPack(("leather_armor",)),
}

STARTING_UTILITY_PACKS: dict[str, StartingLoadoutPack] = {
    "starter_basic": StartingLoadoutPack(("linen_shirt", "fur_pants", "travel_boots", "belt")),
}

# Fixed T0 starts selected from the reviewed 14-style reference. No runtime dependency on var/.
STARTING_IMPRINTS: dict[str, StartingImprintDefinition] = {
    "starter_guard_01": StartingImprintDefinition(
        imprint_key="starter_guard_01",
        title="Меч и щит — средняя броня",
        primary_stats=("endurance", "strength", "perception", "agility"),
        attribute_values=_attribute_values(
            strength=17,
            agility=14,
            endurance=20,
            intellect=12,
            memory=16,
            mental=13,
            perception=16,
            projection=13,
            prediction=14,
        ),
        combat_style="one_handed_shield",
        armor_pack="medium_full",
        utility_pack="starter_basic",
        skill_xp=(("skill_swords", 0.1), ("skill_shield_mastery", 0.075), ("skill_medium_armor", 0.05)),
        lore_tags=("physical", "medium", "starter"),
    ),
    "starter_heavy_sword_guard_01": StartingImprintDefinition(
        imprint_key="starter_heavy_sword_guard_01",
        title="Меч и щит — тяжёлая броня",
        primary_stats=("endurance", "strength", "perception", "agility"),
        attribute_values=_attribute_values(
            strength=17,
            agility=14,
            endurance=20,
            intellect=12,
            memory=16,
            mental=13,
            perception=16,
            projection=13,
            prediction=14,
        ),
        combat_style="one_handed_shield",
        armor_pack="heavy_full",
        utility_pack="starter_basic",
        skill_xp=(("skill_swords", 0.1), ("skill_shield_mastery", 0.075), ("skill_heavy_armor", 0.05)),
        lore_tags=("physical", "heavy", "starter"),
    ),
    "starter_mace_guard_01": StartingImprintDefinition(
        imprint_key="starter_mace_guard_01",
        title="Булава и щит — средняя броня",
        primary_stats=("endurance", "strength", "perception", "agility"),
        attribute_values=_attribute_values(
            strength=19,
            agility=13,
            endurance=20,
            intellect=12,
            memory=15,
            mental=14,
            perception=16,
            projection=12,
            prediction=14,
        ),
        combat_style="mace_shield",
        armor_pack="medium_full",
        utility_pack="starter_basic",
        skill_xp=(("skill_macing", 0.1), ("skill_shield_mastery", 0.075), ("skill_medium_armor", 0.05)),
        lore_tags=("physical", "medium", "starter"),
    ),
    "starter_heavy_guard_01": StartingImprintDefinition(
        imprint_key="starter_heavy_guard_01",
        title="Булава и щит — тяжёлая броня",
        primary_stats=("endurance", "strength", "perception", "agility"),
        attribute_values=_attribute_values(
            strength=19,
            agility=13,
            endurance=20,
            intellect=12,
            memory=15,
            mental=14,
            perception=16,
            projection=12,
            prediction=14,
        ),
        combat_style="mace_shield",
        armor_pack="heavy_full",
        utility_pack="starter_basic",
        skill_xp=(("skill_macing", 0.1), ("skill_shield_mastery", 0.075), ("skill_heavy_armor", 0.05)),
        lore_tags=("physical", "heavy", "starter"),
    ),
    "starter_tactician_01": StartingImprintDefinition(
        imprint_key="starter_tactician_01",
        title="Двуручный меч — средняя броня",
        primary_stats=("strength", "agility", "endurance", "prediction"),
        attribute_values=_attribute_values(
            strength=18,
            agility=16,
            endurance=19,
            intellect=12,
            memory=15,
            mental=13,
            perception=16,
            projection=12,
            prediction=14,
        ),
        combat_style="flamberge_two_handed",
        armor_pack="medium_full",
        utility_pack="starter_basic",
        skill_xp=(("skill_swords", 0.1), ("skill_two_handed", 0.075), ("skill_medium_armor", 0.05)),
        lore_tags=("physical", "medium", "starter"),
    ),
    "starter_heavy_tactician_01": StartingImprintDefinition(
        imprint_key="starter_heavy_tactician_01",
        title="Двуручный меч — тяжёлая броня",
        primary_stats=("strength", "agility", "endurance", "prediction"),
        attribute_values=_attribute_values(
            strength=18,
            agility=16,
            endurance=19,
            intellect=12,
            memory=15,
            mental=13,
            perception=16,
            projection=12,
            prediction=14,
        ),
        combat_style="flamberge_two_handed",
        armor_pack="heavy_full",
        utility_pack="starter_basic",
        skill_xp=(("skill_swords", 0.1), ("skill_two_handed", 0.075), ("skill_heavy_armor", 0.05)),
        lore_tags=("physical", "heavy", "starter"),
    ),
    "starter_medium_breaker_01": StartingImprintDefinition(
        imprint_key="starter_medium_breaker_01",
        title="Двуручный молот — средняя броня",
        primary_stats=("strength", "endurance", "perception", "agility"),
        attribute_values=_attribute_values(
            strength=20,
            agility=13,
            endurance=19,
            intellect=12,
            memory=14,
            mental=13,
            perception=18,
            projection=12,
            prediction=14,
        ),
        combat_style="two_handed_impact",
        armor_pack="medium_full",
        utility_pack="starter_basic",
        skill_xp=(("skill_macing", 0.1), ("skill_two_handed", 0.075), ("skill_medium_armor", 0.05)),
        lore_tags=("physical", "medium", "starter"),
    ),
    "starter_breaker_01": StartingImprintDefinition(
        imprint_key="starter_breaker_01",
        title="Двуручный молот — тяжёлая броня",
        primary_stats=("strength", "endurance", "perception", "agility"),
        attribute_values=_attribute_values(
            strength=20,
            agility=13,
            endurance=19,
            intellect=12,
            memory=14,
            mental=13,
            perception=18,
            projection=12,
            prediction=14,
        ),
        combat_style="two_handed_impact",
        armor_pack="heavy_full",
        utility_pack="starter_basic",
        skill_xp=(("skill_macing", 0.1), ("skill_two_handed", 0.075), ("skill_heavy_armor", 0.05)),
        lore_tags=("physical", "heavy", "starter"),
    ),
    "starter_rift_survivor_01": StartingImprintDefinition(
        imprint_key="starter_rift_survivor_01",
        title="Алебарда — средняя броня",
        primary_stats=("strength", "endurance", "agility", "perception"),
        attribute_values=_attribute_values(
            strength=19,
            agility=15,
            endurance=18,
            intellect=12,
            memory=14,
            mental=13,
            perception=17,
            projection=12,
            prediction=15,
        ),
        combat_style="polearm_reach",
        armor_pack="medium_full",
        utility_pack="starter_basic",
        skill_xp=(("skill_polearms", 0.1), ("skill_two_handed", 0.075), ("skill_medium_armor", 0.05)),
        lore_tags=("physical", "medium", "starter"),
    ),
    "starter_heavy_rift_survivor_01": StartingImprintDefinition(
        imprint_key="starter_heavy_rift_survivor_01",
        title="Алебарда — тяжёлая броня",
        primary_stats=("strength", "endurance", "agility", "perception"),
        attribute_values=_attribute_values(
            strength=19,
            agility=15,
            endurance=18,
            intellect=12,
            memory=14,
            mental=13,
            perception=17,
            projection=12,
            prediction=15,
        ),
        combat_style="polearm_reach",
        armor_pack="heavy_full",
        utility_pack="starter_basic",
        skill_xp=(("skill_polearms", 0.1), ("skill_two_handed", 0.075), ("skill_heavy_armor", 0.05)),
        lore_tags=("physical", "heavy", "starter"),
    ),
    "starter_dual_blades_01": StartingImprintDefinition(
        imprint_key="starter_dual_blades_01",
        title="Стилет и дага — лёгкая броня",
        primary_stats=("agility", "perception", "endurance", "prediction"),
        attribute_values=_attribute_values(
            strength=12,
            agility=20,
            endurance=15,
            intellect=15,
            memory=16,
            mental=13,
            perception=17,
            projection=13,
            prediction=14,
        ),
        combat_style="dual_fencing_light",
        armor_pack="light_full",
        utility_pack="starter_basic",
        skill_xp=(("skill_fencing", 0.1), ("skill_dual_wield", 0.075), ("skill_light_armor", 0.05)),
        lore_tags=("physical", "light", "starter"),
    ),
    "starter_medium_dual_blades_01": StartingImprintDefinition(
        imprint_key="starter_medium_dual_blades_01",
        title="Стилет и дага — средняя броня",
        primary_stats=("agility", "perception", "endurance", "prediction"),
        attribute_values=_attribute_values(
            strength=12,
            agility=20,
            endurance=15,
            intellect=15,
            memory=16,
            mental=13,
            perception=17,
            projection=13,
            prediction=14,
        ),
        combat_style="dual_fencing_light",
        armor_pack="medium_full",
        utility_pack="starter_basic",
        skill_xp=(("skill_fencing", 0.1), ("skill_dual_wield", 0.075), ("skill_medium_armor", 0.05)),
        lore_tags=("physical", "medium", "starter"),
    ),
    "starter_hunter_01": StartingImprintDefinition(
        imprint_key="starter_hunter_01",
        title="Короткий лук — лёгкая броня",
        primary_stats=("agility", "perception", "endurance", "memory"),
        attribute_values=_attribute_values(
            strength=12,
            agility=19,
            endurance=16,
            intellect=12,
            memory=16,
            mental=13,
            perception=18,
            projection=15,
            prediction=14,
        ),
        combat_style="shortbow_quiver",
        armor_pack="light_full",
        utility_pack="starter_basic",
        skill_xp=(("skill_archery", 0.1), ("skill_ranged_combat", 0.075), ("skill_light_armor", 0.05)),
        lore_tags=("physical", "light", "starter"),
    ),
    "starter_archer_01": StartingImprintDefinition(
        imprint_key="starter_archer_01",
        title="Длинный лук — лёгкая броня",
        primary_stats=("agility", "perception", "endurance", "strength"),
        attribute_values=_attribute_values(
            strength=13,
            agility=18,
            endurance=16,
            intellect=12,
            memory=15,
            mental=14,
            perception=18,
            projection=15,
            prediction=14,
        ),
        combat_style="longbow_quiver",
        armor_pack="light_full",
        utility_pack="starter_basic",
        skill_xp=(("skill_archery", 0.1), ("skill_ranged_combat", 0.075), ("skill_light_armor", 0.05)),
        lore_tags=("physical", "light", "starter"),
    ),
}

DEFAULT_STARTING_IMPRINT_KEY = "starter_guard_01"
