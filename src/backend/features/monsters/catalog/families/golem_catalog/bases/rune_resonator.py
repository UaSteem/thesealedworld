from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

RUNE_RESONATOR = MemberBaseDTO(
    id="rune_resonator",
    role="elite",
    assembly_cost=30,
    stats=BaseStatsDTO(
        strength=29,
        agility=13,
        endurance=35,
        intellect=23,
        memory=22,
        mental=26,
        perception=20,
        projection=24,
        prediction=21,
    ),
    loadout=BaseLoadoutDTO(
        main_hand="golem_fist",
        off_hand="golem_grasp",
        chest_armor="golem_shell",
        amulet="golem_core",
    ),
    tiers=TierAvailabilityDTO(min_tier=2, max_tier=5),
    spawn_weight=100,
)
