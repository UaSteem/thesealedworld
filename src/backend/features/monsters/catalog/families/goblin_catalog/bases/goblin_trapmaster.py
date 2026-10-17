from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import (
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

GOBLIN_TRAPMASTER = MemberBaseDTO(
    id="goblin_trapmaster",
    role="elite",
    stats=BaseStatsDTO(
        strength=11,
        agility=14,
        endurance=13,
        intellect=16,
        memory=12,
        mental=10,
        perception=15,
        projection=8,
        prediction=9,
    ),
    equipment_set_id="trapmaster",
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=150,
    default_image=ImageAssetReference(
        asset_id="goblin_tribe.goblin_trapmaster",
        source_path="assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_trapmaster-face-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
