from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import (
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

GOBLIN_CUTTER = MemberBaseDTO(
    id="goblin_cutter",
    role="minion",
    assembly_cost=10,
    stats=BaseStatsDTO(
        strength=11,
        agility=13,
        endurance=11,
        intellect=8,
        memory=6,
        mental=8,
        perception=11,
        projection=5,
        prediction=7,
    ),
    equipment_set_id="cutter",
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=20,
    default_image=ImageAssetReference(
        asset_id="goblin_tribe.goblin_cutter",
        source_path="assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_cutter-face-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
