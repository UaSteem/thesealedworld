"""Monster-owned feint selection while assembling a combat snapshot."""

from typing import Any

from src.backend.features.game_catalog.combat.resources.feints import get_feint_catalog_entry


def build_monster_feint_loadout(loadout: dict[str, Any], *, role: str | None) -> dict[str, Any]:
    """Keep HP-healing feints for elites/bosses, excluding them for ordinary ranks.

    This changes the available arsenal only, without changing shared feint
    definitions or the combat engine's healing behavior.
    """
    result = dict(loadout)
    if "known_feints" not in loadout:
        return result
    known = list(loadout.get("known_feints") or [])
    if role in {"minion", "veteran"}:
        known = [feint_id for feint_id in known if not _restores_hp(feint_id)]
    result["known_feints"] = known
    return result


def _restores_hp(feint_id: str) -> bool:
    entry = get_feint_catalog_entry(feint_id)
    if entry is None:
        return False
    technical = entry.technical
    if "heal" in technical.applicability_tags:
        return True
    for effect in [*(technical.effects or []), *(technical.preparation_effects or [])]:
        if effect.get("id") == "restore_hp":
            return True
        params = effect.get("params") or {}
        if any(str(key).startswith("heal_") for key in params):
            return True
    return False
