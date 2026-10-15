from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

RAT_KING = MemberVariantDTO(
    id="rat_king",
    base_id="rat_king",
    name="Крысиный король",
    description="Живой клубок крыс с переплетёнными хвостами; из него выбираются новые крысы, присоединяясь к стае.",
    skills=("skill_archery", "skill_ranged_combat", "skill_heavy_armor", "skill_tactics", "skill_anatomy"),
    tags=("king", "hive_mind", "summoner"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="rat_swarm.rat_king",
        source_path="assets/monster_defaults/rat_swarm/png/rat_king-v2.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
