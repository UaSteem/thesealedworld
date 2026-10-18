from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

QUARRY_OVERSEER = MemberBaseDTO(
    id="quarry_overseer",
    role="boss",
    assembly_cost=120,
    stats=BaseStatsDTO(
        strength=35,
        agility=15,
        endurance=38,
        intellect=22,
        memory=23,
        mental=28,
        perception=24,
        projection=21,
        prediction=24,
    ),
    loadout=BaseLoadoutDTO(
        main_hand="golem_fist",
        off_hand="golem_grasp",
        chest_armor="golem_shell",
        amulet="golem_core",
    ),
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=100,
)
