from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

ALPHA_PRIME = MemberVariantDTO(
    text_id="wolf.member.alpha_prime",
    id="alpha_prime",
    base_id="alpha_prime",
    skills=("skill_fencing", "skill_shield_mastery", "skill_heavy_armor", "skill_tactics", "skill_anatomy"),
    tags=("alpha", "prime", "legendary"),
)
