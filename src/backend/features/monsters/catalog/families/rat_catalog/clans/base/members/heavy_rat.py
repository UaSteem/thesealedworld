from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

HEAVY_RAT = MemberVariantDTO(
    id="heavy_rat",
    base_id="heavy_rat",
    name="Крыса-тяжеловес",
    description="Здоровая тяжёлая крыса с широким низким телом и короткими сильными лапами.",
    skills=("skill_fencing", "skill_shield_mastery", "skill_medium_armor", "skill_anatomy"),
    tags=("heavy", "strong"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="rat_swarm.heavy_rat",
        source_path="assets/monster_defaults/rat_swarm/png/heavy_rat-v2.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
