from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

PACK_LEADER = MemberVariantDTO(
    text_id="wolf.member.pack_leader",
    id="pack_leader",
    base_id="pack_leader",
    skills=("skill_fencing", "skill_shield_mastery", "skill_medium_armor", "skill_tactics", "skill_anatomy"),
    tags=("leader", "support", "alpha"),
)
