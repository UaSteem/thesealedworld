from src.backend.features.monsters.catalog.nested_contracts import ClanDTO

from .members.quarry_overseer import QUARRY_OVERSEER
from .members.rune_guardian import RUNE_GUARDIAN
from .members.rune_punisher import RUNE_PUNISHER
from .members.rune_resonator import RUNE_RESONATOR
from .members.stone_bulwark import STONE_BULWARK
from .members.stone_catcher import STONE_CATCHER
from .members.stone_colossus import STONE_COLOSSUS
from .members.stone_crusher import STONE_CRUSHER
from .members.stone_ram import STONE_RAM
from .members.stone_sentry import STONE_SENTRY
from .members.stone_thrower import STONE_THROWER
from .members.stone_worker import STONE_WORKER

BASE_GOLEMS = ClanDTO(
    text_id="golem.clan.base",
    id="golem_foundry.base",
    members=(
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
)
