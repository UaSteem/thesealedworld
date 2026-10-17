from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import (
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

GOBLIN_CHIEF = MemberBaseDTO(
    id="goblin_chief",
    role="boss",
    stats=BaseStatsDTO(
        strength=21,
        agility=20,
        endurance=22,
        intellect=16,
        memory=15,
        mental=19,
        perception=18,
        projection=17,
        prediction=14,
    ),
    equipment_set_id="chief",
    tiers=TierAvailabilityDTO(min_tier=0, max_tier=5),
    spawn_weight=600,
    default_image=ImageAssetReference(
        asset_id="goblin_tribe.goblin_chief",
        source_path="assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_chief-face-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
