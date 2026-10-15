from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

BANDIT_CUTTHROAT = MemberVariantDTO(
    id="bandit_cutthroat",
    base_id="bandit_cutthroat",
    name="bandit_cutthroat",
    description="A quick and ruthless knife-boss with two daggers, likely a former city rogue.",
    skills=(
        "skill_fencing",
        "skill_light_armor",
        "skill_dual_wield",
        "skill_tactics",
        "skill_parrying",
        "skill_anatomy",
    ),
    tags=(),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="bandit_gang.bandit_cutthroat",
        source_path="assets/monster_defaults/bandit_gang/png/bandit_cutthroat-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
