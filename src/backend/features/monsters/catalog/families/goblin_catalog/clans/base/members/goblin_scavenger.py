from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

GOBLIN_SCAVENGER = MemberVariantDTO(
    id="goblin_scavenger",
    base_id="goblin_scavenger",
    name="goblin_scavenger",
    description="A goblin carrying a large, overflowing backpack. Wields a simple club.",
    skills=("skill_macing", "skill_shield_mastery", "skill_light_armor"),
    tags=("scavenger", "hoarder", "scrap", "buckler"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="goblin_tribe.goblin_scavenger",
        source_path="assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_scavenger-face-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
