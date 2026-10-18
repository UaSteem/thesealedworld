from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

STONE_THROWER = MemberVariantDTO(
    text_id="golem.member.stone_thrower",
    id="stone_thrower",
    base_id="stone_thrower",
    skills=("skill_archery", "skill_ranged_combat", "skill_heavy_armor", "skill_tactics"),
    ability_ids=(),
    tags=("ranged",),
)
