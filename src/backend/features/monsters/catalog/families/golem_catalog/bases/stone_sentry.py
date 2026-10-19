from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

STONE_SENTRY = MemberBaseDTO(
    id="stone_sentry",
    role="minion",
    assembly_cost=15,
    stats=BaseStatsDTO(
        strength=20,
        agility=10,
        endurance=23,
        intellect=9,
        memory=10,
        mental=13,
        perception=15,
        projection=7,
        prediction=12,
    ),
    loadout=BaseLoadoutDTO(
        main_hand="golem_fist",
        off_hand="golem_slab",
        chest_armor="golem_shell",
        amulet="golem_core",
    ),
    tiers=TierAvailabilityDTO(min_tier=2, max_tier=5),
    spawn_weight=100,
)
