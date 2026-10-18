from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

RUNE_PUNISHER = MemberVariantDTO(
    text_id="golem.member.rune_punisher",
    id="rune_punisher",
    base_id="rune_punisher",
    skills=("skill_macing", "skill_two_handed", "skill_heavy_armor", "skill_anatomy"),
    ability_ids=("basic_break_stance",),
    tags=("heavy",),
)
