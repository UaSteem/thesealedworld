from src.backend.features.monsters.catalog.contracts import ImageAssetReference
from src.backend.features.monsters.catalog.nested_contracts import (
    BaseLoadoutDTO,
    BaseStatsDTO,
    MemberBaseDTO,
    TierAvailabilityDTO,
)

RUNNER = MemberBaseDTO(
    id="runner",
    role="minion",
    assembly_cost=12,
    stats=BaseStatsDTO(
        strength=14,
        agility=15,
        endurance=13,
        intellect=10,
        memory=8,
        mental=11,
        perception=12,
        projection=7,
        prediction=9,
    ),
    loadout=BaseLoadoutDTO(
        main_hand="wolf_young_fangs", off_hand=None, chest_armor="wolf_hide", amulet="wolf_pack_mark"
    ),
    tiers=TierAvailabilityDTO(min_tier=1, max_tier=5),
    spawn_weight=20,
    default_image=ImageAssetReference(
        **{
            "asset_id": "wolf_pack.runner",
            "source_path": "assets/monster_defaults/wolf_pack/png/runner-v1.png",
            "review_status": "review_ready",
            "display_mirror": False,
        }
    ),
)
