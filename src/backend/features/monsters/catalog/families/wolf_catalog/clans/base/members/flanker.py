from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

FLANKER = MemberVariantDTO(
    text_id="wolf.member.flanker",
    id="flanker",
    base_id="flanker",
    skills=("skill_fencing", "skill_medium_armor"),
    tags=("tactical", "fast"),
)
