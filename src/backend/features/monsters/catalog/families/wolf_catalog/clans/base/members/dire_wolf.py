from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

DIRE_WOLF = MemberVariantDTO(
    text_id="wolf.member.dire_wolf",
    id="dire_wolf",
    base_id="dire_wolf",
    skills=("skill_fencing", "skill_shield_mastery", "skill_heavy_armor", "skill_anatomy"),
    tags=("dire", "heavy", "brute"),
)
