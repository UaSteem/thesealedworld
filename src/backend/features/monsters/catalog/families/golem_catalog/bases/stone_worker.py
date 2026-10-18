from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

STONE_WORKER = MemberBaseDTO(
    id="stone_worker",
    role="minion",
    assembly_cost=40,
    stats=BaseStatsDTO(
        strength=22,
        agility=8,
        endurance=24,
        intellect=7,
        memory=8,
        mental=12,
        perception=9,
        projection=6,
        prediction=8,
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
