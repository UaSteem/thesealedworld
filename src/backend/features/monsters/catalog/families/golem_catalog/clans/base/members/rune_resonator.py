from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

RUNE_RESONATOR = MemberVariantDTO(
    text_id="golem.member.rune_resonator",
    id="rune_resonator",
    base_id="rune_resonator",
    skills=("skill_macing", "skill_fencing", "skill_dual_wield", "skill_heavy_armor", "skill_tactics"),
    ability_ids=("stone_skin",),
    tags=("paired",),
)
