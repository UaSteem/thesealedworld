from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

RUNE_GUARDIAN = MemberVariantDTO(
    text_id="golem.member.rune_guardian",
    id="rune_guardian",
    base_id="rune_guardian",
    skills=("skill_macing", "skill_shield_mastery", "skill_heavy_armor", "skill_tactics"),
    ability_ids=("stone_skin",),
    tags=("shield",),
)
