from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

MANGY_BITER = MemberBaseDTO(
    id="mangy_biter",
    role="minion",
    stats=BaseStatsDTO(
        strength=14,
        agility=15,
        endurance=13,
        intellect=9,
        memory=8,
        mental=11,
        perception=12,
        projection=7,
        prediction=10,
    ),
    loadout=BaseLoadoutDTO(
        main_hand="wolf_young_fangs", off_hand="wolf_locking_fangs", chest_armor="wolf_hide", amulet="wolf_pack_mark"
    ),
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=20,
)
