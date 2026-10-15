from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

GOBLIN_SPARKPICK = MemberVariantDTO(
    id="goblin_sparkpick",
    base_id="goblin_sparkpick",
    name="goblin_sparkpick",
    description="A scavenger carrying a bent tool that spits unstable ether sparks when swung.",
    skills=("skill_macing", "skill_shield_mastery", "skill_light_armor"),
    tags=("scrap", "ether", "reckless", "buckler"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="goblin_tribe.goblin_sparkpick",
        source_path="assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_sparkpick-face-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
