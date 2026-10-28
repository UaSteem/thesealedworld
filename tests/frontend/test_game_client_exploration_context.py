"""Only server-supported navigation gets a new renderer; unknown content keeps legacy HTML."""
from src.frontend.game_features.session.services.session_context_builder import SessionContextBuilder
from src.shared.enums import CoreDomain
from src.shared.schemas.exploration import GridButtonDTO, NavigationGridDTO, WorldNavigationDTO


def test_session_context_embeds_only_supported_exploration():
    builder = object.__new__(SessionContextBuilder)
    navigation = WorldNavigationDTO(loc_id='52_52', title='Площадь', description='Место',
        grid=NavigationGridDTO(n=GridButtonDTO(id='north',label='Север',action='move:52_51:1',is_active=True)))
    context = builder._context(state=CoreDomain.EXPLORATION, char_id=7, transaction_id='t',
                               payload_type='exploration_navigation', exploration=navigation)
    assert context['exploration_client_payload']['loc_id'] == '52_52'
    assert context['exploration_client_payload']['actions'][0]['params'] == {'char_id': 7, 'target_id': '52_51'}
    unsupported = builder._context(state=CoreDomain.EXPLORATION, char_id=7, transaction_id='t',
                                  payload_type='unknown_existing_screen', exploration={'items': []})
    assert unsupported['exploration_client_payload'] is None
