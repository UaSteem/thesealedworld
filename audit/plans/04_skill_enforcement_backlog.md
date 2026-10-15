# 04 — Предложения к project skills, validators и Quality Gates

Дата плана:10.10.2026; источники09.10, чтение09–10.10.2026. Режим: **PLAN ONLY → DOCUMENT → STOP**. Этот файл — backlog предложений для технической стабилизации Sealed World. Он не изменяет навыки, код, тесты, CI, зависимости, данные или игровой контракт и не разрешает начинать рабочие пакеты.

Источники: [master audit](../10_master_audit.md), [116 canonical findings / 120 original IDs](../10_findings_registry.md), [RC-01–17](../10_root_causes.md), [skill gaps](../10_skill_gaps.md). Классификация каждой находки и окончательное соответствие пакетам находятся в соседних документах плана. Здесь aliases соответствуют стабильным IDs `WP-<alias>` в [37 пакетах](02_technical_work_packages.md); B01–19 — отдельная нумерация предложений backlog, не число рабочих пакетов.

## 1. Допуск и доказательность

Система — pre-alpha; Hex — отдельный experimental prototype; прежний player Rift — legacy с неизвестной дальнейшей поддержкой. Severity не понижается по стадии, но urgency и scope зависят от публикации и решения владельца. Наличие Compose/router не доказывает production exposure. Потенциально публичные административные API требуют отдельной разрешённой проверки экспозиции; в этом задании production не проверяется.

**Knowledge (K)** — устойчивый контракт, который агенту нужно знать; **Workflow (W)** — повторяемая процедура проверки; **Enforcement (E)** — измеримый тест/validator/CI signal. Если правило уже есть, достаточно адресного уточнения и нового сигнала. Разовый дефект не превращается в новый global skill.

Доступны три уровня допуска:

1. **Техническое предложение:** auth/permissions, secret validation, serialization, сохранение/доставка, совместимость API/migrations и измерение технических ресурсов без изменения gameplay.
2. **VERIFY-FIRST:** прежде чем выбрать исправление, установить contract/config/package version либо доказать окно отказа в изолированной среде.
3. **Условное / отложенное:** once-only reward, unknown combat outcome, lifecycle/retention policy, legacy/Hex migration или правило механики требуют явного решения владельца. Можно описать проверку прежнего поведения; нельзя утвердить новое ожидаемое игровое поведение через тест.

Игровые формулы, количество XP/ресурсов, loot tables, AI decision policy, turn rules, abilities/effects, World/Rift generation, Hex geometry, Scenario/game content и игровая UI/UX семантика исключены. Техническая route isolation не превращает Hex в обязательную beta-фичу. SQL-транзакцию Expedition/Loot нельзя дробить ради формального ownership.

Новые проверки ниже **предложены, не исполнены**. В этом проходе выполнено чтение/статическая сверка маршрутов/auth/DTO consumers, settings, metrics/logging configuration, manager commit/dirty operations, chat cursor, AI commit/enqueue, archive reader, validators, CI и dependency manifest. Прежние pytest/probes остаются историческими результатами аудитов; real storage, hosted CI, Docker, ARQ, dependency install и production не запускались. Для остальных узких manifestation evidence сохранён исходный audit anchor, который надо перепроверить перед реализацией.

## 2. Существующие правила и защиты

| Уже есть | Текущий источник | Что это не доказывает |
| --- | --- | --- |
| Backend character owner check и feature-owned semantic integrations | [backend architecture:26](../../.agents/skills/turnbasedmmorpg-backend/references/feature-architecture.md), [project rules:18](../../.agents/skills/turnbasedmmorpg-project/references/project-rules.md) | Подключение dependency к каждому route; отсутствие всех foreign state writes |
| Typed frontend API clients, запрет game internals, site-owned repositories | [frontend architecture:29](../../.agents/skills/turnbasedmmorpg-frontend/references/feature-architecture.md), [BaseApiClient:12](../../src/frontend/core/api.py) | Backend response и frontend fixture имеют один контракт; blanket запрет frontend DB конфликтует с site ownership |
| Meaningful contract/edge tests и real-boundary integration; риск-пропорциональный gate | [testing:5](../../.agents/skills/turnbasedmmorpg-quality/references/testing.md), [validation:3](../../.agents/skills/turnbasedmmorpg-quality/references/validation.md) | Fakes повторяют RedisJSON/Lua/SQL concurrency/Streams; negative test активировал проверяемую precondition |
| Source of truth / Mongo schema_version / retry write status | [storage ownership:8](../../.agents/skills/turnbasedmmorpg-backend/references/storage-ownership.md), [document patterns:88](../../.agents/skills/turnbasedmmorpg-backend/references/document-patterns.md) | SQL checkpoint совпадает с live runtime, producer obligation durable и replay идемпотентен |
| No-PII logging; thin handlers и semantic stream clients | [logging:43](../../.agents/skills/turnbasedmmorpg-quality/references/logging.md), [Streams:59](../../.agents/skills/turnbasedmmorpg-backend/references/redis-streams.md) | Redaction exception locals/access log/metrics; место correlation context согласовано между двумя правилами |
| Main full gate, build needs quality, lockfile, non-root runtime; слойный/manual deploy | [CI:43](../../.github/workflows/ci.yml), [deployment:41](../../.agents/skills/turnbasedmmorpg-release/references/deployment.md) | Develop behavioral gate, clean checkout install, immutable digest/provenance либо repository approvals |
| Items/skills/scenario fixture validators и ограниченные ownership tests | [validator:12](../../tools/validators/run.py), [boundaries:7](../../tests/backend/features/test_infrastructure_boundaries.py) | Все key spaces/imports/DTO проверены: [prefix scan:63](../../tests/backend/features/test_infrastructure_boundaries.py) исключает Rift |
| Studio selected source read-only | [Studio skill:8](../../.agents/skills/turnbasedmmorpg-studio/SKILL.md) | Программный запрет HTTP mutations; local compute вне selected source само по себе не нарушает контракт |

