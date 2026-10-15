from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

BANDIT_CAPTAIN = MemberVariantDTO(
    id="bandit_captain",
    base_id="bandit_captain",
    name="bandit_captain",
    description="The leader of this small gang, a hardened survivor with a sword, shield, and reinforced mail.",
    skills=("skill_swords", "skill_medium_armor", "skill_shield_mastery", "skill_tactics", "skill_parrying"),
    tags=(),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="bandit_gang.bandit_captain",
        source_path="assets/monster_defaults/bandit_gang/png/bandit_captain-v1.png",
        review_status="accepted",
        display_mirror=True,
    ),
)
