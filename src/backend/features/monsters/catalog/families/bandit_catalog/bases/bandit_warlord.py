from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

BANDIT_WARLORD = MemberBaseDTO(
    id="bandit_warlord",
    role="elite",
    assembly_cost=30,
    stats=BaseStatsDTO(
        strength=15,
        agility=18,
        endurance=16,
        intellect=13,
        memory=11,
        mental=14,
        perception=17,
        projection=10,
        prediction=12,
    ),
    loadout=BaseLoadoutDTO(
        main_hand=None,
        two_hand="longbow",
        head_armor=None,
        chest_armor="light_chest_armor",
        arms_armor=None,
        legs_armor=None,
        feetwear=None,
        outer_garment=None,
        gloves_garment=None,
        amulet="amulet",
        ring_1=None,
        ring_2=None,
        belt_accessory=None,
        off_hand="quiver_bodkin",
    ),
    tiers=TierAvailabilityDTO(min_tier=1, max_tier=5),
    spawn_weight=150,
    default_image=ImageAssetReference(
        asset_id="bandit_gang.bandit_warlord",
        source_path="assets/monster_defaults/bandit_gang/png/bandit_warlord-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
