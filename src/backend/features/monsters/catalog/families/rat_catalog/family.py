"""Canonical authored family, independent of historical family resources."""

from src.backend.features.monsters.catalog.nested_contracts import FamilyDTO, FamilyTraitsDTO, LootProfileDTO

from .bases.brood_alpha import BROOD_ALPHA
from .bases.burrow_guard import BURROW_GUARD
from .bases.heavy_rat import HEAVY_RAT
from .bases.ironfang import IRONFANG
from .bases.pack_rat import PACK_RAT
from .bases.rat_brute import RAT_BRUTE
from .bases.rat_king import RAT_KING
from .bases.scavenger_rat import SCAVENGER_RAT
from .bases.screecher import SCREECHER
from .bases.sewer_rat import SEWER_RAT
from .bases.swarm_rat import SWARM_RAT
from .bases.tunnel_rat import TUNNEL_RAT
from .clans.base.clan import BASE_CLAN

RAT_FAMILY = FamilyDTO(
    text_id="rat.family",
    id="rat_swarm",
    bases=(
        SEWER_RAT,
        SCAVENGER_RAT,
        SWARM_RAT,
        TUNNEL_RAT,
        PACK_RAT,
        SCREECHER,
        BURROW_GUARD,
        IRONFANG,
        HEAVY_RAT,
        RAT_BRUTE,
        BROOD_ALPHA,
        RAT_KING,
    ),
    clans=(BASE_CLAN,),
    traits=FamilyTraitsDTO(
        resource_version=1.4,
        archetype="beast",
        organization_type="swarm",
        default_tags=("beast", "rat", "swarm"),
        loot_profile=LootProfileDTO(
            salvage_type="beast_parts",
            loot_mode="salvage",
            allowed_loadout_slots="natural_only",
            equipment_drop_policy="none",
            drops_as_equipment=False,
            materials=("fang", "hide_scrap", "bone", "tainted_sample"),
            equipment_quality=None,
        ),
    ),
)
