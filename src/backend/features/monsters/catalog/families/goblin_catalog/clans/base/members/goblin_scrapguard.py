from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

GOBLIN_SCRAPGUARD = MemberVariantDTO(
    text_id="goblin.member.goblin_scrapguard",
    id="goblin_scrapguard",
    base_id="goblin_scrapguard",
    skills=("skill_macing", "skill_medium_armor", "skill_shield_mastery"),
    tags=("shield", "defender", "scrap"),
    ability_ids=(),
)
