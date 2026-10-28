# Упрощение экипировки и колчан во второй руке

Статус: review-pending. Режим: независимый ревизор (задан владельцем). Проверка: pending.
Исходный запрос: `2026-10-25-equipment-migration-prompt.md` содержит полный неизменённый запрос.

## Требования
- R1: Убрать chest_garment/legs_garment из активной игры; сохранить нагрудники/поножи по фактической механике. implementation done; verification pending (независимая ревизия).
- R2: Перчатки, пояс, плащ — аксессуары; наручи отдельно; не добавлять перчаткам броню. implementation done; verification pending (независимая ревизия).
- R3: Колчан off_hand исключительно с луком; лук сохраняет two_hand; щит/оружие несовместимы; другие two_hand без исключений. implementation done; verification pending (независимая ревизия).
- R4: 14 визуальных позиций с двумя руками (обычный two_hand сохраняет объединённое представление). implementation done; verification pending (независимая ревизия).
- R5: Проверить enum/DTO, генерацию/стартеры, equip/unequip/смену оружия, projections/combat/stats, inventory/tooltips, studio/admin, saved layouts. implementation done; verification pending (независимая ревизия).
- R6: Предметы при переносе/смене оружия не теряются. Подготовить проверяемый dry-run перенос и безопасное применение без запуска рабочих данных. implementation done; verification pending (независимая ревизия).
- R7: Не трогать game_ui_lab, archive/game_ui_lab_alpha, CSS/canvas/размеры/статус/чат/сцену; без commit/push/deploy и рабочих данных. implementation done; verification pending (независимая ревизия).

## Инвентаризация и решения до реализации
- Активные ordinary garment bases: apron, shirt, tunic (chest_garment), pants (legs_garment). Их определения сохраняются вне активного loader в archive/equipment_slots_2026_10_25/retired_bases.json с checksum. medium_leg_armor и прочая armor остаются.
- Существующие base IDs gloves/cloak/belt и технические slots gloves_garment/outer_garment/belt_accessory сохраняются. UI layer меняется на accessory; механика и тип garment перчаток/плаща сохраняются ради предотвращения скрытой смены affix pools/статов.
- Все 3 лука уже two_hand и skill_archery; сохраняем это. 6 quivers имеют type=ammo и переназначаются на off_hand без изменения charge/effect/power.
- Новые активные контракты replacement-only. Старые названия допустимы только в явно отделённом offline boundary migrator и архиве, не как aliases активного equip.
- Retired экземпляры (включая предыдущие IDs linen_shirt/wool_tunic/fur_pants) сохраняют ID/количество/механику/текст и уходят в backpack; equip запрещён. Никакой конвертации в броню или удаления.
- Legacy quiver переносится в свободный off_hand только при луке в two_hand; при конфликте off_hand сохраняет существующий предмет, quiver в backpack. Несовместимый off_hand при two_hand отправляется в backpack. При снятии/замене лука на не-лук quiver в backpack; bow→bow сохраняет quiver. Никакого автоматического надевания quiver из backpack.
- Dry-run инструмент читает только явно указанный JSON snapshot runtime inventory (layout/by_id), создаёт отчёт; write-out отдельного нового snapshot только с явным флагом. Это НЕ SQL/Redis live migrator. Применение к SQL требует отдельного адаптера/поручения и остановки активных сессий/flush.

## План
1. Добавить тесты нового observable контракта, подтвердить ожидаемые падения.
2. Архивировать 4 базы; изменить enum/каталоги/стартеры/Monster projections без смены их прочих механик.
3. Ввести единые правила hand compatibility, equip/unequip и активные snapshots; обновить inventory и подписи, не CSS.
4. Подготовить offline migration, проверить conservation/idempotency/conflicts и dirty runtime handling.
5. Выполнить focused tests/lint, получить независимую ревизию и исправить замечания.

## Проверки и ограничения
Проверка завершена в указанном ниже локальном объёме. В дереве есть значительные чужие изменения; HEAD diff не является перечнем только этой задачи.


## Реализация и проверки исполнителя (2026-10-25)

