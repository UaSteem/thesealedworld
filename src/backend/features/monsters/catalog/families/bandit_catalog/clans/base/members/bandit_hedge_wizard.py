from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

BANDIT_HEDGE_WIZARD = MemberVariantDTO(
    id="bandit_hedge_wizard",
    base_id="bandit_hedge_wizard",
    name="bandit_hedge_wizard",
    description="An outcast who dabbles in forbidden magic, using a crude staff to cast chaotic spells.",
    skills=("skill_polearms", "skill_light_armor", "skill_two_handed"),
    tags=(),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="bandit_gang.bandit_hedge_wizard",
        source_path="assets/monster_defaults/bandit_gang/png/bandit_hedge_wizard-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
