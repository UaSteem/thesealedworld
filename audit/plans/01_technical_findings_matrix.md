# 01 — Матрица находок для technical hardening

Дата плана: 10.10.2026; источник audit02–10: 09.10.2026; статическое чтение для плана: 09–10.10.2026. **PLAN ONLY.** Матрица классифицирует существующие findings для технической защиты, надёжности и границ ответственности. Она не разрешает implementation, изменение gameplay или development неподтверждённо поддерживаемых поверхностей.

Основание: [audit/10_findings_registry.md:1](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:1) и [audit/10_root_causes.md:1](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:1). Сохранены **120 исходных IDs / 116 canonical**. Новых finding IDs и новых security-аудит выводов нет. Canonical обозначает единицу учёта полного дубля, а не один commit, package или универсальное исправление.

## Классы и независимые gates

У каждого canonical **ровно один PRIMARY**. Secondary gates не меняют счётчик и не означают разрешение реализации. Исходная severity, историческая доказательность и текущая статическая перепроверка показаны отдельно.

| PRIMARY | Значение для плана | Canonical |
| --- | --- | ---: |
| TECH-HARDENING | Разрешён технический контракт при сохранении game behavior; secondary проверки/решения всё ещё обязательны. | 68 |
| GAME-DESIGN | Gameplay, topology, combat/effects либо game UX; за пределами technical hardening. | 3 |
| MIXED | Техническая часть неотделима от неутверждённого owner/game contract. Сначала решение, затем отдельный допустимый slice. | 9 |
| EXPERIMENTAL-LEGACY | Legacy/Experimental applicability не установлена; runtime development не включён. | 17 |
| VERIFY-FIRST | Отдельный эффект, reachability, environment или actual policy сначала подтверждается. | 14 |
| NO-ACTION | Observation/accepted policy без самостоятельной необходимости action; это **не already fixed**. | 5 |
| **Итого** | **Взаимоисключающие классы** | **116** |

Общая стадия — **Pre-alpha**; Old Rift — **Legacy, runtime support unknown**; Hex — **Experimental/Dev-only**; Studio/tools — **Dev-only**. Alpha в исходных аудитах — historical/public label, не оценка фактической готовности. Intended Production Compose/workflow не подтверждает actual server configuration.

RC-01…RC-17 сохранены из master root-cause synthesis. Связь с RC — cross-audit ассоциация причины/контекста, не новое доказательство production-инцидента и не предписание общего framework. «—» означает, что системная причина для записи не установлена. Локальные дефекты и risks не принудительно притянуты к root cause. В частности, reader/migration drift A05-11/A05-13 не объявлен следствием documentation drift RC-17.

Package обозначается стабильным семантическим именем WP-<alias>; «—» означает deferred/no-action. У MIXED/VERIFY-FIRST имя — только возможный package после gates. Номер или наличие package не повышает finding до доказанного текущего дефекта.

## Полнота и дубли

| Аудит исходных IDs | Исходных | Ведущих canonical карточек |
| --- | ---: | ---: |
| 02 | 15 | 15 |
| 03 | 13 | 13 |
| 04 | 21 | 21 |
| 05 | 15 | 13 |
| 06 | 12 | 12 |
| 07 | 18 | 17 |
| 08 | 15 | 14 |
| 09 | 11 | 11 |
| **Всего** | **120** | **116** |

Четыре пары полного дубля: **A04-01 + A07-05**, **A04-12 + A05-07**, **A04-17 + A05-09**, **A07-14 + A08-01**. Severity каждого исходного участника сохранена. Частичные пересечения не объединены. A04-02 остаётся отдельным canonical; A04-17/A05-09 не real-Redis reproduction; A07-14/A08-01 не утверждение о фактических production keys.

Ненумерованные observations/риски, исторические тесты и ограничения восьми аудит-отчётов сохранены в исходном реестре. Они контекст этих карточек; им не присвоены новые IDs и они не увеличивают 120/116. Матрица не создаёт отдельную механическую очередь работ для каждого предложения исходного аудита.

## Быстрый индекс

| Canonical | Все original IDs | PRIMARY | RC | Возможный package |
| --- | --- | --- | --- | --- |
| A02-01 | A02-01 | TECH-HARDENING | RC-11 | WP-boundary-state |
| A02-02 | A02-02 | EXPERIMENTAL-LEGACY | RC-11 | — |
| A02-03 | A02-03 | TECH-HARDENING | RC-11 | WP-boundary-state |
| A02-04 | A02-04 | TECH-HARDENING | RC-11 | WP-boundary-state |
| A02-05 | A02-05 | TECH-HARDENING | RC-11 | WP-boundary-state |
| A02-06 | A02-06 | TECH-HARDENING | RC-11 | WP-boundary-state |
| A02-07 | A02-07 | TECH-HARDENING | RC-11 | WP-boundary-state |
| A02-08 | A02-08 | TECH-HARDENING | RC-11 | WP-boundary-dto |
| A02-09 | A02-09 | TECH-HARDENING | RC-11 | WP-boundary-state |
| A02-10 | A02-10 | EXPERIMENTAL-LEGACY | RC-17 | — |
| O02-01 | O02-01 | NO-ACTION | — | — |
| O02-02 | O02-02 | NO-ACTION | — | — |
| O02-03 | O02-03 | NO-ACTION | — | — |
| O02-04 | O02-04 | VERIFY-FIRST | — | WP-ac-sync |
| O02-05 | O02-05 | VERIFY-FIRST | — | WP-stream-recovery |
| A03-01 | A03-01 | MIXED | RC-07 | WP-reward-once |
| A03-02 | A03-02 | MIXED | RC-09 | WP-reward-once |
| A03-03 | A03-03 | TECH-HARDENING | RC-08 | WP-combat-commit |
| A03-04 | A03-04 | TECH-HARDENING | RC-07 | WP-combat-commit |
| A03-05 | A03-05 | MIXED | RC-10 | WP-reward-once |
| A03-06 | A03-06 | TECH-HARDENING | RC-10 | WP-combat-archive |
| A03-07 | A03-07 | MIXED | RC-07 | WP-reward-once |
| A03-08 | A03-08 | EXPERIMENTAL-LEGACY | — | — |
| A03-09 | A03-09 | VERIFY-FIRST | RC-08 | WP-combat-commit |
| A03-10 | A03-10 | VERIFY-FIRST | RC-08 | WP-ac-sync |
| A03-11 | A03-11 | EXPERIMENTAL-LEGACY | RC-08 | — |
| A03-12 | A03-12 | VERIFY-FIRST | RC-09,RC-10 | WP-combat-archive |
| A03-13 | A03-13 | GAME-DESIGN | — | — |
| A04-01 | A04-01, A07-05 | EXPERIMENTAL-LEGACY | RC-02 | — |
| A04-02 | A04-02 | EXPERIMENTAL-LEGACY | RC-02 | — |
| A04-03 | A04-03 | EXPERIMENTAL-LEGACY | RC-09 | — |
| A04-04 | A04-04 | EXPERIMENTAL-LEGACY | RC-09 | — |
| A04-05 | A04-05 | EXPERIMENTAL-LEGACY | RC-07 | — |
| A04-06 | A04-06 | EXPERIMENTAL-LEGACY | — | — |
| A04-07 | A04-07 | EXPERIMENTAL-LEGACY | — | — |
| A04-08 | A04-08 | MIXED | — | WP-reward-once |
| A04-09 | A04-09 | TECH-HARDENING | — | WP-boundary-state |
| A04-10 | A04-10 | TECH-HARDENING | RC-09 | WP-ai-durability |
| A04-11 | A04-11 | TECH-HARDENING | — | WP-ai-durability |
| A04-12 | A04-12, A05-07 | TECH-HARDENING | RC-09 | WP-ai-durability |
| A04-13 | A04-13 | TECH-HARDENING | RC-09 | WP-ai-durability |
| A04-14 | A04-14 | TECH-HARDENING | — | WP-test-controls |
| A04-15 | A04-15 | EXPERIMENTAL-LEGACY | RC-08 | — |
| A04-16 | A04-16 | EXPERIMENTAL-LEGACY | RC-07 | — |
| A04-17 | A04-17, A05-09 | EXPERIMENTAL-LEGACY | RC-08 | — |
| A04-18 | A04-18 | VERIFY-FIRST | RC-09,RC-10 | WP-ai-durability |
| A04-19 | A04-19 | GAME-DESIGN | — | — |
| A04-20 | A04-20 | EXPERIMENTAL-LEGACY | — | — |
| A04-21 | A04-21 | GAME-DESIGN | — | — |
| A05-01 | A05-01 | MIXED | RC-07 | WP-reward-once |
| A05-02 | A05-02 | TECH-HARDENING | — | WP-loot-transfer |
| A05-03 | A05-03 | TECH-HARDENING | RC-08 | WP-inventory-sync |
| A05-04 | A05-04 | MIXED | RC-09 | WP-reward-once |
| A05-05 | A05-05 | TECH-HARDENING | RC-10 | WP-stream-recovery |
| A05-06 | A05-06 | TECH-HARDENING | RC-09 | WP-chat-archive |
| A05-08 | A05-08 | TECH-HARDENING | RC-10 | WP-ai-durability |
| A05-10 | A05-10 | EXPERIMENTAL-LEGACY | RC-09 | — |
| A05-11 | A05-11 | TECH-HARDENING | — | WP-combat-readback |
| A05-12 | A05-12 | TECH-HARDENING | RC-08 | WP-session-lifecycle |
| A05-13 | A05-13 | TECH-HARDENING | — | WP-site-migrations |
| A05-14 | A05-14 | VERIFY-FIRST | — | WP-loot-transfer |
| A05-15 | A05-15 | VERIFY-FIRST | — | WP-chat-archive |
| A06-01 | A06-01 | TECH-HARDENING | RC-13,RC-17 | WP-test-controls |
| A06-02 | A06-02 | TECH-HARDENING | RC-12 | WP-test-controls |
| A06-03 | A06-03 | TECH-HARDENING | RC-12 | WP-storage-harness |
| A06-04 | A06-04 | TECH-HARDENING | RC-12 | WP-test-controls |
| A06-05 | A06-05 | TECH-HARDENING | RC-14 | WP-dependency-source |
| A06-06 | A06-06 | TECH-HARDENING | RC-13 | WP-test-controls |
| A06-07 | A06-07 | TECH-HARDENING | RC-12 | WP-test-controls |
| A06-08 | A06-08 | TECH-HARDENING | RC-13 | WP-boundary-state |
| A06-09 | A06-09 | TECH-HARDENING | RC-13 | WP-quality-provenance |
| A06-10 | A06-10 | NO-ACTION | — | — |
| A06-11 | A06-11 | NO-ACTION | RC-13 | — |
| A06-12 | A06-12 | TECH-HARDENING | RC-13 | WP-test-controls |
| A07-01 | A07-01 | TECH-HARDENING | RC-01 | WP-auth-game |
| A07-02 | A07-02 | TECH-HARDENING | RC-01 | WP-auth-config |
| A07-03 | A07-03 | TECH-HARDENING | RC-01 | WP-auth-admin |
| A07-04 | A07-04 | TECH-HARDENING | RC-01,RC-04 | WP-auth-internal |
| A07-06 | A07-06 | TECH-HARDENING | RC-01 | WP-chat-access |
| A07-07 | A07-07 | TECH-HARDENING | RC-01 | WP-chat-access |
| A07-08 | A07-08 | TECH-HARDENING | RC-03 | WP-session-lifecycle |
| A07-09 | A07-09 | TECH-HARDENING | RC-03 | WP-session-lifecycle |
| A07-10 | A07-10 | TECH-HARDENING | RC-03 | WP-session-lifecycle |
| A07-11 | A07-11 | TECH-HARDENING | RC-03 | WP-auth-game |
| A07-12 | A07-12 | TECH-HARDENING | RC-01,RC-04,RC-05 | WP-studio-readonly |
| A07-13 | A07-13 | TECH-HARDENING | RC-01 | WP-auth-game |
| A07-14 | A07-14, A08-01 | TECH-HARDENING | RC-04 | WP-secret-validation |
| A07-15 | A07-15 | TECH-HARDENING | RC-04 | WP-surface-isolation |
| A07-16 | A07-16 | VERIFY-FIRST | RC-03,RC-06 | WP-session-lifecycle |
| A07-17 | A07-17 | VERIFY-FIRST | — | WP-browser-render |
| A07-18 | A07-18 | MIXED | RC-07 | WP-reward-once |
| A08-02 | A08-02 | TECH-HARDENING | RC-05 | WP-runtime-isolation |
| A08-03 | A08-03 | TECH-HARDENING | RC-01,RC-04 | WP-auth-internal |
| A08-04 | A08-04 | TECH-HARDENING | RC-04,RC-16 | WP-surface-isolation |
| A08-05 | A08-05 | TECH-HARDENING | RC-06 | WP-metrics-redaction |
| A08-06 | A08-06 | TECH-HARDENING | RC-06 | WP-log-redaction |
| A08-07 | A08-07 | TECH-HARDENING | RC-06 | WP-log-redaction |
| A08-08 | A08-08 | TECH-HARDENING | RC-04 | WP-runtime-isolation |
| A08-09 | A08-09 | TECH-HARDENING | RC-14 | WP-supply-chain |
| A08-10 | A08-10 | TECH-HARDENING | RC-14 | WP-dependency-source |
| A08-11 | A08-11 | VERIFY-FIRST | RC-13,RC-14 | WP-quality-provenance |
| A08-12 | A08-12 | VERIFY-FIRST | RC-05 | WP-runtime-isolation |
| A08-13 | A08-13 | TECH-HARDENING | RC-05,RC-16 | WP-runtime-isolation |
| A08-14 | A08-14 | VERIFY-FIRST | — | WP-transport-policy |
| A08-15 | A08-15 | VERIFY-FIRST | — | WP-recovery-readiness |
| A09-01 | A09-01 | TECH-HARDENING | RC-15 | WP-combat-io |
| A09-02 | A09-02 | TECH-HARDENING | RC-16 | WP-ac-sync |
| A09-03 | A09-03 | TECH-HARDENING | RC-16 | WP-chat-archive |
| A09-04 | A09-04 | TECH-HARDENING | RC-16 | WP-chat-fanout |
| A09-05 | A09-05 | TECH-HARDENING | RC-15 | WP-combat-io |
| A09-06 | A09-06 | TECH-HARDENING | RC-11,RC-15 | WP-ac-sync |
| A09-07 | A09-07 | EXPERIMENTAL-LEGACY | RC-15,RC-16 | — |
| A09-08 | A09-08 | TECH-HARDENING | RC-15 | WP-chat-archive |
| A09-09 | A09-09 | TECH-HARDENING | RC-16 | WP-ai-resource-budget |
| A09-10 | A09-10 | TECH-HARDENING | RC-16 | WP-ai-resource-budget |
| A09-11 | A09-11 | MIXED | RC-16 | WP-browser-retention |

## Текущая перепроверка и границы

Для **каждого из 116 canonical** перечитаны актуальные локальные code anchors всех его original IDs; при необходимости добавлены соседние causal blocks и existing guards. Проверены существование файлов и диапазоны line refs. Это bounded static recheck, не полный повторный аудит каждого модуля, не runtime verification. Карточка ниже указывает реально прочитанные факты; исходное «воспроизведено» остаётся историческим.

Дополнительно прочитаны входные auth/WS/chat contracts, текущие validators и установленный BaseCommonSettings, Streams consumer/processor, Mongo append, dirty/snapshot и commit blocks, CI/build/deploy workflows, Docker source policies, Studio selector/client boundaries, performance IO/loop/insertion paths. Missing scripts у A06-01 проверен filesystem inventory. Факты из .venv — локальные installed bytes, не proof canonical library/release/production source.

В этом задании **не запускались** pytest/collection/performance probes/scanners, services/Compose, миграции, Redis/SQL/Mongo/AI jobs, build/install/update, HTTP/SSH/production reads или deployment. Не читались secrets/.env тела, GitHub settings/registry artifacts. Характеристики p95/CCU, frequencies, actual ingress, grants, file modes, runtime TLS, backups/alerts остаются неизвестны. Ни один historical test не назван выполненным сейчас.

Тесты в поле «будущая проверка» — условия приёмки возможной реализации, не команды к исполнению в этой planning-задаче. Reward/durability/death once, Knowledge cap, common logout и browser history сначала требуют owner contract. Политика security допустимых callers тоже должна сохранять легитимные game/site/admin/service/dev consumers.

## Карточки 116 canonical

### A02-01 — Expedition и Loot worker нарушают ownership persistent state

- **Original IDs / source severity:** A02-01 — High; [audit/02_architecture_boundaries.md:280](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:280); аудит 02. [Canonical в реестре:75](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:75).
- **Историческая доказательность:** A02-01: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha.
- **PRIMARY:** TECH-HARDENING. **Почему:** Чужое persistence ownership переносится за semantic boundary с сохранением общего SQL UoW. **RC:** [RC-11:162](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:162). **Возможный package:** WP-boundary-state.
- **Технический/owner контракт исходной находки:** Expedition; Loot; Items; Inventory; Character. Persistence/rules принадлежат feature owner при сохранении общего UoW.
- **Выполнено сейчас — статическое чтение:** Импорты Expedition содержат Character, Inventory projection, ItemPlacement/ResourceBalance; Loot transfer использует SQL session и ExpeditionService. **Прочитанные anchors:** [src/backend/features/expedition/service.py:12](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/expedition/service.py:12), [src/backend/features/loot/workers/tasks/loot_claim_task.py:189](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/loot/workers/tasks/loot_claim_task.py:189).
- **Secondary gates / ограничения:** Не дробить conservation/rollback на независимые commits; policy safe/unsafe не менять. **Исторические ограничения:** A02-01: Авария и corruption не воспроизведены; не дробить transaction ради транспорта.
- **Будущая необходимая проверка (сейчас не выполнена):** A02-01: Conservation, repeat death/safe-sync, mid-transfer rollback, real SQL constraints.

### A02-02 — Combat/Rift зависят от внутренних constructor graphs

- **Original IDs / source severity:** A02-02 — High; [audit/02_architecture_boundaries.md:291](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:291); аудит 02. [Canonical в реестре:84](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:84).
- **Историческая доказательность:** A02-02: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha / Legacy (Rift; поддержка runtime неизвестна).
- **PRIMARY:** EXPERIMENTAL-LEGACY. **Почему:** Constructor/completion coupling захватывает Legacy Rift; рабочий план runtime требует решения о поддержке. **RC:** [RC-11:162](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:162). **Возможный package:** —.
- **Технический/owner контракт исходной находки:** Combat; Rift; GameSession; Monsters; Loot. Соседний constructor graph не внешний API; completion policy имеет владельца.
- **Выполнено сейчас — статическое чтение:** Rift dependency строит CombatCreationOrchestrator; encounter вызывает create_from_request; finalizer импортирует RiftRuntimeIntegration. **Прочитанные anchors:** [src/backend/features/rift/dependencies.py:137](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/dependencies.py:137), [src/backend/features/rift/services/encounter_service.py:110](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/services/encounter_service.py:110), [src/backend/features/combat/workers/tasks/victory_finalizer_task.py:191](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/workers/tasks/victory_finalizer_task.py:191).
- **Secondary gates / ограничения:** Legacy support unknown; generic Combat owner boundary можно выделить отдельно после выбора поддерживаемых consumers. **Исторические ограничения:** A02-02: Coupling подтверждён; race не доказана.
- **Будущая необходимая проверка (сейчас не выполнена):** A02-02: Duplicate/parallel completion, defeat/draw, restart до Rift apply.

### A02-03 — RedisJSON schema активного персонажа протекает наружу

- **Original IDs / source severity:** A02-03 — High; [audit/02_architecture_boundaries.md:301](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:301); аудит 02. [Canonical в реестре:93](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:93).
- **Историческая доказательность:** A02-03: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha.
- **PRIMARY:** TECH-HARDENING. **Почему:** Storage paths и dirty должны принадлежать manager; это техническая инкапсуляция. **RC:** [RC-11:162](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:162). **Возможный package:** WP-boundary-state.
- **Технический/owner контракт исходной находки:** Character; Combat; Expedition; GameSession. Storage paths/TTL/dirty принадлежат manager через semantic operation.
- **Выполнено сейчас — статическое чтение:** Expedition и Combat finalizer вызывают patch_fields с $.state/$.sessions; mark_dirty отдельный await. **Прочитанные anchors:** [src/backend/features/expedition/service.py:194](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/expedition/service.py:194), [src/backend/features/combat/workers/tasks/victory_finalizer_task.py:294](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/workers/tasks/victory_finalizer_task.py:294), [src/backend/features/game_session/integrations/session_integrator.py:306](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/game_session/integrations/session_integrator.py:306).
- **Secondary gates / ограничения:** Потеря state сейчас не воспроизводилась; preserve transition/order/dirty targets. **Исторические ограничения:** A02-03: Raw-path факт не доказывает потерю конкурентного state.
- **Будущая необходимая проверка (сейчас не выполнена):** A02-03: State transitions, dirty targets, patch→mark fault, concurrent refresh/respawn.

### A02-04 — Character зависит от внутренней формы Inventory hydration

- **Original IDs / source severity:** A02-04 — Medium; [audit/02_architecture_boundaries.md:311](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:311); аудит 02. [Canonical в реестре:102](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:102).
- **Историческая доказательность:** A02-04: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha.
- **PRIMARY:** TECH-HARDENING. **Почему:** Owner projection/hydration API можно укрепить без изменения inventory rules. **RC:** [RC-11:162](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:162). **Возможный package:** WP-boundary-state.
- **Технический/owner контракт исходной находки:** Character; Inventory. Projection и ownership queries — owner-owned contracts.
- **Выполнено сейчас — статическое чтение:** Character импортирует runtime_item_from_instance/build_active_character_projection/build_runtime_session; Inventory DI импортирует CharacterRepository. **Прочитанные anchors:** [src/backend/features/character/integrations/character_state_integrator.py:26](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/character/integrations/character_state_integrator.py:26), [src/backend/features/inventory/dependencies.py:9](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/inventory/dependencies.py:9).
- **Secondary gates / ограничения:** Изменять только boundary; empty/equipped/ownership fixtures сохранить. **Исторические ограничения:** A02-04: Нет доказанного recursive вызова.
- **Будущая необходимая проверка (сейчас не выполнена):** A02-04: Equipped/backpack/expedition hydrate, empty, ownership denial, SQL projection.

### A02-05 — Loot orchestration частично находится в GameSession

- **Original IDs / source severity:** A02-05 — Medium; [audit/02_architecture_boundaries.md:321](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:321); аудит 02. [Canonical в реестре:111](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:111).
- **Историческая доказательность:** A02-05: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha.
- **PRIMARY:** TECH-HARDENING. **Почему:** Claim/schedule принадлежит Loot; перенос orchestration сохраняет payload и результат. **RC:** [RC-11:162](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:162). **Возможный package:** WP-boundary-state.
- **Технический/owner контракт исходной находки:** GameSession; Loot; System. Loot owns claim/schedule и payload; Session owns navigation.
- **Выполнено сейчас — статическое чтение:** GameSession claim_post_combat_loot конструирует LootIntegration/LootService; SYSTEM_TASKS содержит loot_claim_task. **Прочитанные anchors:** [src/backend/features/game_session/integrations/session_integrator.py:263](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/game_session/integrations/session_integrator.py:263), [src/backend/features/system/workers/arq.py:25](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/system/workers/arq.py:25).
- **Secondary gates / ограничения:** Once/cashout policy — отдельный MIXED gate; queue registry не менять без consumer verification. **Исторические ограничения:** A02-05: ARQ integration сейчас не выполнен.
- **Будущая необходимая проверка (сейчас не выполнена):** A02-05: Empty/repeated claim, queue absent, reservation→enqueue fault, state outcome.

### A02-06 — Gameplay policy смешана со storage/core