- До production edits: 3 новых observable tests ожидаемо упали на старых enum, колчане без лука и 17 позициях. После реализации эти проверки проходят.
- Новые проверки: 15 regression tests в `test_equipment_contract.py` и `test_equipment_migration.py`: bow→bow, замена оружия/снятие/выбрасывание лука, conservation, ammo не является off-hand атакой, unchanged combat stats при добавлении ammo без бонусов, 14 positions, explicit migration/dry-run/overwrite refusal, отказ flush legacy layout. Вместе с rat schema-normalization test: 16 passed.
- Расширенный прогон: `var/equipment-slots-verified.log`: 1300 passed, 14 skipped, 10 failed (58.58 s). Один пропущенный count expectation в player comparison исправлен; отдельный повтор этого теста: 1 passed. Остальные 9 failures ниже относятся к baseline.
- Фокус проверки: Inventory, Items, Character runtime, Monsters (включая HTTP/catalog/inspection/prepared/stats), GameCatalog, starter materialization, starter tool и frontend inventory template contracts. Вне Windows sandbox; в sandbox прогон зависал на первом async inventory test, остановлен. `.venv/Scripts/pytest.exe` не работает (uv trampoline); использовался `.venv/Scripts/python.exe -m pytest`.
- Scoped `git diff --check` для task file list: pass. Scoped Ruff production/new code: pass. Полный task file list Ruff находит четыре существовавшие import errors в `tests/backend/features/items/test_catalog_service.py` (I001) и `tools/reset_character_inventory.py` (I001/E402); импорты этой задачей не менялись.
- Task semantic file list: `var/equipment-slots-files.txt` (135 путей), включая все 30 family prepared ammo payloads и 12 shared ammo payloads, индексы/manifests. Артефакты `var/` — локальные доказательства, не источник runtime данных.
- Исторические family literals не переписывались. Hash-константы numeric baseline не обновлялись. Для нового DTO применяется только явная обратная нормализация удалённых None keys и quiver/off_hand при сравнении с frozen fixtures.
- Исходный `_sync_active_character_items` AST совпадает с HEAD; actor-state metrics поведение этой задачей не меняется.

### Девять baseline failures

1. `tests/backend/features/inventory/test_inventory_service.py::test_equip_action_requests_active_character_gear_score_recalculation`
2. `tests/backend/features/inventory/test_inventory_service.py::test_equip_garment_action_requests_active_character_gear_score_recalculation`
   Оба воспроизведены на исходном HEAD InventoryService (через изолированный import hook без замены рабочего кода): `var/equipment-baseline-metrics.log`: 2 failed, тот же assert `metrics not in active_doc`. Предыдущая naming задача также фиксировала эти failures.
3. `tests/backend/features/monsters/test_bandit_alpha_balance.py::test_bandit_price_ladder_preserves_other_authored_mechanics`
4. `tests/backend/features/monsters/test_goblin_calibrated_scaling.py::test_goblin_senior_definitions_prices_and_equipment_remain_unchanged`
5. `tests/backend/features/monsters/test_rat_alpha_balance.py::test_all_72_prepared_sets_preserve_identity_power_skills_and_other_bonuses`
6. `tests/backend/features/monsters/test_wolf_alpha_balance.py::test_retained_wolf_prepared_fields_are_unchanged_after_thorns_and_offhand_removal`
   Эти четыре digest failures воспроизведены на сохранённых BEFORE source через import hook: `var/equipment-baseline-digests.log`: 98 passed, 4 failed. Текущие backward-normalized digest значения совпадают с baseline. Чужие числовые hash ожидания не исправляются этой задачей.
7. `tests/backend/features/monsters/test_alpha_tier_gates.py::test_historical_bandit_manifest_validates_all_saved_sets`
8. `tests/backend/features/monsters/test_prepared_remaining_equipment.py::test_complete_prepared_equipment_matches_authored_members[rat_swarm]`
9. `tests/backend/features/monsters/test_prepared_remaining_equipment.py::test_complete_prepared_equipment_matches_authored_members[bandit_gang]`
   Отказ на stale `manifest.sources` checksum `src/backend/features/items/resources/affixes/catalog.py`; этот файл задачей не менялся. Старые source provenance hashes не подменяются новым состоянием генератора. Current payload files hashes согласованы после slot-only edits.

