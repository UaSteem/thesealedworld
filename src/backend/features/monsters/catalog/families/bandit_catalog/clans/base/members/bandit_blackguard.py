from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

BANDIT_BLACKGUARD = MemberVariantDTO(
    text_id="bandit.member.bandit_blackguard",
    id="bandit_blackguard",
    base_id="bandit_blackguard",
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
)