- **Original IDs / source severity:** A02-06 — Medium; [audit/02_architecture_boundaries.md:330](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:330); аудит 02. [Canonical в реестре:120](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:120).
- **Историческая доказательность:** A02-06: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha).
- **PRIMARY:** TECH-HARDENING. **Почему:** Техническое перемещение уже существующей regen logic; формулы и профили заморожены. **RC:** [RC-11:162](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:162). **Возможный package:** WP-boundary-state.
- **Технический/owner контракт исходной находки:** Character; Inventory; Combat; Monsters; actor_state. Infrastructure сохраняет; feature owns gameplay policy.
- **Выполнено сейчас — статическое чтение:** Session manager refresh_vitals_max валидирует attributes/vitals/items; Character private regen вызывает CharacterVitalsCalculator.apply_regen; core содержит player/monster rules. **Прочитанные anchors:** [src/backend/infrastructure/actor_state/managers/session.py:419](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/actor_state/managers/session.py:419), [src/backend/core/calculators/data/attribute_rule_profiles.py:24](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/core/calculators/data/attribute_rule_profiles.py:24), [src/backend/features/character/integrations/character_state_integrator.py:261](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/character/integrations/character_state_integrator.py:261).
- **Secondary gates / ограничения:** Не корректировать rates/формулы/regen timing; сравнить observables до и после owner extraction. **Исторические ограничения:** A02-06: Общий calculator существует; дублируются entrypoints, не обязательно формула.
- **Будущая необходимая проверка (сейчас не выполнена):** A02-06: Fixed-clock regen, no double regen, max-vitals/equipment refresh, Redis atomicity.

### A02-07 — Transport adapters содержат use-case wiring и обратную утечку транспорта

- **Original IDs / source severity:** A02-07 — Medium; [audit/02_architecture_boundaries.md:339](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:339); аудит 02. [Canonical в реестре:129](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:129).
- **Историческая доказательность:** A02-07: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha).
- **PRIMARY:** TECH-HARDENING. **Почему:** DI и transport adapters отделяются от feature orchestration без нового игрового поведения. **RC:** [RC-11:162](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:162). **Возможный package:** WP-boundary-state.
- **Технический/owner контракт исходной находки:** Combat; Character; Inventory; Items; Streams. Thin transport handler и semantic outbound client.
- **Выполнено сейчас — статическое чтение:** Combat event создаёт orchestrator graph; Character handler открывает session; reward service напрямую events.request ItemEvents.GENERATE_REQUESTED. **Прочитанные anchors:** [src/backend/features/combat/events/__init__.py:37](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/events/__init__.py:37), [src/backend/features/character/events/__init__.py:73](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/character/events/__init__.py:73), [src/backend/features/inventory/services/reward_service.py:122](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/inventory/services/reward_service.py:122).
- **Secondary gates / ограничения:** Preserve request/reply/error/timeout и transaction boundary; не механический CRUD wrapper. **Исторические ограничения:** A02-07: Доставка настоящих Streams не проверена.
- **Будущая необходимая проверка (сейчас не выполнена):** A02-07: Ack/error/correlation/timeout, failed reply, redelivery.

### A02-08 — Inventory runtime schema в cross-side shared

- **Original IDs / source severity:** A02-08 — Medium; [audit/02_architecture_boundaries.md:348](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:348); аудит 02. [Canonical в реестре:138](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:138).
- **Историческая доказательность:** A02-08: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha).
- **PRIMARY:** TECH-HARDENING. **Почему:** Runtime storage DTO может быть owner-owned при сохранении публичного wire contract. **RC:** [RC-11:162](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:162). **Возможный package:** WP-boundary-dto.
- **Технический/owner контракт исходной находки:** Inventory; Character; shared. Shared содержит cross-side API, не backend runtime storage shape.
- **Выполнено сейчас — статическое чтение:** InventoryRuntimeSessionDTO объявлен в shared и содержит by_id/layout/is_dirty; manager и projection используют его. **Прочитанные anchors:** [src/shared/schemas/inventory.py:86](D:/Workspace/personal/pets/TurnBasedMMORPG/src/shared/schemas/inventory.py:86), [src/backend/infrastructure/inventory/managers/session.py:6](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/inventory/managers/session.py:6), [src/backend/features/inventory/services/projection.py:22](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/inventory/services/projection.py:22).
- **Secondary gates / ограничения:** Не разрывать общие client DTO; сначала consumer inventory и serialization compatibility. **Исторические ограничения:** A02-08: Frontend type consumer не найден; внешние consumer не исключены.
- **Будущая необходимая проверка (сейчас не выполнена):** A02-08: Redis roundtrip, frontend/API response contract, consumer inventory.

### A02-09 — Simulation module имеет несколько независимых причин изменения

- **Original IDs / source severity:** A02-09 — Medium; [audit/02_architecture_boundaries.md:357](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:357); аудит 02. [Canonical в реестре:147](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:147).
- **Историческая доказательность:** A02-09: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha / Experimental.
- **PRIMARY:** TECH-HARDENING. **Почему:** Только live runtime импорт private helper из simulation является технической границей. **RC:** [RC-11:162](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:162). **Возможный package:** WP-boundary-state.
- **Технический/owner контракт исходной находки:** Combat; live AI; admin simulation. Независимые run/training/report/policy ответственности имеют явные contracts.
- **Выполнено сейчас — статическое чтение:** ai_turn_task импортирует _policy_from_training_row из ai_simulation_service; service одновременно содержит run orchestration. **Прочитанные anchors:** [src/backend/features/combat/services/ai_simulation_service.py:54](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/services/ai_simulation_service.py:54), [src/backend/features/combat/workers/tasks/ai_turn_task.py:10](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/workers/tasks/ai_turn_task.py:10).
- **Secondary gates / ограничения:** Simulation redesign и AI decisions отложены; выделение immutable policy mapping не менять policy semantics. **Исторические ограничения:** A02-09: Размер файла сам по себе не дефект; migration не предложена здесь.
- **Будущая необходимая проверка (сейчас не выполнена):** A02-09: Simulation/admin/worker/policy mapping contracts.

### A02-10 — Architecture guidance содержит устаревшие anchors

- **Original IDs / source severity:** A02-10 — Low; [audit/02_architecture_boundaries.md:366](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:366); аудит 02. [Canonical в реестре:156](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:156).
- **Историческая доказательность:** A02-10: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha / Legacy (Rift; поддержка runtime неизвестна).
- **PRIMARY:** EXPERIMENTAL-LEGACY. **Почему:** Stage/legacy documentation drift не даёт разрешение развивать старый Rift. **RC:** [RC-17:234](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:234). **Возможный package:** —.
- **Технический/owner контракт исходной находки:** Project skills; Rift; Combat. Guidance anchors/stage отражают актуальные owner decisions.
- **Выполнено сейчас — статическое чтение:** Skill approved boundary ссылается на local dev harness, текущие Rift models/routes существуют. **Прочитанные anchors:** [.agents/skills/turnbasedmmorpg-rift/references/implementation-boundaries.md:1](D:/Workspace/personal/pets/TurnBasedMMORPG/.agents/skills/turnbasedmmorpg-rift/references/implementation-boundaries.md:1), [src/backend/infrastructure/rift/models.py:12](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/rift/models.py:12), [src/backend/features/rift/api/router.py:31](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/api/router.py:31).
- **Secondary gates / ограничения:** Legacy support decision; skill update лишь отдельное предложение, не правка сейчас. **Исторические ограничения:** A02-10: История approvals неполна; code existence не approval.
- **Будущая необходимая проверка (сейчас не выполнена):** A02-10: Link check, current-stage/owner-decision review.

### O02-01 — GenerationAI registry registration — допустимая extension wiring с централизованным editing point (§5); перемещение composition необязательно сейчас.

- **Original IDs / source severity:** O02-01 — Observation; [audit/02_architecture_boundaries.md:377](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:377); аудит 02. [Canonical в реестре:165](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:165).
- **Историческая доказательность:** O02-01: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha).
- **PRIMARY:** NO-ACTION. **Почему:** Центральная registration точка сейчас допустима; standalone дефект не установлен. **RC:** — (системная причина не установлена). **Возможный package:** —.
- **Технический/owner контракт исходной находки:** GenerationAI; World; Items; Monsters. Допустимое extension registration имеет явную composition ownership.
- **Выполнено сейчас — статическое чтение:** build_generation_ai_registry последовательно регистрирует item/monster/news/world handlers. **Прочитанные anchors:** [src/backend/features/generation_ai/bootstrap.py:23](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/bootstrap.py:23).
- **Secondary gates / ограничения:** NO-ACTION — accepted structure, не утверждение already fixed; revisit только при доказанном конфликте ownership. **Исторические ограничения:** O02-01: Observation: перенос composition необязателен.
- **Будущая необходимая проверка (сейчас не выполнена):** O02-01: Registry owner/facade и task registration review.

### O02-02 — shared security/logging/metrics — полезные cross-cutting modules при более узком буквальном skill; решить policy, не удалять автоматически.

- **Original IDs / source severity:** O02-02 — Observation; [audit/02_architecture_boundaries.md:378](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:378); аудит 02. [Canonical в реестре:174](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:174).
- **Историческая доказательность:** O02-02: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha).
- **PRIMARY:** NO-ACTION. **Почему:** Shared policy observation не доказывает неправильное место конкретной security функции. **RC:** — (системная причина не установлена). **Возможный package:** —.
- **Технический/owner контракт исходной находки:** shared; security; logging; metrics; project policy. Cross-cutting utilities требуют явной допустимости в shared.
- **Выполнено сейчас — статическое чтение:** shared/security/passwords содержит password hash primitives и PASSWORD_ITERATIONS. **Прочитанные anchors:** [src/shared/security/passwords.py:15](D:/Workspace/personal/pets/TurnBasedMMORPG/src/shared/security/passwords.py:15).
- **Secondary gates / ограничения:** Не превращать observation в blanket relocation или новое security audit; auth defects имеют отдельные A07 IDs. **Исторические ограничения:** O02-02: Не доказан runtime defect; нужен owner contract.
- **Будущая необходимая проверка (сейчас не выполнена):** O02-02: Policy review потребителей security/logging/metrics.

### O02-03 — readiness native resolver ограничена ambient RNG/catalog/tunables; это препятствие планируемой extraction, не требование сейчас внедрять иной язык.

- **Original IDs / source severity:** O02-03 — Observation; [audit/02_architecture_boundaries.md:379](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:379); аудит 02. [Canonical в реестре:183](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:183).
- **Историческая доказательность:** O02-03: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Experimental.
- **PRIMARY:** NO-ACTION. **Почему:** Native extraction — возможность, а не утверждённое требование и не технический defect. **RC:** — (системная причина не установлена). **Возможный package:** —.
- **Технический/owner контракт исходной находки:** Combat resolver; native extraction. Portable resolver input включает RNG/rules/tunables.
- **Выполнено сейчас — статическое чтение:** MathCore использует module random.random; native-ready purity сама по себе не заявлена кодом. **Прочитанные anchors:** [src/backend/features/combat/runtime/engine/math_core.py:30](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/engine/math_core.py:30).
- **Secondary gates / ограничения:** Не вводить native ABI, замену RNG или боевых формул по этой observation. **Исторические ограничения:** O02-03: Extraction не текущий обязательный продуктовый scope.
- **Будущая необходимая проверка (сейчас не выполнена):** O02-03: Explicit snapshot corpus, RNG/rules/tunables parity.

### O02-04 — конкурентное Rift completion и patch/dirty partial failures требуют integration proof. Нельзя считать corruption подтверждённым.

- **Original IDs / source severity:** O02-04 — Observation; [audit/02_architecture_boundaries.md:380](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:380); аудит 02. [Canonical в реестре:192](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:192).
- **Историческая доказательность:** O02-04: Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Pre-alpha / Legacy (Rift; поддержка runtime неизвестна).
- **PRIMARY:** VERIFY-FIRST. **Почему:** Широкая completion/patch hypothesis требует сначала разделить конкретные failure windows. **RC:** — (системная причина не установлена). **Возможный package:** WP-ac-sync.
- **Технический/owner контракт исходной находки:** Combat; Rift; Character dirty state. Completion/patch/dirty согласованы при fault/concurrency.
- **Выполнено сейчас — статическое чтение:** Rift apply проверяет active_encounter_id; AC patch_fields использует transaction=False; guard не доказывает атомарность всего эффекта. **Прочитанные anchors:** [src/backend/features/rift/integrations/runtime.py:410](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/integrations/runtime.py:410), [src/backend/infrastructure/actor_state/managers/session.py:119](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/actor_state/managers/session.py:119).
- **Secondary gates / ограничения:** Legacy part deferred; shared AC verification separately; no real-store race now. **Исторические ограничения:** O02-04: Нет integration proof; broad observation.
- **Будущая необходимая проверка (сейчас не выполнена):** O02-04: Real RedisJSON barriers, completion failure boundaries.

### O02-05 — `src/backend/features/loot/workers/arq.py:27` и `system/workers/arq.py:53` используют SYSTEM queue с разными registries; текущий `deploy/compose.game.yml:186` запускает SystemArqSettings. Не доказана одновременная работа несовместимых consumers; это latent config risk при выборе другого entrypoint.

- **Original IDs / source severity:** O02-05 — Observation; [audit/02_architecture_boundaries.md:381](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/02_architecture_boundaries.md:381); аудит 02. [Canonical в реестре:201](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:201).
- **Историческая доказательность:** O02-05: Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Shared infrastructure (Pre-alpha).
- **PRIMARY:** VERIFY-FIRST. **Почему:** Риск альтернативного worker registry применим лишь при реальном запуске второго consumer. **RC:** — (системная причина не установлена). **Возможный package:** WP-stream-recovery.
- **Технический/owner контракт исходной находки:** Loot; System; ARQ; deployment. Consumer registry соответствует выбранной queue/entrypoint.
- **Выполнено сейчас — статическое чтение:** LootArqSettings и SystemArqSettings используют SYSTEM queue; Compose выбран system-worker; SYSTEM_TASKS содержит Loot. **Прочитанные anchors:** [src/backend/features/loot/workers/arq.py:27](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/loot/workers/arq.py:27), [src/backend/features/system/workers/arq.py:53](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/system/workers/arq.py:53), [deploy/compose.game.yml:186](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/compose.game.yml:186).
- **Secondary gates / ограничения:** Проверить deployed entrypoint/registry до action; не менять выбранный working consumer без доказательства. **Исторические ограничения:** O02-05: Compose сейчас выбирает SystemArqSettings; одновременность не доказана.
- **Будущая необходимая проверка (сейчас не выполнена):** O02-05: Queue→function→deployed worker matrix.

### A03-01 — Повтор finalizer повторно начисляет XP

- **Original IDs / source severity:** A03-01 — High; [audit/03_combat_runtime.md:294](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:294); аудит 03. [Canonical в реестре:212](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:212).
- **Историческая доказательность:** A03-01: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha.
- **PRIMARY:** MIXED. **Почему:** Unit of reward application/replay contract сначала утверждает owner; суммы/XP policy вне scope. **RC:** [RC-07:114](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:114). **Возможный package:** WP-reward-once.
- **Технический/owner контракт исходной находки:** Combat; Character; Expedition. Один combat/character progression effect один раз.
- **Выполнено сейчас — статическое чтение:** collector enqueues victory_finalizer; finalizer вызывает ExperienceFinalizer; rewards идут apply_progress/apply_skill_progress без combat-id аргумента. **Прочитанные anchors:** [src/backend/features/combat/workers/tasks/collector_task.py:76](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/workers/tasks/collector_task.py:76), [src/backend/features/combat/workers/tasks/victory_finalizer_task.py:69](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/workers/tasks/victory_finalizer_task.py:69), [src/backend/features/combat/runtime/services/experience_finalizer.py:69](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/services/experience_finalizer.py:69), [src/backend/features/combat/runtime/services/experience_finalizer.py:83](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/services/experience_finalizer.py:83).
- **Secondary gates / ограничения:** MIXED: решить once per combat/phase/participant; повтор сейчас не запускался, XP formula заморожена. **Исторические ограничения:** A03-01: Additive path статически установлен; runtime repro не запускался.
- **Будущая необходимая проверка (сейчас не выполнена):** A03-01: Sequential/concurrent duplicate, crash после XP, cumulative delta=1.

### A03-02 — Ошибка финализации оставляет закрытый бой без завершённых последствий

- **Original IDs / source severity:** A03-02 — High; [audit/03_combat_runtime.md:302](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:302); аудит 03. [Canonical в реестре:221](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:221).
- **Историческая доказательность:** A03-02: Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. **Стадия:** Pre-alpha.
- **PRIMARY:** MIXED. **Почему:** Recovery orchestration касается XP/death/durability; approved completion semantics неизвестны. **RC:** [RC-09:138](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:138). **Возможный package:** WP-reward-once.
- **Технический/owner контракт исходной находки:** Combat; Character; Archive; ARQ. Closed combat имеет результат и восстановимые последствия.
- **Выполнено сейчас — статическое чтение:** set_battle_winner предшествует vitals/XP/freeze/enqueue; широкий except только логирует исключение. **Прочитанные anchors:** [src/backend/features/combat/workers/tasks/victory_finalizer_task.py:71](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/workers/tasks/victory_finalizer_task.py:71), [src/backend/features/combat/workers/tasks/collector_task.py:46](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/workers/tasks/collector_task.py:46), [src/backend/features/combat/workers/tasks/victory_finalizer_task.py:133](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/workers/tasks/victory_finalizer_task.py:133).
- **Secondary gates / ограничения:** Можно технически хранить pending phases лишь после owner effect contract; не выбирать новый combat outcome. **Исторические ограничения:** A03-02: Infrastructure injection отсутствует.
- **Будущая необходимая проверка (сейчас не выполнена):** A03-02: Fault каждого шага, restart, eventual result без double XP.

### A03-03 — Commit exchange не атомарен

- **Original IDs / source severity:** A03-03 — High; [audit/03_combat_runtime.md:309](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:309); аудит 03. [Canonical в реестре:230](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:230).
- **Историческая доказательность:** A03-03: Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Pre-alpha.
- **PRIMARY:** TECH-HARDENING. **Почему:** Commit atomicity/fencing — технический инвариант уже рассчитанного exchange. **RC:** [RC-08:126](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:126). **Возможный package:** WP-combat-commit.
- **Технический/owner контракт исходной находки:** Combat; RedisJSON. Actor/queue/step/logs exchange согласованы.
- **Выполнено сейчас — статическое чтение:** Executor check_worker_lock предшествует commit_session; session manager пишет через pipeline(transaction=False). **Прочитанные anchors:** [src/backend/features/combat/workers/tasks/executor_task.py:120](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/workers/tasks/executor_task.py:120), [src/backend/features/combat/integrations/session_integration.py:401](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/integrations/session_integration.py:401), [src/backend/infrastructure/combat/managers/session.py:608](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/combat/managers/session.py:608).
- **Secondary gates / ограничения:** Comment «атомарный» не proof; real Redis multi-key/fault checks будущие, не gameplay resolver changes. **Исторические ограничения:** A03-03: Python kill после отправки pipeline не доказывает Redis partial failure.
- **Будущая необходимая проверка (сейчас не выполнена):** A03-03: Error k-й команды, missing actor, retry batch, consistency/recovery.

### A03-04 — Повтор create с тем же combat_id сбрасывает существующий бой

- **Original IDs / source severity:** A03-04 — High; [audit/03_combat_runtime.md:316](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:316); аудит 03. [Canonical в реестре:239](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:239).
- **Историческая доказательность:** A03-04: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Pre-alpha.
- **PRIMARY:** TECH-HARDENING. **Почему:** Повтор технического create не должен незаметно перезаписать существующий runtime; unit create identity проверить. **RC:** [RC-07:114](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:114). **Возможный package:** WP-combat-commit.
- **Технический/owner контракт исходной находки:** Combat; Exploration; RedisJSON. Повтор create ID не уничтожает progress.
- **Выполнено сейчас — статическое чтение:** create session делает hset/JSON set actor/targets через transaction=False, existence guard в прочитанном write block нет. **Прочитанные anchors:** [src/backend/infrastructure/combat/managers/session.py:89](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/combat/managers/session.py:89).
- **Secondary gates / ограничения:** До решения freeze create-vs-replace contract; не менять participants/combat initiation rules. **Исторические ограничения:** A03-04: Real Redis не запускался; reset commands установлены.
- **Будущая необходимая проверка (сейчас не выполнена):** A03-04: Repeat до/после ready/exchange, concurrent creators, mid-create fault.

### A03-05 — Поздний loot preorder не попадает в завершённый результат

- **Original IDs / source severity:** A03-05 — Medium; [audit/03_combat_runtime.md:323](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:323); аудит 03. [Canonical в реестре:248](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:248).
- **Историческая доказательность:** A03-05: Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. **Стадия:** Pre-alpha.
- **PRIMARY:** MIXED. **Почему:** Late preorder и reward entitlement требуют owner contract, затем надёжную доставку. **RC:** [RC-10:150](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:150). **Возможный package:** WP-reward-once.
- **Технический/owner контракт исходной находки:** Combat; Loot; Streams. Loot-ready и combat-finished сходятся независимо от порядка.
- **Выполнено сейчас — статическое чтение:** LootStreamClient exposes order_hidden_corpses; producer request interface существующий. **Прочитанные anchors:** [src/backend/features/loot/integrations/stream_client.py:18](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/loot/integrations/stream_client.py:18).
- **Secondary gates / ограничения:** Порядок eligibility/reward и expected rendezvous сейчас не утверждён; не создавать новый loot policy. **Исторические ограничения:** A03-05: Частота неизвестна; полный user effect требует integration.
- **Будущая необходимая проверка (сейчас не выполнена):** A03-05: Оба порядка, delay preorder, повтор событий, visibility/result.

### A03-06 — После commit потеря enqueue support оставляет архив без analytics facts

- **Original IDs / source severity:** A03-06 — Medium; [audit/03_combat_runtime.md:330](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:330); аудит 03. [Canonical в реестре:257](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:257).
- **Историческая доказательность:** A03-06: Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. **Стадия:** Pre-alpha.
- **PRIMARY:** TECH-HARDENING. **Почему:** Надёжная доставка уже сформированного analytics fact не меняет бой. **RC:** [RC-10:150](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:150). **Возможный package:** WP-combat-archive.
- **Технический/owner контракт исходной находки:** Combat; Support analytics; ARQ. Committed exchange имеет восстановимый analytics fact.
- **Выполнено сейчас — статическое чтение:** ResultSupportTask строит факт и append_analytics; executor commits перед enqueue_result_support_tasks. **Прочитанные anchors:** [src/backend/features/combat/runtime/support/result_support_task.py:16](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/support/result_support_task.py:16).
- **Secondary gates / ограничения:** Проверить durable obligation/retry identity; очередной emit не равно stored analytics. **Исторические ограничения:** A03-06: Queue fault не инъецировался.
- **Будущая необходимая проверка (сейчас не выполнена):** A03-06: Enqueue fault, delayed/duplicate support, expected seq.

### A03-07 — Durability marker не защищает повтор после частично успешного применения

- **Original IDs / source severity:** A03-07 — Medium; [audit/03_combat_runtime.md:336](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:336); аудит 03. [Canonical в реестре:266](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:266).
- **Историческая доказательность:** A03-07: Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. **Стадия:** Pre-alpha.
- **PRIMARY:** MIXED. **Почему:** Единица применения durability effect и duplicate policy требуют owner, величина damage вне scope. **RC:** [RC-07:114](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:114). **Возможный package:** WP-reward-once.
- **Технический/owner контракт исходной находки:** Combat; Inventory; Character. Durability event меняет SQL mechanics не более раза.
- **Выполнено сейчас — статическое чтение:** Inventory проверяет idempotency_key перед effect; set runtime и repository.commit происходят до завершающего marker блока. **Прочитанные anchors:** [src/backend/features/inventory/services/inventory_service.py:197](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/inventory/services/inventory_service.py:197), [src/backend/features/combat/runtime/services/durability_policy.py:56](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/services/durability_policy.py:56), [src/backend/features/inventory/services/inventory_service.py:230](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/inventory/services/inventory_service.py:230).
- **Secondary gates / ограничения:** MIXED; once key и replay после SQL commit доказать, не менять durability formula/scope. **Исторические ограничения:** A03-07: Sequential complete duplicate уже guarded; real integration нет.
- **Будущая необходимая проверка (сейчас не выполнена):** A03-07: Fault до/после commit/marker, concurrent event, durable delta=1.

### A03-08 — Ошибка загрузки policy обходит failed-состояние simulation run

