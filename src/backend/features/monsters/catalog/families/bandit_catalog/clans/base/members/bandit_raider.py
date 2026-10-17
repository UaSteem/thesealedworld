from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

BANDIT_RAIDER = MemberVariantDTO(
    text_id="bandit.member.bandit_raider",
    id="bandit_raider",
    base_id="bandit_raider",
    skills=("skill_macing", "skill_medium_armor", "skill_shield_mastery"),
    tags=("raider", "shield", "bruiser"),
    ability_ids=(),
)
