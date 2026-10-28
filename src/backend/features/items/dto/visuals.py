"""Authored item artwork; selection and persisted instance appearance are separate contracts."""

from __future__ import annotations

from functools import cached_property
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

if TYPE_CHECKING:
    from collections.abc import Mapping

    from src.backend.features.items.dto.catalog import BaseItemTemplateDTO, MaterialTemplateDTO

VisualId = Annotated[str, Field(min_length=1, pattern=r"^\S+$")]


class ItemAppearanceDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    visual_variant_id: VisualId | None = None
    visual_set_id: VisualId | None = None
    width_cells: int = Field(default=1, ge=1)
    height_cells: int = Field(default=1, ge=1)
    volume_units: int = Field(default=1, ge=1)


class ItemVisualRenditionDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    storage_key: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    width: int = Field(ge=1)
    height: int = Field(ge=1)
    content_type: Literal["image/webp"] = "image/webp"

    @field_validator("storage_key")
    @classmethod
    def validate_storage_key(cls, value: str) -> str:
        if not value.startswith("items/") or "\\" in value or ":" in value:
            raise ValueError("Item image storage key must belong to items/")
        if any(part in {"", ".", ".."} for part in value.split("/")) or not value.endswith(".webp"):
            raise ValueError("Item image storage key must be a relative WebP object key")
        return value


class ItemVisualPublicDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    visual_variant_id: VisualId
    visual_set_id: VisualId
    material_id: VisualId
    material_tier: int = Field(ge=0, le=7)
    name: str
    description: str
    thumbnail_url: str | None = None
    image_url: str | None = None
    width_cells: int = Field(default=1, ge=1)
    height_cells: int = Field(default=1, ge=1)


class ItemVisualVariantDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    visual_variant_id: VisualId
    material_id: VisualId
    material_tier: int = Field(ge=0, le=7, strict=True)
    source_path: str
    condition: Literal["clean", "worn"]
    description_ru: str = ""
    required_lore_tags: tuple[VisualId, ...] = ()
    thumbnail: ItemVisualRenditionDTO | None = None
    image: ItemVisualRenditionDTO | None = None

    @field_validator("source_path")
    @classmethod
    def validate_source_path(cls, value: str) -> str:
        path = PurePosixPath(value)
        if (
            not value
            or "\\" in value
            or ":" in value
            or path.is_absolute()
            or any(part in {"", ".", ".."} for part in value.split("/"))
        ):
            raise ValueError("Image source must be a repository-relative POSIX file path")
        return value


class ItemVisualSetDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    visual_set_id: VisualId
    base_ids: tuple[VisualId, ...] = Field(min_length=1)
    variants: tuple[ItemVisualVariantDTO, ...] = Field(min_length=1)
    width_cells: int = Field(default=1, ge=1)
    height_cells: int = Field(default=1, ge=1)


class ItemVisualCatalogDTO(BaseModel):
    """Validated definitions with derived ID dictionaries, following the skill catalog pattern."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    sets: tuple[ItemVisualSetDTO, ...]

    @model_validator(mode="after")
    def validate_unique_ids(self) -> Self:
        seen_sets: set[str] = set()
        seen_bases: set[str] = set()
        seen_variants: set[str] = set()
        for visual_set in self.sets:
            if visual_set.visual_set_id in seen_sets:
                raise ValueError(f"Duplicate visual set ID: {visual_set.visual_set_id}")
            seen_sets.add(visual_set.visual_set_id)
            for base_id in visual_set.base_ids:
                if base_id in seen_bases:
                    raise ValueError(f"Duplicate visual set binding for base: {base_id}")
                seen_bases.add(base_id)
            for variant in visual_set.variants:
                if variant.visual_variant_id in seen_variants:
                    raise ValueError(f"Duplicate visual variant ID: {variant.visual_variant_id}")
                seen_variants.add(variant.visual_variant_id)
        return self

    @cached_property
    def sets_by_id(self) -> dict[str, ItemVisualSetDTO]:
        return {visual_set.visual_set_id: visual_set for visual_set in self.sets}

    @cached_property
    def variants_by_id(self) -> dict[str, ItemVisualVariantDTO]:
        return {variant.visual_variant_id: variant for visual_set in self.sets for variant in visual_set.variants}

    @cached_property
    def base_set_ids(self) -> dict[str, str]:
        return {base_id: visual_set.visual_set_id for visual_set in self.sets for base_id in visual_set.base_ids}

    def validate_item_references(
        self,
        base_items: Mapping[str, BaseItemTemplateDTO],
        materials: Mapping[str, MaterialTemplateDTO],
    ) -> None:
        """Explicit assembly check; does not load Items, inspect files or select an image."""
        for visual_set in self.sets:
            for base_id in visual_set.base_ids:
                if base_id not in base_items:
                    raise ValueError(f"Unknown item base: {base_id}")
            for variant in visual_set.variants:
                material = materials.get(variant.material_id)
                if material is None:
                    raise ValueError(f"Unknown visual material: {variant.material_id}")
                if variant.material_tier != material.tier:
                    raise ValueError(f"Visual material tier mismatch: {variant.visual_variant_id}")
                for base_id in visual_set.base_ids:
                    base = base_items[base_id]
                    if (
                        material.category not in base.allowed_materials
                        or (material.allowed_item_types and base.type not in material.allowed_item_types)
                        or (material.allowed_armor_classes and base.armor_class not in material.allowed_armor_classes)
                    ):
                        raise ValueError(f"Visual material {material.id} is not allowed for base {base_id}")
