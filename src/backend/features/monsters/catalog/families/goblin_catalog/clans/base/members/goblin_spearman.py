from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

GOBLIN_SPEARMAN = MemberVariantDTO(
    id="goblin_spearman",
    base_id="goblin_spearman",
    name="goblin_spearman",
    description="A disciplined goblin with a long spear and a crude wooden shield.",
    skills=("skill_polearms", "skill_medium_armor", "skill_shield_mastery"),
    tags=("infantry", "shield"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="goblin_tribe.goblin_spearman",
        source_path="assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_spearman-face-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
