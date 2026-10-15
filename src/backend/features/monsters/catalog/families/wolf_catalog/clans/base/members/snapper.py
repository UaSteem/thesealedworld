from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

SNAPPER = MemberVariantDTO(
    id="snapper",
    base_id="snapper",
    name="snapper",
    description="A wolf with powerful jaws, focused on finishing off wounded prey.",
    skills=("skill_fencing", "skill_dual_wield", "skill_light_armor"),
    tags=("executioner", "strong_jaw"),
    image=ImageAssetReference(
        **{
            "asset_id": "wolf_pack.snapper",
            "source_path": "assets/monster_defaults/wolf_pack/png/snapper-v1.png",
            "review_status": "review_ready",
            "display_mirror": False,
        }
    ),
)
