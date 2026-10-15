from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

GOBLIN_CHIEF = MemberVariantDTO(
    id="goblin_chief",
    base_id="goblin_chief",
    name="goblin_chief",
    description="A larger, smarter goblin wearing a crude crown and better armor. Shouts commands.",
    skills=("skill_macing", "skill_shield_mastery", "skill_heavy_armor", "skill_tactics", "skill_anatomy"),
    tags=("leader", "commander", "heavy_armor", "shield"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="goblin_tribe.goblin_chief",
        source_path="assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_chief-face-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
