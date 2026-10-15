from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

FLANKER = MemberVariantDTO(
    id="flanker",
    base_id="flanker",
    name="flanker",
    description="A clever wolf that always tries to get behind its prey.",
    skills=("skill_fencing", "skill_dual_wield", "skill_medium_armor"),
    tags=("tactical", "fast"),
    image=ImageAssetReference(
        **{
            "asset_id": "wolf_pack.flanker",
            "source_path": "assets/monster_defaults/wolf_pack/png/flanker-v1.png",
            "review_status": "review_ready",
            "display_mirror": False,
        }
    ),
)
