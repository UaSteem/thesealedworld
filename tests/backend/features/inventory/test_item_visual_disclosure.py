from types import SimpleNamespace

import pytest
from sqlalchemy.dialects import postgresql

from src.backend.features.inventory.repositories.items import InventoryItemRepository, runtime_item_from_instance
from src.backend.features.inventory.services.projection import build_runtime_session
from src.backend.features.inventory.services.view import InventoryViewService
from src.backend.features.items.services.visual_service import ItemVisualService


def instance(*, identified=False, status="generated"):
    return SimpleNamespace(
        id="sword-1", base_id="sword", item_type="weapon", rarity="common", rarity_tier=1,
        is_identified=identified, text_status=status, name="SECRET LEGACY NAME", description="SECRET LEGACY LORE",
        mechanics={"valid_slots": ["main_hand"], "durability_current": 9, "durability_max": 10},
        generation={"material_id": "mat_iron_ingot", "narrative_tags": []},
        appearance={"visual_variant_id": "sword.basic.iron.t1", "width_cells": 1, "height_cells": 3},
        metadata_={"lore": "SECRET METADATA LORE", "text_payload": {"name": "SECRET PAYLOAD"}},
        _inventory_generated_template=SimpleNamespace(name="SECRET AI NAME", description="SECRET AI LORE", text_status=status),
    )


def placement(**changes):
    return SimpleNamespace(holder_type="character", holder_id="7", storage_type="backpack", slot=None, locked_by=None, **changes)


@pytest.mark.unit
def test_unidentified_ready_text_never_reaches_inventory_dto_or_dom():
    from tools.game_preview.fixtures import PreviewFixture
    from tools.game_preview.render import render_preview

    item = runtime_item_from_instance(instance(), placement())
    window = InventoryViewService().build_window(build_runtime_session(7, [item]), can_act=True)
    serialized = window.model_dump_json()
    assert "SECRET" not in serialized
    assert window.visible_rows[0].details.is_identified is False
    assert window.visible_rows[0].details.text_status == "generated"
    assert {action.action for action in window.visible_rows[0].details.actions} >= {"equip", "identify"}
    html = render_preview(template_name="game/components/inventory/window.html", fixture=PreviewFixture(
        context={"inventory_window": window}, template="game/components/inventory/window.html", title="Test",
    ), wrap=False)
    assert "SECRET" not in html
    assert '"action": "identify"' in html
    assert item.image_url in html
    assert "--item-w: 1; --item-h: 3;" in html


@pytest.mark.unit
@pytest.mark.parametrize("identified,status,expected", [
    (False, "generated", False), (True, "pending", False), (True, "generated", True),
])
def test_identification_and_text_readiness_are_independent(identified, status, expected):
    item = runtime_item_from_instance(instance(identified=identified, status=status), placement())
    assert item.is_identified is identified
    assert (item.name == "SECRET AI NAME") is expected
    assert (item.description == "SECRET AI LORE") is expected
    assert item.mechanics["durability_current"] == 9
    assert item.thumbnail_url != item.image_url
    assert item.visual_variant_id == "sword.basic.iron.t1"


@pytest.mark.unit
@pytest.mark.parametrize("identified,status", [(False, "generated"), (True, "pending")])
def test_stale_cached_unidentified_text_is_reprojected_before_public_window(identified, status):
    item = runtime_item_from_instance(instance(), placement())
    item.is_identified, item.text_status = identified, status
    item.name, item.description = "SECRET CACHED NAME", "SECRET CACHED LORE"
    item.metadata = {"lore": "SECRET CACHED METADATA"}
    session = build_runtime_session(7, [item])
    window = InventoryViewService().build_window(session, can_act=True)
    assert "SECRET" not in window.model_dump_json()


@pytest.mark.unit
def test_noncovered_item_keeps_generic_icon_and_catalog_baseline():
    record = instance()
    record.base_id, record.appearance = "battle_axe", {}
    item = runtime_item_from_instance(record, placement())
    window = InventoryViewService().build_window(build_runtime_session(7, [item]), can_act=True)
    assert item.thumbnail_url is None and item.image_url is None
    assert window.visible_rows[0].icon == "weapon_axe"
    assert "топор" in window.visible_rows[0].name.lower()


@pytest.mark.unit
def test_equipment_uses_thumbnail_and_empty_slot_keeps_label_and_svg():
    import re

    from tools.game_preview.fixtures import build_fixture
    from tools.game_preview.render import render_preview

    fixture = build_fixture("inventory/swords")
    html = render_preview(template_name=fixture.template, fixture=fixture, wrap=False)
    buttons = re.findall(r"<button\b.*?</button>", html, flags=re.DOTALL)
    occupied = next(button for button in buttons if 'data-slot-id="main_hand"' in button)
    empty = next(button for button in buttons if 'data-slot-id="off_hand"' in button)
    visual = ItemVisualService().get_public_variant("sword.basic.iron.t1")
    # The larger image is inside the tooltip template, while the slot uses the thumbnail.
    slot_surface = occupied.split('<template class="inventory-tooltip-template">')[0]
    assert f'src="{visual.thumbnail_url}"' in slot_surface
    assert f'src="{visual.image_url}"' not in slot_surface
    assert "inventory-slot-title" not in slot_surface
    assert '<span class="inventory-slot-title">Вторая</span>' in empty
    assert "inventory-gear/shield.svg" in empty


