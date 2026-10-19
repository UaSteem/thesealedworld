from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

STONE_CRUSHER = MemberBaseDTO(
    id="stone_crusher",
    role="veteran",
    assembly_cost=23,
    stats=BaseStatsDTO(
        strength=32,
        agility=10,
        endurance=31,
        intellect=9,
        memory=10,
        mental=17,
        perception=13,
        projection=9,
        prediction=13,
    ),
    loadout=BaseLoadoutDTO(
        two_hand="golem_crushing_arms",
        chest_armor="golem_shell",
        amulet="golem_core",
    ),
    tiers=TierAvailabilityDTO(min_tier=2, max_tier=5),
    spawn_weight=100,
)
