from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

IRONFANG = MemberVariantDTO(
    text_id="rat.member.ironfang",
    id="ironfang",
    base_id="ironfang",
    skills=("skill_macing", "skill_two_handed", "skill_heavy_armor", "skill_anatomy"),
    tags=("fangs", "fighter"),
    ability_ids=(),
)
