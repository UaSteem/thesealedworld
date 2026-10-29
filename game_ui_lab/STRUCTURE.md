# Game UI Lab: карта файлов

Все пути ниже — относительно `game_ui_lab`. Перед правкой прочитать [решения](docs/current-decisions.md). Действующий интерфейс не заменять отдельной копией.

## Сборка и запуск

| Узел | Файл |
| --- | --- |
| Локальный HTTP-сервер, разрешённые static/fixture пути, сборка HTML | `app.py` |
| Запуск из PowerShell | `start.ps1` |
| Основная оболочка, Debug-кнопки, порядок скриптов | `templates/index.html` |
| Один Game/canvas, переключение сцен, возврат, ограничения боя | `static/game/core/boot.js` |
| Загрузка боевых групп ассетов | `static/game/core/assets.js` |
| Общий resize coordinator | `static/game/shared/resize.js` |

## Что менять по поручению художника

| Поручение | Существующий владелец |
| --- | --- |
| Цветовая гамма | `static/game/shell/obsidian-bronze.css` — семантические токены, не менять общую тему в src |
| Размеры поля, предел1920, страницы, наложения | `static/game/shell/workspace.css`; базовые стили `shell.css`, логическая геометрия `viewport.js` |
| Компактный аватар и ресурсы | `templates/shared/player-hud.html`, `workspace.css` |
| Игровое меню | `templates/shared/player-hud.html`, обработчики `core/boot.js` |
| Оболочка и вкладки персонажа | `templates/shared/character-window.html`, `workspace.css`, `core/boot.js` |
| Портрет и слоты экипировки | `templates/shared/character-panel.html`, `static/game/shell/character.css` |
| Инвентарь: фильтры, сетка, осмотр | `static/game/scenes/inventory/scene.js`; адаптер `client.js`, данные/упаковка `data.js`, цвета `theme.js` в той же папке |
| Атрибуты, группы навыков, модификаторы, билды, квесты, настройки | `CharacterDraft` в `static/game/scenes/drafts/pages.js`; данные `data/starter_guard_01.json` |
| Тексты намерений: диалоги, город, смерть/победа, добыча | `data/page-briefs.json`; отрисовка `static/game/scenes/drafts/aftermath.js` |
| Текущая лесная сцена для примерки | `static/game/scenes/rift-preview.js`, фиксированная карта `data/rift-preview.json` |
| Отдаление/Debug зума | `rift-preview.js`, блок `.rift-debug-window` в `templates/index.html`, `workspace.css` |
| Арена и кварталы | `static/game/scenes/drafts/arena.js`, `districts.js`, `construction.js` |
| Бой | `static/game/scenes/combat/scene.js`, `static/game/ui/combat-controls.js`, `target-inspector.js`, `static/game/shared/hex-layout.js` |
| Чат: разметка, данные, сворачивание, прозрачность | `templates/shared/chat.html`, `static/game/shell/chat.js`, `overlay-chat.js`, `workspace.css` |

Папка `scenes/drafts` пока содержит и действующие страницы. Само слово drafts не означает, что нужно рисовать их заново. `drafts/scenario.js` и `drafts/city.js` больше не подключены в актуальные страницы: не возвращать их вместо briefs без поручения.

## Данные, ассеты и наработки

| Папка | Назначение |
| --- | --- |
| `static/game/assets/` | Только подключённые материалы интерфейса и manifests |
| `static/game/assets/catalog.json` | Боевые текстуры: группы, пути, размеры и хеши |
| `static/game/assets/places/painted/` | Используемые фоны помещений/кварталов |
| `static/game/assets/rift/manifest.json` | 16 используемых изображений рифта с происхождением/хешами |
| `static/game/shared/rift-renderer/` | Локальная копия нужного отрисовщика и метаданных, без запуска Rift Lab |
| `data/inventory.json`, `fixtures/inventory.py` | Слепок предметов, точный allowlist `/inventory-art/`; изображения читаются из `assets/item_art/renders` корневого проекта |
| `sources/` | Художественные мастера/происхождение, не browser assets |
| `experiments/visuals/<задача>/` | Новые картинки, варианты и сравнения до выбора |
| `experiments/prototypes/` | Изолированные технические наработки |
| `experiments/history/` | Заменённые реализации/картинки; старый aftermath в `aftermath-interactive.js` |
| `docs/` | Текущие решения и исторические исследования; приоритет у `docs/current-decisions.md` |
| `tools/` | Подготовка и проверка материалов |

Исправление действующего компонента делается на его месте. Не создавать параллельные папки final2/fixed/new как новые источники истины. Выбранный эксперимент переносится в своего владельца вместе с нужными ссылками; неиспользуемые пробы остаются вне active assets.

## Границы зависимостей и проверки

`src/frontend/static` корневого проекта предоставляет fonts/theme/Phaser/SVG/аватар на чтение. Это разрешённая зависимость существующей Lab, а не разрешение менять src. Изображения предметов также внешние относительно Lab; не заявлять автономную поставку или чистый checkout без отдельной проверки.

`inventory_app.py`, `templates/inventory.html`, `static/game/scenes/inventory/boot.js` и `chat-layout.js` — старый отдельный технический стенд сетки. Общий интерфейс открывается через `app.py`; старый resize-чата не подключать к нему обратно.

Тесты находятся в `tests/game_ui_lab` корневого проекта; часть проверяет исторические pure modules из experiments/history. Команды — в [README](README.md). Положительный результат таких тестов не подтверждает текущую визуальную приёмку.

Граница frontend/backend: [проверка стенда](docs/frontend-boundary-check.md). Lab — самостоятельный прототип будущего фронтенда; повторять текущий frontend src не требуется. Backend-код и алгоритмы здесь не реализуются: их ответы имитируются моками.

Журнал боя в общей панели сообщений: static/game/shell/combat-log.js — отдельные моковые события/renderer; message-panels.js — только переключение панелей и доступность по сцене; chat.js — обычные каналы. Журнал не подключать к чат-отправке/хранилищу. Разметка общая в templates/shared/chat.html.
