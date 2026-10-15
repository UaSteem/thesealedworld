from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

BANDIT_WARLORD = MemberVariantDTO(
    id="bandit_warlord",
    base_id="bandit_warlord",
    name="bandit_warlord",
    description="A hard-eyed bandit marksman who keeps the line pinned while allies close in.",
    skills=("skill_archery", "skill_light_armor", "skill_ranged_combat", "skill_tactics", "skill_anatomy"),
    tags=("marksman", "commander", "ranged"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="bandit_gang.bandit_warlord",
        source_path="assets/monster_defaults/bandit_gang/png/bandit_warlord-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
