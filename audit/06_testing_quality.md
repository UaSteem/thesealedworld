# Аудит 06/10 — Testing Strategy, Test Quality и Quality Gates

Дата: 09.10.2026. Проект: Sealed World / TurnBasedMMORPG. База Git: `6ccc9256`; объект аудита — **текущее рабочее дерево**, включая многочисленные исходные staged/unstaged/untracked изменения пользователя. Это не аттестация чистого HEAD или production. Предыдущие отчёты использованы как навигация, существенные выводы проверены по текущим файлам.

## 1. Executive Summary

Тесты хорошо защищают значительную часть чистой игровой логики, DTO, отдельных переходов состояния и серверного представления. Они существенно слабее защищают реальные хранилища, последовательности восстановления после ошибки, повторную доставку событий и совместную работу frontend/backend. Количество тестов не компенсирует эти пробелы.

Основные результаты:

- Найдено **304 test files**, AST содержит **2 606 test functions**. Pytest собирает **2 787 случаев из 303 модулей**, но завершает collection с **одной ошибкой**: оставшийся импорт удалённого `scripts.backfill_generated_assets_to_s3`. Полный штатный gate сейчас не может пройти collection.
- Завершённая репрезентативная выборка: **362 passed**, 39,37 с, два предупреждения. Команда завершилась с кодом **1 из-за coverage**, а не из-за упавших тестов: выборка покрыла **38,39% всего `src`** при глобальном пороге 74%. Это не общий coverage проекта.
- Более широкий диагностический запуск без сломанного модуля остановлен внешним лимитом 55 с: в сохранённом выводе **1 707 PASSED**, без завершённых FAILED/ERROR. Последний начавшийся тест — многосидовая генерация hex. Полного результата и пригодного итогового coverage этого запуска нет; это не доказательство нового зависания.
- Async-зависание воспроизведено **без pytest и без приложения**: `asyncio.new_event_loop()` внутри sandbox застревает в `socket.accept → _fallback_socketpair → ProactorEventLoop._make_self_pipe`. В разрешённом запуске вне sandbox та же операция и три выбранных async-теста завершились. Это ограничение данного окружения, а не доказанный deadlock Combat/Rift.
- Найден конкретный **ложно проходящий regression test** для A03-13: mock отключает bleed-триггер до проверки парирования. Штатный тест проходит; диагностический вызов того же теста с успешными бросками падает на `target.statuses.effects == []`. Production и файлы тестов не изменялись.
- Настоящие PostgreSQL/RedisJSON/Mongo/Streams integration suites и browser E2E в исследованном наборе не обнаружены. Есть полезные интеграции Python-компонентов, TestClient, MockTransport, stateful fakes; они не доказывают внешнюю атомарность или совместимость запросов с БД.
- Общий line-coverage threshold **74%** исполняется. Цель **≥90%** документирована. **100% patch coverage не контролируется и больше не является действующим требованием текущей testing strategy**. Branch coverage не включён.
- Для push в `develop` объявлены hooks и mypy, но нет pytest. PR в `develop` не входит в workflow trigger. Чистая CI-установка также не обеспечена: `codex-ai` ссылается на отсутствующий sibling path.

Реестр содержит 12 находок: 5 High, 5 Medium, 1 Low, 1 Observation. Новые ID относятся к тестовой системе и gate, а не повторяют игровые дефекты A03/A04. Исправления, новые тестовые файлы, изменения CI/skills, установки пакетов и deployment не выполнялись.

## 2. Методология и охват

Прочитаны действующие AGENTS, project/quality skills и references `project-rules`, `repository-operations`, `testing`, `validation`, `check-commands`; для специализированной проверки — combat/rift контекст. Применены cost-aware-delegation, project-skill-loader, verified-execution и диагностические ограничения ask-before-editing. Три независимые проверки охватывали CI/coverage, репрезентативные suites и известные дефекты; ведущий сверил ключевые источники, выполнил диагностику и подготовил отчёт.

Навигация: `audit/01_project_inventory.md`, `02_architecture_boundaries.md`, `03_combat_runtime.md`, `04_rift_world_generation.md`. Старый Graphify не использовался. Полный повторный аудит Combat, Rift и Persistence не проводился.

Методы: AST-инвентаризация всех `tests/**/test_*.py`, фактическая pytest collection, чтение test doubles и assertion вместе с соответствующим production path, анализ workflow predicates и установленного runner, ограниченные subprocess-запуски с timeout, read-only fixture validation. Тип теста определялся исполняемой границей, не именем файла.

Среда исполнения: Windows, `.venv/Scripts/python.exe`, **Python 3.14.3**, pytest **9.0.3**, pytest-asyncio **1.3.0**, pytest-cov **7.1.0**, pytest-mock **3.15.1**, coverage **7.13.5**, anyio **4.13.0**, httpx **0.28.1**. CI настраивает Python **3.13** (`.github/workflows/ci.yml:29,53`), поэтому локальный результат не является Linux/3.13-сертификацией. Новые зависимости не устанавливались; использована готовая venv, без `uv sync`.

### Журнал выполненных проверок

Во всех pytest-проверках отключались запись bytecode и pytest cache; `-o addopts=` убирал стандартный шум/coverage там, где он не нужен. Конфигурация проекта не менялась. Для измерения coverage использован отдельный `COVERAGE_FILE` в системном Temp, не корневой `.coverage`.

| Проверка | Результат и предел доказательства |
| --- | --- |
| `python -B -m pytest --collect-only -q -o addopts= -p no:cacheprovider` | Exit 2; 2 787 collected, 1 error, 17,27 с. Повторная collection с in-memory reporting plugin дала те же 2 787 items / 303 modules и marker counts |
| AST всех test files | 304 файла, 2 606 функций, ошибок разбора нет; учитывает три функции из модуля с ошибкой импорта |
| `asyncio.new_event_loop()` в дочернем Python; dump через 3 с, timeout 8 с | Sandbox: зависание до приложения; процесс завершён внешним timeout |
| Два теста `tests/shared/test_log_task_wrapper.py` в sandbox | Timeout 8 с на первом async-тесте; не считается test failure |
| Те же два теста + `test_runtime_processors.py::test_crit_bleed_trigger_is_cancelled_when_attack_is_parried` вне sandbox | **3 passed in 2.70s**, exit 0; также отдельно успешно создан/закрыт ProactorEventLoop |
| `pytest tests --ignore=tests/backend/features/generation_ai/test_asset_backfill.py` с отдельным coverage, timeout 55 с | Незавершённая диагностика: 1 707 строк PASSED, далее начат hex shape test. Нет итогового verdict/coverage; исключение модуля не предлагается как исправление gate |
| Завершённая выборка ниже с отдельным coverage, timeout 50 с | **362 passed**, 2 warnings, 39,37 с; exit 1 исключительно по coverage, 23 471 / 61 145 statements = 38,39% |
| Существующий parry-test, вызванный в памяти с другим mock RNG | С успешными бросками проваливается assertion на строке 5570; детали §4, §10 |
| `python -B tools/validators/run.py` | Exit 0: `Fixture validation passed.` |

Завершённая coverage-выборка состояла из:

```text
tests/backend/features/character/test_state_integrator_bootstrap.py
tests/backend/features/inventory/test_inventory_service.py
tests/backend/features/items/test_instance_repository.py
tests/backend/features/loot/test_loot_integration.py
tests/backend/features/world/test_navigation_service.py
tests/backend/features/scenario/test_evaluator.py
tests/backend/features/scenario/test_scenario_repository.py
tests/backend/features/generation_ai/test_generation_ai_core.py
tests/backend/core/bus
tests/backend/core/test_arq_queue_routing.py
tests/backend/features/rift/services/test_player_service.py
tests/backend/features/rift/integrations/test_runtime_integration.py
tests/frontend/features/cabinet
tests/frontend/features/auth
tests/shared
tests/fastapi_cabinet
```

Аргументы: `-q -o addopts= -o log_cli=false -p no:cacheprovider --cov=src --cov-report=json:<temp>/coverage.json --tb=short --basetemp=<temp>/pytest`. Лимит задавался через `subprocess.run(..., timeout=50)`; `COVERAGE_FILE=<temp>/.coverage`, `PYTHONDONTWRITEBYTECODE=1`. Сохранённые диагностические артефакты текущей машины: `C:/Users/prime/AppData/Local/Temp/a06-focused-dpk9i2kn/{run.txt,coverage.json,.coverage}`; вывод незавершённого запуска — `C:/Users/prime/AppData/Local/Temp/a06-testing-qmb3r9hy/run.txt`. Temp не является постоянным хранилищем отчёта; существенные результаты перенесены сюда.

## 3. Инвентаризация тестов

### Фактическое распределение

Под test file понимается файл, подходящий `python_files = ["test_*.py"]` внутри `testpaths=["tests"]` (`pyproject.toml:152-165`). В исходниках вне `tests` есть dev-модули со словом test, но они не входят в эту collection. Функции AST и pytest cases различаются из-за параметризации, наследуемых markers и failed import.

