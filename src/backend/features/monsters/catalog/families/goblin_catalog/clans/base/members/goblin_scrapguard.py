from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

GOBLIN_SCRAPGUARD = MemberVariantDTO(
    id="goblin_scrapguard",
    base_id="goblin_scrapguard",
    name="goblin_scrapguard",
    description="A squat goblin hiding behind a crude shield packed with scavenged metal plates.",
    skills=("skill_macing", "skill_medium_armor", "skill_shield_mastery"),
    tags=("shield", "defender", "scrap"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="goblin_tribe.goblin_scrapguard",
        source_path="assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_scrapguard-face-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
