from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

BANDIT_CAPTAIN = MemberVariantDTO(
    text_id="bandit.member.bandit_captain",
    id="bandit_captain",
    base_id="bandit_captain",
    skills=("skill_swords", "skill_medium_armor", "skill_shield_mastery", "skill_tactics", "skill_parrying"),
    tags=(),
    ability_ids=(),
)
