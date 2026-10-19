from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

RUNE_PUNISHER = MemberBaseDTO(
    id="rune_punisher",
    role="elite",
    assembly_cost=30,
    stats=BaseStatsDTO(
        strength=38,
        agility=16,
        endurance=34,
        intellect=14,
        memory=15,
        mental=23,
        perception=22,
        projection=15,
        prediction=22,
    ),
    loadout=BaseLoadoutDTO(
        two_hand="golem_crushing_arms",
        chest_armor="golem_shell",
        amulet="golem_core",
    ),
    tiers=TierAvailabilityDTO(min_tier=2, max_tier=5),
    spawn_weight=100,
)
