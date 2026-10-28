"""Game themes are selected before paint and built independently of layout."""

import json
import os
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from codex_core.dev.static_compiler.css import CSSCompiler
from tools.css_token_inventory import inventory
from tools.game_preview import render as preview
from tools.game_preview.fixtures import PreviewFixture, build_fixture

ROOT = Path(__file__).resolve().parents[2]
CSS = ROOT / "src/frontend/static/css"
THEME_LINK = re.compile(r'<link[^>]+rel="stylesheet"[^>]+href="([^"]+)"')
DEFINITION = re.compile(r"(--[\w-]+)\s*:\s*([^;{}]+)")
REFERENCE = re.compile(r"var\(\s*(--[\w-]+)")


def _compiled(source: Path, output: Path) -> str:
    assert CSSCompiler().compile(source, output, remove_comments=True)
    return output.read_text(encoding="utf-8")


def _assert_acyclic(definitions, name, key, stack=()):
    assert key not in stack, f"{name}: variable cycle {' -> '.join((*stack, key))}"
    for reference in REFERENCE.findall(definitions[key]):
        _assert_acyclic(definitions, name, reference, (*stack, key))


def test_game_theme_and_layout_compile_as_separate_assets(tmp_path):
    config = json.loads((CSS / "compiler_config.json").read_text(encoding="utf-8"))
    assert config["css"].get("theme_bundle.css") == "theme.css"
    theme = _compiled(CSS / "theme_bundle.css", tmp_path / "theme.css")
    game = _compiled(CSS / "game_bundle.css", tmp_path / "game.css")
    assert "--col-bg-base:" in theme
    assert "--col-bg-base:" not in game
    assert "classic" not in theme.lower()
    assert "#303e4b" in theme.lower()
    assert "var(--col-" in game
    assert ".game-top-row" in game


def test_classic_remains_an_isolated_complete_theme_with_the_same_contract(tmp_path):
    themes = CSS / "game/themes"
    adventure = dict(DEFINITION.findall((themes / "adventure.css").read_text(encoding="utf-8")))
    classic = dict(DEFINITION.findall((themes / "classic.css").read_text(encoding="utf-8")))
    assert adventure.keys() == classic.keys()
    assert "--col-bg-base" in adventure
    assert adventure["--col-bg-base"] != classic["--col-bg-base"]
    for name, theme in (("adventure", adventure), ("classic", classic)):
        entry = tmp_path / f"{name}-entry.css"
        entry.write_text(
            f'@import url("{(CSS / "game/core/scales.css").as_posix()}");\n'
            f'@import url("{(themes / f"{name}.css").as_posix()}");\n',
            encoding="utf-8",
        )
        compiled = _compiled(entry, tmp_path / f"{name}.css")
        definitions = dict(DEFINITION.findall(compiled))
        for key, value in definitions.items():
            for reference in REFERENCE.findall(value):
                assert reference in definitions, f"{name}: {key} references undefined {reference}"

        for key in definitions:
            _assert_acyclic(definitions, name, key)
        assert all(key in definitions for key in theme)


def test_game_component_colors_are_theme_references(tmp_path):
    game = _compiled(CSS / "game_bundle.css", tmp_path / "game.css")
    # URLs contain content art rather than CSS palette values.
    declarations = re.sub(r"url\([^)]*\)", "", game)
    literals = re.findall(r"#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?)\(\s*[+.-]?\d", declarations)
    assert not literals, f"Hardcoded game palette remains outside theme: {literals[:20]}"


def test_classic_preserves_recorded_rgb_chrome_and_icon_filters():
    mapping = json.loads(
        (ROOT / "docs/ru/frontend/interface_design/game_theme_token_map.json").read_text(encoding="utf-8")
    )
    classic = dict(DEFINITION.findall((CSS / "game/themes/classic.css").read_text(encoding="utf-8")))
    for channel in mapping["rgb_channels"]:
        assert classic[channel["token"]].strip() == " ".join(map(str, channel["original_rgb"]))
    for original, token in mapping["texture_tokens"].items():
        assert classic[token].strip() == original
    for token, record in mapping["filter_tokens"].items():
        assert classic[token].strip() == record["classic"]