| Область | Test files | Собранные cases |
| --- | ---: | ---: |
| Backend, всего | 215 | 2 115 |
| Frontend, всего | 64 | 582 |
| FastAPI Cabinet, отдельный контракт библиотеки | 7 | 22 |
| Shared | 10 | 39 |
| Studio | 1 | 1 |
| Telegram bot | 2 | 6 |
| Tools | 3 | 13 |
| `tests/unit/arena/runtime` | 2 | 9 |
| **Итого** | **304** | **2 787**, collection error в одном файле |

| Backend feature | Файлы | Cases |
| --- | ---: | ---: |
| Combat | 30 | 784 |
| Character | 15 | 123 |
| Inventory | 5 | 40 |
| Items | 9 | 92 |
| Loot | 6 | 28 |
| Rift | 16 | 160 |
| World | 9 | 56 |
| Exploration | 10 | 64 |
| Scenario | 16 | 160 |
| GenerationAI | 5 | 35; один из пяти модулей не импортируется |
| Monsters | 36 | 210 |
| Game catalog | 3 | 24 |
| Game lobby | 4 | 27 |
| Game session | 1 | 23 |
| Expedition | 1 | 7 |
| Arena | 3 | 23 |
| City services | 1 | 11 |
| Admin players | 3 | 8 |
| NPC | 2 | 4 |
| System | 2 | 4 |
| Межфичевые файлы в `features/` | 2 | 25 |

Остальные backend: core — 17 файлов / 87 cases; infrastructure — 8 / 49; realtime — 8 / 60; chat — 2 / 7; test_app — 1 / 4. В frontend: auth — 61 case, cabinet — 105, account — 30, email — 8, feedback — 17, public_site — 9, surveys — 10; остальные core/game_features/integrations/root — 342.

### Уровни, fixtures и инструменты

| Категория | Наблюдение |
| --- | --- |
| Markers | Зарегистрированы `unit`, `integration`. Реальные collected items: unit — **1 529**, asyncio — **1 070**, parametrize — **227**. `integration`/E2E markers не найдены. Markers пересекаются и не определяют реальную изоляцию |
| Async | AST: **1 061 async test functions**, 1 545 sync. Pytest auto mode добавляет asyncio marker и учитывает параметризацию; поэтому 1 070 items не противоречат 1 061 definitions |
| Параметризация | **43** `parametrize` decorators; 227 collected items имеют этот marker. Это не 227 независимых test definitions |
| Fixtures | **86** fixture definitions внутри test files + **7** в conftest = **93**. Async fixture definitions в этих файлах не обнаружены. Все найденные conftest: backend, frontend, combat, realtime; последний содержит FakeWebSocket, не fixture |
| Fakes | **309** классов с префиксами Fake/Dummy/Stub/InMemory в test files — нижняя эвристическая оценка, не число всех doubles. Есть также `_FakeLogger`, nested doubles, conftest-классы |
| Mocks | **76** test files содержат AsyncMock/MagicMock/unittest.mock/mocker. Monkeypatch применяется и вне них. Число не оценивает качество |
| Builders | Локальные `actor`, `stats`, `make_*`, `build_*`, `create_*`; 70 helper definitions по этой эвристике, не все являются фабриками. Общего обязательного builder framework не обнаружено |
| Unit | Чистые math/DTO/catalog tests; service tests с in-memory dependency; отрицательные/граничные cases. Это основа набора |
| Component interaction | Настоящие несколько Python-компонентов с fake storage; ASGI/TestClient, MockTransport; например Combat simulator использует настоящий executor (`test_simulation.py:765`) |
| Настоящая инфраструктура | Не обнаружены исполняемые suites с поднятым PostgreSQL, RedisJSON, MongoDB, Redis Streams/ARQ worker или их testcontainers. Нет DB-backed fixture с rollback/test schema |
| E2E/browser | Playwright/Selenium/browser journey не обнаружены. TestClient не исполняет браузерный JS/HTMX/WebSocket |
| Property-based | Hypothesis не установлен и не объявлен. **Инвариантные тесты есть**: многосидовые hex loops, симметрия arena rating, DTO roundtrip/структуры. Это примерные property-style проверки без shrinking/генеративного движка |
| Mutation | mutmut не установлен; mutation job/config не найдены. Mutation score не измерялся |
| Security | Есть реальные unit/API assertions для подписи/expiry токенов, паролей, CSRF, headers, auth redirects. Это не полный security audit и не автоматическая проверка всех trust boundaries |
| Performance | Нет выделенного benchmark/load suite и latency/SLO gate. Лимиты simulation и запрет wall-clock sleep проверяются функционально (`test_simulation.py:850,928`), не измеряют production throughput |

`tests/backend/conftest.py:146-169` подменяет bootstrap контейнеров; `tests/frontend/conftest.py:8-22` отключает DB startup/rollup. Документированный layout с `tests/conftest.py`/`tests/shared/conftest.py` — целевая схема, не фактическое наличие этих файлов.

## 4. Качество unit-тестов

| Домен и образец | Что действительно защищено | Предел / риск |
| --- | --- | --- |
| Combat: `test_runtime_processors.py`, `runtime/engine/test_resolver_trigger_contract.py:126-157`, `test_simulation.py:765` | Настоящий resolver/pipeline/executor, flags, damage/effects/tokens, branch outcomes; simulation не дублирует damage-алгоритм | Некоторые mocks задают порядок внутренних RNG-вызовов. A06-02 — конкретный ложный pass. Не все tests с названием regression достигают нужного precondition |
| Character: `test_state_integrator_bootstrap.py:185-213` | Поля восстановленной active session, состояние и проекции, не только вызов метода | Fake persistence не доказывает совместимость SQL/Mongo/Redis или восстановление после реального рестарта |
| Inventory: `test_inventory_service.py:112-149,640` | Изменение projection и TTL в stateful fake, запрет действия в scenario state | FakeRedis сохраняет ссылки на dict и не моделирует серверную сериализацию/атомарность; SQL ownership/конкурентный transfer не проверен реальной БД |
| Items: `test_instance_repository.py:16-30,34-70` | Проверяются созданные ORM-объекты, durability/material/affixes | FakeSession принимает объект и возвращает подготовленный результат; неправильный SQL predicate/constraint может остаться невидимым |
| Loot: `test_loot_integration.py:11-59,92-155` | Реальный adapter, значения corpse/TTL; integer TTL — полезная регрессия | Это integration объекта, не Redis; exactly-once claim не следует из единичного fake enqueue |
| Rift: `test_hex_generator.py:38-94`, `runtime/test_zone_generation.py:306-557` | BFS-достижимость, ограничения формы, события и gates; множество сценариев | Same-process seeds не защищают от PYTHONHASHSEED; runtime payload test не проверяет доверие к данным клиента |
| World: `test_navigation_service.py:27-151`, `test_node_graph.py` | Стоимость движения, заблокированные выходы, графовые переходы | Фактические persistence и межпроцессная детерминированность отдельно не аттестованы |
| Exploration: `test_encounter_integration.py:15-103`, `test_knowledge_service.py:10-45` | Семантика adapter и изолированный XP cap | Изолированный cap не гарантирует, что штатная сборка вообще подключила ограничитель (A04-08) |
| Scenario: `test_evaluator.py:10-29`, `test_scenario_repository.py:12-21,42-45` | Условия evaluator проверяют наблюдаемый результат; ошибки/пустые результаты присутствуют | `upsert_master` assertion только на `execute.assert_called_once()` не различает правильный и неправильный SQL |
| GenerationAI: `test_generation_ai_core.py:98-107,348-403,439-598` | State transitions, ошибки provider/schema, enqueue/retry через fake repository | Fake claim не исполняет SQL attempt/time/locking predicates; retry mismatch на поздней попытке невидим |
| Frontend/site: `features/public_site/test_play_entry.py:11-107`, auth/account/cabinet suites | HTTP status, redirect/cookies, серверный HTML, формы и обработка ошибок | Строка в шаблоне не доказывает выполнение JS, HTMX swap, responsive/accessibility или корректную связку backend response → UI |
| Shared: `schemas/test_inventory_contract.py:28-63`, `test_url_utils.py`, `test_log_task_wrapper.py:31-102` | DTO shape/serialization, URL policy, logging success/failure с cleanup | Изолированный DTO-тест не доказывает, что обе стороны используют тот же DTO на wire |
| FastAPI Cabinet: `tests/fastapi_cabinet/test_site.py:35-88`, `frontend/features/cabinet/test_cabinet_integration.py:9-28` | Реально монтируются library routes/assets и consumer modules, проверяется rendering | Reduced app не эквивалентна защищённому production `/admin` и browser journey |

### Подтверждённый ложный pass: crit-bleed после parry

`tests/backend/features/combat/test_runtime_processors.py:5540-5571` выглядит как сильный regression: гарантированные crit/parry, проверка tokens, отсутствие effects/APPLY_EFFECT. Однако строка 5556 задаёт последовательность `[(0, True), (0, True), (1, False), (0, True)]`.

