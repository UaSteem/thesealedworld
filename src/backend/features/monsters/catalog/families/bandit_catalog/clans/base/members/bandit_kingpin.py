from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

BANDIT_KINGPIN = MemberVariantDTO(
    id="bandit_kingpin",
    base_id="bandit_kingpin",
    name="bandit_kingpin",
    description="A road executioner who favors a heavy two-handed weapon and a direct charge.",
    skills=("skill_macing", "skill_heavy_armor", "skill_two_handed", "skill_tactics", "skill_anatomy"),
    tags=(),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="bandit_gang.bandit_kingpin",
        source_path="assets/monster_defaults/bandit_gang/png/bandit_kingpin-v1.png",
        review_status="accepted",
        display_mirror=True,
    ),
)
