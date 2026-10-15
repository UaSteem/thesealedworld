from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

PACK_HUNTMASTER = MemberVariantDTO(
    id="pack_huntmaster",
    base_id="pack_huntmaster",
    name="Вожак-загонщик",
    description="A cunning wolf pack huntmaster who coordinates pursuit and cuts off escaping prey.",
    skills=("skill_fencing", "skill_shield_mastery", "skill_heavy_armor", "skill_tactics", "skill_anatomy"),
    tags=("cunning", "coordinator", "hunter"),
    image=ImageAssetReference(
        **{
            "asset_id": "wolf_pack.pack_huntmaster",
            "source_path": "assets/monster_defaults/wolf_pack/png/pack_huntmaster-v1.png",
            "review_status": "review_ready",
            "display_mirror": False,
        }
    ),
)