Реальная последовательность: accuracy → crit → **ON_CRIT trigger roll** → parry. `resolver/orchestrator.py:47-59`, `steps/crit.py:68-85`, `support/trigger_activator.py:161-180`. Третий mock result отменяет сам trigger, несмотря на его chance=1.0. Тест не проверяет `trigger_attempts.passed`/`fired_triggers`, поэтому пустые effects достигаются без проверки отмены эффекта защитой.

Эксперимент:

1. Штатный pytest node прошёл вне sandbox.
2. Тот же существующий test function вызван через `asyncio.run`, с временным subclass `pytest.MonkeyPatch`, перехватывающим только назначение `MathCore.roll_chance` и возвращающим `(0.0, True)`; файлы/production implementation не менялись.
3. Первый диагностический вариант с четырьмя успешными results дошёл до **пятого** броска сопротивления эффекта и закончился StopIteration. Это промежуточный незавершённый probe, не regression verdict.
4. Вариант с успешными results для всех вызовов дал пять бросков (chances 0.9, 1.0, 1.0, 1.0, 1.0) и **AssertionError на строке 5570**: `target.statuses.effects == []`. Assertion был пойман диагностической оболочкой, поэтому её exit 0 не означает pass.

Это A06-02: неверный setup теста скрывает уже известный A03-13. Минимальная будущая регрессия должна подтвердить активацию trigger до проверки отсутствия эффекта после parry; positive control должен показать эффект при контакте. Заменять всю реальную pipeline mock-объектом не нужно.

### Изоляция, хрупкость, порядок

Stateful fakes, локальные fixtures и monkeypatch с восстановлением — сильная основа. Но `FakeRedisClient.set/get` и `FakePipeline` в `tests/backend/conftest.py:16-39,80-128` сохраняют/возвращают Python dict без wire roundtrip, не реализуют WATCH/Lua/изоляцию, лишь последовательно воспроизводят команды. Время TTL записывается, не течёт. Это полезный double, но не семантический эквивалент RedisJSON.

Backend `app` fixture мутирует singleton `app.state`, не восстанавливая исходные значения (`conftest.py:149-159`); frontend очищает dependency overrides (`frontend/conftest.py:21-22`). Отсюда есть риск зависимости от порядка, но shuffled/reverse-order запуск не выполнен: подтверждённого загрязнения конкретного теста нет. Import-time registry initialization видна в библиотеках abilities/effects/triggers/monsters; настройки окружения также участвуют в импортах. Combat conftest удаляет `COMBAT_AI_POLICY_PATH` через monkeypatch — хорошая локальная изоляция.

Assertions по source text/именам путей пригодны для узкого запрета legacy shape, но хрупки при эквивалентном рефакторинге и слабы для поведения. Особенно `test_infrastructure_boundaries.py` и frontend template contracts следует дополнять проверкой наблюдаемой границы, не заменять всё snapshot-строками.

## 5. Integration и contract coverage

Ни один `FakeRedis` не считается доказательством атомарности настоящего Redis. В таблице «компонентный» означает совместное исполнение Python-частей, иногда с fake storage, а не живую инфраструктуру.

| Граница | Фактическая защита | Что может пройти незамеченным / минимальное будущее доказательство |
| --- | --- | --- |
| Character ↔ Inventory | Character bootstrap и inventory state/projection tests; настоящие DTO/builders с fake state (`test_state_integrator_bootstrap.py:185`, `test_inventory_service.py:112`) | SQL ownership, гидратация актуального item shape, rollback экипировки; совместный scenario с реальными доменными adapters + один PostgreSQL contract |
| Combat ↔ Rift | Реальная Rift result application с fake stores (`rift/integrations/test_combat_result_runtime.py:130,185`); finalizer fake Rift integration (`test_victory_finalizer_task.py:314`) | Missing Combat → false victory, повторное применение результата, origin/trust. Связать настоящий SystemIntegrator и RiftRuntimeIntegration с in-memory storage, затем recovery/fault case |
| Combat ↔ Expedition | `expedition/test_expedition_notices.py:66-177`: death/respawn/safe sync/TTL через FakePublisher/FakeLootManager | Общая finalization → corpse → respawn цепочка и durable recovery не исполняются; component lifecycle + DB/Redis recovery |
| Combat ↔ Loot | Finalizer, corpse/result routing, loot adapters тестируются отдельно | Порядок публикации и поздняя corpse map, duplicate rewards, crash between stores. Stateful producer/consumer scenario, отдельно Streams retry test |
| GameSession ↔ Loot | `game_session/test_session_service.py:585,619,655,704`: enqueue, batching, next state, unavailable queue | Claim worker persistence/duplicates не следуют из fake enqueue; связать job payload с worker и проверить награду ровно один раз |
| Frontend ↔ Backend | Shared DTO, backend TestClient, frontend MockTransport (`test_game_settings_module.py:18-20,257-401`, `test_internal_routers.py:105-164`) | Отдельные fixtures могут согласованно отстать от реального response/request; нужен ASGI-backed consumer→real backend router test с fake persistence |
| Streams producer ↔ consumer | `core/bus/test_producer.py:1-60` проверяет имя/корреляцию/TTL вызова mock transport; `test_router.py:6-18` регистрацию handler; feature handler tests | Нет общего каталога producer event → actual registered handler → schema/return. Неверное событие в непроверенном пути, сериализация, ACK/reclaim/redelivery/consumer group остаются открыты |
| ARQ enqueue ↔ registration | `core/test_arq_queue_routing.py:9-52` проверяет queues и отдельные system jobs; `combat/test_ai_simulation_admin.py:818-845` timeout/max tries; enqueue assertions в service tests | Полезная частичная contract protection, но не исчерпывающий producer→queue→worker реестр и не реальный ARQ dispatch |
| PostgreSQL repo ↔ SQLAlchemy | ORM constructors и query construction с FakeSession/AsyncMock; transaction context commit/rollback (`core/database/test_session.py:23-77`) | SQL dialect, миграции, constraints, JSON operators, on-conflict, isolation/locks не проверены реальным сервером |
| Redis managers ↔ RedisJSON | FakeRedis + session manager tests, формы command/pipeline/TTL | JSONPath result shape, сериализация, TTL expiry, transaction=False partial write, Lua/CAS/connection failure. Нужен небольшой suite Redis Stack |
| Mongo repos ↔ MongoDB | `infrastructure/mongo/test_bootstrap.py:11-39` проверяет вызов ensure_indexes fake repositories; snapshot orchestration uses doubles | Индексы/уникальность/BSON/replace-upsert/query/доступность snapshot после restart не исполняются; нужен disposable Mongo contract |
| FastAPI Cabinet ↔ consumer | Реальная библиотека + зарегистрированные project modules в reduced FastAPI, routes/assets rendering | Неполное доказательство admin auth и frontend backend wiring; один consumer access/action contract и browser smoke |

DTO и public facade защищены там, где тест импортирует/создаёт настоящий объект и проверяет структуру. Event-name assertions точечные; они не образуют полной проверки producer/consumer совместимости. Ownership частично проверяется бизнес-отказами/архитектурным scan, но глобальной автоматической защиты нет. Сериализация частично проверяется DTO, однако fakes не вынуждают настоящий bytes/JSON/BSON roundtrip. Commit/rollback **вызван** и transaction **обеспечила инвариант** — разные утверждения.

Приоритет для pre-alpha — несколько дорогих границ, а не инфраструктура на каждый unit-test: inventory transfer, combat finalization/retry, GenerationAI SQL claim, RedisJSON exchange commit, initial Rift snapshot/restore.

## 6. E2E readiness

Browser suite в текущем checkout не обнаружен; dependencies и workflows его не запускают. Это соответствует явному отложенному E2E-плану (`docs/ru/management/testing_strategy.md:9-13,116-122`), поэтому отсутствие полного browser coverage не объявляется самостоятельным High-дефектом.

| Пользовательская цепочка | Уже имеющееся доказательство | Чего нет |
| --- | --- | --- |
| Регистрация/вход | Auth service/routes, redirects, cookies, token cases (`tests/frontend/features/auth/`, `backend/core/test_security.py`) | Browser submit → persisted account → cookie/session через реальные frontend/backend |
| Создание персонажа, старт session | Lobby и Character/GameSession tests с fakes | Полный frontend→backend→storage journey |
| Перемещение, encounter, combat | Navigation, encounter, runtime/pipeline/simulation | Browser action и live updates, реальная очередь, recovery при disconnect |
| Награда и Inventory | Claim enqueue/DTO/projection/unit behavior | Combat→claim→durable item balance→UI, включая повтор |
| Rift | Runtime state/gates/restore с fake stores | Реальный пользовательский проход с combat и восстановлением после потери Redis |
| Logout/reconnect | Auth expired/session replaced routes и cookie cleanup | Браузер с live connection, повторный вход, корректная восстановленная игровая панель |
| Админка | Mounted Cabinet rendering, modules, MockTransport actions | Реальная роль/отказ обычному игроку + отправка admin action + backend result в UI |
| Site/account | Account/auth/public/feedback tests | Browser validation, JS, переходы, реальные email delivery и persistence |

