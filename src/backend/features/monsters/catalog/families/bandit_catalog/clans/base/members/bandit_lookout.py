from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

BANDIT_LOOKOUT = MemberVariantDTO(
    text_id="bandit.member.bandit_lookout",
    id="bandit_lookout",
    base_id="bandit_lookout",
    skills=("skill_polearms", "skill_light_armor"),
    tags=("watcher", "spear", "scout"),
    ability_ids=(),
)
