from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

GOBLIN_TRAPMASTER = MemberVariantDTO(
    text_id="goblin.member.goblin_trapmaster",
    id="goblin_trapmaster",
    base_id="goblin_trapmaster",
    skills=("skill_fencing", "skill_dual_wield", "skill_medium_armor", "skill_tactics", "skill_anatomy"),
    tags=("trapper", "engineer", "controller", "dual_wield", "precision"),
    ability_ids=(),
)
