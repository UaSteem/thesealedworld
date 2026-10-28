# Актуальный игровой интерфейс и графика

Обновлено: 2026-10-28. Это указатель текущего клиента, а не перечень старых прототипов.

## Клиент и отображаемая графика

- Модули клиента: `src/frontend/static/js/game/client/`.
- Оболочка: `src/frontend/templates/game/base_game.html` и `session_content_inner.html`.
- Runtime-графика: `src/frontend/static/images/game-client/`, перечень в `catalog.json`.
- Фоны арены и кварталов: `src/frontend/static/images/game-client/places/`, перечень в `manifest.json`.
- Маршруты и серверные адаптеры: `src/frontend/game_features/`.
- Журнал переноса и границы проверки: `tasks/active/2026-10-26-game-ui-runtime-migration.md`.

Неперенесённые домены сохраняют реальное HTML-отображение. Наличие клиентского
модуля не означает завершение переноса всей игры или подтверждение production.

## Общие исходники для разработки и художника

- Мастера UI боя: `assets/game_client_sources/combat/ui/`.
- Исходные JPEG городских сцен: `assets/game_client_sources/places/originals/`.
- Сохранённые сжатые фоны для публикации: `assets/game_client_sources/places/painted/`.
- Происхождение и SHA-256: `assets/game_client_sources/manifest.json`.
- Пересборка UI: `tools/game_ui_migration/build_ui_assets.py`.
- Подготовка сжатых фонов: `tools/game_ui_migration/build_place_backgrounds.py`.
- Публикация выбранных фонов в static: `tools/game_ui_migration/build_runtime_places.py`.

Полноразмерные художественные мастера не являются player-download. Фон жилого
квартала сохранён как мастер; его наличие не означает подключение сцены в runtime.

`game_ui_lab/` и `rift_lab/` остаются локальными экспериментальными приложениями,
исключёнными из Git-снимка. Они не требуются для запуска основного клиента или
пересборки перечисленных ассетов. Их демонстрационные данные не являются
состоянием игры.

## Исторические изображения

Старые `src/frontend/static/images/exploration/terrain/`, `images/scenes/` и
`images/game/arena/backgrounds/` не являются источником нового дизайна.
Часть файлов сохраняется для неперенесённых экранов или действующих URL;
это не означает утверждение их стиля. Корневой `archive/` — локальная история,
а не доступная другому участнику папка скачиваемого репозитория.
