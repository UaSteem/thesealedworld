from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

STONE_RAM = MemberVariantDTO(
    text_id="golem.member.stone_ram",
    id="stone_ram",
    base_id="stone_ram",
    skills=("skill_macing", "skill_two_handed", "skill_heavy_armor", "skill_anatomy"),
    ability_ids=(),
    tags=("heavy",),
)
