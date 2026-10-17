from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

TUNNEL_RAT = MemberVariantDTO(
    text_id="rat.member.tunnel_rat",
    id="tunnel_rat",
    base_id="tunnel_rat",
    skills=("skill_fencing", "skill_dual_wield", "skill_medium_armor"),
    tags=("digger", "stealth"),
    ability_ids=(),
)
