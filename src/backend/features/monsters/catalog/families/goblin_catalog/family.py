"""Canonical authored family, independent of historical family resources."""

from src.backend.features.monsters.catalog.nested_contracts import FamilyDTO, FamilyTraitsDTO, LootProfileDTO

from .bases.goblin_bomber import GOBLIN_BOMBER
from .bases.goblin_chief import GOBLIN_CHIEF
from .bases.goblin_cutter import GOBLIN_CUTTER
from .bases.goblin_scavenger import GOBLIN_SCAVENGER
from .bases.goblin_scrapguard import GOBLIN_SCRAPGUARD
from .bases.goblin_slinger import GOBLIN_SLINGER
from .bases.goblin_sneak import GOBLIN_SNEAK
from .bases.goblin_sparkpick import GOBLIN_SPARKPICK
from .bases.goblin_spearman import GOBLIN_SPEARMAN
from .bases.goblin_tinkerer import GOBLIN_TINKERER
from .bases.goblin_trapmaster import GOBLIN_TRAPMASTER
from .bases.scrap_king import SCRAP_KING
from .clans.base.clan import BASE_CLAN

GOBLIN_FAMILY = FamilyDTO(
    id="goblin_tribe",
    name="Гоблины",
    description="",
    bases=(
        GOBLIN_SNEAK,
        GOBLIN_SCAVENGER,
        GOBLIN_CUTTER,
        GOBLIN_SPARKPICK,
        GOBLIN_SPEARMAN,
        GOBLIN_SLINGER,
        GOBLIN_SCRAPGUARD,
        GOBLIN_TINKERER,
        GOBLIN_BOMBER,
        GOBLIN_TRAPMASTER,
        GOBLIN_CHIEF,
        SCRAP_KING,
    ),
    clans=(BASE_CLAN,),
    traits=FamilyTraitsDTO(
        resource_version=1.4,
        archetype="humanoid",
        organization_type="horde",
        default_tags=("goblin", "small", "cunning", "tinkerer"),
        loot_profile=LootProfileDTO(
            salvage_type="humanoid_gear",
            loot_mode="equipment",
            allowed_loadout_slots="full_humanoid",
            equipment_drop_policy="fixed_loadout",
            drops_as_equipment=True,
            materials=("scrap_metal", "torn_cloth", "cracked_tool"),
            equipment_quality="poor_to_common",
        ),
    ),
)
