from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import (
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

GOBLIN_SLINGER = MemberBaseDTO(
    id="goblin_slinger",
    role="veteran",
    assembly_cost=23,
    stats=BaseStatsDTO(
        strength=12,
        agility=15,
        endurance=13,
        intellect=11,
        memory=10,
        mental=9,
        perception=14,
        projection=7,
        prediction=8,
    ),
    equipment_set_id="slinger",
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=50,
    default_image=ImageAssetReference(
        asset_id="goblin_tribe.goblin_slinger",
        source_path="assets/monster_defaults/goblin_tribe/svg/goblin_slinger.svg",
        review_status="accepted",
        display_mirror=False,
    ),
)
