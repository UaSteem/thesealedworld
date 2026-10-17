from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

RUNNER = MemberVariantDTO(
    text_id="wolf.member.runner",
    id="runner",
    base_id="runner",
    skills=("skill_fencing", "skill_dual_wield", "skill_light_armor"),
    tags=("fast", "scout"),
)
