from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

STALKER = MemberVariantDTO(
    text_id="wolf.member.stalker",
    id="stalker",
    base_id="stalker",
    skills=("skill_fencing", "skill_dual_wield", "skill_light_armor"),
    tags=("stealth", "hunter"),
)
