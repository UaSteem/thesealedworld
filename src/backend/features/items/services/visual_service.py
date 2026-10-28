"""Items-owned selection and public presentation of authored artwork."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from src.backend.features.generation_ai.asset_storage import build_asset_public_url
from src.backend.features.items.dto.visuals import ItemAppearanceDTO, ItemVisualPublicDTO
from src.backend.features.items.resources.retired_presentations import RETIRED_ITEM_PRESENTATIONS
from src.backend.features.items.resources.visuals import ITEM_VISUAL_CATALOG

if TYPE_CHECKING:
    from src.backend.features.items.dto.instance import GeneratedItemDTO
    from src.backend.features.items.services.catalog_service import ItemCatalogService


class ItemVisualService:
    def __init__(self, catalog: ItemCatalogService | None = None, *, public_base_url: str | None = None) -> None:
        if catalog is None:
            from src.backend.features.items.services.catalog_service import ItemCatalogService

            catalog = ItemCatalogService.load_default()
        if public_base_url is None:
            from src.backend.config.settings import settings

            public_base_url = settings.asset_public_base_url
        self.catalog = catalog
        self.public_base_url = public_base_url
        self.definitions = ITEM_VISUAL_CATALOG
        self.definitions.validate_item_references(catalog.base_items, catalog.materials)
        from src.backend.features.items.resources.affixes.narrative import validate_narrative_tags

        for variant in self.definitions.variants_by_id.values():
            validate_narrative_tags(variant.required_lore_tags)

    def select(
        self, item: GeneratedItemDTO, *, lore_tags: tuple[str, ...] = (), seed: str | None = None
    ) -> ItemAppearanceDTO | None:
        from src.backend.features.items.resources.affixes.narrative import validate_narrative_tags

        lore_tags = validate_narrative_tags(lore_tags)
        set_id = self.definitions.base_set_ids.get(item.base_id)
        material = self.catalog.get_material(item.material_id) if item.material_id else None
        if set_id is None or material is None:
            return None
        visual_set = self.definitions.sets_by_id[set_id]
        available_tags = set(lore_tags)
        candidates = [
            variant
            for variant in visual_set.variants
            if variant.material_id == material.id
            and variant.material_tier == material.tier
            and set(variant.required_lore_tags) <= available_tags
        ]
        if not candidates:
            return None
        specificity = max(len(set(variant.required_lore_tags)) for variant in candidates)
        preferred = sorted(
            (variant for variant in candidates if len(set(variant.required_lore_tags)) == specificity),
            key=lambda variant: variant.visual_variant_id,
        )
        # A separate RNG keeps appearance choices from consuming mechanical affix rolls.
        variant = random.Random(f"item-appearance:v1:{seed}" if seed is not None else None).choice(preferred)
        return ItemAppearanceDTO(
            visual_variant_id=variant.visual_variant_id,
            visual_set_id=set_id,
            width_cells=visual_set.width_cells,
            height_cells=visual_set.height_cells,
            volume_units=visual_set.width_cells * visual_set.height_cells,
        )

    def base_presentation(
        self, base_id: str, material_id: str | None, visual_variant_id: str | None = None
    ) -> tuple[str, str]:
        from src.backend.features.items.runtime.item_factory import ItemFactory

        base = self.catalog.get_base_item(base_id)
        material = self.catalog.get_material(material_id) if material_id else None
        if base is None:
            retired = RETIRED_ITEM_PRESENTATIONS.get(base_id)
            if retired is None:
                return "Неизвестный предмет", "Происхождение предмета неизвестно."
            name, description = retired
            if material and material.name_prefix_ru:
                name = f"{ItemFactory._agree_prefix(material.name_prefix_ru, name)} {name.lower()}"
            return name, description
        name = base.name_ru
        if material and material.name_prefix_ru:
            name = f"{ItemFactory._agree_prefix(material.name_prefix_ru, name)} {name.lower()}"
        variant = self.definitions.variants_by_id.get(visual_variant_id or "")
        set_id = self.definitions.base_set_ids.get(base_id)
        visual_set = self.definitions.sets_by_id.get(set_id or "")
        if (
            variant is not None
            and visual_set is not None
            and any(entry.visual_variant_id == visual_variant_id for entry in visual_set.variants)
            and variant.material_id == material_id
            and variant.description_ru
        ):
            return name, variant.description_ru
        return name, base.narrative_description or "Предмет с пока неизвестной историей."

    def get_public_variant(self, visual_variant_id: str) -> ItemVisualPublicDTO | None:
        variant = self.definitions.variants_by_id.get(visual_variant_id)
        if variant is None:
            return None
        visual_set = next(
            visual_set
            for visual_set in self.definitions.sets
            if any(entry.visual_variant_id == visual_variant_id for entry in visual_set.variants)
        )
        name, description = self.base_presentation(visual_set.base_ids[0], variant.material_id, visual_variant_id)
        return ItemVisualPublicDTO(
            visual_variant_id=visual_variant_id,
            visual_set_id=visual_set.visual_set_id,
            material_id=variant.material_id,
            material_tier=variant.material_tier,
            name=name,
            description=description,
            thumbnail_url=(
                build_asset_public_url(self.public_base_url, variant.thumbnail.storage_key)
                if variant.thumbnail
                else None
            ),
            image_url=build_asset_public_url(self.public_base_url, variant.image.storage_key)
            if variant.image
            else None,
            width_cells=visual_set.width_cells,
            height_cells=visual_set.height_cells,
        )

    def public_catalog(self) -> dict[str, ItemVisualPublicDTO]:
        return {
            variant_id: entry
            for variant_id in sorted(self.definitions.variants_by_id)
            if (entry := self.get_public_variant(variant_id)) is not None
        }
