from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

STONE_CRUSHER = MemberBaseDTO(
    id="stone_crusher",
    role="veteran",
    assembly_cost=60,
    stats=BaseStatsDTO(
        strength=29,
        agility=9,
        endurance=28,
        intellect=8,
        memory=9,
        mental=16,
        perception=12,
        projection=8,
        prediction=12,
    ),
    loadout=BaseLoadoutDTO(
        two_hand="golem_crushing_arms",
        chest_armor="golem_shell",
        amulet="golem_core",
    ),
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=100,
)