- **Original IDs / source severity:** A03-08 — Medium; [audit/03_combat_runtime.md:342](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:342); аудит 03. [Canonical в реестре:275](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:275).
- **Историческая доказательность:** A03-08: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Experimental.
- **PRIMARY:** EXPERIMENTAL-LEGACY. **Почему:** Live simulation orchestration принадлежит Experimental/Dev-only; automatic product hardening нет. **RC:** — (системная причина не установлена). **Возможный package:** —.
- **Технический/owner контракт исходной находки:** Combat; AI simulation; SQL. Failed job отражается terminal run state.
- **Выполнено сейчас — статическое чтение:** combat_ai_live_simulation_task awaits policy payload до persist closure и основного failure handling. **Прочитанные anchors:** [src/backend/features/combat/workers/tasks/ai_simulation_task.py:43](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/workers/tasks/ai_simulation_task.py:43).
- **Secondary gates / ограничения:** Если среда поддерживается, отдельный technical failure-state slice; AI learning/simulation outcomes не менять. **Исторические ограничения:** A03-08: Stale cleanup отдельно; integration job не запускалась.
- **Будущая необходимая проверка (сейчас не выполнена):** A03-08: Missing row, invalid policy, DB setup error, cancellation.

### A03-09 — Stale executor context и отсутствие fencing

- **Original IDs / source severity:** A03-09 — High; [audit/03_combat_runtime.md:359](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:359); аудит 03. [Canonical в реестре:284](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:284).
- **Историческая доказательность:** A03-09: Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Pre-alpha.
- **PRIMARY:** VERIFY-FIRST. **Почему:** Concurrency hypothesis остаётся предварительной до проверки lease/fencing реального store. **RC:** [RC-08:126](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:126). **Возможный package:** WP-combat-commit.
- **Технический/owner контракт исходной находки:** Combat executor; Redis lease. Snapshot writer fenced по version/epoch.
- **Выполнено сейчас — статическое чтение:** Executor load_battle_context стоит до executor lease block; check перед save отделён от transaction=False manager commit. **Прочитанные anchors:** [src/backend/features/combat/workers/tasks/executor_task.py:59](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/workers/tasks/executor_task.py:59), [src/backend/infrastructure/combat/managers/session.py:608](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/combat/managers/session.py:608).
- **Secondary gates / ограничения:** VERIFY-FIRST; воспроизвести stale-read + expired lease barrier; не считать established lost update. **Исторические ограничения:** A03-09: Production corruption не доказана; lease release owner-aware.
- **Будущая необходимая проверка (сейчас не выполнена):** A03-09: Two-worker read/acquire/check/save barriers, expiry/restart.

### A03-10 — AC dirty generation не является CAS

- **Original IDs / source severity:** A03-10 — Medium; [audit/03_combat_runtime.md:363](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:363); аудит 03. [Canonical в реестре:293](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:293).
- **Историческая доказательность:** A03-10: Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Pre-alpha.
- **PRIMARY:** VERIFY-FIRST. **Почему:** Условие race есть, фактическая потеря dirty требует storage verification. **RC:** [RC-08:126](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:126). **Возможный package:** WP-ac-sync.
- **Технический/owner контракт исходной находки:** Character AC; Combat; SQL sync. Clear G не очищает mark G+1; replacement не теряет patch.
- **Выполнено сейчас — статическое чтение:** AC clear_dirty читает generation, затем отдельный patch $.sync_dirty=None; patch pipeline nontransactional. **Прочитанные anchors:** [src/backend/infrastructure/actor_state/managers/session.py:166](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/actor_state/managers/session.py:166), [src/backend/infrastructure/actor_state/managers/session.py:119](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/actor_state/managers/session.py:119), [src/backend/features/character/integrations/system_integrator.py:42](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/character/integrations/system_integrator.py:42).
- **Secondary gates / ограничения:** Существующий generation guard сохранить; real concurrent mutation не запускалась. **Исторические ограничения:** A03-10: Неатомарность установлена; effect не воспроизведён.
- **Будущая необходимая проверка (сейчас не выполнена):** A03-10: Sync/finalizer/refresh barriers, patch→mark fault.

### A03-11 — Частичный/конкурентный Rift completion

- **Original IDs / source severity:** A03-11 — Medium; [audit/03_combat_runtime.md:367](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:367); аудит 03. [Canonical в реестре:302](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:302).
- **Историческая доказательность:** A03-11: Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Pre-alpha / Legacy (Rift; поддержка runtime неизвестна).
- **PRIMARY:** EXPERIMENTAL-LEGACY. **Почему:** Completion касается Legacy Rift и synthetic victory branch; поддержка неизвестна. **RC:** [RC-08:126](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:126). **Возможный package:** —.
- **Технический/owner контракт исходной находки:** Combat; Rift; GameSession. Outcome/completion/instance/session/presence согласованы.
- **Выполнено сейчас — статическое чтение:** apply_combat_result сравнивает active encounter; CombatSystemIntegrator передаёт result=«victory». **Прочитанные anchors:** [src/backend/features/rift/integrations/runtime.py:410](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/integrations/runtime.py:410), [src/backend/features/combat/integrations/system_integrator.py:259](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/integrations/system_integrator.py:259).
- **Secondary gates / ограничения:** Legacy decision и outcome owner; не объединять с A04-15 — partial completion шире. **Исторические ограничения:** A03-11: Sequential successful duplicate no-op; concurrent effect не доказан.
- **Будущая необходимая проверка (сейчас не выполнена):** A03-11: Parallel callbacks, fault each save, defeat/missing runtime.

### A03-12 — Freeze может обогнать support analytics; TTL и archive retry ограничены

- **Original IDs / source severity:** A03-12 — Medium; [audit/03_combat_runtime.md:371](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:371); аудит 03. [Canonical в реестре:311](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:311).
- **Историческая доказательность:** A03-12: Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Pre-alpha.
- **PRIMARY:** VERIFY-FIRST. **Почему:** Archive freeze/TTL/insert/late facts требуют нескольких независимых probes. **RC:** [RC-09:138](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:138), [RC-10:150](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:150). **Возможный package:** WP-combat-archive.
- **Технический/owner контракт исходной находки:** Combat; Support; Archive; Mongo; SQL. Freeze содержит expected facts; payload и persist устойчивы.
- **Выполнено сейчас — статическое чтение:** persist task читает Redis finalization; Builder отдельно читает actors/analytics/logs; executor enqueue после commit. **Прочитанные anchors:** [src/backend/features/combat/workers/tasks/finalization_persist_task.py:27](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/workers/tasks/finalization_persist_task.py:27), [src/backend/features/combat/workers/tasks/executor_task.py:127](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/workers/tasks/executor_task.py:127), [src/backend/features/combat/runtime/services/finalization_builder.py:25](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/services/finalization_builder.py:25).
- **Secondary gates / ограничения:** VERIFY-FIRST; current source ordering не доказывает real TTL/race/duplicate PG effects. **Исторические ограничения:** A03-12: Unique combat_id удерживает одну row; не каждый archive неполон.
- **Будущая необходимая проверка (сейчас не выполнена):** A03-12: Delay support, Mongo/SQL outage, concurrent persist, expiry.

### A03-13 — Crit-bleed применяется после парирования/уклонения

- **Original IDs / source severity:** A03-13 — Medium; [audit/03_combat_runtime.md:348](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/03_combat_runtime.md:348); аудит 03. [Canonical в реестре:320](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:320).
- **Историческая доказательность:** A03-13: Исторически воспроизведено локальной проверкой/тестом исходного аудита; сейчас не повторялось. **Стадия:** Pre-alpha.
- **PRIMARY:** GAME-DESIGN. **Почему:** Связь crit/parry и applied effects определяет боевую семантику, запрещённую в hardening. **RC:** — (системная причина не установлена). **Возможный package:** —.
- **Технический/owner контракт исходной находки:** Combat engine; Game catalog. On-contact crit effect не появляется после parry/dodge.
- **Выполнено сейчас — статическое чтение:** ON_CRIT weapon catalog содержит bleed; trigger activation добавляет is_hit/is_crit conditions; crit step выполняется до parry. **Прочитанные anchors:** [src/backend/features/game_catalog/combat/resources/triggers/definitions/rules/weapon_triggers.py:12](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/game_catalog/combat/resources/triggers/definitions/rules/weapon_triggers.py:12), [src/backend/features/combat/runtime/engine/resolver/support/trigger_activator.py:71](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/engine/resolver/support/trigger_activator.py:71), [src/backend/features/combat/runtime/engine/resolver/orchestrator.py:50](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/engine/resolver/orchestrator.py:50).
- **Secondary gates / ограничения:** GAME-DESIGN; возможен только test-precondition guard A06-02 без выбора иной effect semantics. **Исторические ограничения:** A03-13: Исторический post-phase probe; полный pipeline pytest не завершён; ненулевой DoT не измерен.
- **Будущая необходимая проверка (сейчас не выполнена):** A03-13: Fired trigger precondition; parry/dodge/block/hit/noncrit, tokens отдельно.

### A04-01 — клиент управляет игровыми исходами

- **Original IDs / source severity:** A04-01 — High; [audit/04_rift_world_generation.md:111](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:111); аудит 04; A07-05 — High; [audit/07_application_security.md:207](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:207); аудит 07. [Canonical в реестре:331](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:331).
- **Историческая доказательность:** A04-01: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. Сейчас выборочно подтверждены только указанные статические предпосылки; A07-05: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Legacy (поддержка runtime неизвестна).
- **PRIMARY:** EXPERIMENTAL-LEGACY. **Почему:** Trust defect лежит в Legacy Rift DTO; routine включение runtime запрещено. **RC:** [RC-02:54](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:54). **Возможный package:** —.
- **Технический/owner контракт исходной находки:** Rift player API; Character; Combat. Сервер определяет event/outcome/attributes.
- **Выполнено сейчас — статическое чтение:** Player DTO допускает force_event; route передаёт request в PlayerService; такая граница присутствует сейчас. **Прочитанные anchors:** [src/backend/features/rift/api/router.py:56](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/api/router.py:56), [src/backend/features/rift/dto/runtime.py:17](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/dto/runtime.py:17), [src/backend/features/rift/services/player_service.py:64](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/services/player_service.py:64), [src/backend/features/rift/api/router.py:64](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/api/router.py:64).
- **Secondary gates / ограничения:** Original IDs A04-01/A07-05; поддержка/публикация Legacy и owner server-fact contract до реализации; A04-02 отдельно. **Исторические ограничения:** A04-01: Node combat manual resolve уже запрещён; full exploit/production нет; A07-05: Постоянные base attributes mutation не доказаны; node completion guard есть.
- **Будущая необходимая проверка (сейчас не выполнена):** A04-01: Player DTO→service negative force_event/outcome/attributes, guards сохраняются; A07-05: Deny player overrides, authoritative combat callback, preserve node guards.

### A04-02 — отсутствие результата боя трактуется как победа

- **Original IDs / source severity:** A04-02 — High; [audit/04_rift_world_generation.md:123](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:123); аудит 04. [Canonical в реестре:340](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:340).
- **Историческая доказательность:** A04-02: Исторически воспроизведено локальной проверкой/тестом исходного аудита; сейчас не повторялось. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Legacy (Rift) / Pre-alpha (Combat).
- **PRIMARY:** EXPERIMENTAL-LEGACY. **Почему:** Synthetic outcome recovery меняет Legacy progression и требует outcome owner. **RC:** [RC-02:54](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:54). **Возможный package:** —.
- **Технический/owner контракт исходной находки:** Combat; Rift; recovery. Unknown combat result не победа и не clears gate.
- **Выполнено сейчас — статическое чтение:** Combat missing-session handler вызывает recover_missing_combat_transition; integrator apply_combat_result передаёт literal victory. **Прочитанные anchors:** [src/backend/features/combat/api/router.py:48](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/api/router.py:48), [src/backend/features/combat/integrations/system_integrator.py:259](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/integrations/system_integrator.py:259), [src/backend/features/rift/integrations/runtime.py:453](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/integrations/runtime.py:453).
- **Secondary gates / ограничения:** Нельзя заменять outcome/выдачу награды как «техническую» правку; standalone canonical. **Исторические ограничения:** A04-02: Исторический in-memory repro; не network/cross-store proof.
- **Будущая необходимая проверка (сейчас не выполнена):** A04-02: Real integrations с fake stores: missing/defeat/known victory; затем expiry/restart.

### A04-03 — начальное прохождение не сохраняется в Mongo

- **Original IDs / source severity:** A04-03 — High; [audit/04_rift_world_generation.md:140](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:140); аудит 04. [Canonical в реестре:349](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:349).
- **Историческая доказательность:** A04-03: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Legacy (поддержка runtime неизвестна).
- **PRIMARY:** EXPERIMENTAL-LEGACY. **Почему:** Durable initial snapshot касается неподтверждённо поддерживаемого Legacy. **RC:** [RC-09:138](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:138). **Возможный package:** —.
- **Технический/owner контракт исходной находки:** Rift; Redis; Mongo; membership SQL. Начатый run имеет durable initial snapshot.
- **Выполнено сейчас — статическое чтение:** Entry вызывает save_instance_runtime(mode=redis_and_db); integration для этой mode пишет Redis, db_only отклоняет. **Прочитанные anchors:** [src/backend/features/rift/services/entry_service.py:54](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/services/entry_service.py:54), [src/backend/features/rift/integrations/runtime.py:55](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/integrations/runtime.py:55), [src/backend/features/rift/integrations/runtime.py:148](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/integrations/runtime.py:148).
- **Secondary gates / ограничения:** Legacy persistence/TTL/support decision; не заявлен current restart reproduction. **Исторические ограничения:** A04-03: Реальное ожидание TTL не выполнено.
- **Будущая необходимая проверка (сейчас не выполнена):** A04-03: Fresh entry→loss Redis→restore session/presence/refs.

### A04-04 — membership остаётся активным после выхода

- **Original IDs / source severity:** A04-04 — Medium; [audit/04_rift_world_generation.md:148](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:148); аудит 04. [Canonical в реестре:358](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:358).
- **Историческая доказательность:** A04-04: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Legacy (поддержка runtime неизвестна).
- **PRIMARY:** EXPERIMENTAL-LEGACY. **Почему:** Exit membership recovery — Legacy lifecycle; не включать автоматически. **RC:** [RC-09:138](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:138). **Возможный package:** —.
- **Технический/owner контракт исходной находки:** Rift; membership SQL; Redis. Terminal exit исключён из active restore index.
- **Выполнено сейчас — статическое чтение:** Exit меняет session status и save_run_session; active repository query выбирает ACTIVE_RESTORE_STATUSES. **Прочитанные anchors:** [src/backend/features/rift/services/player_service.py:173](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/services/player_service.py:173), [src/backend/features/rift/integrations/runtime.py:141](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/integrations/runtime.py:141), [src/backend/infrastructure/rift/repositories/state.py:61](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/rift/repositories/state.py:61).
- **Secondary gates / ограничения:** Полную DB status propagation не переоценивать по local windows; live revival сейчас не проверен. **Исторические ограничения:** A04-04: Автоматический re-entry каждого игрока не заявляется.
- **Будущая необходимая проверка (сейчас не выполнена):** A04-04: Exit→SQL status→restore lookup после повторного входа.

### A04-05 — entry не идемпотентен

- **Original IDs / source severity:** A04-05 — Medium; [audit/04_rift_world_generation.md:156](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:156); аудит 04. [Canonical в реестре:367](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:367).
- **Историческая доказательность:** A04-05: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Legacy (поддержка runtime неизвестна).
- **PRIMARY:** EXPERIMENTAL-LEGACY. **Почему:** Повторный entry нуждается в Legacy identity/lifecycle решении. **RC:** [RC-07:114](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:114). **Возможный package:** —.
- **Технический/owner контракт исходной находки:** Rift; Scenario; Character. Один request_id создаёт один run.
- **Выполнено сейчас — статическое чтение:** prepare_from_scenario принимает request_id; entry создаёт runtime/session. **Прочитанные anchors:** [src/backend/features/rift/services/entry_service.py:86](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/services/entry_service.py:86).
- **Secondary gates / ограничения:** Проверка duplicate request не выполнялась; gameplay admission/instance reuse не выбирать. **Исторические ограничения:** A04-05: Совместный вход разных players не готовый подтверждённый механизм.
- **Будущая необходимая проверка (сейчас не выполнена):** A04-05: Repeat entry, crash до linkage; count/identity invariant.

### A04-06 — повторный start уничтожает прежний travel

- **Original IDs / source severity:** A04-06 — Medium; [audit/04_rift_world_generation.md:164](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:164); аудит 04. [Canonical в реестре:376](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:376).
- **Историческая доказательность:** A04-06: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Legacy (поддержка runtime неизвестна).
- **PRIMARY:** EXPERIMENTAL-LEGACY. **Почему:** Travel state admission — игровой контракт Legacy. **RC:** — (системная причина не установлена). **Возможный package:** —.
- **Технический/owner контракт исходной находки:** Rift travel; Character state. Активный travel/encounter требует отказа либо явной отмены.
- **Выполнено сейчас — статическое чтение:** start_travel_runtime строит новый travel из open target; PlayerService использует текущий runtime. **Прочитанные anchors:** [src/backend/features/rift/runtime/navigation/screen_builder.py:134](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/runtime/navigation/screen_builder.py:134), [src/backend/features/rift/runtime/navigation/screen_builder.py:347](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/runtime/navigation/screen_builder.py:347), [src/backend/features/rift/services/player_service.py:154](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/services/player_service.py:154).
- **Secondary gates / ограничения:** Не определять новую interruption/restart policy; source checks ещё не parallel replay. **Исторические ограничения:** A04-06: Статический path; runtime regression не повторён.
- **Будущая необходимая проверка (сейчас не выполнена):** A04-06: Start→combat interrupt→second start; state/status matrix.

### A04-07 — межпроцессная невоспроизводимость seed

- **Original IDs / source severity:** A04-07 — Medium; [audit/04_rift_world_generation.md:172](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:172); аудит 04. [Canonical в реестре:385](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:385).
- **Историческая доказательность:** A04-07: Исторически воспроизведено локальной проверкой/тестом исходного аудита; сейчас не повторялось. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Legacy (поддержка runtime неизвестна).
- **PRIMARY:** EXPERIMENTAL-LEGACY. **Почему:** Генератор старого Rift и его детерминизм отложены вместе с Legacy. **RC:** — (системная причина не установлена). **Возможный package:** —.
- **Технический/owner контракт исходной находки:** Rift generation; Python RNG. Seed/config задают normalized topology независимо от hash seed.
- **Выполнено сейчас — статическое чтение:** _select_branch_source строит candidates из set[str] open_node_ids и rng.choice(candidates). **Прочитанные anchors:** [src/backend/features/rift/runtime/generation/zone_instance.py:848](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/runtime/generation/zone_instance.py:848), [src/backend/features/rift/runtime/generation/zone_instance.py:857](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/runtime/generation/zone_instance.py:857).
- **Secondary gates / ограничения:** Отсутствие hash() не закрывает finding; исторический PYTHONHASHSEED probe не повторён; gen algorithm не менять. **Исторические ограничения:** A04-07: Историческая process probe; новых запусков нет; UUID исключены.
- **Будущая необходимая проверка (сейчас не выполнена):** A04-07: Same seed/config, PYTHONHASHSEED 1/2/3, normalized graph equality.

### A04-08 — Knowledge XP cap не включается

- **Original IDs / source severity:** A04-08 — High; [audit/04_rift_world_generation.md:188](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:188); аудит 04. [Canonical в реестре:394](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:394).
- **Историческая доказательность:** A04-08: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Pre-alpha.
- **PRIMARY:** MIXED. **Почему:** Подключение Knowledge cap изменит фактическую progression; это MIXED. **RC:** — (системная причина не установлена). **Возможный package:** WP-reward-once.
- **Технический/owner контракт исходной находки:** Exploration; Knowledge; Character progression. Штатный encounter path включает XP cap.
- **Выполнено сейчас — статическое чтение:** EncounterService ищет integration.redis; integration constructor получает redis, но сохраняет managers/config без self.redis; cap_rewards условный. **Прочитанные anchors:** [src/backend/features/exploration/services/encounter_service.py:46](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/exploration/services/encounter_service.py:46), [src/backend/features/exploration/integrations/encounter_integration.py:63](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/exploration/integrations/encounter_integration.py:63), [src/backend/features/exploration/services/encounter_service.py:285](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/exploration/services/encounter_service.py:285), [src/backend/features/exploration/dependencies.py:98](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/exploration/dependencies.py:98), [src/backend/features/exploration/integrations/encounter_integration.py:73](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/exploration/integrations/encounter_integration.py:73).
- **Secondary gates / ограничения:** Не активировать XP limit; сначала утвердить Knowledge behavior, затем wiring regression с frozen formulas. **Исторические ограничения:** A04-08: Количественное XP accumulation не исполнялось.
- **Будущая необходимая проверка (сейчас не выполнена):** A04-08: Штатный wiring, повтор сверх location budget, total capped.

### A04-09 — отказ перемещения игнорируется

- **Original IDs / source severity:** A04-09 — Medium; [audit/04_rift_world_generation.md:196](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:196); аудит 04. [Canonical в реестре:403](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:403).
- **Историческая доказательность:** A04-09: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha.
- **PRIMARY:** TECH-HARDENING. **Почему:** Согласование результата storage mutation и ответа — технический контракт, если не менять move rules. **RC:** — (системная причина не установлена). **Возможный package:** WP-boundary-state.
- **Технический/owner контракт исходной находки:** Exploration gateway; World; Character. Rejected move не публикует target success/encounter.
- **Выполнено сейчас — статическое чтение:** Gateway await move_player без обработки bool; SystemIntegrator возвращает False при отсутствующей target location. **Прочитанные anchors:** [src/backend/features/exploration/gateway/exploration_gateway.py:63](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/exploration/gateway/exploration_gateway.py:63), [src/backend/features/exploration/integrations/system_integrator.py:44](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/exploration/integrations/system_integrator.py:44).
- **Secondary gates / ограничения:** Preserve roll/order/game UX; только truth of response, owner error/compensation contract до implementation. **Исторические ограничения:** A04-09: No real store race; specified branch.
- **Будущая необходимая проверка (сейчас не выполнена):** A04-09: False move injection, no target encounter, actual position response.

### A04-10 — World cache не имеет полного контракта публикации

- **Original IDs / source severity:** A04-10 — Medium; [audit/04_rift_world_generation.md:204](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:204); аудит 04. [Canonical в реестре:412](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:412).
- **Историческая доказательность:** A04-10: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha.
- **PRIMARY:** TECH-HARDENING. **Почему:** Durable publication/projection существующих данных техническая; генерация карты вне scope. **RC:** [RC-09:138](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:138). **Возможный package:** WP-ai-durability.
- **Технический/owner контракт исходной находки:** World; AI handlers; SQL; Redis bootstrap. Cache publication полна/актуальна либо явно отказала.
- **Выполнено сейчас — статическое чтение:** World task apply_result работает с SQL session; warm_runtime_cache формирует full location cache; batch Redis pipeline raise_on_error=False. **Прочитанные anchors:** [src/backend/features/world/tasks_ai.py:98](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/world/tasks_ai.py:98), [src/backend/features/world/services/cache_service.py:26](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/world/services/cache_service.py:26), [src/backend/infrastructure/world/location_store.py:35](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/world/location_store.py:35).
- **Secondary gates / ограничения:** Сначала определить already-approved publication boundary; не auto-activate generated nodes/routes/content. **Исторические ограничения:** A04-10: Bootstrap rollback — дополнительный риск; actual production нет.
- **Будущая необходимая проверка (сейчас не выполнена):** A04-10: AI→Redis read, deactivate→warm, failed write/rollback.

### A04-11 — несовместимые лимиты повторов GenerationAI

- **Original IDs / source severity:** A04-11 — High; [audit/04_rift_world_generation.md:215](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:215); аудит 04. [Canonical в реестре:421](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:421).
- **Историческая доказательность:** A04-11: Исторически воспроизведено локальной проверкой/тестом исходного аудита; сейчас не повторялось. **Стадия:** Shared infrastructure (Pre-alpha).
- **PRIMARY:** TECH-HARDENING. **Почему:** Scheduler retry-state consistency техническая, конкретный budget отдельный ops contract. **RC:** — (системная причина не установлена). **Возможный package:** WP-ai-durability.
- **Технический/owner контракт исходной находки:** GenerationAI; World JSON; SQL; ARQ. Cooldown достижим следующим claim либо task terminal.
- **Выполнено сейчас — статическое чтение:** _retry_limit возвращает max(base,8) для schema error; claim SQL фильтрует attempts < max_attempts; World specs max_attempts=4. **Прочитанные anchors:** [src/backend/features/generation_ai/services.py:216](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/services.py:216), [src/backend/features/generation_ai/repositories.py:142](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/repositories.py:142), [src/backend/features/world/tasks_ai.py:169](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/world/tasks_ai.py:169).
- **Secondary gates / ограничения:** Сохранить утверждённый budget; исторический retry probe не повторён; не менять AI prompts/content. **Исторические ограничения:** A04-11: Историческая condition probe; не real SQL/ARQ; Monster limit8 не этот case.
- **Будущая необходимая проверка (сейчас не выполнена):** A04-11: Claims/errors до terminal; реальный SQL attempt predicate.

