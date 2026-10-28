"""Inventory game CSS sources without compiling or changing runtime assets.

Run from any directory: python tools/css_token_inventory.py [--check].
This is a lexical migration aid, not a CSS parser or computed-style validator.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "src/frontend/static/css"
REPORT = ROOT / "docs/ru/frontend/interface_design/game_css_token_inventory"
IMPORT = re.compile(r"@import\s+(?:url\(\s*)?[\"']([^\"']+)[\"']\s*\)?([^;]*);", re.I)
DEFINITION = re.compile(r"(?<![\w-])(--[\w-]+)\s*:\s*([^;{}]+)")
REFERENCE = re.compile(r"var\(\s*(--[\w-]+)")
COLOR = re.compile(r"(?<![\w-])#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?)\([^)]*\)")
LITERAL_COLOR = re.compile(r"(?<![\w-])#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?)\(\s*[+.-]?\d[^)]*\)")
SIZE = re.compile(r"(?<![\w-])-?(?:\d*\.)?\d+(?:px|rem|em|vh|vw|vmin|vmax)\b")
FONT = re.compile(r"\bfont(?:-family|-size|-weight|-style|-stretch|-variant)?\s*:\s*[^;{}\n]+")
MOBILE = re.compile(
    r"@media[^{}]+|\b(?:matchMedia|innerWidth|outerWidth|isMobile|isTouch|pointer:\s*coarse|hover:\s*none)\b", re.I
)


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def uncomment(source: str) -> str:
    """Retain offsets and line numbers while excluding CSS/JS block comments."""
    return re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m[0]), source, flags=re.S)


def locations(pattern: re.Pattern[str], source: str) -> list[dict]:
    return [
        {
            "line": source.count("\n", 0, m.start()) + 1,
            "value": m[0],
            "line_text": source[
                source.rfind("\n", 0, m.start()) + 1 : source.find("\n", m.start())
                if "\n" in source[m.start() :]
                else len(source)
            ].strip()[:240],
        }
        for m in pattern.finditer(source)
    ]


def selector_candidates(source: str) -> list[dict]:
    """Index lexical block headers; nested at-rules are not computed selectors."""
    result = []
    for match in re.finditer(r"([^{}]+)\{", source):
        header = match[1].rsplit(";", 1)[-1].strip()
        if header and not header.startswith("@"):
            start = match.start(1) + match[1].rfind(header)
            result.append({"line": source.count("\n", 0, start) + 1, "selector": header})
    return result


def inventory() -> dict:
    config = json.loads((CSS / "compiler_config.json").read_text(encoding="utf-8"))
    entries = [CSS / "theme_bundle.css", CSS / "game_bundle.css"]
    ordered: list[Path] = []
    edges: list[dict] = []
    issues: list[str] = []

    def visit(path: Path, stack: tuple[Path, ...] = ()) -> None:
        path = path.resolve()
        if path in stack:
            issues.append("Import cycle: " + " -> ".join(relative(p) for p in (*stack, path)))
            return
        if path in ordered:
            return
        if not path.is_file():
            issues.append("Missing import: " + relative(path))
            return
        ordered.append(path)
        source = uncomment(path.read_text(encoding="utf-8"))
        for match in IMPORT.finditer(source):
            target, condition = match.groups()
            edge = {
                "from": relative(path),
                "line": source.count("\n", 0, match.start()) + 1,
                "target": target,
                "condition": condition.strip(),
            }
            if target.startswith(("https:", "http:", "//", "data:")):
                edge["external"] = True
            else:
                child = (path.parent / target).resolve()
                edge["resolved"] = relative(child)
                visit(child, (*stack, path))
            edges.append(edge)

    for entry in entries:
        visit(entry)
    game_files = set((CSS / "game").rglob("*.css"))
    files = set(ordered) | game_files
    files |= set((ROOT / "src/frontend/templates/game").rglob("*.html"))
    files |= set((ROOT / "src/frontend/static/js/game").rglob("*.js"))
    js_dir = ROOT / "src/frontend/static/js"
    for bundle in ("game.js",):
        for source in config.get("js", {}).get(bundle, {}).get("sources", []):
            files.add(js_dir / source)
    # Loaded separately from the compiled bundle in base_game.html.
    files.add(js_dir / "core/status.js")
    records = []
    for path in sorted(files, key=relative):
        raw = path.read_bytes()
        text = raw.decode("utf-8-sig")
        source = uncomment(text)
        definitions = [
            {"line": source.count("\n", 0, m.start()) + 1, "name": m[1], "value": m[2].strip()}
            for m in DEFINITION.finditer(source)
        ]
        role = {
            "game/themes/adventure.css": "active-theme-values",
            "game/themes/classic.css": "disabled-theme",
            "game/core/tokens.css": "lab-compatibility-entry",
            "game/core/scales.css": "common-scales",
            "theme_bundle.css": "active-theme-entry",
            "game_bundle.css": "active-layout-entry",
        }.get(path.relative_to(CSS).as_posix() if path.is_relative_to(CSS) else "")
        records.append(
            {
                "path": relative(path),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "kind": path.suffix.lstrip("."),
                "in_active_css_graph": path in ordered,
                "css_role": role or ("active-game-consumer" if path in ordered else "conservative-source-candidate"),
                "selector_candidates": selector_candidates(source) if path.suffix == ".css" else [],
                "definitions": definitions,
                "references": locations(REFERENCE, source),
                "color_candidates": locations(COLOR, source),
                "literal_color_candidates": locations(LITERAL_COLOR, source),
                "font_candidates": locations(FONT, source),
                "size_candidates": locations(SIZE, source),
                "responsive_candidates": locations(MOBILE, source),
            }
        )
    defined = {d["name"] for r in records if r["in_active_css_graph"] for d in r["definitions"]}
    used = {m["value"].split("(", 1)[1].strip() for r in records if r["in_active_css_graph"] for m in r["references"]}
    token_path = CSS / "game/core/tokens.css"
    token_bytes = token_path.read_bytes()
    return {
        "schema_version": 2,
        "scope": "Current working-tree active theme and layout CSS import graphs; conservative scan also includes disabled Classic and Lab compatibility source, game templates and configured game JS. Vendor and compiled outputs excluded.",
        "limitations": [
            "Lexical candidates only: media conditions, selectors, fallbacks, comment-like strings and contextual token overrides require review; no browser computed-style or reachability proof.",
            "Undefined candidates may be defined dynamically, by inherited outer styles, or via var() fallbacks. No computed cyclic-variable analysis is claimed.",
            "Color candidates include variable-based color expressions and content art; literal_color_candidates only index numeric/hex candidates. Size candidates include legitimate geometry. Do not replace occurrences mechanically.",
            "core/tokens.css is now a Lab compatibility wrapper, not the active runtime theme or an original palette baseline. Pre-migration baselines remain in archive/game_css_baseline/2026-10-24/; Classic is a separate disabled theme source.",
            "Runtime template includes and API paths are not resolved by this script; all game templates are scanned conservatively. Site/cabinet and Rift Lab are outside migration-consumer scan.",
        ],
        "build": {
            "config": relative(CSS / "compiler_config.json"),
            "css_outputs": config["css"],
            "entries": [relative(entry) for entry in entries],
            "command": r".\.venv\Scripts\python.exe -m src.frontend.core.static",
            "implementation": "src/frontend/core/static.py",
            "dependency": "codex_core.dev.static_compiler.compiler.StaticCompiler",
        },
        "desktop_viewports": [[3840, 2160], [2560, 1440], [1920, 1080], [1366, 768]],
        "css_source_order": [relative(p) for p in ordered],
        "imports": edges,
        "import_issues": issues,
        "unimported_game_css": sorted(relative(p) for p in game_files - set(ordered)),
        "undefined_reference_candidates": sorted(used - defined),
        "compatibility_core_tokens": {
            "path": relative(token_path),
            "sha256": hashlib.sha256(token_bytes).hexdigest(),
            "source": token_bytes.decode("utf-8-sig"),
        },
        "files": records,
    }


def markdown(data: dict) -> str:
    files = data["files"]
    fields = (
        "definitions",
        "references",
        "color_candidates",
        "literal_color_candidates",
        "font_candidates",
        "size_candidates",
        "responsive_candidates",
    )
    counts = {field: sum(len(r[field]) for r in files) for field in fields}
    lines = [
        "# Инвентаризация игрового CSS и тем",
        "",
        "Отчёт генерируется из текущих файлов рабочего дерева. Пересоздание: `python tools/css_token_inventory.py`; проверка актуальности: та же команда с `--check`.",
        "",
        "Это статическая карта текущих источников, не визуальная проверка. Данные с путями, строками, значениями, SHA-256 и классификацией активных/отключённых источников находятся в `game_css_token_inventory.json`.",
        "",
        "## Сборка и загрузка",
        "",
        "- Активные entry: `theme_bundle.css` → `theme.css`, `game_bundle.css` → `game.css` через `compiler_config.json`.",
        "- Штатная команда: `" + data["build"]["command"] + "`. Скрипт инвентаризации сборку не запускает.",
        "- Реализация: `src/frontend/core/static.py`, зависимость `codex_core.dev.static_compiler.compiler.StaticCompiler`.",
        "- `base_game.html` и preview загружают `theme.css` перед `game.css`; Adventure задан на корневом HTML до первого отображения. Шрифты загружаются отдельно.",
        "- Активная тема: `game/themes/adventure.css`; общие шкалы: `game/core/scales.css`. `game/themes/classic.css` отключён от runtime-entry; `game/core/tokens.css` — совместимый wrapper scales+Classic только для Lab.",
        "- Текущая цель: desktop 3840×2160, 2560×1440, 1920×1080, 1366×768. Mobile отложен; его архив и manifest ведутся отдельно.",
        "",
        "## Объём",
        "",
        f"- {len(data['css_source_order'])} CSS-файлов в цепочке импорта, {len(files)} файлов в консервативном сканировании.",
    ]
    lines += [f"- `{name}`: {count}." for name, count in counts.items()]
    lines += [
        f"- CSS game-источников вне entry: {len(data['unimported_game_css'])}; кандидатов ссылок без определения в CSS-графе: {len(data['undefined_reference_candidates'])}.",
        "",
        "## Владельцы и дальнейшая миграция",
        "",
        "| Источник | Назначение | Следующий шаг |",
        "| --- | --- | --- |",
        "| `game/core/scales.css` | Общие шкалы, размеры и aliases | Сохранять единый контракт без копий в компонентах |",
        "| `game/themes/adventure.css`, `classic.css` | Совместимые значения тем; Classic отключён | Проверять равенство ключей и изолированную сборку |",
        "| `game/core/tokens.css` | Lab compatibility wrapper, вне активного графа | Не подключать его в game_bundle |",
        "| `game/shell/layout/index.css`, `game/shell/responsive/index.css` | Общая композиция и breakpoint-правила | Сохранить desktop, мобильные извлечения сверить с архивом |",
        "| `game/components/` | Повторно используемые компоненты с токенами | Не возвращать литералы палитры/шрифтов в правила |",
        "| `game/domains/` | Содержимое игровых экранов | Не дублировать shell; исключения геометрии описывать явно |",
        "| `templates/game/`, game JS | Inline CSS, динамические цвета, подсказки | Сопоставить кандидатов с view models и порталами; не менять серверные контракты |",
        "| `rift_lab/static/theme-tokens.css`, `themes.css` | Исходный образец Adventure (вне consumer scan) | Лабораторный runtime не переносить |",
        "",
        "## Крупнейшие источники цветовых выражений (включая темы)",
        "",
        "| Файл | Цвета | Шрифты | Размеры |",
        "| --- | ---: | ---: | ---: |",
    ]
    ranked = sorted(files, key=lambda r: (-len(r["color_candidates"]), r["path"]))[:15]
    lines += [
        f"| `{r['path']}` | {len(r['color_candidates'])} | {len(r['font_candidates'])} | {len(r['size_candidates'])} |"
        for r in ranked
    ]
    lines += ["", "## Ограничения", ""] + ["- " + limit for limit in data["limitations"]]
    lines += [
        "",
        "Наблюдения не доказывают работу production или визуальную эквивалентность Classic. Для этого нужны отдельные browser fixtures/screenshots; исходный baseline хранится в архиве, текущий JSON описывает текущее рабочее дерево.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="Fail if committed/generated reports differ from current sources"
    )
    args = parser.parse_args()
    data = inventory()
    outputs = {
        REPORT.with_suffix(".json"): json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        REPORT.with_suffix(".md"): markdown(data),
    }
    stale = []
    for path, content in outputs.items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(relative(path))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    print(
        json.dumps(
            {
                "files": len(data["files"]),
                "css_graph": len(data["css_source_order"]),
                "import_issues": data["import_issues"],
                "stale_reports": stale,
            },
            ensure_ascii=False,
        )
    )
    return int(bool(stale or data["import_issues"]))


if __name__ == "__main__":
    raise SystemExit(main())
