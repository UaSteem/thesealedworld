from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

STONE_SENTRY = MemberVariantDTO(
    text_id="golem.member.stone_sentry",
    id="stone_sentry",
    base_id="stone_sentry",
    skills=("skill_macing", "skill_shield_mastery", "skill_heavy_armor", "skill_parrying"),
    ability_ids=(),
    tags=("shield",),
)
