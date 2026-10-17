from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

BANDIT_WARLORD = MemberVariantDTO(
    text_id="bandit.member.bandit_warlord",
    id="bandit_warlord",
    base_id="bandit_warlord",
    skills=("skill_archery", "skill_light_armor", "skill_ranged_combat", "skill_tactics", "skill_anatomy"),
    tags=("marksman", "commander", "ranged"),
    ability_ids=(),
)
