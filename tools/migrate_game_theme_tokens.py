"""Recorded one-shot migration from literal game styles to theme parameters.

This changes source files only. It refuses to rerun after the contract exists.
The mapping records original RGB values and stable semantic shade names so new
shades can be appended later without renumbering existing parameters.
"""

from __future__ import annotations

import colorsys
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "src/frontend/static/css"
GAME = CSS / "game"
CONTRACT = ROOT / "docs/ru/frontend/interface_design/game_theme_token_map.json"
COLOR = re.compile(r"(?<![\w-])#[0-9a-fA-F]{3,8}\b|\brgba?\([^)]*\)")
PROPERTY = re.compile(r"(?:(?<=[{;\n])|^)\s*(?P<name>--[\w-]+|[a-zA-Z][\w-]*)\s*:")
PROTECTED = re.compile(r"/\*.*?\*/|url\((?:[^()\"']|\"[^\"]*\"|'[^']*')*\)|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'", re.S)
PALETTE = {
    "surface": "32 43 54", "panel": "48 62 75", "raised": "59 76 91",
    "inset": "36 50 62", "text": "241 233 219", "muted": "188 200 208",
    "accent": "223 185 128", "action": "116 209 200", "danger": "216 117 104",
    "success": "118 185 149", "energy": "100 182 209", "stamina": "156 186 113",
    "magic": "168 128 212", "neutral": "153 160 170",
}
FONT = {8: "--type-2xs", 9: "--type-xs", 10: "--type-sm", 11: "--type-caption", 12: "--type-base", 13: "--text-prose-compact", 14: "--type-md", 16: "--type-lg", 18: "--type-xl", 20: "--type-2xl", 22: "--game-avatar-placeholder-size", 24: "--type-3xl", 28: "--type-4xl", 32: "--type-5xl", 36: "--type-6xl", 40: "--type-7xl", 48: "--type-8xl", 64: "--type-display", 7: "--text-3xs"}
SPACE = {4: "--sp-1", 8: "--sp-2", 12: "--sp-3", 16: "--sp-4", 20: "--sp-5", 24: "--sp-6", 32: "--sp-8", 40: "--sp-10", 48: "--sp-12"}
WEIGHT = {400: "--weight-regular", 500: "--weight-medium", 600: "--weight-semibold", 700: "--weight-bold", 800: "--weight-heavy", 900: "--weight-black"}


def parse_color(value: str):
    if value.startswith("#"):
        text = value[1:]
        if len(text) in (3, 4):
            text = "".join(c * 2 for c in text)
        if len(text) not in (6, 8):
            return None
        rgb = tuple(int(text[i:i + 2], 16) for i in (0, 2, 4))
        return rgb, (int(text[6:8], 16) / 255 if len(text) == 8 else 1)
    parts = [part.strip() for part in value[value.index("(") + 1:-1].split(",")]
    if len(parts) not in (3, 4):
        return None
    try:
        rgb = tuple(round(float(part.rstrip("%")) * (2.55 if part.endswith("%") else 1)) for part in parts[:3])
        alpha = float(parts[3].rstrip("%")) / (100 if parts[3].endswith("%") else 1) if len(parts) == 4 else 1
        return rgb, alpha
    except ValueError:
        return None


def color_matches(source: str):
    protected = [(m.start(), m.end()) for m in PROTECTED.finditer(source)]
    for match in COLOR.finditer(source):
        if not any(a <= match.start() < b for a, b in protected):
            yield match


def family(rgb):
    hue, saturation, value = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))
    if value < 0.24:
        return "surface"
    if saturation < 0.16:
        return "text" if value > 0.75 else "neutral"
    hue *= 360
    if 20 <= hue < 70:
        return "text" if saturation < 0.47 and value > 0.65 else "accent"
    if hue < 20 or hue >= 340:
        return "danger"
    if hue < 165:
        return "success"
    if hue < 190:
        return "action"
    if hue < 250:
        return "energy"
    return "magic"


def value_spans(source: str):
    """Property values, respecting nested functions, quoted strings and comments."""
    protected = {m.start(): m.end() for m in PROTECTED.finditer(source)}
    index = 0
    while index < len(source):
        if index in protected:
            index = protected[index]
            continue
        match = PROPERTY.match(source, index)
        if not match:
            index += 1
            continue
        start = match.end()
        end = start
        depth = 0
        while end < len(source):
            if end in protected:
                end = protected[end]
                continue
            char = source[end]
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            elif depth == 0 and char in ";{}":
                break
            end += 1
        if end < len(source) and source[end] != "{":
            yield match.group("name"), start, end
        index = end + 1


def declaration_map(source):
    return {name: source[start:end].strip() for name, start, end in value_spans(source) if name.startswith("--")}


def css_set(values):
    return ":root {\n" + "".join(f"  {name}: {value};\n" for name, value in values.items()) + "}\n"


