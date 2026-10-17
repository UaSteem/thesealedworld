from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

BANDIT_CUTTHROAT = MemberVariantDTO(
    text_id="bandit.member.bandit_cutthroat",
    id="bandit_cutthroat",
    base_id="bandit_cutthroat",
    skills=(
        "skill_fencing",
        "skill_light_armor",
        "skill_dual_wield",
        "skill_tactics",
        "skill_parrying",
        "skill_anatomy",
    ),
    tags=(),
    ability_ids=(),
)
