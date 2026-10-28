from src.frontend.game_features.city_services.view_models.client import build_places_client_payload


def arena(**values):
    return {'screen': 'mode_menu', 'title': 'Арена', 'description': 'Зал', 'buttons': [], **values}


def city(**values):
    return {'service_id': 'svc_tavern_hub', 'service_type': 'tavern', 'screen': 'main',
            'title': 'Двор', 'description': 'Описание', 'buttons': [], **values}


def test_arena_commands_preserve_confirmation_without_modal_and_hide_mock_modes():
    result = build_places_client_payload(char_id=7, arena=arena(buttons=[
        {'text': 'Войти', 'action': 'check_combat_ready', 'mode': 'one_vs_one',
         'value': {'arena_session_id': 'exact', 'confirm': True, 'private': 'SECRET'}},
        {'text': 'Группа', 'action': 'menu_mode', 'mode': 'group'},
        {'text': 'Нет', 'action': 'start_battle'}], metadata={'group_lobby': {'private': 'SECRET'}}))
    first, group, unknown = result['actions']
    assert first['params'] == {'char_id': 7, 'action': 'check_combat_ready', 'mode': 'one_vs_one',
                               'arena_session_id': 'exact', 'confirm': True}
    assert group['enabled'] is unknown['enabled'] is False
    assert 'modal' not in first['params'] and 'SECRET' not in str(result)


def test_arena_poll_conditions_values_and_zero_details():
    result = build_places_client_payload(char_id=7, arena=arena(screen='combat_pending', mode='one_vs_one',
        arena_session_id='real', poll_after_ms=50, gs=0, wait_time_sec=0,
        metadata={'polling': True, 'queue_waiting_count': 0}))
    poll = next(a for a in result['actions'] if a.get('hidden_poll'))
    assert result['poll'] == {'id': poll['id'], 'interval_ms': 250}
    assert poll['params'] == {'char_id': 7, 'action': 'check_combat_ready', 'mode': 'one_vs_one', 'arena_session_id': 'real'}
    assert any(d['value'] == 0 for d in result['details'])
    assert build_places_client_payload(arena=arena(screen='combat_pending', arena_session_id='x'))['poll'] is None
    assert build_places_client_payload(arena=arena(screen='searching'))['poll'] is not None


def test_tavern_buttons_room_and_portal_npc_are_server_backed():
    result = build_places_client_payload(char_id=5, city_service=city(screen='section', section_id='room',
        location_id='53_53', background_url='/tavern.webp', metadata={'room': {'is_owned': False, 'can_rest': False,
            'private': 'SECRET'}, 'common_hall': {'occupants_count': 0, 'private': 'SECRET'}}, buttons=[
                {'label': 'Отдых', 'action': 'rest', 'section_id': 'room', 'is_disabled': True}]))
    assert result['background_url'] == '/tavern.webp'
    assert result['actions'][0]['enabled'] is False
    assert result['actions'][0]['params'] == {'char_id': 5, 'action': 'rest', 'service_id': 'svc_tavern_hub',
        'screen': 'section', 'section_id': 'room', 'location_id': '53_53'}
    assert 'SECRET' not in str(result)
    portal = build_places_client_payload(char_id=5, city_service=city(service_id='svc_portal_hub',
        service_type='portal', background_url='/portal.webp', metadata={'npc': {'name': 'Оценщик',
            'role': 'Гид', 'portrait_url': '/npc.webp', 'section_id': 'contact', 'private': 'SECRET'}}))
    npc_action = next(a for a in portal['actions'] if a['id'] == portal['npc']['action_id'])
    assert npc_action['params']['action'] == 'start_dialogue'
    assert npc_action['params']['section_id'] == 'contact'
    assert portal['background_url'] == '/portal.webp'
    assert 'SECRET' not in str(portal)


def test_unavailable_uses_no_mock_board_and_known_art_only():
    result = build_places_client_payload(arena=arena(mode='group', metadata={'group_lobby': {'SECRET': 1}}))
    assert result['unavailable'] and 'SECRET' not in str(result)
    assert result['background_url'].endswith('/arena-hall.webp')
    market = build_places_client_payload(city_service=city(service_type='market', service_id='svc_market_hub'))
    assert market['background_url'].endswith('/trading-quarter.webp')
    unknown = build_places_client_payload(city_service=city(service_type='unknown', background_url='/actual.webp'))
    assert unknown['background_url'] == '/actual.webp'
    assert build_places_client_payload(arena={'items': []}) is None
    assert build_places_client_payload() is None


def _render_places(template_name, **context):
    from pathlib import Path

    from jinja2 import Environment, FileSystemLoader, select_autoescape

    environment = Environment(loader=FileSystemLoader(Path('src/frontend/templates')),
                              autoescape=select_autoescape(['html']))
    return environment.get_template(template_name).render(char_id=7, nav=None, **context)


