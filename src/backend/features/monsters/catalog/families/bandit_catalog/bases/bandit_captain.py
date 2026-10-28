from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

BANDIT_CAPTAIN = MemberBaseDTO(
    id="bandit_captain",
    role="elite",
    assembly_cost=30,
    stats=BaseStatsDTO(
        strength=18,
        agility=16,
        endurance=17,
        intellect=12,
        memory=11,
        mental=15,
        perception=13,
        projection=14,
        prediction=10,
    ),
    loadout=BaseLoadoutDTO(
        main_hand="sword",
        off_hand="shield",
        two_hand=None,
        head_armor=None,
        chest_armor="medium_chest_armor",
        arms_armor=None,
        legs_armor=None,
        feetwear=None,
        outer_garment=None,
        gloves_garment=None,
        amulet="amulet",
        ring_1=None,
        ring_2=None,
        belt_accessory=None,
    ),
    tiers=TierAvailabilityDTO(min_tier=1, max_tier=5),
    spawn_weight=150,
    default_image=ImageAssetReference(
        asset_id="bandit_gang.bandit_captain",
        source_path="assets/monster_defaults/bandit_gang/png/bandit_captain-v1.png",
        review_status="accepted",
        display_mirror=True,
    ),
)
