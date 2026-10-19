from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

SNAPPER = MemberVariantDTO(
    text_id="wolf.member.snapper",
    id="snapper",
    base_id="snapper",
    skills=("skill_fencing", "skill_light_armor"),
    tags=("executioner", "strong_jaw"),
)
