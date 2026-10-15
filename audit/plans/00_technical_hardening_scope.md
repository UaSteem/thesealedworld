# Sealed World — Technical Hardening & Boundary Stabilization: scope

Дата плана:10.10.2026, Europe/Berlin; источники09.10, статическое чтение09–10.10.2026. Режим: READ → VERIFY → CLASSIFY → DESIGN WORK PACKAGES → DOCUMENT → STOP. **Это проект первого этапа, не разрешение на реализацию.**

## 1. Цель и исходные свидетельства

Повысить безопасность, надёжность и проверяемость технических границ существующего pre-alpha приложения, сохранив игровые правила. Объект — текущее рабочее дерево на HEAD `6ccc92561c633f618eb7ee082c36caa44a1400f7`, включая прежние staged/unstaged/untracked изменения пользователя. При начале планирования Git показывает 376 tracked dirty entries; совпадение HEAD не доказывает совпадение dirty tree со старым аудитом.

Основные источники: [master](../10_master_audit.md), [120 исходных ID / 116 canonical](../10_findings_registry.md), [17 системных механизмов](../10_root_causes.md), [skill gaps](../10_skill_gaps.md). Дополнительные A02/A05–09 используются с проверкой текущих файлов; Combat/Rift — только для технических authority, storage, transport и lifecycle contracts. Старый Graphify не используется как актуальная карта.

Техническая severity, доказательность, стадия и классификация scope — независимые оси. TECH-HARDENING не значит «выполнить сейчас»; High не задаёт порядковый номер пакета. Public label Alpha не переопределяет общую Pre-alpha стадию владельца. Production topology, deployed images, secrets, GitHub settings и фактическая публичная доступность неизвестны.

## 2. Разрешённый результат этого запроса

Создать/редактировать только следующие пять документов:

1. [00 — scope](00_technical_hardening_scope.md).
2. [01 — полная классификация](01_technical_findings_matrix.md).
3. [02 — рабочие пакеты](02_technical_work_packages.md).
4. [03 — варианты исполнения](03_execution_options.md).
5. [04 — skills/enforcement backlog](04_skill_enforcement_backlog.md).

Исходный реестр и аудиты не редактируются. Код, тесты/fixtures, CI, Docker/Nginx, схемы/миграции, skills, зависимости, Git state и production не меняются. Планирование не включает новые тестовые файлы, service startup, installations, deployment, production reading, эксплуатационные/нагрузочные пробы или автоматический переход к реализации. Допустимы чтение актуальных исходников/конфигурации, проверка связей/номеров строк и структурная проверка пяти документов. Доказательства исторических тестов не обозначаются как повторно выполненные.

## 3. Кандидаты в техническую стабилизацию

| Граница | Допустимая цель будущего пакета | Условие допуска |
| --- | --- | --- |
| HTTP/WS caller → операция/объект | Проверяемые principal, role, session, ownership/membership; auth до reads/mutations/queue | Подтверждены caller class и consumers, есть legitimate positive case и negative matrix |
| Player command → server fact | Клиент не задаёт серверный outcome/attributes/diagnostic overrides | Установлен reachable server-owned путь; если его нет, запрет bypass и незавершённая механика разделяются, replacement gameplay не создаётся |
| Internal/admin/dev ingress | Environment publication policy и backend permissions независимо друг от друга | Принята route audience matrix; Nginx не считается заменой backend authorization |
| Secrets/service identity/session | Fail-closed config, цели/scopes credentials, ясная revocation/rotation | Не вводится один универсальный token для всех consumers; migration/compatibility credentials отдельно утверждены |
| Logs/metrics/external data | Redaction, ограниченная cardinality, безопасные typed/contained inputs | Legitimate diagnostics и rich-text/product contract сохранены; XSS/PII incident не утверждается по sink alone |
| Dependency/build/promotion | Clean source resolution, checked artifact provenance, meaningful CI inputs/events | Источник зависимостей и поддерживаемые platforms подтверждены; не допускается «просто убрать gate» |
| Storage/transport/recovery | Восстанавливаемое принятие, version-aware commit/flush, понятный duplicate/error contract | Авторитет состояния и operation identity установлены; real-adapter проверка возможна изолированно; replay не включается до safe effect contract |
| Domain boundaries | Semantic owner facade/integration, stable public DTO и manager-owned keys | Общая SQL UoW и наблюдаемые transitions сохраняются; никакого mass move/services rewrite |
| Resource budgets | Меньше лишнего payload/scan, bounded queues/drain/slow consumer handling | Сохранены ordering, durable acceptance, result полнота и допустимый latency; требующий product выбора retention отложен |
| Testing/enforcement | Negative/positive security, API/storage/retry contracts и validators | Тест достигает опасной precondition; fake не выдаётся за real storage; thresholds не подменяют контракт |

