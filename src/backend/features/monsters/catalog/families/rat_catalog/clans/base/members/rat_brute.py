from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

RAT_BRUTE = MemberVariantDTO(
    text_id="rat.member.rat_brute",
    id="rat_brute",
    base_id="rat_brute",
    skills=("skill_macing", "skill_two_handed", "skill_heavy_armor", "skill_tactics", "skill_anatomy"),
    tags=("brute", "strong"),
    ability_ids=(),
)
