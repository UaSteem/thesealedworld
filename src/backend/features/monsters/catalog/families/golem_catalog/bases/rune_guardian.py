from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

RUNE_GUARDIAN = MemberBaseDTO(
    id="rune_guardian",
    role="elite",
    assembly_cost=80,
    stats=BaseStatsDTO(
        strength=29,
        agility=11,
        endurance=36,
        intellect=15,
        memory=16,
        mental=23,
        perception=16,
        projection=16,
        prediction=18,
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
