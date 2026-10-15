from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

DIRE_WOLF = MemberVariantDTO(
    id="dire_wolf",
    base_id="dire_wolf",
    name="dire_wolf",
    description="A massive, prehistoric wolf. Its fur is thick and its eyes burn with hunger.",
    skills=("skill_fencing", "skill_shield_mastery", "skill_heavy_armor", "skill_anatomy"),
    tags=("dire", "heavy", "brute"),
    image=ImageAssetReference(
        **{
            "asset_id": "wolf_pack.dire_wolf",
            "source_path": "assets/monster_defaults/wolf_pack/png/dire_wolf-v1.png",
            "review_status": "review_ready",
            "display_mirror": False,
        }
    ),
)
