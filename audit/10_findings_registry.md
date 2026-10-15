# 10 — Сводный реестр находок аудитов 02–09

Дата консолидации: 09.10.2026. Объект: локальное рабочее дерево TurnBasedMMORPG. База, указанная в аудитах: 6ccc92561c633f618eb7ee082c36caa44a1400f7; дерево уже содержит staged/unstaged/untracked изменения. Совпадение HEAD не подтверждает тождество снимков рабочего дерева. Это master consolidation существующих свидетельств, **не новый security audit, не план реализации и не разрешение исправлять приложение**.

## Правила чтения

Сохранены все 120 исходных ID. Заголовки A-ID взяты из развёрнутых карточек; для записей только в таблицах сохранён текст исходной строки. Для O02 сохранена исходная формулировка целиком. Severity — **исходная**, без автоматического повышения по стадии или по более позднему доказательству. У A04-21 исходная severity не присвоена.

Доказательность, стадия и срочность независимы от severity. «Исторически воспроизведено» означает результат, записанный автором исходного аудита; **при консолидации тесты/пробы не повторялись**. «Подтверждён failure window» означает установленный в отчёте порядок и границу отказа; production-инцидент/частота этим не доказаны. «Гипотеза» сохраняет непроверенность эффекта при статически установленных предпосылках. Неактуальные находки без нового доказательства не назначены.

Стадия классифицирует поверхность по уточнению владельца: общая система — Pre-alpha; Old Rift — Legacy (поддержка runtime неизвестна); Hex — Experimental/Dev-only; Studio/tools — Dev-only. Alpha сохраняется только как public label или историческое описание исходного аудита, а не оценка текущей готовности. Shared infrastructure обслуживает Pre-alpha/Legacy/Experimental/Dev-only consumers. «Production по конфигурации» — intended Compose/workflow, а не подтверждённое состояние сервера. История утверждения стадии Rift неполна.

Срочность — ось классификации, **не очередь работ**. Она условна при неизвестной публикации/стадии: архитектура и performance — «При стабилизации домена»; auth/trust границы при подтверждённой публикации — «До следующего публичного релиза»; experimental — «До beta при включении поверхности»; legacy — «Не исправлять без архитектурного решения» о поддержке/выводе; неутверждённый продукт — «Не исправлять без архитектурного решения». Срочность production-условий требует подтверждения фактической экспозиции; live reads здесь не выполнялись.

Canonical объединяет лишь полный дубль: одна причина, одно исправление, совместимая проверка. Каждая исходная карточка остаётся отдельной. Связи различают полный дубль, частичное пересечение, общую причину, зависимость проверки и самостоятельный контракт. Отсутствие перечисленной связи не доказывает независимость всех возможных причин.

## Полнота и контроль ID

| Аудит | Исходные ID | High | Medium | Low | Observation | Без severity | Всего |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 02 | A02-01–10; O02-01–05 | 3 | 6 | 1 | 5 | 0 | 15 |
| 03 | A03-01–13, включая A03-13 перед разделом рисков | 5 | 8 | 0 | 0 | 0 | 13 |
| 04 | A04-01–21, включая 7 строк §8 | 8 | 10 | 2 | 0 | 1 | 21 |
| 05 | A05-01–15 | 5 | 10 | 0 | 0 | 0 | 15 |
| 06 | A06-01–12 | 5 | 5 | 1 | 1 | 0 | 12 |
| 07 | A07-01–18, включая 5 строк §13 | 8 | 9 | 0 | 1 | 0 | 18 |
| 08 | A08-01–15, включая Low и Observation | 2 | 11 | 1 | 1 | 0 | 15 |
| 09 | A09-01–11 | 4 | 7 | 0 | 0 | 0 | 11 |
| **Итого** | **120 уникальных исходных ID** | **40** | **66** | **5** | **8** | **1** | **120** |

Повторное упоминание старого ID в следующем аудите не создаёт находку. Числа confirmed в executive summaries меньше полного реестра из-за рисков/observations. Inventory 01 вне охвата 02–09; 09_performance_probes.py — приложение к 09, не отдельный реестр.

## Полные дубли

| Canonical | Исходные ID | Основание полного дубля | Раздельные оценки |
| --- | --- | --- | --- |
| A04-01 | A04-01; A07-05 | Один player DTO→dispatcher доверяет force_event/outcome/attributes; общая серверная граница и отрицательные inputs | Gameplay/security view, исходная стадия |
| A04-12 | A04-12; A05-07 | Один initial Mongo error подавляется; pending/hydration без durable input; общий acceptance/recovery contract | High в 04 / Medium в 05, World/news examples |
| A04-17 | A04-17; A05-09 | Один Rift capture→clear без revision; общий compare-clear contract и mutation barrier | Риск в 04 / подтверждённое failure window в 05 |
| A07-14 | A07-14; A08-01 | Одна prod settings boundary принимает known-default signing/internal keys | Условный риск в 07 / settings probe в 08; real keys неизвестны |

Границы объединения: A04-02 (false victory при missing-result recovery) остаётся самостоятельным canonical; упоминание этой ветки в security view A07-05 не поглощает её DTO-группой. A04-17/A05-09 усиливают evidence одного окна, но real-Redis воспроизведение отсутствует. A07-14/A08-01 подтверждают дефект default validation текущего источника; actual production keys/эксплуатация неизвестны. Дополнительные cookies/dev-default условия A08-01 не отменяют самостоятельных session/dev-exposure находок.

Только эти четыре объединения дают **116 canonical записей**, четыре группы по два ID. Это не число подтверждённых текущих дефектов. Более позднее evidence добавляется к группе, но не переписывает историческую оценку участника.

**Частичные пересечения не объединены:** A03-11/A04-15 (A03 также partial completion и synthetic outcome); A04-18/A05-08 (A04 также orphan assets/Mongo); A06-05/A08-10 (A08 также Docker source policy); A07-04/A08-03 (A07 также analytics/backfill; A08 также edge/scan limits); A07-15/A08-04 (A08 также unbounded instances); A06-09/A08-11 (A08 также governance/ref/concurrency).

## Проверки при консолидации

Полностью прочитаны все разделы восьми исходных Markdown-отчётов, включая риски, observations, выполненные/незавершённые пробы и ограничения. Сверены уникальные ID, строки начала карточек и исходные severity; повторные упоминания старых IDs не посчитаны повторно.

Выборочно перечитаны текущие исходники: Combat/Rift routes и зависимости; Rift dispatcher/отсутствующий combat recovery; GenerationAI initial payload error/hydration; Rift dirty flush/mark/clear; Exploration Knowledge wiring; Combat nontransactional create/commit/archive reader; chat membership, archive schedule/batch, Mongo full-document return; metrics label-before-routing; default dev flag/Hex process-global state. Это подтверждает ограниченные текущие статические предпосылки, **не end-to-end эффект**.

Для нормализованных code anchors карточек автоматически проверены существование файла и попадание номера в текущий диапазон. Это навигационная проверка; семантическое совпадение каждой строки не заявляется. Первая ссылка — исходный evidence; code anchors — основные нормализованные ссылки из карточки; полный набор остаётся в исходном аудите. Неоднозначные сокращения не превращались в придуманный путь.

Сейчас не запускались pytest, performance probes, scanners, Compose, миграции, services, dependency installs или внешние запросы. Secrets, production, GitHub settings, registry/image bytes и реальные хранилища не читались.

## Исторические проверки

| Аудит | Результат, записанный в исходном отчёте | Ограничение |
| --- | --- | --- |
| 02 | 41 выбранный тест passed, 2.82s | Doubles/in-memory; не real storage |
| 03 | 3 tests passed; локальный post-phase bleed probe | Незавершённые пересекающиеся async runs не суммировать; полный pipeline не прошёл |
| 04 | 96 tests passed; hash-seed/recovery/retry-condition probes | Без настоящих PG/Mongo/Redis/AI; recovery с doubles |
| 05 | 2 sync tests passed; ORM introspection | Async setup остановлен; no real migrations/fault injection |
| 06 | 362 cases passed, **exit 1 по частичному coverage 38.39% при пороге 74%**; отдельно 3 passed; collection exit 2 | Не full-suite pass; 1707 PASSED незавершённого run не verdict; sandbox loop hang локализован вне приложения |
| 07 | Статический route/contract/AST анализ | Pytest не запускался; DTO/parser probe не exploit proof |
| 08 | Compose model exit 0; settings/logging/metrics inert probes | Не runtime/deploy validation; synthetic canary/local library |
| 09 | Автономные AST/in-memory probes exit 0; счётчики/synthetic timings | Не RTT/p95/CCU/real Redis/SQL/browser benchmark |

Будущие проверки карточек **не выполнены сейчас**. Успешные исторические команды не сертифицируют весь домен.

## Аудит 02

### A02-01 — Expedition и Loot worker нарушают ownership persistent state

- **Источник / аудит:** [audit/02_architecture_boundaries.md:280](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:280); аудит 02. **Code anchors:** [src/backend/features/expedition/service.py:12](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/expedition/service.py:12), [src/backend/features/loot/workers/tasks/loot_claim_task.py:189](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/loot/workers/tasks/loot_claim_task.py:189)
- **Исходная severity:** High. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Expedition; Loot; Items; Inventory; Character. Persistence/rules принадлежат feature owner при сохранении общего UoW.
- **Trigger / impact:** Transfer/cashout/death вне owner API → Coupling accounting и чужих ORM.
- **Необходимая проверка:** Conservation, repeat death/safe-sync, mid-transfer rollback, real SQL constraints. **Ограничения:** Авария и corruption не воспроизведены; не дробить transaction ради транспорта.
- **Canonical:** A02-01. **Связи:** Причина архитектурного coupling к A05-01/02/04; самостоятельные correctness-контракты.

### A02-02 — Combat/Rift зависят от внутренних constructor graphs

- **Источник / аудит:** [audit/02_architecture_boundaries.md:291](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:291); аудит 02. **Code anchors:** [src/backend/features/rift/dependencies.py:137](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/dependencies.py:137), [src/backend/features/rift/services/encounter_service.py:110](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/services/encounter_service.py:110), [src/backend/features/combat/workers/tasks/victory_finalizer_task.py:191](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/workers/tasks/victory_finalizer_task.py:191)
- **Исходная severity:** High. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha / Legacy (Rift; поддержка runtime неизвестна). **Срочность:** Не исправлять без архитектурного решения о поддержке/выводе Legacy; при текущей публикации сначала проверить экспозицию.
- **Домены / контракт:** Combat; Rift; GameSession; Monsters; Loot. Соседний constructor graph не внешний API; completion policy имеет владельца.
- **Trigger / impact:** Start/finish/return Combat↔Rift → Замена internals требует чужих правок; несколько completion callers.
- **Необходимая проверка:** Duplicate/parallel completion, defeat/draw, restart до Rift apply. **Ограничения:** Coupling подтверждён; race не доказана.
- **Canonical:** A02-02. **Связи:** Причина/контекст A03-11,A04-02/15; не полный дубль.

### A02-03 — RedisJSON schema активного персонажа протекает наружу

- **Источник / аудит:** [audit/02_architecture_boundaries.md:301](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:301); аудит 02. **Code anchors:** [src/backend/features/expedition/service.py:194](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/expedition/service.py:194), [src/backend/features/combat/workers/tasks/victory_finalizer_task.py:294](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/workers/tasks/victory_finalizer_task.py:294), [src/backend/features/game_session/integrations/session_integrator.py:306](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/game_session/integrations/session_integrator.py:306)
- **Исходная severity:** High. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Character; Combat; Expedition; GameSession. Storage paths/TTL/dirty принадлежат manager через semantic operation.
- **Trigger / impact:** Patch активного персонажа caller-owned JSON paths → Междоменный schema contract и раздельные transition/dirty.
- **Необходимая проверка:** State transitions, dirty targets, patch→mark fault, concurrent refresh/respawn. **Ограничения:** Raw-path факт не доказывает потерю конкурентного state.
- **Canonical:** A02-03. **Связи:** Причина широкой поверхности A03-10; не общий canonical.

### A02-04 — Character зависит от внутренней формы Inventory hydration

- **Источник / аудит:** [audit/02_architecture_boundaries.md:311](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:311); аудит 02. **Code anchors:** [src/backend/features/character/integrations/character_state_integrator.py:26](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/character/integrations/character_state_integrator.py:26), [src/backend/features/inventory/dependencies.py:9](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/inventory/dependencies.py:9)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Character; Inventory. Projection и ownership queries — owner-owned contracts.
- **Trigger / impact:** Hydration через чужие tuples/private builders → Рефакторинг Inventory/Character требует соседних правок.
- **Необходимая проверка:** Equipped/backpack/expedition hydrate, empty, ownership denial, SQL projection. **Ограничения:** Нет доказанного recursive вызова.
- **Canonical:** A02-04. **Связи:** Зависимость contract tests A06-03/07; самостоятельная граница.

### A02-05 — Loot orchestration частично находится в GameSession

- **Источник / аудит:** [audit/02_architecture_boundaries.md:321](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:321); аудит 02. **Code anchors:** [src/backend/features/game_session/integrations/session_integrator.py:263](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/game_session/integrations/session_integrator.py:263), [src/backend/features/system/workers/arq.py:25](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/system/workers/arq.py:25)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** GameSession; Loot; System. Loot owns claim/schedule и payload; Session owns navigation.
- **Trigger / impact:** Claim_all+ручная сборка ARQ payload в GameSession → Retry/schedule policy распределена.
- **Необходимая проверка:** Empty/repeated claim, queue absent, reservation→enqueue fault, state outcome. **Ограничения:** ARQ integration сейчас не выполнен.
- **Canonical:** A02-05. **Связи:** Контекст A03-05,A05-01; разные причины/проверки.

### A02-06 — Gameplay policy смешана со storage/core

- **Источник / аудит:** [audit/02_architecture_boundaries.md:330](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:330); аудит 02. **Code anchors:** [src/backend/infrastructure/actor_state/managers/session.py:419](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/actor_state/managers/session.py:419), [src/backend/core/calculators/data/attribute_rule_profiles.py:24](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/core/calculators/data/attribute_rule_profiles.py:24), [src/backend/features/character/integrations/character_state_integrator.py:261](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/character/integrations/character_state_integrator.py:261)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha). **Срочность:** При стабилизации домена.
- **Домены / контракт:** Character; Inventory; Combat; Monsters; actor_state. Infrastructure сохраняет; feature owns gameplay policy.
- **Trigger / impact:** Storage manager regen/refresh; core selects player/monster rules → Изменение persistence требует gameplay defaults.
- **Необходимая проверка:** Fixed-clock regen, no double regen, max-vitals/equipment refresh, Redis atomicity. **Ограничения:** Общий calculator существует; дублируются entrypoints, не обязательно формула.
- **Canonical:** A02-06. **Связи:** Причина/контекст A03-10; независим от storage-path A02-03.

### A02-07 — Transport adapters содержат use-case wiring и обратную утечку транспорта

- **Источник / аудит:** [audit/02_architecture_boundaries.md:339](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:339); аудит 02. **Code anchors:** [src/backend/features/combat/events/__init__.py:37](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/events/__init__.py:37), [src/backend/features/character/events/__init__.py:73](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/character/events/__init__.py:73), [src/backend/features/inventory/services/reward_service.py:122](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/inventory/services/reward_service.py:122)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha). **Срочность:** При стабилизации домена.
- **Домены / контракт:** Combat; Character; Inventory; Items; Streams. Thin transport handler и semantic outbound client.
- **Trigger / impact:** Handler wiring/error/ack; service request+reply parsing → Транспорт влияет на business service; policy повторяется.
- **Необходимая проверка:** Ack/error/correlation/timeout, failed reply, redelivery. **Ограничения:** Доставка настоящих Streams не проверена.
- **Canonical:** A02-07. **Связи:** Зависимость A05-05 transport проверки; не delivery defect сам по себе.

### A02-08 — Inventory runtime schema в cross-side shared

- **Источник / аудит:** [audit/02_architecture_boundaries.md:348](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:348); аудит 02. **Code anchors:** [src/shared/schemas/inventory.py:86](D:/Workspace/personal/pets/TurnBasedMMORPG/src/shared/schemas/inventory.py:86), [src/backend/infrastructure/inventory/managers/session.py:6](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/inventory/managers/session.py:6), [src/backend/features/inventory/services/projection.py:22](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/inventory/services/projection.py:22)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha). **Срочность:** При стабилизации домена.
- **Домены / контракт:** Inventory; Character; shared. Shared содержит cross-side API, не backend runtime storage shape.
- **Trigger / impact:** InventoryRuntimeSessionDTO с dirty/version в shared → Runtime refactor становится общим schema contract.
- **Необходимая проверка:** Redis roundtrip, frontend/API response contract, consumer inventory. **Ограничения:** Frontend type consumer не найден; внешние consumer не исключены.
- **Canonical:** A02-08. **Связи:** Независим от runtime lost-update A05-03.

### A02-09 — Simulation module имеет несколько независимых причин изменения

- **Источник / аудит:** [audit/02_architecture_boundaries.md:357](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:357); аудит 02. **Code anchors:** [src/backend/features/combat/services/ai_simulation_service.py:54](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/services/ai_simulation_service.py:54), [src/backend/features/combat/workers/tasks/ai_turn_task.py:10](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/workers/tasks/ai_turn_task.py:10)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha / Experimental. **Срочность:** До beta при включении поверхности.
- **Домены / контракт:** Combat; live AI; admin simulation. Независимые run/training/report/policy ответственности имеют явные contracts.
- **Trigger / impact:** Live worker импортирует private training helper → Admin/training changes расширяют live import surface.
- **Необходимая проверка:** Simulation/admin/worker/policy mapping contracts. **Ограничения:** Размер файла сам по себе не дефект; migration не предложена здесь.
- **Canonical:** A02-09. **Связи:** Контекст A03-08; failure lifecycle и cohesion раздельны.

### A02-10 — Architecture guidance содержит устаревшие anchors

- **Источник / аудит:** [audit/02_architecture_boundaries.md:366](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:366); аудит 02. **Code anchors:** [.agents/skills/turnbasedmmorpg-rift/references/implementation-boundaries.md:1](D:/Workspace/personal/pets/TurnBasedMMORPG/.agents/skills/turnbasedmmorpg-rift/references/implementation-boundaries.md:1), [src/backend/infrastructure/rift/models.py:12](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/rift/models.py:12), [src/backend/features/rift/api/router.py:31](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/api/router.py:31)
- **Исходная severity:** Low. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha / Legacy (Rift; поддержка runtime неизвестна). **Срочность:** Не исправлять без архитектурного решения о поддержке/выводе Legacy; при текущей публикации сначала проверить экспозицию.
- **Домены / контракт:** Project skills; Rift; Combat. Guidance anchors/stage отражают актуальные owner decisions.
- **Trigger / impact:** Агент читает old harness/resolver.py reference → Ошибочный запрет/трактовка текущей реализации.
- **Необходимая проверка:** Link check, current-stage/owner-decision review. **Ограничения:** История approvals неполна; code existence не approval.
- **Canonical:** A02-10. **Связи:** Частичное knowledge пересечение O02-02; самостоятельная maintenance запись.

