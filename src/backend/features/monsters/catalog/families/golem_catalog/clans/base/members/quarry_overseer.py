from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

QUARRY_OVERSEER = MemberVariantDTO(
    text_id="golem.member.quarry_overseer",
    id="quarry_overseer",
    base_id="quarry_overseer",
    skills=("skill_macing", "skill_fencing", "skill_dual_wield", "skill_heavy_armor", "skill_tactics"),
    ability_ids=("basic_break_stance", "stone_skin"),
    tags=("paired",),
)
