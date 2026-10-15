from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import MemberVariantDTO

GOBLIN_TRAPMASTER = MemberVariantDTO(
    id="goblin_trapmaster",
    base_id="goblin_trapmaster",
    name="goblin_trapmaster",
    description="A patient goblin engineer covered in twine, hooks, and stolen monolith fragments.",
    skills=("skill_fencing", "skill_dual_wield", "skill_medium_armor", "skill_tactics", "skill_anatomy"),
    tags=("trapper", "engineer", "controller", "dual_wield", "precision"),
    ability_ids=(),
    image=ImageAssetReference(
        asset_id="goblin_tribe.goblin_trapmaster",
        source_path="assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_trapmaster-face-v1.png",
        review_status="accepted",
        display_mirror=False,
    ),
)
