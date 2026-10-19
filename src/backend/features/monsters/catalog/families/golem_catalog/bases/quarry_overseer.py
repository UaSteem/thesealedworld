from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

QUARRY_OVERSEER = MemberBaseDTO(
    id="quarry_overseer",
    role="boss",
    assembly_cost=45,
    stats=BaseStatsDTO(
        strength=39,
        agility=17,
        endurance=42,
        intellect=24,
        memory=25,
        mental=31,
        perception=26,
        projection=23,
        prediction=26,
    ),
    loadout=BaseLoadoutDTO(
        main_hand="golem_fist",
        off_hand="golem_grasp",
        chest_armor="golem_shell",
        amulet="golem_core",
    ),
    tiers=TierAvailabilityDTO(min_tier=2, max_tier=5),
    spawn_weight=100,
)
