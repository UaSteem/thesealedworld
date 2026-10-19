from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

SEWER_RAT = MemberVariantDTO(
    text_id="rat.member.sewer_rat",
    id="sewer_rat",
    base_id="sewer_rat",
    skills=("skill_fencing", "skill_light_armor"),
    tags=("young", "weak"),
    ability_ids=(),
)
