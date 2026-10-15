from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

GOBLIN_TINKERER = MemberVariantDTO(
    id="goblin_tinkerer",
    base_id="goblin_tinkerer",
    name="goblin_tinkerer",
    description="A goblin with a leather cap and a belt full of tools. Throws caltrops and sets traps.",
    skills=("skill_fencing", "skill_shield_mastery", "skill_medium_armor", "skill_tactics"),
    tags=("engineer", "duelist", "scrap", "buckler"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="goblin_tribe.goblin_tinkerer",
        source_path="assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_tinkerer-face-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
