from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

GOBLIN_SPEARMAN = MemberVariantDTO(
    text_id="goblin.member.goblin_spearman",
    id="goblin_spearman",
    base_id="goblin_spearman",
    skills=("skill_polearms", "skill_medium_armor", "skill_shield_mastery"),
    tags=("infantry", "shield"),
    ability_ids=(),
)
