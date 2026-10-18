from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

STONE_COLOSSUS = MemberBaseDTO(
    id="stone_colossus",
    role="boss",
    assembly_cost=120,
    stats=BaseStatsDTO(
        strength=42,
        agility=10,
        endurance=44,
        intellect=13,
        memory=15,
        mental=27,
        perception=18,
        projection=15,
        prediction=17,
    ),
    loadout=BaseLoadoutDTO(
        two_hand="golem_crushing_arms",
        chest_armor="golem_shell",
        amulet="golem_core",
    ),
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=100,
)
