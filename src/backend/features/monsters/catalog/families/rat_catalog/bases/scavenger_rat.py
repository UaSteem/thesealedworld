from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

SCAVENGER_RAT = MemberBaseDTO(
    id="scavenger_rat",
    role="minion",
    assembly_cost=6,
    stats=BaseStatsDTO(
        strength=9,
        agility=10,
        endurance=8,
        intellect=4,
        memory=4,
        mental=6,
        perception=8,
        projection=3,
        prediction=5,
    ),
    loadout=BaseLoadoutDTO(
        main_hand="rat_bite_claws",
        off_hand=None,
        two_hand=None,
        head_armor=None,
        chest_armor="rat_light_hide",
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
    spawn_weight=20,
    default_image=ImageAssetReference(
        asset_id="rat_swarm.scavenger_rat",
        source_path="assets/monster_defaults/rat_swarm/png/scavenger_rat-v2.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
