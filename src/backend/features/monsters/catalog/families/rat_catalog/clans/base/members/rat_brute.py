from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

RAT_BRUTE = MemberVariantDTO(
    id="rat_brute",
    base_id="rat_brute",
    name="Крыса-громила",
    description="Огромная крыса с высокими плечами, мощными передними лапами и боевыми шрамами.",
    skills=("skill_macing", "skill_two_handed", "skill_heavy_armor", "skill_tactics", "skill_anatomy"),
    tags=("brute", "strong"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="rat_swarm.rat_brute",
        source_path="assets/monster_defaults/rat_swarm/png/rat_brute-v2.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
