"""Project current intrinsic accessory bonuses without rewriting authored rolls."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, Any

from src.backend.features.items.resources.base_item.accessories.belts import BELTS_DB
from src.backend.features.items.resources.base_item.accessories.jewelry import JEWELRY_DB

if TYPE_CHECKING:
    from src.backend.features.items.services.catalog_service import ItemCatalogService

_SUPPORT_KEYS = {"ring": "hp_regen", "amulet": "en_regen", "earring": "stamina_regen", "belt": "hp"}
_BASES = {**JEWELRY_DB, **BELTS_DB}


@lru_cache(maxsize=1)
def _catalog() -> ItemCatalogService:
    from src.backend.features.items.services.catalog_service import ItemCatalogService

    return ItemCatalogService.load_default()


def resolve_accessory_bonuses(item: dict[str, Any], mechanics: dict[str, Any]) -> dict[str, Any]:
    """Return intrinsic bonuses with current support scaled by the item's material.

    Saved equipment contains baked implicit bonuses. Reproject only the support
    property owned by the accessory base; affixes and all other authored values
    remain untouched. Assignment, rather than addition, makes projection idempotent.
    """
    implicit = dict(mechanics.get("implicit_bonuses") or {})
    base_id = str(item.get("base_id") or mechanics.get("base_id") or "")
    key = _SUPPORT_KEYS.get(base_id)
    if key is None:
        return implicit
    material = mechanics.get("material") or {}
    metadata = item.get("metadata") or mechanics.get("metadata") or {}
    generation = item.get("generation") or {}
    tier_mult = material.get("tier_mult", mechanics.get("tier_mult"))
    if tier_mult is None:
        material_id = (
            material.get("material_id")
            or item.get("material_id")
            or metadata.get("material_id")
            or generation.get("material_id")
        )
        template = _catalog().get_material(str(material_id)) if material_id else None
        tier_mult = template.tier_mult if template is not None else 1.0
    implicit[key] = round(float(_BASES[base_id]["implicit_bonuses"][key]) * float(tier_mult), 4)
    return implicit
