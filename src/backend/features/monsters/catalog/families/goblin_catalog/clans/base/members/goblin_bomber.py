from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

GOBLIN_BOMBER = MemberVariantDTO(
    text_id="goblin.member.goblin_bomber",
    id="goblin_bomber",
    base_id="goblin_bomber",
    skills=("skill_archery", "skill_medium_armor", "skill_ranged_combat", "skill_tactics"),
    tags=("bomber", "explosives", "reckless", "archer", "fire_arrows"),
    ability_ids=(),
)
