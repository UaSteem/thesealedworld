"""No-database inventory previews using the authored sword material ladder."""

from tools.game_preview.fixtures import PreviewFixture

from src.backend.features.inventory.services.projection import build_runtime_session
from src.backend.features.inventory.services.view import InventoryViewService
from src.backend.features.items.services.visual_service import ItemVisualService
from src.shared.schemas.inventory import InventoryRuntimeItemDTO


def build_fixture(name: str, params: dict[str, str]) -> PreviewFixture:
    if name == "future":
        return _future_fixture()
    if name != "swords":
        raise ValueError("Inventory fixture supports 'inventory/swords' and 'inventory/future'.")
    visuals = ItemVisualService()
    items = []
    for visual in sorted(visuals.public_catalog().values(), key=lambda entry: entry.material_tier):
        items.append(
            InventoryRuntimeItemDTO(
                item_id=f"preview-sword-{visual.material_tier}",
                base_id="sword",
                item_type="weapon",
                name=visual.name,
                description=visual.description,
                material_id=visual.material_id,
                visual_variant_id=visual.visual_variant_id,
                thumbnail_url=visual.thumbnail_url,
                image_url=visual.image_url,
                rarity_tier=visual.material_tier,
                valid_slots=["main_hand", "off_hand"],
                mechanics={"power": 4 + visual.material_tier * 2, "durability_current": 10, "durability_max": 10},
                metadata={"width_cells": visual.width_cells, "height_cells": visual.height_cells},
            )
        )
    # A separate equipped object proves thumbnail selection while all six larger
    # images remain in the bag. The second hand and armor retain empty-slot icons.
    equipped = items[1].model_copy(
        deep=True,
        update={
            "item_id": "preview-equipped-sword",
            "placement": "equipped",
            "slot": "main_hand",
        },
    )
    fallback = InventoryRuntimeItemDTO(
        item_id="preview-fallback",
        base_id="battle_axe",
        item_type="weapon",
        name="Боевой топор",
        valid_slots=["main_hand"],
        metadata={"width_cells": 2, "height_cells": 2},
    )
    window = InventoryViewService().build_window(
        build_runtime_session(101, [equipped, *items, fallback]),
        can_act=True,
        strength=8,
        avatar_url="/static/images/avatars/silhouette_m.webp",
        avatar_name="Sword preview",
    )
    return PreviewFixture(
        context={"inventory_window": window, "char_id": 101, "domain": "inventory"},
        template="game/components/inventory/right_panel.html",
        title="Inventory: swords T0–T5",
        description="No database: selected artwork, two image sizes, empty equipment slots and generic fallback.",
        body_class="inventory-preview",
    )


def _future_fixture() -> PreviewFixture:
    from src.backend.features.items.dto.instance import ItemGenerationRequestDTO, ItemOriginRefDTO
    from src.backend.features.items.runtime.item_factory import ItemFactory

    visuals = ItemVisualService()
    factory = ItemFactory(visuals.catalog)
    items = []
    tiers = {}
    for visual in sorted(visuals.public_catalog().values(), key=lambda entry: entry.material_tier):
        tier = visual.material_tier
        generated = factory.generate_player_item(
            ItemGenerationRequestDTO(
                base_id="sword",
                material_id=visual.material_id,
                rarity_tier=tier,
                affix_count=2 if tier >= 2 else 0,
                forced_affix_ids=["weapon_accuracy", "crit_chance"] if tier >= 2 else [],
                origin_ref=ItemOriginRefDTO(seed=f"inventory-layout-preview:{tier}"),
            )
        )
        item_id = f"layout-sword-{tier}"
        tiers[item_id] = tier
        items.append(
            InventoryRuntimeItemDTO(
                item_id=item_id,
                base_id=generated.base_id,
                item_type=generated.item_type,
                name=visual.name,
                description=visual.description,
                rarity=generated.rarity,
                rarity_tier=generated.rarity_tier,
                material_id=generated.material_id,
                visual_variant_id=visual.visual_variant_id,
                thumbnail_url=visual.thumbnail_url,
                image_url=visual.image_url,
                valid_slots=generated.valid_slots,
                mechanics={
                    **generated.mechanics,
                    "power": generated.power,
                    "durability_current": generated.durability_max,
                    "durability_max": generated.durability_max,
                },
                metadata={"width_cells": 1, "height_cells": 3},
            )
        )
    window = InventoryViewService().build_window(build_runtime_session(101, items), can_act=False)
    return PreviewFixture(
        context={
            "future_rows": window.visible_rows,
            "future_tiers": tiers,
            "selected_id": "layout-sword-4",
            "future_phaser_payload": {
                "items": [
                    {
                        "item_id": row.item_id,
                        "visual_variant_id": row.visual_variant_id,
                        "name": row.name,
                        "tier": tiers[row.item_id],
                        "rarity_label": row.rarity_label,
                        "image_url": row.image_url,
                        "thumbnail_url": row.thumbnail_url,
                        "texture_url": (
                            f"/preview/item-textures/{row.visual_variant_id}/image"
                            f"?v={(row.image_url or '').rsplit('/', 1)[-1]}"
                        ),
                        "grid_w": row.grid_w,
                        "grid_h": row.grid_h,
                        "description": row.details.description,
                        "details": [line.model_dump(mode="json") for line in row.details.details],
                        "affixes": [line.model_dump(mode="json") for line in row.details.affixes],
                        "is_identified": False,
                    }
                    for row in window.visible_rows
                    if row.details is not None
                ],
                "columns": 8,
                "rows": 5,
                "selected_id": None,
            },
        },
        template="game/previews/inventory_future.html",
        title="Инвентарь — пример новой карточки",
        description="Presentation-only preview; character equipment excluded, one eight-cell belt, existing sword data.",
        body_class="inventory-future-preview",
    )
