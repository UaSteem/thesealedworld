from src.backend.features.monsters.catalog.nested_contracts import ClanDTO

from .members.goblin_bomber import GOBLIN_BOMBER
from .members.goblin_chief import GOBLIN_CHIEF
from .members.goblin_cutter import GOBLIN_CUTTER
from .members.goblin_scavenger import GOBLIN_SCAVENGER
from .members.goblin_scrapguard import GOBLIN_SCRAPGUARD
from .members.goblin_slinger import GOBLIN_SLINGER
from .members.goblin_sneak import GOBLIN_SNEAK
from .members.goblin_sparkpick import GOBLIN_SPARKPICK
from .members.goblin_spearman import GOBLIN_SPEARMAN
from .members.goblin_tinkerer import GOBLIN_TINKERER
from .members.goblin_trapmaster import GOBLIN_TRAPMASTER
from .members.scrap_king import SCRAP_KING

BASE_CLAN = ClanDTO(
    text_id="goblin.clan.base",
    id="goblin_tribe.base",
    normal_spawn=True,
    features=(),
    members=(
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
)
