from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

GOBLIN_BOMBER = MemberVariantDTO(
    id="goblin_bomber",
    base_id="goblin_bomber",
    name="goblin_bomber",
    description="A goblin with a manic grin and a sack of crude explosives.",
    skills=("skill_archery", "skill_medium_armor", "skill_ranged_combat", "skill_tactics"),
    tags=("bomber", "explosives", "reckless", "archer", "fire_arrows"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="goblin_tribe.goblin_bomber",
        source_path="assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_bomber-face-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
