from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

GOBLIN_SNEAK = MemberVariantDTO(
    id="goblin_sneak",
    base_id="goblin_sneak",
    name="goblin_sneak",
    description="A small goblin with a hooded cloak and a pair of sharp daggers, moves silently.",
    skills=("skill_fencing", "skill_dual_wield", "skill_light_armor"),
    tags=("stealth", "assassin", "dual_wield", "knife"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="goblin_tribe.goblin_sneak",
        source_path="assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_sneak-face-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
