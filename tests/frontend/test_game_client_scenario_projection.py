"""The canvas receives a presentation projection, never raw scenario context."""
import copy

from src.frontend.game_features.scenario.view_models.client import build_scenario_client_payload
from src.shared.schemas.scenario import ScenarioButtonDTO, ScenarioPayloadDTO


def test_scenario_projection_omits_context_and_preserves_authoritative_values():
    scenario = ScenarioPayloadDTO(
        node_key='real-node', text='Actual text', buttons=[
            ScenarioButtonDTO(action_id='opaque:second', label='Второй'),
            ScenarioButtonDTO(action_id='opaque:first', label='Первый', icon='question'),
        ], extra_data={
            'quest_title': 'Квест', 'background_url': '/static/scenario.webp',
            'npc_reputation': 0, 'npc_affinity': False,
            'reputation': {'npc': 0, 'faction': False, 'private': 'SECRET'},
            'scenario_session_id': 'SECRET', 'visited_nodes': ['SECRET'], 'return_context': {'SECRET': 1},
            'ui': {'private': 'SECRET'}, 'arbitrary_quest_counter': 'SECRET',
            'rewards': [{'label': 'Монеты', 'value': 0, 'private': 'SECRET'}, {'private': 'SECRET'}],
            'right_panel': {'id': 'SECRET', 'widgets': [{
                'type': 'meter_list', 'title': 'Профиль', 'visible': False,
                'items': [{'label': 'Сила', 'value': 0, 'display_value': '17%', 'percent': 17,
                           'catalog': 'attributes', 'catalog_key': 'strength', 'private': 'SECRET'}],
                'data': {'text': 'Данные', 'private': 'SECRET', 'max': 20}, 'private': 'SECRET',
            }]},
        }, ui={'private': 'SECRET'},
    )
    original = copy.deepcopy(scenario.model_dump())
    result = build_scenario_client_payload(scenario, char_id=7)
    assert result['char_id'] == 7
    assert 'SECRET' not in str(result)
    assert 'ui' not in result
    assert result['extra_data']['npc_reputation'] == 0
    assert result['extra_data']['npc_affinity'] is False
    assert result['extra_data']['reputation'] == {'npc': 0, 'faction': False}
    assert result['extra_data']['rewards'] == [{'label': 'Монеты', 'value': 0}]
    widget = result['extra_data']['right_panel']['widgets'][0]
    assert widget['visible'] is False
    assert widget['items'][0]['percent'] == 17
    assert widget['items'][0]['display_value'] == '17%'
    assert widget['data'] == {'text': 'Данные'}
    assert [button['action_id'] for button in result['buttons']] == ['opaque:second', 'opaque:first']
    assert [button['label'] for button in result['buttons']] == ['Второй', 'Первый']
    assert scenario.model_dump() == original


def test_scenario_projection_converts_formatter_markup_without_active_content():
    scenario = ScenarioPayloadDTO(node_key='node', text=(
        'Начало<br><br><div class="whisper">Голос &amp; ответ</div>'
        '<span style="color: var(--col-accent);">Золото</span>'
        '<script>SECRET_SCRIPT</script><style>SECRET_STYLE</style>'
        '<!--SECRET_COMMENT--><img src=x onerror="SECRET_EVENT">'
        '&lt;буквальный текст&gt;'
    ), buttons=[ScenarioButtonDTO(action_id='opaque<id>', label='<span>Ответ &amp; выбор</span>')],
        system_messages=['<b>Сообщение</b>'], status_bar=['<script>SECRET</script>Время 0'])
    result = build_scenario_client_payload(scenario, 7)
    assert 'Начало\n\n' in result['text']
    assert 'Голос & ответ' in result['text']
    assert 'Золото' in result['text']
    assert '<буквальный текст>' in result['text']
    assert 'SECRET' not in result['text']
    assert '<span' not in result['text'] and '<div' not in result['text']
    assert result['buttons'] == [{'action_id': 'opaque<id>', 'label': 'Ответ & выбор', 'icon': None}]
    assert result['system_messages'] == ['Сообщение']
    assert result['status_bar'] == ['Время 0']


def test_scenario_projection_handles_absent_metadata_without_inventing_rows():
    scenario = ScenarioPayloadDTO(node_key='empty', text='', is_terminal=True)
    result = build_scenario_client_payload(scenario, 9)
    assert result['extra_data'] == {}
    assert result['buttons'] == []
    assert result['system_messages'] == []
    assert result['status_bar'] == []
    assert result['is_terminal'] is True