class IdentifySession:
    def __init__(self, row):
        self.row = row
        self.statement = None
        self.flushed = 0

    async def execute(self, statement):
        self.statement = statement
        return SimpleNamespace(first=lambda: self.row)

    async def flush(self):
        self.flushed += 1


@pytest.mark.unit
async def test_identify_locks_owned_item_and_is_idempotent_without_text_ready():
    from src.backend.core.database import load_orm_models

    load_orm_models()
    record = instance(status="pending")
    db = IdentifySession((record, placement()))
    repo = InventoryItemRepository(db)
    assert await repo.identify_character_item(7, "sword-1")
    assert await repo.identify_character_item(7, "sword-1")
    assert record.is_identified is True
    assert record.text_status == "pending"
    statement = str(db.statement.compile(dialect=postgresql.dialect()))
    assert "FOR UPDATE OF item_instances, item_placements" in statement
    assert "item_placements.holder_id" in statement
    assert db.statement.compile().params["holder_id_1"] == "7"


@pytest.mark.unit
@pytest.mark.parametrize("row", [None, (instance(), SimpleNamespace(locked_by="trade", storage_type="backpack")),
                                     (instance(), SimpleNamespace(locked_by=None, storage_type="discarded"))])
async def test_identify_rejects_unowned_locked_or_inactive_items(row):
    db = IdentifySession(row)
    assert await InventoryItemRepository(db).identify_character_item(7, "sword-1") is False
    assert db.flushed == 0


@pytest.mark.unit
def test_bootstrap_exposes_normalized_public_visuals_with_content_hash():
    from src.backend.features.game_catalog.services.catalog_service import GameCatalogBootstrapService

    bootstrap = GameCatalogBootstrapService().build_bootstrap()
    visual = bootstrap.catalogs["item_visuals"]["sword.basic.iron.t1"]
    assert visual == ItemVisualService().get_public_variant("sword.basic.iron.t1").model_dump(mode="json")
    assert visual["width_cells"] == 1 and visual["height_cells"] == 3
    assert {"source_path", "mechanics", "required_lore_tags"}.isdisjoint(visual)
    assert bootstrap.manifest.catalogs["item_visuals"] == GameCatalogBootstrapService._hash(bootstrap.catalogs["item_visuals"])


@pytest.mark.unit
async def test_identify_action_keeps_existing_owner_authorization(monkeypatch):
    from unittest.mock import AsyncMock

    from fastapi import HTTPException

    from importlib import import_module

    router = import_module("src.backend.features.inventory.api.router")
    from src.shared.schemas.inventory import InventoryActionRequestDTO

    monkeypatch.setattr(router, "require_game_character_scope", lambda *args: None)
    service = SimpleNamespace(apply_action=AsyncMock())
    characters = SimpleNamespace(get_by_id_and_user_id=AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as error:
        await router.apply_inventory_action(
            request=SimpleNamespace(), dto=InventoryActionRequestDTO(char_id=7, item_id="sword-1", action="identify"),
            current_user=SimpleNamespace(id=3), service=service, characters=characters,
        )
    assert error.value.status_code == 404
    service.apply_action.assert_not_awaited()


@pytest.mark.unit
async def test_identify_action_pending_repeat_and_state_guard(fake_redis_service, fake_redis_client):
    from unittest.mock import AsyncMock

    from src.backend.features.inventory.services.inventory_service import InventoryActionForbiddenError, InventoryService
    from src.backend.infrastructure.actor_state.managers import CharacterSessionManager
    from src.backend.infrastructure.inventory.managers import InventorySessionManager
    from src.shared.schemas.inventory import InventoryActionRequestDTO, WalletDTO

    fake_redis_client.store["game:ac:7"] = {"char_id": 7, "state": "exploration", "risk": {}, "sessions": {}}
    record = instance(status="pending")

    async def identify(*args, **kwargs):
        record.is_identified = True
        return True

    repository = SimpleNamespace(
        list_character_items=AsyncMock(return_value=[(record, placement())]), get_wallet=AsyncMock(return_value=WalletDTO()),
        identify_character_item=AsyncMock(side_effect=identify), commit=AsyncMock(),
    )
    service = InventoryService(repository=repository, inventory_sessions=InventorySessionManager(fake_redis_service),
                               character_sessions=CharacterSessionManager(fake_redis_service), stream_client=AsyncMock())
    request = InventoryActionRequestDTO(char_id=7, action="identify", item_id="sword-1")
    first = await service.apply_action(request)
    second = await service.apply_action(request)
    assert first.visible_rows[0].details.is_identified is True
    assert second.visible_rows[0].details.is_identified is True
    assert second.visible_rows[0].details.text_status == "pending"
    assert "SECRET" not in second.visible_rows[0].name
    assert "identify" not in {action.action for action in second.visible_rows[0].details.actions}
    assert repository.commit.await_count == 2
    record._inventory_generated_template.text_status = "generated"
    ready = await service.open_window(7)
    assert ready.visible_rows[0].name == "SECRET AI NAME"
    fake_redis_client.store["game:ac:7"]["state"] = "combat"
    with pytest.raises(InventoryActionForbiddenError):
        await service.apply_action(request)
    assert repository.commit.await_count == 2
