from src.backend.features.monsters.catalog.nested_contracts import ClanDTO

from .members.brood_alpha import BROOD_ALPHA
from .members.burrow_guard import BURROW_GUARD
from .members.heavy_rat import HEAVY_RAT
from .members.ironfang import IRONFANG
from .members.pack_rat import PACK_RAT
from .members.rat_brute import RAT_BRUTE
from .members.rat_king import RAT_KING
from .members.scavenger_rat import SCAVENGER_RAT
from .members.screecher import SCREECHER
from .members.sewer_rat import SEWER_RAT
from .members.swarm_rat import SWARM_RAT
from .members.tunnel_rat import TUNNEL_RAT

BASE_CLAN = ClanDTO(
    text_id="rat.clan.base",
    id="rat_swarm.base",
    normal_spawn=True,
    features=(),
    members=(
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
)
