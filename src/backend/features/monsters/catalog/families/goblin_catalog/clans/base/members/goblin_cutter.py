from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

GOBLIN_CUTTER = MemberVariantDTO(
    text_id="goblin.member.goblin_cutter",
    id="goblin_cutter",
    base_id="goblin_cutter",
    skills=("skill_fencing", "skill_dual_wield", "skill_light_armor"),
    tags=("knife", "bleeder", "ambusher", "dual_wield"),
    ability_ids=(),
)
