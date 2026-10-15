from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

SCRAP_KING = MemberVariantDTO(
    id="scrap_king",
    base_id="scrap_king",
    name="scrap_king",
    description="A standing, combat-ready goblin scrap king with salvaged armor and a heavy weapon.",
    skills=("skill_macing", "skill_heavy_armor", "skill_two_handed", "skill_tactics", "skill_anatomy"),
    tags=("king", "heavy_armor", "engineer", "two_handed", "scrap"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="goblin_tribe.scrap_king",
        source_path="assets/monster_defaults/goblin_tribe/face_repair_candidates/scrap_king-standing-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