Минимальный будущий набор после стабилизации контрактов:

1. Seeded пользователь: вход → lobby → выбор/создание персонажа → старт session → одно перемещение; проверить cookie, активный персонаж и обновлённую панель.
2. Контролируемый encounter → combat → награда → Inventory; повторный claim/refresh не увеличивает баланс. Сначала компонентный сценарий, затем один browser smoke.
3. Вход в существующий Rift → combat/переход → reconnect/восстановление. Проверить фактическое состояние, не только отсутствие ошибки страницы.
4. Admin/non-admin: доступ к `/admin`, одно обратимое обновление настройки и её чтение через настоящий backend route; обычный пользователь получает отказ.

Это проверки уже имеющихся routes/services, не требования тестировать ещё не реализованный контент. Для pre-alpha не нужен E2E на каждый вариант монстра, ability или layout.

## 7. Coverage и patch coverage

| Вид | Фактическое состояние |
| --- | --- |
| Enforceable global threshold | `fail_under = 74`, `pyproject.toml:176-178`; pytest-cov включён стандартным addopts на `src` |
| Документированная цель | ≥90%, `docs/ru/management/testing_strategy.md:17` |
| Patch threshold | Автоматического diff-cover/Codecov patch job, comparison base и fail-under для changed lines не найдено |
| Требование «100% patch» | **Не действует в текущих прочитанных правилах**: strategy `:23-28` и quality `references/testing.md:7-9` явно отказываются от произвольного процента для каждой правки. Не следует приписывать проекту старую политику |
| Branch coverage | `[tool.coverage.run]` не задаёт `branch=true`, команды не добавляют `--cov-branch`; измеряются statements, не альтернативы условий |
| Omits | `*/migrations/*`, `*/tests/*`, `*/conftest.py` (`pyproject.toml:168-173`). Это patterns, не автоматическое исключение всех Alembic-файлов |
| Exclusions | pragma no cover, raise NotImplementedError, TYPE_CHECKING, main guard (`:179-184`). В свежем частичном отчёте 1 019 excluded lines; аудит каждой такой строки не выполнен |
| Старый `.coverage` | 356 352 bytes, timestamp 19.06.2026 17:47:33 UTC; не использован как текущий coverage и не перезаписан |
| Измерено сейчас | Завершённая выборка 362 tests: 23 471 covered / 61 145 statements, **38,3858%**, exit 1 по сохранённому порогу |
| Общее актуальное покрытие | **Не установлено**: штатная suite имеет collection blocker, широкий диагностический run ограничен временем |

Глобальный порог действительно сработал на частичной выборке, но такой fail не доказывает регрессию общего покрытия. Обходить порог для обычного gate не предлагается. Точечная проверка поведения без coverage использовала `-o addopts=` исключительно для диагностики.

Ни 74%, ни 90%, ни гипотетические 100% lines не докажут правильность transaction boundary или достижения trigger precondition. A06-02 показывает это на существующем тесте. Дополнительные тесты должны отличать неверное поведение от верного; заполнение строк assertions без такого различия не является улучшением.

## 8. CI/CD Quality Gates

### События и исполняемые команды

| Событие | Объявленное поведение | Ограничение |
| --- | --- | --- |
| Локально | `uv run pre-commit run --all-files`; mypy; `uv run pytest`; полный `uv run python tools/dev/check.py` | Установка git hook/факт запуска пользователем не проверялись. Hooks с `--fix` могут менять файлы; полный runner в аудите не запускался |
| Push в develop | `ci.yml:19-41`: `uv sync`, pre-commit, mypy | Нет pytest/coverage/validators/MkDocs |
| PR в develop | `ci.yml:3-6` допускает только main | Этот CI workflow не запускается |
| PR в main | `ci.yml:43-66`: all-groups sync, `check.py --ci` | Branch protection/required checks с сервера GitHub не запрашивались |
| Merge/push в main | Тот же full gate, затем `docker-build needs: quality` | Пять build checks: site/game/chat/worker/nginx; Docker build не означает runtime smoke |
| Release tag v* / ручной image build | `build-images.yml:3-43`: full gate → build/push images | Gate задуман обязательным через needs; выполнение зависит от установки deps |
| Production deployment | Ручной workflow: SSH preflight → deploy, `deploy-production.yml:3-44` | Не проверяет successful quality для выбранного image_ref; compose `up --wait` проверяет доступную container health, не игровой сценарий |

### Инструменты и реальная роль

- **Pre-commit** (`.pre-commit-config.yaml:3-84`): whitespace/end-of-file, YAML/JSON/large files, Ruff lint/format, Markdownlint, Bandit, pip-audit, detect-secrets, hadolint wrapper, djLint. Ruff и Markdownlint запускаются с `--fix`. Это объявленный набор, не утверждение о его успешном прохождении сейчас.
- **Ruff**: Python 3.13 target; `tests`, `tools`, `temp`, `archive` исключены конфигурацией (`pyproject.toml:85-93`). Нельзя утверждать, что общий lint полностью контролирует test code.
- **Mypy**: `src tools`, non-strict, `ignore_missing_imports=true`, `call-arg` отключён, большой список `ignore_errors=true` (`pyproject.toml:99-150`). Полезный gate, но не полноценная статическая проверка межфичевых контрактов.
- **Bandit**: skips и исключения tests/tools (`pyproject.toml:186-190`); это выбранная политика, не полный security proof.
- **Pip-audit**: runner `uv run pip-audit` проверяет project environment. Remote pre-commit hook работает в отдельном Python environment, получает `--local` без requirements/project input и **не является эквивалентной проверкой приложения** (A06-12). Их ignore-list также расходятся: runner дополнительно исключает `CVE-2026-45409` (`pyproject.toml:198-199`), hook — нет (`.pre-commit-config.yaml:43-60`). Текущая уязвимость/фактический fail не проверялись; зафиксированы различие охвата и policy drift.
- **Detect-secrets**, Markdownlint, **MkDocs** есть в автоматизации; MkDocs добавляется project runner через `uv run --group docs mkdocs build --clean` (`tools/dev/check.py:32-37`). Не запускался из-за ненужных генерируемых изменений для read-only аудита.
- **Pytest/coverage**: runner использует все `tests`; threshold из config. `test-stages=["unit"]`, но `test-markers={unit=""}` (`pyproject.toml:200-205`) означает отсутствие `-m`, не только unit.
- **Validators**: items/skills/scenario (`tools/validators/run.py:11-28`), локально прошли. Не следует называть это валидацией всех данных World/Rift.
- **Architecture**: `test_infrastructure_boundaries.py:1-77` проверяет перемещение отдельных managers/legacy paths и шесть Redis prefixes; Rift явно исключён из scan. Все ownership/import rules этим не охвачены.

### Переносимость runner и зависимостей

Исследован **установленный** `.venv/Lib/site-packages/codex_core/dev/check_runner.py`, а не только соседний checkout библиотеки. `run_ci:470-500` выполняет lint, types, security, extras и test stages, затем fail при любом false. `_test_command:343-353` добавляет marker только для непустой строки. Таким образом stage `unit` действительно запускает всё.

`tools/dev/check.py:8-17` сначала может подложить `C:/install/projects/codex_tools/codex-core/src`, затем импортирует пакет. На текущей машине использован installed module, поэтому **отсутствие hardcoded path само по себе не ломает runner**. Но при наличии пути другой версии он меняет источник реализации. Следует сохранить воспроизводимость версии и убрать зависимость поведения от случайного локального каталога; это portability risk, не доказанный текущий failure.

Более конкретный блокер — `pyproject.toml:34-35` и `uv.lock:470-471`: `codex-ai` берётся из `../../codex_tools/codex-ai`. Чистый Actions checkout не создаёт этот каталог; workflow не fetch/copy его перед `uv sync`. Проверка dependency graph на чистом runner поэтому не обеспечена (A06-05). Существующая локальная venv позволяет запускать тесты, но не подтверждает переносимость `uv sync`. Actual hosted logs и remote status в этот аудит не входили.

## 9. Async pytest investigation

### Локализация

Минимальный дочерний процесс:

```python
import faulthandler
faulthandler.dump_traceback_later(3)
import asyncio
print("before loop", flush=True)
loop = asyncio.new_event_loop()
print(type(loop).__name__, flush=True)
loop.close()
```

В sandbox процесс не завершился за 8 с; stack:

```text
socket.py:298 accept
socket.py:633 _fallback_socketpair
asyncio/proactor_events.py:786 _make_self_pipe
asyncio/proactor_events.py:639 __init__
asyncio/windows_events.py:316 __init__
asyncio/events.py:732,844 new_event_loop
```

