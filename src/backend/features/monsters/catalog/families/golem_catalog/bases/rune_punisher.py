from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

RUNE_PUNISHER = MemberBaseDTO(
    id="rune_punisher",
    role="elite",
    assembly_cost=80,
    stats=BaseStatsDTO(
        strength=34,
        agility=14,
        endurance=31,
        intellect=13,
        memory=14,
        mental=21,
        perception=20,
        projection=14,
        prediction=20,
    ),
    loadout=BaseLoadoutDTO(
        two_hand="golem_crushing_arms",
        chest_armor="golem_shell",
        amulet="golem_core",
    ),
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=100,
)
