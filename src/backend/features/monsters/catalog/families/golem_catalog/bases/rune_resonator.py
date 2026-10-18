from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

RUNE_RESONATOR = MemberBaseDTO(
    id="rune_resonator",
    role="elite",
    assembly_cost=80,
    stats=BaseStatsDTO(
        strength=26,
        agility=12,
        endurance=32,
        intellect=21,
        memory=20,
        mental=24,
        perception=18,
        projection=22,
        prediction=19,
    ),
    loadout=BaseLoadoutDTO(
        main_hand="golem_fist",
        off_hand="golem_grasp",
        chest_armor="golem_shell",
        amulet="golem_core",
    ),
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=100,
)
