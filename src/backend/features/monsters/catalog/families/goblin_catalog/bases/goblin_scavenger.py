from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import (
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

GOBLIN_SCAVENGER = MemberBaseDTO(
    id="goblin_scavenger",
    role="minion",
    assembly_cost=7,
    stats=BaseStatsDTO(
        strength=9,
        agility=11,
        endurance=9,
        intellect=8,
        memory=6,
        mental=6,
        perception=10,
        projection=5,
        prediction=6,
    ),
    equipment_set_id="scavenger",
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=20,
    default_image=ImageAssetReference(
        asset_id="goblin_tribe.goblin_scavenger",
        source_path="assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_scavenger-face-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
