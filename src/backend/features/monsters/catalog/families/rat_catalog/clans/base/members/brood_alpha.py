from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

BROOD_ALPHA = MemberVariantDTO(
    id="brood_alpha",
    base_id="brood_alpha",
    name="Вожак выводка",
    description="Опытный умный вожак выводка с надорванным ухом, направляющий остальных крыс.",
    skills=("skill_fencing", "skill_shield_mastery", "skill_heavy_armor", "skill_tactics", "skill_anatomy"),
    tags=("leader", "alpha", "tactician"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="rat_swarm.brood_alpha",
        source_path="assets/monster_defaults/rat_swarm/png/brood_alpha-v2.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
