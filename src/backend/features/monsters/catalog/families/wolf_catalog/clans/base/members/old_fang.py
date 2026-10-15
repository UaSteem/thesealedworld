from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

OLD_FANG = MemberVariantDTO(
    id="old_fang",
    base_id="old_fang",
    name="old_fang",
    description="An old, scarred wolf. Missing an ear, but moves with deadly efficiency.",
    skills=("skill_fencing", "skill_dual_wield", "skill_medium_armor", "skill_tactics", "skill_anatomy"),
    tags=("veteran", "cunning"),
    image=ImageAssetReference(
        **{
            "asset_id": "wolf_pack.old_fang",
            "source_path": "assets/monster_defaults/wolf_pack/png/old_fang-v1.png",
            "review_status": "review_ready",
            "display_mirror": False,
        }
    ),
)