### A04-12 — первоначальный payload может быть потерян

- **Original IDs / source severity:** A04-12 — High; [audit/04_rift_world_generation.md:232](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:232); аудит 04; A05-07 — Medium; [audit/05_persistence_consistency.md:316](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:316); аудит 05. [Canonical в реестре:430](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:430).
- **Историческая доказательность:** A04-12: Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. Сейчас выборочно подтверждены только указанные статические предпосылки; A05-07: Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Shared infrastructure (Pre-alpha).
- **PRIMARY:** TECH-HARDENING. **Почему:** Accepted task обязан иметь восстанавливаемый input, без изменения generated content. **RC:** [RC-09:138](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:138). **Возможный package:** WP-ai-durability.
- **Технический/owner контракт исходной находки:** GenerationAI; World; Mongo; SQL. Accepted task имеет durable recoverable input.
- **Выполнено сейчас — статическое чтение:** Initial Mongo exception помечает write_failed и return; hydration missing document возвращает task; World/news handlers требуют input fields. **Прочитанные anchors:** [src/backend/features/generation_ai/repositories.py:221](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/repositories.py:221), [src/backend/features/generation_ai/repositories.py:249](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/repositories.py:249), [src/backend/features/world/tasks_ai.py:55](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/world/tasks_ai.py:55), [src/backend/features/generation_ai/repositories.py:228](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/repositories.py:228), [src/backend/features/generation_ai/tasks_news.py:18](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/tasks_news.py:18), [src/backend/features/generation_ai/repositories.py:234](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/repositories.py:234).
- **Secondary gates / ограничения:** A04-12 High/A05-07 Medium сохранены; real Mongo failure/recovery не запускался; не suppress initial acceptance failure. **Исторические ограничения:** A04-12: Real Mongo не проверена; severity High сохранена; A05-07: Severity Medium сохранена; material resource loss не доказана.
- **Будущая необходимая проверка (сейчас не выполнена):** A04-12: Initial outage→restart→recovery или exact rejection; A05-07: Initial write/read outages, restart; recover/reject без orphan pending.

### A04-13 — done возможен без сохранённого результата

- **Original IDs / source severity:** A04-13 — Medium; [audit/04_rift_world_generation.md:240](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:240); аудит 04. [Canonical в реестре:439](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:439).
- **Историческая доказательность:** A04-13: Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. **Стадия:** Shared infrastructure (Pre-alpha).
- **PRIMARY:** TECH-HARDENING. **Почему:** Completed status и durable result — техническая state integrity. **RC:** [RC-09:138](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:138). **Возможный package:** WP-ai-durability.
- **Технический/owner контракт исходной находки:** GenerationAI; Mongo results; SQL status. Done соответствует сохранённой task history/result.
- **Выполнено сейчас — статическое чтение:** mark_done выставляет done до _record_result_payload; запись Mongo ловит exception, write_failed и return; worker затем SQL commit. **Прочитанные anchors:** [src/backend/features/generation_ai/repositories.py:159](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/repositories.py:159), [src/backend/features/generation_ai/repositories.py:261](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/repositories.py:261), [src/backend/features/generation_ai/workers/tasks.py:31](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/workers/tasks.py:31), [src/backend/features/generation_ai/repositories.py:270](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/repositories.py:270).
- **Secondary gates / ограничения:** Утвердить technical completion guarantee; внешняя генерация/asset policy неизменна; сейчас static ordering. **Исторические ограничения:** A04-13: Уже применённый игровой контент не объявлен потерянным.
- **Будущая необходимая проверка (сейчас не выполнена):** A04-13: Result outage после apply, SQL status и payload availability.

### A04-14 — статический аудит World сломан

- **Original IDs / source severity:** A04-14 — Low; [audit/04_rift_world_generation.md:248](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:248); аудит 04. [Canonical в реестре:448](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:448).
- **Историческая доказательность:** A04-14: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Dev-only.
- **PRIMARY:** TECH-HARDENING. **Почему:** Dev diagnostic tool signature drift можно исправлять технически без генератора redesign. **RC:** — (системная причина не установлена). **Возможный package:** WP-test-controls.
- **Технический/owner контракт исходной находки:** World local audit tool. CLI вызывает актуальную constructor signature.
- **Выполнено сейчас — статическое чтение:** world_static_audit.py вызывает LLMWorldGenerator(data,ai=None); текущий constructor принимает generation_ai. **Прочитанные anchors:** [tools/world_static_audit.py:230](D:/Workspace/personal/pets/TurnBasedMMORPG/tools/world_static_audit.py:230), [src/backend/features/world/services/generator_service.py:165](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/world/services/generator_service.py:165).
- **Secondary gates / ограничения:** Не запускать tool и не менять generated topology; будущий smoke ограничить static harness. **Исторические ограничения:** A04-14: Full CLI не завершился; signatures сравнивались.
- **Будущая необходимая проверка (сейчас не выполнена):** A04-14: Bounded tool constructor/invariants после разрешения env.

### A04-15 — Два обработчика результата читают одинаковый active_encounter_id и независимо сохраняют instance/session. Barrier-test параллельных finalizer/return должен подтвердить одно логическое применение

- **Original IDs / source severity:** A04-15 — High; [audit/04_rift_world_generation.md:314](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:314); аудит 04. [Canonical в реестре:457](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:457).
- **Историческая доказательность:** A04-15: Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Legacy (поддержка runtime неизвестна).
- **PRIMARY:** EXPERIMENTAL-LEGACY. **Почему:** Parallel completion применим к Legacy; общий cause не превращает в разрешённый package. **RC:** [RC-08:126](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:126). **Возможный package:** —.
- **Технический/owner контракт исходной находки:** Rift; Combat completion. Один encounter применяет один logical result.
- **Выполнено сейчас — статическое чтение:** Rift apply читает session и сравнивает encounter before later mutation. **Прочитанные anchors:** [src/backend/features/rift/integrations/runtime.py:410](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/integrations/runtime.py:410).
- **Secondary gates / ограничения:** Existing guards не full atomic proof; Legacy decision и real Redis barrier до work. **Исторические ограничения:** A04-15: Guard sequential no-op; concurrency не воспроизведена.
- **Будущая необходимая проверка (сейчас не выполнена):** A04-15: Parallel finalizer/return barriers; crash после session save.

### A04-16 — XP сердца начисляется до записи завершения и очистки ссылок. Инъекция ошибки после начисления и повтор complete должны доказать отсутствие второй награды

- **Original IDs / source severity:** A04-16 — High; [audit/04_rift_world_generation.md:315](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:315); аудит 04. [Canonical в реестре:466](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:466).
- **Историческая доказательность:** A04-16: Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Legacy (поддержка runtime неизвестна).
- **PRIMARY:** EXPERIMENTAL-LEGACY. **Почему:** Повтор heart reward зависит от Legacy outcome и once contract. **RC:** [RC-07:114](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:114). **Возможный package:** —.
- **Технический/owner контракт исходной находки:** Rift heart completion; progression. Heart XP применён один раз при повторе/fault.
- **Выполнено сейчас — статическое чтение:** Exit применяет _apply_symbiote_reward до save_run_session/portal marker. **Прочитанные anchors:** [src/backend/features/rift/services/player_service.py:192](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/services/player_service.py:192).
- **Secondary gates / ограничения:** Legacy + MIXED secondary: единица reward application утверждается отдельно, XP values заморожены. **Исторические ограничения:** A04-16: Нормальный fully completed repeat не объявлен уязвимым.
- **Будущая необходимая проверка (сейчас не выполнена):** A04-16: Error сразу после XP, retry/concurrent complete, cumulative delta.

### A04-17 — Между snapshot write и clear_dirty приходит новое движение. Новая dirty revision должна сохраниться

- **Original IDs / source severity:** A04-17 — Medium; [audit/04_rift_world_generation.md:316](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:316); аудит 04; A05-09 — Medium; [audit/05_persistence_consistency.md:332](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:332); аудит 05. [Canonical в реестре:475](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:475).
- **Историческая доказательность:** A04-17: Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. Сейчас выборочно подтверждены только указанные статические предпосылки; A05-09: Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Legacy (поддержка runtime неизвестна).
- **PRIMARY:** EXPERIMENTAL-LEGACY. **Почему:** Snapshot clear window находится в Legacy storage. **RC:** [RC-08:126](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:126). **Возможный package:** —.
- **Технический/owner контракт исходной находки:** Rift checkpoint; Redis; Mongo; SQL. Snapshot G ack не очищает dirty G+1.
- **Выполнено сейчас — статическое чтение:** flush_dirty_run_session capture→flush_runtime_snapshot→clear_dirty без generation аргумента; manager mark_dirty writes marker отдельно. **Прочитанные anchors:** [src/backend/features/rift/integrations/runtime.py:287](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/integrations/runtime.py:287), [src/backend/infrastructure/rift/managers/session.py:115](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/rift/managers/session.py:115), [src/backend/features/rift/integrations/runtime.py:297](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/integrations/runtime.py:297).
- **Secondary gates / ограничения:** A04-17/A05-09 полный дубль; historical stronger failure window, не real Redis proof; support gate. **Исторические ограничения:** A04-17: Исторический risk; более позднее статическое window в A05-09; A05-09: No real Redis repro; window статически установлено.
- **Будущая необходимая проверка (сейчас не выполнена):** A04-17: Mutation barrier, dirty/new revision survives; two flush; A05-09: Mutation barrier, two flush workers, non-regressing snapshot.

### A04-18 — После SQL commit не выполняется ARQ enqueue; либо asset/Mongo write выполнен, а SQL откатился. Проверить recovery очереди и очистку несвязанных результатов

- **Original IDs / source severity:** A04-18 — Medium; [audit/04_rift_world_generation.md:317](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:317); аудит 04. [Canonical в реестре:484](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:484).
- **Историческая доказательность:** A04-18: Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Shared infrastructure (Pre-alpha).
- **PRIMARY:** VERIFY-FIRST. **Почему:** Orphan assets и commit/enqueue шире одного доказанного эффекта; нужна раздельная проверка. **RC:** [RC-09:138](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:138), [RC-10:150](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:150). **Возможный package:** WP-ai-durability.
- **Технический/owner контракт исходной находки:** GenerationAI; Assets; Mongo; SQL; ARQ. Committed task queued; external results имеют reconciliation.
- **Выполнено сейчас — статическое чтение:** Worker SQL commit перед schedule_pending_task_ids; service очищает local pending list перед await scheduling. **Прочитанные anchors:** [src/backend/features/generation_ai/workers/tasks.py:33](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/workers/tasks.py:33), [src/backend/features/generation_ai/services.py:169](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/services.py:169), [src/backend/features/generation_ai/repositories.py:55](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/repositories.py:55).
- **Secondary gates / ограничения:** VERIFY-FIRST для всей записи; scheduling часть покрывает A05-08, orphan object cleanup не вводить без recovery/retention contract. **Исторические ограничения:** A04-18: Broad две границы; не все orphan effects воспроизведены.
- **Будущая необходимая проверка (сейчас не выполнена):** A04-18: Enqueue fault/restart, orphan asset/document reconciliation.

### A04-19 — У внешнего WorldRegionNodeGenerator road_cells пуст, тогда как межрегиональный выход требует дороги с обеих сторон. Проверять при подключении; это не поломка доступного сейчас D4

- **Original IDs / source severity:** A04-19 — Medium; [audit/04_rift_world_generation.md:318](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:318); аудит 04. [Canonical в реестре:493](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:493).
- **Историческая доказательность:** A04-19: Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Pre-alpha (неподключённый генератор).
- **PRIMARY:** GAME-DESIGN. **Почему:** World connected roads/region reachability — topology/game design, исключено. **RC:** — (системная причина не установлена). **Возможный package:** —.
- **Технический/owner контракт исходной находки:** WorldRegionNodeGenerator; World roads. External region crossing требует road on both sides.
- **Выполнено сейчас — статическое чтение:** Node generator формирует road_cells/route plan; navigation требует road с обеих сторон cross-region. **Прочитанные anchors:** [src/backend/features/world/runtime/node_graph.py:49](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/world/runtime/node_graph.py:49), [src/backend/features/world/services/navigation_service.py:84](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/world/services/navigation_service.py:84).
- **Secondary gates / ограничения:** Не исправлять карту, дороги, геометрию или допуск маршрутов. **Исторические ограничения:** A04-19: Current D4 этим не сломан; закрытые gates могут быть intended.
- **Будущая необходимая проверка (сейчас не выполнена):** A04-19: Road reciprocity/boundaries при реальном подключении.

### A04-20 — Hex movement проверяет соседство и walkable, но не edge masks; ответы действий возвращают полный state. Старый next_floor расходится с текущим single-floor heart layout

- **Original IDs / source severity:** A04-20 — Low; [audit/04_rift_world_generation.md:319](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:319); аудит 04. [Canonical в реестре:502](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:502).
- **Историческая доказательность:** A04-20: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Experimental / Dev-only.
- **PRIMARY:** EXPERIMENTAL-LEGACY. **Почему:** Hex masks/next-floor — Experimental/Dev-only и запрещённая игровая геометрия. **RC:** — (системная причина не установлена). **Возможный package:** —.
- **Технический/owner контракт исходной находки:** Hex prototype; movement; next_floor. Dev contract согласует masks/state/single-floor heart.
- **Выполнено сейчас — статическое чтение:** Hex runtime move проверяет neighbors/active combat; hex test route публикует action; builder задаёт required entrance/heart slots. **Прочитанные anchors:** [src/backend/features/rift/services/hex_runtime_service.py:104](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/services/hex_runtime_service.py:104), [src/backend/features/rift/api/hex_test_router.py:84](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/api/hex_test_router.py:84), [src/backend/features/rift/runtime/hex/generation/builder.py:2486](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/runtime/hex/generation/builder.py:2486).
- **Secondary gates / ограничения:** Только surface isolation разрешена через A08-04; generation/masks/floors deferred. **Исторические ограничения:** A04-20: Tests фиксируют single-floor; не production blocker.
- **Будущая необходимая проверка (сейчас не выполнена):** A04-20: Edges/masks, state projection, single-floor/next_floor owner decision.

### A04-21 — Exploration local map помечает существующие соседние локации известными без обращения к персональному knowledge. Дефект только при требовании персонального тумана войны

- **Original IDs / source severity:** A04-21 — Не присвоена; [audit/04_rift_world_generation.md:320](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/04_rift_world_generation.md:320); аудит 04. [Canonical в реестре:511](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:511).
- **Историческая доказательность:** A04-21: Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Pre-alpha.
- **PRIMARY:** GAME-DESIGN. **Почему:** Fog/unknown local map — ещё не утверждённый UX/game contract. **RC:** — (системная причина не установлена). **Возможный package:** —.
- **Технический/owner контракт исходной находки:** Exploration local map; Knowledge; product policy. Персональный fog-of-war только при утверждённом требовании.
- **Выполнено сейчас — статическое чтение:** build_local_map ограничивает radius1–4 и строит map вокруг текущих coords. **Прочитанные anchors:** [src/backend/features/exploration/services/navigation_service.py:105](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/exploration/services/navigation_service.py:105).
- **Secondary gates / ограничения:** Severity не присвоена в источнике; не выбирать discovery/reveal policy в hardening. **Исторические ограничения:** A04-21: Severity не присвоена; обязательный current fog contract не установлен.
- **Будущая необходимая проверка (сейчас не выполнена):** A04-21: Уточнить contract; known/unknown fixtures после решения.

### A05-01 — Safe loot claim не сохраняет количество ресурсов при повторе

- **Original IDs / source severity:** A05-01 — High; [audit/05_persistence_consistency.md:268](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:268); аудит 05. [Canonical в реестре:522](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:522).
- **Историческая доказательность:** A05-01: Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. **Стадия:** Pre-alpha.
- **PRIMARY:** MIXED. **Почему:** Safe/unsafe claim once/conservation касается reward entitlement; сначала owner unit of application. **RC:** [RC-07:114](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:114). **Возможный package:** WP-reward-once.
- **Технический/owner контракт исходной находки:** Loot; Inventory; Expedition; SQL; Redis. Выдано не больше source debit; claim один раз.
- **Выполнено сейчас — статическое чтение:** Unsafe branch проверяет processed claim_key; safe branch начисляет запрошенные resource_deltas в wallet; helper consumption вызван отдельно. **Прочитанные anchors:** [src/backend/features/loot/workers/tasks/loot_claim_task.py:203](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/loot/workers/tasks/loot_claim_task.py:203).
- **Secondary gates / ограничения:** MIXED; не менять economy/amounts/source eligibility; запросить once contract и actual-consumption conservation, replay сейчас не выполнен. **Исторические ограничения:** A05-01: Row lock сериализует, но не conservation; real PG repro нет.
- **Будущая необходимая проверка (сейчас не выполнена):** A05-01: Duplicate/two claimants, insufficient source, first batch commit fault.

### A05-02 — Loot SQL transfer не проверяет точный источник предмета

- **Original IDs / source severity:** A05-02 — High; [audit/05_persistence_consistency.md:276](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:276); аудит 05. [Canonical в реестре:531](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:531).
- **Историческая доказательность:** A05-02: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha.
- **PRIMARY:** TECH-HARDENING. **Почему:** Источник custody и успех SQL transition должны подтверждать permission, не менять loot table. **RC:** — (системная причина не установлена). **Возможный package:** WP-loot-transfer.
- **Технический/owner контракт исходной находки:** Loot; Items; Inventory. Transfer exact SQL holder; success соответствует rowcount.
- **Выполнено сейчас — статическое чтение:** UPDATE ItemPlacement ограничен item_ids и holder_type list; exact corpse holder_id и affected rowcount в write block отсутствуют. **Прочитанные anchors:** [src/backend/features/loot/workers/tasks/loot_claim_task.py:213](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/loot/workers/tasks/loot_claim_task.py:213), [src/backend/features/loot/services/loot_service.py:332](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/loot/services/loot_service.py:332).
- **Secondary gates / ограничения:** Owner утверждает allowed source transitions; preserve single SQL UoW и частичный rollback; не сменить entitlement policy. **Исторические ограничения:** A05-02: PK предотвращает duplicate row, не неправильный transfer.
- **Будущая необходимая проверка (сейчас не выполнена):** A05-02: Other corpse/system, zero-row transfer, two claimants.

### A05-03 — Inventory snapshot/flush не сериализованы

- **Original IDs / source severity:** A05-03 — Medium; [audit/05_persistence_consistency.md:284](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:284); аудит 05. [Canonical в реестре:540](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:540).
- **Историческая доказательность:** A05-03: Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. **Стадия:** Pre-alpha.
- **PRIMARY:** TECH-HARDENING. **Почему:** Revision-safe persistence сохраняет уже выполненную inventory action. **RC:** [RC-08:126](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:126). **Возможный package:** WP-inventory-sync.
- **Технический/owner контракт исходной находки:** Inventory; Character; Redis; SQL. Accepted action не стирается чужой action/flush.
- **Выполнено сейчас — статическое чтение:** Manager get читает $, set пишет весь DTO; worker читает snapshot, flush_session, затем separate clear_dirty. **Прочитанные anchors:** [src/backend/features/inventory/services/inventory_service.py:84](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/inventory/services/inventory_service.py:84), [src/backend/infrastructure/inventory/managers/session.py:20](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/inventory/managers/session.py:20), [src/backend/features/inventory/workers/tasks/session_tasks.py:22](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/inventory/workers/tasks/session_tasks.py:22), [src/backend/features/inventory/workers/tasks/session_tasks.py:39](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/inventory/workers/tasks/session_tasks.py:39).
- **Secondary gates / ограничения:** Current static interleaving window, не real concurrent store proof; equip/loadout semantics заморожены. **Исторические ограничения:** A05-03: Interleaving не запускался; item duplication не доказана.
- **Будущая необходимая проверка (сейчас не выполнена):** A05-03: Action/action, action/flush barriers, next sweep SQL/AC.

### A05-04 — Death corpse публикуется до SQL commit, repair неполон

- **Original IDs / source severity:** A05-04 — Medium; [audit/05_persistence_consistency.md:292](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:292); аудит 05. [Canonical в реестре:549](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:549).
- **Историческая доказательность:** A05-04: Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. **Стадия:** Pre-alpha.
- **PRIMARY:** MIXED. **Почему:** Corpse/death recovery затрагивает потери/expiry и reward source, требуется owner. **RC:** [RC-09:138](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:138). **Возможный package:** WP-reward-once.
- **Технический/owner контракт исходной находки:** Expedition; Loot; Character. Corpse имеет committed source и rebuild до expiry.
- **Выполнено сейчас — статическое чтение:** Expedition moves items/resources и выставляет corpse metadata; этот прочитанный SQL block не проверяет всю Redis/SQL recovery chain. **Прочитанные anchors:** [src/backend/features/expedition/service.py:238](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/expedition/service.py:238).
- **Secondary gates / ограничения:** MIXED; сначала approved death/restore/retention contract; не менять penalties/corpse visibility/drop logic. **Исторические ограничения:** A05-04: Штатный expiry не дефект; real fault нет.
- **Будущая необходимая проверка (сейчас не выполнена):** A05-04: Commit failure after Redis save; loss before expires_at; retry same contents.

### A05-05 — Streams pending не восстанавливаются

- **Original IDs / source severity:** A05-05 — High; [audit/05_persistence_consistency.md:300](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:300); аудит 05. [Canonical в реестре:558](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:558).
- **Историческая доказательность:** A05-05: Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. **Стадия:** Shared infrastructure (Pre-alpha / Legacy).
- **PRIMARY:** TECH-HARDENING. **Почему:** Техническая PEL recovery должна сохранять уже approved business effect и versioned bus contract. **RC:** [RC-10:150](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:150). **Возможный package:** WP-stream-recovery.
- **Технический/owner контракт исходной находки:** Core bus consumers; codex-platform; Redis. Accepted message завершён либо retry/DLQ доступен.
- **Выполнено сейчас — статическое чтение:** Installed processor читает read_events и ACK после callback; installed consumer xreadgroup streams=«>»; producer xtrim(maxlen). **Прочитанные anchors:** [src/backend/core/containers/redis.py:136](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/core/containers/redis.py:136), [.venv/Lib/site-packages/codex_platform/streams/processor.py:180](D:/Workspace/personal/pets/TurnBasedMMORPG/.venv/Lib/site-packages/codex_platform/streams/processor.py:180), [src/backend/core/bus/producer.py:60](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/core/bus/producer.py:60), [.venv/Lib/site-packages/codex_platform/streams/consumer.py:96](D:/Workspace/personal/pets/TurnBasedMMORPG/.venv/Lib/site-packages/codex_platform/streams/consumer.py:96).
- **Secondary gates / ограничения:** Source authority библиотеки вне repo; installed bytes не production proof; reclaim без consumer idempotency сначала forbidden. **Исторические ограничения:** A05-05: Installed dependency examined; prod version неизвестна.
- **Будущая необходимая проверка (сейчас не выполнена):** A05-05: Real Redis before/after effect, restart, XPENDING/retention, dedup.

### A05-06 — Chat archive cursor пропускает неуспешную запись

- **Original IDs / source severity:** A05-06 — High; [audit/05_persistence_consistency.md:308](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:308); аудит 05. [Canonical в реестре:567](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:567).
- **Историческая доказательность:** A05-06: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha.
- **PRIMARY:** TECH-HARDENING. **Почему:** Cursor обязан отражать durable acknowledged prefix; это storage contract. **RC:** [RC-09:138](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:138). **Возможный package:** WP-chat-archive.
- **Технический/owner контракт исходной находки:** Chat; Redis; Mongo; SQL. Checkpoint не обходит failed original body.
- **Выполнено сейчас — статическое чтение:** Archive new_last_id обновляется до try, ошибка учитывается и loop продолжается, итоговый cursor пишется после loop. **Прочитанные anchors:** [src/backend/chat/workers/archive.py:44](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/chat/workers/archive.py:44), [src/backend/chat/api/router.py:112](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/chat/api/router.py:112), [src/backend/chat/services/message_service.py:42](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/chat/services/message_service.py:42), [src/backend/chat/workers/archive.py:57](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/chat/workers/archive.py:57).
- **Secondary gates / ограничения:** Future fail→later success/poison replay с настоящими Redis/Mongo/PG; не менять chat UX/retention. **Исторические ограничения:** A05-06: Visible broadcast не durable acceptance; no real outage.
- **Будущая необходимая проверка (сейчас не выполнена):** A05-06: One-off Nth failure→retry, all bodies unique IDs; XADD failure.

