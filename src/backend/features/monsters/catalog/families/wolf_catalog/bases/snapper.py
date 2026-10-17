from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

SNAPPER = MemberBaseDTO(
    id="snapper",
    role="veteran",
    stats=BaseStatsDTO(
        strength=16,
        agility=14,
        endurance=15,
        intellect=10,
        memory=9,
        mental=12,
        perception=13,
        projection=8,
        prediction=11,
    ),
    loadout=BaseLoadoutDTO(
        main_hand="wolf_bite_claws", off_hand="wolf_locking_fangs", chest_armor="wolf_hide", amulet="wolf_pack_mark"
    ),
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=50,
    default_image=ImageAssetReference(
        **{
            "asset_id": "wolf_pack.snapper",
            "source_path": "assets/monster_defaults/wolf_pack/png/snapper-v1.png",
            "review_status": "review_ready",
            "display_mirror": False,
        }
    ),
)
