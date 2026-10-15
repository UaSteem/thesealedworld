from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

SCREECHER = MemberVariantDTO(
    id="screecher",
    base_id="screecher",
    name="Крыса-крикун",
    description="Матёрая крыса с мощным горловым мешком, предупреждающая стаю пронзительным криком.",
    skills=("skill_archery", "skill_ranged_combat", "skill_medium_armor"),
    tags=("support", "alarm"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="rat_swarm.screecher",
        source_path="assets/monster_defaults/rat_swarm/png/screecher-v2.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