### A05-08 — GenerationAI pending/cooldown теряется между commit и enqueue

- **Original IDs / source severity:** A05-08 — Medium; [audit/05_persistence_consistency.md:324](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:324); аудит 05. [Canonical в реестре:585](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:585).
- **Историческая доказательность:** A05-08: Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. **Стадия:** Shared infrastructure (Pre-alpha).
- **PRIMARY:** TECH-HARDENING. **Почему:** Commit и job-delivery необходимо связать durable recovery, не новыми AI задачами. **RC:** [RC-10:150](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:150). **Возможный package:** WP-ai-durability.
- **Технический/owner контракт исходной находки:** GenerationAI; SQL; ARQ Redis. Committed schedulable row eventually получает job.
- **Выполнено сейчас — статическое чтение:** Generation API enqueue_many→SQL commit→schedule_pending; worker process→commit→schedule pending. **Прочитанные anchors:** [src/backend/features/generation_ai/api.py:52](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/api.py:52), [src/backend/features/generation_ai/workers/tasks.py:32](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/workers/tasks.py:32).
- **Secondary gates / ограничения:** ARQ failures/restart не воспроизводились; minimal durable obligation candidate, content and retry budget preserved. **Исторические ограничения:** A05-08: Manual resend может помочь; real runtime recovery не запускался.
- **Будущая необходимая проверка (сейчас не выполнена):** A05-08: Kill after commit, enqueue/follow-up fault, due-row replay.

### A05-10 — Rift restore считает instance достаточным и перезаписывает живые sessions

- **Original IDs / source severity:** A05-10 — Medium; [audit/05_persistence_consistency.md:340](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:340); аудит 05. [Canonical в реестре:603](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:603).
- **Историческая доказательность:** A05-10: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Legacy (поддержка runtime неизвестна).
- **PRIMARY:** EXPERIMENTAL-LEGACY. **Почему:** Partial snapshot restore — Legacy persistence admission. **RC:** [RC-09:138](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:138). **Возможный package:** —.
- **Технический/owner контракт исходной находки:** Rift; Redis; Mongo; SQL membership. Restore missing component не игнорирует и не затирает newer live.
- **Выполнено сейчас — статическое чтение:** require_run_session восстанавливает instance через membership при missing Redis session; create_session пишет whole payload. **Прочитанные anchors:** [src/backend/features/rift/integrations/runtime.py:172](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/integrations/runtime.py:172), [src/backend/infrastructure/rift/managers/session.py:25](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/rift/managers/session.py:25).
- **Secondary gates / ограничения:** Нельзя выбирать новую recreate/reward policy; support/restore completeness gate до work. **Исторические ограничения:** A05-10: Rewards duplication не доказана; independent component TTL.
- **Будущая необходимая проверка (сейчас не выполнена):** A05-10: Each-key expiry, S0/S1, interrupted SETs, repeat restore.

### A05-11 — Archive reader обращается к несуществующему SQL payload

- **Original IDs / source severity:** A05-11 — Medium; [audit/05_persistence_consistency.md:348](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:348); аудит 05. [Canonical в реестре:612](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:612).
- **Историческая доказательность:** A05-11: Исторически воспроизведено локальной проверкой/тестом исходного аудита; сейчас не повторялось. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Pre-alpha.
- **PRIMARY:** TECH-HARDENING. **Почему:** Archive reader должен соответствовать уже существующей SQL/Mongo storage schema. **RC:** — (системная причина не установлена). **Возможный package:** WP-combat-readback.
- **Технический/owner контракт исходной находки:** Combat result archive; Redis; SQL; Mongo. Persisted full archive читается после cache/runtime loss.
- **Выполнено сейчас — статическое чтение:** _load_from_db возвращает row.finalization; model CombatFinalization содержит SQL metadata и Mongo pointer/status, но не поле finalization; fallback suppress(Exception). **Прочитанные anchors:** [src/backend/features/combat/services/result_archive_service.py:147](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/services/result_archive_service.py:147), [src/backend/infrastructure/combat/models/finalization.py:12](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/combat/models/finalization.py:12), [src/backend/features/combat/services/result_archive_service.py:37](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/services/result_archive_service.py:37), [src/backend/infrastructure/combat/models/finalization.py:35](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/combat/models/finalization.py:35).
- **Secondary gates / ограничения:** Reader/model drift требует field-schema check и real archive cold-read; никаких новых combat result semantics. **Исторические ограничения:** A05-11: Историческая ORM probe, не e2e; reward data loss не доказана.
- **Будущая необходимая проверка (сейчас не выполнена):** A05-11: Persist→delete Redis→read report; Mongo outage/missing pointer.

### A05-12 — Site refresh rotation имеет два commits

- **Original IDs / source severity:** A05-12 — Medium; [audit/05_persistence_consistency.md:356](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:356); аудит 05. [Canonical в реестре:621](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:621).
- **Историческая доказательность:** A05-12: Подтверждён failure window по исходному отчёту; реальное межхранилищное воспроизведение не выполнено. **Стадия:** Pre-alpha.
- **PRIMARY:** TECH-HARDENING. **Почему:** Atomic refresh rotation — technical auth lifecycle без игровых последствий. **RC:** [RC-08:126](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:126). **Возможный package:** WP-session-lifecycle.
- **Технический/owner контракт исходной находки:** Site Auth; refresh; PostgreSQL. Rotation фиксирует old→new одной durable operation.
- **Выполнено сейчас — статическое чтение:** Site refresh delete_refresh_token затем create_tokens; persistence delete/create каждый вызывает commit. **Прочитанные anchors:** [src/frontend/features/auth/services/site_auth_service.py:124](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/features/auth/services/site_auth_service.py:124), [src/frontend/features/auth/integrations/auth_persistence.py:67](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/features/auth/integrations/auth_persistence.py:67), [src/frontend/features/auth/repositories/token_repository.py:25](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/features/auth/repositories/token_repository.py:25).
- **Secondary gates / ограничения:** Single-session/replay/failure tests будущие; existing site token contract preserve, common logout отдельно. **Исторические ограничения:** A05-12: Threshold7d снижает частоту; security compromise не заявляется.
- **Будущая необходимая проверка (сейчас не выполнена):** A05-12: Fail new insert, concurrent threshold refresh, lost response retry.

### A05-13 — Site clean migration конфликтует с live ORM baseline

- **Original IDs / source severity:** A05-13 — High; [audit/05_persistence_consistency.md:364](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:364); аудит 05. [Canonical в реестре:630](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:630).
- **Историческая доказательность:** A05-13: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha; intended Production).
- **PRIMARY:** TECH-HARDENING. **Почему:** Fresh schema reproducibility — техническая migration contract. **RC:** — (системная причина не установлена). **Возможный package:** WP-site-migrations.
- **Технический/owner контракт исходной находки:** Site migrations; ORM; deployment. Historical migrations reproducibly строят empty schema.
- **Выполнено сейчас — статическое чтение:** 0001 импортирует live Base и create_all; RefreshToken содержит token_hash;0002 добавляет token_hash и читает старую token колонку. **Прочитанные anchors:** [src/frontend/alembic/versions/0001_site_schema_baseline.py:12](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/alembic/versions/0001_site_schema_baseline.py:12), [src/frontend/features/auth/models/refresh_token.py:15](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/features/auth/models/refresh_token.py:15), [src/frontend/alembic/versions/0002_security_baseline.py:22](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/alembic/versions/0002_security_baseline.py:22), [src/frontend/alembic/versions/0001_site_schema_baseline.py:24](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/alembic/versions/0001_site_schema_baseline.py:24).
- **Secondary gates / ограничения:** Static source mismatch confirmed; ORM introspection историческая, clean PG migration сейчас не запускалась; data loss avoided. **Исторические ограничения:** A05-13: Real migration не запускалась; prod schema unknown; blind stamp/drop недопустим.
- **Будущая необходимая проверка (сейчас не выполнена):** A05-13: Empty PG upgrade, old schema upgrade, repeat head, schema diff.

### A05-14 — Конкурентное создание двух active Expedition

- **Original IDs / source severity:** A05-14 — Medium; [audit/05_persistence_consistency.md:374](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:374); аудит 05. [Canonical в реестре:639](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:639).
- **Историческая доказательность:** A05-14: Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Pre-alpha.
- **PRIMARY:** VERIFY-FIRST. **Почему:** No-row locking hypothesis требует проверить реальный unique/concurrency invariant и owner lifecycle. **RC:** — (системная причина не установлена). **Возможный package:** WP-loot-transfer.
- **Технический/owner контракт исходной находки:** Expedition; Inventory; SQL; Redis. Один live run на character.
- **Выполнено сейчас — статическое чтение:** Expedition get_active_run(for_update=True) при None создаёт active run; repository select-with-lock существует. **Прочитанные anchors:** [src/backend/features/expedition/service.py:85](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/expedition/service.py:85), [src/backend/features/expedition/repository.py:25](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/expedition/repository.py:25).
- **Secondary gates / ограничения:** VERIFY-FIRST; constraints и actual duplicate create не доказаны; не вводить новую expedition policy. **Исторические ограничения:** A05-14: No-row lock не найден; полный entrypoint serialization неизвестен.
- **Будущая необходимая проверка (сейчас не выполнена):** A05-14: Two real SQL sessions barrier no-row, lifecycle both runs.

### A05-15 — Mongo chat append/seq не доказан конкурентно и повторно корректным

- **Original IDs / source severity:** A05-15 — Medium; [audit/05_persistence_consistency.md:382](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/05_persistence_consistency.md:382); аудит 05. [Canonical в реестре:648](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:648).
- **Историческая доказательность:** A05-15: Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Pre-alpha.
- **PRIMARY:** VERIFY-FIRST. **Почему:** Mongo append dedup/seq/update-operator поведение нельзя подтвердить doubles. **RC:** — (системная причина не установлена). **Возможный package:** WP-chat-archive.
- **Технический/owner контракт исходной находки:** Chat; Mongo; SQL message index. message_id/seq однозначны при replay/concurrency.
- **Выполнено сейчас — статическое чтение:** append_message читает count, вычисляет seq и затем find_one_and_update в отдельной операции. **Прочитанные anchors:** [src/backend/infrastructure/mongo/chat_buckets.py:48](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/mongo/chat_buckets.py:48).
- **Secondary gates / ограничения:** VERIFY-FIRST; real Mongo server/version/parallel same-message probe будущие; standalone не объединён с payload amplification A09-08. **Исторические ограничения:** A05-15: Single worker уменьшает одну гонку; exact Mongo response не измерен.
- **Будущая необходимая проверка (сейчас не выполнена):** A05-15: Real Mongo first insert, concurrent append/replay, bucket boundary.

### A06-01 — Сломанная collection после удаления script

- **Original IDs / source severity:** A06-01 — High; [audit/06_testing_quality.md:381](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/06_testing_quality.md:381); аудит 06. [Canonical в реестре:659](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:659).
- **Историческая доказательность:** A06-01: Исторически воспроизведено локальной проверкой/тестом исходного аудита; сейчас не повторялось. **Стадия:** Shared infrastructure (Pre-alpha).
- **PRIMARY:** TECH-HARDENING. **Почему:** Collection linkage нужно восстановить технически, не реанимировать removed app feature. **RC:** [RC-13:186](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:186), [RC-17:234](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:234). **Возможный package:** WP-test-controls.
- **Технический/owner контракт исходной находки:** Tests; GenerationAI collection. Обязательный test set импортируется полностью.
- **Выполнено сейчас — статическое чтение:** test_asset_backfill импортирует scripts.backfill_generated_assets_to_s3; scripts directory отсутствует в текущем tree. **Прочитанные anchors:** [tests/backend/features/generation_ai/test_asset_backfill.py:6](D:/Workspace/personal/pets/TurnBasedMMORPG/tests/backend/features/generation_ai/test_asset_backfill.py:6), [pyproject.toml:154](D:/Workspace/personal/pets/TurnBasedMMORPG/pyproject.toml:154).
- **Secondary gates / ограничения:** Collection command сейчас не запускалась; будущий fix выберет intended replacement/remove obsolete test scope явно. **Исторические ограничения:** A06-01: Исторический collection; не new full run; --ignore не remedy contract.
- **Будущая необходимая проверка (сейчас не выполнена):** A06-01: Clean pytest collect-only0, backfill actual owner entrypoint.

### A06-02 — Regression test parry не активирует проверяемый trigger

- **Original IDs / source severity:** A06-02 — High; [audit/06_testing_quality.md:391](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/06_testing_quality.md:391); аудит 06. [Canonical в реестре:668](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:668).
- **Историческая доказательность:** A06-02: Исторически воспроизведено локальной проверкой/тестом исходного аудита; сейчас не повторялось. **Стадия:** Shared infrastructure (Pre-alpha).
- **PRIMARY:** TECH-HARDENING. **Почему:** Strengthen trigger test preconditions разрешено, менять боевые effects нельзя. **RC:** [RC-12:174](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:174). **Возможный package:** WP-test-controls.
- **Технический/owner контракт исходной находки:** Combat regression tests; Engine triggers. Negative effect assertion достигает fired trigger precondition.
- **Выполнено сейчас — статическое чтение:** Fixture rolls задан списком; resolver crit раньше parry; trigger_activator отдельно roll_chance для chance. **Прочитанные anchors:** [tests/backend/features/combat/test_runtime_processors.py:5556](D:/Workspace/personal/pets/TurnBasedMMORPG/tests/backend/features/combat/test_runtime_processors.py:5556), [src/backend/features/combat/runtime/engine/resolver/orchestrator.py:47](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/engine/resolver/orchestrator.py:47), [src/backend/features/combat/runtime/engine/resolver/support/trigger_activator.py:161](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/engine/resolver/support/trigger_activator.py:161).
- **Secondary gates / ограничения:** Freeze owner-approved expectation и assert activation; не «исправлять» A03-13 resolver semantics, historical probe not rerun. **Исторические ограничения:** A06-02: Исторический controlled probe assertion fail; wrapper exit0 не pass.
- **Будущая необходимая проверка (сейчас не выполнена):** A06-02: Fired/attempted assertions, hit positive control, parry/no-effect, tokens.

### A06-03 — Нет доказательной защиты реальных storage/broker contracts

- **Original IDs / source severity:** A06-03 — High; [audit/06_testing_quality.md:401](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/06_testing_quality.md:401); аудит 06. [Canonical в реестре:677](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:677).
- **Историческая доказательность:** A06-03: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha / Legacy).
- **PRIMARY:** TECH-HARDENING. **Почему:** Real boundary harness закрывает test-evidence gap, не меняет rules. **RC:** [RC-12:174](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:174). **Возможный package:** WP-storage-harness.
- **Технический/owner контракт исходной находки:** Test adapters; SQL; RedisJSON; Mongo; Streams. Server-dependent contracts имеют representative real boundary proof.
- **Выполнено сейчас — статическое чтение:** FakeRedisClient хранит dict и pipeline fake; Item tests FakeSession; Scenario AsyncMock session. **Прочитанные anchors:** [tests/backend/conftest.py:10](D:/Workspace/personal/pets/TurnBasedMMORPG/tests/backend/conftest.py:10), [tests/backend/features/items/test_instance_repository.py:16](D:/Workspace/personal/pets/TurnBasedMMORPG/tests/backend/features/items/test_instance_repository.py:16), [tests/backend/features/scenario/test_scenario_repository.py:12](D:/Workspace/personal/pets/TurnBasedMMORPG/tests/backend/features/scenario/test_scenario_repository.py:12).
- **Secondary gates / ограничения:** No new harness/tests run now; будущие RedisJSON/Streams/SQL/Mongo contract checks isolate data. **Исторические ограничения:** A06-03: External private harness не искался; absence tests не defect proof.
- **Будущая необходимая проверка (сейчас не выполнена):** A06-03: Disposable server SQL rollback/source, Redis roundtrip/fault, Mongo/index, Streams reclaim.

### A06-04 — Lifecycle tests не защищают retry/fault invariants наград и восстановления

- **Original IDs / source severity:** A06-04 — High; [audit/06_testing_quality.md:411](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/06_testing_quality.md:411); аудит 06. [Canonical в реестре:686](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:686).
- **Историческая доказательность:** A06-04: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha / Legacy).
- **PRIMARY:** TECH-HARDENING. **Почему:** Lifecycle retry/fault coverage — техническая проверка уже утверждённых contracts. **RC:** [RC-12:174](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:174). **Возможный package:** WP-test-controls.
- **Технический/owner контракт исходной находки:** Lifecycle tests; Combat; Rift; GenerationAI. Replay/fault/restart часть contract многошагового effect.
- **Выполнено сейчас — статическое чтение:** VictoryFinalizer/ExperienceFinalizer/Lifecycle tests используют fake services/queue/store и single-call positive assertions. **Прочитанные anchors:** [tests/backend/features/combat/test_victory_finalizer_task.py:175](D:/Workspace/personal/pets/TurnBasedMMORPG/tests/backend/features/combat/test_victory_finalizer_task.py:175), [tests/backend/features/combat/test_experience_finalizer.py:229](D:/Workspace/personal/pets/TurnBasedMMORPG/tests/backend/features/combat/test_experience_finalizer.py:229), [tests/backend/features/combat/test_lifecycle_service.py:138](D:/Workspace/personal/pets/TurnBasedMMORPG/tests/backend/features/combat/test_lifecycle_service.py:138).
- **Secondary gates / ограничения:** Rewards/death expected outcome нужно утвердить до negative replay test; не новый once rule. **Исторические ограничения:** A06-04: Тестовая модель, не new game ID; real restart отдельно.
- **Будущая необходимая проверка (сейчас не выполнена):** A06-04: Repeat same ID, failure each step, eventual result/conservation, initial snapshot.

### A06-05 — Чистый CI checkout не содержит обязательную path dependency

- **Original IDs / source severity:** A06-05 — High; [audit/06_testing_quality.md:421](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/06_testing_quality.md:421); аудит 06. [Canonical в реестре:695](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:695).
- **Историческая доказательность:** A06-05: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha; intended Production).
- **PRIMARY:** TECH-HARDENING. **Почему:** CI должен получать тот же выбранный source dependency воспроизводимо. **RC:** [RC-14:198](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:198). **Возможный package:** WP-dependency-source.
- **Технический/owner контракт исходной находки:** CI; uv; codex-ai source. Single checkout+install получает все declared sources.
- **Выполнено сейчас — статическое чтение:** pyproject и uv.lock codex-ai directory ../../codex_tools/codex-ai; CI делает checkout и uv sync. **Прочитанные anchors:** [pyproject.toml:34](D:/Workspace/personal/pets/TurnBasedMMORPG/pyproject.toml:34), [uv.lock:470](D:/Workspace/personal/pets/TurnBasedMMORPG/uv.lock:470), [.github/workflows/ci.yml:24](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/ci.yml:24).
- **Secondary gates / ограничения:** Actual CI run и local donor path availability неизвестны; approved library source/version сначала выбрать, no dependency upgrade now. **Исторические ограничения:** A06-05: Hosted failure не запускался; ready local venv не proof.
- **Будущая необходимая проверка (сейчас не выполнена):** A06-05: Clean Linux locked install/collect/full gate без venv/sibling.

### A06-06 — Develop не имеет behavioral gate

- **Original IDs / source severity:** A06-06 — Medium; [audit/06_testing_quality.md:431](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/06_testing_quality.md:431); аудит 06. [Canonical в реестре:704](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:704).
- **Историческая доказательность:** A06-06: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha).
- **PRIMARY:** TECH-HARDENING. **Почему:** Develop behavior gate scope — quality policy, не game behavior. **RC:** [RC-13:186](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:186). **Возможный package:** WP-test-controls.
- **Технический/owner контракт исходной находки:** Develop CI workflow. Integration branch получает behavioral checks.
- **Выполнено сейчас — статическое чтение:** CI develop job содержит linters/types; quality с checker ограничен PR/main condition. **Прочитанные anchors:** [.github/workflows/ci.yml:3](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/ci.yml:3), [.github/workflows/ci.yml:19](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/ci.yml:19).
- **Secondary gates / ограничения:** External required-check policy неизвестна; выбрать proportional behavior gates без blanket full-suite mandate. **Исторические ограничения:** A06-06: Required checks/remote actual runs неизвестны.
- **Будущая необходимая проверка (сейчас не выполнена):** A06-06: Event/ref matrix; selected failing test blocks develop check.

### A06-07 — Frontend/backend проверяются раздельно с независимыми fixtures

- **Original IDs / source severity:** A06-07 — Medium; [audit/06_testing_quality.md:441](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/06_testing_quality.md:441); аудит 06. [Canonical в реестре:713](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:713).
- **Историческая доказательность:** A06-07: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha).
- **PRIMARY:** TECH-HARDENING. **Почему:** Wire contracts frontend/backend нужно сверять без изменения game payload semantics. **RC:** [RC-12:174](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:174). **Возможный package:** WP-test-controls.
- **Технический/owner контракт исходной находки:** Frontend; Backend; HTTP contract tests. Producer/consumer jointly проверяют critical wire contract.
- **Выполнено сейчас — статическое чтение:** Frontend cabinet tests MockTransport; backend internal router tests отдельный TestClient; cabinet integration render isolated. **Прочитанные anchors:** [tests/frontend/features/cabinet/test_game_settings_module.py:18](D:/Workspace/personal/pets/TurnBasedMMORPG/tests/frontend/features/cabinet/test_game_settings_module.py:18), [tests/backend/features/test_internal_routers.py:105](D:/Workspace/personal/pets/TurnBasedMMORPG/tests/backend/features/test_internal_routers.py:105), [tests/frontend/features/cabinet/test_cabinet_integration.py:9](D:/Workspace/personal/pets/TurnBasedMMORPG/tests/frontend/features/cabinet/test_cabinet_integration.py:9).
- **Secondary gates / ограничения:** True compatibility/auth/source selector matrix не выполнена; preserve allowed consumers and denial behavior. **Исторические ограничения:** A06-07: Browser/Docker не обязательны; limited sampled HTTP scope.
- **Будущая необходимая проверка (сейчас не выполнена):** A06-07: Real ASGI consumer→router update/reset/transition, incompatible-field negative.

### A06-08 — Архитектурный gate проверяет только часть объявленных invariants

- **Original IDs / source severity:** A06-08 — Medium; [audit/06_testing_quality.md:451](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/06_testing_quality.md:451); аудит 06. [Canonical в реестре:722](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:722).
- **Историческая доказательность:** A06-08: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha / Legacy).
- **PRIMARY:** TECH-HARDENING. **Почему:** Architecture guard должен проверять approved ownership, включая semantic access. **RC:** [RC-13:186](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:186). **Возможный package:** WP-boundary-state.
- **Технический/owner контракт исходной находки:** Architecture tests; Ownership rules. Gate обнаруживает актуальные forbidden imports/keyspaces.
- **Выполнено сейчас — статическое чтение:** Boundary test skip Rift paths; forbidden_prefixes literal list покрывает лишь subset keyspaces. **Прочитанные anchors:** [tests/backend/features/test_infrastructure_boundaries.py:9](D:/Workspace/personal/pets/TurnBasedMMORPG/tests/backend/features/test_infrastructure_boundaries.py:9), [.agents/skills/turnbasedmmorpg-project/references/project-rules.md:17](D:/Workspace/personal/pets/TurnBasedMMORPG/.agents/skills/turnbasedmmorpg-project/references/project-rules.md:17), [tests/backend/features/test_infrastructure_boundaries.py:63](D:/Workspace/personal/pets/TurnBasedMMORPG/tests/backend/features/test_infrastructure_boundaries.py:63).
- **Secondary gates / ограничения:** Legacy modules проверять isolation отдельно, не обязать их development; AST/literal guard не security proof. **Исторические ограничения:** A06-08: Existing relocated-manager regressions полезны; не full rule enforcement.
- **Будущая необходимая проверка (сейчас не выполнена):** A06-08: Synthetic forbidden import/new prefix/Rift violation + allowed adapter.