### O02-01 — GenerationAI registry registration — допустимая extension wiring с централизованным editing point (§5); перемещение composition необязательно сейчас.

- **Источник / аудит:** [audit/02_architecture_boundaries.md:377](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:377); аудит 02. **Code anchors:** [src/backend/features/generation_ai/bootstrap.py:23](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/bootstrap.py:23)
- **Исходная severity:** Observation. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha). **Срочность:** Отложить до утверждения применимого контракта/использования поверхности.
- **Домены / контракт:** GenerationAI; World; Items; Monsters. Допустимое extension registration имеет явную composition ownership.
- **Trigger / impact:** Новый task handler меняет central bootstrap → Централизованная editing point; не авария архитектуры.
- **Необходимая проверка:** Registry owner/facade и task registration review. **Ограничения:** Observation: перенос composition необязателен.
- **Canonical:** O02-01. **Связи:** Независим от payload/scheduling A04-12/18.

### O02-02 — shared security/logging/metrics — полезные cross-cutting modules при более узком буквальном skill; решить policy, не удалять автоматически.

- **Источник / аудит:** [audit/02_architecture_boundaries.md:378](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:378); аудит 02. **Code anchors:** [src/shared/security/passwords.py:15](D:/Workspace/personal/pets/TurnBasedMMORPG/src/shared/security/passwords.py:15)
- **Исходная severity:** Observation. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha). **Срочность:** Отложить до утверждения применимого контракта/использования поверхности.
- **Домены / контракт:** shared; security; logging; metrics; project policy. Cross-cutting utilities требуют явной допустимости в shared.
- **Trigger / impact:** Буквальное only-models правило шире реального usage → Неоднозначность guidance; auto-delete опасен.
- **Необходимая проверка:** Policy review потребителей security/logging/metrics. **Ограничения:** Не доказан runtime defect; нужен owner contract.
- **Canonical:** O02-02. **Связи:** Частичное knowledge пересечение A02-10; не telemetry defect A08-05/07.

### O02-03 — readiness native resolver ограничена ambient RNG/catalog/tunables; это препятствие планируемой extraction, не требование сейчас внедрять иной язык.

- **Источник / аудит:** [audit/02_architecture_boundaries.md:379](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:379); аудит 02. **Code anchors:** [src/backend/features/combat/runtime/engine/math_core.py:30](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/engine/math_core.py:30)
- **Исходная severity:** Observation. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Experimental. **Срочность:** Отложить до утверждения применимого контракта/использования поверхности.
- **Домены / контракт:** Combat resolver; native extraction. Portable resolver input включает RNG/rules/tunables.
- **Trigger / impact:** Попытка native/process extraction с ambient state → Ограниченная readiness/parity.
- **Необходимая проверка:** Explicit snapshot corpus, RNG/rules/tunables parity. **Ограничения:** Extraction не текущий обязательный продуктовый scope.
- **Canonical:** O02-03. **Связи:** Контекст A02-09,A09-05; не performance bottleneck.

### O02-04 — конкурентное Rift completion и patch/dirty partial failures требуют integration proof. Нельзя считать corruption подтверждённым.

- **Источник / аудит:** [audit/02_architecture_boundaries.md:380](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:380); аудит 02. **Code anchors:** [src/backend/features/rift/integrations/runtime.py:410](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/integrations/runtime.py:410), [src/backend/infrastructure/actor_state/managers/session.py:119](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/actor_state/managers/session.py:119)
- **Исходная severity:** Observation. **Доказательность:** Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Pre-alpha / Legacy (Rift; поддержка runtime неизвестна). **Срочность:** Не исправлять без архитектурного решения о поддержке/выводе Legacy; при текущей публикации сначала проверить экспозицию.
- **Домены / контракт:** Combat; Rift; Character dirty state. Completion/patch/dirty согласованы при fault/concurrency.
- **Trigger / impact:** Параллельные completion или отказ между patch/mark → Предполагаемые partial/lost state.
- **Необходимая проверка:** Real RedisJSON barriers, completion failure boundaries. **Ограничения:** Нет integration proof; broad observation.
- **Canonical:** O02-04. **Связи:** Частичные A03-10/11,A04-15/17; широкий scope не объединён.

### O02-05 — `src/backend/features/loot/workers/arq.py:27` и `system/workers/arq.py:53` используют SYSTEM queue с разными registries; текущий `deploy/compose.game.yml:186` запускает SystemArqSettings. Не доказана одновременная работа несовместимых consumers; это latent config risk при выборе другого entrypoint.

- **Источник / аудит:** [audit/02_architecture_boundaries.md:381](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:381); аудит 02. **Code anchors:** [src/backend/features/loot/workers/arq.py:27](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/loot/workers/arq.py:27), [src/backend/features/system/workers/arq.py:53](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/system/workers/arq.py:53), [deploy/compose.game.yml:186](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/compose.game.yml:186)
- **Исходная severity:** Observation. **Доказательность:** Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Shared infrastructure (Pre-alpha). **Срочность:** При стабилизации домена.
- **Домены / контракт:** Loot; System; ARQ; deployment. Consumer registry соответствует выбранной queue/entrypoint.
- **Trigger / impact:** Альтернативный Loot worker с SYSTEM queue → Latent mismatch registry при неверном entrypoint.
- **Необходимая проверка:** Queue→function→deployed worker matrix. **Ограничения:** Compose сейчас выбирает SystemArqSettings; одновременность не доказана.
- **Canonical:** O02-05. **Связи:** Самостоятельный latent configuration contract.

## Аудит 03

### A03-01 — Повтор finalizer повторно начисляет XP

- **Источник / аудит:** [audit/03_combat_runtime.md:294](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:294); аудит 03. **Code anchors:** [src/backend/features/combat/workers/tasks/collector_task.py:76](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/workers/tasks/collector_task.py:76), [src/backend/features/combat/workers/tasks/victory_finalizer_task.py:69](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/workers/tasks/victory_finalizer_task.py:69), [src/backend/features/combat/runtime/services/experience_finalizer.py:69](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/services/experience_finalizer.py:69)
- **Исходная severity:** High. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Combat; Character; Expedition. Один combat/character progression effect один раз.
- **Trigger / impact:** Повтор finalizer с положительным xp_buffer до TTL → Повторное начисление XP.
- **Необходимая проверка:** Sequential/concurrent duplicate, crash после XP, cumulative delta=1. **Ограничения:** Additive path статически установлен; runtime repro не запускался.
- **Canonical:** A03-01. **Связи:** Причина/контекст A02-02/03; тестовая зависимость A06-04.

### A03-02 — Ошибка финализации оставляет закрытый бой без завершённых последствий

- **Источник / аудит:** [audit/03_combat_runtime.md:302](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:302); аудит 03. **Code anchors:** [src/backend/features/combat/workers/tasks/victory_finalizer_task.py:71](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/workers/tasks/victory_finalizer_task.py:71), [src/backend/features/combat/workers/tasks/collector_task.py:46](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/workers/tasks/collector_task.py:46)
- **Исходная severity:** High. **Доказательность:** Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Combat; Character; Archive; ARQ. Closed combat имеет результат и восстановимые последствия.
- **Trigger / impact:** Failure после active=0 до cache/side effects/enqueue → Inactive бой без post_combat/archive; swallowed exception.
- **Необходимая проверка:** Fault каждого шага, restart, eventual result без double XP. **Ограничения:** Infrastructure injection отсутствует.
- **Canonical:** A03-02. **Связи:** Зависимость от idempotency A03-01; не одно исправление.

### A03-03 — Commit exchange не атомарен

- **Источник / аудит:** [audit/03_combat_runtime.md:309](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:309); аудит 03. **Code anchors:** [src/backend/features/combat/workers/tasks/executor_task.py:120](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/workers/tasks/executor_task.py:120), [src/backend/features/combat/integrations/session_integration.py:401](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/integrations/session_integration.py:401), [src/backend/infrastructure/combat/managers/session.py:608](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/combat/managers/session.py:608)
- **Исходная severity:** High. **Доказательность:** Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Combat; RedisJSON. Actor/queue/step/logs exchange согласованы.
- **Trigger / impact:** Частичная ошибка nontransactional commit → Новые actors со старой queue/meta либо обратный partial state.
- **Необходимая проверка:** Error k-й команды, missing actor, retry batch, consistency/recovery. **Ограничения:** Python kill после отправки pipeline не доказывает Redis partial failure.
- **Canonical:** A03-03. **Связи:** Зависимость A03-09 fencing; самостоятельная atomicity граница.

### A03-04 — Повтор create с тем же combat_id сбрасывает существующий бой

- **Источник / аудит:** [audit/03_combat_runtime.md:316](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:316); аудит 03. **Code anchors:** [src/backend/infrastructure/combat/managers/session.py:89](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/combat/managers/session.py:89)
- **Исходная severity:** High. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Combat; Exploration; RedisJSON. Повтор create ID не уничтожает progress.
- **Trigger / impact:** Повторный create после ready/exchange → Reset actors/targets/moves/history.
- **Необходимая проверка:** Repeat до/после ready/exchange, concurrent creators, mid-create fault. **Ограничения:** Real Redis не запускался; reset commands установлены.
- **Canonical:** A03-04. **Связи:** Связан повторной delivery с A05-05; не generic ownership finding.

### A03-05 — Поздний loot preorder не попадает в завершённый результат

- **Источник / аудит:** [audit/03_combat_runtime.md:323](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:323); аудит 03. **Code anchors:** [src/backend/features/loot/integrations/stream_client.py:18](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/loot/integrations/stream_client.py:18)
- **Исходная severity:** Medium. **Доказательность:** Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Combat; Loot; Streams. Loot-ready и combat-finished сходятся независимо от порядка.
- **Trigger / impact:** Consumer пишет preorder после finish → Late corpses hidden, routing без loot.
- **Необходимая проверка:** Оба порядка, delay preorder, повтор событий, visibility/result. **Ограничения:** Частота неизвестна; полный user effect требует integration.
- **Canonical:** A03-05. **Связи:** Частичное orchestration A02-05; самостоятельный rendezvous.

### A03-06 — После commit потеря enqueue support оставляет архив без analytics facts

- **Источник / аудит:** [audit/03_combat_runtime.md:330](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:330); аудит 03. **Code anchors:** [src/backend/features/combat/runtime/support/result_support_task.py:16](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/support/result_support_task.py:16)
- **Исходная severity:** Medium. **Доказательность:** Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Combat; Support analytics; ARQ. Committed exchange имеет восстановимый analytics fact.
- **Trigger / impact:** Commit успешен; enqueue support падает → Fact только в памяти потерян, archive неполон.
- **Необходимая проверка:** Enqueue fault, delayed/duplicate support, expected seq. **Ограничения:** Queue fault не инъецировался.
- **Canonical:** A03-06. **Связи:** Частичный A03-12: failure enqueue отдельно от successful delayed support.

### A03-07 — Durability marker не защищает повтор после частично успешного применения

- **Источник / аудит:** [audit/03_combat_runtime.md:336](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:336); аудит 03. **Code anchors:** [src/backend/features/inventory/services/inventory_service.py:197](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/inventory/services/inventory_service.py:197), [src/backend/features/combat/runtime/services/durability_policy.py:56](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/services/durability_policy.py:56)
- **Исходная severity:** Medium. **Доказательность:** Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Combat; Inventory; Character. Durability event меняет SQL mechanics не более раза.
- **Trigger / impact:** SQL commit→AC sync failure→повтор до marker → Повторный износ.
- **Необходимая проверка:** Fault до/после commit/marker, concurrent event, durable delta=1. **Ограничения:** Sequential complete duplicate уже guarded; real integration нет.
- **Canonical:** A03-07. **Связи:** Общая replay причина A03-01/A05-01; разные ledgers/owners.

### A03-08 — Ошибка загрузки policy обходит failed-состояние simulation run

- **Источник / аудит:** [audit/03_combat_runtime.md:342](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:342); аудит 03. **Code anchors:** [src/backend/features/combat/workers/tasks/ai_simulation_task.py:43](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/workers/tasks/ai_simulation_task.py:43)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Experimental. **Срочность:** До beta при включении поверхности.
- **Домены / контракт:** Combat; AI simulation; SQL. Failed job отражается terminal run state.
- **Trigger / impact:** Policy loader ошибается до try → Run не проходит стандартный mark_failed.
- **Необходимая проверка:** Missing row, invalid policy, DB setup error, cancellation. **Ограничения:** Stale cleanup отдельно; integration job не запускалась.
- **Canonical:** A03-08. **Связи:** Cohesion context A02-09; не полный дубль.

### A03-09 — Stale executor context и отсутствие fencing

- **Источник / аудит:** [audit/03_combat_runtime.md:359](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:359); аудит 03. **Code anchors:** [src/backend/features/combat/workers/tasks/executor_task.py:59](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/workers/tasks/executor_task.py:59), [src/backend/infrastructure/combat/managers/session.py:608](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/combat/managers/session.py:608)
- **Исходная severity:** High. **Доказательность:** Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Combat executor; Redis lease. Snapshot writer fenced по version/epoch.
- **Trigger / impact:** Read до lock; expiry между owner check и commit → Предполагаемые stale write/lost update/queue trim.
- **Необходимая проверка:** Two-worker read/acquire/check/save barriers, expiry/restart. **Ограничения:** Production corruption не доказана; lease release owner-aware.
- **Canonical:** A03-09. **Связи:** Зависимость A03-03 atomic commit; не совместный canonical.

### A03-10 — AC dirty generation не является CAS

- **Источник / аудит:** [audit/03_combat_runtime.md:363](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:363); аудит 03. **Code anchors:** [src/backend/infrastructure/actor_state/managers/session.py:166](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/actor_state/managers/session.py:166), [src/backend/infrastructure/actor_state/managers/session.py:119](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/actor_state/managers/session.py:119), [src/backend/features/character/integrations/system_integrator.py:42](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/character/integrations/system_integrator.py:42)
- **Исходная severity:** Medium. **Доказательность:** Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Character AC; Combat; SQL sync. Clear G не очищает mark G+1; replacement не теряет patch.
- **Trigger / impact:** Mutation между generation read и clear; full update → Предполагаемый lost dirty/state.
- **Необходимая проверка:** Sync/finalizer/refresh barriers, patch→mark fault. **Ограничения:** Неатомарность установлена; effect не воспроизведён.
- **Canonical:** A03-10. **Связи:** Причина A02-03/06; похожий независимый A05-03/09.

### A03-11 — Частичный/конкурентный Rift completion

- **Источник / аудит:** [audit/03_combat_runtime.md:367](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:367); аудит 03. **Code anchors:** [src/backend/features/rift/integrations/runtime.py:410](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/integrations/runtime.py:410), [src/backend/features/combat/integrations/system_integrator.py:259](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/integrations/system_integrator.py:259)
- **Исходная severity:** Medium. **Доказательность:** Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Pre-alpha / Legacy (Rift; поддержка runtime неизвестна). **Срочность:** Не исправлять без архитектурного решения о поддержке/выводе Legacy; при текущей публикации сначала проверить экспозицию.
- **Домены / контракт:** Combat; Rift; GameSession. Outcome/completion/instance/session/presence согласованы.
- **Trigger / impact:** Parallel finalizer/continue, crash between saves, missing runtime → Предполагаемое partial result, stale presence, synthetic victory.
- **Необходимая проверка:** Parallel callbacks, fault each save, defeat/missing runtime. **Ограничения:** Sequential successful duplicate no-op; concurrent effect не доказан.
- **Canonical:** A03-11. **Связи:** Частичный A04-15; missing-outcome ветка уточнена A04-02; O02-04 широкий.

### A03-12 — Freeze может обогнать support analytics; TTL и archive retry ограничены

- **Источник / аудит:** [audit/03_combat_runtime.md:371](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:371); аудит 03. **Code anchors:** [src/backend/features/combat/workers/tasks/finalization_persist_task.py:27](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/workers/tasks/finalization_persist_task.py:27), [src/backend/features/combat/workers/tasks/executor_task.py:127](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/workers/tasks/executor_task.py:127), [src/backend/features/combat/runtime/services/finalization_builder.py:25](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/services/finalization_builder.py:25)
- **Исходная severity:** Medium. **Доказательность:** Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Combat; Support; Archive; Mongo; SQL. Freeze содержит expected facts; payload и persist устойчивы.
- **Trigger / impact:** Support после freeze, cache TTL до persist, concurrent insert → Предполагаемый incomplete archive/failed persist.
- **Необходимая проверка:** Delay support, Mongo/SQL outage, concurrent persist, expiry. **Ограничения:** Unique combat_id удерживает одну row; не каждый archive неполон.
- **Canonical:** A03-12. **Связи:** Частичный A03-06; самостоятельный reader A05-11.

### A03-13 — Crit-bleed применяется после парирования/уклонения

- **Источник / аудит:** [audit/03_combat_runtime.md:348](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:348); аудит 03. **Code anchors:** [src/backend/features/game_catalog/combat/resources/triggers/definitions/rules/weapon_triggers.py:12](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/game_catalog/combat/resources/triggers/definitions/rules/weapon_triggers.py:12), [src/backend/features/combat/runtime/engine/resolver/support/trigger_activator.py:71](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/engine/resolver/support/trigger_activator.py:71), [src/backend/features/combat/runtime/engine/resolver/orchestrator.py:50](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/engine/resolver/orchestrator.py:50)
- **Исходная severity:** Medium. **Доказательность:** Исторически воспроизведено локальной проверкой/тестом исходного аудита; сейчас не повторялось. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Combat engine; Game catalog. On-contact crit effect не появляется после parry/dodge.
- **Trigger / impact:** is_hit/is_crit=true при is_parried=true и queued bleed → Материализован лишний status защищённой цели.
- **Необходимая проверка:** Fired trigger precondition; parry/dodge/block/hit/noncrit, tokens отдельно. **Ограничения:** Исторический post-phase probe; полный pipeline pytest не завершён; ненулевой DoT не измерен.
- **Canonical:** A03-13. **Связи:** Зависимость тестовой защиты A06-02; не полный дубль.

## Аудит 04

### A04-01 — клиент управляет игровыми исходами

- **Источник / аудит:** [audit/04_rift_world_generation.md:111](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:111); аудит 04. **Code anchors:** [src/backend/features/rift/api/router.py:56](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/api/router.py:56), [src/backend/features/rift/dto/runtime.py:17](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/dto/runtime.py:17), [src/backend/features/rift/services/player_service.py:64](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/services/player_service.py:64)
- **Исходная severity:** High. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Legacy (поддержка runtime неизвестна). **Срочность:** Не исправлять без архитектурного решения о поддержке/выводе Legacy; при текущей публикации сначала проверить экспозицию.
- **Домены / контракт:** Rift player API; Character; Combat. Сервер определяет event/outcome/attributes.
- **Trigger / impact:** Client overrides в существующем player runtime → Обход transition combat/blocker checks.
- **Необходимая проверка:** Player DTO→service negative force_event/outcome/attributes, guards сохраняются. **Ограничения:** Node combat manual resolve уже запрещён; full exploit/production нет.
- **Canonical:** A04-01. **Связи:** Полный дубль A07-05; canonical A04-01.

