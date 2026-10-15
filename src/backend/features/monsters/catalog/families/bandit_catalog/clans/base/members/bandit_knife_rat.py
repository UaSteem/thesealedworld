from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

BANDIT_KNIFE_RAT = MemberVariantDTO(
    id="bandit_knife_rat",
    base_id="bandit_knife_rat",
    name="bandit_knife_rat",
    description="A thin alley fighter carrying a chipped dagger and too much confidence.",
    skills=("skill_fencing", "skill_dual_wield", "skill_light_armor"),
    tags=("dagger", "ambusher", "street"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="bandit_gang.bandit_knife_rat",
        source_path="assets/monster_defaults/bandit_gang/png/bandit_knife_rat-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