### A06-09 — Deploy workflow не связывает image_ref с успешным quality result

- **Original IDs / source severity:** A06-09 — Medium; [audit/06_testing_quality.md:461](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/06_testing_quality.md:461); аудит 06. [Canonical в реестре:731](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:731).
- **Историческая доказательность:** A06-09: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (intended Production).
- **PRIMARY:** TECH-HARDENING. **Почему:** Promotion должна опираться на tested artifact identity; это technical release integrity. **RC:** [RC-13:186](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:186). **Возможный package:** WP-quality-provenance.
- **Технический/owner контракт исходной находки:** Deploy workflow; Image provenance. Promotion связывает image с successful quality.
- **Выполнено сейчас — статическое чтение:** Build-images needs quality; deploy-production accepts independent image_ref and preflight SSH, без needs build quality. **Прочитанные anchors:** [.github/workflows/deploy-production.yml:16](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/deploy-production.yml:16), [.github/workflows/build-images.yml:17](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/build-images.yml:17), [.github/workflows/build-images.yml:43](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/build-images.yml:43), [.github/workflows/deploy-production.yml:41](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/deploy-production.yml:41).
- **Secondary gates / ограничения:** External registry/environment controls unknown; no deployment ran; partial overlap A08-11 retained. **Исторические ограничения:** A06-09: External organisational controls не установлены; deploy не запускался.
- **Будущая необходимая проверка (сейчас не выполнена):** A06-09: Reject unknown/failed artifact before SSH; tested immutable ref accepted.

### A06-10 — Coverage защищает общий объём statements, не patch/branches

- **Original IDs / source severity:** A06-10 — Observation; [audit/06_testing_quality.md:471](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/06_testing_quality.md:471); аудит 06. [Canonical в реестре:740](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:740).
- **Историческая доказательность:** A06-10: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha).
- **PRIMARY:** NO-ACTION. **Почему:** Текущий74 threshold согласуется с project strategy; произвольный patch gate не нужен. **RC:** — (системная причина не установлена). **Возможный package:** —.
- **Технический/owner контракт исходной находки:** Coverage policy; Quality reports. Threshold/цель/patch reporting различаются.
- **Выполнено сейчас — статическое чтение:** pyproject fail_under=74; strategy explicitly enforce configured threshold and proportional local coverage. **Прочитанные anchors:** [pyproject.toml:165](D:/Workspace/personal/pets/TurnBasedMMORPG/pyproject.toml:165), [docs/ru/management/testing_strategy.md:17](D:/Workspace/personal/pets/TurnBasedMMORPG/docs/ru/management/testing_strategy.md:17), [.agents/skills/turnbasedmmorpg-quality/references/testing.md:7](D:/Workspace/personal/pets/TurnBasedMMORPG/.agents/skills/turnbasedmmorpg-quality/references/testing.md:7), [pyproject.toml:177](D:/Workspace/personal/pets/TurnBasedMMORPG/pyproject.toml:177).
- **Secondary gates / ограничения:** NO-ACTION — policy observation accepted; не снижать threshold, не считать defects fixed/CI green. **Исторические ограничения:** A06-10: Observation; соответствует current strategy; total coverage unknown.
- **Будущая необходимая проверка (сейчас не выполнена):** A06-10: Below74% config smoke; changed-behavior review; future policy only if adopted.

### A06-11 — Stage «unit» не отделяет уровни тестирования

- **Original IDs / source severity:** A06-11 — Low; [audit/06_testing_quality.md:481](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/06_testing_quality.md:481); аудит 06. [Canonical в реестре:749](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:749).
- **Историческая доказательность:** A06-11: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha).
- **PRIMARY:** NO-ACTION. **Почему:** Название unit stage с пустым selector само по себе не proof пропуска tests. **RC:** [RC-13:186](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:186). **Возможный package:** —.
- **Технический/owner контракт исходной находки:** Test stages; Markers; Installed runner. Stage selector честно задаёт набор/внешние deps.
- **Выполнено сейчас — статическое чтение:** test-stages=[unit], test-paths=[tests], test-markers unit=empty; full test-command uv run pytest. **Прочитанные anchors:** [pyproject.toml:200](D:/Workspace/personal/pets/TurnBasedMMORPG/pyproject.toml:200), [pyproject.toml:158](D:/Workspace/personal/pets/TurnBasedMMORPG/pyproject.toml:158).
- **Secondary gates / ограничения:** NO-ACTION текущей observation: не обязательный relabel/refactor; при change gate проверить runner taxonomy, actual external runner unexecuted. **Исторические ограничения:** A06-11: Историческая collection counts; текущая suite не запущена.
- **Будущая необходимая проверка (сейчас не выполнена):** A06-11: Collect stage matrix, explicit external deps, nonempty integration.

### A06-12 — Pip-audit hook проверяет своё окружение вместо зависимостей приложения

- **Original IDs / source severity:** A06-12 — Medium; [audit/06_testing_quality.md:491](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/06_testing_quality.md:491); аудит 06. [Canonical в реестре:758](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:758).
- **Историческая доказательность:** A06-12: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha).
- **PRIMARY:** TECH-HARDENING. **Почему:** Dependency audit должен охватывать intended environment и учитываемые exceptions. **RC:** [RC-13:186](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:186). **Возможный package:** WP-test-controls.
- **Технический/owner контракт исходной находки:** Pip-audit; Pre-commit; Develop CI. Dependency audit смотрит application dependency set.
- **Выполнено сейчас — статическое чтение:** pre-commit pip-audit hook использует --local в own hook env; project command отдельный skip-editable/ignore set. **Прочитанные anchors:** [.pre-commit-config.yaml:39](D:/Workspace/personal/pets/TurnBasedMMORPG/.pre-commit-config.yaml:39), [pyproject.toml:198](D:/Workspace/personal/pets/TurnBasedMMORPG/pyproject.toml:198), [.github/workflows/ci.yml:34](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/ci.yml:34).
- **Secondary gates / ограничения:** No scanners/advisory lookup now; утверждённую scope/exceptions provenance проверить, не объявлять vulnerability absence. **Исторические ограничения:** A06-12: CVE service не вызывался; main runner имеет отдельный project audit.
- **Будущая необходимая проверка (сейчас не выполнена):** A06-12: Diagnostic application versions seen; synthetic advisory fails gate.

### A07-01 — Combat и Rift player API не устанавливают пользователя и владельца

- **Original IDs / source severity:** A07-01 — High; [audit/07_application_security.md:167](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:167); аудит 07. [Canonical в реестре:769](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:769).
- **Историческая доказательность:** A07-01: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Pre-alpha / Legacy (Rift).
- **PRIMARY:** TECH-HARDENING. **Почему:** Game HTTP authentication/character owner scope — техническая trust boundary независимо от правил боя. **RC:** [RC-01:42](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:42). **Возможный package:** WP-auth-game.
- **Технический/owner контракт исходной находки:** Combat; Old Rift; HTTP identity/ownership. Request связан verified game actor/owner/runtime member.
- **Выполнено сейчас — статическое чтение:** Combat router не имеет auth dependency; endpoint receives char_id+orchestrator; app mounts router; game_auth уже умеет aud/type/exp и session lock. **Прочитанные anchors:** [src/backend/features/combat/api/router.py:26](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/api/router.py:26), [src/backend/features/combat/dependencies.py:23](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/dependencies.py:23), [src/backend/features/combat/services/session_service.py:143](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/services/session_service.py:143), [src/backend/core/game_auth.py:182](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/core/game_auth.py:182).
- **Secondary gates / ограничения:** Existing token guards reuse; generic Combat current TECH, Rift branch secondary Legacy support gate; actual internet exposure неизвестна. **Исторические ограничения:** A07-01: Production ingress unknown; runtime existence required; Rift support unknown.
- **Будущая необходимая проверка (сейчас не выполнена):** A07-01: Anonymous/wrong token/nonowner/selected mismatch denied before service.

### A07-02 — Runtime config API не требует административного права

- **Original IDs / source severity:** A07-02 — High; [audit/07_application_security.md:177](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:177); аудит 07. [Canonical в реестре:778](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:778).
- **Историческая доказательность:** A07-02: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha).
- **PRIMARY:** TECH-HARDENING. **Почему:** Config permission укрепляется без изменения tunables/значений gameplay. **RC:** [RC-01:42](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:42). **Возможный package:** WP-auth-config.
- **Технический/owner контракт исходной находки:** Game config; Admin/service; Redis. Live config read/write требует privileged identity.
- **Выполнено сейчас — статическое чтение:** Config router APIRouter без auth; app include_router; manager.set пишет validated known key в Redis. **Прочитанные anchors:** [src/backend/features/game_config/api/router.py:6](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/game_config/api/router.py:6), [src/backend/infrastructure/game_config/manager.py:162](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/game_config/manager.py:162), [src/backend/app.py:53](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/app.py:53).
- **Secondary gates / ограничения:** Разделить read/write service/admin callers; deny anonymous/wrong identity; запрещён balance/config value redesign. **Исторические ограничения:** A07-02: Not arbitrary Redis injection; actual manager/ingress required.
- **Будущая необходимая проверка (сейчас не выполнена):** A07-02: Wrong authority не вызывает manager; keys/value validation сохраняется.

### A07-03 — Administrative generation/content/simulation API без auth gate

- **Original IDs / source severity:** A07-03 — High; [audit/07_application_security.md:187](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:187); аудит 07. [Canonical в реестре:787](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:787).
- **Историческая доказательность:** A07-03: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha / Experimental).
- **PRIMARY:** TECH-HARDENING. **Почему:** Admin execution policy техническая; jobs/content implementation не менять. **RC:** [RC-01:42](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:42). **Возможный package:** WP-auth-admin.
- **Технический/owner контракт исходной находки:** GenerationAI; Monsters; Combat AI admin. Privileged jobs/content/report operations имеют admin permission.
- **Выполнено сейчас — статическое чтение:** GenAI/Monsters admin routers без auth declaration; rebuild apply commits SQL; app includes producer routers. **Прочитанные anchors:** [src/backend/features/generation_ai/api.py:23](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/api.py:23), [src/backend/features/monsters/api/router.py:24](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/monsters/api/router.py:24), [src/backend/features/monsters/services/generated_rebuild_service.py:47](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/monsters/services/generated_rebuild_service.py:47).
- **Secondary gates / ограничения:** Разные human-admin/service principals и Studio read-only; experimental simulation producer isolation, no AI algorithm development. **Исторические ограничения:** A07-03: Providers/cost/actual deployment неизвестны; read/delete не требуют worker.
- **Будущая необходимая проверка (сейчас не выполнена):** A07-03: No-right before DB/enqueue/provider; appropriate read/status permissions.

### A07-04 — Internal session diagnostics и combat analytics без доступа по роли

- **Original IDs / source severity:** A07-04 — Medium; [audit/07_application_security.md:197](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:197); аудит 07. [Canonical в реестре:796](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:796).
- **Историческая доказательность:** A07-04: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha / Legacy).
- **PRIMARY:** TECH-HARDENING. **Почему:** Diagnostics/analytics/backfill имеют permission boundary, не только URL prefix. **RC:** [RC-01:42](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:42), [RC-04:78](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:78). **Возможный package:** WP-auth-internal.
- **Технический/owner контракт исходной находки:** Internal diagnostics; Combat analytics/backfill. Internal metadata/analytics и backfill role-gated.
- **Выполнено сейчас — статическое чтение:** Combat/scenario/exploration internal endpoints читают session managers; app включает их без top-level auth dependencies. **Прочитанные anchors:** [src/backend/features/combat/api/internal_router.py:27](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/api/internal_router.py:27), [src/backend/features/scenario/api/internal_router.py:10](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/scenario/api/internal_router.py:10), [src/backend/features/exploration/api/internal_router.py:10](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/exploration/api/internal_router.py:10).
- **Secondary gates / ограничения:** Analytics consumers broader A08-03; actual route chain/limits/service identity verify before deny policy; no public prefix blanket removal. **Исторические ограничения:** A07-04: Secrets в replies не утверждаются; production data/ingress не читались.
- **Будущая необходимая проверка (сейчас не выполнена):** A07-04: Role matrix list/detail/filter/backfill, minimal projections.

### A07-06 — История приватных чатов не проверяет членство

- **Original IDs / source severity:** A07-06 — High; [audit/07_application_security.md:218](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:218); аудит 07. [Canonical в реестре:814](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:814).
- **Историческая доказательность:** A07-06: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Pre-alpha.
- **PRIMARY:** TECH-HARDENING. **Почему:** Thread membership — confidentiality boundary, содержание/UX чата сохраняются. **RC:** [RC-01:42](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:42). **Возможный package:** WP-chat-access.
- **Технический/owner контракт исходной находки:** Chat history; DM; Membership. Login не private thread permission.
- **Выполнено сейчас — статическое чтение:** History endpoints получают authenticated _char_id, но не используют его в thread/index query; DM get тоже scope-only. **Прочитанные anchors:** [src/backend/chat/api/router.py:16](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/chat/api/router.py:16), [src/backend/chat/repositories/message_repo.py:36](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/chat/repositories/message_repo.py:36), [src/backend/chat/api/router.py:88](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/chat/api/router.py:88).
- **Secondary gates / ограничения:** Public vs private allowlist и actual subject type owner-reviewed; negative foreign-DM/party/system + valid member future. **Исторические ограничения:** A07-06: No production history/exploit; public channels отдельная policy.
- **Будущая необходимая проверка (сейчас не выполнена):** A07-06: Nonmember/inactive member/system recipient denied before hydration.

### A07-07 — Chat send не проверяет разрешённый канал и scope

- **Original IDs / source severity:** A07-07 — High; [audit/07_application_security.md:228](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:228); аудит 07. [Canonical в реестре:823](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:823).
- **Историческая доказательность:** A07-07: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha.
- **PRIMARY:** TECH-HARDENING. **Почему:** Privileged channel/scope permissions технические при уже approved channel semantics. **RC:** [RC-01:42](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:42). **Возможный package:** WP-chat-access.
- **Технический/owner контракт исходной находки:** Realtime; Chat send; Channel/scope. Signed sender имеет право на channel/scope.
- **Выполнено сейчас — статическое чтение:** ChatChannel включает system/combat; WS bridge receives validated payload; with_session_scope вызывается только zone без scope. **Прочитанные anchors:** [src/backend/realtime/dto/envelope.py:20](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/realtime/dto/envelope.py:20), [src/backend/realtime/api/ws.py:325](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/realtime/api/ws.py:325), [src/backend/realtime/services/chat_bridge.py:78](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/realtime/services/chat_bridge.py:78), [src/backend/realtime/api/ws.py:334](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/realtime/api/ws.py:334).
- **Secondary gates / ограничения:** Не изобретать party/trade/game channel rules; approved sender/membership/source-of-truth matrix before implementation. **Исторические ограничения:** A07-07: JWT sender остаётся signed; actual live delivery unknown.
- **Будущая необходимая проверка (сейчас не выполнена):** A07-07: System channel denied, nonmember denied, zone/membership before buffer.

### A07-08 — WebSocket chat bootstrap не связывает URL character ID с claims

- **Original IDs / source severity:** A07-08 — Medium; [audit/07_application_security.md:238](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:238); аудит 07. [Canonical в реестре:832](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:832).
- **Историческая доказательность:** A07-08: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha.
- **PRIMARY:** TECH-HARDENING. **Почему:** WS character must bind signed claim, not independent URL actor. **RC:** [RC-03:66](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:66). **Возможный package:** WP-session-lifecycle.
- **Технический/owner контракт исходной находки:** WebSocket; Chat bootstrap; Actor mapping. Claims actor единственный identity source.
- **Выполнено сейчас — статическое чтение:** Handshake obtains character_id=claims.character_id; separate char_id query reads game:ac and writes chat:char_to_user; Origin/session lock guards присутствуют. **Прочитанные anchors:** [src/backend/realtime/api/ws.py:87](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/realtime/api/ws.py:87), [src/backend/realtime/services/connection_manager.py:39](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/realtime/services/connection_manager.py:39), [src/backend/realtime/services/notice_service.py:45](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/realtime/services/notice_service.py:45), [src/backend/realtime/api/ws.py:142](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/realtime/api/ws.py:142).
- **Secondary gates / ограничения:** Preserve anti-CSWSH/aud/exp/lock; test mismatch and legitimate reconnect, no gameplay scope redesign. **Исторические ограничения:** A07-08: Player.notice использует claims; чужие notices не доказаны.
- **Будущая необходимая проверка (сейчас не выполнена):** A07-08: Mismatch rejected; all bootstrap/topics/mappings from claims; reconnect.

### A07-09 — Деактивация учётной записи не применяется ко всем действующим сессиям

- **Original IDs / source severity:** A07-09 — Medium; [audit/07_application_security.md:248](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:248); аудит 07. [Canonical в реестре:841](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:841).
- **Историческая доказательность:** A07-09: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha).
- **PRIMARY:** TECH-HARDENING. **Почему:** Inactive account eligibility — текущий security lifecycle inconsistency, game values не меняются. **RC:** [RC-03:66](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:66). **Возможный package:** WP-session-lifecycle.
- **Технический/owner контракт исходной находки:** Site/game auth; Account moderation. Disable account имеет определённую силу для existing sessions.
- **Выполнено сейчас — статическое чтение:** Login проверяет not user.is_active; Frontend current-user lookup возвращает any existing user; backend token path stamps is_active=True. **Прочитанные anchors:** [src/frontend/features/auth/services/site_auth_service.py:66](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/features/auth/services/site_auth_service.py:66), [src/frontend/features/auth/services/auth_service.py:103](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/features/auth/services/auth_service.py:103), [src/frontend/features/auth/dependencies/providers.py:50](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/features/auth/dependencies/providers.py:50).
- **Secondary gates / ограничения:** Authoritative status/cache/revocation behavior needs explicit contract; не вводить gameplay ban policy. **Исторические ограничения:** A07-09: Production TTL/external lock revocation unknown.
- **Будущая необходимая проверка (сейчас не выполнена):** A07-09: Disable→site lookup/refresh/game actions/WS bounded revoke.

### A07-10 — Browser logout не завершает game session

- **Original IDs / source severity:** A07-10 — Medium; [audit/07_application_security.md:257](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:257); аудит 07. [Canonical в реестре:850](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:850).
- **Историческая доказательность:** A07-10: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha.
- **PRIMARY:** TECH-HARDENING. **Почему:** Site/game logout cleanup технически связывается после явного scope договора. **RC:** [RC-03:66](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:66). **Возможный package:** WP-session-lifecycle.
- **Технический/owner контракт исходной находки:** Site logout; Game cookies; WS session. Общий logout прекращает site и game authority.
- **Выполнено сейчас — статическое чтение:** Site logout работает с site refresh cookie; game cookies отдельны и middleware может refresh их независимо. **Прочитанные anchors:** [src/frontend/features/auth/routes/pages.py:137](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/features/auth/routes/pages.py:137), [src/frontend/game_features/session/token_state.py:31](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/game_features/session/token_state.py:31), [src/frontend/game_features/session/middleware.py:56](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/game_features/session/middleware.py:56).
- **Secondary gates / ограничения:** Owner gate: common vs separate logout подтверждать; не silent common logout/game UX change. **Исторические ограничения:** A07-10: Actual browser domains не тестировались; разделённый logout требует product decision.
- **Будущая необходимая проверка (сейчас не выполнена):** A07-10: HTTP/refresh/WS deny after logout; domain/path/legacy cookies.

### A07-11 — Inventory принимает site token вне выбранной game session

- **Original IDs / source severity:** A07-11 — Medium; [audit/07_application_security.md:266](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:266); аудит 07. [Canonical в реестре:859](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:859).
- **Историческая доказательность:** A07-11: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha.
- **PRIMARY:** TECH-HARDENING. **Почему:** Owner guard существует, selected-active-character boundary для site tokens требует policy. **RC:** [RC-03:66](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:66). **Возможный package:** WP-auth-game.
- **Технический/owner контракт исходной находки:** Inventory; Site/game auth; Selected actor. Gameplay mutation требует current game context сверх owner.
- **Выполнено сейчас — статическое чтение:** Backend get_current_user принимает site токен; require_game_character_scope возвращает при отсутствии game claims; Inventory _ensure_owner защищает ownership. **Прочитанные anchors:** [src/backend/core/auth.py:20](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/core/auth.py:20), [src/backend/features/inventory/api/router.py:42](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/inventory/api/router.py:42), [src/backend/features/inventory/services/inventory_service.py:84](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/inventory/services/inventory_service.py:84), [src/backend/core/auth.py:75](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/core/auth.py:75), [src/backend/features/inventory/api/router.py:35](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/inventory/api/router.py:35).
- **Secondary gates / ограничения:** Не утверждать «любого чужого персонажа»: owner guard реальный; reject own inactive actor only with approved selected scope. **Исторические ограничения:** A07-11: Cross-user IDOR не установлен; owner query работает.
- **Будущая необходимая проверка (сейчас не выполнена):** A07-11: Site token denied; selected mismatch denied; good owner/game accepted.

### A07-12 — Studio не обеспечивает auth/read-only contract

- **Original IDs / source severity:** A07-12 — High; [audit/07_application_security.md:275](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:275); аудит 07. [Canonical в реестре:868](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:868).
- **Историческая доказательность:** A07-12: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Dev-only.
- **PRIMARY:** TECH-HARDENING. **Почему:** Нарушение явно установленного Studio source read-only contract техническое, хоть surface Dev-only. **RC:** [RC-01:42](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:42), [RC-04:78](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:78), [RC-05:90](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:90). **Возможный package:** WP-studio-readonly.
- **Технический/owner контракт исходной находки:** Studio; Source selector; Cabinet; Backend HTTP. Analytical Studio auth/read-only действует до backend call.
- **Выполнено сейчас — статическое чтение:** Studio source selector принимает local/prod; cabinet router строится without auth argument; integrations admin_monsters содержит POST methods. **Прочитанные anchors:** [src/studio/app.py:137](D:/Workspace/personal/pets/TurnBasedMMORPG/src/studio/app.py:137), [src/fastapi_cabinet/site.py:27](D:/Workspace/personal/pets/TurnBasedMMORPG/src/fastapi_cabinet/site.py:27), [src/studio/features/source_selector/middleware.py:25](D:/Workspace/personal/pets/TurnBasedMMORPG/src/studio/features/source_selector/middleware.py:25), [src/studio/features/cabinet/modules/combat_ai_testing/cabinet.py:69](D:/Workspace/personal/pets/TurnBasedMMORPG/src/studio/features/cabinet/modules/combat_ai_testing/cabinet.py:69), [src/studio/integrations/backend_api/admin_monsters.py:264](D:/Workspace/personal/pets/TurnBasedMMORPG/src/studio/integrations/backend_api/admin_monsters.py:264).
- **Secondary gates / ограничения:** Never perform prod writes; selected-source mutating call chain/consumer check before proposed block; Studio не production deployment. **Исторические ограничения:** A07-12: Prod tunnel/ACL/permissions unknown; не public-prod claim; DB readonly не protects HTTP.
- **Будущая необходимая проверка (сейчас не выполнена):** A07-12: Unauthorized denied; every action source policy before write; allowlist.

### A07-13 — Backend Exploration не имеет actor/ownership dependency

- **Original IDs / source severity:** A07-13 — Medium; [audit/07_application_security.md:285](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:285); аудит 07. [Canonical в реестре:877](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:877).
- **Историческая доказательность:** A07-13: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha.
- **PRIMARY:** TECH-HARDENING. **Почему:** Caller char_id ownership — техническая граница независимо от Exploration design. **RC:** [RC-01:42](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:42). **Возможный package:** WP-auth-game.
- **Технический/owner контракт исходной находки:** Exploration backend API; Actor owner. Caller mode identity/user or internal service задаёт actor rights.
- **Выполнено сейчас — статическое чтение:** Exploration route signatures только request/gateway, receives char_id; backend mounts /exploration without router auth. **Прочитанные anchors:** [src/backend/features/exploration/api/router.py:17](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/exploration/api/router.py:17), [src/backend/features/exploration/gateway/exploration_gateway.py:30](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/exploration/gateway/exploration_gateway.py:30), [src/backend/app.py:72](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/app.py:72).
- **Secondary gates / ограничения:** Nginx /api exposure не доказывает публикацию /exploration; supported frontend adapter+internal caller compatibility future. **Исторические ограничения:** A07-13: Основной proxy /api не публикует этот prefix; actual access unknown.
- **Будущая необходимая проверка (сейчас не выполнена):** A07-13: Deny no identity/nonowner/scope; assert intended ingress.

