from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

RAT_BRUTE = MemberBaseDTO(
    id="rat_brute",
    role="boss",
    assembly_cost=45,
    stats=BaseStatsDTO(
        strength=23,
        agility=21,
        endurance=24,
        intellect=16,
        memory=15,
        mental=22,
        perception=20,
        projection=19,
        prediction=18,
    ),
    loadout=BaseLoadoutDTO(
        main_hand=None,
        off_hand=None,
        two_hand="rat_crushing_bite",
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
    ),
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=600,
    default_image=ImageAssetReference(
        asset_id="rat_swarm.rat_brute",
        source_path="assets/monster_defaults/rat_swarm/png/rat_brute-v2.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
