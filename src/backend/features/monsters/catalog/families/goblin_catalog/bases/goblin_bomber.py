from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import (
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

GOBLIN_BOMBER = MemberBaseDTO(
    id="goblin_bomber",
    role="elite",
    stats=BaseStatsDTO(
        strength=12,
        agility=16,
        endurance=15,
        intellect=14,
        memory=9,
        mental=11,
        perception=13,
        projection=8,
        prediction=10,
    ),
    equipment_set_id="bomber",
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=150,
    default_image=ImageAssetReference(
        asset_id="goblin_tribe.goblin_bomber",
        source_path="assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_bomber-face-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
