from src.backend.features.monsters.catalog.nested_contracts import ClanDTO

from .members.bandit_billhook import BANDIT_BILLHOOK
from .members.bandit_blackguard import BANDIT_BLACKGUARD
from .members.bandit_captain import BANDIT_CAPTAIN
from .members.bandit_cutthroat import BANDIT_CUTTHROAT
from .members.bandit_hedge_wizard import BANDIT_HEDGE_WIZARD
from .members.bandit_kingpin import BANDIT_KINGPIN
from .members.bandit_knife_rat import BANDIT_KNIFE_RAT
from .members.bandit_lookout import BANDIT_LOOKOUT
from .members.bandit_poacher import BANDIT_POACHER
from .members.bandit_raider import BANDIT_RAIDER
from .members.bandit_thug import BANDIT_THUG
from .members.bandit_warlord import BANDIT_WARLORD

BASE_CLAN = ClanDTO(
    text_id="bandit.clan.base",
    id="bandit_gang.base",
    normal_spawn=True,
    features=(),
    members=(
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
)
