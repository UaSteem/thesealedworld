"""Project current intrinsic accessory bonuses without rewriting authored rolls."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, Any

from src.backend.features.items.resources.base_item.accessories.belts import BELTS_DB
from src.backend.features.items.resources.base_item.accessories.jewelry import JEWELRY_DB
from src.backend.features.items.resources.base_item.garment.basic import GARMENT_DB
from src.backend.features.items.resources.support_progression import support_bonus_at_tier

if TYPE_CHECKING:
    from src.backend.features.items.services.catalog_service import ItemCatalogService

_SUPPORT_KEYS = {
    "ring": ("hp_regen", "mental_resistance"),
    "amulet": ("en_regen", "debuff_avoidance"),
    "earring": ("stamina_regen", "initiative"),
    "belt": ("hp",),
    "boots": ("stamina", "stamina_regen", "environment_gravity_resistance"),
    "gloves": ("anti_dodge_chance", "physical_crit_chance", "environment_bio_resistance"),
    "cloak": ("hp_regen", "environment_heat_resistance", "environment_cold_resistance"),
}
_BASES = {**JEWELRY_DB, **BELTS_DB, **GARMENT_DB["basic"]}


@lru_cache(maxsize=1)
def _catalog() -> ItemCatalogService:
    from src.backend.features.items.services.catalog_service import ItemCatalogService

    return ItemCatalogService.load_default()


def resolve_accessory_bonuses(item: dict[str, Any], mechanics: dict[str, Any]) -> dict[str, Any]:
    """Return current owned implicits using material tier or ordinary multiplier.

    Saved equipment contains baked implicit bonuses. Reproject only the support
    properties owned by the accessory base; affixes and all other authored values
    remain untouched. Assignment, rather than addition, makes projection idempotent.
    """
    implicit = dict(mechanics.get("implicit_bonuses") or {})
    base_id = str(item.get("base_id") or mechanics.get("base_id") or "")
    keys = _SUPPORT_KEYS.get(base_id)
    if keys is None:
        return implicit
    material = mechanics.get("material") or {}
    metadata = item.get("metadata") or mechanics.get("metadata") or {}
    generation = item.get("generation") or {}
    material_id = (
        material.get("material_id")
        or item.get("material_id")
        or metadata.get("material_id")
        or generation.get("material_id")
    )
    template = _catalog().get_material(str(material_id)) if material_id else None
    tier = material.get("tier")
    if tier is None and template is not None:
        tier = template.tier
    if tier is None:
        tier = next(
            (
                value
                for value in (
                    mechanics.get("tier"),
                    metadata.get("tier"),
                    item.get("item_tier"),
                    generation.get("item_tier"),
                    mechanics.get("item_tier"),
                )
                if value is not None
            ),
            0,
        )
    tier_mult = material.get("tier_mult", mechanics.get("tier_mult"))
    if tier_mult is None:
        tier_mult = template.tier_mult if template is not None else 1.0
    for key in keys:
        value = _BASES[base_id]["implicit_bonuses"].get(key)
        if value is None:
            implicit.pop(key, None)
        else:
            support_value = support_bonus_at_tier(base_id, key, tier)
            implicit[key] = support_value if support_value is not None else round(float(value) * float(tier_mult), 4)
    return implicit
