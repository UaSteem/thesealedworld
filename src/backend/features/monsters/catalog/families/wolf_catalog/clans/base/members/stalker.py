from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

STALKER = MemberVariantDTO(
    id="stalker",
    base_id="stalker",
    name="stalker",
    description="A wolf that moves low to the ground, blending with the terrain.",
    skills=("skill_fencing", "skill_dual_wield", "skill_light_armor"),
    tags=("stealth", "hunter"),
    image=ImageAssetReference(
        **{
            "asset_id": "wolf_pack.stalker",
            "source_path": "assets/monster_defaults/wolf_pack/png/stalker-v1.png",
            "review_status": "review_ready",
            "display_mirror": False,
        }
    ),
)
