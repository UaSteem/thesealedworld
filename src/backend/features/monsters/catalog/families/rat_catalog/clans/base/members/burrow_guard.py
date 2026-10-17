from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

BURROW_GUARD = MemberVariantDTO(
    text_id="rat.member.burrow_guard",
    id="burrow_guard",
    base_id="burrow_guard",
    skills=("skill_archery", "skill_ranged_combat", "skill_medium_armor", "skill_anatomy"),
    tags=("guardian", "defender"),
    ability_ids=(),
)
