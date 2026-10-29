"""The Lab exposes one reusable client shell and a registered combat scene."""
import json

from game_ui_lab.app import LAB_ROOT, render_index, resolve_asset
from game_ui_lab.inventory_app import render_inventory


def test_game_entrypoint_loads_core_then_scene_then_boot():
    html = render_index()
    scripts = [
        '/ui-static/game/core/assets.js',
        '/ui-static/game/shared/hex-layout.js',
        '/ui-static/game/ui/combat-controls.js',
        '/ui-static/game/ui/target-inspector.js',
        '/ui-static/game/scenes/combat/scene.js',
        '/ui-static/game/core/boot.js',
    ]
    positions = [html.index(script) for script in scripts]
    assert positions == sorted(positions)
    for script in scripts:
        assert resolve_asset(script) is not None
    for retired in ('/ui-static/hex-battle-scene.js', '/ui-static/actor-details.js',
                    '/ui-static/combat-hud.js', '/ui-static/hud-layout.js'):
        assert retired not in html


def test_combat_and_inventory_use_same_shell_modules():
    combat, inventory = render_index(), render_inventory()
    for path in ('game/shell/shell.css', 'game/shell/character.css',
                 'game/shell/chat.js'):
        assert f'/ui-static/{path}' in combat
        assert f'/ui-static/{path}' in inventory
        assert resolve_asset(f'/ui-static/{path}') is not None


def test_main_chat_overlays_field_while_standalone_inventory_keeps_its_resize_stand():
    combat, inventory = render_index(), render_inventory()
    assert '/ui-static/game/shell/overlay-chat.js' in combat
    assert 'id="chat-divider"' not in combat
    assert '/ui-static/game/shell/chat-layout.js' in inventory


def test_active_asset_catalog_resolves_all_groups_without_old_sheet():
    catalog = json.loads((LAB_ROOT / 'static/game/assets/catalog.json').read_text())
    assert catalog['schema_version'] == 1
    assert {entry['group'] for entry in catalog['assets']} == {
        'combat-core', 'combat-controls', 'combat-inspector',
    }
    assert len({entry['key'] for entry in catalog['assets']}) == len(catalog['assets'])
    for entry in catalog['assets']:
        assert resolve_asset(entry['url']) is not None
        assert 'hex-sheet-bars-runes' not in entry['url']


def test_inventory_scene_has_its_own_module_in_client_tree():
    html = render_inventory()
    assert '/ui-static/game/scenes/inventory/boot.js' in html
    assert '/ui-static/game/scenes/inventory/inventory.css' in html
    assert resolve_asset('/ui-static/game/scenes/inventory/scene.js') is not None
    assert '/ui-static/inventory/' not in html
