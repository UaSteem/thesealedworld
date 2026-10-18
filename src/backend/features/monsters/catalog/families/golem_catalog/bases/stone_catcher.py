from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

STONE_CATCHER = MemberBaseDTO(
    id="stone_catcher",
    role="veteran",
    assembly_cost=60,
    stats=BaseStatsDTO(
        strength=26,
        agility=14,
        endurance=27,
        intellect=10,
        memory=11,
        mental=16,
        perception=17,
        projection=9,
        prediction=16,
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
