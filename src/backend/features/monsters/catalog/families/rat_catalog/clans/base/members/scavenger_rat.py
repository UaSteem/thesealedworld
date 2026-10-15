from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

SCAVENGER_RAT = MemberVariantDTO(
    id="scavenger_rat",
    base_id="scavenger_rat",
    name="Крыса-собиратель",
    description="Молодая крыса-собиратель, защищающая найденный лоскут ткани.",
    skills=("skill_fencing", "skill_dual_wield", "skill_light_armor"),
    tags=("young", "scavenger", "hoarder"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="rat_swarm.scavenger_rat",
        source_path="assets/monster_defaults/rat_swarm/png/scavenger_rat-v2.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