Тот же bounded subprocess вне sandbox: exit 0, напечатан `ProactorEventLoop`, loop закрыт. Изолированные logger tests и combat parry test завершились 3 passed. Уже после этого завершилась выборка с async/TestClient — 362 passed. Первоначальная диагностическая оболочка один раз ошиблась на `.decode()` уже строкового TimeoutExpired output; она исправлена в памяти, а минимальный probe повторён успешно. Эта ошибка оболочки не классифицируется как дефект проекта.

**Вывод:** доказанная точка блокировки — создание self-pipe средствами стандартной библиотеки в sandbox. Смена режима исполнения снимает блокировку. Конкретный низкоуровневый механизм sandbox/firewall/loopback не установлен; утверждать определённое сетевое правило без диагностики ОС нельзя. Достаточно доказано, что зависание не требует приложения, pytest, fixtures или внешнего storage.

### Проверенные альтернативы

| Возможная причина | Результат |
| --- | --- |
| Sandbox/окружение агента | Подтверждено сравнением одинакового stdlib probe в двух режимах |
| Ошибка pytest-asyncio config | `asyncio_mode=auto` (`pyproject.toml:154`); нет custom event_loop fixture. Plugin 1.3.0 использует default test loop scope=function (`plugin.py:118-122`). Ошибка конфигурации как причина данного зависания не подтверждена |
| Async fixture teardown | В проектных tests/conftest async fixture definitions не найдены. Проблема возникает до исполнения test coroutine; нет доказательства дефектного teardown |
| TestClient/AsyncClient lifespan | Вне sandbox есть успешно завершённые TestClient-тесты. Frontend lifespan создаёт rollup task, отменяет и await-ит её, закрывает http client/DB (`src/frontend/app.py:158-169`); fixture заменяет rollup/DB на noop |
| Background tasks / pending tasks | Backend lifecycle содержит stop/close (`src/backend/core/lifespan.py:99-115`). Их production shutdown в реальной инфраструктуре не проверен. Подтверждённых pending-task leaks по завершённой выборке нет |
| Plugin conflict | Stdlib reproduction обходится вообще без plugins, поэтому конфликт не нужен для объяснения. Полная матрица disabled/autoload plugins не запускалась — на найденную причину она не влияет |
| Настоящий application deadlock | Для воспроизведённого случая опровергается отсутствием приложения в probe. Другие deadlocks без живой инфраструктуры не исключены |
| Поздний timeout широкого run | На 55 с suite дошла до sync hex multi-seed generation; это отдельный time budget, не повтор Proactor setup hang |

Минимальное направление: для диагностики сначала короткий stdlib loop probe; при таком stack использовать разрешённое рабочее окружение, сохранять внешний timeout и traceback. Не «чинить» Combat/Rift сменой loop policy без доказательства; Selector loop также использует socketpair и не является обоснованным универсальным решением. Полезен bounded timeout/diagnostic artifact для CI, но конкретная pytest-timeout dependency сейчас не устанавливалась. Наличие тестовых timeout в приложении ARQ не ограничивает сам pytest process.

## 10. Property-based / mutation opportunities

Уже есть полезные invariants: `test_hex_generator.py:66-94` перебирает 20 seeds и проверяет геометрию; `tests/unit/arena/runtime/test_rating.py` — симметрию/нулевую сумму; resolver suites проверяют границы. Hypothesis не нужен для каждой service wrapper.

| Приоритет | Свойство | Дешёвая форма / будущий эксперимент |
| --- | --- | --- |
| Высокий | Combat contact/effect | Матрица miss/dodge/parry/block/hit × crit × успешный trigger; проверить preconditions, effect/event и tokens независимо. A06-02 доказывает ценность |
| Высокий | Inventory conservation | Для последовательности equip/unequip/transfer/retry сумма предметов и ресурсов сохраняется, один item имеет одного владельца; in-memory state machine + несколько real-DB boundary cases |
| Высокий | Idempotent event/finalization | Дублирование, перестановка, crash after each side effect не меняют итоговый reward и позволяют завершение; component/fault injection, отдельно durable restart |
| Высокий | Rift connectivity/determinism | BFS всех обязательных узлов, валидные edges, одинаковая нормализованная topology при одинаковом seed в отдельных процессах с `PYTHONHASHSEED=1,2,3` |
| Средний | Hex neighbor symmetry | Для внутренних клеток соседство симметрично; для границ нет wraparound; сравнивать полный диапазон размеров/parity |
| Средний | World coordinate transforms | Roundtrip и соседство на положительных/отрицательных координатах, границах/parity; не копировать implementation formula в ожидаемый результат |
| Средний | Serialization roundtrip | `model_dump(mode="json") → JSON → model_validate`, RedisJSON/BSON integration для dates/enums/optional; сохранить semantic state |
| Средний | Resource balance | HP/resources bounds, стоимость ровно один раз, отсутствие отрицательного расхода при reject/retry; зафиксировать реальные допускаемые overcap правила |

Mutation tooling отсутствует. Production code ради mutation не менялся; **mutation score не заявляется**. Контролируемое изменение test RNG в памяти (§4) — проверка достижимости ветки, не полноценная mutation campaign.

Воспроизводимый будущий узкий mutation experiment: в отдельном disposable checkout выбрать `_effect_conditions_met` и финальные contact guards; сначала зелёная focal suite, затем по одному mutant (инвертировать contact flag, убрать condition, перепутать parry/block); для каждого прогнать конкретные nodes с timeout. Mutant считается killed только содержательным assertion, отдельно учитывать timeout/import error и equivalent mutants. Второй участок — attempt comparison GenerationAI, где важен реальный SQL claim, а не копия условия в fake. Не масштабировать mutation на всю кодовую базу до устранения collection blocker и vacuous test.

## 11. Known defects versus existing tests

Эта таблица оценивает тестовую защиту известных находок. Она не вводит новые ID для самих игровых багов и не утверждает, что все были повторно воспроизведены live. Ссылки ниже — текущие тесты и соответствующие production границы.

| Дефект | Существующая защита и причина пропуска | Минимальные assertions / подходящий уровень | Реальная инфраструктура |
| --- | --- | --- | --- |
| **A03-01 duplicate XP** | `test_experience_finalizer.py:229`, `test_victory_finalizer_task.py:175`: один happy-path вызов/fake progression. Нет повторного одного combat_id и cumulative persisted delta; finalizer `workers/tasks/victory_finalizer_task.py:71-85` | Дважды/конкурентно обработать один результат, assert XP delta на combat+character ровно один раз; crash после XP до finalization record → retry | Stateful fake достаточен для последовательного regression; SQL/Redis нужен для durable/concurrent claim |
| **A03-02 partial finalization** | Finalizer tests `:175,242,314,344` преимущественно успешные ветви. Реальные шаги/except: `workers/tasks/victory_finalizer_task.py:71-134`; inactive gate в `collector_task.py:76-83` | Failure после winner, vitals, XP, cache, enqueue; assert unfinished остаётся обнаружимым, retry завершает все шаги, награда не удваивается | Component faulting fake сначала; отдельный restart/fault-injection на настоящих stores |
| **A03-03 non-atomic exchange** | `test_session_store.py:293,317,330,382` проверяет успешные документы/команды; manager `infrastructure/combat/managers/session.py:608` использует transaction=False | Ошибка k-й RedisJSON-команды/обрыв; assert согласованность actor+queue+step+logs либо явная recoverability; не выдавать последовательный FakePipeline за атомарность | Настоящий Redis Stack и fault injection необходимы для strong claim; fake лишь моделирует известный сценарий |
| **A03-04 duplicate creation** | `test_lifecycle_service.py:138,196,268`, `test_session_store.py:237,258` создают первый бой. `session.py:89-108` перезаписывает/удаляет runtime history | Создать, выполнить exchange, создать тот же ID ещё раз: state/history неизменны, результат согласован. Затем parallel creators/partial create | Sequential regression возможен с stateful fake; CAS/concurrency — настоящий Redis |
| **A03-13 crit-bleed after parry** | Есть точный по имени тест `test_runtime_processors.py:5540-5571`, но третий RNG result выключает trigger. **Штатный pytest pass подтверждён; с успешным trigger/resistance тот же assertion падает** | Assert trigger attempted+passed/fired до проверки: parry=true, effects/APPLY_EFFECT отсутствуют, crit/parry tokens сохранены; добавить positive control | Нет; реальный pipeline полностью доступен in-memory. A06-02 |
| **A04-01 client-controlled Rift outcomes** | `runtime/test_zone_generation.py:452-550,837-852` принимает заданный payload/force_event как тестовый input. Player tests `services/test_player_service.py:334` проверяют server attributes без конкурирующего client override; node-combat reject не покрывает transition outcome. Production `player_service.py:74,96-103`, `actions/dispatcher.py:46-54,199-205` | Подать client attributes выше server, force_event=none, forged transition victory; assert отклонено/игнорируется, guard/travel не прогрессирует. Проверить public DTO→service, а не только pure runtime | Нет для trust regression: real routes/services с fake authoritative state; browser опционален |
| **A04-02 missing Combat = victory** | `rift/integrations/test_combat_result_runtime.py:130,185` проверяет явную победу/поражение. `combat/test_api_and_view.py:1455-1520` использует fake SystemIntegrator (`:425-427`), обходя настоящий `system_integrator.py:261` | Missing combat и archive при active Rift guard: outcome unknown, gate/event не cleared; совместить настоящие Combat/Rift adapters | In-memory достаточно; expiry/restart отдельно real Redis/Mongo |
| **A04-03 missing initial snapshot** | `rift/test_dependencies.py:37-82` проверяет wiring repository; `integrations/test_runtime_integration.py:409,544` — explicit flush/dirty. Entry `services/entry_service.py:54,68`, `integrations/runtime.py:65-69,157-167` не доказан через немедленный restore | Fresh entry без последующих actions → убрать Redis → восстановить: persisted snapshot/session/membership pointer существует, presence восстановлена | Fake stores достаточны для orchestration gap; настоящий Mongo/SQL/Redis нужен для durable claim |
| **A04-07 seed nondeterminism** | `test_hex_generator.py:38,66,96,413` — один процесс/разные seeds/shape; нет равенства same seed между hash seeds | Subprocess с PYTHONHASHSEED 1/2/3; одинаковые config+seed → одинаковые normalized nodes/edges/finish | Не нужна БД, нужны отдельные процессы; в этом аудите дефект повторно количественно не измерялся |
| **A04-08 disabled Knowledge cap** | `exploration/test_knowledge_service.py:10-45` cap тестируется отдельно; encounter integration tests `:114,137` не собирают весь dependency path. `encounter_service.py:46-50,285-287`, `encounter_integration.py:63-79` | Штатная сборка с fake Redis, повторные награды в одной локации сверх бюджета; total XP ограничен, recorder получает capped amount | Нет для wiring regression; durable concurrent cap — реальный Redis/SQL |
| **A04-11 GenerationAI retry mismatch** | `test_generation_ai_core.py:522-540` начинает с attempts=2 и проверяет один cooldown на следующей попытке. Fake claim `:98-107` не реализует SQL filter. `services.py:216-219`, `repositories.py:136-140` | Последовательность claims/errors до terminal состояния; каждый cooldown действительно повторно claimable или terminal; отсутствие вечного cooldown после max_attempts | Проверка policy возможна без БД; окончательная защита реального SQL predicate/skip_locked требует PostgreSQL |

