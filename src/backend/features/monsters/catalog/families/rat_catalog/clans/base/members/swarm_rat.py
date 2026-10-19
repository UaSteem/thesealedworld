from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

SWARM_RAT = MemberVariantDTO(
    text_id="rat.member.swarm_rat",
    id="swarm_rat",
    base_id="swarm_rat",
    skills=("skill_fencing", "skill_light_armor"),
    tags=("young", "swarm"),
    ability_ids=(),
)