## 4. Что строго исключено

Не меняются damage/crit formulas, attributes, modifiers, balance, classes, abilities/effects, turn rules, AI combat policy, loot tables, XP/progression formulas, экономика, World/Rift generation rules, hex geometry, story/Scenario rules, content и игровой UI/UX. Незавершённая механика не реализуется под видом security patch. Никакого native rewrite, нового microservice, общего distributed-transaction framework или нового skill на каждый дефект.

A03-13 crit-bleed — gameplay runtime issue: этот этап может сделать его regression control честным (A06-02), но не изменить эффект. Seed/RNG/generation, fog-of-war, Knowledge XP cap и heart/reward rules не становятся техническими задачами по одному audit ID. Player authority defect A04-01/A07-05 относится к Legacy Rift: не превращает технический Hex prototype в обязательный полноценный dungeon.

## 5. Как сохраняется игровая семантика

Для каждого будущего изменения фиксируются отдельно:

- **Технический инвариант:** кто имеет право вызвать, какую версию подтвердить, какие данные приняты, как корректно повторить/прочитать/восстановить.
- **Игровой инвариант:** какой именно outcome, reward amount, trigger, death/travel/loot state transition уже утверждён. Формулы и policy не редактируются.
- **Источник истины:** SQL fact/owner, live Redis state, durable checkpoint и Mongo payload/pointer; слово «cache» не скрывает принятую несохранённую state.
- **Replay contract:** stable identity, duplicate before/after commit, conflicting same-ID input, error/restart boundaries и response loss.
- **Positive parity:** существующий разрешённый caller и нормальный gameplay получают прежний результат/награду/порядок; unauthorized requests отклоняются раньше side effects.

Защита «один утверждённый reward один раз» допустима только при подтверждённом operation identity и once-only бизнес-контракте. Если источник этого решения отсутствует, запись остаётся MIXED и пакет содержит decision gate, а не готовую ledger-схему. Retry/Reclaim без этого допуска запрещён: recovery может усилить double application. Нельзя массово превратить read-check-write в lock или outbox, не установив ошибки/authoritative store конкретного owner.

Транспортное разделение feature не оправдывает разрыв полезной общей SQL-транзакции Expedition/Loot. Semantic facade может принимать общий UoW; оставшийся commit принадлежит use case. Runtime/path/DTO refactor сохраняет wire/storage shape либо получает отдельно проверяемую DATA-MIGRATION. Blind stamp/drop/wipe и silent fallback запрещены. См. [ownership](../../.agents/skills/turnbasedmmorpg-project/references/project-rules.md), [compatibility](../../.agents/skills/turnbasedmmorpg-project/references/compatibility-decisions.md), [hybrid persistence](../../.agents/skills/turnbasedmmorpg-backend/references/storage-ownership.md).

## 6. Классификация полного реестра

Ровно одна primary scope-class у каждого из 116 canonical; все 120 original IDs сохранены. Вторичные ограничения не теряются, но не суммируются как дополнительные findings.

| Primary class | Значение |
| --- | --- |
| TECH-HARDENING | Подтверждённая техническая граница; возможное исправление сохраняет существующие игровые правила |
| GAME-DESIGN | Утверждённое/предлагаемое игровое правило является предметом изменения; отдельное решение владельца |
| MIXED | Техническое исправление требует неустановленного gameplay/operation contract или меняет наблюдаемую семантику |
| EXPERIMENTAL-LEGACY | Surface отдельно experimental/dev-only/legacy; не включается автоматически в основной этап |
| VERIFY-FIRST | Не хватает текущего причинного доказательства, конфигурации или server semantics; сначала ограниченная проверка |
| NO-ACTION | Observation/допустимый компромисс или доказанно устранённая проблема; факт устранения требует источника |

Из наблюдения не производится обязательный refactor. Отсутствие source-first recheck не маскируется TECH. По группе полного дубля сохраняются исходные оценки участников (например High/Medium для AI input), а не придумывается усреднённая severity. Root cause — механизм RC, не обещание одного общего изменения. Ненумерованные narrative observations A10 сохранены как контекст и verification questions; они не создают 117-ю canonical запись.

## 7. Experimental/Legacy и public security

