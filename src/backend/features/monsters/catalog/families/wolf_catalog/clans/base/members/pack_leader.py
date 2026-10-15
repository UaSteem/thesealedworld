from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

PACK_LEADER = MemberVariantDTO(
    id="pack_leader",
    base_id="pack_leader",
    name="pack_leader",
    description="A large wolf with a confident stance. Howls to coordinate the pack.",
    skills=("skill_fencing", "skill_shield_mastery", "skill_medium_armor", "skill_tactics", "skill_anatomy"),
    tags=("leader", "support", "alpha"),
    image=ImageAssetReference(
        **{
            "asset_id": "wolf_pack.pack_leader",
            "source_path": "assets/monster_defaults/wolf_pack/png/pack_leader-v1.png",
            "review_status": "review_ready",
            "display_mirror": False,
        }
    ),
)
