from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

TUNNEL_RAT = MemberVariantDTO(
    id="tunnel_rat",
    base_id="tunnel_rat",
    name="Крыса-землекоп",
    description="Опытная крыса-землекоп с крупными передними когтями и старым шрамом на морде.",
    skills=("skill_fencing", "skill_dual_wield", "skill_medium_armor"),
    tags=("digger", "stealth"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="rat_swarm.tunnel_rat",
        source_path="assets/monster_defaults/rat_swarm/png/tunnel_rat-v2.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
