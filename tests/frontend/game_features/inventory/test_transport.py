"""Inventory transport uses the existing authenticated API and authoritative DTO."""
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient
from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.frontend.core.renderer import get_ui_renderer
from src.frontend.features.auth.dependencies.providers import get_frontend_auth_service
from src.frontend.game_features.inventory.dependencies import get_backend_inventory_api
from src.frontend.game_features.inventory.routes.fragments import router
from src.shared.schemas.inventory import InventoryQuickSlotDTO, InventoryWindowDTO


def payload():
    return InventoryWindowDTO(char_id=7, avatar_name='Actual actor', can_act=False,
        forbidden_reason='В бою недоступно', body_zones=[], weapon_slots=[], accessory_rows=[],
        quick_slots=[InventoryQuickSlotDTO(slot_id='belt_slot_1', slot_index=1, enabled=True),
                     InventoryQuickSlotDTO(slot_id='belt_slot_2', slot_index=2, reason='belt_capacity')],
        tabs=[], visible_rows=[])


class Api:
    def __init__(self):
        self.calls = []
        self.failure = None
        self.value = payload()

    async def view(self, token, **kwargs):
        self.calls.append(('view', token, kwargs))
        return SimpleNamespace(payload=self.value)

    async def action(self, token, dto, **kwargs):
        self.calls.append(('action', token, dto, kwargs))
        if self.failure:
            response = httpx.Response(self.failure, json={'detail': {'message': 'Сервер отклонил'}},
                                      request=httpx.Request('POST', 'https://example.test/action'))
            raise httpx.HTTPStatusError('failed', request=response.request, response=response)
        return SimpleNamespace(payload=self.value)


class Auth:
    def __init__(self):
        self.calls = 0
        self.reject = False

    async def require_current_user(self, request):
        self.calls += 1
        if self.reject:
            raise HTTPException(status_code=401)
        return object()


class UI:
    async def render(self, name, context):
        if name.endswith('belt.html'):
            env = Environment(loader=FileSystemLoader(Path('src/frontend/templates')), autoescape=select_autoescape())
            return HTMLResponse(env.get_template(name).render(**context))
        return HTMLResponse('legacy inventory')


def setup():
    app, api, auth = FastAPI(), Api(), Auth()
    app.include_router(router)
    app.dependency_overrides[get_backend_inventory_api] = lambda: api
    app.dependency_overrides[get_frontend_auth_service] = lambda: auth
    app.dependency_overrides[get_ui_renderer] = UI
    client = TestClient(app)
    client.cookies.set('tbmmorpg_game_access_token', 'test-game-token')
    return client, api, auth


def test_client_inventory_payload_and_legacy_default():
    client, api, auth = setup()
    response = client.get('/game/inventory/window', params={'char_id': 7, 'tab': 'resources', 'presentation': 'client'})
    assert response.status_code == 200
    assert response.json() == {'inventory': payload().model_dump(mode='json'), 'notice': None}
    assert api.calls == [('view', 'test-game-token', {'char_id': 7, 'tab': 'resources'})]
    assert auth.calls == 1
    assert client.get('/game/inventory/window?char_id=7').text == 'legacy inventory'
    assert client.get('/game/inventory/window?char_id=7&presentation=invalid').status_code == 422


def test_client_action_forwards_existing_dto_and_refresh_header():
    client, api, _auth = setup()
    response = client.post('/game/inventory/action', data={'char_id': 7, 'action': 'equip',
        'item_id': 'item-actual', 'slot_id': 'main_hand', 'tab_id': 'items', 'presentation': 'client'})
    assert response.status_code == 200
    assert response.headers['HX-Trigger'] == 'character-status-refresh'
    assert response.json()['notice'] is None
    assert api.calls[0][2].model_dump() == {'char_id': 7, 'action': 'equip', 'item_id': 'item-actual', 'slot_id': 'main_hand'}
    assert len(api.calls) == 1
    legacy = client.post('/game/inventory/action', data={'char_id': 7, 'action': 'drop', 'item_id': 'item-actual'})
    assert legacy.headers['HX-Trigger'] == 'character-status-refresh'


@pytest.mark.parametrize("failure_status", [400, 409])
def test_client_conflict_refreshes_authoritative_view_and_exposes_notice(failure_status):
    client, api, _auth = setup()
    api.failure = failure_status
    response = client.post('/game/inventory/action', data={'char_id': 7, 'action': 'drop',
        'item_id': 'item-actual', 'presentation': 'client'})
    assert response.json()['notice'] == 'Сервер отклонил'
    assert response.json()['inventory']['can_act'] is False
    assert [call[0] for call in api.calls] == ['action', 'view']
    assert response.headers['HX-Trigger'] == 'character-status-refresh'


def test_belt_fragment_only_renders_real_quick_slots_no_inventory_actions():
    client, api, _auth = setup()
    response = client.get('/game/inventory/belt?char_id=7')
    assert response.status_code == 200
    assert response.text.count('data-belt-slot=') == 2
    assert 'belt_slot_1' in response.text and 'belt_slot_2' in response.text
    assert 'data-belt-enabled="false"' in response.text
    assert 'Пусто' in response.text
    assert '/game/inventory/action' not in response.text
    assert len(api.calls) == 1


def test_transport_requires_auth_and_game_token_before_backend():
    client, api, auth = setup()
    auth.reject = True
    assert client.get('/game/inventory/window?char_id=7&presentation=client').status_code == 401
    assert not api.calls
    auth.reject = False
    client.cookies.clear()
    response = client.get('/game/inventory/belt?char_id=7', follow_redirects=False)
    assert response.status_code == 303
    assert not api.calls


def test_missing_payload_is_failure_not_fake_empty_inventory():
    client, api, _auth = setup()
    api.value = None
    response = client.get('/game/inventory/window?char_id=7&presentation=client')
    assert response.status_code == 502