### A07-14 — условный риск конфигурации

- **Original IDs / source severity:** A07-14 — High; [audit/07_application_security.md:298](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:298); аудит 07; A08-01 — High; [audit/08_infrastructure_security.md:237](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:237); аудит 08. [Canonical в реестре:886](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:886).
- **Историческая доказательность:** A07-14: Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту; A08-01: Исторически воспроизведено локальной проверкой/тестом исходного аудита; сейчас не повторялось. **Стадия:** Shared infrastructure (Pre-alpha; intended Production).
- **PRIMARY:** TECH-HARDENING. **Почему:** Known-default validation fail-closed техническая; actual keys не исследуются. **RC:** [RC-04:78](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:78). **Возможный package:** WP-secret-validation.
- **Технический/owner контракт исходной находки:** Settings; JWT; Internal service identity. Production отвергает default/missing security keys.
- **Выполнено сейчас — статическое чтение:** Backend/frontend defaults известны; backend validator не проверяет secret defaults; BaseCommonSettings только debug→production property; internal guard rejects change-me but not dev-default. **Прочитанные anchors:** [src/backend/config/settings.py:49](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/config/settings.py:49), [src/frontend/config/settings.py:30](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/config/settings.py:30), [src/backend/core/game_auth.py:58](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/core/game_auth.py:58), [deploy/compose.site.yml:39](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/compose.site.yml:39), [.venv/Lib/site-packages/codex_core/settings/base.py:133](D:/Workspace/personal/pets/TurnBasedMMORPG/.venv/Lib/site-packages/codex_core/settings/base.py:133), [src/backend/config/settings.py:102](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/config/settings.py:102), [src/backend/core/game_auth.py:65](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/core/game_auth.py:65).
- **Secondary gates / ограничения:** A07-14/A08-01 полный дубль; static validator defect current, реальных prodkeys/exploit нет; existing keys migration/staging contract gate. **Исторические ограничения:** A07-14: Actual keys/controls unknown; severityHigh risk сохранена; A08-01: Историческая settings probe; actual keys/ingress неизвестны; не production exploit.
- **Будущая необходимая проверка (сейчас не выполнена):** A07-14: No real credential prod-settings fail-closed fixtures; A08-01: Prod no/default keys reject, distinct keys accept, no secret validation output.

### A07-15 — dev exposure risk

- **Original IDs / source severity:** A07-15 — Medium; [audit/07_application_security.md:299](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:299); аудит 07. [Canonical в реестре:895](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:895).
- **Историческая доказательность:** A07-15: Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Experimental / Dev-only.
- **PRIMARY:** TECH-HARDENING. **Почему:** Default dev publication отдельно от development Legacy/Hex logic — technical. **RC:** [RC-04:78](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:78). **Возможный package:** WP-surface-isolation.
- **Технический/owner контракт исходной находки:** Dev Rift routes; Deployment flags. Dev endpoint isolated/default-off при public deployment.
- **Выполнено сейчас — статическое чтение:** build_rift_router включает dev+hex при enable_dev_routes True; setting default=True; app mount Rift. **Прочитанные anchors:** [src/backend/features/rift/api/router.py:179](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/api/router.py:179), [src/backend/config/settings.py:59](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/config/settings.py:59).
- **Secondary gates / ограничения:** Actual prod override unknown; preserve intended local harness; original router:195 stale, current179 verified. **Исторические ограничения:** A07-15: Actual flag/ingress unknown; not automatically isolated.
- **Будущая необходимая проверка (сейчас не выполнена):** A07-15: Prod flag/router assertion, dev access denied where disabled.

### A07-16 — lifecycle/abuse risk

- **Original IDs / source severity:** A07-16 — Medium; [audit/07_application_security.md:300](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:300); аудит 07. [Canonical в реестре:904](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:904).
- **Историческая доказательность:** A07-16: Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Pre-alpha.
- **PRIMARY:** VERIFY-FIRST. **Почему:** Длинная WS жизнь/quota/lock риска требует actual policy и runtime evidence. **RC:** [RC-03:66](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:66), [RC-06:102](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:102). **Возможный package:** WP-session-lifecycle.
- **Технический/owner контракт исходной находки:** Realtime session lifetime; Limits; URL credentials. Long-lived authority revoked/expired и bounded abuse.
- **Выполнено сейчас — статическое чтение:** Decode/lock проверяются при handshake; receive loop heartbeat не содержит repeated expiry/status check; query token fallback существует. **Прочитанные anchors:** [src/backend/realtime/api/ws.py:213](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/realtime/api/ws.py:213).
- **Secondary gates / ограничения:** VERIFY-FIRST; heartbeat уже guard liveness, не lifetime; реальных quotas/edge controls неизвестно, no denial-of-service audit. **Исторические ограничения:** A07-16: Server/proxy limits unknown; handshake already guarded; no proven DoS/leak.
- **Будущая необходимая проверка (сейчас не выполнена):** A07-16: Lifetime/revoke, quotas/frame budgets, redaction synthetic checks.

### A07-17 — unsafe-render sinks

- **Original IDs / source severity:** A07-17 — Observation; [audit/07_application_security.md:301](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:301); аудит 07. [Canonical в реестре:913](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:913).
- **Историческая доказательность:** A07-17: Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Pre-alpha / Experimental / Dev-only.
- **PRIMARY:** VERIFY-FIRST. **Почему:** HTML sinks есть, доказанный untrusted origin/reachable exploit отсутствует. **RC:** — (системная причина не установлена). **Возможный package:** WP-browser-render.
- **Технический/owner контракт исходной находки:** Scenario rich text; Hex DOM; Content. Allowed rich text/sanitizer boundary defined.
- **Выполнено сейчас — статическое чтение:** Scenario template rich_text → safe; Hex template innerHTML enemy.name interpolation присутствуют. **Прочитанные anchors:** [src/frontend/templates/game/domains/scenario/viewport/main.html:59](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/templates/game/domains/scenario/viewport/main.html:59), [src/frontend/templates/game/test_hex_rift.html:565](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/templates/game/test_hex_rift.html:565).
- **Secondary gates / ограничения:** VERIFY-FIRST source provenance/sanitizer/inert fixtures; Hex Dev-only gate; не новый XSS audit или content/UX rewrite. **Исторические ограничения:** A07-17: Observation, not confirmed XSS; source boundary missing.
- **Будущая необходимая проверка (сейчас не выполнена):** A07-17: Source-to-sink fixtures, sanitizer/escaping/CSP contract.

### A07-18 — повторное применение rewards

- **Original IDs / source severity:** A07-18 — Medium; [audit/07_application_security.md:302](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/07_application_security.md:302); аудит 07. [Canonical в реестре:922](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:922).
- **Историческая доказательность:** A07-18: Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Pre-alpha / Legacy.
- **PRIMARY:** MIXED. **Почему:** Широкий repeated-reward risk требует owner once/eligibility contract до work. **RC:** [RC-07:114](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:114). **Возможный package:** WP-reward-once.
- **Технический/owner контракт исходной находки:** Rift rewards; Loot entitlement; Retry. Repeated delivery не повторяет authoritative rewards.
- **Выполнено сейчас — статическое чтение:** Rift exit reward before session marker; safe/unsafe Loot processed guards различны; completion objective guards существуют. **Прочитанные anchors:** [src/backend/features/rift/services/player_service.py:192](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/services/player_service.py:192), [src/backend/features/loot/workers/tasks/loot_claim_task.py:203](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/loot/workers/tasks/loot_claim_task.py:203), [src/backend/features/rift/services/player_service.py:114](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/services/player_service.py:114).
- **Secondary gates / ограничения:** MIXED + verify gate + Legacy subset; не объединять три unrelated scenarios в exploit claim, preserve XP/loot values. **Исторические ограничения:** A07-18: Real delivery/actual effect not measured; не new confirmed exploit.
- **Будущая необходимая проверка (сейчас не выполнена):** A07-18: Controlled interleaving, authoritative idempotency/conservation.

### A08-02 — Общие secrets и сеть расширяют последствия компрометации

- **Original IDs / source severity:** A08-02 — Medium; [audit/08_infrastructure_security.md:249](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:249); аудит 08. [Canonical в реестре:942](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:942).
- **Историческая доказательность:** A08-02: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (intended Production).
- **PRIMARY:** TECH-HARDENING. **Почему:** Service least privilege — technical deployment boundary, не новая distributed gameplay architecture. **RC:** [RC-05:90](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:90). **Возможный package:** WP-runtime-isolation.
- **Технический/owner контракт исходной находки:** Runtime services; SQL; Redis; Mongo; S3. Service credentials/network scopes минимальны.
- **Выполнено сейчас — статическое чтение:** Site/game/bot подключают общий env_file, site получает GAME_DATABASE_URL, game SITE_DATABASE_URL; общий network используется. **Прочитанные anchors:** [deploy/compose.site.yml:39](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/compose.site.yml:39), [deploy/compose.game.yml:43](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/compose.game.yml:43), [deploy/compose.tg-bot.yml:8](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/compose.tg-bot.yml:8).
- **Secondary gates / ограничения:** Actual DB grants/secrets/runtime unknown; minimal consumer-specific env/DB access variant, no new microservices. **Исторические ограничения:** A08-02: Initial RCE/host escape не доказаны; actual grants unknown.
- **Будущая необходимая проверка (сейчас не выполнена):** A08-02: Service env inventory, least-privilege denied operations, allowed workflow.

### A08-03 — Внутренние session API доступны через публичный proxy

- **Original IDs / source severity:** A08-03 — Medium; [audit/08_infrastructure_security.md:259](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:259); аудит 08. [Canonical в реестре:951](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:951).
- **Историческая доказательность:** A08-03: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (intended Production).
- **PRIMARY:** TECH-HARDENING. **Почему:** Proxy publication и backend permission самостоятельные уровни технического контроля. **RC:** [RC-01:42](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:42), [RC-04:78](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:78). **Возможный package:** WP-auth-internal.
- **Технический/owner контракт исходной находки:** Nginx; Internal session API; Redis scan. Public edge и direct API не раскрывают internal diagnostics.
- **Выполнено сейчас — статическое чтение:** Nginx /api/ proxy_pass backend; app mount internal routers; scenario internal session listing без auth. **Прочитанные anchors:** [deploy/nginx/site.conf.template:120](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/nginx/site.conf.template:120), [src/backend/app.py:43](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/app.py:43), [src/backend/features/scenario/api/internal_router.py:7](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/scenario/api/internal_router.py:7).
- **Secondary gates / ограничения:** Existing limit_req сохранён, blanket /api deny ломает game/admin consumers; partial overlap A07-04 not duplicate. **Исторические ограничения:** A08-03: Running configuration unknown; no DB credential/owner mutation proof.
- **Будущая необходимая проверка (сейчас не выполнена):** A08-03: Anonymous edge/direct deny; scoped caller + bounded pagination.

### A08-04 — Experimental генератор открыт и не ограничивает накопление инстансов

- **Original IDs / source severity:** A08-04 — High; [audit/08_infrastructure_security.md:269](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:269); аудит 08. [Canonical в реестре:960](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:960).
- **Историческая доказательность:** A08-04: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Experimental / Dev-only.
- **PRIMARY:** TECH-HARDENING. **Почему:** TECH scope ограничен dev/Hex publication isolation; capacity development deferred. **RC:** [RC-04:78](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:78), [RC-16:222](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:222). **Возможный package:** WP-surface-isolation.
- **Технический/owner контракт исходной находки:** Hex dev API; Runtime memory; Redis; Nginx. Dev generation isolated/bounded; unknown ID не unbounded allocation.
- **Выполнено сейчас — статическое чтение:** enable_dev_rift_routes default True; router includes hex_test_router; HexRuntimeService держит process instances. **Прочитанные anchors:** [src/backend/config/settings.py:59](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/config/settings.py:59), [src/backend/features/rift/api/router.py:179](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/api/router.py:179), [src/backend/app.py:68](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/app.py:68), [src/backend/features/rift/services/hex_runtime_service.py:22](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/services/hex_runtime_service.py:22).
- **Secondary gates / ограничения:** Secondary EXPERIMENTAL-LEGACY: bounds/lifetime/perf only if owner approves supported dev harness; no Hex masks/game generation. **Исторические ограничения:** A08-04: Release of dirty files unknown; Redis TTL не expires process dict; no load attack.
- **Будущая необходимая проверка (сейчас не выполнена):** A08-04: Prod absent route, bounded counts/eviction, unknown-ID small fixtures.

### A08-05 — Публичные metrics сохраняют исходные URL, включая bearer identifiers

- **Original IDs / source severity:** A08-05 — Medium; [audit/08_infrastructure_security.md:279](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:279); аудит 08. [Canonical в реестре:969](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:969).
- **Историческая доказательность:** A08-05: Исторически воспроизведено локальной проверкой/тестом исходного аудита; сейчас не повторялось. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Shared infrastructure (intended Production).
- **PRIMARY:** TECH-HARDENING. **Почему:** Labels должны исключать токены и uncontrolled cardinality. **RC:** [RC-06:102](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:102). **Возможный package:** WP-metrics-redaction.
- **Технический/owner контракт исходной находки:** Prometheus middleware/endpoint; Frontend URLs. Telemetry labels не user tokens/IDs; exposure scoped.
- **Выполнено сейчас — статическое чтение:** Middleware вычисляет path_template до call_next, fallback request.url.path; counters label path; /metrics без auth. **Прочитанные anchors:** [src/shared/infrastructure/metrics_middleware.py:23](D:/Workspace/personal/pets/TurnBasedMMORPG/src/shared/infrastructure/metrics_middleware.py:23), [src/shared/infrastructure/metrics.py:9](D:/Workspace/personal/pets/TurnBasedMMORPG/src/shared/infrastructure/metrics.py:9), [src/shared/infrastructure/metrics_endpoint.py:12](D:/Workspace/personal/pets/TurnBasedMMORPG/src/shared/infrastructure/metrics_endpoint.py:12).
- **Secondary gates / ограничения:** Protect existing metric meaning; actual exporters/scrapes unknown; future inert known-token URL probe, not secret reads. **Исторические ограничения:** A08-05: Историческая inert AST probe; full HTTP incomplete; feature/login constraints.
- **Будущая необходимая проверка (сейчас не выполнена):** A08-05: Synthetic token absent, external metrics denied, unknown-path labels bounded.

### A08-06 — Nginx access log содержит URL-токены

- **Original IDs / source severity:** A08-06 — Medium; [audit/08_infrastructure_security.md:291](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:291); аудит 08. [Canonical в реестре:978](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:978).
- **Историческая доказательность:** A08-06: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (intended Production).
- **PRIMARY:** TECH-HARDENING. **Почему:** Request URL tokens/PII требуют observability redaction без изменения routes. **RC:** [RC-06:102](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:102). **Возможный package:** WP-log-redaction.
- **Технический/owner контракт исходной находки:** Nginx access logs; Survey/email/WS URLs. Logs не хранят bearer URL secrets.
- **Выполнено сейчас — статическое чтение:** Nginx log_format использует request_uri; surveys и email verification embed token in path. **Прочитанные anchors:** [deploy/nginx/nginx.conf:20](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/nginx/nginx.conf:20), [src/frontend/features/surveys/routes/pages.py:16](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/features/surveys/routes/pages.py:16), [src/frontend/features/account/routes/email_verify.py:87](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/features/account/routes/email_verify.py:87).
- **Secondary gates / ограничения:** Operational log retention/access unknown; mask path+query with useful route/diagnostic fields preserved. **Исторические ограничения:** A08-06: Email login/password/TTL ограничивают impact; query WS fallback диагностический.
- **Будущая необходимая проверка (сейчас не выполнена):** A08-06: Synthetic token absent from Nginx/app/collector; retain request context.

### A08-07 — Production exception logging раскрывает locals; явно логируется PII

- **Original IDs / source severity:** A08-07 — Medium; [audit/08_infrastructure_security.md:301](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:301); аудит 08. [Canonical в реестре:987](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:987).
- **Историческая доказательность:** A08-07: Исторически воспроизведено локальной проверкой/тестом исходного аудита; сейчас не повторялось. **Стадия:** Shared infrastructure (intended Production).
- **PRIMARY:** TECH-HARDENING. **Почему:** Exception diagnose/backtrace и PII — technical confidentiality policy. **RC:** [RC-06:102](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:102). **Возможный package:** WP-log-redaction.
- **Технический/owner контракт исходной находки:** Logging wrapper; codex-core/Loguru; Email PII. Prod exception diagnostics не locals/credentials/PII.
- **Выполнено сейчас — статическое чтение:** Project setup delegates codex_core; installed prod sink serializes stdout without explicit diagnose/backtrace; Loguru defaults True. **Прочитанные anchors:** [src/shared/infrastructure/logging_config.py:42](D:/Workspace/personal/pets/TurnBasedMMORPG/src/shared/infrastructure/logging_config.py:42), [.venv/Lib/site-packages/codex_core/common/loguru_setup.py:287](D:/Workspace/personal/pets/TurnBasedMMORPG/.venv/Lib/site-packages/codex_core/common/loguru_setup.py:287), [.venv/Lib/site-packages/loguru/_defaults.py:43](D:/Workspace/personal/pets/TurnBasedMMORPG/.venv/Lib/site-packages/loguru/_defaults.py:43), [.venv/Lib/site-packages/loguru/_defaults.py:44](D:/Workspace/personal/pets/TurnBasedMMORPG/.venv/Lib/site-packages/loguru/_defaults.py:44).
- **Secondary gates / ограничения:** Installed library bytes != canonical deploy artifact; изменения библиотеки отдельный owner/release gate, project-only proposal here. **Исторические ограничения:** A08-07: Историческая synthetic canary/local pinned library; image bytes/logs unknown.
- **Будущая необходимая проверка (сейчас не выполнена):** A08-07: Canary/SMTP exception stdout+collector no token/body/email, trace retained.

### A08-08 — Local/observability Compose публикует чувствительные сервисы на всех interfaces

- **Original IDs / source severity:** A08-08 — Medium; [audit/08_infrastructure_security.md:311](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:311); аудит 08. [Canonical в реестре:996](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:996).
- **Историческая доказательность:** A08-08: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Dev-only / optional overlay.
- **PRIMARY:** TECH-HARDENING. **Почему:** Dev ingress с known credentials ограничивается по environment purpose. **RC:** [RC-04:78](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:78). **Возможный package:** WP-runtime-isolation.
- **Технический/owner контракт исходной находки:** Local Compose; Studio; DB; Mailpit; Dashboards. Dev data/admin bind isolated and gated if external.
- **Выполнено сейчас — статическое чтение:** Dev Compose публикует 5432:5432 с dev password; observability9090:9090; host binding omitted. **Прочитанные anchors:** [deploy/docker-compose.yml:9](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/docker-compose.yml:9), [deploy/docker-compose.db.yml:7](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/docker-compose.db.yml:7), [deploy/docker-compose.observability.yml:7](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/docker-compose.observability.yml:7).
- **Secondary gates / ограничения:** Не изменять фактические servers/firewall; local accessibility contract and supported dev clients first. **Исторические ограничения:** A08-08: Не production overlay; actual firewall/tunnel/initial-volume state unknown.
- **Будущая необходимая проверка (сейчас не выполнена):** A08-08: Resolved port binds loopback; external mode requires credentials/access.

### A08-09 — Mutable Actions/images не фиксируют цепочку происхождения

- **Original IDs / source severity:** A08-09 — Medium; [audit/08_infrastructure_security.md:321](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:321); аудит 08. [Canonical в реестре:1005](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:1005).
- **Историческая доказательность:** A08-09: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (intended Production / CI).
- **PRIMARY:** TECH-HARDENING. **Почему:** Immutable actions/base images/provenance — technical release integrity. **RC:** [RC-14:198](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:198). **Возможный package:** WP-supply-chain.
- **Технический/owner контракт исходной находки:** Actions; Base/runtime images; GHCR; Provenance. Privileged executable/artifact refs immutable and verifiable.
- **Выполнено сейчас — статическое чтение:** Checkout/build/SSH actions tags присутствуют; infra postgres tag; some setup-uv pinned SHA. **Прочитанные anchors:** [.github/workflows/deploy-production.yml:34](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/deploy-production.yml:34), [.github/workflows/build-images.yml:21](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/build-images.yml:21), [deploy/compose.infra.yml:5](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/compose.infra.yml:5).
- **Secondary gates / ограничения:** Do not claim all unpinned/no quality: build needs quality; registry bytes/signed provenance/external protections not checked. **Исторические ограничения:** A08-09: Compromise не обнаружен; fork PR не privileged; setup-uv SHA исключение.
- **Будущая необходимая проверка (сейчас не выполнена):** A08-09: Pinned privileged Actions, digest manifest/source/gate binding; mismatch deny.

### A08-10 — CI зависит от отсутствующего local source, Docker меняет source policy

- **Original IDs / source severity:** A08-10 — Medium; [audit/08_infrastructure_security.md:331](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:331); аудит 08. [Canonical в реестре:1014](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:1014).
- **Историческая доказательность:** A08-10: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha; intended Production build).
- **PRIMARY:** TECH-HARDENING. **Почему:** Validation/build source parity — reproducibility contract. **RC:** [RC-14:198](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:198). **Возможный package:** WP-dependency-source.
- **Технический/owner контракт исходной находки:** uv source; CI; Python Docker build. CI/image получают один approved immutable source.
- **Выполнено сейчас — статическое чтение:** Local codex-ai directory in pyproject/lock; CI uv sync; Docker export --no-sources chooses published dependency path. **Прочитанные anchors:** [pyproject.toml:28](D:/Workspace/personal/pets/TurnBasedMMORPG/pyproject.toml:28), [uv.lock:470](D:/Workspace/personal/pets/TurnBasedMMORPG/uv.lock:470), [.github/workflows/ci.yml:24](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/ci.yml:24), [deploy/backend/Dockerfile:9](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/backend/Dockerfile:9), [deploy/frontend/Dockerfile:9](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/frontend/Dockerfile:9).
- **Secondary gates / ограничения:** Partial A06-05; actual published API compatibility unknown, version/source decision before rollout; no install now. **Исторические ограничения:** A08-10: Actual registry substitution/confusion не доказаны; offline export incomplete.
- **Будущая необходимая проверка (сейчас не выполнена):** A08-10: Clean locked install, export source identity, image wheel/hash provenance.

### A08-11 — Production dispatch не привязан к отдельному approval/ref/provenance gate

- **Original IDs / source severity:** A08-11 — Medium; [audit/08_infrastructure_security.md:351](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:351); аудит 08. [Canonical в реестре:1023](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:1023).
- **Историческая доказательность:** A08-11: Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Shared infrastructure (intended Production).
- **PRIMARY:** VERIFY-FIRST. **Почему:** Governance/ref/environment controls могут существовать вне repo; сначала подтвердить. **RC:** [RC-13:186](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:186), [RC-14:198](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:198). **Возможный package:** WP-quality-provenance.
- **Технический/owner контракт исходной находки:** Production dispatch; GitHub governance. Privileged promotion/ref/review/serialization enforceable.
- **Выполнено сейчас — статическое чтение:** Deploy workflow_dispatch accepts image_ref; build tag/manual triggers; deploy chain needs SSH preflight only. **Прочитанные anchors:** [.github/workflows/deploy-production.yml:3](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/deploy-production.yml:3), [.github/workflows/build-images.yml:7](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/build-images.yml:7), [.github/workflows/deploy-production.yml:41](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/deploy-production.yml:41).
- **Secondary gates / ограничения:** VERIFY-FIRST external protections/review/concurrency/digest policy; not proof arbitrary actor can deploy. **Исторические ограничения:** A08-11: Actor уже deployment-authorized; YAML absence не actual bypass.
- **Будущая необходимая проверка (сейчас не выполнена):** A08-11: Read real protections; deny untrusted ref/artifact; two runs serialized.

### A08-12 — Права production .env не закреплены при записи