### A04-02 — отсутствие результата боя трактуется как победа

- **Источник / аудит:** [audit/04_rift_world_generation.md:123](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:123); аудит 04. **Code anchors:** [src/backend/features/combat/api/router.py:48](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/api/router.py:48), [src/backend/features/combat/integrations/system_integrator.py:259](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/integrations/system_integrator.py:259), [src/backend/features/rift/integrations/runtime.py:453](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/integrations/runtime.py:453)
- **Исходная severity:** High. **Доказательность:** Исторически воспроизведено локальной проверкой/тестом исходного аудита; сейчас не повторялось. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Legacy (Rift) / Pre-alpha (Combat). **Срочность:** Не исправлять без архитектурного решения о поддержке/выводе Legacy; при текущей публикации сначала проверить экспозицию.
- **Домены / контракт:** Combat; Rift; recovery. Unknown combat result не победа и не clears gate.
- **Trigger / impact:** Missing combat runtime и archive при active guard → Cleared event/open gate без результата.
- **Необходимая проверка:** Real integrations с fake stores: missing/defeat/known victory; затем expiry/restart. **Ограничения:** Исторический in-memory repro; не network/cross-store proof.
- **Canonical:** A04-02. **Связи:** Частичный A03-11; причина outcome, не constructor coupling A02-02.

### A04-03 — начальное прохождение не сохраняется в Mongo

- **Источник / аудит:** [audit/04_rift_world_generation.md:140](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:140); аудит 04. **Code anchors:** [src/backend/features/rift/services/entry_service.py:54](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/services/entry_service.py:54), [src/backend/features/rift/integrations/runtime.py:55](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/integrations/runtime.py:55), [src/backend/features/rift/integrations/runtime.py:148](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/integrations/runtime.py:148)
- **Исходная severity:** High. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Legacy (поддержка runtime неизвестна). **Срочность:** Не исправлять без архитектурного решения о поддержке/выводе Legacy; при текущей публикации сначала проверить экспозицию.
- **Домены / контракт:** Rift; Redis; Mongo; membership SQL. Начатый run имеет durable initial snapshot.
- **Trigger / impact:** Entry без дальнейшего action; Redis TTL/loss → Membership есть, restore snapshot отсутствует.
- **Необходимая проверка:** Fresh entry→loss Redis→restore session/presence/refs. **Ограничения:** Реальное ожидание TTL не выполнено.
- **Canonical:** A04-03. **Связи:** Частичное checkpoint/restore пересечение A05-10; иная причина.

### A04-04 — membership остаётся активным после выхода

- **Источник / аудит:** [audit/04_rift_world_generation.md:148](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:148); аудит 04. **Code anchors:** [src/backend/features/rift/services/player_service.py:173](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/services/player_service.py:173), [src/backend/features/rift/integrations/runtime.py:141](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/integrations/runtime.py:141), [src/backend/infrastructure/rift/repositories/state.py:61](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/rift/repositories/state.py:61)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Legacy (поддержка runtime неизвестна). **Срочность:** Не исправлять без архитектурного решения о поддержке/выводе Legacy; при текущей публикации сначала проверить экспозицию.
- **Домены / контракт:** Rift; membership SQL; Redis. Terminal exit исключён из active restore index.
- **Trigger / impact:** Leave/complete без membership mark_status → SQL active membership остаётся eligible.
- **Необходимая проверка:** Exit→SQL status→restore lookup после повторного входа. **Ограничения:** Автоматический re-entry каждого игрока не заявляется.
- **Canonical:** A04-04. **Связи:** Самостоятельный lifecycle index, не snapshot/restore A05-10.

### A04-05 — entry не идемпотентен

- **Источник / аудит:** [audit/04_rift_world_generation.md:156](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:156); аудит 04. **Code anchors:** [src/backend/features/rift/services/entry_service.py:86](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/services/entry_service.py:86)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Legacy (поддержка runtime неизвестна). **Срочность:** Не исправлять без архитектурного решения о поддержке/выводе Legacy; при текущей публикации сначала проверить экспозицию.
- **Домены / контракт:** Rift; Scenario; Character. Один request_id создаёт один run.
- **Trigger / impact:** Повтор prepare одинакового char/request/seed → Новые UUID/membership, overwritten refs, orphan run.
- **Необходимая проверка:** Repeat entry, crash до linkage; count/identity invariant. **Ограничения:** Совместный вход разных players не готовый подтверждённый механизм.
- **Canonical:** A04-05. **Связи:** Общая replay причина A03-04; разные owners/creation contracts.

### A04-06 — повторный start уничтожает прежний travel

- **Источник / аудит:** [audit/04_rift_world_generation.md:164](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:164); аудит 04. **Code anchors:** [src/backend/features/rift/runtime/navigation/screen_builder.py:134](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/runtime/navigation/screen_builder.py:134), [src/backend/features/rift/runtime/navigation/screen_builder.py:347](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/runtime/navigation/screen_builder.py:347), [src/backend/features/rift/services/player_service.py:154](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/services/player_service.py:154)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Legacy (поддержка runtime неизвестна). **Срочность:** Не исправлять без архитектурного решения о поддержке/выводе Legacy; при текущей публикации сначала проверить экспозицию.
- **Домены / контракт:** Rift travel; Character state. Активный travel/encounter требует отказа либо явной отмены.
- **Trigger / impact:** Start во время interrupted travel/combat → Перезаписан прежний active_travel.
- **Необходимая проверка:** Start→combat interrupt→second start; state/status matrix. **Ограничения:** Статический path; runtime regression не повторён.
- **Canonical:** A04-06. **Связи:** Самостоятельный navigation contract.

### A04-07 — межпроцессная невоспроизводимость seed

- **Источник / аудит:** [audit/04_rift_world_generation.md:172](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:172); аудит 04. **Code anchors:** [src/backend/features/rift/runtime/generation/zone_instance.py:848](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/runtime/generation/zone_instance.py:848)
- **Исходная severity:** Medium. **Доказательность:** Исторически воспроизведено локальной проверкой/тестом исходного аудита; сейчас не повторялось. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Legacy (поддержка runtime неизвестна). **Срочность:** Не исправлять без архитектурного решения о поддержке/выводе Legacy; при текущей публикации сначала проверить экспозицию.
- **Домены / контракт:** Rift generation; Python RNG. Seed/config задают normalized topology независимо от hash seed.
- **Trigger / impact:** rng.choice списка из set[str] в разных процессах → Различные finish/void structure.
- **Необходимая проверка:** Same seed/config, PYTHONHASHSEED 1/2/3, normalized graph equality. **Ограничения:** Историческая process probe; новых запусков нет; UUID исключены.
- **Canonical:** A04-07. **Связи:** Независим от local/global RNG observation O02-03.

### A04-08 — Knowledge XP cap не включается

- **Источник / аудит:** [audit/04_rift_world_generation.md:188](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:188); аудит 04. **Code anchors:** [src/backend/features/exploration/services/encounter_service.py:46](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/exploration/services/encounter_service.py:46), [src/backend/features/exploration/integrations/encounter_integration.py:63](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/exploration/integrations/encounter_integration.py:63), [src/backend/features/exploration/services/encounter_service.py:285](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/exploration/services/encounter_service.py:285)
- **Исходная severity:** High. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Exploration; Knowledge; Character progression. Штатный encounter path включает XP cap.
- **Trigger / impact:** Integration не сохраняет redis; _knowledge=None → Награда идёт uncapped progression.
- **Необходимая проверка:** Штатный wiring, повтор сверх location budget, total capped. **Ограничения:** Количественное XP accumulation не исполнялось.
- **Canonical:** A04-08. **Связи:** Зависимость A06-04 wiring regression; самостоятельный economic policy.

### A04-09 — отказ перемещения игнорируется

- **Источник / аудит:** [audit/04_rift_world_generation.md:196](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:196); аудит 04. **Code anchors:** [src/backend/features/exploration/gateway/exploration_gateway.py:63](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/exploration/gateway/exploration_gateway.py:63), [src/backend/features/exploration/integrations/system_integrator.py:44](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/exploration/integrations/system_integrator.py:44)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Exploration gateway; World; Character. Rejected move не публикует target success/encounter.
- **Trigger / impact:** Target исчезает между resolve и move; False игнорируется → Позиция прежняя, ответ описывает другую.
- **Необходимая проверка:** False move injection, no target encounter, actual position response. **Ограничения:** No real store race; specified branch.
- **Canonical:** A04-09. **Связи:** Самостоятельный state acknowledgment contract.

### A04-10 — World cache не имеет полного контракта публикации

- **Источник / аудит:** [audit/04_rift_world_generation.md:204](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:204); аудит 04. **Code anchors:** [src/backend/features/world/tasks_ai.py:98](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/world/tasks_ai.py:98), [src/backend/features/world/services/cache_service.py:26](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/world/services/cache_service.py:26), [src/backend/infrastructure/world/location_store.py:35](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/world/location_store.py:35)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** World; AI handlers; SQL; Redis bootstrap. Cache publication полна/актуальна либо явно отказала.
- **Trigger / impact:** AI update SQL, deactivate node, partial pipeline, rollback bootstrap → Stale content/keys или phantom projection.
- **Необходимая проверка:** AI→Redis read, deactivate→warm, failed write/rollback. **Ограничения:** Bootstrap rollback — дополнительный риск; actual production нет.
- **Canonical:** A04-10. **Связи:** Причина publish-boundary, отдельна от GenerationAI task payload.

### A04-11 — несовместимые лимиты повторов GenerationAI

- **Источник / аудит:** [audit/04_rift_world_generation.md:215](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:215); аудит 04. **Code anchors:** [src/backend/features/generation_ai/services.py:216](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/services.py:216), [src/backend/features/generation_ai/repositories.py:142](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/repositories.py:142), [src/backend/features/world/tasks_ai.py:169](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/world/tasks_ai.py:169)
- **Исходная severity:** High. **Доказательность:** Исторически воспроизведено локальной проверкой/тестом исходного аудита; сейчас не повторялось. **Стадия:** Shared infrastructure (Pre-alpha). **Срочность:** При стабилизации домена.
- **Домены / контракт:** GenerationAI; World JSON; SQL; ARQ. Cooldown достижим следующим claim либо task terminal.
- **Trigger / impact:** Четыре schema failures при max_attempts=4 и service limit8 → Cooldown task нельзя claim снова.
- **Необходимая проверка:** Claims/errors до terminal; реальный SQL attempt predicate. **Ограничения:** Историческая condition probe; не real SQL/ARQ; Monster limit8 не этот case.
- **Canonical:** A04-11. **Связи:** Независим от commit→enqueue A05-08.

### A04-12 — первоначальный payload может быть потерян

- **Источник / аудит:** [audit/04_rift_world_generation.md:232](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:232); аудит 04. **Code anchors:** [src/backend/features/generation_ai/repositories.py:221](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/repositories.py:221), [src/backend/features/generation_ai/repositories.py:249](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/repositories.py:249), [src/backend/features/world/tasks_ai.py:55](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/world/tasks_ai.py:55)
- **Исходная severity:** High. **Доказательность:** Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Shared infrastructure (Pre-alpha). **Срочность:** При стабилизации домена.
- **Домены / контракт:** GenerationAI; World; Mongo; SQL. Accepted task имеет durable recoverable input.
- **Trigger / impact:** Mongo initial write fails, SQL commit/schedule succeeds → Bare hydrated task без исходного payload.
- **Необходимая проверка:** Initial outage→restart→recovery или exact rejection. **Ограничения:** Real Mongo не проверена; severity High сохранена.
- **Canonical:** A04-12. **Связи:** Полный дубль A05-07; canonical A04-12.

### A04-13 — done возможен без сохранённого результата

- **Источник / аудит:** [audit/04_rift_world_generation.md:240](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:240); аудит 04. **Code anchors:** [src/backend/features/generation_ai/repositories.py:159](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/repositories.py:159), [src/backend/features/generation_ai/repositories.py:261](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/repositories.py:261), [src/backend/features/generation_ai/workers/tasks.py:31](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/workers/tasks.py:31)
- **Исходная severity:** Medium. **Доказательность:** Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. **Стадия:** Shared infrastructure (Pre-alpha). **Срочность:** При стабилизации домена.
- **Домены / контракт:** GenerationAI; Mongo results; SQL status. Done соответствует сохранённой task history/result.
- **Trigger / impact:** Record_result fails после domain apply → Done без полного JSON-result/history.
- **Необходимая проверка:** Result outage после apply, SQL status и payload availability. **Ограничения:** Уже применённый игровой контент не объявлен потерянным.
- **Canonical:** A04-13. **Связи:** Самостоятельный result contract; не initial input A04-12.

### A04-14 — статический аудит World сломан

- **Источник / аудит:** [audit/04_rift_world_generation.md:248](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:248); аудит 04. **Code anchors:** [tools/world_static_audit.py:230](D:/Workspace/personal/pets/TurnBasedMMORPG/tools/world_static_audit.py:230), [src/backend/features/world/services/generator_service.py:165](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/world/services/generator_service.py:165)
- **Исходная severity:** Low. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Dev-only. **Срочность:** Отложить до утверждения применимого контракта/использования поверхности.
- **Домены / контракт:** World local audit tool. CLI вызывает актуальную constructor signature.
- **Trigger / impact:** LLMWorldGenerator(data, ai=None) → TypeError после успешных imports.
- **Необходимая проверка:** Bounded tool constructor/invariants после разрешения env. **Ограничения:** Full CLI не завершился; signatures сравнивались.
- **Canonical:** A04-14. **Связи:** Связан stale script test A06-01 по knowledge, иной entrypoint.

### A04-15 — Два обработчика результата читают одинаковый active_encounter_id и независимо сохраняют instance/session. Barrier-test параллельных finalizer/return должен подтвердить одно логическое применение

- **Источник / аудит:** [audit/04_rift_world_generation.md:314](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:314); аудит 04. **Code anchors:** [src/backend/features/rift/integrations/runtime.py:410](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/integrations/runtime.py:410)
- **Исходная severity:** High. **Доказательность:** Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Legacy (поддержка runtime неизвестна). **Срочность:** Не исправлять без архитектурного решения о поддержке/выводе Legacy; при текущей публикации сначала проверить экспозицию.
- **Домены / контракт:** Rift; Combat completion. Один encounter применяет один logical result.
- **Trigger / impact:** Два handlers после same active encounter read → Предполагаемые duplicate/lost/presence partial effects.
- **Необходимая проверка:** Parallel finalizer/return barriers; crash после session save. **Ограничения:** Guard sequential no-op; concurrency не воспроизведена.
- **Canonical:** A04-15. **Связи:** Частичный A03-11; O02-04 широкий scope.

### A04-16 — XP сердца начисляется до записи завершения и очистки ссылок. Инъекция ошибки после начисления и повтор complete должны доказать отсутствие второй награды

- **Источник / аудит:** [audit/04_rift_world_generation.md:315](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:315); аудит 04. **Code anchors:** [src/backend/features/rift/services/player_service.py:192](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/services/player_service.py:192)
- **Исходная severity:** High. **Доказательность:** Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Legacy (поддержка runtime неизвестна). **Срочность:** Не исправлять без архитектурного решения о поддержке/выводе Legacy; при текущей публикации сначала проверить экспозицию.
- **Домены / контракт:** Rift heart completion; progression. Heart XP применён один раз при повторе/fault.
- **Trigger / impact:** XP до finish/cleanup; failure и повтор complete → Предполагаемая вторая reward.
- **Необходимая проверка:** Error сразу после XP, retry/concurrent complete, cumulative delta. **Ограничения:** Нормальный fully completed repeat не объявлен уязвимым.
- **Canonical:** A04-16. **Связи:** Частичный A07-18; independent от Combat XP A03-01.

### A04-17 — Между snapshot write и clear_dirty приходит новое движение. Новая dirty revision должна сохраниться

- **Источник / аудит:** [audit/04_rift_world_generation.md:316](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:316); аудит 04. **Code anchors:** [src/backend/features/rift/integrations/runtime.py:287](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/integrations/runtime.py:287)
- **Исходная severity:** Medium. **Доказательность:** Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Legacy (поддержка runtime неизвестна). **Срочность:** Не исправлять без архитектурного решения о поддержке/выводе Legacy; при текущей публикации сначала проверить экспозицию.
- **Домены / контракт:** Rift checkpoint; Redis; Mongo; SQL. Snapshot G ack не очищает dirty G+1.
- **Trigger / impact:** Movement между capture/write и clear → Предполагаемый rollback к старому snapshot.
- **Необходимая проверка:** Mutation barrier, dirty/new revision survives; two flush. **Ограничения:** Исторический risk; более позднее статическое window в A05-09.
- **Canonical:** A04-17. **Связи:** Полный дубль A05-09; canonical A04-17.

### A04-18 — После SQL commit не выполняется ARQ enqueue; либо asset/Mongo write выполнен, а SQL откатился. Проверить recovery очереди и очистку несвязанных результатов

- **Источник / аудит:** [audit/04_rift_world_generation.md:317](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:317); аудит 04. **Code anchors:** [src/backend/features/generation_ai/workers/tasks.py:33](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/workers/tasks.py:33), [src/backend/features/generation_ai/services.py:169](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/services.py:169), [src/backend/features/generation_ai/repositories.py:55](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/repositories.py:55)
- **Исходная severity:** Medium. **Доказательность:** Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Shared infrastructure (Pre-alpha). **Срочность:** При стабилизации домена.
- **Домены / контракт:** GenerationAI; Assets; Mongo; SQL; ARQ. Committed task queued; external results имеют reconciliation.
- **Trigger / impact:** Commit→enqueue crash; bytes/Mongo→SQL rollback → Task stranded либо orphan/repeated generation.
- **Необходимая проверка:** Enqueue fault/restart, orphan asset/document reconciliation. **Ограничения:** Broad две границы; не все orphan effects воспроизведены.
- **Canonical:** A04-18. **Связи:** Частичный A05-08 scheduling; не полный дубль из-за assets/Mongo.

### A04-19 — У внешнего WorldRegionNodeGenerator road_cells пуст, тогда как межрегиональный выход требует дороги с обеих сторон. Проверять при подключении; это не поломка доступного сейчас D4

- **Источник / аудит:** [audit/04_rift_world_generation.md:318](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:318); аудит 04. **Code anchors:** [src/backend/features/world/runtime/node_graph.py:49](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/world/runtime/node_graph.py:49), [src/backend/features/world/services/navigation_service.py:84](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/world/services/navigation_service.py:84)
- **Исходная severity:** Medium. **Доказательность:** Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Pre-alpha (неподключённый генератор). **Срочность:** При стабилизации домена.
- **Домены / контракт:** WorldRegionNodeGenerator; World roads. External region crossing требует road on both sides.
- **Trigger / impact:** Подключение генератора с пустым road_cells → Предполагаемо отсутствуют межрегиональные exits.
- **Необходимая проверка:** Road reciprocity/boundaries при реальном подключении. **Ограничения:** Current D4 этим не сломан; закрытые gates могут быть intended.
- **Canonical:** A04-19. **Связи:** Самостоятельный future content/navigation contract.

