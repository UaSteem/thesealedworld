from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

BANDIT_BLACKGUARD = MemberVariantDTO(
    id="bandit_blackguard",
    base_id="bandit_blackguard",
    name="bandit_blackguard",
    description="A disciplined killer in stolen armor, carrying a heavy mace and a tower shield.",
    skills=(
        "skill_macing",
        "skill_heavy_armor",
        "skill_shield_mastery",
        "skill_tactics",
        "skill_parrying",
        "skill_anatomy",
    ),
    tags=("blackguard", "heavy", "guard"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="bandit_gang.bandit_blackguard",
        source_path="assets/monster_defaults/bandit_gang/png/bandit_blackguard-v1.png",
        review_status="accepted",
        display_mirror=True,
    ),
)
