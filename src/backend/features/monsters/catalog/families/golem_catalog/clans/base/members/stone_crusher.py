from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

STONE_CRUSHER = MemberVariantDTO(
    text_id="golem.member.stone_crusher",
    id="stone_crusher",
    base_id="stone_crusher",
    skills=("skill_macing", "skill_two_handed", "skill_heavy_armor", "skill_anatomy"),
    ability_ids=("basic_break_stance",),
    tags=("heavy",),
)
