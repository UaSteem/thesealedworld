# Каталоги, bootstrap и изображения: единые правила проекта

Статус: reviewed-awaiting-acceptance. Пользователь выбрал независимого ревизора 2026-10-24.

## Исходный запрос
Владелец использует Python-словари и Pydantic-модели на сервере. Поручено изучить организацию Monsters, наличие ссылок на изображения и старые bootstrap. Если общего навыка для повторения принятого подхода нет, разработать соответствующее проектное руководство.

## Требования
- R1: Проследить текущий authored Monsters каталог: Python-данные, модели, сборка, индексы и публичный фасад. Реализация done; проверка pass (независимый ревизор).
- R2: Проверить image references, наличие файлов и путь до потребителей. Отделить source assets, опубликованные файлы, DTO и runtime instance. Реализация done; проверка pass (независимый ревизор).
- R3: Сопоставить новый Monsters bootstrap и существующий GameCatalog bootstrap; не объявлять их контрактами одного назначения. Реализация done; проверка pass (независимый ревизор).
- R4: Проверить существующие project skills и закрепить недостающие общие правила без дублирующего навыка, если существующий entrypoint подходит. Реализация done; проверка pass (независимый ревизор).
- R5: Для новых серверных валидируемых ресурсов предпочитать Python-источники, Pydantic и ID-индексы. Не переписывать существующие frozen dataclass definitions только ради формы. Реализация done; проверка pass (независимый ревизор).
- R6: Не реализовывать Items image selector и не менять приложение, runtime JSON, картинки, bootstrap API, БД или production-состояние в рамках нового руководства. Исправления собственного прежнего переименования вести отдельно в его MD. Реализация done; проверка pass (независимый ревизор).

## План
1. Проверить исходники, ссылки и доступные чистые тесты без внешних сервисов.
2. Зафиксировать различия, ограничения и точные code anchors.
3. После выбора режима: добавить focused reference к существующему turnbasedmmorpg-project; дать условные ссылки из backend/game-content. Новую верхнеуровневую skill не создавать, если общий project entrypoint покрывает задачу.
4. Проверить YAML/frontmatter, локальные ссылки, маршрутизацию и фактические команды; записать результаты.

## Первичные наблюдения
- Monsters: contracts.py содержит Pydantic DTO и frozen dataclass definitions. nested_contracts.py использует strict/frozen Pydantic для stats/loadout и dataclass для композиции.
- registry.py валидирует последовательности до построения dict; indexes.py хранит read-only ID mappings и индекс тегов.
- ImageAssetReference уже содержит asset_id/source_path/review_status/display_mirror. База задаёт default_image; вариант может задать image override.
- Текущий локальный каталог: 6 семейств, 6 кланов, 63 участника. Изображения есть у 47, source и ожидаемые frontend-файлы найдены. Golems и anchors не имеют image refs.
- Новый MonsterCatalogBootstrapDTO содержит typed dictionaries; MonsterCatalogBootstrapService создаёт content hashes и manifest. API поддерживает ETag/304.
- Старый GameCatalogBootstrapDTO содержит catalogs: dict[str, dict[str, dict[str, Any]]]. Общий bootstrap собирает item/skill/combat/public monster family sections, JSON является транспортом. Frontend использует IndexedDB и словарный поиск.
- ItemCatalogService загружает Python resources через Pydantic model_validate, проверяет дубли и создаёт base_items/materials/raw_resources/entries.
- Существующие навыки описывают эти домены по отдельности. Общего предписания обследовать и переиспользовать существующий catalog/bootstrap/asset pattern перед новой реализацией не найдено.

## Ограничения проверки
Диагностика локальных исходников не доказывает deployment или подключение authored image refs к боевым runtime instances. Публикация изображений в рамках задачи не запускалась.

## Проверка и результат

Изменены три project-owned entrypoint и добавлен один focused reference:
- `.agents/skills/turnbasedmmorpg-project/references/catalog-conventions.md`;
- `.agents/skills/turnbasedmmorpg-project/SKILL.md`;
- `.agents/skills/turnbasedmmorpg-backend/SKILL.md`;
- `.agents/skills/turnbasedmmorpg-game-content/SKILL.md`.

Резервные копии исходных entrypoint: `var/catalog-conventions-skill-backup/`.

Фактические проверки:
- Каталог/локализация/bootstrap/nested sources: 28 passed, 1 deselected, 1 warning (5.56 s), лог `var/catalog-conventions-tests.log`.
- Исключённый из sandbox-прогона HTTP-тест выполнен отдельно вне sandbox: 1 passed, 1 warning (3.45 s), лог `var/catalog-conventions-http-test.log`. Тест явно запрещает доступ к БД, проверяет авторизацию, ETag/304 и безопасные поля.
- Независимый read-only подсчёт: 6 семейств, 6 кланов, 63 участника. 47 image refs; source и ожидаемые опубликованные файлы найдены. 12 golems + 4 anchors без image refs.
- Ведущий дополнительно проверил побайтовое равенство всех 47 source/published файлов: различий нет. Ревизор подтвердил существование, но не проводил отдельное сравнение байтов.
- Обычный Monsters bootstrap: 5 non-system families, 59 members; повторная сборка стабильна, source_path/base_stats отсутствуют.
- General bootstrap: 14 секций catalogs; Items содержит 198 записей public text. Это наблюдение текущего состояния, не числовой инвариант навыка.
- Official `skill-creator/scripts/quick_validate.py`: все 3 entrypoint valid. Новая ссылка из каждого entrypoint разрешается.

Независимая ревизия `/root/review_catalog_guidance`:
- Исходное замечание R4: в backend-навыке не добавилась ссылка и появились CRCRLF из-за staging исходного CRLF. Восстановлено исходное тело, нормализованы переводы строк и добавлена одна строка маршрутизации.
- Повторная проверка: все Markdown-ссылки трёх entrypoint разрешаются, новые маршруты присутствуют, CRCRLF отсутствуют, остальные инструкции сохранены.
- Итог: PASS R1–R6, открытых actionable findings нет.
- Точные существенные утверждения итогового отчёта проверены отдельно после первичного вердикта. Уточнение: ревизор подтвердил соответствие historical файлов HEAD и отсутствие числовых изменений в корректировке теста; хронология предыдущей ошибки наблюдалась ведущим.

Коррекция прежней задачи переименования описана в `tasks/active/2026-10-24-item-base-slot-naming.md`. К архитектуре нового руководства она не относится.
Приложение, API и выбор изображений в рамках нового руководства не реализовывались. Публикация картинок, БД, production и live Combat не проверялись и не менялись. Commit/push/deploy не выполнялись.
