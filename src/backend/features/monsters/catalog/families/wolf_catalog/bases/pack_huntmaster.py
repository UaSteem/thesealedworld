from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

PACK_HUNTMASTER = MemberBaseDTO(
    id="pack_huntmaster",
    role="boss",
    assembly_cost=54,
    stats=BaseStatsDTO(
        strength=21,
        agility=19,
        endurance=22,
        intellect=16,
        memory=17,
        mental=20,
        perception=18,
        projection=15,
        prediction=14,
    ),
    loadout=BaseLoadoutDTO(
        main_hand="wolf_alpha_fangs",
        off_hand="wolf_braced_mane",
        chest_armor="wolf_heavy_hide",
        amulet="wolf_pack_mark",
    ),
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=600,
    default_image=ImageAssetReference(
        **{
            "asset_id": "wolf_pack.pack_huntmaster",
            "source_path": "assets/monster_defaults/wolf_pack/png/pack_huntmaster-v1.png",
            "review_status": "review_ready",
            "display_mirror": False,
        }
    ),
)
