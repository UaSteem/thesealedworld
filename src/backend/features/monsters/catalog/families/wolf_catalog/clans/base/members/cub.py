from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

CUB = MemberVariantDTO(
    id="cub",
    base_id="cub",
    name="cub",
    description="A young wolf, inexperienced but eager. Soft fur and sharp little teeth.",
    skills=("skill_fencing", "skill_dual_wield", "skill_light_armor"),
    tags=("young", "weak"),
    image=ImageAssetReference(
        **{
            "asset_id": "wolf_pack.cub",
            "source_path": "assets/monster_defaults/wolf_pack/png/cub-v1.png",
            "review_status": "accepted",
            "display_mirror": False,
        }
    ),
)
