from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

RAT_KING = MemberVariantDTO(
    text_id="rat.member.rat_king",
    id="rat_king",
    base_id="rat_king",
    skills=("skill_archery", "skill_ranged_combat", "skill_heavy_armor", "skill_tactics", "skill_anatomy"),
    tags=("king", "hive_mind", "summoner"),
    ability_ids=(),
)
