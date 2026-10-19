from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

STONE_BULWARK = MemberBaseDTO(
    id="stone_bulwark",
    role="veteran",
    assembly_cost=23,
    stats=BaseStatsDTO(
        strength=28,
        agility=10,
        endurance=35,
        intellect=11,
        memory=13,
        mental=20,
        perception=15,
        projection=9,
        prediction=15,
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
