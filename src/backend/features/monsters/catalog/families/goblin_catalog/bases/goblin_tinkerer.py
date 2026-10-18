from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import (
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

GOBLIN_TINKERER = MemberBaseDTO(
    id="goblin_tinkerer",
    role="elite",
    assembly_cost=30,
    stats=BaseStatsDTO(
        strength=11,
        agility=15,
        endurance=13,
        intellect=16,
        memory=12,
        mental=10,
        perception=14,
        projection=9,
        prediction=8,
    ),
    equipment_set_id="tinkerer",
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=150,
    default_image=ImageAssetReference(
        asset_id="goblin_tribe.goblin_tinkerer",
        source_path="assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_tinkerer-face-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
