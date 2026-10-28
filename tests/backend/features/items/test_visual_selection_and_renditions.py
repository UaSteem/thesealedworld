from __future__ import annotations

import hashlib
import random
from pathlib import Path

import pytest
from PIL import Image
from pydantic import ValidationError
from tools.assets.item_visuals import rendition_files

from src.backend.features.items.dto.instance import ItemGenerationRequestDTO, ItemOriginRefDTO
from src.backend.features.items.dto.visuals import ItemVisualCatalogDTO, ItemVisualRenditionDTO
from src.backend.features.items.resources.visuals import ITEM_VISUAL_CATALOG
from src.backend.features.items.runtime.item_factory import ItemFactory
from src.backend.features.items.services.catalog_service import ItemCatalogService
from src.backend.features.items.services.visual_service import ItemVisualService

ROOT = Path(__file__).resolve().parents[4]


def test_all_twelve_renditions_are_real_transparent_content_addressed_webp():
    files = rendition_files()
    assert len(files) == 12
    assert len({rendition.storage_key for _, rendition in files}) == 12
    for path, rendition in files:
        assert path.is_relative_to(ROOT / "assets/item_art/renders")
        assert hashlib.sha256(path.read_bytes()).hexdigest() == rendition.sha256
        assert rendition.sha256 in rendition.storage_key
        with Image.open(path) as rendered:
            assert rendered.format == "WEBP"
            assert rendered.size == (rendition.width, rendition.height)
            alpha = rendered.convert("RGBA").getchannel("A")
            assert alpha.getextrema() == (0, 255)
            bbox = alpha.getbbox()
            assert bbox is not None
            assert bbox[3] - bbox[1] > 2 * (bbox[2] - bbox[0])
    for variant in ITEM_VISUAL_CATALOG.variants_by_id.values():
        assert (variant.thumbnail.width, variant.thumbnail.height) == (96, 288)
        assert (variant.image.width, variant.image.height) == (256, 768)


def test_public_catalog_has_only_baseline_text_and_two_delivery_urls():
    service = ItemVisualService(public_base_url="/static/generated-assets")
    public = service.public_catalog()
    assert len(public) == 6
    assert public["sword.basic.adamantite.t4"].name == "Адамантитовый меч"
    for entry in public.values():
        payload = entry.model_dump(mode="json")
        assert entry.thumbnail_url.startswith("/static/generated-assets/items/sword/")
        assert entry.image_url.startswith("/static/generated-assets/items/sword/")
        assert entry.thumbnail_url != entry.image_url
        assert entry.description
        assert (entry.width_cells, entry.height_cells) == (1, 3)
        assert not any(key in payload for key in ("source_path", "mechanics", "clan_id", "generated_template_id"))
    assert service.get_public_variant("not-a-real-variant") is None


def test_selector_uses_material_not_rarity_and_falls_back_for_missing_art():
    catalog = ItemCatalogService.load_default()
    service = ItemVisualService(catalog, public_base_url="/assets")
    factory = ItemFactory(catalog)
    request = ItemGenerationRequestDTO(base_id="sword", material_id="mat_iron_ingot", rarity_tier=4)
    item = factory.generate_player_item(request)
    assert service.select(item).visual_variant_id == "sword.basic.iron.t1"
    missing_tier = factory.generate_player_item(request.model_copy(update={"material_id": "mat_void_metal_ingot"}))
    assert service.select(missing_tier) is None
    other_base = factory.generate_player_item(request.model_copy(update={"base_id": "longsword"}))
    assert service.select(other_base) is None


def test_selector_prefers_matching_lore_art_and_does_not_consume_mechanical_randomness():
    catalog = ItemCatalogService.load_default()
    service = ItemVisualService(catalog, public_base_url="/assets")
    data = ITEM_VISUAL_CATALOG.model_dump()
    iron = next(entry for entry in data["sets"][0]["variants"] if entry["material_id"] == "mat_iron_ingot")
    specialized = {**iron, "visual_variant_id": "sword.blood.iron.t1", "required_lore_tags": ("blood_drain",)}
    data["sets"][0]["variants"] += (specialized,)
    service.definitions = ItemVisualCatalogDTO.model_validate(data)
    request = ItemGenerationRequestDTO(
        base_id="sword", material_id="mat_iron_ingot", rarity_tier=3, origin_ref=ItemOriginRefDTO(seed="fixed")
    )
    factory = ItemFactory(catalog)
    item = factory.generate_player_item(request)
    before = random.getstate()
    assert service.select(item, seed="fixed").visual_variant_id == "sword.basic.iron.t1"
    first = service.select(item, lore_tags=("blood_drain",), seed="fixed")
    assert first.visual_variant_id == "sword.blood.iron.t1"
    assert service.select(item, lore_tags=("blood_drain",), seed="fixed") == first
    assert random.getstate() == before
    assert factory.generate_player_item(request).mechanics == item.mechanics


@pytest.mark.parametrize("key", ["../x.webp", "/items/x.webp", "items/../x.webp", "items/x.png", "https://x/a.webp"])
def test_rendition_keys_are_typed_safe_s3_object_keys(key):
    with pytest.raises(ValidationError):
        ItemVisualRenditionDTO(storage_key=key, sha256="a" * 64, width=96, height=288)
