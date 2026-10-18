from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

STONE_CATCHER = MemberVariantDTO(
    text_id="golem.member.stone_catcher",
    id="stone_catcher",
    base_id="stone_catcher",
    skills=("skill_macing", "skill_fencing", "skill_dual_wield", "skill_heavy_armor"),
    ability_ids=("basic_expose_weakness",),
    tags=("paired",),
)
