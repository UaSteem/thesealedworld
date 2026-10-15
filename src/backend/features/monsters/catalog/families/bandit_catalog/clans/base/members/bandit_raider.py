from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

BANDIT_RAIDER = MemberVariantDTO(
    id="bandit_raider",
    base_id="bandit_raider",
    name="bandit_raider",
    description="A hard-handed raider with a mace and shield, used to breaking doors and skulls.",
    skills=("skill_macing", "skill_medium_armor", "skill_shield_mastery"),
    tags=("raider", "shield", "bruiser"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="bandit_gang.bandit_raider",
        source_path="assets/monster_defaults/bandit_gang/png/bandit_raider-v1.png",
        review_status="accepted",
        display_mirror=True,
    ),
)
