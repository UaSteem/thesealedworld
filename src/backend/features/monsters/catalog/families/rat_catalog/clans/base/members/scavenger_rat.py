from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

SCAVENGER_RAT = MemberVariantDTO(
    text_id="rat.member.scavenger_rat",
    id="scavenger_rat",
    base_id="scavenger_rat",
    skills=("skill_fencing", "skill_light_armor"),
    tags=("young", "scavenger", "hoarder"),
    ability_ids=(),
)
