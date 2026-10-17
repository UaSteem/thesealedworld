from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

GOBLIN_CHIEF = MemberVariantDTO(
    text_id="goblin.member.goblin_chief",
    id="goblin_chief",
    base_id="goblin_chief",
    skills=("skill_macing", "skill_shield_mastery", "skill_heavy_armor", "skill_tactics", "skill_anatomy"),
    tags=("leader", "commander", "heavy_armor", "shield"),
    ability_ids=(),
)
