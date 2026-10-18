from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

STONE_BULWARK = MemberBaseDTO(
    id="stone_bulwark",
    role="veteran",
    assembly_cost=60,
    stats=BaseStatsDTO(
        strength=25,
        agility=9,
        endurance=32,
        intellect=10,
        memory=12,
        mental=18,
        perception=14,
        projection=8,
        prediction=14,
    ),
    loadout=BaseLoadoutDTO(
        main_hand="golem_fist",
        off_hand="golem_slab",
        chest_armor="golem_shell",
        amulet="golem_core",
    ),
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=100,
)
