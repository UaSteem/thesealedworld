from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

ALPHA_PRIME = MemberBaseDTO(
    id="alpha_prime",
    role="boss",
    stats=BaseStatsDTO(
        strength=21,
        agility=20,
        endurance=22,
        intellect=16,
        memory=15,
        mental=19,
        perception=18,
        projection=17,
        prediction=14,
    ),
    loadout=BaseLoadoutDTO(
        main_hand="wolf_alpha_fangs",
        off_hand="wolf_bone_shoulders",
        chest_armor="wolf_heavy_hide",
        amulet="wolf_pack_mark",
    ),
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=600,
    default_image=ImageAssetReference(
        **{
            "asset_id": "wolf_pack.fenrir",
            "source_path": "assets/monster_defaults/wolf_pack/png/fenrir-v1.png",
            "review_status": "accepted",
            "display_mirror": False,
        }
    ),
)
