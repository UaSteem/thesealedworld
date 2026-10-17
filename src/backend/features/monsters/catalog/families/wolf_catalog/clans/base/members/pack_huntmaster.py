from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

PACK_HUNTMASTER = MemberVariantDTO(
    text_id="wolf.member.pack_huntmaster",
    id="pack_huntmaster",
    base_id="pack_huntmaster",
    skills=("skill_fencing", "skill_shield_mastery", "skill_heavy_armor", "skill_tactics", "skill_anatomy"),
    tags=("cunning", "coordinator", "hunter"),
)
