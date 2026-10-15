from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

GOBLIN_SLINGER = MemberVariantDTO(
    id="goblin_slinger",
    base_id="goblin_slinger",
    name="goblin_slinger",
    description="A fast goblin with a short bow and a simple quiver of training arrows.",
    skills=("skill_archery", "skill_ranged_combat", "skill_light_armor"),
    tags=("ranged", "archer", "fast", "quiver"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="goblin_tribe.goblin_slinger",
        source_path="assets/monster_defaults/goblin_tribe/svg/goblin_slinger.svg",
        review_status="accepted",
        display_mirror=False,
    ),
)
