from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

MANGY_BITER = MemberVariantDTO(
    text_id="wolf.member.mangy_biter",
    id="mangy_biter",
    base_id="mangy_biter",
    skills=("skill_fencing", "skill_dual_wield", "skill_light_armor"),
    tags=("mangy", "ambusher", "bleeder"),
)
