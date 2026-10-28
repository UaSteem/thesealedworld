"""Real session context carries only the public scenario presentation."""
from src.frontend.game_features.session.services.session_context_builder import SessionContextBuilder
from src.shared.enums import CoreDomain
from src.shared.schemas.scenario import ScenarioPayloadDTO


def test_scenario_session_context_carries_client_payload():
    builder = object.__new__(SessionContextBuilder)
    scenario = ScenarioPayloadDTO(node_key='node-real', text='До<br>После', extra_data={'scenario_session_id': 'hidden'})
    context = builder._context(state=CoreDomain.SCENARIO, char_id=7, transaction_id='t',
                               payload_type='scenario_screen', scenario=scenario)
    assert context['scenario_client_payload']['node_key'] == 'node-real'
    assert context['scenario_client_payload']['char_id'] == 7
    assert context['scenario_client_payload']['text'] == 'До\nПосле'
    assert 'scenario_session_id' not in context['scenario_client_payload']['extra_data']



def test_scenario_template_embeds_safe_json_and_exact_action_id():
    import json
    import re
    from pathlib import Path

    from jinja2 import Environment, FileSystemLoader, select_autoescape

    from src.frontend.game_features.scenario.view_models.client import build_scenario_client_payload
    from src.shared.schemas.scenario import ScenarioButtonDTO

    action_id = 'action-</script><script>bad</script>'
    scenario = ScenarioPayloadDTO(node_key='node-real', text='Рассказ',
        buttons=[ScenarioButtonDTO(label='Продолжить', action_id=action_id)],
        extra_data={'scenario_session_id': 'never-serialize-this'})
    env = Environment(loader=FileSystemLoader(Path('src/frontend/templates')), autoescape=select_autoescape())
    env.filters['scenario_rich_text'] = lambda text: text  # Unchanged legacy filter is outside this JSON boundary test.
    rendered = env.get_template('game/domains/scenario/viewport/main.html').render(
        scenario=scenario, char_id=7, scenario_client_payload=build_scenario_client_payload(scenario,7))
    script = re.search(r'<script type="application/json" data-game-client-scenario>(.*?)</script>', rendered, re.S).group(1)
    assert '</script>' not in script
    assert json.loads(script)['buttons'][0]['action_id'] == action_id
    assert 'never-serialize-this' not in script
    assert 'data-game-client-scenario-action="action-&lt;/script&gt;' in rendered
    assert 'hx-post="/game/scenario/step"' in rendered
