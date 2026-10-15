from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

OLD_FANG = MemberBaseDTO(
    id="old_fang",
    role="elite",
    stats=BaseStatsDTO(
        strength=17,
        agility=13,
        endurance=16,
        intellect=12,
        memory=11,
        mental=14,
        perception=15,
        projection=9,
        prediction=10,
    ),
    loadout=BaseLoadoutDTO(
        main_hand="wolf_elite_fangs",
        off_hand="wolf_locking_fangs",
        chest_armor="wolf_medium_hide",
        amulet="wolf_pack_mark",
    ),
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=150,
)
