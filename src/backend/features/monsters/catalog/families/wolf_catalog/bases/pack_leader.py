from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

PACK_LEADER = MemberBaseDTO(
    id="pack_leader",
    role="elite",
    assembly_cost=30,
    stats=BaseStatsDTO(
        strength=17,
        agility=15,
        endurance=16,
        intellect=11,
        memory=10,
        mental=13,
        perception=14,
        projection=12,
        prediction=9,
    ),
    loadout=BaseLoadoutDTO(
        main_hand="wolf_elite_fangs",
        off_hand="wolf_braced_mane",
        chest_armor="wolf_medium_hide",
        amulet="wolf_pack_mark",
    ),
    tiers=TierAvailabilityDTO(min_tier=1, max_tier=5),
    spawn_weight=150,
    default_image=ImageAssetReference(
        **{
            "asset_id": "wolf_pack.pack_leader",
            "source_path": "assets/monster_defaults/wolf_pack/png/pack_leader-v1.png",
            "review_status": "review_ready",
            "display_mirror": False,
        }
    ),
)
