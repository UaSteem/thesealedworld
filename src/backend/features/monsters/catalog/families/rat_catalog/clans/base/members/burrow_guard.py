from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

BURROW_GUARD = MemberVariantDTO(
    id="burrow_guard",
    base_id="burrow_guard",
    name="Страж норы",
    description="Коренастый страж норы с мощными плечами, старым шрамом и простой серьгой в ухе.",
    skills=("skill_archery", "skill_ranged_combat", "skill_medium_armor", "skill_anatomy"),
    tags=("guardian", "defender"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="rat_swarm.burrow_guard",
        source_path="assets/monster_defaults/rat_swarm/png/burrow_guard-v2.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
