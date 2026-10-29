import pytest
from game_ui_lab.app import LAB_ROOT, STATIC_ROOT, render_index, resolve_asset


def test_shell_is_isolated_and_uses_shared_adventure_assets():
    html = render_index()
    assert 'data-game-theme="adventure"' in html
    assert "/static/css/theme.css" in html
    assert "/static/js/vendor/phaser.min.js" in html
    assert 'id="combat-stage"' in html
    assert "Ada Guard" in html
    assert "/game/combat/action" not in html
    assert "/api/" not in html
    source = (LAB_ROOT / "app.py").read_text(encoding="utf-8")
    assert "from rift_lab" not in source
    assert "from src." not in source


def test_assets_resolve_only_inside_public_roots():
    assert resolve_asset("/ui-static/game/core/boot.js") == LAB_ROOT / "static/game/core/boot.js"
    assert resolve_asset("/ui-static/scene.js") is None
    assert resolve_asset("/static/css/theme.css") == STATIC_ROOT / "css/theme.css"


@pytest.mark.parametrize(
    "request_path",
    [
        "/ui-static/../app.py",
        "/ui-static/%2e%2e/app.py",
        "/ui-static/%252e%252e/app.py",
        "/static/../../../AGENTS.md",
        "/ui-static/..%5capp.py",
        "/ui-static/%00bad",
        "/app.py",
    ],
)
def test_asset_traversal_is_rejected(request_path):
    assert resolve_asset(request_path) is None
