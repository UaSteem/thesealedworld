from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

BANDIT_HEDGE_WIZARD = MemberVariantDTO(
    text_id="bandit.member.bandit_hedge_wizard",
    id="bandit_hedge_wizard",
    base_id="bandit_hedge_wizard",
    skills=("skill_polearms", "skill_light_armor", "skill_two_handed"),
    tags=(),
    ability_ids=(),
)
