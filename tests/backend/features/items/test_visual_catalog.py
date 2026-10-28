from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.backend.features.items.dto.visuals import ItemVisualCatalogDTO, ItemVisualSetDTO, ItemVisualVariantDTO
from src.backend.features.items.resources.visuals import (
    BASE_VISUAL_SET_IDS,
    ITEM_VISUAL_CATALOG,
    VISUAL_SETS_DB,
    VISUAL_VARIANTS_DB,
)
from src.backend.features.items.services.catalog_service import ItemCatalogService

ROOT = Path(__file__).resolve().parents[4]


def test_sword_catalog_matches_workbench_files_and_real_items():
    items = ItemCatalogService.load_default()
    ITEM_VISUAL_CATALOG.validate_item_references(items.base_items, items.materials)
    assert BASE_VISUAL_SET_IDS == {"sword": "sword.basic"}
    visual_set = VISUAL_SETS_DB[BASE_VISUAL_SET_IDS["sword"]]
    assert visual_set.base_ids == ("sword",)
    assert {variant.material_tier for variant in visual_set.variants} == set(range(6))

    directory = ROOT / "assets/item_art/variants/sword"
    workbench = json.loads((directory / "variants.json").read_text(encoding="utf-8"))
    assert workbench["base_id"] == "sword"
    assert set(VISUAL_VARIANTS_DB) == {entry["visual_variant_id"] for entry in workbench["variants"]}
    for entry in workbench["variants"]:
        variant = VISUAL_VARIANTS_DB[entry["visual_variant_id"]]
        assert variant.material_id == entry["material_id"]
        assert variant.material_tier == entry["material_tier"]
        assert variant.condition == entry["condition"]
        assert entry["base_id"] in visual_set.base_ids
        assert ROOT / variant.source_path == directory / entry["file"]
        assert hashlib.sha256((ROOT / variant.source_path).read_bytes()).hexdigest() == entry["sha256"]
    assert VISUAL_VARIANTS_DB["sword.basic.scrap_metal.t0"].condition == "worn"
    assert all(variant.condition == "clean" for variant in visual_set.variants if variant.material_tier > 0)


def test_visual_models_round_trip_through_json_and_derive_same_indexes():
    restored = ItemVisualCatalogDTO.model_validate_json(ITEM_VISUAL_CATALOG.model_dump_json())
    assert restored == ITEM_VISUAL_CATALOG
    assert restored.base_set_ids == BASE_VISUAL_SET_IDS
    assert restored.sets_by_id == VISUAL_SETS_DB
    assert restored.variants_by_id == VISUAL_VARIANTS_DB


@pytest.mark.parametrize("duplicate", ["set", "base", "variant", "cross_set_variant"])
def test_duplicate_ids_rejected_before_indexes_can_hide_them(duplicate):
    data = ITEM_VISUAL_CATALOG.model_dump()
    visual_set = data["sets"][0]
    if duplicate == "set":
        data["sets"] = (visual_set, visual_set)
    elif duplicate == "base":
        visual_set["base_ids"] = ("sword", "sword")
    elif duplicate == "variant":
        visual_set["variants"] += (visual_set["variants"][0],)
    else:
        other_set = {**visual_set, "visual_set_id": "sword.other", "base_ids": ("longsword",)}
        data["sets"] = (visual_set, other_set)
    with pytest.raises(ValidationError, match="Duplicate"):
        ItemVisualCatalogDTO.model_validate(data)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ("unknown_base", "Unknown item base"),
        ("unknown_material", "Unknown visual material"),
        ("wrong_tier", "tier mismatch"),
        ("disallowed_category", "not allowed"),
        ("disallowed_type", "not allowed"),
        ("disallowed_armor_class", "not allowed"),
    ],
)
def test_explicit_reference_check_rejects_inconsistent_catalogs(change, message):
    items = ItemCatalogService.load_default()
    data = ITEM_VISUAL_CATALOG.model_dump()
    visual_set = data["sets"][0]
    variant = visual_set["variants"][0]
    material_id = variant["material_id"]
    if change == "unknown_base":
        visual_set["base_ids"] = ("missing_base",)
    elif change == "unknown_material":
        variant["material_id"] = "missing_material"
    elif change == "wrong_tier":
        variant["material_tier"] = 1
    elif change == "disallowed_category":
        items.base_items["sword"] = items.base_items["sword"].model_copy(update={"allowed_materials": ["leather"]})
    elif change == "disallowed_type":
        items.materials[material_id] = items.materials[material_id].model_copy(update={"allowed_item_types": ["armor"]})
    else:
        items.materials[material_id] = items.materials[material_id].model_copy(
            update={"allowed_armor_classes": ["heavy"]}
        )
    catalog = ItemVisualCatalogDTO.model_validate(data)
    with pytest.raises(ValueError, match=message):
        catalog.validate_item_references(items.base_items, items.materials)


def test_same_set_can_serve_two_bases_and_multiple_variants_of_one_material():
    data = ITEM_VISUAL_CATALOG.model_dump()
    visual_set = data["sets"][0]
    visual_set["base_ids"] = ("sword", "longsword")
    alternate = {**visual_set["variants"][1], "visual_variant_id": "sword.alternate.iron.t1"}
    visual_set["variants"] += (alternate,)
    catalog = ItemVisualCatalogDTO.model_validate(data)
    items = ItemCatalogService.load_default()
    catalog.validate_item_references(items.base_items, items.materials)
    assert catalog.base_set_ids == {"sword": "sword.basic", "longsword": "sword.basic"}
    assert len(catalog.variants_by_id) == 7


@pytest.mark.parametrize(
    "path", ["", "/tmp/a.svg", "../a.svg", "a/../b.svg", "C:/a.svg", "a\\b.svg", "https://x/a.svg"]
)
def test_source_path_requires_repository_relative_file_path(path):
    data = VISUAL_VARIANTS_DB["sword.basic.iron.t1"].model_dump()
    data["source_path"] = path
    with pytest.raises(ValidationError, match="repository-relative"):
        ItemVisualVariantDTO.model_validate(data)


@pytest.mark.parametrize("update", [{"material_tier": -1}, {"material_tier": 8}, {"material_tier": True}, {"power": 7}])
def test_variant_rejects_invalid_tiers_and_mechanical_fields(update):
    data = {**VISUAL_VARIANTS_DB["sword.basic.iron.t1"].model_dump(), **update}
    with pytest.raises(ValidationError):
        ItemVisualVariantDTO.model_validate(data)


@pytest.mark.parametrize("field", ["base_ids", "variants"])
def test_visual_set_must_have_bases_and_variants(field):
    data = VISUAL_SETS_DB["sword.basic"].model_dump()
    data[field] = ()
    with pytest.raises(ValidationError):
        ItemVisualSetDTO.model_validate(data)
