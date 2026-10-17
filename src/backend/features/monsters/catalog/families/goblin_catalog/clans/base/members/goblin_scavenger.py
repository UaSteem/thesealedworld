from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

GOBLIN_SCAVENGER = MemberVariantDTO(
    text_id="goblin.member.goblin_scavenger",
    id="goblin_scavenger",
    base_id="goblin_scavenger",
    skills=("skill_macing", "skill_shield_mastery", "skill_light_armor"),
    tags=("scavenger", "hoarder", "scrap", "buckler"),
    ability_ids=(),
)
