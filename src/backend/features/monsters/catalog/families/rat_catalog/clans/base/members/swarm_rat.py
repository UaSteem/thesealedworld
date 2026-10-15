from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

SWARM_RAT = MemberVariantDTO(
    id="swarm_rat",
    base_id="swarm_rat",
    name="Стайная крыса",
    description="Маленькая юркая крыса, опасная вместе с остальной стаей.",
    skills=("skill_fencing", "skill_dual_wield", "skill_light_armor"),
    tags=("young", "swarm"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="rat_swarm.swarm_rat",
        source_path="assets/monster_defaults/rat_swarm/png/swarm_rat-v2.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
