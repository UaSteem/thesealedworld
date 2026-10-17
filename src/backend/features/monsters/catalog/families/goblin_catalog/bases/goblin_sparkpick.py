from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import (
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

GOBLIN_SPARKPICK = MemberBaseDTO(
    id="goblin_sparkpick",
    role="minion",
    stats=BaseStatsDTO(
        strength=12,
        agility=14,
        endurance=13,
        intellect=11,
        memory=8,
        mental=9,
        perception=10,
        projection=7,
        prediction=6,
    ),
    equipment_set_id="sparkpick",
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=20,
    default_image=ImageAssetReference(
        asset_id="goblin_tribe.goblin_sparkpick",
        source_path="assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_sparkpick-face-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
