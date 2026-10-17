from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

GOBLIN_SPARKPICK = MemberVariantDTO(
    text_id="goblin.member.goblin_sparkpick",
    id="goblin_sparkpick",
    base_id="goblin_sparkpick",
    skills=("skill_macing", "skill_shield_mastery", "skill_light_armor"),
    tags=("scrap", "ether", "reckless", "buckler"),
    ability_ids=(),
)
