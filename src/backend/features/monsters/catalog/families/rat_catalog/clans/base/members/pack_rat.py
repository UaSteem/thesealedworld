from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

PACK_RAT = MemberVariantDTO(
    id="pack_rat",
    base_id="pack_rat",
    name="Крыса-загонщик",
    description="Поджарая опытная крыса, обходящая добычу с фланга и действующая вместе со стаей.",
    skills=("skill_fencing", "skill_shield_mastery", "skill_light_armor"),
    tags=("pack_tactics", "flanker"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="rat_swarm.pack_rat",
        source_path="assets/monster_defaults/rat_swarm/png/pack_rat-v2.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
