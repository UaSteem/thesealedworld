"""The main game shell exposes a local inventory without a second page/server."""
import json
import re

from game_ui_lab.app import LAB_ROOT, render_index, resolve_asset
from game_ui_lab.inventory_app import ART


def test_main_shell_contains_inventory_fixture_and_close_control():
    html = render_index()
    match = re.search(r'<script id="inventory-data" type="application/json">(.*?)</script>', html, re.S)
    assert match is not None
    inventory = json.loads(match.group(1))
    assert len(inventory['items']) == 6
    assert all(item['texture_url'].startswith('/inventory-art/') for item in inventory['items'])
    assert 'id="inventory-close"' in html
    assert '8880' not in html


def test_main_server_resolves_only_exact_fixture_art_urls():
    for url, path in ART.items():
        assert resolve_asset(url) == path
    for url in ('/inventory-art/unknown/image', '/inventory-art/../image',
                '/inventory-art/sword.basic.iron.t1/image/extra'):
        assert resolve_asset(url) is None


def test_resize_coordinator_belongs_to_shared_client_infrastructure():
    assert (LAB_ROOT / 'static/game/shared/resize.js').is_file()
