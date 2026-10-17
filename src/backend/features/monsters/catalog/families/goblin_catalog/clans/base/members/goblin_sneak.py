from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

GOBLIN_SNEAK = MemberVariantDTO(
    text_id="goblin.member.goblin_sneak",
    id="goblin_sneak",
    base_id="goblin_sneak",
    skills=("skill_fencing", "skill_dual_wield", "skill_light_armor"),
    tags=("stealth", "assassin", "dual_wield", "knife"),
    ability_ids=(),
)