Для A04-01 важно сохранить уже имеющийся положительный тест server attributes и отказ manual **node** combat. Проблема — недостающие adversarial inputs и **transition** path, а не полное отсутствие проверок безопасности Rift.

## 12. Testability архитектуры

Положительная база: constructor injection у многих services/adapters, настоящие Pydantic DTO, stateful in-memory stores, semantic integrations, pure math/evaluator/graph components. Combat simulator исполняет реальный executor. Сотни tests завершились без Docker и живых DB; это доказанная возможность, не только архитектурное обещание.

Ограничения:

- Широкий orchestrator может принять множество permissive doubles, не проверяя согласованность жизненного цикла. Finalizer объединяет разные side effects; одиночный mock call не обеспечивает testability restart/retry. Нужны явные наблюдаемые checkpoints и faulting stores, не глобальная перепись архитектуры.
- Character/Inventory cross-feature hydration имеет внутренние DTO/ORM знания (карта `audit/02_architecture_boundaries.md:145-151`); tests с hand-built tuples не подтверждают контракт реального repository. Публичный projection contract стоит проверять в месте стыка.
- Global catalog/settings initialization осложняет import isolation и конфигурационные тесты; сбор всех 303 модулей уже загружает много production modules. Удалённый script import прерывает всю suite до выбора поведения.
- Clock/RNG преимущественно подменяются monkeypatch; это допустимо, но sequence-based RNG без semantic preconditions хрупок. Seed не заменяет контроль Python hash order и чужого global RNG. Для существенных детерминированных компонентов полезна узкая clock/RNG dependency, не mock самого алгоритма.
- SQL repository doubles обходят существенную часть query behavior; Mongo bootstrap fake проверяет wiring, не физический индекс. Это ограничение выбранного test level, а не повод требовать mocks повсюду.
- Shared singleton `app` и вручную изменяемый `app.state` создают риск order coupling. Функциональные tests с fresh minimal FastAPI лучше изолируют routes, но при этом не покрывают production lifespan; нужны оба разных типа проверки.
- Импорт внешних codex-* и FastAPI Cabinet контрактов даёт полезный version tripwire, но текущая готовая venv не доказывает чистую установку. Testability без Docker не равна воспроизводимости CI.

Локальная цель улучшения — сильные public contract fixtures, несколько настоящих adapter tests, stateful fault injection и явные preconditions. Глобальный рефакторинг всех сервисов ради единого test framework не обоснован.

## 13. Подтверждённые недостатки

### A06-01 — Сломанная collection после удаления script

- **Severity:** High. **Статус:** подтверждено. **Уверенность:** высокая.
- **Файлы/строки:** `tests/backend/features/generation_ai/test_asset_backfill.py:6-10`; отсутствует `scripts/backfill_generated_assets_to_s3.py`; настройки collection `pyproject.toml:154-165`.
- **Нарушенный invariant:** весь обязательный test set должен импортироваться до исполнения gate.
- **Последствие:** pytest/full gate завершается exit 2, не даёт штатного полного результата; три test functions данного файла вообще не собираются.
- **Доказательство:** реальная collection: 2 787 collected, `ModuleNotFoundError: No module named 'scripts'`.
- **Минимальное направление:** согласовать тест с принятым новым владельцем/удалением backfill utility; не замалчивать ошибку постоянным `--ignore`.
- **Ожидаемая регрессия:** clean-environment `pytest --collect-only` возвращает 0; поведение backfill проверяется по действующему entrypoint, если оно остаётся поддерживаемым.

### A06-02 — Regression test parry не активирует проверяемый trigger

- **Severity:** High. **Статус:** подтверждено исполнением. **Уверенность:** высокая.
- **Файлы/строки:** `test_runtime_processors.py:5556-5571`; `resolver/orchestrator.py:47-59`; `support/trigger_activator.py:161-180`; `ability_service.py:1354-1369` (полные пути в §4).
- **Invariant:** negative assertion об отмене эффекта должен достигать состояния, где эффект иначе возник бы.
- **Последствие:** зелёный тест создаёт ложную уверенность в защите от A03-13.
- **Доказательство:** штатный node PASS; controlled RNG с successful trigger/resistance → AssertionError на `:5570`, пять зарегистрированных RNG calls.
- **Минимальное направление:** исправить setup, подтвердить trigger_attempt/fired preconditions, positive control; избегать неименованной очереди бросков, которую можно неверно сопоставить этапам.
- **Ожидаемая регрессия:** crit + fired bleed + parry не оставляет status/event; crit + hit оставляет; tokens проверяются отдельно. Production code здесь не исправлялся.

### A06-03 — Нет доказательной защиты реальных storage/broker contracts

- **Severity:** High. **Статус:** подтверждено для текущего набора. **Уверенность:** высокая по просмотренным fixtures/поиску, без утверждения о внешних закрытых suites.
- **Файлы/строки:** `tests/backend/conftest.py:10-128,146-169`; `tests/backend/features/items/test_instance_repository.py:16-30`; `tests/backend/features/scenario/test_scenario_repository.py:12-21,42-45`; `tests/backend/infrastructure/mongo/test_bootstrap.py:11-39`; `tests/backend/core/bus/test_producer.py:1-60`.
- **Invariant:** поведение, зависящее от SQL dialect, RedisJSON/BSON wire, server atomicity и broker delivery semantics, должно иметь хотя бы репрезентативную проверку реального adapter boundary. HTTP-согласование frontend/backend рассматривается отдельно в A06-07.
- **Последствие:** SQL predicate/constraint, RedisJSON response/partial write, Mongo index или Streams redelivery могут сломаться при зелёных unit tests.
- **Доказательство:** FakeSession/AsyncMock/fake pipeline не исполняют SQL/Redis/Mongo; real infrastructure fixture/config/CI service suite не найдены. FakeSession может вернуть ожидаемую строку даже при неверном WHERE.
- **Минимальное направление:** маленькие disposable PostgreSQL/Redis Stack/Mongo suites только для критичных операций, с отдельным stage и данными.
- **Ожидаемая регрессия:** DB upsert/read/rollback/ownership, two-worker claim, RedisJSON roundtrip/TTL/partial failure, Mongo snapshot/index, Streams duplicate/reclaim; assertions по итоговым данным, не только вызовам.

### A06-04 — Lifecycle tests не защищают retry/fault invariants наград и восстановления

