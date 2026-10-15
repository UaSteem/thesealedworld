"""Canonical nested starter catalogs and the unchanged historical anchor family."""

from src.backend.features.monsters.catalog.authoring import define_base_clan
from src.backend.features.monsters.catalog.families.bandit_catalog.family import BANDIT_FAMILY
from src.backend.features.monsters.catalog.families.goblin_catalog.family import GOBLIN_FAMILY
from src.backend.features.monsters.catalog.families.rat_catalog.family import RAT_FAMILY
from src.backend.features.monsters.catalog.families.system.anchor_sovereigns import ANCHOR_SOVEREIGNS_FAMILY
from src.backend.features.monsters.catalog.families.wolf_catalog.family import WOLF_FAMILY
from src.backend.features.monsters.catalog.nested_contracts import FamilyDTO, resolve_family


def _base_catalog(data: FamilyDTO):
    family, clans, members = resolve_family(data)
    # This registration currently supports the authored base clan only.
    if len(clans) != 1 or clans[0].id != f"{family.id}.base":
        raise ValueError("Base registration requires exactly one explicit base clan")
    return family, clans[0], members


RATS = _base_catalog(RAT_FAMILY)
WOLVES = _base_catalog(WOLF_FAMILY)
BANDITS = _base_catalog(BANDIT_FAMILY)
GOBLINS = _base_catalog(GOBLIN_FAMILY)
ANCHORS = define_base_clan(
    ANCHOR_SOVEREIGNS_FAMILY,
    family_name="Владыки якорей",
    clan_id="anchor_sovereigns.base",
    clan_name="Владыки якорей",
    normal_spawn=False,
    presentation={},
)

PREPARED_FAMILIES = (RATS, WOLVES, BANDITS, GOBLINS, ANCHORS)