### A04-20 — Hex movement проверяет соседство и walkable, но не edge masks; ответы действий возвращают полный state. Старый next_floor расходится с текущим single-floor heart layout

- **Источник / аудит:** [audit/04_rift_world_generation.md:319](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:319); аудит 04. **Code anchors:** [src/backend/features/rift/services/hex_runtime_service.py:104](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/services/hex_runtime_service.py:104), [src/backend/features/rift/api/hex_test_router.py:84](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/api/hex_test_router.py:84), [src/backend/features/rift/runtime/hex/generation/builder.py:2486](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/runtime/hex/generation/builder.py:2486)
- **Исходная severity:** Low. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Experimental / Dev-only. **Срочность:** Отложить до утверждения применимого контракта/использования поверхности.
- **Домены / контракт:** Hex prototype; movement; next_floor. Dev contract согласует masks/state/single-floor heart.
- **Trigger / impact:** Move по adjacent walkable без masks; old next_floor → Неоднозначная dev semantics; full state response.
- **Необходимая проверка:** Edges/masks, state projection, single-floor/next_floor owner decision. **Ограничения:** Tests фиксируют single-floor; не production blocker.
- **Canonical:** A04-20. **Связи:** Частичный content scope A08-04; exposure/retention иные причины.

### A04-21 — Exploration local map помечает существующие соседние локации известными без обращения к персональному knowledge. Дефект только при требовании персонального тумана войны

- **Источник / аудит:** [audit/04_rift_world_generation.md:320](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:320); аудит 04. **Code anchors:** [src/backend/features/exploration/services/navigation_service.py:105](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/exploration/services/navigation_service.py:105)
- **Исходная severity:** Не присвоена. **Доказательность:** Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Pre-alpha. **Срочность:** Не исправлять без архитектурного решения о персональном fog-of-war.
- **Домены / контракт:** Exploration local map; Knowledge; product policy. Персональный fog-of-war только при утверждённом требовании.
- **Trigger / impact:** Cached соседние nodes показываются без knowledge → Возможное раскрытие map data относительно будущей policy.
- **Необходимая проверка:** Уточнить contract; known/unknown fixtures после решения. **Ограничения:** Severity не присвоена; обязательный current fog contract не установлен.
- **Canonical:** A04-21. **Связи:** Не исправлять без архитектурного решения; независим от XP cap A04-08.

## Аудит 05

### A05-01 — Safe loot claim не сохраняет количество ресурсов при повторе

- **Источник / аудит:** [audit/05_persistence_consistency.md:268](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:268); аудит 05. **Code anchors:** [src/backend/features/loot/workers/tasks/loot_claim_task.py:203](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/loot/workers/tasks/loot_claim_task.py:203)
- **Исходная severity:** High. **Доказательность:** Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Loot; Inventory; Expedition; SQL; Redis. Выдано не больше source debit; claim один раз.
- **Trigger / impact:** Safe replay после SQL commit до Redis remove; zero/absent source → Создание валюты/ресурсов.
- **Необходимая проверка:** Duplicate/two claimants, insufficient source, first batch commit fault. **Ограничения:** Row lock сериализует, но не conservation; real PG repro нет.
- **Canonical:** A05-01. **Связи:** Причина amplification A05-04; different ledger от A03-01/07.

### A05-02 — Loot SQL transfer не проверяет точный источник предмета

- **Источник / аудит:** [audit/05_persistence_consistency.md:276](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:276); аудит 05. **Code anchors:** [src/backend/features/loot/workers/tasks/loot_claim_task.py:213](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/loot/workers/tasks/loot_claim_task.py:213), [src/backend/features/loot/services/loot_service.py:332](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/loot/services/loot_service.py:332)
- **Исходная severity:** High. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Loot; Items; Inventory. Transfer exact SQL holder; success соответствует rowcount.
- **Trigger / impact:** Stale/replayed payload после source lifecycle change → Wrong recipient/false-success claim.
- **Необходимая проверка:** Other corpse/system, zero-row transfer, two claimants. **Ограничения:** PK предотвращает duplicate row, не неправильный transfer.
- **Canonical:** A05-02. **Связи:** Самостоятельная ownership проверка; A05-01 resource conservation отдельно.

### A05-03 — Inventory snapshot/flush не сериализованы

- **Источник / аудит:** [audit/05_persistence_consistency.md:284](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:284); аудит 05. **Code anchors:** [src/backend/features/inventory/services/inventory_service.py:84](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/inventory/services/inventory_service.py:84), [src/backend/infrastructure/inventory/managers/session.py:20](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/inventory/managers/session.py:20), [src/backend/features/inventory/workers/tasks/session_tasks.py:22](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/inventory/workers/tasks/session_tasks.py:22)
- **Исходная severity:** Medium. **Доказательность:** Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Inventory; Character; Redis; SQL. Accepted action не стирается чужой action/flush.
- **Trigger / impact:** Same snapshot writers или action перед clean SET → Rollback layout/equipment и inconsistent loadout.
- **Необходимая проверка:** Action/action, action/flush barriers, next sweep SQL/AC. **Ограничения:** Interleaving не запускался; item duplication не доказана.
- **Canonical:** A05-03. **Связи:** Общая CAS причина A03-10/A05-09; разные keyspaces/contracts.

### A05-04 — Death corpse публикуется до SQL commit, repair неполон

- **Источник / аудит:** [audit/05_persistence_consistency.md:292](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:292); аудит 05. **Code anchors:** [src/backend/features/expedition/service.py:238](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/expedition/service.py:238)
- **Исходная severity:** Medium. **Доказательность:** Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Expedition; Loot; Character. Corpse имеет committed source и rebuild до expiry.
- **Trigger / impact:** Redis publication до commit; Redis loss после commit → Phantom corpse либо недоступное имущество.
- **Необходимая проверка:** Commit failure after Redis save; loss before expires_at; retry same contents. **Ограничения:** Штатный expiry не дефект; real fault нет.
- **Canonical:** A05-04. **Связи:** Зависимость ущерба A05-01; архитектурный context A02-01.

### A05-05 — Streams pending не восстанавливаются

- **Источник / аудит:** [audit/05_persistence_consistency.md:300](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:300); аудит 05. **Code anchors:** [src/backend/core/containers/redis.py:136](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/core/containers/redis.py:136), [.venv/Lib/site-packages/codex_platform/streams/processor.py:180](D:/Workspace/personal/pets/TurnBasedMMORPG/.venv/Lib/site-packages/codex_platform/streams/processor.py:180), [src/backend/core/bus/producer.py:60](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/core/bus/producer.py:60)
- **Исходная severity:** High. **Доказательность:** Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. **Стадия:** Shared infrastructure (Pre-alpha / Legacy). **Срочность:** Не исправлять без архитектурного решения о поддержке/выводе Legacy; при текущей публикации сначала проверить экспозицию.
- **Домены / контракт:** Core bus consumers; codex-platform; Redis. Accepted message завершён либо retry/DLQ доступен.
- **Trigger / impact:** Crash/read/handler error оставляет PEL; consumer читает > → Stranded lifecycle/reward events; trim missing payload.
- **Необходимая проверка:** Real Redis before/after effect, restart, XPENDING/retention, dedup. **Ограничения:** Installed dependency examined; prod version неизвестна.
- **Canonical:** A05-05. **Связи:** Зависимость consumer idempotency A03-01/04,A05-01; не одна задача.

### A05-06 — Chat archive cursor пропускает неуспешную запись

- **Источник / аудит:** [audit/05_persistence_consistency.md:308](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:308); аудит 05. **Code anchors:** [src/backend/chat/workers/archive.py:44](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/chat/workers/archive.py:44), [src/backend/chat/api/router.py:112](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/chat/api/router.py:112), [src/backend/chat/services/message_service.py:42](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/chat/services/message_service.py:42)
- **Исходная severity:** High. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Chat; Redis; Mongo; SQL. Checkpoint не обходит failed original body.
- **Trigger / impact:** Mongo/SQL outage на записи batch → Cursor advances, история permanently missing body.
- **Необходимая проверка:** One-off Nth failure→retry, all bodies unique IDs; XADD failure. **Ограничения:** Visible broadcast не durable acceptance; no real outage.
- **Canonical:** A05-06. **Связи:** Independent от throughput A09-03 и append-seq A05-15.

### A05-07 — GenerationAI принимает task без сохранённого input

- **Источник / аудит:** [audit/05_persistence_consistency.md:316](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:316); аудит 05. **Code anchors:** [src/backend/features/generation_ai/repositories.py:228](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/repositories.py:228), [src/backend/features/generation_ai/tasks_news.py:18](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/tasks_news.py:18)
- **Исходная severity:** Medium. **Доказательность:** Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Shared infrastructure (Pre-alpha). **Срочность:** При стабилизации домена.
- **Домены / контракт:** GenerationAI; Content; SQL; Mongo; ARQ. Accepted task имеет durable input.
- **Trigger / impact:** Initial Mongo failure подавлен; pending schedules bare task → Неисполнимый запрос/потеря input.
- **Необходимая проверка:** Initial write/read outages, restart; recover/reject без orphan pending. **Ограничения:** Severity Medium сохранена; material resource loss не доказана.
- **Canonical:** A04-12. **Связи:** Полный дубль A04-12; canonical A04-12.

### A05-08 — GenerationAI pending/cooldown теряется между commit и enqueue

- **Источник / аудит:** [audit/05_persistence_consistency.md:324](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:324); аудит 05. **Code anchors:** [src/backend/features/generation_ai/api.py:52](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/api.py:52), [src/backend/features/generation_ai/workers/tasks.py:32](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/workers/tasks.py:32)
- **Исходная severity:** Medium. **Доказательность:** Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. **Стадия:** Shared infrastructure (Pre-alpha). **Срочность:** При стабилизации домена.
- **Домены / контракт:** GenerationAI; SQL; ARQ Redis. Committed schedulable row eventually получает job.
- **Trigger / impact:** Crash/fault после commit; in-memory list очищен до enqueue → Durable pending/cooldown stranded без scanner.
- **Необходимая проверка:** Kill after commit, enqueue/follow-up fault, due-row replay. **Ограничения:** Manual resend может помочь; real runtime recovery не запускался.
- **Canonical:** A05-08. **Связи:** Частичный A04-18; independent retry-limit A04-11.

### A05-09 — Rift snapshot flush очищает новую dirty-мутацию

- **Источник / аудит:** [audit/05_persistence_consistency.md:332](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:332); аудит 05. **Code anchors:** [src/backend/features/rift/integrations/runtime.py:287](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/integrations/runtime.py:287), [src/backend/infrastructure/rift/managers/session.py:115](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/rift/managers/session.py:115)
- **Исходная severity:** Medium. **Доказательность:** Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Legacy (поддержка runtime неизвестна). **Срочность:** Не исправлять без архитектурного решения о поддержке/выводе Legacy; при текущей публикации сначала проверить экспозицию.
- **Домены / контракт:** Rift; Redis; Mongo; SQL. Ack captured G не чистит новое изменение G+1.
- **Trigger / impact:** Mutation после snapshot capture до clear → Потеря сигнала flush; rollback после Redis loss.
- **Необходимая проверка:** Mutation barrier, two flush workers, non-regressing snapshot. **Ограничения:** No real Redis repro; window статически установлено.
- **Canonical:** A04-17. **Связи:** Полный дубль A04-17; canonical A04-17.

### A05-10 — Rift restore считает instance достаточным и перезаписывает живые sessions

- **Источник / аудит:** [audit/05_persistence_consistency.md:340](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:340); аудит 05. **Code anchors:** [src/backend/features/rift/integrations/runtime.py:172](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/integrations/runtime.py:172), [src/backend/infrastructure/rift/managers/session.py:25](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/rift/managers/session.py:25)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Legacy (поддержка runtime неизвестна). **Срочность:** Не исправлять без архитектурного решения о поддержке/выводе Legacy; при текущей публикации сначала проверить экспозицию.
- **Домены / контракт:** Rift; Redis; Mongo; SQL membership. Restore missing component не игнорирует и не затирает newer live.
- **Trigger / impact:** Session-only expiry; instance-only loss при live S1/snapshot S0 → Run недоступен либо navigation/encounter rollback.
- **Необходимая проверка:** Each-key expiry, S0/S1, interrupted SETs, repeat restore. **Ограничения:** Rewards duplication не доказана; independent component TTL.
- **Canonical:** A05-10. **Связи:** Частичный recovery A04-03; отдельные причины.

### A05-11 — Archive reader обращается к несуществующему SQL payload

- **Источник / аудит:** [audit/05_persistence_consistency.md:348](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:348); аудит 05. **Code anchors:** [src/backend/features/combat/services/result_archive_service.py:147](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/services/result_archive_service.py:147), [src/backend/infrastructure/combat/models/finalization.py:12](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/combat/models/finalization.py:12), [src/backend/features/combat/services/result_archive_service.py:37](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/services/result_archive_service.py:37)
- **Исходная severity:** Medium. **Доказательность:** Исторически воспроизведено локальной проверкой/тестом исходного аудита; сейчас не повторялось. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Combat result archive; Redis; SQL; Mongo. Persisted full archive читается после cache/runtime loss.
- **Trigger / impact:** Reader row.finalization отсутствует в current SQL ORM → Silent None даже при успешном Mongo persist.
- **Необходимая проверка:** Persist→delete Redis→read report; Mongo outage/missing pointer. **Ограничения:** Историческая ORM probe, не e2e; reward data loss не доказана.
- **Canonical:** A05-11. **Связи:** Independent от persist/TTL A03-12; fallback outcome context A04-02.

### A05-12 — Site refresh rotation имеет два commits

- **Источник / аудит:** [audit/05_persistence_consistency.md:356](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:356); аудит 05. **Code anchors:** [src/frontend/features/auth/services/site_auth_service.py:124](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/features/auth/services/site_auth_service.py:124), [src/frontend/features/auth/integrations/auth_persistence.py:67](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/features/auth/integrations/auth_persistence.py:67), [src/frontend/features/auth/repositories/token_repository.py:25](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/features/auth/repositories/token_repository.py:25)
- **Исходная severity:** Medium. **Доказательность:** Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Site Auth; refresh; PostgreSQL. Rotation фиксирует old→new одной durable operation.
- **Trigger / impact:** Delete commit→insert failure; parallel readers → Потеря refresh/forced re-login; race policy unknown.
- **Необходимая проверка:** Fail new insert, concurrent threshold refresh, lost response retry. **Ограничения:** Threshold7d снижает частоту; security compromise не заявляется.
- **Canonical:** A05-12. **Связи:** Independent deactivate/logout A07-09/10.

### A05-13 — Site clean migration конфликтует с live ORM baseline

- **Источник / аудит:** [audit/05_persistence_consistency.md:364](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:364); аудит 05. **Code anchors:** [src/frontend/alembic/versions/0001_site_schema_baseline.py:12](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/alembic/versions/0001_site_schema_baseline.py:12), [src/frontend/features/auth/models/refresh_token.py:15](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/features/auth/models/refresh_token.py:15), [src/frontend/alembic/versions/0002_security_baseline.py:22](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/alembic/versions/0002_security_baseline.py:22)
- **Исходная severity:** High. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha; intended Production). **Срочность:** При стабилизации домена.
- **Домены / контракт:** Site migrations; ORM; deployment. Historical migrations reproducibly строят empty schema.
- **Trigger / impact:** Live metadata baseline then duplicate ADD token/referral/email fields → Clean deploy/restore blocked.
- **Необходимая проверка:** Empty PG upgrade, old schema upgrade, repeat head, schema diff. **Ограничения:** Real migration не запускалась; prod schema unknown; blind stamp/drop недопустим.
- **Canonical:** A05-13. **Связи:** Зависимость operational restore A08-15; повторные упоминания не новые IDs.

### A05-14 — Конкурентное создание двух active Expedition

- **Источник / аудит:** [audit/05_persistence_consistency.md:374](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:374); аудит 05. **Code anchors:** [src/backend/features/expedition/service.py:85](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/expedition/service.py:85), [src/backend/features/expedition/repository.py:25](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/expedition/repository.py:25)
- **Исходная severity:** Medium. **Доказательность:** Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Expedition; Inventory; SQL; Redis. Один live run на character.
- **Trigger / impact:** Two no-row FOR UPDATE reads без external serialization → Предполагаемое разделение pending reward/ownership.
- **Необходимая проверка:** Two real SQL sessions barrier no-row, lifecycle both runs. **Ограничения:** No-row lock не найден; полный entrypoint serialization неизвестен.
- **Canonical:** A05-14. **Связи:** Самостоятельный live-run uniqueness contract.

### A05-15 — Mongo chat append/seq не доказан конкурентно и повторно корректным

- **Источник / аудит:** [audit/05_persistence_consistency.md:382](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:382); аудит 05. **Code anchors:** [src/backend/infrastructure/mongo/chat_buckets.py:48](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/mongo/chat_buckets.py:48)
- **Исходная severity:** Medium. **Доказательность:** Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Chat; Mongo; SQL message index. message_id/seq однозначны при replay/concurrency.
- **Trigger / impact:** Two count reads; Mongo success→SQL rollback; first upsert operators → Предполагаемые duplicate/wrong body или server write failure.
- **Необходимая проверка:** Real Mongo first insert, concurrent append/replay, bucket boundary. **Ограничения:** Single worker уменьшает одну гонку; exact Mongo response не измерен.
- **Canonical:** A05-15. **Связи:** Independent от cursor A05-06; shared implementation A09-08 с иным performance contract.

## Аудит 06

### A06-01 — Сломанная collection после удаления script

- **Источник / аудит:** [audit/06_testing_quality.md:381](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/06_testing_quality.md:381); аудит 06. **Code anchors:** [tests/backend/features/generation_ai/test_asset_backfill.py:6](D:/Workspace/personal/pets/TurnBasedMMORPG/tests/backend/features/generation_ai/test_asset_backfill.py:6), [pyproject.toml:154](D:/Workspace/personal/pets/TurnBasedMMORPG/pyproject.toml:154)
- **Исходная severity:** High. **Доказательность:** Исторически воспроизведено локальной проверкой/тестом исходного аудита; сейчас не повторялось. **Стадия:** Shared infrastructure (Pre-alpha). **Срочность:** При стабилизации домена.
- **Домены / контракт:** Tests; GenerationAI collection. Обязательный test set импортируется полностью.
- **Trigger / impact:** Test импортирует удалённый scripts utility → Collection exit2; full gate blocked.
- **Необходимая проверка:** Clean pytest collect-only0, backfill actual owner entrypoint. **Ограничения:** Исторический collection; не new full run; --ignore не remedy contract.
- **Canonical:** A06-01. **Связи:** Самостоятельный blocker; stale constructor A04-14 иной файл.