Работающий JWT decoder, game-session lock, Scenario/Inventory ownership, frontend cabinet superuser/CSRF, WS Origin, owner-aware Redis release, SQL locks/unique identities, shared live/simulation executor и schema validation сохраняются. Новая защита дополняет их, а не объявляет существующие safeguards отсутствующими.

## 3. Backlog K / W / E

### B01 — Route policy и object entitlement

**Aliases:** `auth-game`, `auth-config`, `auth-admin`, `auth-internal`, `chat-access`. **IDs:** A07-01/02/03/04/06/07/13, A08-03; RC-01, RC-04. A07-01 в части legacy Rift условен решением о поддержке. Технический core допускается без изменения игровых правил. Сложность контроля Medium.

**Evidence:** [Combat router:27](../../src/backend/features/combat/api/router.py), [GameConfig:6](../../src/backend/features/game_config/api/router.py), [GenerationAI:23](../../src/backend/features/generation_ai/api.py), [Chat history:27](../../src/backend/chat/api/router.py), [Chat send bridge:78](../../src/backend/realtime/services/chat_bridge.py); полные affected routes/consumers — A07 §§3–5/10. Статически current handlers не устанавливают нужный principal либо получают caller, но не используют его в history/membership decision.

**K:** owner check уже обязателен; предлагаемое расширение — каждый опубликованный HTTP/WS adapter имеет явные audience, verified principal, operation и object scope. Player identity, admin capability и internal service identity — разные credentials; одно название `/internal` не задаёт policy. Разные read/write permissions и public chat channels описываются явно.

**W:** новая/изменённая route требует матрицу entrypoint → expected caller → credential → resource ownership/membership → allowed fields → consumers → failure response. Проверить inherited router/dependency/lifespan wiring, frontend/admin clients и worker/service callers; не считать UI/edge auth достаточным.

**E:** route inventory с обязательной явной policy или документированным public exception плюс сценарии через actual app assembly. Negative: missing credential, valid wrong audience, обычный player в admin/config, чужой character/conversation, запрет private history/send scope. Positive: owner/участник, разрешённый public channel, проверенный service/admin caller и штатный typed consumer проходят. Denial происходит до runtime read/write/enqueue с реальной проверкой отсутствия эффекта. Скан decorator names сам по себе недостаточен. Policy identifiers/permissions ещё требуют решения владельца, но не игровые mechanics.

### B02 — Site identity, selected character, logout/refresh/WS lifecycle

**Alias:** `session-lifecycle`. **IDs:** A07-08/09/10/11/16, A05-12; RC-03, RC-08. A07-16 — VERIFY-FIRST; revocation delay/long-lived WS policy согласовать отдельно. Medium.

**Evidence:** [auth:16](../../src/backend/core/auth.py), [scope:63](../../src/backend/core/auth.py), [WS bootstrap:123](../../src/backend/realtime/api/ws.py), [auth persistence:67](../../src/frontend/features/auth/integrations/auth_persistence.py). Current site/game decode converge в AuthenticatedUser, game scope пропускается при отсутствии claims; refresh commits рассматриваются A05-12.

**K:** identity ≠ active account ≠ выбранный character ≠ действующая game session. Уточнить token audience/type, source actor identity, disable/logout/replace/expiry semantics для HTTP/refresh/WS; rotation сохраняет один согласованный state transition. Existing signature/expiry/single-session protections сохраняются.

**W:** пройти login → select → HTTP → refresh → replace → logout/disable → existing socket. Проверить cookies/domain cleanup, clients/refresh error handling и reconnect; authoritative state берётся из утверждённого owner contract.

**E:** negative URL actor mismatch, site token на game-only mutation, replaced/disabled/replayed refresh, failure между rotation steps. Positive active owner session, allowed site account operations и обычное renewal/reconnect работают. Для concurrent rotation использовать isolated PG; WS revocation утверждать только после определения максимальной задержки и policy. Не вводить silent fallback, оживляющий отозванную session.

### B03 — Internal/dev публикация и Studio selected-source capabilities

**Aliases:** `surface-isolation`, `studio-readonly`. **IDs:** A07-12/15, A08-03/04/08; RC-04, контекст RC-05. Hardening runtime publication — technical; Hex progression/legacy support — вне допуска. Medium, settings evidence current; actual exposure VERIFY-FIRST.

**Evidence:** [dev router assembly:179](../../src/backend/features/rift/api/router.py), [default flag:59](../../src/backend/config/settings.py), [Nginx API proxy:120](../../deploy/nginx/site.conf.template), [Studio selected URL:67](../../src/studio/features/cabinet/modules/combat_ai_testing/cabinet.py), [mutators:1516](../../src/studio/features/cabinet/modules/combat_ai_testing/cabinet.py). Source allowlist и SQL read-only role не ограничивают backend HTTP POST.

**K:** env label, DEBUG=False, sidebar absence и endpoint prefix не являются authorization. Selected-source read-only применяется к HTTP/DB/Redis/enqueue. Local compute может существовать через отдельно разрешённый канал вне selected source; не считать само вычисление нарушением.

**W:** inventory router table/edge path/bind/profile по env; source × action × credential для Studio; определить intended dev usage и backup/data principal. Local bind default и production deny проверять раздельно, не подключаясь к VPS в планировании.

**E:** negative restricted env не монтирует dev route либо гарантированно отказывает; unknown ID GET не запускает неограниченную генерацию; selected read-only source не вызывает POST/queue/write независимо от UI controls. Positive разрешённые dev auth/fixture, selected-source reads и source switcher работают. Если local compute разрешён, отдельный positive test доказывает, что он не пишет selected source. Hex quota/capacity числа — technical resource contract, требующий утверждения; geometry/edge masks/heart progression не меняются.

