from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

DIRE_WOLF = MemberBaseDTO(
    id="dire_wolf",
    role="elite",
    assembly_cost=36,
    stats=BaseStatsDTO(
        strength=17,
        agility=14,
        endurance=16,
        intellect=11,
        memory=10,
        mental=15,
        perception=13,
        projection=9,
        prediction=12,
    ),
    loadout=BaseLoadoutDTO(
        main_hand="wolf_elite_fangs",
        off_hand="wolf_bone_shoulders",
        chest_armor="wolf_heavy_hide",
        amulet="wolf_pack_mark",
    ),
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=150,
    default_image=ImageAssetReference(
        **{
            "asset_id": "wolf_pack.dire_wolf",
            "source_path": "assets/monster_defaults/wolf_pack/png/dire_wolf-v1.png",
            "review_status": "review_ready",
            "display_mirror": False,
        }
    ),
)
