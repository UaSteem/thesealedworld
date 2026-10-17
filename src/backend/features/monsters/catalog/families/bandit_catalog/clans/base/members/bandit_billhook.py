from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

BANDIT_BILLHOOK = MemberVariantDTO(
    text_id="bandit.member.bandit_billhook",
    id="bandit_billhook",
    base_id="bandit_billhook",
    skills=("skill_polearms", "skill_medium_armor"),
    tags=("polearm", "disabler", "roadside"),
    ability_ids=(),
)