### B04 — Fail-closed secrets и минимальные runtime permissions

**Aliases:** `secret-validation`, `runtime-isolation`; для role/network проверки — зависимость `surface-isolation`. **IDs:** canonical A07-14 (original A07-14/A08-01), A08-02/12/13/14; RC-04, RC-05. Secret validation technical; actual grants/umask/forwarded trust VERIFY-FIRST. Small для settings regression, Medium для role contract.

**Evidence:** [backend settings:49](../../src/backend/config/settings.py), [frontend settings:30](../../src/frontend/config/settings.py), [shared env surface:39](../../deploy/compose.site.yml), [deploy workflow](../../.github/workflows/deploy-production.yml); настоящие values не читались и не выводятся.

**K:** production-like startup не принимает пустые/known-default signing/internal keys; runtime principal получает нужные data/provider permissions; migration/admin privileges отделены. Cookie/TLS/forwarded-header expectations проверяются вместе с trusted proxy boundary. Secret bytes не входят в reports/logs.

**W:** settings construct без .env/real secrets; сверить app/service/migration identities и resources, scope mount/network needs, создание env file и restart scope. Причина неизвестного deployment override остаётся unknown.

**E:** negative synthetic defaults/empty keys rejected, forbidden cross-domain read/write denied under runtime identity, untrusted forwarded data не меняет security URL contract; positive distinct valid synthetic values и allowed runtime workflows работают. Compose/static manifest checks — быстрый сигнал, grants/ACL checks — только isolated PG/Mongo/Redis/storage principals. Не «проверять» permissions под суперпользователем и не расширять runtime доступ ради проходящего теста.

### B05 — Redaction и cardinality у разных diagnostic sinks

**Aliases:** `metrics-redaction`, `log-redaction`. **IDs:** A08-05/06/07, контекст A07-16; RC-06, смежный RC-16. Technical; установленный logging library contract и shipped version — VERIFY-FIRST. Medium.

**Evidence:** [metrics dispatch:23](../../src/shared/infrastructure/metrics_middleware.py), [path fallback:45](../../src/shared/infrastructure/metrics_middleware.py), [logging setup:42](../../src/shared/infrastructure/logging_config.py), [Nginx format:20](../../deploy/nginx/nginx.conf). Historical canary A08 не воспроизводился.

**K:** raw path/query, bearer-like identifiers, locals и PII имеют отдельный sensitivity contract; JSON escaping ≠ redaction. Labels используют bounded route shape, включая unknown paths; sanitization не лишает систему полезных status/service/correlation/error class полей.

**W:** traced synthetic secret проходит application exception sink, email/task logs, Nginx access sink и metrics endpoint отдельно. Проверить внешнюю logging dependency в фактически собираемой версии. Location/IP retention/audience не выводить из code defaults.

**E:** negative canary отсутствует во всех captured sinks и random token paths не создают unbounded metric labels; positive aggregate counts/duration/status/error event и safe correlation сохраняются. Не snapshot всего logger message formatting; проверять отсутствие чувствительного input и наличие полезного диагностического контракта. Новый project security skill не требуется.

### B06 — Producer/consumer API, DTO, event и worker registration contracts

**Aliases:** `boundary-dto`, `stream-recovery`, часть `test-controls`. **IDs:** A02-04/08, A06-07, O02-05, A06-11; RC-11, RC-12, RC-13. O02-05 VERIFY-FIRST entrypoint; taxonomy A06-11 — техническая точность, не новая отдельная functional bug. Medium.

**Evidence:** [shared runtime DTO:86](../../src/shared/schemas/inventory.py), [frontend API:12](../../src/frontend/core/api.py), [system task registry:55](../../src/backend/features/system/workers/arq.py), [quality test stage:200](../../pyproject.toml). Current validator проверяет content fixtures, не API roundtrip.

**K:** public API DTO и backend runtime shape различаются; HTTP status/envelope/errors, Streams serialized payload и ARQ queue/job/result version принадлежат явному owner contract. Не копировать fixtures отдельно в frontend/backend, не переносить repositories в shared.

**W:** зафиксировать producer и actual consumer для DTO/API/event/job; проверить сериализацию, enum/nullability/version, auth headers и queue registration. Backend response создавать реальным serializer/service, клиентом читать тем же shared/typed adapter. Site-owned repositories допустимы; game internals запрещены.

**E:** positive actual serialized response parses client, producer payload executes intended worker registry; negative incompatible/missing version/field/queue gives explicit contract error и не запускает чужую operation. Directional import/consumer inventory разрешает public API types, запрещает backend-only runtime types в shared по решённой policy. Перенос Python path при неизменном wire shape не должен требовать fictional data migration.

### B07 — Доказательные тесты и isolated storage harness

**Aliases:** `test-controls`, `storage-harness`. **IDs:** A06-01/02/03/04/07/11, проверочные зависимости A03/A05; RC-12, RC-13, RC-17. A06-02 не разрешает изменение crit-bleed mechanics A03-13. Large для harness, Small/Medium для focused controls.

**Evidence:** [FakeRedis:10](../../tests/backend/conftest.py), [boundary tests:63](../../tests/backend/features/test_infrastructure_boundaries.py), [stale collection import:6](../../tests/backend/features/generation_ai/test_asset_backfill.py), [A06 meaningful-test analysis](../06_testing_quality.md).

**K:** Python dict/pipeline fake доказывает domain flow, не wire serialization, Lua, WATCH/lease, clock TTL, transaction isolation, uniqueness либо PEL replay. Assertions о запрете должны иметь independent positive control, показывающий достижимость проверяемого пути; случай A06-02 — свидетельство качества setup, а не разрешение утвердить новое игровое правило.

