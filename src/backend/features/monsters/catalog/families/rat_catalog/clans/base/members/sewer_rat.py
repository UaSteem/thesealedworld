from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

SEWER_RAT = MemberVariantDTO(
    id="sewer_rat",
    base_id="sewer_rat",
    name="Канализационная крыса",
    description="Молодая небольшая крыса с мягкой серо-коричневой шерстью и осторожным любопытным взглядом.",
    skills=("skill_fencing", "skill_dual_wield", "skill_light_armor"),
    tags=("young", "weak"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="rat_swarm.sewer_rat",
        source_path="assets/monster_defaults/rat_swarm/png/sewer_rat-v2.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
