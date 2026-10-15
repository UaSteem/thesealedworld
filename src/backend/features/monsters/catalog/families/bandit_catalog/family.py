"""Canonical authored family, independent of historical family resources."""

from src.backend.features.monsters.catalog.nested_contracts import FamilyDTO, FamilyTraitsDTO, LootProfileDTO

from .bases.bandit_billhook import BANDIT_BILLHOOK
from .bases.bandit_blackguard import BANDIT_BLACKGUARD
from .bases.bandit_captain import BANDIT_CAPTAIN
from .bases.bandit_cutthroat import BANDIT_CUTTHROAT
from .bases.bandit_hedge_wizard import BANDIT_HEDGE_WIZARD
from .bases.bandit_kingpin import BANDIT_KINGPIN
from .bases.bandit_knife_rat import BANDIT_KNIFE_RAT
from .bases.bandit_lookout import BANDIT_LOOKOUT
from .bases.bandit_poacher import BANDIT_POACHER
from .bases.bandit_raider import BANDIT_RAIDER
from .bases.bandit_thug import BANDIT_THUG
from .bases.bandit_warlord import BANDIT_WARLORD
from .clans.base.clan import BASE_CLAN

BANDIT_FAMILY = FamilyDTO(
    id="bandit_gang",
    name="Бандиты",
    description="",
    bases=(
        BANDIT_THUG,
        BANDIT_POACHER,
        BANDIT_LOOKOUT,
        BANDIT_KNIFE_RAT,
        BANDIT_CUTTHROAT,
        BANDIT_RAIDER,
        BANDIT_BILLHOOK,
        BANDIT_CAPTAIN,
        BANDIT_HEDGE_WIZARD,
        BANDIT_BLACKGUARD,
        BANDIT_KINGPIN,
        BANDIT_WARLORD,
    ),
    clans=(BASE_CLAN,),
    traits=FamilyTraitsDTO(
        resource_version=1.4,
        archetype="humanoid",
        organization_type="gang",
        default_tags=("human", "outlaw", "survivor", "marauder"),
        loot_profile=LootProfileDTO(
            salvage_type="humanoid_gear",
            loot_mode="equipment",
            allowed_loadout_slots="full_humanoid",
            equipment_drop_policy="fixed_loadout",
            drops_as_equipment=True,
            materials=("coin_scraps", "torn_cloth", "worn_leather"),
            equipment_quality="poor_to_common",
        ),
    ),
)
