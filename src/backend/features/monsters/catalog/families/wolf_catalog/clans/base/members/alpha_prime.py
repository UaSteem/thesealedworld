from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

ALPHA_PRIME = MemberVariantDTO(
    id="alpha_prime",
    base_id="alpha_prime",
    name="Фенрир",
    description="The apex predator. A wolf of perfect form and terrifying power.",
    skills=("skill_fencing", "skill_shield_mastery", "skill_heavy_armor", "skill_tactics", "skill_anatomy"),
    tags=("alpha", "prime", "legendary"),
    image=ImageAssetReference(
        **{
            "asset_id": "wolf_pack.fenrir",
            "source_path": "assets/monster_defaults/wolf_pack/png/fenrir-v1.png",
            "review_status": "accepted",
            "display_mirror": False,
        }
    ),
)