### A06-02 — Regression test parry не активирует проверяемый trigger

- **Источник / аудит:** [audit/06_testing_quality.md:391](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/06_testing_quality.md:391); аудит 06. **Code anchors:** [tests/backend/features/combat/test_runtime_processors.py:5556](D:/Workspace/personal/pets/TurnBasedMMORPG/tests/backend/features/combat/test_runtime_processors.py:5556), [src/backend/features/combat/runtime/engine/resolver/orchestrator.py:47](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/engine/resolver/orchestrator.py:47), [src/backend/features/combat/runtime/engine/resolver/support/trigger_activator.py:161](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/engine/resolver/support/trigger_activator.py:161)
- **Исходная severity:** High. **Доказательность:** Исторически воспроизведено локальной проверкой/тестом исходного аудита; сейчас не повторялось. **Стадия:** Shared infrastructure (Pre-alpha). **Срочность:** При стабилизации домена.
- **Домены / контракт:** Combat regression tests; Engine triggers. Negative effect assertion достигает fired trigger precondition.
- **Trigger / impact:** Sequence mock выключает ON_CRIT до parry → Vacuous green test скрывает A03-13.
- **Необходимая проверка:** Fired/attempted assertions, hit positive control, parry/no-effect, tokens. **Ограничения:** Исторический controlled probe assertion fail; wrapper exit0 не pass.
- **Canonical:** A06-02. **Связи:** Зависимость проверки A03-13; game bug и test bug не дубль.

### A06-03 — Нет доказательной защиты реальных storage/broker contracts

- **Источник / аудит:** [audit/06_testing_quality.md:401](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/06_testing_quality.md:401); аудит 06. **Code anchors:** [tests/backend/conftest.py:10](D:/Workspace/personal/pets/TurnBasedMMORPG/tests/backend/conftest.py:10), [tests/backend/features/items/test_instance_repository.py:16](D:/Workspace/personal/pets/TurnBasedMMORPG/tests/backend/features/items/test_instance_repository.py:16), [tests/backend/features/scenario/test_scenario_repository.py:12](D:/Workspace/personal/pets/TurnBasedMMORPG/tests/backend/features/scenario/test_scenario_repository.py:12)
- **Исходная severity:** High. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha / Legacy). **Срочность:** Не исправлять без архитектурного решения о поддержке/выводе Legacy; при текущей публикации сначала проверить экспозицию.
- **Домены / контракт:** Test adapters; SQL; RedisJSON; Mongo; Streams. Server-dependent contracts имеют representative real boundary proof.
- **Trigger / impact:** Fake query/pipeline/wire заменяют server semantics → False confidence ownership/atomicity/delivery.
- **Необходимая проверка:** Disposable server SQL rollback/source, Redis roundtrip/fault, Mongo/index, Streams reclaim. **Ограничения:** External private harness не искался; absence tests не defect proof.
- **Canonical:** A06-03. **Связи:** Зависимость доказательств A03-03/09,A05-01/05/15; не объединять production finds.

### A06-04 — Lifecycle tests не защищают retry/fault invariants наград и восстановления

- **Источник / аудит:** [audit/06_testing_quality.md:411](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/06_testing_quality.md:411); аудит 06. **Code anchors:** [tests/backend/features/combat/test_victory_finalizer_task.py:175](D:/Workspace/personal/pets/TurnBasedMMORPG/tests/backend/features/combat/test_victory_finalizer_task.py:175), [tests/backend/features/combat/test_experience_finalizer.py:229](D:/Workspace/personal/pets/TurnBasedMMORPG/tests/backend/features/combat/test_experience_finalizer.py:229), [tests/backend/features/combat/test_lifecycle_service.py:138](D:/Workspace/personal/pets/TurnBasedMMORPG/tests/backend/features/combat/test_lifecycle_service.py:138)
- **Исходная severity:** High. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha / Legacy). **Срочность:** Не исправлять без архитектурного решения о поддержке/выводе Legacy; при текущей публикации сначала проверить экспозицию.
- **Домены / контракт:** Lifecycle tests; Combat; Rift; GenerationAI. Replay/fault/restart часть contract многошагового effect.
- **Trigger / impact:** Happy path one-call/early retry вместо full sequence → Known reward/recovery defects не ловятся.
- **Необходимая проверка:** Repeat same ID, failure each step, eventual result/conservation, initial snapshot. **Ограничения:** Тестовая модель, не new game ID; real restart отдельно.
- **Canonical:** A06-04. **Связи:** Зависимость A03-01/02/04,A04-03/08/11; partial A06-03 test level.

### A06-05 — Чистый CI checkout не содержит обязательную path dependency

- **Источник / аудит:** [audit/06_testing_quality.md:421](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/06_testing_quality.md:421); аудит 06. **Code anchors:** [pyproject.toml:34](D:/Workspace/personal/pets/TurnBasedMMORPG/pyproject.toml:34), [uv.lock:470](D:/Workspace/personal/pets/TurnBasedMMORPG/uv.lock:470), [.github/workflows/ci.yml:24](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/ci.yml:24)
- **Исходная severity:** High. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha; intended Production). **Срочность:** При стабилизации домена.
- **Домены / контракт:** CI; uv; codex-ai source. Single checkout+install получает все declared sources.
- **Trigger / impact:** Clean runner uv sync без sibling checkout → Missing path dependency blocks gate.
- **Необходимая проверка:** Clean Linux locked install/collect/full gate без venv/sibling. **Ограничения:** Hosted failure не запускался; ready local venv не proof.
- **Canonical:** A06-05. **Связи:** Частичный A08-10: Docker source policy добавляет scope.

### A06-06 — Develop не имеет behavioral gate

- **Источник / аудит:** [audit/06_testing_quality.md:431](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/06_testing_quality.md:431); аудит 06. **Code anchors:** [.github/workflows/ci.yml:3](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/ci.yml:3)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha). **Срочность:** При стабилизации домена.
- **Домены / контракт:** Develop CI workflow. Integration branch получает behavioral checks.
- **Trigger / impact:** Push develop hooks/types only; PR develop вне trigger → Functional regression обнаружится позднее на main.
- **Необходимая проверка:** Event/ref matrix; selected failing test blocks develop check. **Ограничения:** Required checks/remote actual runs неизвестны.
- **Canonical:** A06-06. **Связи:** Independent от clean install A06-05; test set dependency.

### A06-07 — Frontend/backend проверяются раздельно с независимыми fixtures

- **Источник / аудит:** [audit/06_testing_quality.md:441](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/06_testing_quality.md:441); аудит 06. **Code anchors:** [tests/frontend/features/cabinet/test_game_settings_module.py:18](D:/Workspace/personal/pets/TurnBasedMMORPG/tests/frontend/features/cabinet/test_game_settings_module.py:18), [tests/backend/features/test_internal_routers.py:105](D:/Workspace/personal/pets/TurnBasedMMORPG/tests/backend/features/test_internal_routers.py:105), [tests/frontend/features/cabinet/test_cabinet_integration.py:9](D:/Workspace/personal/pets/TurnBasedMMORPG/tests/frontend/features/cabinet/test_cabinet_integration.py:9)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha). **Срочность:** При стабилизации домена.
- **Домены / контракт:** Frontend; Backend; HTTP contract tests. Producer/consumer jointly проверяют critical wire contract.
- **Trigger / impact:** Независимые frontend mock replies/backend expectations → DTO/route/auth/serialization drift проходит раздельно.
- **Необходимая проверка:** Real ASGI consumer→router update/reset/transition, incompatible-field negative. **Ограничения:** Browser/Docker не обязательны; limited sampled HTTP scope.
- **Canonical:** A06-07. **Связи:** Partial A06-03 storage/broker; разные boundaries.

### A06-08 — Архитектурный gate проверяет только часть объявленных invariants

- **Источник / аудит:** [audit/06_testing_quality.md:451](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/06_testing_quality.md:451); аудит 06. **Code anchors:** [tests/backend/features/test_infrastructure_boundaries.py:9](D:/Workspace/personal/pets/TurnBasedMMORPG/tests/backend/features/test_infrastructure_boundaries.py:9), [.agents/skills/turnbasedmmorpg-project/references/project-rules.md:17](D:/Workspace/personal/pets/TurnBasedMMORPG/.agents/skills/turnbasedmmorpg-project/references/project-rules.md:17)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha / Legacy). **Срочность:** Не исправлять без архитектурного решения о поддержке/выводе Legacy; при текущей публикации сначала проверить экспозицию.
- **Домены / контракт:** Architecture tests; Ownership rules. Gate обнаруживает актуальные forbidden imports/keyspaces.
- **Trigger / impact:** Literal6-prefix scan; unconditional Rift skip → Новые нарушения ownership обходят gate.
- **Необходимая проверка:** Synthetic forbidden import/new prefix/Rift violation + allowed adapter. **Ограничения:** Existing relocated-manager regressions полезны; не full rule enforcement.
- **Canonical:** A06-08. **Связи:** Cause protection gaps A02-01/03/08; implementation и enforcement раздельны.

### A06-09 — Deploy workflow не связывает image_ref с успешным quality result

- **Источник / аудит:** [audit/06_testing_quality.md:461](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/06_testing_quality.md:461); аудит 06. **Code anchors:** [.github/workflows/deploy-production.yml:16](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/deploy-production.yml:16), [.github/workflows/build-images.yml:17](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/build-images.yml:17)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (intended Production). **Срочность:** При стабилизации домена.
- **Домены / контракт:** Deploy workflow; Image provenance. Promotion связывает image с successful quality.
- **Trigger / impact:** Manual image_ref без gate/provenance verification → Непроверенный artifact eligible к deploy.
- **Необходимая проверка:** Reject unknown/failed artifact before SSH; tested immutable ref accepted. **Ограничения:** External organisational controls не установлены; deploy не запускался.
- **Canonical:** A06-09. **Связи:** Частичные A08-11 governance и A08-09 mutable chain.

### A06-10 — Coverage защищает общий объём statements, не patch/branches

- **Источник / аудит:** [audit/06_testing_quality.md:471](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/06_testing_quality.md:471); аудит 06. **Code anchors:** [pyproject.toml:165](D:/Workspace/personal/pets/TurnBasedMMORPG/pyproject.toml:165), [docs/ru/management/testing_strategy.md:17](D:/Workspace/personal/pets/TurnBasedMMORPG/docs/ru/management/testing_strategy.md:17), [.agents/skills/turnbasedmmorpg-quality/references/testing.md:7](D:/Workspace/personal/pets/TurnBasedMMORPG/.agents/skills/turnbasedmmorpg-quality/references/testing.md:7)
- **Исходная severity:** Observation. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha). **Срочность:** При стабилизации домена.
- **Домены / контракт:** Coverage policy; Quality reports. Threshold/цель/patch reporting различаются.
- **Trigger / impact:** Statement74% без branch/diff enforcement → Новая branch может быть не защищена; неверное обещание100% patch.
- **Необходимая проверка:** Below74% config smoke; changed-behavior review; future policy only if adopted. **Ограничения:** Observation; соответствует current strategy; total coverage unknown.
- **Canonical:** A06-10. **Связи:** Самостоятельный measurement/policy; не дефект precondition A06-02.

### A06-11 — Stage «unit» не отделяет уровни тестирования

- **Источник / аудит:** [audit/06_testing_quality.md:481](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/06_testing_quality.md:481); аудит 06. **Code anchors:** [pyproject.toml:200](D:/Workspace/personal/pets/TurnBasedMMORPG/pyproject.toml:200), [pyproject.toml:158](D:/Workspace/personal/pets/TurnBasedMMORPG/pyproject.toml:158)
- **Исходная severity:** Low. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha). **Срочность:** При стабилизации домена.
- **Домены / контракт:** Test stages; Markers; Installed runner. Stage selector честно задаёт набор/внешние deps.
- **Trigger / impact:** Unit stage marker пустой; -m unit excludes cases → Неясные уровни; future DB tests без preparation.
- **Необходимая проверка:** Collect stage matrix, explicit external deps, nonempty integration. **Ограничения:** Историческая collection counts; текущая suite не запущена.
- **Canonical:** A06-11. **Связи:** Independent от A06-03 отсутствующей server suite.

### A06-12 — Pip-audit hook проверяет своё окружение вместо зависимостей приложения

- **Источник / аудит:** [audit/06_testing_quality.md:491](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/06_testing_quality.md:491); аудит 06. **Code anchors:** [.pre-commit-config.yaml:39](D:/Workspace/personal/pets/TurnBasedMMORPG/.pre-commit-config.yaml:39), [pyproject.toml:198](D:/Workspace/personal/pets/TurnBasedMMORPG/pyproject.toml:198), [.github/workflows/ci.yml:34](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/ci.yml:34)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha). **Срочность:** При стабилизации домена.
- **Домены / контракт:** Pip-audit; Pre-commit; Develop CI. Dependency audit смотрит application dependency set.
- **Trigger / impact:** Isolated Python hook --local без requirements input → Green hook не подтверждает project packages.
- **Необходимая проверка:** Diagnostic application versions seen; synthetic advisory fails gate. **Ограничения:** CVE service не вызывался; main runner имеет отдельный project audit.
- **Canonical:** A06-12. **Связи:** Частичный supply-chain evidence A08-10; ignore-list drift отдельное наблюдение.

## Аудит 07

### A07-01 — Combat и Rift player API не устанавливают пользователя и владельца

- **Источник / аудит:** [audit/07_application_security.md:167](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:167); аудит 07. **Code anchors:** [src/backend/features/combat/api/router.py:26](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/api/router.py:26), [src/backend/features/combat/dependencies.py:23](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/dependencies.py:23), [src/backend/features/combat/services/session_service.py:143](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/services/session_service.py:143)
- **Исходная severity:** High. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Pre-alpha / Legacy (Rift). **Срочность:** Не исправлять без архитектурного решения о поддержке/выводе Legacy; при текущей публикации сначала проверить экспозицию.
- **Домены / контракт:** Combat; Old Rift; HTTP identity/ownership. Request связан verified game actor/owner/runtime member.
- **Trigger / impact:** Route доступен; path char_id selector без principal → Unauthorized read/mutation по code contract.
- **Необходимая проверка:** Anonymous/wrong token/nonowner/selected mismatch denied before service. **Ограничения:** Production ingress unknown; runtime existence required; Rift support unknown.
- **Canonical:** A07-01. **Связи:** Shared missing-gate cause A07-02/03/04, разные permissions/scopes.

### A07-02 — Runtime config API не требует административного права

- **Источник / аудит:** [audit/07_application_security.md:177](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:177); аудит 07. **Code anchors:** [src/backend/features/game_config/api/router.py:6](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/game_config/api/router.py:6), [src/backend/infrastructure/game_config/manager.py:162](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/game_config/manager.py:162), [src/backend/app.py:53](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/app.py:53)
- **Исходная severity:** High. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha). **Срочность:** До следующего публичного релиза при применимости поверхности; действующая экспозиция требует отдельной проверки.
- **Домены / контракт:** Game config; Admin/service; Redis. Live config read/write требует privileged identity.
- **Trigger / impact:** HTTP config namespace/key operations без auth → Unauthorized valid overrides/reset.
- **Необходимая проверка:** Wrong authority не вызывает manager; keys/value validation сохраняется. **Ограничения:** Not arbitrary Redis injection; actual manager/ingress required.
- **Canonical:** A07-02. **Связи:** Independent config authorization; A08-03 partial public internal exposure.

### A07-03 — Administrative generation/content/simulation API без auth gate

- **Источник / аудит:** [audit/07_application_security.md:187](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:187); аудит 07. **Code anchors:** [src/backend/features/generation_ai/api.py:23](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/api.py:23), [src/backend/features/monsters/api/router.py:24](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/monsters/api/router.py:24), [src/backend/features/monsters/services/generated_rebuild_service.py:47](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/monsters/services/generated_rebuild_service.py:47)
- **Исходная severity:** High. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha / Experimental). **Срочность:** До следующего публичного релиза при применимости поверхности; действующая экспозиция требует отдельной проверки.
- **Домены / контракт:** GenerationAI; Monsters; Combat AI admin. Privileged jobs/content/report operations имеют admin permission.
- **Trigger / impact:** Admin APIs без router/service gate → Затратные jobs/rebuild/report deletes/read доступны по route contract.
- **Необходимая проверка:** No-right before DB/enqueue/provider; appropriate read/status permissions. **Ограничения:** Providers/cost/actual deployment неизвестны; read/delete не требуют worker.
- **Canonical:** A07-03. **Связи:** Producer authorization independent A04-12,A05-08 persistence.

### A07-04 — Internal session diagnostics и combat analytics без доступа по роли

- **Источник / аудит:** [audit/07_application_security.md:197](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:197); аудит 07. **Code anchors:** [src/backend/features/combat/api/internal_router.py:27](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/api/internal_router.py:27), [src/backend/features/scenario/api/internal_router.py:10](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/scenario/api/internal_router.py:10), [src/backend/features/exploration/api/internal_router.py:10](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/exploration/api/internal_router.py:10)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha / Legacy). **Срочность:** Не исправлять без архитектурного решения о поддержке/выводе Legacy; при текущей публикации сначала проверить экспозицию.
- **Домены / контракт:** Internal diagnostics; Combat analytics/backfill. Internal metadata/analytics и backfill role-gated.
- **Trigger / impact:** Unauthenticated list/detail/drilldown/backfill → Runtime identifiers/raw analytics exposed; privileged write.
- **Необходимая проверка:** Role matrix list/detail/filter/backfill, minimal projections. **Ограничения:** Secrets в replies не утверждаются; production data/ingress не читались.
- **Canonical:** A07-04. **Связи:** Частичный A08-03; шире analytics/write permissions.

### A07-05 — Player Rift DTO допускает клиентское управление серверными решениями

- **Источник / аудит:** [audit/07_application_security.md:207](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:207); аудит 07. **Code anchors:** [src/backend/features/rift/dto/runtime.py:17](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/dto/runtime.py:17), [src/backend/features/rift/api/router.py:64](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/api/router.py:64), [src/backend/features/rift/services/player_service.py:64](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/services/player_service.py:64)
- **Исходная severity:** High. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Legacy (поддержка runtime неизвестна). **Срочность:** Не исправлять без архитектурного решения о поддержке/выводе Legacy; при текущей публикации сначала проверить экспозицию.
- **Домены / контракт:** Old Rift player DTO; Server state. Client command не server event/result/attributes.
- **Trigger / impact:** Active Rift принимает diagnostic overrides → Integrity bypass transition/blocker.
- **Необходимая проверка:** Deny player overrides, authoritative combat callback, preserve node guards. **Ограничения:** Постоянные base attributes mutation не доказаны; node completion guard есть.
- **Canonical:** A04-01. **Связи:** Полный дубль A04-01; A04-02 false-victory остаётся отдельным canonical.

### A07-06 — История приватных чатов не проверяет членство

