from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import (
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

GOBLIN_SCRAPGUARD = MemberBaseDTO(
    id="goblin_scrapguard",
    role="veteran",
    stats=BaseStatsDTO(
        strength=14,
        agility=13,
        endurance=15,
        intellect=10,
        memory=9,
        mental=11,
        perception=12,
        projection=8,
        prediction=7,
    ),
    equipment_set_id="scrapguard",
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=50,
    default_image=ImageAssetReference(
        asset_id="goblin_tribe.goblin_scrapguard",
        source_path="assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_scrapguard-face-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
