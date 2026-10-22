# A03-01/02: надёжное завершение боя

Дата: 2026-10-22. Режим: с независимым ревизором.

## Исходный запрос
«Завершение боя — A03-01/02. Повтор финализатора повторно начисляет XP; ошибка оставляет закрытый бой с незавершёнными последствиями. Лишний опыт либо зависшее завершение боя — начать проверки и решение этой проблемы».

## Требования
- R1: проверить актуальность A03-01/02 по текущему коду и изолированным тестам. implementation=done; verification=pass (исполнитель + независимый ревизор, local/adapter scope).
- R2: один combat_id начисляет progression каждому персонажу однократно, в том числе при повторе, конкуренции и сбое после применения. Формулы XP сохранить. implementation=done; verification=pass (исполнитель + независимый ревизор, local/adapter scope).
- R3: незавершённые последствия боя обнаружимы и возобновляемы после ошибки/restart; результат и награды не теряются и не удваиваются. implementation=done; verification=pass (исполнитель + независимый ревизор, local/adapter scope).
- R4: независимая ревизия и честный отчёт о локальных проверках и инфраструктурных ограничениях. implementation=done; verification=pass (исполнитель + независимый ревизор, local/adapter scope).

## Границы
До приёмки: без commit/push/deploy, реальных игровых данных, secrets, новых зависимостей. После приёмки разрешён коммит только этой задачи; push/deploy не поручены. Смежные audit IDs не закрывать автоматически. Не менять формулы наград или исход боя.

## План
1. Проследить finalizer, владельцев progression, worker retry/recovery, сохранение finalization и защиту downstream.
2. Написать воспроизводящие regression tests до исправлений.
3. Добавить атомарную дедупликацию в owning operation и возобновляемый lifecycle; проверить отказ на границах.
4. Выполнить focused checks, независимую ревизию, исправить замечания.

## Первичная диагностика
Чистый git status перед работой. Current victory_finalizer_task закрывает runtime первым шагом, затем применяет XP; except логирует и не пробрасывает ошибку. CombatExperienceFinalizer вызывает apply_progress/apply_skill_progress без combat_id. Audit 11 переиспользует A03-02 для другого дефекта: задача следует canonical названию audit/03 и registry.

## Результаты
Реализация и независимая проверка завершены. Пользователь принял результат 22.10.2026; подробные доказательства и ограничения ниже.

## Уточнение и классификация
Пользователь выбрал независимого ревизора. База проверки: develop, HEAD fa2f2664.
- A03-01: High; подтверждено текущим статическим анализом additive path; shared combat runtime, активный World/Expedition pre-alpha и другие consumers; устранить до следующего публичного релиза.
- A03-02: High; подтверждён текущий failure window inactive → side effects → swallowed exception; та же поверхность; устранить до следующего публичного релиза.
- Локальный guard вокруг финализатора недостаточен: после сбоя между reward и marker повтор начислит XP. Выбран owner-level atomic dedup плюс возобновляемое завершение. Runtime-воспроизведение ещё pending.
- Knowledge: существующие backend/combat/quality skills уже требуют idempotency, commit point и fault/integration проверки. Изменение skills сейчас не требуется; проверяется enforcement в коде и тестах.

## Проверки до исправления
2026-10-22: новые regression tests созданы до production edits. Исполнитель получил 2 ожидаемых failure: отсутствующий combat_id у owning operation и подавленная ошибка финализатора. Ведущий независимо подтвердил swallowed RuntimeError командой `.venv/Scripts/python.exe -m pytest tests/backend/features/combat/test_finalization_recovery.py --no-cov -o faulthandler_timeout=15` (на промежуточном состоянии: 1 passed, 1 failed, 5.81s; XP identity уже передавался после начальной правки).
Sandbox-run зависает до тела async tests: faulthandler показывает socket._fallback_socketpair → accept при создании ProactorEventLoop. Повтор с require_escalated разрешён auto-review и выполняется; тестовый event loop не подменяется. Реальные stores не используются.

## Независимая ревизия: первый снимок
Ревизор: внутренний independent_review (Astra High), read-only. R1 pass, R2 partial, R3 fail, R4 partial. Независимый focused запуск: 43 passed (recovery, victory finalizer, XP finalizer, anatomy XP). Воспроизведены два R3-пропуска: death_pending→corpse failure и Rift session-clear→cleanup failure. Исполнитель исправляет оба; первоначальный verdict сохранён, финальная проверка pending.

## Изолированная инфраструктура
Ведущий проверил доступность Docker и существующие образы; созданы только временные контейнеры codex-a030102-pg-20261022 и codex-a030102-redis-20261022, без volumes, с localhost-only random ports. Никакие игровые хранилища не используются. PostgreSQL pg_isready successful. Adapter tests pending; cleanup обязателен до завершения.

## Параллельная работа
Пользователь подтвердил изменения других чатов в том же домене: одинаковые файлы ждать, разные части править самостоятельно. Наш исполнитель не редактирует combat manager/session и inventory, сохраняет внешние изменения. Их runtime/atomicity/durability работы не считаются нашей реализацией.