- **Источник / аудит:** [audit/07_application_security.md:218](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:218); аудит 07. **Code anchors:** [src/backend/chat/api/router.py:16](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/chat/api/router.py:16), [src/backend/chat/repositories/message_repo.py:36](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/chat/repositories/message_repo.py:36)
- **Исходная severity:** High. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Pre-alpha. **Срочность:** До следующего публичного релиза при применимости поверхности; действующая экспозиция требует отдельной проверки.
- **Домены / контракт:** Chat history; DM; Membership. Login не private thread permission.
- **Trigger / impact:** Valid bearer + private identifier; membership omitted → Чужая private/group/system history доступна по code contract.
- **Необходимая проверка:** Nonmember/inactive member/system recipient denied before hydration. **Ограничения:** No production history/exploit; public channels отдельная policy.
- **Canonical:** A07-06. **Связи:** Common permission policy with A07-07; read/write paths отдельно.

### A07-07 — Chat send не проверяет разрешённый канал и scope

- **Источник / аудит:** [audit/07_application_security.md:228](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:228); аудит 07. **Code anchors:** [src/backend/realtime/dto/envelope.py:20](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/realtime/dto/envelope.py:20), [src/backend/realtime/api/ws.py:325](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/realtime/api/ws.py:325), [src/backend/realtime/services/chat_bridge.py:78](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/realtime/services/chat_bridge.py:78)
- **Исходная severity:** High. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha. **Срочность:** До следующего публичного релиза при применимости поверхности; действующая экспозиция требует отдельной проверки.
- **Домены / контракт:** Realtime; Chat send; Channel/scope. Signed sender имеет право на channel/scope.
- **Trigger / impact:** Accepted handshake и user-specified service/private channel → Wrong privileged/private addressing/archive/broadcast.
- **Необходимая проверка:** System channel denied, nonmember denied, zone/membership before buffer. **Ограничения:** JWT sender остаётся signed; actual live delivery unknown.
- **Canonical:** A07-07. **Связи:** Частичное membership A07-06; separate publish permission.

### A07-08 — WebSocket chat bootstrap не связывает URL character ID с claims

- **Источник / аудит:** [audit/07_application_security.md:238](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:238); аудит 07. **Code anchors:** [src/backend/realtime/api/ws.py:87](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/realtime/api/ws.py:87), [src/backend/realtime/services/connection_manager.py:39](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/realtime/services/connection_manager.py:39), [src/backend/realtime/services/notice_service.py:45](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/realtime/services/notice_service.py:45)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha. **Срочность:** До следующего публичного релиза при применимости поверхности; действующая экспозиция требует отдельной проверки.
- **Домены / контракт:** WebSocket; Chat bootstrap; Actor mapping. Claims actor единственный identity source.
- **Trigger / impact:** URL char_id отличается от signed character_id → Name/location/zone/reverse map mismatch.
- **Необходимая проверка:** Mismatch rejected; all bootstrap/topics/mappings from claims; reconnect. **Ограничения:** Player.notice использует claims; чужие notices не доказаны.
- **Canonical:** A07-08. **Связи:** Partial session identity A07-11; different websocket boot path.

### A07-09 — Деактивация учётной записи не применяется ко всем действующим сессиям

- **Источник / аудит:** [audit/07_application_security.md:248](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:248); аудит 07. **Code anchors:** [src/frontend/features/auth/services/site_auth_service.py:66](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/features/auth/services/site_auth_service.py:66), [src/frontend/features/auth/services/auth_service.py:103](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/features/auth/services/auth_service.py:103), [src/frontend/features/auth/dependencies/providers.py:50](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/features/auth/dependencies/providers.py:50)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha). **Срочность:** До следующего публичного релиза при применимости поверхности; действующая экспозиция требует отдельной проверки.
- **Домены / контракт:** Site/game auth; Account moderation. Disable account имеет определённую силу для existing sessions.
- **Trigger / impact:** Credentials выданы до is_active=false → Access/game session живут до expiry/lock без common disable.
- **Необходимая проверка:** Disable→site lookup/refresh/game actions/WS bounded revoke. **Ограничения:** Production TTL/external lock revocation unknown.
- **Canonical:** A07-09. **Связи:** Independent persistence A05-12 и logout A07-10.

### A07-10 — Browser logout не завершает game session

- **Источник / аудит:** [audit/07_application_security.md:257](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:257); аудит 07. **Code anchors:** [src/frontend/features/auth/routes/pages.py:137](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/features/auth/routes/pages.py:137), [src/frontend/game_features/session/token_state.py:31](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/game_features/session/token_state.py:31), [src/frontend/game_features/session/middleware.py:56](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/game_features/session/middleware.py:56)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha. **Срочность:** До следующего публичного релиза при применимости поверхности; действующая экспозиция требует отдельной проверки.
- **Домены / контракт:** Site logout; Game cookies; WS session. Общий logout прекращает site и game authority.
- **Trigger / impact:** Browser logout with active game cookie/session → Игровой доступ/refresh сохраняется.
- **Необходимая проверка:** HTTP/refresh/WS deny after logout; domain/path/legacy cookies. **Ограничения:** Actual browser domains не тестировались; разделённый logout требует product decision.
- **Canonical:** A07-10. **Связи:** Independent disable A07-09; legacy cookie cleanup отдельная поверхность.

### A07-11 — Inventory принимает site token вне выбранной game session

- **Источник / аудит:** [audit/07_application_security.md:266](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:266); аудит 07. **Code anchors:** [src/backend/core/auth.py:20](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/core/auth.py:20), [src/backend/features/inventory/api/router.py:42](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/inventory/api/router.py:42), [src/backend/features/inventory/services/inventory_service.py:84](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/inventory/services/inventory_service.py:84)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha. **Срочность:** До следующего публичного релиза при применимости поверхности; действующая экспозиция требует отдельной проверки.
- **Домены / контракт:** Inventory; Site/game auth; Selected actor. Gameplay mutation требует current game context сверх owner.
- **Trigger / impact:** Valid site token owner, inactive character inventory → Изменение своего неактивного персонажа вне session.
- **Необходимая проверка:** Site token denied; selected mismatch denied; good owner/game accepted. **Ограничения:** Cross-user IDOR не установлен; owner query работает.
- **Canonical:** A07-11. **Связи:** Independent HTTP ownership A07-01; guard type/scope иной.

### A07-12 — Studio не обеспечивает auth/read-only contract

- **Источник / аудит:** [audit/07_application_security.md:275](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:275); аудит 07. **Code anchors:** [src/studio/app.py:137](D:/Workspace/personal/pets/TurnBasedMMORPG/src/studio/app.py:137), [src/fastapi_cabinet/site.py:27](D:/Workspace/personal/pets/TurnBasedMMORPG/src/fastapi_cabinet/site.py:27), [src/studio/features/source_selector/middleware.py:25](D:/Workspace/personal/pets/TurnBasedMMORPG/src/studio/features/source_selector/middleware.py:25)
- **Исходная severity:** High. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Dev-only. **Срочность:** Немедленно проверить или ограничить доступ при Studio рядом с live source; actual tunnel/access неизвестны.
- **Домены / контракт:** Studio; Source selector; Cabinet; Backend HTTP. Analytical Studio auth/read-only действует до backend call.
- **Trigger / impact:** Accessible Studio; selected source backend can write → Mutating HTTP actions despite read-only label/source.
- **Необходимая проверка:** Unauthorized denied; every action source policy before write; allowlist. **Ограничения:** Prod tunnel/ACL/permissions unknown; не public-prod claim; DB readonly не protects HTTP.
- **Canonical:** A07-12. **Связи:** Зависимость source permissions; partial A08-08 local exposure; отдельный enforcement.

### A07-13 — Backend Exploration не имеет actor/ownership dependency

- **Источник / аудит:** [audit/07_application_security.md:285](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:285); аудит 07. **Code anchors:** [src/backend/features/exploration/api/router.py:17](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/exploration/api/router.py:17), [src/backend/features/exploration/gateway/exploration_gateway.py:30](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/exploration/gateway/exploration_gateway.py:30), [src/backend/app.py:72](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/app.py:72)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha. **Срочность:** До следующего публичного релиза при применимости поверхности; действующая экспозиция требует отдельной проверки.
- **Домены / контракт:** Exploration backend API; Actor owner. Caller mode identity/user or internal service задаёт actor rights.
- **Trigger / impact:** Direct/alternative ingress до /exploration → Gateway доверяет char_id без actor authority.
- **Необходимая проверка:** Deny no identity/nonowner/scope; assert intended ingress. **Ограничения:** Основной proxy /api не публикует этот prefix; actual access unknown.
- **Canonical:** A07-13. **Связи:** Common missing-gate cause A07-01; route publication отличается.

### A07-14 — условный риск конфигурации

- **Источник / аудит:** [audit/07_application_security.md:298](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:298); аудит 07. **Code anchors:** [src/backend/config/settings.py:49](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/config/settings.py:49), [src/frontend/config/settings.py:30](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/config/settings.py:30), [src/backend/core/game_auth.py:58](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/core/game_auth.py:58)
- **Исходная severity:** High. **Доказательность:** Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Shared infrastructure (Pre-alpha; intended Production). **Срочность:** Немедленно проверить или ограничить доступ при публичной конфигурации с defaults; реальные keys здесь не проверены.
- **Домены / контракт:** Settings; JWT; Internal service identity. Production отвергает default/missing security keys.
- **Trigger / impact:** Misconfigured startup с known development keys → Условная trusted identity forgery.
- **Необходимая проверка:** No real credential prod-settings fail-closed fixtures. **Ограничения:** Actual keys/controls unknown; severityHigh risk сохранена.
- **Canonical:** A07-14. **Связи:** Полный дубль A08-01; canonical A07-14, static validator facts усиливают group evidence.

### A07-15 — dev exposure risk

- **Источник / аудит:** [audit/07_application_security.md:299](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:299); аудит 07. **Code anchors:** [src/backend/features/rift/api/router.py:179](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/api/router.py:179) (актуальный mount; исторический номер 195 устарел), [src/backend/config/settings.py:59](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/config/settings.py:59)
- **Исходная severity:** Medium. **Доказательность:** Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Experimental / Dev-only. **Срочность:** До следующего публичного релиза при применимости поверхности; действующая экспозиция требует отдельной проверки.
- **Домены / контракт:** Dev Rift routes; Deployment flags. Dev endpoint isolated/default-off при public deployment.
- **Trigger / impact:** ENABLE_DEV_RIFT_ROUTES true/default and published router → Условная unintended dev surface.
- **Необходимая проверка:** Prod flag/router assertion, dev access denied where disabled. **Ограничения:** Actual flag/ingress unknown; not automatically isolated.
- **Canonical:** A07-15. **Связи:** Частичный A08-04 с independent unbounded-instance effect.

### A07-16 — lifecycle/abuse risk

- **Источник / аудит:** [audit/07_application_security.md:300](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:300); аудит 07. **Code anchors:** [src/backend/realtime/api/ws.py:213](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/realtime/api/ws.py:213)
- **Исходная severity:** Medium. **Доказательность:** Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Pre-alpha. **Срочность:** До следующего публичного релиза при применимости поверхности; действующая экспозиция требует отдельной проверки.
- **Домены / контракт:** Realtime session lifetime; Limits; URL credentials. Long-lived authority revoked/expired и bounded abuse.
- **Trigger / impact:** WS after expiry/replacement; no loop recheck/application quotas → Условные stale access/DoS/token log effects.
- **Необходимая проверка:** Lifetime/revoke, quotas/frame budgets, redaction synthetic checks. **Ограничения:** Server/proxy limits unknown; handshake already guarded; no proven DoS/leak.
- **Canonical:** A07-16. **Связи:** Частичный A08-06 log channel; not same fix for WS lifetime.

### A07-17 — unsafe-render sinks

- **Источник / аудит:** [audit/07_application_security.md:301](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:301); аудит 07. **Code anchors:** [src/frontend/templates/game/domains/scenario/viewport/main.html:59](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/templates/game/domains/scenario/viewport/main.html:59), [src/frontend/templates/game/test_hex_rift.html:565](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/templates/game/test_hex_rift.html:565)
- **Исходная severity:** Observation. **Доказательность:** Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Pre-alpha / Experimental / Dev-only. **Срочность:** Отложить до утверждения применимого контракта/использования поверхности.
- **Домены / контракт:** Scenario rich text; Hex DOM; Content. Allowed rich text/sanitizer boundary defined.
- **Trigger / impact:** safe/innerHTML sinks with unestablished untrusted source → Условный executable markup exposure.
- **Необходимая проверка:** Source-to-sink fixtures, sanitizer/escaping/CSP contract. **Ограничения:** Observation, not confirmed XSS; source boundary missing.
- **Canonical:** A07-17. **Связи:** Independent assets/URL auth; Hex runtime exposure A08-04 different.

### A07-18 — повторное применение rewards

- **Источник / аудит:** [audit/07_application_security.md:302](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:302); аудит 07. **Code anchors:** [src/backend/features/rift/services/player_service.py:192](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/services/player_service.py:192), [src/backend/features/loot/workers/tasks/loot_claim_task.py:203](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/loot/workers/tasks/loot_claim_task.py:203), [src/backend/features/rift/services/player_service.py:114](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/services/player_service.py:114)
- **Исходная severity:** Medium. **Доказательность:** Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Pre-alpha / Legacy. **Срочность:** Не исправлять без архитектурного решения о поддержке/выводе Legacy; при текущей публикации сначала проверить экспозицию.
- **Домены / контракт:** Rift rewards; Loot entitlement; Retry. Repeated delivery не повторяет authoritative rewards.
- **Trigger / impact:** Complete XP before cleanup; conditional claim dedup → Предполагаемый duplicate reward under concurrency/fault.
- **Необходимая проверка:** Controlled interleaving, authoritative idempotency/conservation. **Ограничения:** Real delivery/actual effect not measured; не new confirmed exploit.
- **Canonical:** A07-18. **Связи:** Частичные A04-16,A03-01/11,A05-01/02; broad multiple paths не общий canonical.

## Аудит 08

### A08-01 — Production принимает известные ключи по умолчанию

- **Источник / аудит:** [audit/08_infrastructure_security.md:237](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:237); аудит 08. **Code anchors:** [src/backend/config/settings.py:49](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/config/settings.py:49), [src/frontend/config/settings.py:30](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/config/settings.py:30), [deploy/compose.site.yml:39](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/compose.site.yml:39)
- **Исходная severity:** High. **Доказательность:** Исторически воспроизведено локальной проверкой/тестом исходного аудита; сейчас не повторялось. **Стадия:** Shared infrastructure (intended Production; consumers Pre-alpha). **Срочность:** Немедленно проверить или ограничить доступ при публичной конфигурации с defaults; реальные keys здесь не проверены.
- **Домены / контракт:** Production settings; JWT; Internal auth; Compose. Prod startup отвергает missing/default signing/internal keys.
- **Trigger / impact:** Incomplete env/placeholders проходят debug=False validation → Условная impersonation/admin trusted operations.
- **Необходимая проверка:** Prod no/default keys reject, distinct keys accept, no secret validation output. **Ограничения:** Историческая settings probe; actual keys/ingress неизвестны; не production exploit.
- **Canonical:** A07-14. **Связи:** Полный дубль A07-14; canonical A07-14; cookie/dev-off дополнительные условия не поглощают A07-15.

### A08-02 — Общие secrets и сеть расширяют последствия компрометации

- **Источник / аудит:** [audit/08_infrastructure_security.md:249](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:249); аудит 08. **Code anchors:** [deploy/compose.site.yml:39](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/compose.site.yml:39), [deploy/compose.game.yml:43](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/compose.game.yml:43), [deploy/compose.tg-bot.yml:8](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/compose.tg-bot.yml:8)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (intended Production). **Срочность:** До следующего публичного релиза при применимости поверхности; действующая экспозиция требует отдельной проверки.
- **Домены / контракт:** Runtime services; SQL; Redis; Mongo; S3. Service credentials/network scopes минимальны.
- **Trigger / impact:** Уже скомпрометирован один process/env → Neighbour stores/provider credentials и общий blast radius.
- **Необходимая проверка:** Service env inventory, least-privilege denied operations, allowed workflow. **Ограничения:** Initial RCE/host escape не доказаны; actual grants unknown.
- **Canonical:** A08-02. **Связи:** Зависимость ущерба A08-12 secret-file exposure; independent failure root.

### A08-03 — Внутренние session API доступны через публичный proxy

- **Источник / аудит:** [audit/08_infrastructure_security.md:259](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:259); аудит 08. **Code anchors:** [deploy/nginx/site.conf.template:120](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/nginx/site.conf.template:120), [src/backend/app.py:43](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/app.py:43), [src/backend/features/scenario/api/internal_router.py:7](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/scenario/api/internal_router.py:7)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (intended Production). **Срочность:** До следующего публичного релиза при применимости поверхности; действующая экспозиция требует отдельной проверки.
- **Домены / контракт:** Nginx; Internal session API; Redis scan. Public edge и direct API не раскрывают internal diagnostics.
- **Trigger / impact:** Deployed repo proxy + runtime sessions → Session metadata disclosure и unbounded scan load.
- **Необходимая проверка:** Anonymous edge/direct deny; scoped caller + bounded pagination. **Ограничения:** Running configuration unknown; no DB credential/owner mutation proof.
- **Canonical:** A08-03. **Связи:** Частичный A07-04; analytics/backfill там, edge/scan тут.

### A08-04 — Experimental генератор открыт и не ограничивает накопление инстансов

- **Источник / аудит:** [audit/08_infrastructure_security.md:269](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:269); аудит 08. **Code anchors:** [src/backend/config/settings.py:59](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/config/settings.py:59), [src/backend/features/rift/api/router.py:179](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/api/router.py:179), [src/backend/app.py:68](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/app.py:68)
- **Исходная severity:** High. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Experimental / Dev-only. **Срочность:** До следующего публичного релиза при применимости поверхности; действующая экспозиция требует отдельной проверки.
- **Домены / контракт:** Hex dev API; Runtime memory; Redis; Nginx. Dev generation isolated/bounded; unknown ID не unbounded allocation.
- **Trigger / impact:** Dev flag enabled + repeated new instance IDs → Process dict grows; sync CPU/Redis work availability impact.
- **Необходимая проверка:** Prod absent route, bounded counts/eviction, unknown-ID small fixtures. **Ограничения:** Release of dirty files unknown; Redis TTL не expires process dict; no load attack.
- **Canonical:** A08-04. **Связи:** Частичные A07-15,A04-20; independent resource retention.

### A08-05 — Публичные metrics сохраняют исходные URL, включая bearer identifiers

