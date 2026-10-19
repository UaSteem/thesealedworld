from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

RUNE_GUARDIAN = MemberBaseDTO(
    id="rune_guardian",
    role="elite",
    assembly_cost=30,
    stats=BaseStatsDTO(
        strength=32,
        agility=12,
        endurance=40,
        intellect=16,
        memory=18,
        mental=25,
        perception=18,
        projection=17,
        prediction=20,
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
