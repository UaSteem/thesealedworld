from game_ui_lab.app import render_index, resolve_asset


def test_retired_alpha_opens_current_scene_without_version_switch():
    html = render_index("alpha")
    assert html == render_index("hex")
    assert "/ui-static/game/scenes/combat/scene.js" in html
    assert '/?scene=alpha' not in html
    assert 'data-projection=' not in html


def test_new_scene_and_untrusted_version_cannot_load_arbitrary_scripts():
    html = render_index("hex")
    assert "/ui-static/game/scenes/combat/scene.js" in html
    assert "/ui-static/alpha/map-scene.js" not in html
    assert render_index("../../other.js") == html
