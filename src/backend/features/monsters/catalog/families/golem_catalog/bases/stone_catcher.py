from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

STONE_CATCHER = MemberBaseDTO(
    id="stone_catcher",
    role="veteran",
    assembly_cost=23,
    stats=BaseStatsDTO(
        strength=29,
        agility=15,
        endurance=30,
        intellect=11,
        memory=12,
        mental=18,
        perception=19,
        projection=10,
        prediction=17,
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
