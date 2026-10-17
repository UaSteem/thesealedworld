from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

SCRAP_KING = MemberVariantDTO(
    text_id="goblin.member.scrap_king",
    id="scrap_king",
    base_id="scrap_king",
    skills=("skill_macing", "skill_heavy_armor", "skill_two_handed", "skill_tactics", "skill_anatomy"),
    tags=("king", "heavy_armor", "engineer", "two_handed", "scrap"),
    ability_ids=(),
)
