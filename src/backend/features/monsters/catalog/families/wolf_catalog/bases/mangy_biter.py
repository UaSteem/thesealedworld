from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

MANGY_BITER = MemberBaseDTO(
    id="mangy_biter",
    role="minion",
    assembly_cost=18,
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
    default_image=ImageAssetReference(
        **{
            "asset_id": "wolf_pack.mangy_biter",
            "source_path": "assets/monster_defaults/wolf_pack/png/mangy_biter-v1.png",
            "review_status": "review_ready",
            "display_mirror": False,
        }
    ),
)
