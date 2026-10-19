from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

STONE_COLOSSUS = MemberBaseDTO(
    id="stone_colossus",
    role="boss",
    assembly_cost=45,
    stats=BaseStatsDTO(
        strength=46,
        agility=11,
        endurance=48,
        intellect=14,
        memory=17,
        mental=30,
        perception=20,
        projection=16,
        prediction=19,
    ),
    loadout=BaseLoadoutDTO(
        two_hand="golem_crushing_arms",
        chest_armor="golem_shell",
        amulet="golem_core",
    ),
    tiers=TierAvailabilityDTO(min_tier=2, max_tier=5),
    spawn_weight=100,
)
