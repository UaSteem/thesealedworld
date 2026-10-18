from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

STONE_THROWER = MemberBaseDTO(
    id="stone_thrower",
    role="minion",
    assembly_cost=40,
    stats=BaseStatsDTO(
        strength=19,
        agility=12,
        endurance=20,
        intellect=8,
        memory=9,
        mental=12,
        perception=18,
        projection=9,
        prediction=14,
    ),
    loadout=BaseLoadoutDTO(
        two_hand="golem_stone_throw",
        quiver="golem_stone_reserve",
        chest_armor="golem_shell",
        amulet="golem_core",
    ),
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=100,
)