## Промежуточная adapter проверка
Исполнитель: 4 passed на disposable RedisJSON/PostgreSQL: uncertain EXEC + concurrency; journal freeze/row-lock/checkpoint rollback; expedition duplicate+closed-run replay; safe checkpoint+rehydration receipts. Независимый повтор запрошен, ещё pending.
Смежный Rift: из другого пользовательского чата подтверждён вывод legacy Rift из active build (tasks/active/2026-10-22-rift-alpha-retirement.md). Не исправляем архивируемый runtime и не меняем файлы его владельца. Наш финализатор для legacy snapshots сохраняет явный pending failure вместо фиктивного успеха/победы. Временная сломанная import chain инфраструктуры Rift мешает повтору worker tests; ожидаем стабилизации внешних изменений.


## Итоговая реализация
- R1 [x]: A03-01/02 подтверждены исходным кодом и regression failure до исправления.
- R2 [x]: XP owner-operation получает combat_id; Redis WATCH/EXEC атомарно применяет XP, receipt и dirty generation; SQL checkpoint сохраняет XP/receipt вместе и возвращает receipt при rehydration. Expedition receipt и pending XP фиксируются одной SQL-транзакцией под row lock, Redis-проекция повторяется абсолютным состоянием. Назначение награды (secured/конкретный expedition run_id) заморожено до применения. Формулы XP сохранены.
- R3 [x] в активном World/Expedition scope: SQL journal хранит frozen core до закрытия runtime, выполняет checkpoints под row lock; ошибки видимы worker, ARQ retry и recovery cron возобновляют pending. Архивирование имеет durable pending scanner и fallback к frozen core после потери cache. Death_pending/corpse и session dirty checkpoint возобновляются; старый бой не возвращает персонажа из нового состояния. SQL eligibility filter до LIMIT и keyset pagination предотвращают starvation на >100 записей.
- Legacy Rift, выводимый в архив отдельным поручением: явный blocked_retired с причиной; не finalized и не фиктивная победа. Исправление архивированного Rift runtime не заявляется.
- R4 [x]: независимый ревизор принял текущий стабильный срез, открытых actionable findings в нём нет.

## Финальные проверки
Исполнитель, стабильный срез после чужих коммитов 271a1d55/14b920a0:
- `.venv/Scripts/python.exe -m pytest tests/backend/features/combat/test_finalization_adapters.py tests/backend/features/combat/test_finalization_recovery.py tests/backend/features/combat/test_victory_finalizer_task.py tests/backend/features/combat/test_experience_finalizer.py tests/backend/features/combat/test_anatomy_regeneration_experience.py tests/backend/features/character/test_session_manager_runtime_refs.py tests/backend/features/character/test_session_persistence_service.py tests/backend/features/character/test_state_integrator_bootstrap.py tests/backend/features/expedition --no-cov -q --tb=short`: 87 passed, 11.18s; включает 7 real RedisJSON/PostgreSQL adapter tests. Explicit env указывали только disposable test stores, не app config.
- Ruff check всех 18 source/test файлов задачи: pass.
- Mypy `--no-incremental --follow-imports=silent` по 12 source файлам задачи: pass.
- SHA256 18 файлов до/после tests и mypy: без изменений. Scope и fingerprints: `tmp/codex/A03-01-02/source-fingerprints.json`.
- Ведущий: scoped `git diff --check` pass, текущие journal/owner receipts/SQL filter проверены чтением.

Независимый ревизор, последний стабильный запуск:
- 7 real adapters + 8 recovery + 7 victory tests: 22 passed, 6.66s, exit 0.
- 16 SHA256 source/test файлов до/после: HASH_DIFF_COUNT=0.
- R1/R2/R3/R4: pass на local+adapter уровне. Claims о owner dedup, frozen journal/recovery, death/dirty retry и явном retired блокировании подтверждены.
- Предыдущие 5 fail/9 pass произошли при transient pre-commit stash чужих разрешённых коммитов; источник установлен, после завершения hooks изменения восстановлены, финальные проверки повторены на стабильном состоянии. Это устранённая помеха проверки, не текущий дефект.

## Ограничения и состояние
Полный process-kill/restart реального ARQ, Mongo end-to-end, полный project gate и deployment не выполнялись. Новая миграция для нашего journal не нужна (использован существующий metadata JSONB). Существующие повреждённые результаты без frozen journal автоматически не переигрываются и не объявлены восстановленными. Тестовые контейнеры codex-a030102-pg-20261022 / codex-a030102-redis-20261022 удалены ведущим после ревизии. Игровые данные не изменялись. Commit/push/deploy в рамках этой задачи не выполнялись; чужие коммиты сохранены.

Статус: accepted. Independent review: pass. Приёмка пользователя: 22.10.2026, «Принимаю».


## Приёмка и коммит
22.10.2026 пользователь принял результат и поручил отметить A03-01/02 исправленными в реестре. Разрешён отдельный коммит только этой задачи. Чужие изменения исключаются. Для самостоятельности коммита exception retired-среза объявлен в Combat: зависимость от незакоммиченного Rift retirement module устранена без изменения поведения. После этой правки: 15 recovery/victory tests passed за 6.61s; Ruff passed. Штатные hooks запускаются при коммите.
Независимый ревизор повторно проверил локальную замену exception и адресные записи реестра: замечаний нет, pass R1–R4 сохраняется. Чужие записи реестра A03-13/A06-02 исключены из staged diff.
