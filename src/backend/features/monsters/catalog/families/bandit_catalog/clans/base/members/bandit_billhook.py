from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

BANDIT_BILLHOOK = MemberVariantDTO(
    id="bandit_billhook",
    base_id="bandit_billhook",
    name="bandit_billhook",
    description="A ruined-road enforcer with a hooked polearm for dragging victims off balance.",
    skills=("skill_polearms", "skill_medium_armor"),
    tags=("polearm", "disabler", "roadside"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="bandit_gang.bandit_billhook",
        source_path="assets/monster_defaults/bandit_gang/png/bandit_billhook-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
