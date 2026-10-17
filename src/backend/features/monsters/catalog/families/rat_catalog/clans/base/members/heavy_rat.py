from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

HEAVY_RAT = MemberVariantDTO(
    text_id="rat.member.heavy_rat",
    id="heavy_rat",
    base_id="heavy_rat",
    skills=("skill_fencing", "skill_shield_mastery", "skill_medium_armor", "skill_anatomy"),
    tags=("heavy", "strong"),
    ability_ids=(),
)
