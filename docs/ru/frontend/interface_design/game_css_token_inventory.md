# Инвентаризация игрового CSS и тем

Отчёт генерируется из текущих файлов рабочего дерева. Пересоздание: `python tools/css_token_inventory.py`; проверка актуальности: та же команда с `--check`.

Это статическая карта текущих источников, не визуальная проверка. Данные с путями, строками, значениями, SHA-256 и классификацией активных/отключённых источников находятся в `game_css_token_inventory.json`.

## Сборка и загрузка

- Активные entry: `theme_bundle.css` → `theme.css`, `game_bundle.css` → `game.css` через `compiler_config.json`.
- Штатная команда: `.\.venv\Scripts\python.exe -m src.frontend.core.static`. Скрипт инвентаризации сборку не запускает.
- Реализация: `src/frontend/core/static.py`, зависимость `codex_core.dev.static_compiler.compiler.StaticCompiler`.
- `base_game.html` и preview загружают `theme.css` перед `game.css`; Adventure задан на корневом HTML до первого отображения. Шрифты загружаются отдельно.
- Активная тема: `game/themes/adventure.css`; общие шкалы: `game/core/scales.css`. `game/themes/classic.css` отключён от runtime-entry; `game/core/tokens.css` — совместимый wrapper scales+Classic только для Lab.
- Текущая цель: desktop 3840×2160, 2560×1440, 1920×1080, 1366×768. Mobile отложен; его архив и manifest ведутся отдельно.

## Объём

- 103 CSS-файлов в цепочке импорта, 172 файлов в консервативном сканировании.
- `definitions`: 1568.
- `references`: 6331.
- `color_candidates`: 2703.
- `literal_color_candidates`: 253.
- `font_candidates`: 958.
- `size_candidates`: 2400.
- `responsive_candidates`: 39.
- CSS game-источников вне entry: 3; кандидатов ссылок без определения в CSS-графе: 38.

## Владельцы и дальнейшая миграция

| Источник | Назначение | Следующий шаг |
| --- | --- | --- |
| `game/core/scales.css` | Общие шкалы, размеры и aliases | Сохранять единый контракт без копий в компонентах |
| `game/themes/adventure.css`, `classic.css` | Совместимые значения тем; Classic отключён | Проверять равенство ключей и изолированную сборку |
| `game/core/tokens.css` | Lab compatibility wrapper, вне активного графа | Не подключать его в game_bundle |
| `game/shell/layout/index.css`, `game/shell/responsive/index.css` | Общая композиция и breakpoint-правила | Сохранить desktop, мобильные извлечения сверить с архивом |
| `game/components/` | Повторно используемые компоненты с токенами | Не возвращать литералы палитры/шрифтов в правила |
| `game/domains/` | Содержимое игровых экранов | Не дублировать shell; исключения геометрии описывать явно |
| `templates/game/`, game JS | Inline CSS, динамические цвета, подсказки | Сопоставить кандидатов с view models и порталами; не менять серверные контракты |
| `rift_lab/static/theme-tokens.css`, `themes.css` | Исходный образец Adventure (вне consumer scan) | Лабораторный runtime не переносить |

## Крупнейшие источники цветовых выражений (включая темы)

| Файл | Цвета | Шрифты | Размеры |
| --- | ---: | ---: | ---: |
| `src/frontend/static/css/game/domains/combat/actions.css` | 271 | 70 | 181 |
| `src/frontend/static/css/game/components/inventory.css` | 236 | 44 | 222 |
| `src/frontend/static/css/game/domains/rift/screen.css` | 159 | 34 | 112 |
| `src/frontend/static/css/game/domains/combat/sidebars.css` | 121 | 33 | 64 |
| `src/frontend/static/css/game/components/cards.css` | 117 | 15 | 36 |
| `src/frontend/static/css/game/domains/exploration/encounters.css` | 105 | 64 | 63 |
| `src/frontend/templates/game/test_hex_rift.html` | 97 | 30 | 116 |
| `src/frontend/static/css/game/domains/combat/result.css` | 72 | 38 | 66 |
| `src/frontend/static/css/game/themes/adventure.css` | 70 | 0 | 19 |
| `src/frontend/static/css/game/domains/exploration/scene.css` | 60 | 17 | 57 |
| `src/frontend/static/css/game/themes/classic.css` | 56 | 0 | 19 |
| `src/frontend/static/css/game/domains/combat/logs.css` | 54 | 14 | 16 |
| `src/frontend/static/css/game/components/status_widgets.css` | 53 | 41 | 25 |
| `src/frontend/static/css/game/domains/city_services/index.css` | 53 | 28 | 73 |
| `src/frontend/static/css/game/domains/exploration/right_sidebar.css` | 49 | 11 | 21 |

## Ограничения

- Lexical candidates only: media conditions, selectors, fallbacks, comment-like strings and contextual token overrides require review; no browser computed-style or reachability proof.
- Undefined candidates may be defined dynamically, by inherited outer styles, or via var() fallbacks. No computed cyclic-variable analysis is claimed.
- Color candidates include variable-based color expressions and content art; literal_color_candidates only index numeric/hex candidates. Size candidates include legitimate geometry. Do not replace occurrences mechanically.
- core/tokens.css is now a Lab compatibility wrapper, not the active runtime theme or an original palette baseline. Pre-migration baselines remain in archive/game_css_baseline/2026-10-24/; Classic is a separate disabled theme source.
- Runtime template includes and API paths are not resolved by this script; all game templates are scanned conservatively. Site/cabinet and Rift Lab are outside migration-consumer scan.

Наблюдения не доказывают работу production или визуальную эквивалентность Classic. Для этого нужны отдельные browser fixtures/screenshots; исходный baseline хранится в архиве, текущий JSON описывает текущее рабочее дерево.
