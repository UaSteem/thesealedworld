from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

BANDIT_POACHER = MemberVariantDTO(
    text_id="bandit.member.bandit_poacher",
    id="bandit_poacher",
    base_id="bandit_poacher",
    skills=("skill_archery", "skill_light_armor", "skill_ranged_combat"),
    tags=(),
    ability_ids=(),
)
