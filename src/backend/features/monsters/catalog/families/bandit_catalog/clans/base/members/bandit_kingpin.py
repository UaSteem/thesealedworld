from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

BANDIT_KINGPIN = MemberVariantDTO(
    text_id="bandit.member.bandit_kingpin",
    id="bandit_kingpin",
    base_id="bandit_kingpin",
    skills=("skill_macing", "skill_heavy_armor", "skill_two_handed", "skill_tactics", "skill_anatomy"),
    tags=(),
    ability_ids=(),
)
