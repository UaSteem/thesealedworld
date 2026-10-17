from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

BANDIT_KNIFE_RAT = MemberVariantDTO(
    text_id="bandit.member.bandit_knife_rat",
    id="bandit_knife_rat",
    base_id="bandit_knife_rat",
    skills=("skill_fencing", "skill_dual_wield", "skill_light_armor"),
    tags=("dagger", "ambusher", "street"),
    ability_ids=(),
)
