from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

PACK_RAT = MemberVariantDTO(
    text_id="rat.member.pack_rat",
    id="pack_rat",
    base_id="pack_rat",
    skills=("skill_fencing", "skill_shield_mastery", "skill_light_armor"),
    tags=("pack_tactics", "flanker"),
    ability_ids=(),
)
