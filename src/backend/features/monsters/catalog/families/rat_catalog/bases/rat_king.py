from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

RAT_KING = MemberBaseDTO(
    id="rat_king",
    role="boss",
    assembly_cost=45,
    stats=BaseStatsDTO(
        strength=23,
        agility=16,
        endurance=24,
        intellect=19,
        memory=18,
        mental=22,
        perception=21,
        projection=20,
        prediction=15,
    ),
    loadout=BaseLoadoutDTO(
        main_hand=None,
        two_hand="rat_poison_spit",
        head_armor=None,
        chest_armor="rat_heavy_hide",
        arms_armor=None,
        legs_armor=None,
        feetwear=None,
        outer_garment=None,
        gloves_garment=None,
        amulet="rat_plague_gland",
        ring_1=None,
        ring_2=None,
        belt_accessory=None,
        off_hand="rat_poison_glands",
    ),
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=600,
    default_image=ImageAssetReference(
        asset_id="rat_swarm.rat_king",
        source_path="assets/monster_defaults/rat_swarm/png/rat_king-v2.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
