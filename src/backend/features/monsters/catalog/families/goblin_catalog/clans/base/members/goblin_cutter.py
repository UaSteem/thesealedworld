from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

GOBLIN_CUTTER = MemberVariantDTO(
    id="goblin_cutter",
    base_id="goblin_cutter",
    name="goblin_cutter",
    description="A mean little goblin with a chipped knife and a habit of aiming for tendons.",
    skills=("skill_fencing", "skill_dual_wield", "skill_light_armor"),
    tags=("knife", "bleeder", "ambusher", "dual_wield"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="goblin_tribe.goblin_cutter",
        source_path="assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_cutter-face-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