**W:** в тестовом дизайне назвать наблюдаемый invariant, actual boundary, controlled fault, independent oracle и precondition. Контролировать время/барьеры детерминированно, не через sleeps. Отличать collection, unit/fake, adapter integration и conditional browser checks; не по имени stage/unit-файла.

**E:** минимальные disposable PG/RedisJSON/Mongo с ARQ/Streams checks: rollback/constraint/source predicate; wire JSON/TTL/Lua/owner release/compare-clear; Mongo pointer/schema/repeated identity; enqueue/PEL/ack/reclaim. Negative env guard отказывает при real DSN/неизолированных endpoints; positive harness self-check доказывает actual server roundtrip и cleanup только своего namespace/schema. Пакеты не ставятся и services не запускаются здесь. Critical fixtures не используют реальные account/provider data. Fakes остаются для pure domain tests; не обязательны Docker/browser E2E для каждого forwarding/math изменения.

### B08 — Clean dependency source и реальная input projection quality gate

**Aliases:** `dependency-source`, часть `test-controls`. **IDs:** A06-05/06/10/11/12, A08-10; RC-13, RC-14. A06-10 — NO-ACTION по текущему threshold policy; не разрешение установить retroactive patch percentage. Medium.

**Evidence:** [source override:35](../../pyproject.toml), [runner fallback:8](../../tools/dev/check.py), [CI events:3](../../.github/workflows/ci.yml), [develop job:19](../../.github/workflows/ci.yml), [pip-audit hook:39](../../.pre-commit-config.yaml). One checkout workflow не создаёт sibling source; local venv не является clean installation.

**K:** проверка должна получать опубликованный/явно описанный воспроизводимый dependency source, а audit сканировать приложение/lock/export, не hook-only env. Gate input, event/ref, marker и result association являются контрактом. Порог 74 и цель strong coverage сохраняются до отдельного решения, а не поднимаются ради отчётности.

**W:** описать clean Linux checkout/Python/source policy CI и Docker; сравнить lock/artifact dependencies; пройти PR develop/main и push predicates; проверить installed runner, не приписывать ему flags/steps по названию.

**E:** positive clean isolated install → collection → focused/full required gates с declared sources; negative missing dependency/invalid lock/test failure blocks downstream, fake hook env не считается application audit. Develop behavioral coverage уточняется явной policy и job. Зафиксировать exact commands/results без использования заранее подготовленной venv как единственного свидетельства. Hosted execution и package integrity требуют последующей разрешённой проверки.

### B09 — Quality provenance и immutable supply chain

**Aliases:** `quality-provenance`, `supply-chain`, `recovery-readiness`. **IDs:** A06-09, A08-09/11/12/15; RC-13, RC-14, контекст RC-05/09. Actual GitHub approvals/registry/recovery VERIFY-FIRST. Medium.

**Evidence:** [release build](../../.github/workflows/build-images.yml), [deploy manual inputs](../../.github/workflows/deploy-production.yml), [layer restart contract:18](../../docs/ru/management/deployment-contract.md). Existing main/release `needs: quality`, read-only PR token, non-root images и SHA/version tags полезны, но tag ≠ immutable digest.

**K:** promoted digest связан с source commit, successful quality result, dependency resolution и compatible Compose/schema revision. Manual dispatch не доказывает protected environment approval; schema rollback и image rollback — разные операции.

**W:** проверить build/promote/deploy association и target layer; release manifest и serialization gates; предложить backup/restore drill до влияющих на данные работ. Repository rulesets, host permissions и production credentials остаются unknown.

**E:** negative arbitrary ref/unverified digest/failed checks/incompatible manifest blocked by promotion; positive verified artifact and layer-only rollout сохраняют neighbor service scope. Unit/static workflow tests плюс isolated dry-run manifest verification; настоящий deploy/restore — отдельный owner gate, не проверка текущего плана. No mutable-only latest; pinning/signature approach выбрать по фактической цепочке, не строить новую систему без необходимости.

### B10 — Schema history, archive pointer и versioned readers

**Aliases:** `site-migrations`, `combat-readback`, `combat-archive`. **IDs:** A05-11/13, технический lifecycle A03-02/06/12; RC-09, RC-10, RC-17. Archive finalization expectations, TTL/support barrier — условно после owner contract. Medium.

**Evidence:** [site baseline:24](../../src/frontend/alembic/versions/0001_site_schema_baseline.py), [security baseline:25](../../src/frontend/alembic/versions/0002_security_baseline.py), [archive reader:147](../../src/backend/features/combat/services/result_archive_service.py), [document version rule:119](../../.agents/skills/turnbasedmmorpg-backend/references/document-patterns.md). Current reader получает `row.finalization`, тогда как A05-11 связывает модель с Mongo pointer.

**K:** historical migration воспроизводит свой schema revision, не current ORM future state; archive reader следует index/pointer/document version, не удалённому SQL payload. Missing/unavailable/unsupported archive не интерпретируется автоматически как gameplay result.

**W:** empty DB → all revisions, selected old baseline → head, approved downgrade/backfill/rolling readers; проверить ORM schema parity и Mongo missing/pointer/version separately. Миграция не подразумевает wipe без анализа saved shape/release policy.

**E:** negative historical+current collision, broken/missing pointer/unknown version/fault after index before document не возвращает fabricated successful result; positive seeded old schema upgrades и known archive rehydrates тот же observable result после удаления runtime. Real isolated PG/Mongo harness обязателен для migration/reader boundary. New archive expected reward/count/progression semantics не утверждаются.

### B11 — Streams recovery, durable scheduling и chat archive cursor

**Aliases:** `stream-recovery`, `chat-archive`; зависимости `storage-harness`, `ai-durability`, `combat-archive`. **IDs:** A05-05/06/15, A09-03/08, A03-05/06/12, A05-08; RC-07/09/10/15/16. A05-15 и barrier expectations VERIFY-FIRST; разные windows не один общий defect. Medium/Large.