- **Severity:** High. **Статус:** подтверждено охватом известных контрольных cases. **Уверенность:** высокая.
- **Файлы/строки:** `tests/backend/features/combat/test_victory_finalizer_task.py:175,242,314,344`; `test_experience_finalizer.py:229`; `test_lifecycle_service.py:138`; `tests/backend/features/rift/integrations/test_runtime_integration.py:409,544`; `tests/backend/features/generation_ai/test_generation_ai_core.py:98-107,522-540`.
- **Invariant:** второй вызов и частичный отказ должны быть частью тестового контракта многошаговой операции.
- **Последствие:** A03-01/02/04, A04-03/11 проходят мимо happy-path tests; isolated cap test также не доказывает включение cap.
- **Доказательство:** §11: проверяется единичное применение/ранний retry/explicit flush, не repeat+failure+restore. Это недостаток тестовой модели, не новые ID игровых дефектов.
- **Минимальное направление:** переиспользовать настоящие orchestrators и stateful faulting fakes для последовательностей; дополнить ровно нужные случаи real storage из A06-03.
- **Ожидаемая регрессия:** bounded replay одного operation ID, падение после каждой side effect, повтор после restart; assert reward conservation, discoverable unfinished state, eventual completion, initial snapshot availability.

### A06-05 — Чистый CI checkout не содержит обязательную path dependency

- **Severity:** High. **Статус:** подтверждено конфигурацией; hosted failure не запускался. **Уверенность:** высокая.
- **Файлы/строки:** `pyproject.toml:34-35`, `uv.lock:470-471`; `.github/workflows/ci.yml:24-35,48-59`; `build-images.yml:21-32`.
- **Invariant:** checkout + объявленные install steps должны разрешать все зависимости.
- **Последствие:** `uv sync` на чистом runner не имеет источника codex-ai и не достигает проверок; локальный готовый environment скрывает проблему.
- **Доказательство:** source `../../codex_tools/codex-ai`, отсутствующий в project checkout; workflows выполняют только обычный checkout перед sync, без sibling dependency checkout.
- **Минимальное направление:** доступный published/pinned source либо явное получение правильного sibling source в CI; выбор конкретного способа оставлен этапу стабилизации.
- **Ожидаемая регрессия:** install/collect/full gate на чистом Linux runner из одного описанного workflow, без заранее подготовленной venv и локальных абсолютных paths.

### A06-06 — Develop не имеет behavioral gate

- **Severity:** Medium. **Статус:** подтверждено workflow. **Уверенность:** высокая.
- **Файлы/строки:** `.github/workflows/ci.yml:3-9,19-41,43-66`.
- **Invariant:** изменения основной интеграционной ветки должны получать исполняемую проверку изменённого поведения до распространения.
- **Последствие:** push develop запускает только hooks/types; PR в develop не запускает этот CI; functional/collection regression обнаружится позднее на main.
- **Доказательство:** точные trigger branches и job if, отсутствие pytest в develop job.
- **Минимальное направление:** включить develop PR и достаточный test stage; дорогие проверки можно отдельно планировать по риску.
- **Ожидаемая регрессия:** matrix event/ref показывает pytest для develop PR/push; намеренно failing selected test блокирует соответствующий check. Required status settings GitHub надо проверить отдельно.

### A06-07 — Frontend/backend проверяются раздельно с независимыми fixtures

- **Severity:** Medium. **Статус:** подтверждено для исследованных HTTP границ. **Уверенность:** высокая.
- **Файлы/строки:** `tests/frontend/features/cabinet/test_game_settings_module.py:18-20,257-401`; `tests/backend/features/test_internal_routers.py:105-164`; `tests/frontend/features/cabinet/test_cabinet_integration.py:9-28`.
- **Invariant:** request/response на public boundary должен проверяться producer и consumer совместно хотя бы в критичных сценариях.
- **Последствие:** независимо подготовленные MockTransport replies и backend expectations не гарантируют DTO/route/auth/serialization совместимость реального вызова.
- **Доказательство:** frontend получает ручной HTTP response, backend тестируется отдельно; mounted Cabinet reduced app не связывает настоящий backend.
- **Минимальное направление:** ASGI consumer-contract tests с реальными routers/DTO и fake persistence, без браузера и Docker на каждую проверку.
- **Ожидаемая регрессия:** реальный settings update/reset либо game transition из frontend вызывает backend, парсит ответ и формирует корректный redirect/fragment; несовместимый field/path должен падать.

### A06-08 — Архитектурный gate проверяет только часть объявленных invariants

- **Severity:** Medium. **Статус:** подтверждено. **Уверенность:** высокая.
- **Файлы/строки:** `tests/backend/features/test_infrastructure_boundaries.py:9-77`, особенно `:63-74`; `.agents/skills/turnbasedmmorpg-project/references/project-rules.md:17-41`.
- **Invariant:** feature Redis ownership и запрет frontend→backend feature imports должны проверяться по действующему правилу, а не только по нескольким старым именам.
- **Последствие:** новый запрещённый prefix, иной syntax и любые Rift keys обходят scan; сохранённые location tests не доказывают общую границу.
- **Доказательство:** буквальный список шести prefixes и unconditional Rift skip; проверки существования отдельных symbols/отсутствия старых файлов.
- **Минимальное направление:** AST/import rules и scoped ownership scan, небольшие явные exemptions; оставить полезные regression checks перемещённых managers.
- **Ожидаемая регрессия:** synthetic forbidden import/новый Redis prefix/нарушение в Rift обнаруживаются; разрешённый infrastructure adapter проходит.

### A06-09 — Deploy workflow не связывает image_ref с успешным quality result

- **Severity:** Medium. **Статус:** подтверждено на уровне workflow; внешние организационные ограничения неизвестны. **Уверенность:** высокая по коду.
- **Файлы/строки:** `.github/workflows/deploy-production.yml:16-20,29-44,91-110`; `.github/workflows/build-images.yml:17-43`.
- **Invariant:** production promotion должен использовать проверенный artifact или проверяемую связь image→successful gate.
- **Последствие:** ручной deploy принимает image_ref, не проверяя его quality provenance; SSH reachability и compose health не подтверждают regression status выбранного artifact.
- **Доказательство:** deploy needs только preflight; preflight выполняет SSH echo. Release build имеет quality dependency, но deploy не валидирует принадлежность выбранного image к такому build.
- **Минимальное направление:** разрешать promotion проверенного immutable artifact/reference с привязкой к успешному build/gate; не дублировать всю suite на сервере.
- **Ожидаемая регрессия:** preflight с неизвестным/непрошедшим artifact отвергается до deploy; проверенный artifact допускается; отдельный минимальный post-deploy health/behavior smoke. Deployment в аудите не запускался.

### A06-10 — Coverage защищает общий объём statements, не patch/branches

- **Severity:** Observation. **Статус:** подтверждено; не нарушение текущей политики. **Уверенность:** высокая.
- **Файлы/строки:** `pyproject.toml:165-184`; `docs/ru/management/testing_strategy.md:17-28`; quality `references/testing.md:7-9`.
- **Invariant:** отчётность должна отличать исполняемый threshold от целей и отсутствующих измерений.
- **Последствие:** общий 74% может оставаться зелёным при непроверенной новой ветке; 100% patch нельзя заявлять как выполненную автоматическую гарантию.
- **Доказательство:** нет branch/diff gate; частичный coverage действительно дал exit 1; документ явно не требует фиксированного patch процента.
- **Минимальное направление:** сохранить threshold и содержательный review changed behavior; если нужна новая patch/branch политика, принять её явно и измерять в CI, не создавать dummy tests.
- **Ожидаемая проверка:** конфигурационный smoke демонстрирует failure ниже 74%; при будущем добавлении patch policy — известная непокрытая изменённая ветка обнаруживается. Актуальный общий coverage пока отсутствует.

### A06-11 — Stage «unit» не отделяет уровни тестирования

- **Severity:** Low. **Статус:** подтверждено. **Уверенность:** высокая.
- **Файлы/строки:** `pyproject.toml:158-164,200-205`; установленный `codex_core/dev/check_runner.py:343-353`; collection marker counts §3.
- **Invariant:** имя/selector stage должны ясно задавать его исполняемый набор и внешние зависимости.
- **Последствие:** CI «unit» запускает все tests, а `pytest -m unit` пропустит 1 258 собранных cases, многие из которых также изолированные; будущие DB tests попадут в общий stage без отдельной подготовки.
- **Доказательство:** marker пустой → `-m` не добавляется; integration marker зарегистрирован, но не используется; unit marker лишь на 1 529 из 2 787 cases.
- **Минимальное направление:** назвать текущий stage честно all/fast suite либо последовательно отделить external integration marker и окружение; не маркировать все файлы по имени каталога.
- **Ожидаемая регрессия:** collection stage matrix показывает непересекающиеся/осознанно пересекающиеся наборы; fast stage не требует DB, integration stage не оказывается пустым незаметно.

### A06-12 — Pip-audit hook проверяет своё окружение вместо зависимостей приложения

