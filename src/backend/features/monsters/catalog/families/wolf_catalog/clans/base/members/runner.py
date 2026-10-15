from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

RUNNER = MemberVariantDTO(
    id="runner",
    base_id="runner",
    name="runner",
    description="A lean wolf built for speed. Scouts ahead of the pack.",
    skills=("skill_fencing", "skill_dual_wield", "skill_light_armor"),
    tags=("fast", "scout"),
    image=ImageAssetReference(
        **{
            "asset_id": "wolf_pack.runner",
            "source_path": "assets/monster_defaults/wolf_pack/png/runner-v1.png",
            "review_status": "review_ready",
            "display_mirror": False,
        }
    ),
)