- **Источник / аудит:** [audit/08_infrastructure_security.md:279](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:279); аудит 08. **Code anchors:** [src/shared/infrastructure/metrics_middleware.py:23](D:/Workspace/personal/pets/TurnBasedMMORPG/src/shared/infrastructure/metrics_middleware.py:23), [src/shared/infrastructure/metrics.py:9](D:/Workspace/personal/pets/TurnBasedMMORPG/src/shared/infrastructure/metrics.py:9), [src/shared/infrastructure/metrics_endpoint.py:12](D:/Workspace/personal/pets/TurnBasedMMORPG/src/shared/infrastructure/metrics_endpoint.py:12)
- **Исходная severity:** Medium. **Доказательность:** Исторически воспроизведено локальной проверкой/тестом исходного аудита; сейчас не повторялось. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Shared infrastructure (intended Production). **Срочность:** До следующего публичного релиза при применимости поверхности; действующая экспозиция требует отдельной проверки.
- **Домены / контракт:** Prometheus middleware/endpoint; Frontend URLs. Telemetry labels не user tokens/IDs; exposure scoped.
- **Trigger / impact:** Visited bearer URL saved raw path before routing → Metric token/identifier disclosure + cardinality growth.
- **Необходимая проверка:** Synthetic token absent, external metrics denied, unknown-path labels bounded. **Ограничения:** Историческая inert AST probe; full HTTP incomplete; feature/login constraints.
- **Canonical:** A08-05. **Связи:** Independent log channels A08-06/07; common redaction policy только parent theme.

### A08-06 — Nginx access log содержит URL-токены

- **Источник / аудит:** [audit/08_infrastructure_security.md:291](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:291); аудит 08. **Code anchors:** [deploy/nginx/nginx.conf:20](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/nginx/nginx.conf:20), [src/frontend/features/surveys/routes/pages.py:16](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/features/surveys/routes/pages.py:16), [src/frontend/features/account/routes/email_verify.py:87](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/features/account/routes/email_verify.py:87)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (intended Production). **Срочность:** До следующего публичного релиза при применимости поверхности; действующая экспозиция требует отдельной проверки.
- **Домены / контракт:** Nginx access logs; Survey/email/WS URLs. Logs не хранят bearer URL secrets.
- **Trigger / impact:** Token URL used; log audience reads before expiry/consume → Credential capability replay via log-reader.
- **Необходимая проверка:** Synthetic token absent from Nginx/app/collector; retain request context. **Ограничения:** Email login/password/TTL ограничивают impact; query WS fallback диагностический.
- **Canonical:** A08-06. **Связи:** Частичный A07-16 query logging; separate from metrics A08-05.

### A08-07 — Production exception logging раскрывает locals; явно логируется PII

- **Источник / аудит:** [audit/08_infrastructure_security.md:301](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:301); аудит 08. **Code anchors:** [src/shared/infrastructure/logging_config.py:42](D:/Workspace/personal/pets/TurnBasedMMORPG/src/shared/infrastructure/logging_config.py:42), [.venv/Lib/site-packages/codex_core/common/loguru_setup.py:287](D:/Workspace/personal/pets/TurnBasedMMORPG/.venv/Lib/site-packages/codex_core/common/loguru_setup.py:287), [.venv/Lib/site-packages/loguru/_defaults.py:43](D:/Workspace/personal/pets/TurnBasedMMORPG/.venv/Lib/site-packages/loguru/_defaults.py:43)
- **Исходная severity:** Medium. **Доказательность:** Исторически воспроизведено локальной проверкой/тестом исходного аудита; сейчас не повторялось. **Стадия:** Shared infrastructure (intended Production). **Срочность:** До следующего публичного релиза при применимости поверхности; действующая экспозиция требует отдельной проверки.
- **Домены / контракт:** Logging wrapper; codex-core/Loguru; Email PII. Prod exception diagnostics не locals/credentials/PII.
- **Trigger / impact:** Sensitive locals при exception + logs reader → Runtime secrets/recipient data diagnostic retention.
- **Необходимая проверка:** Canary/SMTP exception stdout+collector no token/body/email, trace retained. **Ограничения:** Историческая synthetic canary/local pinned library; image bytes/logs unknown.
- **Canonical:** A08-07. **Связи:** Independent A08-05/06 channels; library correction canonical source outside task.

### A08-08 — Local/observability Compose публикует чувствительные сервисы на всех interfaces

- **Источник / аудит:** [audit/08_infrastructure_security.md:311](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:311); аудит 08. **Code anchors:** [deploy/docker-compose.yml:9](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/docker-compose.yml:9), [deploy/docker-compose.db.yml:7](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/docker-compose.db.yml:7), [deploy/docker-compose.observability.yml:7](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/docker-compose.observability.yml:7)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Dev-only / optional overlay. **Срочность:** До следующего публичного релиза при применимости поверхности; действующая экспозиция требует отдельной проверки.
- **Домены / контракт:** Local Compose; Studio; DB; Mailpit; Dashboards. Dev data/admin bind isolated and gated if external.
- **Trigger / impact:** Local stack on network-reachable host/firewall → Neighbour network dev data/admin disclosure.
- **Необходимая проверка:** Resolved port binds loopback; external mode requires credentials/access. **Ограничения:** Не production overlay; actual firewall/tunnel/initial-volume state unknown.
- **Canonical:** A08-08. **Связи:** Частичный A07-12 Studio access; source readonly separate.

### A08-09 — Mutable Actions/images не фиксируют цепочку происхождения

- **Источник / аудит:** [audit/08_infrastructure_security.md:321](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:321); аудит 08. **Code anchors:** [.github/workflows/deploy-production.yml:34](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/deploy-production.yml:34), [.github/workflows/build-images.yml:21](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/build-images.yml:21), [deploy/compose.infra.yml:5](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/compose.infra.yml:5)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (intended Production / CI). **Срочность:** До следующего публичного релиза при применимости поверхности; действующая экспозиция требует отдельной проверки.
- **Домены / контракт:** Actions; Base/runtime images; GHCR; Provenance. Privileged executable/artifact refs immutable and verifiable.
- **Trigger / impact:** Upstream/tag compromise or unnoticed mutable change → Job secrets/artifact substitution within privileges.
- **Необходимая проверка:** Pinned privileged Actions, digest manifest/source/gate binding; mismatch deny. **Ограничения:** Compromise не обнаружен; fork PR не privileged; setup-uv SHA исключение.
- **Canonical:** A08-09. **Связи:** Частичные A06-09,A08-11 promotion; mutable supply chain root отдельный.

### A08-10 — CI зависит от отсутствующего local source, Docker меняет source policy

- **Источник / аудит:** [audit/08_infrastructure_security.md:331](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:331); аудит 08. **Code anchors:** [pyproject.toml:28](D:/Workspace/personal/pets/TurnBasedMMORPG/pyproject.toml:28), [uv.lock:470](D:/Workspace/personal/pets/TurnBasedMMORPG/uv.lock:470), [.github/workflows/ci.yml:24](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/ci.yml:24)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha; intended Production build). **Срочность:** До следующего публичного релиза при применимости поверхности; действующая экспозиция требует отдельной проверки.
- **Домены / контракт:** uv source; CI; Python Docker build. CI/image получают один approved immutable source.
- **Trigger / impact:** Clean checkout missing sibling; Docker --no-sources → Install/release blocked либо undocumented artifact resolution.
- **Необходимая проверка:** Clean locked install, export source identity, image wheel/hash provenance. **Ограничения:** Actual registry substitution/confusion не доказаны; offline export incomplete.
- **Canonical:** A08-10. **Связи:** Частичный A06-05; Docker artifact identity scope не потерян.

### A08-11 — Production dispatch не привязан к отдельному approval/ref/provenance gate

- **Источник / аудит:** [audit/08_infrastructure_security.md:351](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:351); аудит 08. **Code anchors:** [.github/workflows/deploy-production.yml:3](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/deploy-production.yml:3), [.github/workflows/build-images.yml:7](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/build-images.yml:7)
- **Исходная severity:** Medium. **Доказательность:** Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Shared infrastructure (intended Production). **Срочность:** До следующего публичного релиза при применимости поверхности; действующая экспозиция требует отдельной проверки.
- **Домены / контракт:** Production dispatch; GitHub governance. Privileged promotion/ref/review/serialization enforceable.
- **Trigger / impact:** Authorized dispatch without external protections or overlapping runs → Unreviewed/incompatible artifact or interleaved deployment.
- **Необходимая проверка:** Read real protections; deny untrusted ref/artifact; two runs serialized. **Ограничения:** Actor уже deployment-authorized; YAML absence не actual bypass.
- **Canonical:** A08-11. **Связи:** Частичный A06-09 provenance; governance/concurrency independent.

### A08-12 — Права production .env не закреплены при записи

- **Источник / аудит:** [audit/08_infrastructure_security.md:361](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:361); аудит 08. **Code anchors:** [.github/workflows/deploy-production.yml:72](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/deploy-production.yml:72)
- **Исходная severity:** Medium. **Доказательность:** Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Shared infrastructure (intended Production). **Срочность:** До следующего публичного релиза при применимости поверхности; действующая экспозиция требует отдельной проверки.
- **Домены / контракт:** SSH deploy; Host filesystem; Env-file permissions. Secret env private across create/replace.
- **Trigger / impact:** Permissive umask/ACL + other host principal → Credential file exposed; blast radius.
- **Необходимая проверка:** Create/replace under permissive umask, stat/ACL/denied-read без content. **Ограничения:** Actual mode/umask unknown; 0644 на VPS не утверждается.
- **Canonical:** A08-12. **Связи:** Зависимость impact A08-02; самостоятельный filesystem boundary.

### A08-13 — Нет дополнительных ограничений post-compromise ресурсов и файловой системы

- **Источник / аудит:** [audit/08_infrastructure_security.md:341](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:341); аудит 08. **Code anchors:** [deploy/compose.infra.yml:4](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/compose.infra.yml:4), [deploy/compose.site.yml:35](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/compose.site.yml:35), [deploy/compose.game.yml:39](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/compose.game.yml:39)
- **Исходная severity:** Low. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (intended Production). **Срочность:** При стабилизации домена.
- **Домены / контракт:** Production containers; Host resources/filesystem. Post-compromise workload/write/capability budget bounded.
- **Trigger / impact:** RCE/workload exhaustion with writable app/no declared extra limits → Easier resource abuse; additional writable paths.
- **Необходимая проверка:** Startup/assets/migrations under limits, denied write/capability, bounded fixture. **Ограничения:** Low hardening; non-root/no socket/privileged компенсируют; daemon policy unknown.
- **Canonical:** A08-13. **Связи:** Частичное capacity A09-10; no proved escape/DoS.

### A08-14 — Недоверенные forwarded headers могут давать HTTP-ссылки с токеном

- **Источник / аудит:** [audit/08_infrastructure_security.md:369](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:369); аудит 08. **Code anchors:** [deploy/nginx/site.conf.template:179](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/nginx/site.conf.template:179), [deploy/compose.site.yml:55](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/compose.site.yml:55), [.venv/Lib/site-packages/uvicorn/config.py:340](D:/Workspace/personal/pets/TurnBasedMMORPG/.venv/Lib/site-packages/uvicorn/config.py:340)
- **Исходная severity:** Medium. **Доказательность:** Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Shared infrastructure (intended Production; feature-dependent). **Срочность:** До следующего публичного релиза при применимости поверхности; действующая экспозиция требует отдельной проверки.
- **Домены / контракт:** Proxy trust; Email canonical origin; Uvicorn. Security link HTTPS canonical origin with bounded proxy trust.
- **Trigger / impact:** Email feature on; bridge proxy untrusted + no browser upgrade → HTTP bearer link may disclose before redirect.
- **Необходимая проверка:** Through-proxy synthetic HTTPS links; forged forwarded headers cannot alter trust. **Ограничения:** Feature off example; HSTS/overrides may protect; no real HTTP leak.
- **Canonical:** A08-14. **Связи:** Independent token logs A08-06; generation/origin cause иной.

### A08-15 — Recovery и security monitoring не доказаны operational evidence

- **Источник / аудит:** [audit/08_infrastructure_security.md:377](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:377); аудит 08. **Code anchors:** [docs/ru/management/deployment.md:179](D:/Workspace/personal/pets/TurnBasedMMORPG/docs/ru/management/deployment.md:179), [.github/workflows/deploy-production.yml:104](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/deploy-production.yml:104), [src/backend/app.py:97](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/app.py:97)
- **Исходная severity:** Observation. **Доказательность:** Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Shared infrastructure (intended Production). **Срочность:** При стабилизации домена.
- **Домены / контракт:** Backups; Recovery; Readiness; TLS; Alerts. Operational claims backed restore/alert/TLS evidence.
- **Trigger / impact:** Volume loss, failed migration, worker/cert/security failure → Unknown completeness/time/detection/incident response.
- **Необходимая проверка:** Gather schedules/roles/retention, isolated restore/drill/alert/readiness/TLS proof. **Ограничения:** Observation: external ops may exist; repo absence не server absence.
- **Canonical:** A08-15. **Связи:** Зависимость migration A05-13; related unnumbered recovery constraints.

## Аудит 09

### A09-01 — история боя повторно читается и записывается целиком

- **Источник / аудит:** [audit/09_performance_scalability.md:64](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/09_performance_scalability.md:64); аудит 09. **Code anchors:** [src/backend/infrastructure/combat/managers/session.py:606](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/combat/managers/session.py:606)
- **Исходная severity:** High. **Доказательность:** Исторически воспроизведено локальной проверкой/тестом исходного аудита; сейчас не повторялось. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Combat logs; Redis; Serialization. Commit cost не повторяет всю immutable history.
- **Trigger / impact:** Each batch read/merge/re-encode/write all turns → O(T²) total bytes/temporary objects.
- **Необходимая проверка:** Bytes/commit vs history, order/retry semantic invariants, real latency. **Ограничения:** Исторические fake-Redis method probes; ms не e2e/p95/SLA.
- **Canonical:** A09-01. **Связи:** Same implementation A03-03, independent performance/atomicity causes.

### A09-02 — частый глобальный AC scan и неполная fairness

- **Источник / аудит:** [audit/09_performance_scalability.md:72](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/09_performance_scalability.md:72); аудит 09. **Code anchors:** [src/backend/infrastructure/actor_state/managers/session.py:520](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/actor_state/managers/session.py:520)
- **Исходная severity:** High. **Доказательность:** Исторически воспроизведено локальной проверкой/тестом исходного аудита; сейчас не повторялось. **Стадия:** Shared infrastructure (Pre-alpha). **Срочность:** При стабилизации домена.
- **Домены / контракт:** AC vitals scanner; Redis; System cron. Scan budget/fairness bounded vs candidates.
- **Trigger / impact:** Every2s scan from0, serial full GET; no candidates/first100 → O(P) read and possible stable-order starvation.
- **Необходимая проверка:** Examined/selected commands, rotating fairness, realistic AC/Redis profile. **Ограничения:** Исторический fake order; real SCAN count hint, no guaranteed starvation.
- **Canonical:** A09-02. **Связи:** Related gameplay/storage mixing A02-06; independent scanner performance.

### A09-03 — архивирование чата имеет низкий фиксированный потолок

- **Источник / аудит:** [audit/09_performance_scalability.md:80](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/09_performance_scalability.md:80); аудит 09. **Code anchors:** [src/backend/chat/workers/archive.py:35](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/chat/workers/archive.py:35), [src/backend/chat/services/message_service.py:45](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/chat/services/message_service.py:45), [src/backend/config/settings.py:85](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/config/settings.py:85)
- **Исходная severity:** High. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Chat archive; Redis buffers; Mongo; SQL. Service drain budget keeps accepted backlog within retention.
- **Trigger / impact:** Arrival>500/topic/10min without drain loop → Nominal3000/hour cap; backlog→trim risk.
- **Необходимая проверка:** Arrival/drain/oldest age/retention isolated load, recovery preserved. **Ограничения:** Arithmetic cap не measured database throughput/incident.
- **Canonical:** A09-03. **Связи:** Independent consistency cursor A05-06 and Mongo bytes A09-08.

### A09-04 — процессный предел и задержка за медленным получателем WebSocket

- **Источник / аудит:** [audit/09_performance_scalability.md:88](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/09_performance_scalability.md:88); аудит 09. **Code anchors:** [src/backend/chat/services/connection_manager.py:19](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/chat/services/connection_manager.py:19), [src/backend/chat/services/message_service.py:39](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/chat/services/message_service.py:39), [deploy/compose.game.yml:81](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/compose.game.yml:81)
- **Исходная severity:** High. **Доказательность:** Исторически воспроизведено локальной проверкой/тестом исходного аудита; сейчас не повторялось. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Chat WebSocket; Connection manager; Realtime. Recipient backpressure isolated; replicas share live delivery.
- **Trigger / impact:** Slow first socket; additional chat process → Delayed broadcast/XADD; room split across processes.
- **Необходимая проверка:** Bounded slow-consumer queue/drop, two-process room delivery, memory/connection. **Ограничения:** Исторический fake socket order; not whole event-loop blockage; current1process not broken by replication hypothesis.
- **Canonical:** A09-04. **Связи:** Independent membership/auth A07-07/08.

### A09-05 — combat повторно загружает весь бой для каждого AI и сохраняет всех actors

- **Источник / аудит:** [audit/09_performance_scalability.md:96](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/09_performance_scalability.md:96); аудит 09. **Code anchors:** [src/backend/features/combat/integrations/session_integration.py:339](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/integrations/session_integration.py:339), [src/backend/infrastructure/combat/managers/session.py:551](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/combat/managers/session.py:551), [src/backend/features/combat/workers/tasks/ai_turn_task.py:51](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/workers/tasks/ai_turn_task.py:51)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Combat; AI workers; Actor snapshots; Redis. Batch costs tied relevant actors/version rather than B full snapshots.
- **Trigger / impact:** B AI jobs each hydrate N; commit all actors → O(BN) payload/validation, full actor writes/TTL.
- **Необходимая проверка:** Representative B/N effects, touched writes/bytes, snapshot parity. **Ограничения:** Pipeline RT≠commands; collector queue threshold bounds Q.
- **Canonical:** A09-05. **Связи:** Related A09-01 history but actor load independent; A03-09 versions prerequisite.

### A09-06 — дубли sync превращаются в повторные полные SQL writes

- **Источник / аудит:** [audit/09_performance_scalability.md:104](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/09_performance_scalability.md:104); аудит 09. **Code anchors:** [src/backend/core/middleware.py:30](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/core/middleware.py:30), [.venv/Lib/site-packages/arq/connections.py:148](D:/Workspace/personal/pets/TurnBasedMMORPG/.venv/Lib/site-packages/arq/connections.py:148), [src/backend/features/character/integrations/system_integrator.py:117](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/character/integrations/system_integrator.py:117)
- **Исходная severity:** Medium. **Доказательность:** Исторически воспроизведено локальной проверкой/тестом исходного аудита; сейчас не повторялось. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Character sync; Middleware; SQL; ARQ. Clean duplicate sync не full durable rewrite.
- **Trigger / impact:** Several enqueue before clear; later no dirty targets → Repeated full repository writes.
- **Необходимая проверка:** Dirty-generation enqueue/write counts, clean repeat no effect, unsafe expedition exception. **Ограничения:** Исторический mocked-repo source probe; SQL statement counts не measured.
- **Canonical:** A09-06. **Связи:** Independent CAS correctness A03-10.

