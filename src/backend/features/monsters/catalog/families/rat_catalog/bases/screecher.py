from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

SCREECHER = MemberBaseDTO(
    id="screecher",
    role="veteran",
    assembly_cost=23,
    stats=BaseStatsDTO(
        strength=12,
        agility=15,
        endurance=13,
        intellect=10,
        memory=8,
        mental=11,
        perception=14,
        projection=7,
        prediction=9,
    ),
    loadout=BaseLoadoutDTO(
        main_hand=None,
        two_hand="rat_poison_spit",
        head_armor=None,
        chest_armor="rat_medium_hide",
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
    spawn_weight=50,
    default_image=ImageAssetReference(
        asset_id="rat_swarm.screecher",
        source_path="assets/monster_defaults/rat_swarm/png/screecher-v2.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