def _transport_commands(html):
    import json
    from html.parser import HTMLParser

    class Commands(HTMLParser):
        def __init__(self):
            super().__init__()
            self.commands = {}

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == 'button' and 'data-game-client-places-action' in attrs:
                self.commands[attrs['data-game-client-places-action']] = {
                    'endpoint': attrs['hx-post'], 'params': json.loads(attrs['hx-vals'])}

    parser = Commands()
    parser.feed(html)
    return parser.commands


def test_actual_arena_jinja_has_one_poll_transport_and_safe_json():
    import json
    import re

    from src.shared.schemas.arena import ArenaUIPayloadDTO

    for screen, polling, expected in [('searching', False, 'check_match'),
                                      ('combat_pending', True, 'check_combat_ready')]:
        model = ArenaUIPayloadDTO.model_validate(arena(screen=screen, mode='one_vs_one',
            title='</script><script>unsafe()</script>', arena_session_id='session-exact',
            metadata={'polling': polling}, buttons=[]))
        projection = build_places_client_payload(char_id=7, arena=model)
        html = _render_places('game/domains/arena/viewport/main.html', arena=model,
                              places_client_payload=projection)
        assert 'hx-trigger="every ' not in html
        script = re.search(r'<script type="application/json" data-game-client-places>(.*?)</script>',
                           html, flags=re.DOTALL).group(1)
        assert '<script>' not in script
        decoded = json.loads(script)
        assert decoded == projection
        poll = next(item for item in projection['actions'] if item.get('hidden_poll'))
        exact = {'char_id': 7, 'action': expected, 'mode': 'one_vs_one'}
        if screen == 'combat_pending':
            exact['arena_session_id'] = 'session-exact'
        assert _transport_commands(html)[poll['id']] == {'endpoint': '/game/arena/action', 'params': exact}
        assert 'confirm' not in exact and 'modal' not in exact


def test_actual_city_jinja_keeps_independent_npc_command():
    from src.shared.schemas.city_services import CityServiceUIPayloadDTO

    model = CityServiceUIPayloadDTO.model_validate(city(service_id='svc_portal_hub', service_type='portal',
        location_id='52_52', metadata={'npc': {'name': 'Оценщик', 'section_id': 'portal_contact'}},
        buttons=[{'label': 'Выйти', 'action': 'leave'}]))
    projection = build_places_client_payload(char_id=7, city_service=model)
    html = _render_places('game/domains/city_services/viewport/main.html', city_service=model,
                          places_client_payload=projection)
    assert _transport_commands(html)[projection['npc']['action_id']] == {
        'endpoint': '/game/city-services/action', 'params': {'char_id': 7, 'action': 'start_dialogue',
            'service_id': 'svc_portal_hub', 'screen': 'main', 'section_id': 'portal_contact', 'location_id': '52_52'}}


def test_places_art_manifest_matches_actual_runtime_files():
    import hashlib
    import json
    from pathlib import Path

    root = Path('src/frontend/static/images/game-client/places')
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8-sig'))
    expected = {'arena-hall.webp', 'administrative-quarter.webp', 'trading-quarter.webp', 'crafting-quarter.webp'}
    assert {item['file'] for item in manifest['images']} == expected
    for item in manifest['images']:
        content = (root / item['file']).read_bytes()
        assert len(content) == item['bytes']
        assert hashlib.sha256(content).hexdigest() == item['sha256']


def test_migrated_group_screen_never_renders_mock_rows_even_in_hidden_transport():
    from src.shared.schemas.arena import ArenaUIPayloadDTO

    model = ArenaUIPayloadDTO.model_validate(arena(mode='group', metadata={'group_lobby': {
        'tabs': [{'id': 'current', 'items': [{'name': 'MOCK_ROW_SENTINEL'}]}]}}))
    projection = build_places_client_payload(char_id=7, arena=model)
    html = _render_places('game/domains/arena/viewport/main.html', arena=model, places_client_payload=projection)
    assert 'MOCK_ROW_SENTINEL' not in html
    assert projection['unavailable']


def test_npc_duplicate_command_preserves_server_disabled_state():
    result = build_places_client_payload(char_id=7, city_service=city(section_id='bar',
        metadata={'npc': {'name': 'Хозяин', 'section_id': 'bar'}},
        buttons=[{'label': 'Разговор', 'action': 'start_dialogue', 'section_id': 'bar', 'is_disabled': True}]))
    assert len(result['actions']) == 1
    assert result['actions'][0]['enabled'] is False
    assert result['npc']['action_id'] == result['actions'][0]['id']
