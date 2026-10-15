from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

BANDIT_LOOKOUT = MemberVariantDTO(
    id="bandit_lookout",
    base_id="bandit_lookout",
    name="bandit_lookout",
    description="A nervous lookout with a spear and patched leather, watching ruined streets for prey.",
    skills=("skill_polearms", "skill_light_armor"),
    tags=("watcher", "spear", "scout"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="bandit_gang.bandit_lookout",
        source_path="assets/monster_defaults/bandit_gang/png/bandit_lookout-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
