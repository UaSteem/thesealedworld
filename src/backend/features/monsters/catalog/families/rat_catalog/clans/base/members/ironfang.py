from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

IRONFANG = MemberVariantDTO(
    id="ironfang",
    base_id="ironfang",
    name="Железный клык",
    description="Поджарая крыса с длинной мордой, сильной челюстью и особенно крупными естественными резцами.",
    skills=("skill_macing", "skill_two_handed", "skill_heavy_armor", "skill_anatomy"),
    tags=("fangs", "fighter"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="rat_swarm.ironfang",
        source_path="assets/monster_defaults/rat_swarm/png/ironfang-v2.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
