from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

CUB = MemberVariantDTO(
    text_id="wolf.member.cub",
    id="cub",
    base_id="cub",
    skills=("skill_fencing", "skill_light_armor"),
    tags=("young", "weak"),
)
