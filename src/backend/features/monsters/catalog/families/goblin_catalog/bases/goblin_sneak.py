from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import (
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

GOBLIN_SNEAK = MemberBaseDTO(
    id="goblin_sneak",
    role="minion",
    stats=BaseStatsDTO(
        strength=11,
        agility=14,
        endurance=12,
        intellect=10,
        memory=7,
        mental=8,
        perception=13,
        projection=6,
        prediction=9,
    ),
    equipment_set_id="sneak",
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=20,
    default_image=ImageAssetReference(
        asset_id="goblin_tribe.goblin_sneak",
        source_path="assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_sneak-face-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
