from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

BANDIT_THUG = MemberVariantDTO(
    text_id="bandit.member.bandit_thug",
    id="bandit_thug",
    base_id="bandit_thug",
    skills=("skill_macing", "skill_medium_armor"),
    tags=(),
    ability_ids=(),
)
