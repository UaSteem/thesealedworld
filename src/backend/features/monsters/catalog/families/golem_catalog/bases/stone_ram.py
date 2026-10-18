from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

STONE_RAM = MemberBaseDTO(
    id="stone_ram",
    role="minion",
    assembly_cost=40,
    stats=BaseStatsDTO(
        strength=25,
        agility=7,
        endurance=25,
        intellect=6,
        memory=7,
        mental=13,
        perception=10,
        projection=6,
        prediction=9,
    ),
    loadout=BaseLoadoutDTO(
        two_hand="golem_crushing_arms",
        chest_armor="golem_shell",
        amulet="golem_core",
    ),
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=100,
)
