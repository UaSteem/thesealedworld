"""Read-only projection route regression; no Backend or game data access."""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient

from src.frontend.core.renderer import get_ui_renderer
from src.frontend.features.auth.dependencies.providers import get_frontend_auth_service
from src.frontend.game_features.character_status.dependencies import get_status_panel_service
from src.frontend.game_features.character_status.routes.fragments import router
from src.shared.schemas.character_status import CharacterActorCoreDTO


def test_character_client_projection_is_explicit_and_authenticated():
    calls = []
    actor = CharacterActorCoreDTO(key='game:ac:7', char_id=7, user_id='owner', state='exploration',
        bio={'name': 'Actual name'}, attributes={'strength': 0}, sessions={'private': 'excluded'},
        skills={'skill_swords': 3}, secret_extra='excluded')

    class Auth:
        async def require_current_user(self, request):
            calls.append('auth')

    class Service:
        async def get_panel(self, request, *, char_id):
            calls.append(char_id)
            return actor

    class UI:
        async def render(self, name, context):
            assert context['character_status'] is actor
            return HTMLResponse('legacy status')

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_frontend_auth_service] = Auth
    app.dependency_overrides[get_status_panel_service] = Service
    app.dependency_overrides[get_ui_renderer] = UI
    client = TestClient(app)
    response = client.get('/game/character-status/panel?char_id=7&presentation=client')
    assert response.status_code == 200
    projection = response.json()['character']
    assert projection['attributes'] == {'strength': 0}
    assert projection['skills'] == {'skill_swords': 3}
    assert not {'key', 'user_id', 'sessions', 'secret_extra'} & projection.keys()
    assert calls == ['auth', 7]
    assert client.get('/game/character-status/panel?char_id=7').text == 'legacy status'