def test_adventure_rarity_names_remain_readable_on_panel_surfaces():
    adventure = dict(DEFINITION.findall((CSS / "game/themes/adventure.css").read_text(encoding="utf-8")))

    def luminance(hex_color):
        channels = [int(hex_color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
        return sum(value * weight for value, weight in zip(linear, (0.2126, 0.7152, 0.0722)))

    for tier in range(7):
        foreground = luminance(adventure[f"--r{tier}"].strip())
        for role in ("--col-bg-surface", "--col-bg-surface-light", "--col-bg-darker"):
            background = luminance(adventure[role].strip())
            assert (foreground + 0.05) / (background + 0.05) >= 4.5, (tier, role)


def test_game_required_tokens_are_defined_or_explicit_dynamic_content(tmp_path):
    theme = _compiled(CSS / "theme_bundle.css", tmp_path / "theme.css")
    game = _compiled(CSS / "game_bundle.css", tmp_path / "game.css")
    definitions = set(DEFINITION.findall(theme + game))
    defined_keys = {key for key, _ in definitions}
    required = set(re.findall(r"var\(\s*(--[\w-]+)\s*\)", game))
    dynamic_content = {
        "--city-service-stage-image",
        "--game-action-icon-url",
        "--game-menu-icon-url",
        "--inventory-item-icon-url",
        "--inventory-tooltip-icon-url",
        "--nav-icon-url",
        "--rift-edge-col",
        "--rift-edge-row",
        "--scenario-choice-icon-url",
        "--service-icon-url",
        "--service-marker-url",
    }
    assert required - defined_keys <= dynamic_content
    assert "var(--world-accent" not in game


def test_inventory_tracks_both_active_entries_and_disabled_classic_separately():
    data = inventory()
    assert data["build"]["entries"] == [
        "src/frontend/static/css/theme_bundle.css",
        "src/frontend/static/css/game_bundle.css",
    ]
    assert "src/frontend/static/css/game/themes/adventure.css" in data["css_source_order"]
    assert "src/frontend/static/css/game/themes/classic.css" not in data["css_source_order"]
    records = {record["path"]: record for record in data["files"]}
    assert records["src/frontend/static/css/game/themes/classic.css"]["css_role"] == "disabled-theme"
    assert records["src/frontend/static/css/game/core/tokens.css"]["css_role"] == "lab-compatibility-entry"
    assert not data["import_issues"]


def test_runtime_and_preview_select_adventure_and_load_theme_before_layout():
    source = (ROOT / "src/frontend/templates/game/base_game.html").read_text(encoding="utf-8")
    assert '<html lang="en" data-game-theme="adventure"' in source
    assert source.index('rel="stylesheet" href="/static/css/theme.css') < source.index(
        'rel="stylesheet" href="/static/css/game.css'
    )
    fixture = PreviewFixture(context={}, template="unused", title="Theme contract")
    html = preview._wrap_html(body="<div class='game-panel'>Panel</div>", fixture=fixture, template_name="unused")
    assert '<html lang="ru" data-game-theme="adventure">' in html
    links = THEME_LINK.findall(html)
    assert next(i for i, link in enumerate(links) if "/theme.css?" in link) < next(
        i for i, link in enumerate(links) if "/game.css?" in link
    )
    assert "classic" not in html.lower()


def test_runtime_cache_version_includes_theme_output(monkeypatch, tmp_path):
    from src.frontend.core import renderer

    theme = tmp_path / "css/theme.css"
    theme.parent.mkdir()
    theme.write_text(":root {}", encoding="utf-8")
    os.utime(theme, (2_000_000_001, 2_000_000_001))
    monkeypatch.setattr(renderer, "settings", SimpleNamespace(static_dir=tmp_path))
    monkeypatch.setattr(preview, "STATIC_DIR", tmp_path)
    assert renderer._static_version() == "2000000001"
    assert preview._static_version() == "2000000001"


@pytest.mark.parametrize(
    "name, marker",
    [
        ("arena", "arena-screen"),
        ("scenario", "scenario-stage"),
        ("services", "city-service-stage"),
        ("exploration", "mobile-encounter-layout"),
    ],
)
def test_additional_theme_preview_surfaces_render_offline(name, marker):
    fixture = build_fixture(f"theme/{name}")
    html = preview.render_preview(template_name=fixture.template, fixture=fixture)
    assert marker in html
    assert 'data-game-theme="adventure"' in html
    assert "PREVIEW" in fixture.description
