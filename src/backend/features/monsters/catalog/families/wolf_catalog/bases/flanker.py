from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

FLANKER = MemberBaseDTO(
    id="flanker",
    role="veteran",
    assembly_cost=27,
    stats=BaseStatsDTO(
        strength=15,
        agility=16,
        endurance=14,
        intellect=11,
        memory=10,
        mental=12,
        perception=13,
        projection=8,
        prediction=9,
    ),
    loadout=BaseLoadoutDTO(
        main_hand="wolf_bite_claws",
        off_hand="wolf_raking_claws",
        chest_armor="wolf_medium_hide",
        amulet="wolf_pack_mark",
    ),
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=50,
    default_image=ImageAssetReference(
        **{
            "asset_id": "wolf_pack.flanker",
            "source_path": "assets/monster_defaults/wolf_pack/png/flanker-v1.png",
            "review_status": "review_ready",
            "display_mirror": False,
        }
    ),
)
