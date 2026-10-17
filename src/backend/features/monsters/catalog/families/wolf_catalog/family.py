"""Canonical authored wolf family; historical wolf resources are independent."""

from src.backend.features.monsters.catalog.nested_contracts import FamilyDTO, FamilyTraitsDTO, LootProfileDTO

from .bases.alpha_prime import ALPHA_PRIME
from .bases.cub import CUB
from .bases.dire_wolf import DIRE_WOLF
from .bases.flanker import FLANKER
from .bases.mangy_biter import MANGY_BITER
from .bases.old_fang import OLD_FANG
from .bases.pack_huntmaster import PACK_HUNTMASTER
from .bases.pack_leader import PACK_LEADER
from .bases.runner import RUNNER
from .bases.snapper import SNAPPER
from .bases.stalker import STALKER
from .clans.base.clan import BASE_PACK

WOLF_FAMILY = FamilyDTO(
    text_id="wolf.family",
    id="wolf_pack",
    bases=(
        CUB,
        RUNNER,
        MANGY_BITER,
        STALKER,
        FLANKER,
        SNAPPER,
        PACK_LEADER,
        DIRE_WOLF,
        OLD_FANG,
        PACK_HUNTMASTER,
        ALPHA_PRIME,
    ),
    clans=(BASE_PACK,),
    traits=FamilyTraitsDTO(
        resource_version=1.4,
        archetype="beast",
        organization_type="pack",
        default_tags=("beast", "wolf", "predator", "pack"),
        loot_profile=LootProfileDTO(
            salvage_type="beast_parts",
            loot_mode="salvage",
            allowed_loadout_slots="natural_only",
            equipment_drop_policy="none",
            drops_as_equipment=False,
            materials=("fang", "hide_scrap", "bone", "pelt"),
        ),
    ),
)
