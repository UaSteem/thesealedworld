from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

MANGY_BITER = MemberVariantDTO(
    id="mangy_biter",
    base_id="mangy_biter",
    name="mangy_biter",
    description="A scarred, underfed wolf that darts in low and snaps at exposed limbs.",
    skills=("skill_fencing", "skill_dual_wield", "skill_light_armor"),
    tags=("mangy", "ambusher", "bleeder"),
    image=ImageAssetReference(
        **{
            "asset_id": "wolf_pack.mangy_biter",
            "source_path": "assets/monster_defaults/wolf_pack/png/mangy_biter-v1.png",
            "review_status": "review_ready",
            "display_mirror": False,
        }
    ),
)
