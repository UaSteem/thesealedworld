from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

BANDIT_THUG = MemberVariantDTO(
    id="bandit_thug",
    base_id="bandit_thug",
    name="bandit_thug",
    description="A rough human bandit armed with a crude axe and a wooden shield.",
    skills=("skill_macing", "skill_medium_armor"),
    tags=(),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="bandit_gang.bandit_thug",
        source_path="assets/monster_defaults/bandit_gang/png/bandit_thug-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
