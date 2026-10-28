"""Prepared artwork catalog. Import explicitly; not loaded by ItemCatalogService or generation."""

from src.backend.features.items.dto.visuals import ItemVisualCatalogDTO

from .sword import SWORD_VISUAL_SET

ITEM_VISUAL_CATALOG = ItemVisualCatalogDTO(sets=(SWORD_VISUAL_SET,))

# Duplicate identities are rejected by the model before any ID index is constructed.
VISUAL_SETS_DB = ITEM_VISUAL_CATALOG.sets_by_id
VISUAL_VARIANTS_DB = ITEM_VISUAL_CATALOG.variants_by_id
BASE_VISUAL_SET_IDS = ITEM_VISUAL_CATALOG.base_set_ids

__all__ = ["BASE_VISUAL_SET_IDS", "ITEM_VISUAL_CATALOG", "VISUAL_SETS_DB", "VISUAL_VARIANTS_DB"]