- **Original IDs / source severity:** A08-12 — Medium; [audit/08_infrastructure_security.md:361](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:361); аудит 08. [Canonical в реестре:1032](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:1032).
- **Историческая доказательность:** A08-12: Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Shared infrastructure (intended Production).
- **PRIMARY:** VERIFY-FIRST. **Почему:** File mode depends remote umask/account, so absence explicit mode is preliminary risk. **RC:** [RC-05:90](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:90). **Возможный package:** WP-runtime-isolation.
- **Технический/owner контракт исходной находки:** SSH deploy; Host filesystem; Env-file permissions. Secret env private across create/replace.
- **Выполнено сейчас — статическое чтение:** Workflow пишет ENV_FILE_CONTENT через redirect в .env; no explicit mode in read deploy block. **Прочитанные anchors:** [.github/workflows/deploy-production.yml:72](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/deploy-production.yml:72), [.github/workflows/deploy-production.yml:83](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/deploy-production.yml:83).
- **Secondary gates / ограничения:** VERIFY-FIRST remote mode/umask/grants without reading secret body; don't demand broad infra rewrite. **Исторические ограничения:** A08-12: Actual mode/umask unknown; 0644 на VPS не утверждается.
- **Будущая необходимая проверка (сейчас не выполнена):** A08-12: Create/replace under permissive umask, stat/ACL/denied-read без content.

### A08-13 — Нет дополнительных ограничений post-compromise ресурсов и файловой системы

- **Original IDs / source severity:** A08-13 — Low; [audit/08_infrastructure_security.md:341](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:341); аудит 08. [Canonical в реестре:1041](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:1041).
- **Историческая доказательность:** A08-13: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (intended Production).
- **PRIMARY:** TECH-HARDENING. **Почему:** Container permission/resource boundaries technical, exact limits require evidence. **RC:** [RC-05:90](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:90), [RC-16:222](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:222). **Возможный package:** WP-runtime-isolation.
- **Технический/owner контракт исходной находки:** Production containers; Host resources/filesystem. Post-compromise workload/write/capability budget bounded.
- **Выполнено сейчас — статическое чтение:** Compose services show restart/shared networks; Docker runtime USER appuser present in app images; image/infra use differ. **Прочитанные anchors:** [deploy/compose.infra.yml:4](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/compose.infra.yml:4), [deploy/compose.site.yml:35](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/compose.site.yml:35), [deploy/compose.game.yml:39](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/compose.game.yml:39), [deploy/backend/Dockerfile:35](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/backend/Dockerfile:35), [deploy/frontend/Dockerfile:36](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/frontend/Dockerfile:36).
- **Secondary gates / ограничения:** Не говорить «все root»: appuser guard существует; inspect capabilities/read-only/seccomp/resources future; gameplay deadlines no change. **Исторические ограничения:** A08-13: Low hardening; non-root/no socket/privileged компенсируют; daemon policy unknown.
- **Будущая необходимая проверка (сейчас не выполнена):** A08-13: Startup/assets/migrations under limits, denied write/capability, bounded fixture.

### A08-14 — Недоверенные forwarded headers могут давать HTTP-ссылки с токеном

- **Original IDs / source severity:** A08-14 — Medium; [audit/08_infrastructure_security.md:369](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:369); аудит 08. [Canonical в реестре:1050](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:1050).
- **Историческая доказательность:** A08-14: Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Shared infrastructure (intended Production; feature-dependent).
- **PRIMARY:** VERIFY-FIRST. **Почему:** Proxy trusted scheme/host and feature reachability требуют environment verification. **RC:** — (системная причина не установлена). **Возможный package:** WP-transport-policy.
- **Технический/owner контракт исходной находки:** Proxy trust; Email canonical origin; Uvicorn. Security link HTTPS canonical origin with bounded proxy trust.
- **Выполнено сейчас — статическое чтение:** Nginx forwards X-Forwarded-Proto $scheme; Uvicorn default forwarded_allow_ips=127.0.0.1; Compose host0.0.0.0. **Прочитанные anchors:** [deploy/nginx/site.conf.template:179](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/nginx/site.conf.template:179), [deploy/compose.site.yml:55](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/compose.site.yml:55), [.venv/Lib/site-packages/uvicorn/config.py:340](D:/Workspace/personal/pets/TurnBasedMMORPG/.venv/Lib/site-packages/uvicorn/config.py:340).
- **Secondary gates / ограничения:** VERIFY-FIRST trust proxy/cookie/email feature flags and overrides; no live URL/token operations. **Исторические ограничения:** A08-14: Feature off example; HSTS/overrides may protect; no real HTTP leak.
- **Будущая необходимая проверка (сейчас не выполнена):** A08-14: Through-proxy synthetic HTTPS links; forged forwarded headers cannot alter trust.

### A08-15 — Recovery и security monitoring не доказаны operational evidence

- **Original IDs / source severity:** A08-15 — Observation; [audit/08_infrastructure_security.md:377](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/08_infrastructure_security.md:377); аудит 08. [Canonical в реестре:1059](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:1059).
- **Историческая доказательность:** A08-15: Гипотеза: исторический риск/неполный контракт; отдельные предпосылки не равны доказанному эффекту. **Стадия:** Shared infrastructure (intended Production).
- **PRIMARY:** VERIFY-FIRST. **Почему:** Runbooks/backup/alerts/runtime TLS are unknown evidence, not established outage. **RC:** — (системная причина не установлена). **Возможный package:** WP-recovery-readiness.
- **Технический/owner контракт исходной находки:** Backups; Recovery; Readiness; TLS; Alerts. Operational claims backed restore/alert/TLS evidence.
- **Выполнено сейчас — статическое чтение:** Deployment doc describes image rollback; workflow compose --wait; app health returns status ok. **Прочитанные anchors:** [docs/ru/management/deployment.md:179](D:/Workspace/personal/pets/TurnBasedMMORPG/docs/ru/management/deployment.md:179), [.github/workflows/deploy-production.yml:104](D:/Workspace/personal/pets/TurnBasedMMORPG/.github/workflows/deploy-production.yml:104), [src/backend/app.py:97](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/app.py:97).
- **Secondary gates / ограничения:** VERIFY-FIRST operational evidence/restore rehearsal plan; не запускать restore/deploy или читать production, Observation retained. **Исторические ограничения:** A08-15: Observation: external ops may exist; repo absence не server absence.
- **Будущая необходимая проверка (сейчас не выполнена):** A08-15: Gather schedules/roles/retention, isolated restore/drill/alert/readiness/TLS proof.

### A09-01 — история боя повторно читается и записывается целиком

- **Original IDs / source severity:** A09-01 — High; [audit/09_performance_scalability.md:64](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/09_performance_scalability.md:64); аудит 09. [Canonical в реестре:1070](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:1070).
- **Историческая доказательность:** A09-01: Исторически воспроизведено локальной проверкой/тестом исходного аудита; сейчас не повторялось. **Стадия:** Pre-alpha.
- **PRIMARY:** TECH-HARDENING. **Почему:** Delta IO и logs paging можно изменить технически при неизменной последовательности/combat facts. **RC:** [RC-15:210](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:210). **Возможный package:** WP-combat-io.
- **Технический/owner контракт исходной находки:** Combat logs; Redis; Serialization. Commit cost не повторяет всю immutable history.
- **Выполнено сейчас — статическое чтение:** Commit вызывает _merge_logs_by_turn; merge загружает get_logs_by_turn; get_logs сначала flatten всех logs, потом slice. **Прочитанные anchors:** [src/backend/infrastructure/combat/managers/session.py:606](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/combat/managers/session.py:606), [src/backend/infrastructure/combat/managers/session.py:803](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/combat/managers/session.py:803), [src/backend/infrastructure/combat/managers/session.py:828](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/combat/managers/session.py:828).
- **Secondary gates / ограничения:** Synthetic timings исторические; no p95/CCU claim; оптимизация обязана сохранять version/atomicity/order/retry. **Исторические ограничения:** A09-01: Исторические fake-Redis method probes; ms не e2e/p95/SLA.
- **Будущая необходимая проверка (сейчас не выполнена):** A09-01: Bytes/commit vs history, order/retry semantic invariants, real latency.

### A09-02 — частый глобальный AC scan и неполная fairness

- **Original IDs / source severity:** A09-02 — High; [audit/09_performance_scalability.md:72](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/09_performance_scalability.md:72); аудит 09. [Canonical в реестре:1079](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:1079).
- **Историческая доказательность:** A09-02: Исторически воспроизведено локальной проверкой/тестом исходного аудита; сейчас не повторялось. **Стадия:** Shared infrastructure (Pre-alpha).
- **PRIMARY:** TECH-HARDENING. **Почему:** Scan work budget/fair cursor технические; regen calculations/timing policy не менять. **RC:** [RC-16:222](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:222). **Возможный package:** WP-ac-sync.
- **Технический/owner контракт исходной находки:** AC vitals scanner; Redis; System cron. Scan budget/fairness bounded vs candidates.
- **Выполнено сейчас — статическое чтение:** scan_vitals_regen_candidates начинает cursor=0 и проверяет state; result limit не является полным work limit. **Прочитанные anchors:** [src/backend/infrastructure/actor_state/managers/session.py:520](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/actor_state/managers/session.py:520).
- **Secondary gates / ограничения:** Future real Redis load/fairness measurement; budget без пропуска eligible characters и без изменения approved regen rate. **Исторические ограничения:** A09-02: Исторический fake order; real SCAN count hint, no guaranteed starvation.
- **Будущая необходимая проверка (сейчас не выполнена):** A09-02: Examined/selected commands, rotating fairness, realistic AC/Redis profile.

### A09-03 — архивирование чата имеет низкий фиксированный потолок

- **Original IDs / source severity:** A09-03 — High; [audit/09_performance_scalability.md:80](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/09_performance_scalability.md:80); аудит 09. [Canonical в реестре:1088](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:1088).
- **Историческая доказательность:** A09-03: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Pre-alpha.
- **PRIMARY:** TECH-HARDENING. **Почему:** Archive drain bounded durability технический; retention и UX не пересматриваются. **RC:** [RC-16:222](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:222). **Возможный package:** WP-chat-archive.
- **Технический/owner контракт исходной находки:** Chat archive; Redis buffers; Mongo; SQL. Service drain budget keeps accepted backlog within retention.
- **Выполнено сейчас — статическое чтение:** Archive count500 раз за stream; cron раз10мин; producer maxlen5000 trims; курсор failure semantics отдельный A05-06. **Прочитанные anchors:** [src/backend/chat/workers/archive.py:35](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/chat/workers/archive.py:35), [src/backend/chat/services/message_service.py:45](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/chat/services/message_service.py:45), [src/backend/config/settings.py:85](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/config/settings.py:85), [src/backend/chat/workers/archive.py:218](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/chat/workers/archive.py:218).
- **Secondary gates / ограничения:** Arrival/backlog реальные неизвестны; prior synthetic rates not deployment capacity; preserve history durability contract. **Исторические ограничения:** A09-03: Arithmetic cap не measured database throughput/incident.
- **Будущая необходимая проверка (сейчас не выполнена):** A09-03: Arrival/drain/oldest age/retention isolated load, recovery preserved.

### A09-04 — процессный предел и задержка за медленным получателем WebSocket

- **Original IDs / source severity:** A09-04 — High; [audit/09_performance_scalability.md:88](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/09_performance_scalability.md:88); аудит 09. [Canonical в реестре:1097](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:1097).
- **Историческая доказательность:** A09-04: Исторически воспроизведено локальной проверкой/тестом исходного аудита; сейчас не повторялось. **Стадия:** Pre-alpha.
- **PRIMARY:** TECH-HARDENING. **Почему:** Slow-sink isolation/worker topology — transport reliability, не изменение chat semantics. **RC:** [RC-16:222](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:222). **Возможный package:** WP-chat-fanout.
- **Технический/owner контракт исходной находки:** Chat WebSocket; Connection manager; Realtime. Recipient backpressure isolated; replicas share live delivery.
- **Выполнено сейчас — статическое чтение:** ChatConnectionManager local dict topics; broadcast_topic sequential await send_text; producer ждёт broadcast before xadd. **Прочитанные anchors:** [src/backend/chat/services/connection_manager.py:19](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/chat/services/connection_manager.py:19), [src/backend/chat/services/message_service.py:39](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/chat/services/message_service.py:39), [deploy/compose.game.yml:81](D:/Workspace/personal/pets/TurnBasedMMORPG/deploy/compose.game.yml:81), [src/backend/chat/services/connection_manager.py:76](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/chat/services/connection_manager.py:76).
- **Secondary gates / ограничения:** Single-process local fanout допустим при подтверждённой topology; broker не mandatory; future slow-sink/order/restart evidence. **Исторические ограничения:** A09-04: Исторический fake socket order; not whole event-loop blockage; current1process not broken by replication hypothesis.
- **Будущая необходимая проверка (сейчас не выполнена):** A09-04: Bounded slow-consumer queue/drop, two-process room delivery, memory/connection.

### A09-05 — combat повторно загружает весь бой для каждого AI и сохраняет всех actors

- **Original IDs / source severity:** A09-05 — Medium; [audit/09_performance_scalability.md:96](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/09_performance_scalability.md:96); аудит 09. [Canonical в реестре:1106](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:1106).
- **Историческая доказательность:** A09-05: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha.
- **PRIMARY:** TECH-HARDENING. **Почему:** Load/write projection можно уменьшить при сохранении AI input/combat result. **RC:** [RC-15:210](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:210). **Возможный package:** WP-combat-io.
- **Технический/owner контракт исходной находки:** Combat; AI workers; Actor snapshots; Redis. Batch costs tied relevant actors/version rather than B full snapshots.
- **Выполнено сейчас — статическое чтение:** AI task load_battle_context; integration собирает all teams actors; full context pipeline actor/moves/actionqueue; commit iterates ctx.actors. **Прочитанные anchors:** [src/backend/features/combat/integrations/session_integration.py:339](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/integrations/session_integration.py:339), [src/backend/infrastructure/combat/managers/session.py:551](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/combat/managers/session.py:551), [src/backend/features/combat/workers/tasks/ai_turn_task.py:51](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/workers/tasks/ai_turn_task.py:51), [src/backend/features/combat/integrations/session_integration.py:417](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/integrations/session_integration.py:417).
- **Secondary gates / ограничения:** Запрещено менять AI decisions/turn order; compare same frozen context, compatible with combat-commit before optimization. **Исторические ограничения:** A09-05: Pipeline RT≠commands; collector queue threshold bounds Q.
- **Будущая необходимая проверка (сейчас не выполнена):** A09-05: Representative B/N effects, touched writes/bytes, snapshot parity.

### A09-06 — дубли sync превращаются в повторные полные SQL writes

- **Original IDs / source severity:** A09-06 — Medium; [audit/09_performance_scalability.md:104](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/09_performance_scalability.md:104); аудит 09. [Canonical в реестре:1115](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:1115).
- **Историческая доказательность:** A09-06: Исторически воспроизведено локальной проверкой/тестом исходного аудита; сейчас не повторялось. **Стадия:** Pre-alpha.
- **PRIMARY:** TECH-HARDENING. **Почему:** Job coalescing и clean no-op — техническая sync boundary. **RC:** [RC-11:162](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:162), [RC-15:210](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:210). **Возможный package:** WP-ac-sync.
- **Технический/owner контракт исходной находки:** Character sync; Middleware; SQL; ARQ. Clean duplicate sync не full durable rewrite.
- **Выполнено сейчас — статическое чтение:** Middleware dirty check существует; ARQ default uuid job id; _dirty_targets clean marker returns None→legacy/full sync interpretation. **Прочитанные anchors:** [src/backend/core/middleware.py:30](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/core/middleware.py:30), [.venv/Lib/site-packages/arq/connections.py:148](D:/Workspace/personal/pets/TurnBasedMMORPG/.venv/Lib/site-packages/arq/connections.py:148), [src/backend/features/character/integrations/system_integrator.py:117](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/character/integrations/system_integrator.py:117), [src/backend/features/character/integrations/system_integrator.py:56](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/character/integrations/system_integrator.py:56), [src/backend/core/middleware.py:48](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/core/middleware.py:48).
- **Secondary gates / ограничения:** Fresh source confirms guard, not every request unconditional; future duplicate queued jobs+clean sync evidence; no lost dirty. **Исторические ограничения:** A09-06: Исторический mocked-repo source probe; SQL statement counts не measured.
- **Будущая необходимая проверка (сейчас не выполнена):** A09-06: Dirty-generation enqueue/write counts, clean repeat no effect, unsafe expedition exception.

### A09-07 — Rift tick переписывает instance, flush обходит чужие sessions

- **Original IDs / source severity:** A09-07 — Medium; [audit/09_performance_scalability.md:112](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/09_performance_scalability.md:112); аудит 09. [Canonical в реестре:1124](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:1124).
- **Историческая доказательность:** A09-07: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Legacy (поддержка runtime неизвестна).
- **PRIMARY:** EXPERIMENTAL-LEGACY. **Почему:** Full Rift payload/session sweep perf — Legacy runtime, support decision required. **RC:** [RC-15:210](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:210), [RC-16:222](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:222). **Возможный package:** —.
- **Технический/owner контракт исходной находки:** Old Rift tick/checkpoint; Redis scan. Personal tick/checkpoint budget bounded by owner/instance.
- **Выполнено сейчас — статическое чтение:** Player _save_runtime_update copies previous session; instance store serializes full runtime $; dirty flush loads snapshot. **Прочитанные anchors:** [src/backend/features/rift/services/player_service.py:218](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/services/player_service.py:218), [src/backend/infrastructure/rift/managers/instance.py:25](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/rift/managers/instance.py:25), [src/backend/features/rift/integrations/runtime.py:287](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/rift/integrations/runtime.py:287).
- **Secondary gates / ограничения:** No auto hardening of unsupported runtime; historical synthetic amplification not real benchmark. **Исторические ограничения:** A09-07: Small presets; no High without profile; graph copy per participant не доказана.
- **Будущая необходимая проверка (сейчас не выполнена):** A09-07: Tick bytes/RT, examined keys, same-instance coalescing preserving consistency.

### A09-08 — Mongo chat возвращает растущий bucket после каждой записи

- **Original IDs / source severity:** A09-08 — Medium; [audit/09_performance_scalability.md:120](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/09_performance_scalability.md:120); аудит 09. [Canonical в реестре:1133](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:1133).
- **Историческая доказательность:** A09-08: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Pre-alpha.
- **PRIMARY:** TECH-HARDENING. **Почему:** Returned Mongo payload projection — техническая оптимизация archive append. **RC:** [RC-15:210](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:210). **Возможный package:** WP-chat-archive.
- **Технический/owner контракт исходной находки:** Chat Mongo buckets; SQL references. Append response ограничен необходимым count/meta.
- **Выполнено сейчас — статическое чтение:** find_one_and_update returns stored document after message append; metadata needed for BucketRef can be narrow. **Прочитанные anchors:** [src/backend/infrastructure/mongo/chat_buckets.py:59](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/mongo/chat_buckets.py:59), [src/backend/infrastructure/mongo/chat_buckets.py:81](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/infrastructure/mongo/chat_buckets.py:81).
- **Secondary gates / ограничения:** Real Mongo bytes/latency future; don't change seq/dedup without A05-15 contract verification. **Исторические ограничения:** A09-08: Nominal1000 bounded; no full SQL N+1/message claim; BSON overflow unknown.
- **Будущая необходимая проверка (сейчас не выполнена):** A09-08: Append/returned bytes, projection contract, bucket/history boundaries.

### A09-09 — GenerationAI удерживает SQL connection/transaction через долгую внешнюю работу

- **Original IDs / source severity:** A09-09 — Medium; [audit/09_performance_scalability.md:126](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/09_performance_scalability.md:126); аудит 09. [Canonical в реестре:1142](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:1142).
- **Историческая доказательность:** A09-09: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. Сейчас выборочно подтверждены только указанные статические предпосылки. **Стадия:** Shared infrastructure (Pre-alpha).
- **PRIMARY:** TECH-HARDENING. **Почему:** SQL connection/lock lifetime across provider awaits — resource reliability. **RC:** [RC-16:222](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:222). **Возможный package:** WP-ai-resource-budget.
- **Технический/owner контракт исходной находки:** GenerationAI SQL claim; Provider; Asset/Mongo. Connection/transaction lifetime limited separately external work.
- **Выполнено сейчас — статическое чтение:** Repository claim with_for_update(skip_locked); worker manual session surrounds process_task and commits afterwards. **Прочитанные anchors:** [src/backend/features/generation_ai/repositories.py:132](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/repositories.py:132), [src/backend/features/generation_ai/workers/tasks.py:20](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/workers/tasks.py:20).
- **Secondary gates / ограничения:** Claim/lease/recovery revision before early commit; retain single task effect consistency, don't parallelize AI/content blindly. **Исторические ограничения:** A09-09: Lock impact not profiled; SKIP LOCKED already prevents waiting on task claim.
- **Будущая необходимая проверка (сейчас не выполнена):** A09-09: Provider/storage timing vs transaction age/pool wait; fault claim/retry contract.

### A09-10 — image normalization синхронно занимает GenerationAI event loop

- **Original IDs / source severity:** A09-10 — Medium; [audit/09_performance_scalability.md:132](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/09_performance_scalability.md:132); аудит 09. [Canonical в реестре:1151](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:1151).
- **Историческая доказательность:** A09-10: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Shared infrastructure (Pre-alpha).
- **PRIMARY:** TECH-HARDENING. **Почему:** Blocking image encode work isolation техническая при сохранении output contract. **RC:** [RC-16:222](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:222). **Возможный package:** WP-ai-resource-budget.
- **Технический/owner контракт исходной находки:** GenerationAI event loop; Image normalization. Sync image work/memory respects event-loop/job budget.
- **Выполнено сейчас — статическое чтение:** Async executor calls normalize_generated_image synchronously; PIL open/load/convert/fit in function. **Прочитанные anchors:** [src/backend/features/generation_ai/integrations/codex_ai_executor.py:90](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/integrations/codex_ai_executor.py:90), [src/backend/features/generation_ai/image_normalization.py:42](D:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/generation_ai/image_normalization.py:42).
- **Secondary gates / ограничения:** Pixel bytes/format/size and retry/resource limits preserve; historical timing no current profiling; no generative prompt/model changes. **Исторические ограничения:** A09-10: Fast no-resize WEBP returns early; synthetic timings not production distribution.
- **Будущая необходимая проверка (сейчас не выполнена):** A09-10: Representative dimensions/images timing/RSS/loop lag, fast WEBP path parity.

### A09-11 — browser chat не ограничивает историю живой вкладки

- **Original IDs / source severity:** A09-11 — Medium; [audit/09_performance_scalability.md:138](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/09_performance_scalability.md:138); аудит 09. [Canonical в реестре:1160](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_findings_registry.md:1160).
- **Историческая доказательность:** A09-11: Подтверждено статическим анализом в исходном аудите; полного повторного анализа сейчас нет. **Стадия:** Pre-alpha.
- **PRIMARY:** MIXED. **Почему:** Bounded memory возможно только при approved видимой history; текущий UX запрещено менять. **RC:** [RC-16:222](D:/Workspace/personal/pets/TurnBasedMMORPG/audit/10_root_causes.md:222). **Возможный package:** WP-browser-retention.
- **Технический/owner контракт исходной находки:** Frontend browser chat; Alpine lists. Live history/DOM memory bounded over tab lifetime.
- **Выполнено сейчас — статическое чтение:** Template channels arrays grow via message push and system push; no visible local trimming at insertion. **Прочитанные anchors:** [src/frontend/templates/shared/chat/main.html:6](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/templates/shared/chat/main.html:6), [src/frontend/templates/shared/chat/main.html:182](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/templates/shared/chat/main.html:182), [src/frontend/templates/shared/chat/main.html:269](D:/Workspace/personal/pets/TurnBasedMMORPG/src/frontend/templates/shared/chat/main.html:269).
- **Secondary gates / ограничения:** MIXED: owner-approved live-tail/history/scroll expectation прежде eviction; нельзя silently truncate, DM behavior/reconnect keep. **Исторические ограничения:** A09-11: No browser heap/Core Web Vitals measured; backend page cap not live cap.
- **Будущая необходимая проверка (сейчас не выполнена):** A09-11: Long-session heap/DOM and bounded tail/history navigation.

## Контроль результата

116 PRIMARY карточек покрывают120 исходных IDs без потерь; только четыре исходные пары разделяют canonical. Никакой NO-ACTION не означает «исправлено». CODE/route presence — локальный статический факт; production applicability, effects under faults и owner decisions не выведены из одного пути/названия/router prefix.

Работа ограничена записью этого Markdown-плана. Gameplay/code/tests/dependencies/CI/config/deploy/skills и исходные audit02–10 не изменялись; новый аудит безопасности не проводился.
