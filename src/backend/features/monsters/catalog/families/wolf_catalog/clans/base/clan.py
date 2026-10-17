from src.backend.features.monsters.catalog.nested_contracts import ClanDTO

from .members.alpha_prime import ALPHA_PRIME
from .members.cub import CUB
from .members.dire_wolf import DIRE_WOLF
from .members.flanker import FLANKER
from .members.mangy_biter import MANGY_BITER
from .members.old_fang import OLD_FANG
from .members.pack_huntmaster import PACK_HUNTMASTER
from .members.pack_leader import PACK_LEADER
from .members.runner import RUNNER
from .members.snapper import SNAPPER
from .members.stalker import STALKER

BASE_PACK = ClanDTO(
    text_id="wolf.clan.base",
    id="wolf_pack.base",
    members=(
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
)