Старый player Rift — Legacy относительно нового Hex, поддержка/публикация неизвестны. Его data/access defects действуют при использовании и не обесцениваются стадией; owner должен отдельно выбрать support/harden/freeze/retire. Изменение game result/reward/travel этой поверхности не входит автоматически. Новый Hex — Experimental/Dev-only technical prototype; allowlist/default-off/bounded publication рассматриваются отдельно от добавления battles/resources/game loop.

Studio предназначена для Dev-only анализа. Если selected source имеет live credentials, read-only и permission scope значимы независимо от локального UI. Отключение опасного доступа и реализация новых функций Studio не объединяются. Local/observability Compose не приравнивается к production, но публикация на внешнем интерфейсе требует проверки контекста.

**Отдельная срочная проверка экспозиции:** A07-02/03/04 и A08-03. Текущее source wiring может допустить config/administrative/internal calls без principal за общим `/api/` proxy. Проверено чтением, а не attack. Без доступа к VPS можно составить exact route/consumer matrix и negative tests на синтетическом изолированном app; реальные image/flags/network требуют отдельно разрешённого read-only operational evidence. Сейчас production не исследуется. Эта проверка не ждёт завершения всех рабочих пакетов и не запускает изменения самостоятельно.

## 8. Критерии допуска будущего пакета

1. Владелец отдельно утвердил конкретный пакет, boundaries и открытые решения; план сам не является approval.
2. Current code/consumer path и guards заново подтверждены; источник не ограничен dirty-tree SHA или историческим report.
3. Primary class/secondary gates позволяют реализацию; MIXED/GAME-DESIGN и Legacy решения закрыты явно.
4. Есть positive/negative acceptance criteria, failure/retry contract и appropriate isolated test fixture. Сторонняя library owner/source учитываются, installed library не правится в consumer checkout.
5. Leaf write ownership для параллельных исполнителей непересекается; common auth/model/manager/CI change имеет одного интегратора.
6. Release/wipe risk определён: NONE для unchanged facts/shapes; DATA-MIGRATION при persisted changes и проверенной migration; WIPE требует отдельного решения и не входит автоматически.
7. Rollback поддерживает admitted data/credentials и старых legitimate consumers; security rollback не означает временное возвращение публичного anonymous admin bypass.

## 9. Критерии завершения будущей стабилизации

Оценивается только утверждённое подмножество пакетов, а не все 116 findings. По нему выполнены targeted regression/integration/contract проверки, full required gates и documented release checks; подтверждены source/build/provenance и agreed publication policy; принятые операции имеют проверенное interrupted-retry/readback/recovery; valid callers/gameplay сохраняют согласованную семантику. Нет неожиданного изменения формул/content/UI. Updated docs/skills/validators отражают реальные новые contracts; неподтверждённые operational условия остаются отмечены, не называются solved.

Для этого **планового запроса** завершение означает пять согласованных Markdown-документов, coverage 116 canonical/120 original IDs, непротиворечивые package aliases/зависимости, сохранённые stages/severity, explicit decision gates и проверенные ссылки. Реализация, current full-suite pass, production capacity/security/recovery attestation не являются результатом планирования.

## 10. Проверка пятифайлового результата — 10.10.2026

Подготовлено ровно пять разрешённых документов: scope, matrix,37 рабочих пакетов,3 execution options,19 K/W/E backlog proposals. Матрица содержит116 уникальных canonical карточек и120 уникальных original IDs; четыре duplicate pairs сохранены, потерь/новых IDs нет. PRIMARY counts:68 TECH-HARDENING,3 GAME-DESIGN,9 MIXED,17 EXPERIMENTAL-LEGACY,14 VERIFY-FIRST,5 NO-ACTION. Все matrix package IDs существуют; original associations отражены в source fields карточек с отдельными narrow gates; каждая из37 карточек имеет все15 требуемых полей и explicit admission.

Проверены858 локальных Markdown-ссылок и735 явных file:line anchors, также line numbers в labels: missing/out-of-range отсутствуют. Эти structural checks не являются runtime или security tests. SHA256 исходных audit01–09,09_performance_probes.py и четырёх master10 документов совпали со снятой перед планированием базой (14 файлов). HEAD неизменен; tracked dirty count остаётся376. Существовавшие пользовательские изменения не исправлялись/не переносились. Разрешённые записи этого задания ограничены пятью файлами audit/plans.

Не исполнялись pytest/collection/probes, services/stores/migrations, builds/install, CI/deploy, production checks или proposed skills/validators. Статическое повторное чтение сохранено отдельно от historical evidence и будущих acceptance tests. Выбор варианта, permission/effect/Legacy/retention/deployment решения оставлены владельцу; выполнение пакетов не начато. **STOP.**