def main():
    if CONTRACT.exists():
        raise SystemExit("Migration contract already exists; do not rerun against migrated sources")
    files = sorted(GAME.rglob("*.css"))
    sources = {p: p.read_text(encoding="utf-8") for p in files}
    original_core = sources[GAME / "core/tokens.css"]
    originals = ROOT / "tmp/game_theme_migration/originals"
    for p in sources:
        target = originals / p.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(p.read_bytes())
    groups = defaultdict(set)
    for source in sources.values():
        for match in color_matches(source):
            parsed = parse_color(match.group())
            if parsed:
                groups[family(parsed[0])].add(parsed[0])
    rgb_tokens = {}
    for group, colors in sorted(groups.items()):
        for index, rgb in enumerate(sorted(colors, key=lambda rgb: (sum(rgb), rgb)), 1):
            rgb_tokens[rgb] = f"--tone-{group}-{index:03}-rgb"

    def color_value(literal):
        parsed = parse_color(literal)
        if not parsed or parsed[0] not in rgb_tokens:
            return literal
        rgb, alpha = parsed
        token = rgb_tokens[rgb]
        return f"rgb(var({token})" + (f" / {alpha:g})" if alpha != 1 else ")")

    old = declaration_map(original_core)
    scales = {}
    classic = {}
    for name, value in old.items():
        if name.startswith(("--col-", "--r")) or name.startswith(("--font-", "--shadow-", "--game-")) and (list(color_matches(value)) or name.startswith("--font-")):
            classic[name] = value
        else:
            scales[name] = value
    # Missing shared family aliases were previously inherited from other surfaces.
    classic.update({"--font-mono": "'JetBrains Mono', 'Courier New', monospace", "--font-text": "'EB Garamond', Georgia, serif", "--font-display": "'EB Garamond', Georgia, serif"})
    for rgb, name in rgb_tokens.items():
        classic[name] = " ".join(map(str, rgb))
    for size, name in FONT.items():
        scales.setdefault(name, f"{size}px")
    for size in range(1, 49):
        SPACE.setdefault(size, f"--space-{size}")
        scales.setdefault(SPACE[size], f"{size}px")
    for weight, name in WEIGHT.items():
        scales[name] = str(weight)
    scales.update({"--radius-none": "0", "--radius-sm": "2px", "--radius-md": "4px", "--radius-lg": "8px", "--radius-pill": "999px", "--border-hairline": "1px"})
    adventure = dict(classic)
    adventure.update({
        "--col-bg": "#202b36", "--col-bg-base": "#202b36", "--col-surface": "#303e4b", "--col-bg-surface": "#303e4b", "--col-bg-surface-light": "#3b4c5b", "--col-bg-darker": "#24323e",
        "--col-parchment": "#dfb980", "--col-parchment-dim": "rgb(223 185 128 / .6)", "--col-accent": "#dfb980", "--col-accent-dim": "rgb(223 185 128 / .4)",
        "--col-text-primary": "#f1e9db", "--col-text-secondary": "#cbd3d8", "--col-text-world": "#f1e9db", "--col-text-dim": "#bcc8d0",
        "--col-border": "#617382", "--col-border-strong": "#bca57e", "--col-membrane": "rgb(223 185 128 / .06)",
        "--col-danger": "#d87568", "--col-energy": "#64b6d1", "--col-stamina": "#9cba71", "--col-success": "#76b995", "--col-info": "#64b6d1", "--col-warning": "#dfb980", "--col-psi": "#a880d4",
        "--game-shell-surface": "#303e4b", "--game-panel-surface": "#303e4b", "--game-drawer-surface": "#293946", "--game-scene-surface": "rgb(32 43 54 / .72)",
        "--font-ui": 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif', "--font-text": 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    })
    for role, value in PALETTE.items():
        classic[f"--theme-{role}-rgb"] = value
        adventure[f"--theme-{role}-rgb"] = value
    for rgb, name in rgb_tokens.items():
        adventure[name] = f"var(--theme-{family(rgb)}-rgb)"
    # Existing glows retain geometry and reference the same palette channels.
    for name, value in classic.items():
        if name.startswith("--shadow-"):
            adventure[name] = COLOR.sub(lambda m: color_value(m.group()), value)
    additions = {
        "--game-avatar-fallback-light": ("#1a1a20", "#3b4c5b"), "--game-avatar-fallback-dark": ("#0a0a0c", "#24323e"),
        "--game-risk-safe": ("rgb(70 238 142)", "#76b995"), "--game-risk-low": ("rgb(220 184 48)", "#dfb980"), "--game-risk-medium": ("rgb(230 106 28)", "#dfb980"), "--game-risk-danger": ("rgb(255 58 42)", "#d87568"),
    }
    for name, (before, after) in additions.items():
        classic[name], adventure[name] = before, after
    textures = {}
    replacements = {}
    for p, source in sources.items():
        if p == GAME / "core/tokens.css":
            continue
        edits = []
        for prop, start, end in value_spans(source):
            value = source[start:end]
            changed = value
            for match in reversed(list(color_matches(value))):
                replacement = color_value(match.group())
                changed = changed[:match.start()] + replacement + changed[match.end():]
                replacements[match.group()] = replacement
            if prop in ("font-family",) and "var(" not in value and value.strip() != "inherit":
                changed = " var(--font-world)" if "Garamond" in value else " var(--font-mono)"
            if prop in ("font-size", "font"):
                changed = re.sub(r"(?<![\w-])(\d+)px\b", lambda m: f"var({FONT[int(m.group(1))]})" if int(m.group(1)) in FONT else m.group(), changed)
            if prop == "font-weight" and value.strip().isdigit():
                weight = int(value.strip())
                if weight in WEIGHT:
                    changed = f" var({WEIGHT[weight]})"
            if prop == "font":
                changed = re.sub(r"^(\s*)(400|500|600|700|800|900)\b", lambda m: m.group(1) + f"var({WEIGHT[int(m.group(2))]})", changed)
            if prop in ("padding", "padding-top", "padding-right", "padding-bottom", "padding-left", "margin", "margin-top", "margin-right", "margin-bottom", "margin-left", "gap", "row-gap", "column-gap"):
                # Geometry inside functions and negative positioning offsets stays local.
                changed = re.sub(r"(?<![\w.-])(\d+)px\b", lambda m: f"var({SPACE[int(m.group(1))]})" if int(m.group(1)) in SPACE else m.group(), changed)
            if prop == "border-radius":
                radii = {2: "--radius-sm", 4: "--radius-md", 8: "--radius-lg", 999: "--radius-pill"}
                changed = re.sub(r"(?<![\w.-])(2|4|8|999)px\b", lambda m, radii=radii: f"var({radii[int(m.group(1))]})", changed)
            # Decorative chrome is theme-owned; item art, scenes, icons and maps remain content.
            if prop.startswith("background") or prop.startswith("--"):
                for url in re.findall(r"url\((?:[^()\"']|\"[^\"]*\"|'[^']*')*\)", changed):
                    if "/ui/textures/" in url or "parchment_dull.webp" in url:
                        if url not in textures:
                            textures[url] = f"--texture-chrome-{len(textures) + 1:02}"
                        changed = changed.replace(url, f"var({textures[url]})")
            changed = re.sub(r"\bwhite\b", "var(--col-highlight)", changed)
            if changed != value:
                edits.append((start, end, changed))
        for start, end, value in reversed(edits):
            source = source[:start] + value + source[end:]
        p.write_text(source, encoding="utf-8")
    classic["--col-highlight"], adventure["--col-highlight"] = "#ffffff", "#f1e9db"
    for url, name in textures.items():
        classic[name] = url
        adventure[name] = "linear-gradient(180deg, rgb(59 76 91 / .6), rgb(36 50 62 / .6))"
    themes = GAME / "themes"
    themes.mkdir(exist_ok=True)
    (GAME / "core/scales.css").write_text("/* Shared game scales and aliases; independent of palette. */\n" + css_set(scales), encoding="utf-8")
    (themes / "classic.css").write_text("/* Disabled legacy theme. Only isolated preview may load it. */\n" + css_set(classic), encoding="utf-8")
    (themes / "adventure.css").write_text("/* Warm Adventure: default game palette, shared by DOM overlays. */\n" + css_set(adventure), encoding="utf-8")
    (GAME / "core/tokens.css").write_text('/* Compatibility entry for standalone Rift Lab. Runtime uses theme_bundle.css. */\n@import url("scales.css");\n@import url("../themes/classic.css");\n', encoding="utf-8")
    (CSS / "theme_bundle.css").write_text('@import url("game/core/scales.css");\n@import url("game/themes/adventure.css");\n', encoding="utf-8")
    bundle = CSS / "game_bundle.css"
    bundle.write_text(bundle.read_text(encoding="utf-8").replace('@import url("game/core/tokens.css");\n', ''), encoding="utf-8")
    CONTRACT.write_text(json.dumps({"version": 1, "literal_to_css": replacements, "rgb_channels": [{"original_rgb": list(rgb), "token": token, "family": family(rgb)} for rgb, token in rgb_tokens.items()], "texture_tokens": textures, "original_source_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256((originals / p.relative_to(ROOT)).read_bytes()).hexdigest() for p in sources}, "note": "Stable family shade identifiers preserve exact legacy RGB values. Never renumber; append future shades. Usage alpha is structural intensity; themes supply channels."}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Migrated {len(sources) - 1} source files, {len(rgb_tokens)} RGB shade parameters, {len(textures)} chrome textures")


if __name__ == "__main__":
    main()