**Evidence:** [stream composition:136](../../src/backend/core/containers/redis.py), [Chat cursor:44](../../src/backend/chat/workers/archive.py), [AI pending scheduling:168](../../src/backend/features/generation_ai/services.py), [RC-10 installed transport evidence](../10_root_causes.md#rc-10--commit-эффекта-и-доставка-следующего-шага-не-связаны-долговечным-обязательством). Installed transport чтение подтверждает new-message `>` loop; shipped version неизвестна.

**K:** PEL ≠ automatic replay; ack, reclaim/retry, poison message, retention и producer obligation explicit. Успешный SQL commit до enqueue правильный, но не гарантия durable delivery. Chat cursor означает подтверждённый durable prefix либо иной утверждённый recoverable disposition, не просто последний просмотренный input.

**W:** failure before/after effect, enqueue/ack, consumer restart/lease expiry, malformed message, retained pending body, повтор одной identity, slow/failed Mongo write. Для archive отдельно определить arrival/drain/oldest age и duplicate seq/append contract; не менять публичную history semantics молча.

**E:** negative isolated Redis consumer crash сохраняет replayable pending; enqueue failure after commit не теряет scheduling obligation; failed record не исчезает за cursor; duplicate delivery не дублирует уже разрешённый durable effect. Positive new event/reclaimed event/known archived payload доставляются, successful-prefix advances, queue registry правильный. Тест должен подтвердить eventual observable data и disposition, не число вызовов `xack`. Universal outbox/distributed transaction не предписывается.

### B12 — GenerationAI acceptance, result durability и bounded resource lifetime

**Aliases:** `ai-durability`, `ai-resource-budget`. **IDs:** A04-11/12/13/18, original A05-07 под canonical A04-12, A05-08, A09-09/10; RC-09/10/16. Technical data/provider workflow без изменения game content/AI policy. Medium.

**Evidence:** [worker:18](../../src/backend/features/generation_ai/workers/tasks.py), [commit/enqueue:32](../../src/backend/features/generation_ai/workers/tasks.py), [pending clear:168](../../src/backend/features/generation_ai/services.py), [A04 AI evidence](../04_rift_world_generation.md#10-generationai-данные-ассеты-и-публикация).

**K:** accepted task имеет durable input; done имеет readable result; retry/claim limit единый; follow-up scheduling recoverable. Template hash identity и prompt richness уже описаны game-content: не менять identity/gameplay/content для исправления доставки. Provider I/O/CPU normalization не должны скрывать held SQL/loop budget.

**W:** initial payload error, hydration missing, retry boundary, result write failure, commit/enqueue failure, repeated task identity, orphan output/asset handling, synthetic slow provider и large-but-approved image input. Выбрать result/disposition contracts до cleanup; не удалять retained artifacts наугад.

**E:** negative failed input не становится accepted/done, retry limit не оставляет неисполняемый cooldown, interrupted schedule восстанавливается, slow provider не удерживает неограниченные resources; positive typed output/apply/result и commit-before-enqueue сохраняются. External providers заменяются contract double; SQL/Mongo/ARQ roundtrip — isolated. Resource budget numbers/version утверждаются отдельно; assertions не сравнивают generated lore/image creative content и не вызывают провайдера.

### B13 — Combat commit, create identity и lease fencing

**Alias:** `combat-commit`. **IDs:** A03-03/04/09, часть A03-02/12; RC-07/08/09. A03-09 race effect VERIFY-FIRST; atomic exchange outcome задан техническим storage contract, turn rules не меняются. Large.

**Evidence:** [commit:594](../../src/backend/infrastructure/combat/managers/session.py), [nontransactional pipeline:608](../../src/backend/infrastructure/combat/managers/session.py), [RC-08 context-before-lock](../10_root_causes.md#rc-08--lease-dirty-marker-и-snapshot-version-не-образуют-атомарный-договор-записи).

**K:** runtime create с той же accepted operation identity не сбрасывает живой бой; lease check/release ≠ fencing captured revision at commit; pipeline batching ≠ атомарный exchange. Define actors/log/queue/meta accepted revision и failure recovery, сохраняя math/turn ordering/output DTO.

**W:** controlled partial command failure, duplicate create/commit, two executor contexts, old lease after successor acquisition, crash before/after accepted exchange. Зафиксировать old observable input/output corpus; не native rewrite.

**E:** negative duplicate/stale writer/fault не делает destructive reset, doubled queue trim или mixed revision; positive fresh owner persists identical authorized exchange, repeated completed identity возвращает договорённый outcome. Real RedisJSON integration + deterministic executor fixture проверяют persisted contract и log order, а не выбранный Lua/MULTI метод. Redis transaction command error не считать автоматическим rollback всех JSON writes.

### B14 — Dirty generation, live snapshot и bounded synchronization

**Aliases:** `ac-sync`, `inventory-sync`. **IDs:** A03-10, A05-03, A09-02/06; RC-08/11/15/16. A04-17 (original A05-09), A05-10 и A09-07 — только условное legacy расширение, не текущая очередь работ. Medium/Large.

**Evidence:** [AC mark/clear:130](../../src/backend/infrastructure/actor_state/managers/session.py), [generation check:166](../../src/backend/infrastructure/actor_state/managers/session.py), [clean/full target mapping:117](../../src/backend/features/character/integrations/system_integrator.py), [legacy snapshot:182](../../src/backend/features/rift/integrations/runtime.py).

**K:** acknowledged generation — конкретная сохранённая версия; новая mutation после capture остаётся dirty. Missing/clean marker не синоним explicit full-sync command. Runtime/projection/checkpoint/rebuild source различаются; authority и accepted-loss window domain-owned.

**W:** mutation between capture/SQL flush/clear, simultaneous snapshot replace, stale restore against live session; scan examined vs selected отдельно. Не менять vitals/regen/progression/equipment rules при переносе storage orchestration.

**E:** negative barrier-injected newer mutation не теряется и не clean-acked; duplicate clean sync не делает повторного full write; scan budget не голодает дальние candidates. Positive approved full-sync и selective dirty target сохраняют identical persistent fields, generation ack correct. In-memory unit checks дополняются RedisJSON/PG для CAS/flush; fixed clock нужен для сохранения существующей regen semantics, не новой формулы. Legacy restore/Hex state schema не мигрировать автоматически.

### B15 — Once-only effect и exact-source transfer: условный owner contract

**Aliases:** `reward-once`, `loot-transfer`. **IDs:** A03-01/02/07, A05-01/02/04/14, A07-18; RC-07/08/09/11/12. A04-16, A04-05/06 и A03-11/A04-15 — legacy/experimental, отдельно gated. Reward-once MIXED до подтверждения once semantics и identity; A05-14 — primary VERIFY-FIRST; для A07-18 primary MIXED, дополнительный verification gate. Transfer entitlement technical после current source contract. Medium/Large.

**Evidence:** [finalizer effects:69](../../src/backend/features/combat/workers/tasks/victory_finalizer_task.py), [safe/unsafe claim:203](../../src/backend/features/loot/workers/tasks/loot_claim_task.py), [Expedition transfer:372](../../src/backend/features/expedition/service.py); поддержанные SQL locks/unique placements/unsafe processed marker сохраняются.

**K:** claim identity и expected ownership/source проверяются authoritative owner; technical conservation ≠ правило размера награды. Однократность привязана к подтверждённой логической operation, не к каждому delivery attempt; agreed effect/ledger записываются в общей разрешённой transaction. Не разделять transaction ради event purity.

**W:** до реализации записать owner-approved identity/result/effect, exact source/destination entitlement, duplicate disposition и recovery после частичного применения. Проверить safe/unsafe independent branches и external corpse publication vs commit; не утверждать что любая повторная доставка всегда no-op без contract.

**E после gate:** negative повтор/параллельный повтор/foreign source/failure after partial commit не дублирует agreed effect и не перемещает чужой item; positive legitimate claim/transfer сохраняет прежние quantities, balances, attributes/progression semantics и atomic SQL unit. Oracle — conservation по seeded facts и approved single effect, не пересчёт XP/loot formula в тесте. Technical harness можно спроектировать сейчас, ожидаемые once-only mechanics — только после решения. До gate нет tests, закрепляющих новый reward policy.

### B16 — Semantic boundary, shared DTO и IO-free Combat

**Aliases:** `boundary-state`, `boundary-dto`, `combat-io`. **IDs:** A02-01/02/03/04/05/06/07/08/09, A06-08; контекст O02-01/02/03; RC-11/12/13. A02-02 legacy constructor change gated support; A02-06 допускает перенос лишь при parity прежней gameplay policy. Medium.

**Evidence:** [ownership policy:20](../../.agents/skills/turnbasedmmorpg-project/references/project-rules.md), [Redis paths:24](../../.agents/skills/turnbasedmmorpg-project/references/project-rules.md), [boundary prefix test:63](../../tests/backend/features/test_infrastructure_boundaries.py), [Combat facade:25](../../src/backend/features/combat/runtime/engine/resolver/__init__.py), [event wiring:37](../../src/backend/features/combat/events/__init__.py), A02 §§4/7/11.

**K:** public owner facade/semantic operation отделены от foreign ORM tuples, raw JSON paths, private policy helper и constructor graph. Integration имеет feature meaning, не CRUD mirror. Pure resolver/production executor остаются общими live/simulation; cross-cutting shared utilities требуют узкой owner policy, не запрета всех imports.

**W:** до переноса callers/data/UoW/error/retry контракт и соседние consumers; выбрать локальную factory/semantic operation, mass move не предписывать. Compare before/after observable flows, clock/RNG/state, no duplicate regen/effect. Explicit address-only exception для composition root с removal/owner justification.

**E:** directed import/API consumer checks, key-space ownership и IO-free runtime tripwires; negative representative foreign internal import/raw patch/new misplaced DTO ловится validator; positive approved composition, typed adapter и permitted cross-cutting utilities проходят. Runtime parity tests сохраняют transaction/effects/log/response shape. Не запрещать весь `infrastructure` import и не мерить cohesion исключительно размером класса/числом строк. Native extraction O02-03, перенос registry O02-01 и shared policy O02-02 сами по себе NO-ACTION/decision topics.

### B17 — Технические budgets: aggregation, archive/fanout и browser retention

**Aliases:** `combat-archive`, `ac-sync`, `chat-archive`, `chat-fanout`, `ai-resource-budget`, `browser-retention`. **IDs:** A09-01/02/03/04/05/06/07/08/09/10/11; RC-15/16. Legacy A09-07 gated; state-cache/version и history-retention contracts определяются до оптимизации. Medium.

**Evidence:** [Combat history merge:606](../../src/backend/infrastructure/combat/managers/session.py), [fanout:76](../../src/backend/chat/services/connection_manager.py), [browser history:176](../../src/frontend/templates/shared/chat/main.html), [AI worker lifetime:19](../../src/backend/features/generation_ai/workers/tasks.py), [A09 measured limits](../09_performance_scalability.md#11-что-можно-оптимизировать-и-что-сначала-измерить).

**K:** limit выбранных candidates/jobs/pages не bound просмотренных keys/bytes/loop time/backlog/DOM; process-local broadcast нельзя масштабировать replicas без delivery contract. Payload cache требует snapshot/version contract. Browser retention — сохранение permitted presentation/history semantics, не redesign chat UX.

**W:** измерять retained bytes/rows/commands, inspected/selected, drain/arrival/oldest, SQL hold/loop lag, slow-sink isolation отдельно; synthetic N и 2N при fixed fixture, bounded clock/barriers. Утвердить budgets относительно operation, не fictional production RPS.

**E:** negative long bounded fixture/slow sink/duplicate clean sync превышает agreed budget либо блокирует delivery; positive same messages/order/results/authorized recipients/active viewport сохраняются. Complexity/count/bytes — устойчивые signals вместо flaky wall-time-only threshold. Browser controls gated retention/scroll/accessibility agreement; multi-process fanout chosen only if required. Formula/AI scoring/Rift graph optimization excluded; no mandatory native engine/services.

### B18 — Guidance drift и согласование maintenance workflow

**Связи:** все aliases через cross-cutting docs guard; **IDs:** A02-10, A04-14, A06-01; context O02-02, A05-11/13; RC-17, SG10-K1–K5. Small; semantic decisions owner-gated.

**Evidence:** [obsolete Rift stage:3](../../.agents/skills/turnbasedmmorpg-rift/references/implementation-boundaries.md), [old resolver anchor:8](../../.agents/skills/turnbasedmmorpg-combat/references/snapshots.md), [Frontend no-DB/site ownership:29](../../.agents/skills/turnbasedmmorpg-frontend/references/feature-architecture.md), [logging correlation:54](../../.agents/skills/turnbasedmmorpg-quality/references/logging.md), [Streams handler shape:96](../../.agents/skills/turnbasedmmorpg-backend/references/redis-streams.md).

**K:** действующие source/stage/authority contracts отличать от planning/history/hypothesis. Уточнить frontend site DB vs game DB, cross-cutting shared policy, local compute вне Studio selected source, handler tracing owner. Отсутствующий stage файл не даёт retrospective approval существующему Rift.

**W:** после authorised contract/schema/API/workflow changes адресно review relevant domain references и source anchors; не загружать весь skill corpus при каждом исправлении. Обновление skills выполнять только в отдельно разрешённом maintenance scope, не в этом плане.

**E:** document link/path checker включая code-span anchors, import/entrypoint checks для tools/tests, семантический review stage/permissions/authority с owner evidence. Positive current link/reference на реализованный contract проходит; negative stale/deleted path и противоречивый owner mapping дают явный finding. Existing MkDocs/links не ловят obsolete semantics; Graphify не является current truth.

### B19 — Source-to-render trust: проверка до назначения защитного изменения

**Alias:** `browser-render`. **ID:** A07-17 Observation; проверочная зависимость RC-12, подтверждённая новая первопричина не назначается. VERIFY-FIRST; legacy/Hex последствия отдельно gated. Small/Medium.

**Evidence:** [Scenario rich-text sink:59](../../src/frontend/templates/game/domains/scenario/viewport/main.html), [Hex DOM sink:565](../../src/frontend/templates/game/test_hex_rift.html); source-to-sink reachability/CSP/auth данных не установлены исходным аудитом. Сам `safe`/`innerHTML` не доказывает XSS.

**K:** для external/user/generated text и URL установить provenance, допустимый rich-text subset, sanitizer/escaping owner и trusted constant exceptions. Не переписывать game content или presentation rules, чтобы скрыть непроверенный риск.

**W:** сначала восстановить источники, storage/editor credentials, rendering adapter и intended markup; проверить положительный trusted/allowed formatting case. Только при подтверждённой untrusted reachability выбирать локальную защиту sink/adapter; source/HTML policy требует владельца.

**E:** proposed isolated fixture тестирует отсутствие активного/недопустимого markup для untrusted input и сохранение allowed formatting/text/link behavior; input не должен ошибочно попадать в более trusted mode. Positive и negative проходят через actual template/DOM consumer. CSP — дополнительная защита, не замена sanitization contract; production browser/network не исследуется. Пока source contract неизвестен — verification task, не обязательный новый sanitizer и не finding severity upgrade.

## 4. Покрытие RC-01–17 и границы применения

| Root cause | Backlog | Допуск / исключение |
| --- | --- | --- |
| RC-01 adapter entitlement | B01, B02, B03 | Technical policy, legacy Rift conditional |
| RC-02 command vs server fact | B01/B06 contract review, B15 gated evidence | A04-01/A07-05 и A04-02 legacy/server outcome требуют authoritative contract и поддержки; не выбрать новое unknown-outcome gameplay поведение |
| RC-03 session authority lifecycle | B02 | Revocation/WS timing owner decision, core scopes technical |
| RC-04 publication fail-closed | B03, B04 | Exposure неизвестна; hardening не Hex/gameplay development |
| RC-05 principal permissions | B03, B04, B09 | Isolated ACL/proxy/env-file proof до выбора; real grants unknown |
| RC-06 diagnostic sensitivity | B05 | Synthetic canaries, shipped library version first |
| RC-07 logical effect identity | B11, B13, B15 | Rewards/durability once gate; no quantity/rule changes |
| RC-08 capture/version/ack/lease | B02, B13, B14, B15 | Race proof first; established storage invariant only |
| RC-09 status vs durable effects/data | B10, B11, B12, B15 | Domain archive/result/accepted-loss policy first; legacy snapshots excluded by default |
| RC-10 durable handoff/replay | B10, B11, B12 | Isolated transport/version proof; producer and consumer windows separate |
| RC-11 storage/wiring leaks | B06, B14, B15, B16 | Preserve UoW/current gameplay; foreign writes do not justify microservices |
| RC-12 test evidence limits | B06, B07, B15, B16, B19 | Independent positive/negative controls, real boundary vs fakes; A07-17 source-to-sink VERIFY-FIRST |
| RC-13 gate input/projection | B07, B08, B09, B16 | Current threshold policy retained; required checks unknown |
| RC-14 source/artifact reproducibility | B08, B09 | Clean source and provenance separate; no installs/builds here |
| RC-15 full aggregate processing | B14, B17 | Technical storage/bytes budget; same outputs/state revision |
| RC-16 work/backlog accumulation | B03, B11, B12, B14, B17 | Bounded work/retention contract; no production capacity claim |
| RC-17 stage/contract drift | B07, B10, B18 | No retrospective owner approval; guidance only proposed |

Этот файл не является второй классификацией всех 116 canonical. Она находится в `01_technical_findings_matrix.md`; выше каждый повторяемый технический механизм связан с исходными IDs/RC и конкретным K/W/E. Разовые исправления (например A03-08 failed simulation state) используют B07/B12 style focused acceptance/error-state test без нового правила и остаются в профильном пакете только после допуска experimental simulation. Ненумерованные risks/observations не получают молчаливый implementation статус.

**Вне технического enforcement сейчас:** A03-13 crit-bleed mechanics; A04-07 generator seed, A04-08 Knowledge cap wiring, A04-09 movement outcome, A04-19 outer-world roads, A04-20 Hex edge/next_floor, A04-21 fog-of-war и игровой остаток A04-01/02; любые loot/XP/AI/generation/Scenario/ability formulas. Их technical tooling/isolated reproduction можно предложить отдельно после решения, но не закреплять новую механику тестом этого этапа. A04-03/04/05/06/15/16/17, A05-10, A03-11 и A09-07 не включаются автоматически как legacy tasks. A04-10 world publication допустим как technical snapshot/status investigation после установленного контракта, а не как permission перепроектировать генерацию.

## 5. Адресаты guidance и объём расширения

| Существующий owner | Предлагаемое адресное расширение | Что не требуется |
| --- | --- | --- |
| Project | Authority/checkpoint/rebuild, allowed semantic boundaries/shared cross-cutting policy, contract change → source/reference review (B06/B14/B16/B18) | Новый skill на каждый A-ID; глобальный repository/dispatcher; массовая directory нормализация |
| Backend | Route audience/principal/object matrix, DTO/event/job owners, failure/duplicate/recovery checklist (B01/B02/B06/B11/B12/B13/B15) | Повторить already documented owner check; единая credential для всех internal routes; distributed ACID framework |
| Frontend | Site DB ownership clarification, actual API consumer contract, token/cookie lifecycle, technical browser retention и source-to-render trust (B02/B06/B17/B18/B19) | Game internals/game DB access, изменения игрового UI/UX |
| Security controls | Repeatable permission/env/redaction/source-to-render checks принадлежат backend/frontend/release/quality owners (B01–B05/B09/B19) | Новый project security skill или новый security-аудит; global security-review остаётся для отдельного explicitly requested review |
| Quality/testing | Positive controls/preconditions, isolated boundary harness, clean gate input/provenance, honest command/result evidence (B06–B09/B16/B17) | 100% patch задним числом; все fakes заменить servers; testing exact implementation calls вместо effects |
| Release | Clean source ↔ tested artifact ↔ Compose/schema, layer restart/restore/provenance и secrets validation (B04/B08/B09/B10) | Автоматический deploy, production probes/backup/restore без разрешения; Alpha UI label как зрелость |
| Combat | Technical create/commit/lease/archive lifecycle и IO-free/common executor parity (B10/B13/B15/B16) | Resolver formulas, turn rules, AI policy, нового native engine; once reward contract до решения |
| Rift | Исправленная stage/source карта, auth/dev isolation, отдельный условный legacy storage appendix (B01/B03/B14/B18) | Hex beta goals/generation/geometry/heart progression, legacy migration без решения |
| Studio | Source/action capability matrix и отделение local compute от selected-source writes (B03/B18) | Interpreting read-only label as ACL; любые prod mutators |
| Game-content | Для технических callers сохранять IDs/template identity/schema/version и generated input provenance (B06/B12) | Расширять catalogs/balance/lore; новый skill про AI queue fault вместо backend workflow |
| Audit-remediation | Текущий skill уже поддерживает четыре оси и K/W/E, source-first и proposal-only | Изменение entrypoint не требуется; не навязывать его generic report template вместо пяти requested documents |

Улучшения выполняются через действующий maintenance workflow только после отдельного разрешения. Выборочный regression test может закрыть один defect без расширения Knowledge. Новая procedure обоснована повторяющейся RC, но runner/validator проверяет конкретный observable signal и допустимые exceptions.

## 6. Критерии будущего принятия и зависимости

K принимается после owner-reviewed contract/source/stage без invented historical rationale. W принимается после выполнимого checklist с documented side effects и scope. E принимается после пары positive/negative scenarios, независимой precondition/oracle, доказанного actual boundary и failure signal; ни один новый gate не должен пропускать нарушение за счёт broad allowlist или изменения игровой expected behavior. Выполненные/неисполненные проверки раздельны.

Сначала требуется согласовать public principal/route policy для B01/B02/B03, operation identity/once/recovery для B10/B13/B15 и source/artifact policy для B08/B09. После этого leaf owners могут независимо создавать auth deny cases, synthetic redaction checks и документальные link checks. B07 harness — общая проверочная зависимость state/transport/migration пакетов; нельзя обещать доказательство Redis/SQL/Mongo поведения одним fake. B16 changes требуют parity corpus прежде переноса; B17 delta/cache/fanout optimization зависит от version/delivery/retention contracts. Это зависимости, не выбранная очередь выполнения; варианты последовательности находятся в `03_execution_options.md`.

На стадии плана проверены source existence/line ranges для ссылок этого файла и соответствие IDs/RC audit10. Требуется отдельная авторизация для future skills/tests/CI/validators edits, установки harness и исполнения jobs. Здесь создан только `audit/plans/04_skill_enforcement_backlog.md`; proposals не применены.
