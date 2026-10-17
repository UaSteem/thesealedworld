from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

GOBLIN_TINKERER = MemberVariantDTO(
    text_id="goblin.member.goblin_tinkerer",
    id="goblin_tinkerer",
    base_id="goblin_tinkerer",
    skills=("skill_fencing", "skill_shield_mastery", "skill_medium_armor", "skill_tactics"),
    tags=("engineer", "duelist", "scrap", "buckler"),
    ability_ids=(),
)