- **Severity:** Medium. **Статус:** подтверждено конфигурацией hook и его manifest. **Уверенность:** высокая; CVE service не вызывался.
- **Файлы/строки:** `.pre-commit-config.yaml:39-61`; `pyproject.toml:198`; `.github/workflows/ci.yml:34-41`. Прочитанные cached hook manifests `C:/Users/prime/.cache/pre-commit/repomay11ilp/.pre-commit-hooks.yaml:1-6` и `repomi75k2w7/.pre-commit-hooks.yaml:1-6`: `entry: pip-audit`, `language: python`, `pass_filenames: false`.
- **Invariant:** dependency audit должен проверять dependency set приложения, а не только инструмент проверки.
- **Последствие:** зелёный pre-commit/develop hook не подтверждает отсутствие известных уязвимостей project dependencies. Main/release runner имеет отдельный `uv run pip-audit`, поэтому находка не означает полного отсутствия аудита зависимостей в проекте.
- **Доказательство:** Python hook environment содержит hook/additional_dependencies; args задают `--local`, timeout и ignore-list, но не requirements input/путь проекта. `pass_filenames=false` не передаёт pyproject как input. Develop вызывает только hooks и mypy, не отдельную project-environment audit-команду.
- **Минимальное направление:** явно аудировать project environment либо экспортированный dependency set в нужных ветках; hook можно оставить для другой осознанной цели. Согласовать ignore policy и её scope.
- **Ожидаемая регрессия:** read-only diagnostic показывает, что аудит видит конкретные application packages и их зафиксированные версии; fixture dependency report с известной тестовой advisory проваливает gate, даже если такой пакет отсутствует в hook environment.

## 14. Непроверенные риски

- **Order dependence singleton app/state:** риск следует из fixture setup, но конкретный reverse/random-order failure не воспроизведён. Нужен ограниченный переставленный запуск подходящих API tests, не предположение о сломанном teardown.
- **Race/atomicity:** нет настоящего Redis/Postgres concurrency run; A06-03/04 подтверждают отсутствие защиты, но не измеряют вероятность каждого production race.
- **CI фактический status и required checks:** remote GitHub runs, branch protection, environments approvals, registry provenance не прочитаны. Workflow definition не равна подтверждённому успешному hosted execution.
- **Runner alternative source:** существование hardcoded codex-core path может подменить installed package; на этой машине импортирован installed runner. Не установлен текущий version divergence.
- **Security policy drift:** разные pip-audit ignore lists подтверждены, но конкретный advisory failure или состояние актуальной vulnerability DB не проверены; это не security audit.
- **Performance/flakiness:** 55-секундный широкий run не завершён, последний hex test не объявляется зависшим. Вариативность длительности, seed distribution и CPU/мemory budget отдельно не измерены.
- **Test doubles aliasing:** FakeRedis не копирует dict, значит мутация может «сохраниться» без set. Контракт double подтверждён чтением, но отдельный ложный pass конкретного persistence test этим способом не воспроизводился.
- **Production lifespan/shutdown:** mocked bootstrap и noop rollup не доказывают корректное закрытие реальных consumers/pools. Завершённые unit/TestClient runs не исключают production pending tasks.

## 15. Сильные решения

1. **Настоящая доменная реализация в тестах.** Combat pipeline/resolver и simulation executor исполняются; evaluator, navigation, DTO и catalog tests не сводятся к mocked algorithm.
2. **Проверки состояния.** Inventory projection/TTL, Character restore fields, Rift gates/graph, loot integer TTL лучше защищают поведение, чем одни call counts.
3. **Негативные paths уже есть.** Auth signature/expiry/password, CSRF mismatch, expired-session cookies, forbidden inventory state, unavailable claim queue. Пробел trust boundary Rift не означает отсутствие security-focused тестов вообще.
4. **Полезные contract tripwires.** Shared inventory DTO serialization, ARQ queues/job registration, FastAPI Cabinet consumer rendering, feature manager ownership locations. Они ограниченны, но их стоит сохранить.
5. **Локальная исполнимость без Docker доказана.** 362-case выборка и 3 focused async tests прошли вне sandbox; для многих регрессий не нужна тяжёлая инфраструктура.
6. **Global threshold работает.** Частичная выборка завершила tests и получила fail по 74%; это реальное enforcement, не только текст документа.
7. **Fixture validation работает.** Items/skills/scenario validator вернул exit 0. Полезный недорогой gate для игровых данных.
8. **Workflow dependencies предусмотрены.** Main full gate, `docker-build needs: quality`, release image `needs: quality`; реальные clean-install blockers надо устранить, сохранив эту последовательность.
9. **Текущая стратегия не стимулирует бессмысленный coverage.** Changed behavior, риск и focused checks сформулированы явно; автоматическое требование 100% patch нельзя вводить задним числом.

Дополнительные затраты пока не оправданы: browser E2E для каждого ability/layout, mutation всего приложения, DB fixtures для чистой арифметики, новые тесты на тривиальный forwarding без контрактного риска, snapshot каждого CSS-класса ради coverage. Приоритет — A06-01/02, воспроизводимый CI и несколько критичных lifecycle/storage boundaries.

## 16. Реестр находок

Все направления исправления ниже — предложения для общей стабилизации после серии аудитов, **не применённые изменения**. Подробные evidence, assertions и confidence — §13.

| ID | Severity | Статус | Недостаток / зона |
| --- | --- | --- | --- |
| A06-01 | High | Подтверждено запуском | Stale script import останавливает collection |
| A06-02 | High | Подтверждено запуском и controlled probe | Parry regression выключает trigger и проходит ложно |
| A06-03 | High | Подтверждено текущим набором | Нет real storage/broker contract suite |
| A06-04 | High | Подтверждено сопоставлением | Недостаточная stateful retry/fault/recovery защита |
| A06-05 | High | Подтверждено конфигурацией | Clean CI не получает path dependency codex-ai |
| A06-06 | Medium | Подтверждено workflow | Develop без pytest gate, PR trigger только main |
| A06-07 | Medium | Подтверждено образцами/поиском | Нет совместной frontend→backend contract проверки |
| A06-08 | Medium | Подтверждено кодом | Неполный architecture boundary gate |
| A06-09 | Medium | Подтверждено workflow | Deploy не проверяет quality provenance image_ref |
| A06-10 | Observation | Подтверждено | Общий line threshold без patch/branch enforcement; соответствует текущей политике |
| A06-11 | Low | Подтверждено runner/collection | Stage unit и markers не выражают реальные уровни |
| A06-12 | Medium | Подтверждено hook config/manifest | Pip-audit hook не аудирует application dependency set |

## 17. Ограничения и уровень уверенности

Высокая уверенность: inventory/collection counts, конкретный import failure, vacuous parry regression, stack и сравнение sandbox/non-sandbox, выполненная 362-test выборка, текущие workflow conditions и coverage settings. Средняя для обобщения отсутствия external integration across the project: проверены весь test tree, dependency/workflow configuration и репрезентативные implementations, но отдельный внешний закрытый harness не искался.

Не выполнены: полный успешный штатный pytest, полный quality runner/pre-commit/mypy/security/MkDocs, live DB/Redis/Mongo/Streams/ARQ integration, browser E2E, deployed smoke, hosted CI installation, full mutation/performance/security audits. Никакой из них не назван пройденным. Последний широкий pytest остановлен намеренным лимитом, не системным verdict.

Авторизованное изменение — этот Markdown-отчёт. Production code, tests, config, workflows, skills не правились; dependencies не устанавливались; deployment и обращения к production не выполнялись. Диагностические pytest/coverage артефакты созданы отдельно в Temp. Исходные пользовательские изменения оставлены на месте. Skills не требуют обновления: рабочие контракты не менялись.

### Testing Health Summary

| Измерение | Оценка | Основание |
| --- | --- | --- |
| **Unit test quality** | Хорошая база, неоднородная надёжность | Реальные алгоритмы/state assertions; один доказанный vacuous regression и слабые repository assertions |
| **Integration confidence** | Низкая для внешних систем | Stateful doubles помогают orchestration, но нет real DB/Redis/Mongo/transport suite |
| **E2E readiness** | Начальная, осознанно отложенная | Есть TestClient/rendering, нет browser journey; достаточно 3–4 приоритетных будущих сценариев |
| **Coverage enforcement** | Частичное, действующее | Global statements ≥74% работает; цель ≥90%, patch/branch enforcement отсутствует, общий свежий coverage неизвестен |
| **CI reliability** | Ограничена подтверждёнными блокерами | Stale collection import, path dependency, develop без pytest; main/release gates правильно связаны по needs |
| **Async test stability** | Работает в проверенной выборке вне sandbox | Setup hang локализован в Windows stdlib socketpair внутри sandbox; application deadlock не установлен |
| **Contract protection** | Точечная | DTO/ARQ/Cabinet contracts есть, producer-consumer/storage/ownership coverage неполное |
| **Regression detection capability** | Сильнее в локальной логике, слабее в lifecycle | 362 assertions-based cases прошли; duplicate/fault/recovery и доверие к payload остаются основными пробелами |
