"""Stone construct draft: prices and T0–T5 availability await balance validation."""

from src.backend.features.monsters.catalog.nested_contracts import FamilyDTO, FamilyTraitsDTO, LootProfileDTO

from .bases.quarry_overseer import QUARRY_OVERSEER
from .bases.rune_guardian import RUNE_GUARDIAN
from .bases.rune_punisher import RUNE_PUNISHER
from .bases.rune_resonator import RUNE_RESONATOR
from .bases.stone_bulwark import STONE_BULWARK
from .bases.stone_catcher import STONE_CATCHER
from .bases.stone_colossus import STONE_COLOSSUS
from .bases.stone_crusher import STONE_CRUSHER
from .bases.stone_ram import STONE_RAM
from .bases.stone_sentry import STONE_SENTRY
from .bases.stone_thrower import STONE_THROWER
from .bases.stone_worker import STONE_WORKER
from .clans.base.clan import BASE_GOLEMS

GOLEM_FAMILY = FamilyDTO(
    text_id="golem.family",
    id="golem_foundry",
    bases=(
        STONE_WORKER,
        STONE_SENTRY,
        STONE_THROWER,
        STONE_RAM,
        STONE_CRUSHER,
        STONE_BULWARK,
        STONE_CATCHER,
        RUNE_GUARDIAN,
        RUNE_PUNISHER,
        RUNE_RESONATOR,
        QUARRY_OVERSEER,
        STONE_COLOSSUS,
    ),
    clans=(BASE_GOLEMS,),
    traits=FamilyTraitsDTO(
        archetype="construct",
        organization_type="solitary",
        default_tags=("construct", "golem", "stone"),
        loot_profile=LootProfileDTO(
            salvage_type="construct_fragments",
            loot_mode="salvage",
            allowed_loadout_slots="natural_only",
            equipment_drop_policy="none",
            drops_as_equipment=False,
            materials=("stone", "rune_fragment"),
        ),
    ),
)
