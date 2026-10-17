from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

BROOD_ALPHA = MemberVariantDTO(
    text_id="rat.member.brood_alpha",
    id="brood_alpha",
    base_id="brood_alpha",
    skills=("skill_fencing", "skill_shield_mastery", "skill_heavy_armor", "skill_tactics", "skill_anatomy"),
    tags=("leader", "alpha", "tactician"),
    ability_ids=(),
)
