from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

OLD_FANG = MemberVariantDTO(
    text_id="wolf.member.old_fang",
    id="old_fang",
    base_id="old_fang",
    skills=("skill_fencing", "skill_dual_wield", "skill_medium_armor", "skill_tactics", "skill_anatomy"),
    tags=("veteran", "cunning"),
)
