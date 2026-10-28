from src.frontend.game_features.exploration.view_models.client import build_exploration_client_payload
from src.shared.schemas.exploration import (
    EncounterDTO,
    GridButtonDTO,
    NavigationActionsDTO,
    NavigationGridDTO,
    WorldNavigationDTO,
)


def nav(**kwargs):
    return WorldNavigationDTO(loc_id='52_52', title='Город', description='Текст', grid=NavigationGridDTO(), **kwargs)


def test_commands_preserve_targets_deduplicate_and_do_not_infer_tile_moves():
    move = GridButtonDTO(id='n', label='Север', action='move:opaque_target:2.5', is_active=True)
    model = nav(navigation=NavigationActionsDTO(movement={'n': move}, services={
        'door': GridButtonDTO(id='door', label='Вход', action='service:svc_exact', is_active=True)}),
        city_map={'mode': 'viewport_7x7', 'rows': [[{'world_x': 51, 'world_y': 51,
            'tile_url': '/tile.webp', 'private': 'SECRET'}]], 'private': 'SECRET'})
    model.grid.n = move
    result = build_exploration_client_payload(model, char_id=7)
    assert len(result['actions']) == 2
    assert result['actions'][0]['params'] == {'char_id': 7, 'target_id': 'opaque_target'}
    assert result['actions'][0]['move_duration'] == 2.5
    assert result['actions'][1]['params'] == {'char_id': 7, 'service_id': 'svc_exact'}
    assert result['city_map']['rows'][0][0]['loc_id'] == '51_51'
    assert 'SECRET' not in str(result)
    assert result == build_exploration_client_payload(model, char_id=7)


def test_disabled_unknown_commands_and_center_look():
    model = nav()
    model.grid.n = GridButtonDTO(id='n', label='N', action='move:x:1', is_active=False)
    model.grid.nw = GridButtonDTO(id='people', label='Люди', action='interact:people', is_active=True)
    model.grid.center = GridButtonDTO(id='look', label='Осмотр', action='interact:look_around', is_active=True)
    result = build_exploration_client_payload(model, char_id=3)
    assert [a['enabled'] for a in result['actions']] == [False, False, True]
    assert result['actions'][1]['endpoint'] is None
    assert result['actions'][1]['tooltip'] == 'Сейчас недоступно'


def test_encounter_options_are_authoritative_without_fallback_attacks():
    model = nav(navigation=NavigationActionsDTO(movement={
        'move': GridButtonDTO(id='m', label='M', action='move:x:1', is_active=True)}))
    encounter = EncounterDTO(id='e', type='COMBAT', title='Enemy', description='Description',
        enemies=[{'name': 'Моб', 'hp_percent': 0, 'visual': {'private': 'SECRET'}}],
        options=[{'id': 'bypass', 'label': 'Обойти'}, {'id': 'inspect', 'label': 'Осмотреть'}],
        metadata={'bypass_chance_percent': 0, 'private': 'SECRET'})
    result = build_exploration_client_payload(model, encounter, char_id=7)
    assert len(result['actions']) == 2
    assert result['actions'][0]['params']['action'] == 'bypass'
    assert result['actions'][1]['endpoint'] is None
    assert result['encounter']['options'][1]['inspection_only'] is True
    assert result['encounter']['bypass_chance_percent'] == 0
    assert result['encounter']['enemies'][0]['hp_percent'] == 0
    assert 'SECRET' not in str(result)
    assert 'attack' not in str(result['actions'])


def test_local_map_zero_counts_description_edges_are_information_only():
    result = build_exploration_client_payload(nav(metadata={'private': 'SECRET'}), char_id=7,
        local_map={'char_id': 7, 'current_loc_id': '52_52', 'rows': [[{
            'loc_id': '52_52', 'x': 52, 'y': 52, 'dx': 0, 'dy': 0, 'description': '<b>Текст</b>',
            'corpse_count': 0, 'players_count': 0, 'private': 'SECRET',
            'edges': {'north': {'direction': 'north', 'state': 'open', 'target_loc_id': 'x', 'private': 'SECRET'}}}]]})
    cell = result['local_map']['rows'][0][0]
    assert cell['corpse_count'] == cell['players_count'] == 0
    assert cell['description'] == 'Текст'
    assert cell['edges']['north']['target_loc_id'] == 'x'
    assert result['actions'] == []
    assert 'SECRET' not in str(result)


def test_unsupported_payload_stays_legacy():
    assert build_exploration_client_payload({'title': 'List', 'items': []}) is None
    assert build_exploration_client_payload({'content': {'kind': 'list', 'data': {}}}) is None
    assert build_exploration_client_payload(None) is None
    assert build_exploration_client_payload(nav().model_dump(), char_id=2)['char_id'] == 2


def test_enemy_intel_preserves_only_available_information_and_finite_scalars():
    encounter = EncounterDTO(id='e', type='COMBAT', title='E', description='D', options=[],
        metadata={'bypass_chance_percent': float('nan')}, enemies=[{
            'name': 'Моб', 'description': '<b>Описание</b>', 'role': 'Guard', 'variant_key': 'v0',
            'visual': {'image_url': '/fallback.webp', 'private': 'SECRET'},
            'intel': {'danger_band': 0, 'private': 'SECRET', 'vitals': {
                'hp': {'label': 0, 'percent': 0, 'private': 'SECRET'},
                'energy': {'label': '0 / 10', 'percent': float('inf')},
                'concentration': {'label': '<b>Нет</b>', 'context': 'SECRET'},
                'private': {'label': 'SECRET'}}}}])
    result = build_exploration_client_payload(nav(), encounter, char_id=7)
    enemy = result['encounter']['enemies'][0]
    assert enemy['description'] == 'Описание'
    assert enemy['role'] == 'Guard' and enemy['variant_key'] == 'v0'
    assert enemy['image'] == '/fallback.webp'
    assert enemy['intel'] == {'danger_band': 0, 'vitals': {
        'hp': {'label': 0, 'percent': 0}, 'energy': {'label': '0 / 10'},
        'concentration': {'label': 'Нет'}}}
    assert 'bypass_chance_percent' not in result['encounter']
    assert 'SECRET' not in str(result)
    encounter.enemies[0].image = '/preferred.webp'
    assert build_exploration_client_payload(nav(), encounter)['encounter']['enemies'][0]['image'] == '/preferred.webp'
