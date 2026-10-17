from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import (
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

SCRAP_KING = MemberBaseDTO(
    id="scrap_king",
    role="boss",
    stats=BaseStatsDTO(
        strength=21,
        agility=15,
        endurance=22,
        intellect=20,
        memory=17,
        mental=19,
        perception=16,
        projection=18,
        prediction=14,
    ),
    equipment_set_id="scrap_king",
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=600,
    default_image=ImageAssetReference(
        asset_id="goblin_tribe.scrap_king",
        source_path="assets/monster_defaults/goblin_tribe/face_repair_candidates/scrap_king-standing-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
