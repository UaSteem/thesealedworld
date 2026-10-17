from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

GOBLIN_SLINGER = MemberVariantDTO(
    text_id="goblin.member.goblin_slinger",
    id="goblin_slinger",
    base_id="goblin_slinger",
    skills=("skill_archery", "skill_ranged_combat", "skill_light_armor"),
    tags=("ranged", "archer", "fast", "quiver"),
    ability_ids=(),
)
