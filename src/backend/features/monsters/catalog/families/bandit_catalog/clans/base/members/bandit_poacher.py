from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

BANDIT_POACHER = MemberVariantDTO(
    id="bandit_poacher",
    base_id="bandit_poacher",
    name="bandit_poacher",
    description="A former hunter, now an outlaw. Uses a simple short bow and wears leather scraps.",
    skills=("skill_archery", "skill_light_armor", "skill_ranged_combat"),
    tags=(),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="bandit_gang.bandit_poacher",
        source_path="assets/monster_defaults/bandit_gang/png/bandit_poacher-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
