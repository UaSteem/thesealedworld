from types import SimpleNamespace

from src.frontend.game_features.session.services.response_director import ResponseDirector
from src.frontend.game_features.session.services.session_context_builder import SessionContextBuilder
from src.shared.enums import CoreDomain
from src.shared.schemas.arena import ArenaUIPayloadDTO
from src.shared.schemas.city_services import CityServiceUIPayloadDTO


def test_places_projection_survives_initial_and_partial_contexts():
    arena = ArenaUIPayloadDTO(screen='main_menu', title='Арена', description='Зал')
    city = CityServiceUIPayloadDTO(service_id='real', service_type='portal', screen='main', title='Портал', description='Вход')
    builder = object.__new__(SessionContextBuilder)
    context = builder._context(state=CoreDomain.ARENA, char_id=7, transaction_id='t', payload_type='arena', arena=arena)
    assert context['places_client_payload']['char_id'] == 7
    assert context['places_client_payload']['kind'] == 'arena'
    director = ResponseDirector(context_builder=builder)
    _, context = director._resolve_arena(SimpleNamespace(payload=arena, payload_type='arena'), 7)
    assert context['places_client_payload']['title'] == 'Арена'
    _, context = director._resolve_city_service(SimpleNamespace(payload=city, payload_type='city_service'), 7)
    assert context['places_client_payload']['kind'] == 'service'
