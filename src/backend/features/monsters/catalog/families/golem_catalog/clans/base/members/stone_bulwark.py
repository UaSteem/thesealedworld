from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

STONE_BULWARK = MemberVariantDTO(
    text_id="golem.member.stone_bulwark",
    id="stone_bulwark",
    base_id="stone_bulwark",
    skills=("skill_macing", "skill_shield_mastery", "skill_heavy_armor", "skill_parrying"),
    ability_ids=(),
    tags=("shield",),
)
