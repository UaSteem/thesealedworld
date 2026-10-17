from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

SCREECHER = MemberVariantDTO(
    text_id="rat.member.screecher",
    id="screecher",
    base_id="screecher",
    skills=("skill_archery", "skill_ranged_combat", "skill_medium_armor"),
    tags=("support", "alarm"),
    ability_ids=(),
)
