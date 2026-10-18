from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import (
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

GOBLIN_SPEARMAN = MemberBaseDTO(
    id="goblin_spearman",
    role="veteran",
    assembly_cost=23,
    stats=BaseStatsDTO(
        strength=13,
        agility=14,
        endurance=15,
        intellect=11,
        memory=9,
        mental=10,
        perception=12,
        projection=8,
        prediction=7,
    ),
    equipment_set_id="spearman",
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=50,
    default_image=ImageAssetReference(
        asset_id="goblin_tribe.goblin_spearman",
        source_path="assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_spearman-face-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