### Ограничения и безопасное применение

- Инструкция: `docs/ru/backend/features/items/equipment_slots.md`. Архив: `archive/equipment_slots_2026_10_25/README.md`, SHA256 retired_bases.json `3d515ced89fe58cc098232a21f63ea3f91aca51dcc0631fa23f7e7b7c64f6a65`.
- Offline tool покрывает full InventoryRuntimeSession JSON, не SQL/generated templates/monster persisted snapshots. Live adapter не реализован и не заявляется. Не выполнялись перенос, flush или изменения рабочих/production данных.
- Нельзя применять к SQL только placements: mechanics.slot/valid_slots/base_id требуют согласованной записи; dirty Redis writers остановить заранее, после переноса пересобрать inventory/AC/GS, исключить stale flush.
- Не выполнялись browser/runtime visual acceptance, полный project gate, commit/push/deploy. Исключённые UI lab/CSS/canvas/размеры/чат/сцена не изменялись этой задачей.

### Независимая ревизия

Первоначальная ревизия: R1–R4 pass, R5/R6 partial из-за P2 публичного отображения retired items; R7 unverified. P2 исправлена и независимо перепроверена: 28 passed. Итог R5/R6 pass в пределах локальной проверки; новых существенных замечаний нет.


## Исправление P2 независимого ревизора: retired presentation

Initial verdict: R1–R4 pass; R5/R6 — одна P2: retired экземпляр отображался как Unknown после исключения базы; R7 unverified на грязном baseline. Остальные границы/ограничения принимаются отдельно ведущим.

- Test-first: 28 параметризованных проверок current/historical retired IDs, migrated snapshot → window, SQL rehydration и трёх состояний disclosure дали 21 ожидаемое падение Unknown и 7 passed для identified+generated.
- Исправление: `items/resources/retired_presentations.py` содержит только immutable trusted public names/descriptions четырёх archived bases и трёх исторических IDs. `ItemVisualService.base_presentation` использует эту read-only presentation при отсутствующей активной базе. Mechanics/slots/catalog entries/генерация не возвращаются; произвольный сохранённый unidentified name/lore не выдаётся.
- SQL rehydration и runtime view используют ту же owning presentation функцию; identified+generated экземпляры сохраняют собственный разрешённый lore.
- Повтор: `var/equipment-retired-verified.log` — 93 passed (5.28 s), включая disclosure, visuals, equip и migration regressions. Scoped Ruff трёх файлов: pass.
- Финальный зелёный consumer suite ДО этой узкой presentation correction: `var/equipment-slots-green.log` — 1301 passed, 14 skipped, 9 deselected (48.07 s). Исключены только девять явно описанных baseline failures; это не полный project gate.
- Scope list теперь 138 путей. Код снова заморожен для проверки исправления ревизором.

## Итог независимой приёмки (2026-10-25)

Ревизор GPT-6 Astra зафиксировал первоначальный вердикт до получения выводов исполнителя, затем проверил исправление P2 и существенные утверждения отчёта. R1–R6 подтверждены в локальном объёме. Независимо: 79 equipment/catalog/combat тестов, 47 shared equipment/template тестов, отдельный CLI test и 28 presentation cases прошли. Зависшие async/monster запуски остановлены; их полный успех не заявляется.

Точные итоговые числа исполнителя: broader suite ДО presentation correction — 1301 passed / 14 skipped / 9 deselected; после correction — 93 passed. Девять документированных исключений: шесть failures воспроизведены через сохранённый baseline/import hook, ещё три связаны со stale source checksums manifests. Не утверждать, что все девять отдельно воспроизведены на baseline.

R7: исполнитель сообщил соблюдение границ; в доступном журнале работы отсутствуют commit/push/deploy и операции с рабочими данными, task scope не включает запрещённые UI поверхности. Независимо доказать авторство всех изменений в изначально грязном дереве невозможно, поэтому verification unverified сохранён. Live SQL/Redis/API/UI, browser visual acceptance и полный project gate не проверены. Пользователь ещё не принял результат; данные не мигрированы.