### A09-07 — Rift tick переписывает instance, flush обходит чужие sessions

- **Источник / аудит:** [audit/09_performance_scalability.md:112](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/09_performance_scalability.md:112); аудит 09. **Code anchors:** [src/backend/features/rift/services/player_service.py:218](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/services/player_service.py:218), [src/backend/infrastructure/rift/managers/instance.py:25](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/rift/managers/instance.py:25), [src/backend/features/rift/integrations/runtime.py:287](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/integrations/runtime.py:287)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Legacy (поддержка runtime неизвестна). **Срочность:** Не исправлять без архитектурного решения о поддержке/выводе Legacy; при текущей публикации сначала проверить экспозицию.
- **Домены / контракт:** Old Rift tick/checkpoint; Redis scan. Personal tick/checkpoint budget bounded by owner/instance.
- **Trigger / impact:** Full instance/session SET/expire; list_by_instance scans all S → 4 sequential RT basic writes; O(S) flush, redundant common snapshot.
- **Необходимая проверка:** Tick bytes/RT, examined keys, same-instance coalescing preserving consistency. **Ограничения:** Small presets; no High without profile; graph copy per participant не доказана.
- **Canonical:** A09-07. **Связи:** Independent dirty correctness A04-17/A05-09.

### A09-08 — Mongo chat возвращает растущий bucket после каждой записи

- **Источник / аудит:** [audit/09_performance_scalability.md:120](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/09_performance_scalability.md:120); аудит 09. **Code anchors:** [src/backend/infrastructure/mongo/chat_buckets.py:59](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/mongo/chat_buckets.py:59)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Chat Mongo buckets; SQL references. Append response ограничен необходимым count/meta.
- **Trigger / impact:** ReturnDocument.AFTER no projection for growing bucket → O(n²×M) returned bytes; shard/history amplification.
- **Необходимая проверка:** Append/returned bytes, projection contract, bucket/history boundaries. **Ограничения:** Nominal1000 bounded; no full SQL N+1/message claim; BSON overflow unknown.
- **Canonical:** A09-08. **Связи:** Same repository A05-15 seq/concurrency, different causes/results.

### A09-09 — GenerationAI удерживает SQL connection/transaction через долгую внешнюю работу

- **Источник / аудит:** [audit/09_performance_scalability.md:126](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/09_performance_scalability.md:126); аудит 09. **Code anchors:** [src/backend/features/generation_ai/repositories.py:132](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/repositories.py:132), [src/backend/features/generation_ai/workers/tasks.py:20](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/workers/tasks.py:20)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Shared infrastructure (Pre-alpha). **Срочность:** При стабилизации домена.
- **Домены / контракт:** GenerationAI SQL claim; Provider; Asset/Mongo. Connection/transaction lifetime limited separately external work.
- **Trigger / impact:** Claim FOR UPDATE held through provider/apply to final commit → Up to5 long transactions/worker; possible pool/lock pressure.
- **Необходимая проверка:** Provider/storage timing vs transaction age/pool wait; fault claim/retry contract. **Ограничения:** Lock impact not profiled; SKIP LOCKED already prevents waiting on task claim.
- **Canonical:** A09-09. **Связи:** Independent enqueue gap A05-08; transaction restructuring would require own verification.

### A09-10 — image normalization синхронно занимает GenerationAI event loop

- **Источник / аудит:** [audit/09_performance_scalability.md:132](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/09_performance_scalability.md:132); аудит 09. **Code anchors:** [src/backend/features/generation_ai/integrations/codex_ai_executor.py:90](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/integrations/codex_ai_executor.py:90), [src/backend/features/generation_ai/image_normalization.py:42](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/image_normalization.py:42)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha). **Срочность:** При стабилизации домена.
- **Домены / контракт:** GenerationAI event loop; Image normalization. Sync image work/memory respects event-loop/job budget.
- **Trigger / impact:** Async executor calls PIL load/resize/WEBP method6 → CPU blocks worker coroutines; pixel-buffer peak.
- **Необходимая проверка:** Representative dimensions/images timing/RSS/loop lag, fast WEBP path parity. **Ограничения:** Fast no-resize WEBP returns early; synthetic timings not production distribution.
- **Canonical:** A09-10. **Связи:** Related resource budget A08-13; independent transaction A09-09.

### A09-11 — browser chat не ограничивает историю живой вкладки

- **Источник / аудит:** [audit/09_performance_scalability.md:138](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/09_performance_scalability.md:138); аудит 09. **Code anchors:** [src/frontend/templates/shared/chat/main.html:6](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/templates/shared/chat/main.html:6)
- **Исходная severity:** Medium. **Доказательность:** Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha. **Срочность:** При стабилизации домена.
- **Домены / контракт:** Frontend browser chat; Alpine lists. Live history/DOM memory bounded over tab lifetime.
- **Trigger / impact:** Messages accumulate arrays; full x-for renders active list → JS memory/DOM grow with live count.
- **Необходимая проверка:** Long-session heap/DOM and bounded tail/history navigation. **Ограничения:** No browser heap/Core Web Vitals measured; backend page cap not live cap.
- **Canonical:** A09-11. **Связи:** Independent server fanout A09-04/archive A09-03.

## Навигационная верификация и предел актуальности

Автоматически проверено 286 нормализованных code file:line anchors: файл существует, номер строки в диапазоне. Исходные audit anchors сверены с фактическим ID. Это навигация, не доказательство неизменности каждого пути; невыбранные участки сохраняют историческое evidence и требуют повторной проверки перед реализацией.

Недоступные исторические anchors не превращены в рабочие ссылки:

- A07-15: src/backend/features/rift/api/router.py:195 вне текущего диапазона 190.

Неоднозначные короткие ссылки не угадывались. Отсутствующий script A06-01 и старый resolver.py A02-10 — предмет находок, не рабочие ссылки. Локальные library anchors не доказывают identity production images.

## Ненумерованные наблюдения, риски и частичные контракты

Эти группы сохранены без новых A/O IDs и без придуманной исходной severity. Они не прибавляются к 120 ID или 116 canonical. Таблица передаёт все существенные ненумерованные ограничения/наблюдения из narrative-разделов, а не повторяет сильные решения или каждую методологическую оговорку. Статические предпосылки и гипотезы разделены; будущие проверки здесь не выполнены.

| Источник | Наблюдение / стадия и доказательность | Контракт, trigger/impact и необходимая проверка | Ограничения / связи |
| --- | --- | --- | --- |
| [02_architecture_boundaries.md:176](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:176) | ScenarioSystemIntegrator cohesion и размеры других services. Observation; Pre-alpha/Legacy | Много методов/fan-out не доказывает God Object; самостоятельные причины изменения не установлены. Проверять при изменении владельца use case; не дробить только по LOC. | A02-09 касается только simulation; не общий canonical. |
| [02_architecture_boundaries.md:88](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:88) | Bootstrap population-rule mapping. Observation; Shared infrastructure | Правило в composition root — будущий перенос при росте, не подтверждённый runtime defect. Проверить owner bootstrap contract и inputs, прежде чем переносить. | Самостоятельная навигационная/ownership заметка, ID не присвоен. |
| [02_architecture_boundaries.md:196](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:196) | Combat shared DTO не готовый native ABI. Observation; Experimental extraction | Pydantic fields не автоматически переносимый ABI. Нужен explicit snapshot/RNG/rules/tunables corpus, если extraction будет утверждена. | Частичное O02-03; не новая обязательная реализация. |
| [03_combat_runtime.md:151](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:151) | resistance_cap pending. Observation; Pre-alpha | Поле присутствует, текущий math не использует; reference отмечает pending. При активации проверить resistance 0/0.85/1/>1 по каналам; без утверждённого правила не gameplay defect. | Не присвоено новое finding ID; текущий balance не сертифицирован. |
| [03_combat_runtime.md:153](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:153) | Seed isolation и replay journal. Observation/неполный contract; Pre-alpha/Experimental | State.seed не отдельный RNG; global random.seed влияет между tasks; UUID/rule/target order важны replay. Проверить same seed после чужих random calls и parallel runs с normalized outcomes. | Related O02-03/A04-07, но set ordering и global RNG не одна причина. |
| [03_combat_runtime.md:171](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:171) | Stats serialized вопреки in-memory-only reference. Статический drift; Shared infrastructure | Derived stats пишутся в Redis; guidance отстаёт. Сверить реальные snapshot поля и owner decision, не удалить serialization по старой инструкции. | Уточнение A02-10, не отдельный gameplay defect. |
| [03_combat_runtime.md:175](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:175) | Custom TTL refresh и cleanup caller. Ограничение/риск; Pre-alpha | Custom create TTL не индивидуальная refresh policy; complete_session caller в live scan не найден, TTL основной cleanup. Проверить intended policy, exact TTL/recovery; search не исключает external caller. | Частичный A03-12 retention; не полный дубль всего archive риска. |
| [03_combat_runtime.md:209](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:209) | Live AI policy DB failure до fallback. Статический failure-path limitation; Pre-alpha | SQL lookup error до bundled fallback может сорвать ход; invalid-row errors обрабатываются. Проверить DB failure + policy_id и approved failure/fallback outcome. | Отдельно от simulation-run mark_failed A03-08. |
| [03_combat_runtime.md:236](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:236) | Arena rating caller отсутствует. Observation; Pre-alpha | apply_match_result definition найдена, production caller не найден; rating_delta placeholder. Перед PvP rating нужна end-to-end запись/повтор; внешние callers неизвестны. | Не доказан defect утверждённого текущего рейтинга. |
| [04_rift_world_generation.md:28](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:28) | World сезонная генерация, внешние регионы и Exploration stubs. Неподключённый/частичный contract; Pre-alpha | Runtime не подключает внешний/сезонный генератор; часть discovery branches stubs; география fixed. Проверить feature/product scope при подключении, не выдавать absent future feature за broken gameplay. | External gen_game_map не исследовался; A04-19 остаётся отдельной road записью. |
| [04_rift_world_generation.md:300](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:300) | Раздельная потеря Rift instance/session, versions и disconnect. Историческое ограничение восстановления; Legacy | Disconnect/restart/разная версия Redis/Mongo/partial writes не воспроизведены. Проверить component expiry/version selection и recovery после каждого шага. | Partial restore подробно подтверждён в A05-10; не новый номер. |
| [04_rift_world_generation.md:340](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:340) | AI images/publication и orphan artifacts. Observation/условный риск; Shared infrastructure | Проверка текста image — metadata, не publication gate; atomic world publication не установлена. Проверить approved asset/content policy, orphan cleanup и staged publication без предположения об утрате applied content. | Частичный A04-18; generation не текущий combat graph calculator. |
| [05_persistence_consistency.md:113](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:113) | Redis durability/eviction, Mongo concerns и backup RPO. Неустановленные operational условия; Shared infrastructure | Volume не гарантирует acknowledged-write recovery; AOF/RDB/eviction/Mongo concerns/topology/backup неизвестны. Нужны approved isolated restart/restore/config evidence, без production чтения в этой задаче. | Related A08-15; отсутствие repo setting не доказательство отключённой durability. |
| [05_persistence_consistency.md:203](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:203) | Game live-ORM baseline evolution/rolling compatibility. Риск; Shared infrastructure | create_all baseline не ALTER ранее stamped схемы; deployed mismatch не установлен. Проверить previous-schema upgrade/downgrade/old worker compatibility без destructive автоматического rollback. | A05-13 конкретный site clean-install blocker; game не поглощён им. |
| [05_persistence_consistency.md:372](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:372) | Scenario resume, Character hard-crash compensation/death-respawn, orphan bytes. Риски без ID; Pre-alpha / Legacy | Полнота transient resume, hard crash до except cleanup, cross-store death/respawn и bytes до rollback не подтверждены. Нужны owner-specific fault/restart/barrier сценарии; не объявлять corruption по возможности. | Related A05-04/A04-18, broad multi-owner risk не full duplicate. |
| [05_persistence_consistency.md:146](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:146) | Inventory cache deletion пересекается с dirty action. Непроверенный interleaving; Pre-alpha | Loot invalidation может удалить несохранённый inventory snapshot. Проверить mutation→claim/invalidate barrier и восстановленный SQL/AC; эффект не воспроизведён. | Partial A05-03; action/action и action/flush не этот invalidation path. |
| [05_persistence_consistency.md:447](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:447) | Arena result replay protection без reachable caller. Ограничение; Pre-alpha | Write API имеет признаки отсутствия ledger, но runtime application caller не установлен. Сначала установить intended/reachable rating flow, потом repeat-result test. | Связь с unnumbered A03 rating observation; severity не присвоена. |
| [06_testing_quality.md:501](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/06_testing_quality.md:501) | Singleton app/state order dependence. Гипотеза; Shared infrastructure | Fixture меняет singleton без полного restore. Нужен bounded reverse/random-order API run; конкретного contamination failure нет. | Не доказан pytest teardown bug. |
| [06_testing_quality.md:501](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/06_testing_quality.md:501) | Real race/atomicity, hosted CI/required checks и production shutdown. Ограничения доказательств; Shared infrastructure | Нет live concurrency, GitHub settings/runs или lifespan shutdown certification. Проверять relevant isolated storage/restart и authorized external governance evidence отдельно. | A06-03/04 — недостаток защиты, не измерение всех race effects. |
| [06_testing_quality.md:501](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/06_testing_quality.md:501) | Alternative runner source/ignore-list security drift. Гипотеза + статические policy факты; Shared infrastructure | Hardcoded sibling path при наличии может заменить installed runner; локально выбран installed. Ignore lists различаются, advisories не проверялись. Проверить actual import origin/approved dependency policy. | A06-12 hook scope отдельный; не актуальная CVE аттестация. |
| [06_testing_quality.md:501](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/06_testing_quality.md:501) | FakeRedis dict aliasing, performance/flakiness budget. Гипотеза/ограничение; Shared infrastructure | Double не копирует dict; отдельный vacuous persistence pass не воспроизведён. Проверить wire/alias semantics; 55s hex run timeout не объявлять hang, нужны timing/seed/RSS profile. | A06-02 — другой доказанный mock-precondition defect. |
| [07_application_security.md:74](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:74) | Email verification/password reset/moderator policy неполны. Неутверждённый/частичный продуктовый contract; Pre-alpha | Завершённый verify/reset и отдельная moderator policy не установлены в исследованных APIs. Уточнить promised flow/roles до security regression; само отсутствие future workflow не уязвимость. | A07-09 active/revocation отдельно; existing sink/transport checks ограничены. |
| [08_infrastructure_security.md:137](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:137) | Shared secret rotation и saved-config/running-state drift. Operational risk; intended Production | Полный env/ref manifest меняется при layer deploy; соседние processes могут сохранять старые credentials/images. Проверить coordinated key-version/layer compatibility; доказанного компрометационного события нет. | Partial A08-02 shared bundle; rotation самостоятельный runbook contract. |
| [08_infrastructure_security.md:149](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:149) | SSH host fingerprint и image_ref→sed validation. Непроверенный operational риск; intended Production | Fingerprint не задан в repo; Actions settings неизвестны. Некорректный dispatch input может испортить env, но authorized actor уже имеет deploy права. Проверить host identity/ref validation без объявления public injection. | Related A08-11 governance; no privilege escalation proof. |
| [08_infrastructure_security.md:164](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:164) | Advisory exclusions, vendored JS, lock/source reproducibility. Ограничения inventory/supply chain; Shared infrastructure | Комментарии no-fix не актуальный CVE verdict; JS не имеет найденного package lock, signed/SBOM image evidence неизвестно. Нужен approved package/version/provenance inventory; no registry fetch сейчас. | A08-09/10 конкретные immutable/source boundaries; не новые ID. |
| [09_performance_scalability.md:187](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/09_performance_scalability.md:187) | Streams consumer fanout/retention/request-reply connection. Статические формы + нагрузочные риски; Shared infrastructure | 10 groups читают каждый entry; handler sequential; publish trim отличается request path; BRPOP держит connection. Проверить event-size/rate/group lag/request-only retention/delivery budgets; не объявлять measured bottleneck. | A05-05 PEL recovery отдельно; command counts не RTT timings. |
| [09_performance_scalability.md:215](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/09_performance_scalability.md:215) | Connection pool budgets и Redis memory/key families. Риск capacity; Shared infrastructure | Pool defaults per-process, replication умножает SQL connections; Redis effective max unbounded; URI/server overrides unknown. Проверить waits/limits/bytes/TTL families под isolated workload; не MB/player estimate. | A09-09 долгий transaction один источник давления, не вся pool модель. |
| [09_performance_scalability.md:235](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/09_performance_scalability.md:235) | World startup, offline O(V²) graph helper, Hex sync generation. Статический observation/условный risk; Pre-alpha / Experimental | World225 nodes warm pipeline bounded сейчас, larger replicas увеличивают startup; offline generator не runtime; Hex sync generation может занять loop. Проверить actual connected path/representative dimensions before optimization. | A08-04 reachable Hex exposure отдельно; source09 dev-mount assertion проверять по current flag. |
| [09_performance_scalability.md:245](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/09_performance_scalability.md:245) | Shared worker queues, CPU cancellation и training profile. Capacity/recovery risk; Shared infrastructure / Experimental | max_jobs не cores/backlog cap; sync compute не yields, support делит combat queue, to_thread cancellation не stops underlying work; simulation profile actual deployment unknown. Проверить queue/CPU/timeout/consumer budgets. | A09-05 actor cost отдельно; не основание split domain containers. |
| [09_performance_scalability.md:264](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/09_performance_scalability.md:264) | SSR waterfalls/catalog bootstrap, immutable static URLs. Статические формы + browser/release риск; Pre-alpha | Sequential requests не обязательно независимы; catalog fetch до cache comparison; stable URL с immutable cache может быть stale после release. Проверить browser waterfall/cache/version manifest/ordering, не parallelize blindly. | Browser heap/CWV/RAM не измерялись; A09-11 live arrays отдельный contract. |
| [09_performance_scalability.md:173](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/09_performance_scalability.md:173) | Mongo index calls/document size, inventory/loot query amplification. Статические формы + профиль нужен; Pre-alpha | Combat upsert вызывает create_index не обязательно rebuild; full documents/page/bucket/large K требуют byte/query profile; BSON/EXPLAIN не измерялись. Проверить sizes/plans/returned bytes на representative isolated fixtures. | Не приписывать full-scan/N+1/overflow без measurement; A09-08 конкретный return amplification. |

## Пределы использования реестра

Реестр сохраняет source severity, независимо классифицирует evidence/stage и связывает контракты. Он не устанавливает актуальную production-достижимость, не обещает прохождение всей suite и не подтверждает инциденты по историческим failure windows. Перед выбором реализации необходима узкая повторная проверка актуального пути, guards, owner decision и окружения. Ни объединённая группа, ни предложенная regression-проверка не разрешают правки исходников, installs, deployments, migrations или чтение production.
