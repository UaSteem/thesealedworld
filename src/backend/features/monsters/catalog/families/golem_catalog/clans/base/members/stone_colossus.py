from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

STONE_COLOSSUS = MemberVariantDTO(
    text_id="golem.member.stone_colossus",
    id="stone_colossus",
    base_id="stone_colossus",
    skills=("skill_macing", "skill_two_handed", "skill_heavy_armor", "skill_anatomy"),
    ability_ids=("basic_cleave_gift", "stone_skin"),
    tags=("heavy",),
)
