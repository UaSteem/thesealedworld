from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

STONE_WORKER = MemberVariantDTO(
    text_id="golem.member.stone_worker",
    id="stone_worker",
    base_id="stone_worker",
    skills=("skill_macing", "skill_fencing", "skill_dual_wield", "skill_heavy_armor"),
    ability_ids=(),
    tags=("paired",),
)
