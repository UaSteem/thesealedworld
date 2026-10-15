# Technical Hardening — рабочие пакеты

Дата плана:10.10.2026; источники09.10, чтение09–10.10.2026. **План, не разрешение на реализацию.** Основание: [scope](00_technical_hardening_scope.md), [116 canonical findings](01_technical_findings_matrix.md), [120 original IDs и evidence](../10_findings_registry.md), [17 root causes](../10_root_causes.md). Проверено текущее dirty tree; production state unknown. Все tests/validators ниже — предложения для будущего выбранного пакета, в этом задании они не запускались и не изменялись.

## Как читать и допускать пакеты

RC в карточке пакета — контекст связанных механизмов; точное finding→RC соответствие принадлежит матрице. Например у A05-02/A05-11/A05-13 root cause не установлена; пакетная ассоциация RC не приписывает им новую доказанную причину. «Подтверждаемые инварианты» — сохраняемые boundary contracts и проверяемые target conditions, не утверждение о уже достигнутой atomicity/безопасности. Current static facts и ограничения подтверждения находятся в evidence tables и каждой canonical карточке.

Предложено **37 пакетов**; это меню ограниченных slices, а не обязательство выполнить их все. Primary class задаёт матрица. MIXED, VERIFY-FIRST и secondary Legacy/experimental conditions остаются gates: связь с техническим пакетом не переводит finding в TECH. Для каждого пакета: source severity/evidence/stage берутся из матрицы без понижения; linked ID может присутствовать в нескольких slices, это не новая canonical finding. Рабочее дерево изменено до этого задания; anchors требуют сверки перед будущей реализацией.

Каждая карточка содержит все15 требуемых полей плюс explicit допуск. `Small/Medium` — относительная сложность slice, не срок и не единица оплаты. `Medium` не поручается целиком параллельным редакторам: сначала contract, затем disjoint leaf tasks и один интегратор общего файла. Например auth-admin — один permission contract и последовательная приёмка групп routers, не перестройка GenerationAI/Combat/Monsters. reward-once — сначала decision/verification; после решения отдельно оценивается каждый эффект/owner. Нет нового microservice, глобального outbox или общей distributed transaction.

**Архитектурные strengths:** сохранить IO-free Combat core/live-simulation executor, существующие auth/ownership/CSRF/Origin gates, SQL transactions/locks/constraints, owner-aware Redis lease release, DI/semantic facades, current queue separation, non-root/TLS/quality runner. Capability/auth errors не подменять успешным empty response; conflict/recovery outcome устанавливать до кода.

**Release admission для каждого пакета:** по умолчанию NONE при неизменных persisted fields/serialized contracts; schema/payload/credential change требует DATA-MIGRATION и upgrade/rollback compatibility proof; WIPE отдельное решение и вне автоматического scope. Credentials provision/rotation, public exposure changes и внешние library releases отдельно согласованы. Security rollback сохраняет запрет unauthorized access. Test fixtures изолированы, не используют production secrets/data.

## Пакеты

### WP-auth-game — Actor и ownership у игровых HTTP adapters

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-auth-game — Actor и ownership у игровых HTTP adapters |
| Исходные IDs | A07-01, A07-11, A07-13 |
| Root causes и домены | RC-01/03; Combat, Inventory, Exploration |
| Допуск | TECH-HARDENING |
| Техническая цель | Принимать только действующую game session владельца char_id. |
| Подтверждаемые инварианты | Сохранить ответы, выбранного персонажа и все legal actions. |
| Предлагаемые изменения / варианты | Общий typed GameAccessScope dependency в существующем DI; apply на adapters. Вариант: feature-local wrapper над общим verified context; один source of truth. |
| Запрещённые изменения | Менять бой, exploration knowledge, inventory rules; автоматически включать Legacy Rift. |
| Необходимые тесты | ASGI valid owner succeeds; site-only/wrong owner/expired/revoked token denied до use case; реальный frontend bearer contract. |
| Regression risks / parity | Сравнить valid response/action parity и frontend callers. |
| Зависимости | WP-session-lifecycle — контракт revoked/session; rollout согласован с клиентом. |
| Параллельность и leaf ownership | Отдельно от infra; общий auth.py/game_auth.py один интегратор. |
| Project skills | backend, combat, quality |
| Validators / Quality Gates | Route policy inventory + ASGI consumer contract; существующий check runner. |
| Размер | Medium |
| Вопросы владельцу | Какие server actions доступны без выбранного персонажа? Legacy Rift отдельно? |

### WP-auth-config — Полномочия Runtime GameConfig

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-auth-config — Полномочия Runtime GameConfig |
| Исходные IDs | A07-02 |
| Root causes и домены | RC-01; GameConfig, frontend cabinet |
| Допуск | TECH-HARDENING |
| Техническая цель | Отделить read policy от config.write/reset на сервере. |
| Подтверждаемые инварианты | Не менять значения, defaults и игровой эффект настроек. |
| Предлагаемые изменения / варианты | Scoped principal dependency до manager; выбрать service-authority или verified administrator с source роли. Отдельные scopes read/write/reset. |
| Запрещённые изменения | Считать любой bearer или общий frontend key администратором; менять tunables. |
| Необходимые тесты | Authorized read/write/reset; anonymous/player/wrong scope denied и zero manager calls; frontend GameConfigApiClient contract. |
| Regression risks / parity | Existing config list/reset payload parity. |
| Зависимости | Owner policy gate; общий authority contract согласовать с WP-auth-admin/internal. |
| Параллельность и leaf ownership | Можно параллельно проектировать; shared auth leaf интегрировать одним владельцем. |
| Project skills | backend, quality |
| Validators / Quality Gates | ASGI permissions matrix + route inventory. |
| Размер | Small |
| Вопросы владельцу | Кто владелец config.write: оператор, cabinet admin, служебная команда? |

### WP-auth-admin — Privileged content/job producers

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-auth-admin — Privileged content/job producers |
| Исходные IDs | A07-03 |
| Root causes и домены | RC-01; GenerationAI, Monsters, Combat simulation, admin players |
| Допуск | TECH-HARDENING |
| Техническая цель | Проверять producer permission до SQL write, costly work и enqueue. |
| Подтверждаемые инварианты | Правомочный producer получает тот же job/result; worker payload и mechanics прежние. |
| Предлагаемые изменения / варианты | Единый scoped policy interface; по одной группе routers apply/verify; scopes content.read/content.generate/simulation.run/admin.manage. Вариант service client identity либо verified admin backend role. |
| Запрещённые изменения | Менять content/prompts/AI behavior или считать worker transport user authorization. |
| Необходимые тесты | Positive authorized each group; anonymous/player/wrong scope before DB/enqueue; real CombatAiTesting caller service header; failed enqueue прежний контракт до WP-ai-durability. |
| Regression risks / parity | DTO/queue names и allowed simulation payload parity. |
| Зависимости | Owner scope/caller list; auth foundation совместно с WP-auth-config/internal. |
| Параллельность и leaf ownership | Группы routes делить на leaf tasks после policy; общий authority один владелец. |
| Project skills | backend, game-content, combat, quality |
| Validators / Quality Gates | Endpoint inventory + producer permission tests. |
| Размер | Medium |
| Вопросы владельцу | Должны ли эти группы вообще быть опубликованы через public ingress? |

### WP-auth-internal — Session diagnostics и analytics access

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-auth-internal — Session diagnostics и analytics access |
| Исходные IDs | A07-04, A08-03 |
| Root causes и домены | RC-01/04/06; Combat, Scenario, Exploration analytics |
| Допуск | TECH-HARDENING |
| Техническая цель | Защитить raw/session diagnostics и отделить analytics.read от backfill.write. |
| Подтверждаемые инварианты | Сохранить легальные operational callers и analytics semantics. |
| Предлагаемые изменения / варианты | Scoped service/diagnostic principal; backend gate обязательный, edge deny отдельная defense. Отдельная policy для aggregate read, raw debug, mutation. |
| Запрещённые изменения | Считать Nginx единственным auth; одним общим token открывать все группы. |
| Необходимые тесты | Known service scope works; anonymous/player/wrong service scope denied; backfill without write scope no DB effects; proxy path test. |
| Regression risks / parity | Diagnostic payload parity для разрешённого клиента. |
| Зависимости | Caller/scope decision; WP-surface-isolation для edge. |
| Параллельность и leaf ownership | Leaf routers можно раздельно, shared permission primitive один владелец. |
| Project skills | backend, quality |
| Validators / Quality Gates | ASGI route matrix + rendered Nginx policy test. |
| Размер | Small |
| Вопросы владельцу | Нужны ли player aggregates и какие fields публичны? |

### WP-chat-access — Chat membership и channel authorization

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-chat-access — Chat membership и channel authorization |
| Исходные IDs | A07-06, A07-07, A07-08 |
| Root causes и домены | RC-01/03; Chat REST/WS |
| Допуск | TECH-HARDENING |
| Техническая цель | Связать principal/selected character и разрешённый channel/scope; проверять DM membership. |
| Подтверждаемые инварианты | Сохранить UUID участников DM и нынешние legit channels/messages. |
| Предлагаемые изменения / варианты | Explicit resolver user UUID↔selected char; REST membership gate и WS bootstrap/send gate. Membership lookup owner facade вместо arbitrary scope из клиента. |
| Запрещённые изменения | Мигрировать UUID в int без отдельного решения; менять product channel rules. |
| Необходимые тесты | Own DM/history/send succeeds; outsider and wrong URL char denied; site UUID/game char mismatch fixture; unauthorized channels emit nothing. |
| Regression risks / parity | Reconnect + legitimate DM/group history/order contracts. |
| Зависимости | WP-session-lifecycle identities/revocation; source membership owner decision. |
| Параллельность и leaf ownership | REST/WS разные листья, общий resolver один интегратор; конфликт с chat-fanout/archive storage fixtures координировать. |
| Project skills | backend, quality |
| Validators / Quality Gates | Real REST+WS principal/membership contract fixtures. |
| Размер | Medium |
| Вопросы владельцу | Где authoritative group/room membership и есть ли гостевые каналы? |

### WP-session-lifecycle — Account/game session revocation

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-session-lifecycle — Account/game session revocation |
| Исходные IDs | A07-09, A07-10, A07-11, A05-12, A07-08, A07-16 |
| Root causes и домены | RC-03/09; site auth, game sessions, refresh |
| Допуск | TECH-HARDENING |
| Техническая цель | Деактивация/logout/refresh rotation имеют согласованную server lifecycle. |
| Подтверждаемые инварианты | Valid active sessions работают; logout/account deactivation не изменяют game facts. |
| Предлагаемые изменения / варианты | Согласовать site logout→game revoke и токен/WS check points; refresh revoke+replacement в одном site UoW. Не строить новый auth server. |
| Запрещённые изменения | Выбирать UI logout policy молча, менять token claims/persisted format без compatibility plan. |
| Необходимые тесты | Refresh failure between writes rolls back; concurrent refresh at most one valid accepted rotation according to agreed policy; deactivated token denied на HTTP/WS; logout reconnect rejected. |
| Regression risks / parity | Authorized login/refresh/bootstrap parity; stale game session defined behavior. |
| Зависимости | Owner revocation latency/logout scope gate; WP-storage-harness real SQL/Redis proof. |
| Параллельность и leaf ownership | Auth shared leaves exclusive; остальные security packages ждут contract либо используют stable interface. |
| Project skills | backend, frontend, quality |
| Validators / Quality Gates | Lifecycle fault/concurrency tests + real consumer contract. |
| Размер | Medium |
| Вопросы владельцу | Logout отзывает текущую session или все? Допустима ли revocation задержка для WS? |

### WP-surface-isolation — Publication dev/internal surface

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-surface-isolation — Publication dev/internal surface |
| Исходные IDs | A07-15, A08-03, A08-04 |
| Root causes и домены | RC-04; backend mount, Nginx, Hex |
| Допуск | TECH-HARDENING; Hex capacity EXCLUDED |
| Техническая цель | Default failclosed experimental mounts и explicit public route allow/deny. |
| Подтверждаемые инварианты | Dev opt-in продолжает работать, gameplay не меняется. |
| Предлагаемые изменения / варианты | Explicit env publication policy, no production default dev mount; rendered edge policy denies internal/admin as owner decided. Hex only exposure guard. |
| Запрещённые изменения | Достраивать Hex, вводить retention policy без отдельного package; считать current VPS проверенным. |
| Необходимые тесты | Production/dev unset/off/on route enumeration; rendered Nginx path checks incl nested/trailing slash; dev authorized positive path. |
| Regression risks / parity | Existing public legitimate API/WS and health reachability. |
| Зависимости | Owner route publication; coordinate auth-internal/admin and WP-transport-policy. |
| Параллельность и leaf ownership | Backend app and Nginx по одному leaf owner; shared app mounts не параллельно edit. |
| Project skills | backend, rift, release, quality |
| Validators / Quality Gates | Mount inventory + config render tests. |
| Размер | Small |
| Вопросы владельцу | Какие environments и группы сознательно public/internal/dev-only? |

### WP-secret-validation — Failclosed известные defaults

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-secret-validation — Failclosed известные defaults |
| Исходные IDs | A07-14, A08-01 |
| Root causes и домены | RC-04/05; settings/startup |
| Допуск | TECH-HARDENING |
| Техническая цель | Запретить known development secrets в declared production. |
| Подтверждаемые инварианты | Testing/dev fixtures используют явный разрешённый режим; нет вывода secret в ошибку. |
| Предлагаемые изменения / варианты | Production validation rejects absent/default values; enumerate actual settings; per-service credential plan separately runtime-isolation. |
| Запрещённые изменения | Случайно печатать secrets, менять их на VPS; автоматическая rotation во время реализации. |
| Необходимые тесты | Known default/missing rejected in prod; valid synthetic values accepted; testing/dev allowed per explicit policy; error redacted. |
| Regression risks / parity | Current local startup/testing contract. |
| Зависимости | Owner environment detection и provision/rotation procedure. |
| Параллельность и leaf ownership | Независимый leaf settings; integration auth configs review. |
| Project skills | backend, release, quality |
| Validators / Quality Gates | Settings table-driven checks + build startup config smoke. |
| Размер | Small |
| Вопросы владельцу | Что authoritative production marker и кто провиженит keys? |

### WP-studio-readonly — Selected-source Studio read-only

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-studio-readonly — Selected-source Studio read-only |
| Исходные IDs | A07-12 |
| Root causes и домены | RC-01/04/17; Studio |
| Допуск | TECH-HARDENING |
| Техническая цель | Selected production/local source не получает write operations. |
| Подтверждаемые инварианты | Read-only analytics и pure isolated local compute вне selected source сохраняются. |
| Предлагаемые изменения / варианты | Source capability gate before HTTP mutators/work; reconcile source-readonly contract and separate isolated outputs. Auth access policy explicit. |
| Запрещённые изменения | Запрещать любой local compute; исправлять Studio UX или gameplay. |
| Необходимые тесты | Read request succeeds; selected-source mutate blocked before client; isolated compute proves no source writer; unauthorized access denied. |
| Regression risks / parity | Existing read selectors/output contracts. |
| Зависимости | Owner trusted local operator/auth boundary and output destinations. |
| Параллельность и leaf ownership | Studio leaves независимы от game auth; shared source client один owner. |
| Project skills | studio, backend, quality |
| Validators / Quality Gates | Source capability tests + instruction consistency review. |
| Размер | Small |
| Вопросы владельцу | Какие local outputs считаются вне selected source? |

### WP-metrics-redaction — Bounded safe metric labels

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-metrics-redaction — Bounded safe metric labels |
| Исходные IDs | A08-05 |
| Root causes и домены | RC-06/16; shared metrics, services |
| Допуск | TECH-HARDENING |
| Техническая цель | Не сохранять raw URL identifiers/token в labels; metrics publication policy. |
| Подтверждаемые инварианты | Stable service/method/status observability остается. |
| Предлагаемые изменения / варианты | Use route templates/finite fallback and approved metrics gate/network scope; test unknown dynamic URLs. |
| Запрещённые изменения | Удалять все metrics; менять gameplay. |
| Необходимые тесты | Synthetic token URLs absent in collected samples; template cardinality bounded; approved scrape works; anonymous denied if policy requires. |
| Regression risks / parity | Existing dashboards review without secret samples. |
| Зависимости | Owner scraping/edge access; surface-isolation coordination. |
| Параллельность и leaf ownership | Shared metrics single leaf owner; independent log package. |
| Project skills | backend, release, quality |
| Validators / Quality Gates | Metric sample/redaction/cardinality assertion. |
| Размер | Small |
| Вопросы владельцу | Кто scrapes metrics и какие labels реально нужны? |

### WP-log-redaction — Secrets/PII-safe exception и ingress logs

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-log-redaction — Secrets/PII-safe exception и ingress logs |
| Исходные IDs | A08-06, A08-07 |
| Root causes и домены | RC-06; Loguru, Nginx, frontend |
| Допуск | TECH-HARDENING |
| Техническая цель | Убрать URL token/locals/PII из production logs, сохранив diagnosis. |
| Подтверждаемые инварианты | Correlation IDs and safe error summaries. |
| Предлагаемые изменения / варианты | Nginx safe URI/log format; production diagnose/locals disabled; explicit allowlisted logging fields. No real secrets in probes. |
| Запрещённые изменения | Обнулить audit trail или выводить реальные logs пользователю. |
| Необходимые тесты | Synthetic token/PII exception + query/WS path absent in sinks; correlation/error class present. |
| Regression risks / parity | Error diagnosis smoke and existing structured fields. |
| Зависимости | Owner retention/access; Nginx leaf согласовать surface/transport. |
| Параллельность и leaf ownership | Logging library owner source учитывать; Nginx one integrator. |
| Project skills | backend, release, quality |
| Validators / Quality Gates | Log sink tests + rendered access_log config. |
| Размер | Small |
| Вопросы владельцу | Какие PII разрешены и срок хранения? |

### WP-dependency-source — Clean source/build contract

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-dependency-source — Clean source/build contract |
| Исходные IDs | A06-05, A08-10 |
| Root causes и домены | RC-14; pyproject/lock/CI/Docker |
| Допуск | TECH-HARDENING |
| Техническая цель | Один объяснимый dependency source contract для clean checkout и каждого image. |
| Подтверждаемые инварианты | Used library APIs/version compatibility preserve. |
| Предлагаемые изменения / варианты | Choose pinned published artifact OR explicit pinned sibling checkout/build; Docker source policy declared and tested, no silent package replacement. |
| Запрещённые изменения | Править installed sibling library, менять packages/API без нужды, обновлять все deps. |
| Необходимые тесты | Clean isolated source resolution; exact required library capability/import smoke; lock and each image dependency provenance compare. |
| Regression risks / parity | Current site/game/chat/worker startup imports. |
| Зависимости | Owner library release/source choice; WP-quality-provenance builds after solution. |
| Параллельность и leaf ownership | Source files/lock one owner; supply-chain files shared coordinator. |
| Project skills | backend, release, quality |
| Validators / Quality Gates | Clean checkout/install + image import smoke. |
| Размер | Medium |
| Вопросы владельцу | Публикуем canonical library release или закрепляем source checkout? |

### WP-quality-provenance — Behavior gate и release artifact identity

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-quality-provenance — Behavior gate и release artifact identity |
| Исходные IDs | A06-06, A06-09, A08-11 |
| Root causes и домены | RC-13/14; CI/deploy |
| Допуск | TECH-HARDENING |
| Техническая цель | Chosen deploy artifact связан с successful required checks конкретного ref/digest. |
| Подтверждаемые инварианты | No deployment during implementation tests; current supported branch policy explicit. |
| Предлагаемые изменения / варианты | Develop behavioral subset/full agreed runner; provenance binding quality→build→immutable digest; manual dispatch approved ref/environment rules. |
| Запрещённые изменения | Молча менять branch protections на GitHub, запускать deploy или обещать current configured protection. |
| Необходимые тесты | Workflow contract simulated push/PR/dispatch cases; failed/unrelated quality cannot authorize artifact; successful selected ref accepted. |
| Regression risks / parity | Existing main/PR check paths; release tags/manual permitted path. |
| Зависимости | WP-dependency-source; owner branch/environment/digest policy. |
| Параллельность и leaf ownership | CI/deploy files one integrator; supply-chain coordinated. |
| Project skills | release, quality |
| Validators / Quality Gates | Workflow static contract + disposable no-deploy pipeline evidence. |
| Размер | Medium |
| Вопросы владельцу | Какие branches/refs допускаются и нужен ли approval environment? |

### WP-supply-chain — Pinned Actions/images и app dependency audit

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-supply-chain — Pinned Actions/images и app dependency audit |
| Исходные IDs | A06-12, A08-09 |
| Root causes и домены | RC-13/14; hooks, CI, images |
| Допуск | TECH-HARDENING |
| Техническая цель | Зафиксировать используемые sources и сканировать именно app environment. |
| Подтверждаемые инварианты | No arbitrary upgrades or lock drift. |
| Предлагаемые изменения / варианты | Pin mutable action/image refs to approved immutable versions; dependency audit from installed locked app env/export. Document update process. |
| Запрещённые изменения | Приписывать hook-env audit приложению; массово обновлять зависимости. |
| Необходимые тесты | Prove audited manifest corresponds lock/runtime; vulnerable synthetic fixture reported; pinned build source readable. |
| Regression risks / parity | Current build behavior and supported platforms. |
| Зависимости | Owner pin/update policy; dependency-source source manifest. |
| Параллельность и leaf ownership | Hooks/CI/Docker leaves coordinated with quality-provenance. |
| Project skills | release, quality |
| Validators / Quality Gates | Actual environment audit evidence + pin checker. |
| Размер | Small |
| Вопросы владельцу | Какие registry/base images поддерживаем и кто обновляет pins? |

### WP-test-controls — Focused contract/test controls

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-test-controls — Focused contract/test controls |
| Исходные IDs | A06-01, A06-02, A06-07, A06-08, A06-04, A04-14, A06-06, A06-12 |
| Root causes и домены | RC-12/13; tests, architecture validator |
| Допуск | TECH plus MIXED test-only gate |
| Техническая цель | Collection и tests доказывают реальные boundary invariants. |
| Подтверждаемые инварианты | Existing game formulas/trigger behavior frozen; observed parity tests не выбирают design. |
| Предлагаемые изменения / варианты | Repair stale collection dependency; activate parry fixture to assert existing rule, shared DTO/real frontend-backend contracts; narrowly extend ownership validator, not blanket rule. |
| Запрещённые изменения | Менять crit/parry rule A03-13; вводить100%patch/branch coverage как обязательный. |
| Необходимые тесты | Collection succeeds; negative mutation shows trigger exercised; real adapter fixtures detect mismatched responses; validator catches known prohibited import and permits facade/UoW. |
| Regression risks / parity | Existing positive suite and diagnostics kept. |
| Зависимости | WP-boundary-* defines exact architecture rule; mechanics expectation owner if ambiguous. |
| Параллельность и leaf ownership | Tests leaves owned per package; shared runner/validator one owner. |
| Project skills | quality, backend, combat |
| Validators / Quality Gates | Existing tools/dev/check.py runner + targeted mutation/control assertions. |
| Размер | Small |
| Вопросы владельцу | Какой existing parry behavior authoritative для regression? |

### WP-storage-harness — Isolated real-store fault harness

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-storage-harness — Isolated real-store fault harness |
| Исходные IDs | A06-03, A06-04, O02-04, A05-15 |
| Root causes и домены | RC-12; PG/RedisJSON/Mongo/Streams |
| Допуск | VERIFY-FIRST foundation |
| Техническая цель | Доказать transaction/CAS/claim/append assumptions в disposable stores. |
| Подтверждаемые инварианты | No production data/service writes; no game policy changes. |
| Предлагаемые изменения / варианты | Opt-in isolated integration fixture versions/config; failure/barrier hooks, deterministic cleanup and capability checks; prioritize contracts used by selected packages. |
| Запрещённые изменения | Все tests переводить в costly integration; тестировать чужой live environment. |
| Необходимые тесты | Real SQL rollback/constraint, RedisJSON generation/CAS, Streams reclaim/ack, Mongo concurrent append+seq; expose assumptions rather than autoasserting guessed invariant. |
| Regression risks / parity | Existing fast tests stay independent. |
| Зависимости | Owner versions/resources; dependency-source availability. |
| Параллельность и leaf ownership | Fixture/container definitions single owner; package tests independent namespaces. |
| Project skills | quality, backend, release |
| Validators / Quality Gates | Capability smoke + isolation/cleanup verification; selected gated integration lane. |
| Размер | Medium |
| Вопросы владельцу | Какие supported store versions и disposable resources доступны CI? |

### WP-site-migrations — Clean Site schema baseline

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-site-migrations — Clean Site schema baseline |
| Исходные IDs | A05-13 |
| Root causes и домены | RC-09/14; frontend/site DB |
| Допуск | TECH-HARDENING |
| Техническая цель | Clean upgrade creates ORM-compatible schema; existing upgrade path checked. |
| Подтверждаемые инварианты | User/site data preserved; no model redesign. |
| Предлагаемые изменения / варианты | Reconcile migration chain with current ORM, empty-DB upgrade and supported existing snapshot; choose baseline correction vs forward migration by actual deployment history. |
| Запрещённые изменения | Удалять applied history, wipe DB или менять model product fields. |
| Необходимые тесты | Empty upgrade→ORM CRUD→downgrade if supported; actual supported baseline upgrade on isolated copy. |
| Regression risks / parity | Auth/session relationships and SQL constraints. |
| Зависимости | Owner applied revision inventory; storage-harness. |
| Параллельность и leaf ownership | Site migration leaves independent from gameplay; session tests coordinate models. |
| Project skills | frontend, backend, release, quality |
| Validators / Quality Gates | Alembic graph + real-PG upgrade/ORM smoke. |
| Размер | Small |
| Вопросы владельцу | Есть ли deployed databases и какие applied revisions? |

### WP-stream-recovery — Redis Streams pending recovery

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-stream-recovery — Redis Streams pending recovery |
| Исходные IDs | A05-05, O02-05 |
| Root causes и домены | RC-09/10; bus/workers |
| Допуск | TECH; alternate registry VERIFY-FIRST |
| Техническая цель | Accepted message после consumer death eventually retry или explicit dead-letter. |
| Подтверждаемые инварианты | Current message schema/group/order constraints preserve; duplicates expected. |
| Предлагаемые изменения / варианты | Bounded stale pending reclaim + ack-after-effect discipline; inspect selected worker registry/queue functions. Version-compatible claim alternative chosen. |
| Запрещённые изменения | Обещать exactly-once broker, менять game event payload or routing by guess. |
| Необходимые тесты | Consumer death before/after effect/ack; reclaim after threshold; poison handling bounded; selected worker has each queued function. |
| Regression risks / parity | Positive once and duplicate handler behavior. |
| Зависимости | Each handler idempotency gate; storage-harness; O02-05 verify current actual entrypoint. |
| Параллельность и leaf ownership | Bus leaf one owner; handler leaves separate after contracts. |
| Project skills | backend, quality |
| Validators / Quality Gates | Real Streams pending/reclaim + registry manifest validator. |
| Размер | Small |
| Вопросы владельцу | Retry threshold/dead-letter owner и actual worker entrypoints? |

### WP-chat-archive — Chat durable archival cursor/append

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-chat-archive — Chat durable archival cursor/append |
| Исходные IDs | A05-06, A05-15, A09-03, A09-08 |
| Root causes и домены | RC-09/10/15; Chat Redis→Mongo |
| Допуск | TECH plus append VERIFY-FIRST |
| Техническая цель | Cursor отражает persisted contiguous success, no ack past failed item. |
| Подтверждаемые инварианты | Message identity/order/history semantics preserve. |
| Предлагаемые изменения / варианты | Persist ack only committed range, bounded incremental batching; project/update Mongo without returning whole bucket. Append seq concurrency only after real verification. |
| Запрещённые изменения | Выбирать новую product retention или удалять old chat history. |
| Необходимые тесты | Fault write at middle/batch, restart, duplicate archive; no skips; concurrent append/seq verified real Mongo; large bucket response cost bounded. |
| Regression risks / parity | Exact message/history order and id parity. |
| Зависимости | WP-storage-harness; authoritative seq/history contract owner. |
| Параллельность и leaf ownership | Chat archive+repo one owner; chat-fanout separate leaves. |
| Project skills | backend, quality |
| Validators / Quality Gates | Real Mongo/Redis retry + deterministic backlog/drain test. |
| Размер | Medium |
| Вопросы владельцу | Кто authoritative sequence generator и допустим backlog drain latency? |

### WP-combat-archive — Combat durable archive/support delivery

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-combat-archive — Combat durable archive/support delivery |
| Исходные IDs | A03-06, A03-12, A09-01 |
| Root causes и домены | RC-09/10/15; Combat archive/analytics |
| Допуск | TECH-HARDENING |
| Техническая цель | Commit has recoverable archive/support obligation; freeze sees known status. |
| Подтверждаемые инварианты | Log/order/analytics facts and live/simulation parity unchanged. |
| Предлагаемые изменения / варианты | Durable owner-local pending obligation/receipt or existing retry record; incremental/history serialization optimization only parity guarded; select one bounded archive handoff. |
| Запрещённые изменения | Новый global outbox/distributed ACID; новый analytics/game event semantics. |
| Необходимые тесты | Failure after commit before enqueue, support unavailable at freeze, restart/archive duplicate; readback exact log/order/facts; history work scales with delta when chosen. |
| Regression risks / parity | Existing frozen/live/archive results identical. |
| Зависимости | WP-combat-commit stable revision; storage-harness; separate readback package. |
| Параллельность и leaf ownership | Combat archive leaves one owner; commit manager shared change serialized. |
| Project skills | combat, backend, quality |
| Validators / Quality Gates | Fault handoff + archive/live golden contract; representative bytes/ops budget. |
| Размер | Medium |
| Вопросы владельцу | TTL/retention promise и кто owns support-complete state? |

### WP-combat-readback — Archive reader SQL payload contract

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-combat-readback — Archive reader SQL payload contract |
| Исходные IDs | A05-11 |
| Root causes и домены | RC-09/11; Combat archive reader |
| Допуск | TECH-HARDENING |
| Техническая цель | Reader uses actual authoritative archived payload. |
| Подтверждаемые инварианты | Public archived response shape remains. |
| Предлагаемые изменения / варианты | Choose correct existing storage field/facade; if absent, explicit unavailable error until separately approved persisted shape. |
| Запрещённые изменения | Придумывать stored SQL payload или читать live state как исторический факт. |
| Необходимые тесты | Stored representative archive reads exact response; missing archive clear outcome; stale SQL attribute cannot be accessed. |
| Regression risks / parity | Live/frozen/archive DTO parity. |
| Зависимости | WP-combat-archive storage owner decision if source changes. |
| Параллельность и leaf ownership | Reader leaf independent after source contract. |
| Project skills | combat, backend, quality |
| Validators / Quality Gates | Real persisted fixture readback contract. |
| Размер | Small |
| Вопросы владельцу | Где authoritative full archive и что означает missing/expired? |

### WP-combat-commit — Versioned Combat create/exchange commit

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-combat-commit — Versioned Combat create/exchange commit |
| Исходные IDs | A03-03, A03-04, A03-09 |
| Root causes и домены | RC-07/08; Combat Redis runtime |
| Допуск | TECH-HARDENING |
| Техническая цель | Accepted exchange atomic for agreed fields; create doesn't overwrite existing combat; stale executor fenced. |
| Подтверждаемые инварианты | Same resolver outputs/log/moves for valid state. |
| Предлагаемые изменения / варианты | Owner-local compare/version atomic commit/create-if-absent using existing Redis primitive; choose Lua/transaction based actual RedisJSON support. |
| Запрещённые изменения | Формулы, turn/move resolution, general distributed transaction. |
| Необходимые тесты | Fault each write, same combat_id repeat, parallel stale executor barrier, lease expiry: no partial accepted state/stale write; IO-free executor output parity. |
| Regression risks / parity | Live/simulation core common pipeline and exact public snapshot/log. |
| Зависимости | WP-storage-harness; define accepted revision contract before archive/reward integrations. |
| Параллельность и leaf ownership | Combat session manager exclusive leaf; archive tests contract driven. |
| Project skills | combat, backend, quality |
| Validators / Quality Gates | Real RedisJSON CAS/create/retry failure proof. |
| Размер | Medium |
| Вопросы владельцу | Which fields define accepted exchange; conflict response policy? |

### WP-ac-sync — ActiveCharacter dirty generation/fair sync

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-ac-sync — ActiveCharacter dirty generation/fair sync |
| Исходные IDs | A03-10, A09-02, A09-06, O02-04 |
| Root causes и домены | RC-08/15/16; Character sync |
| Допуск | TECH-HARDENING |
| Техническая цель | Snapshot commit clears only its generation; new dirty work survives; bounded fair scan. |
| Подтверждаемые инварианты | Character projection/game values preserve. |
| Предлагаемые изменения / варианты | Version-aware compare-clear; owner-scoped batch/cursor fairness and dedup full writes for unchanged revision. First correctness, then measured scan delta. |
| Запрещённые изменения | Менять attributes/stat calculations or claim SQL+Redis ACID. |
| Необходимые тесты | Mutation between SQLwrite/clear, workerrestart, duplicate same generation, uneven hot/cold keys; no lost dirty and eventual covered dirty set. |
| Regression risks / parity | Projection and periodic flush existing output parity. |
| Зависимости | WP-storage-harness; boundary-state owner facade contract. |
| Параллельность и leaf ownership | AC manager/sync worker one owner; Inventory manager separate but projection API co-review. |
| Project skills | backend, quality |
| Validators / Quality Gates | Barrier real Redis/SQL tests + bounded scan/bytes check. |
| Размер | Medium |
| Вопросы владельцу | Required flush latency/fairness budget and version owner? |

### WP-inventory-sync — Inventory hydration/flush version contract

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-inventory-sync — Inventory hydration/flush version contract |
| Исходные IDs | A05-03, A02-04 |
| Root causes и домены | RC-08/11; Inventory↔Character |
| Допуск | TECH-HARDENING |
| Техническая цель | Hydrate/flush cannot overwrite newer session; public projection instead of private hydration form. |
| Подтверждаемые инварианты | Placements/wallet/stats unchanged; existing UoW preserved. |
| Предлагаемые изменения / варианты | Inventory-owned revisioned snapshot/compare-clear and facade for immutable Character projection. |
| Запрещённые изменения | Новый inventory/economy policy; lock-only fix without stale write guard. |
| Необходимые тесты | Concurrent hydrate/mutate/flush barrier, SQL commit failure, Redis set failure; newer dirty retained; Character projection exact parity. |
| Regression risks / parity | Valid equip/placement and ActiveCharacter items projection. |
| Зависимости | WP-storage-harness; boundary-state/dto projection contracts. |
| Параллельность и leaf ownership | Inventory service/session exclusive; durability/reward code shared integrate sequentially. |
| Project skills | backend, quality |
| Validators / Quality Gates | Real RedisJSON+SQL failure sequence test. |
| Размер | Medium |
| Вопросы владельцу | Which store is authoritative per Inventory lifecycle phase? |

### WP-ai-durability — Durable accepted GenerationAI input/recovery

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-ai-durability — Durable accepted GenerationAI input/recovery |
| Исходные IDs | A04-12, A05-07, A04-13, A04-18, A05-08, A03-08, A04-10, A04-11 |
| Root causes и домены | RC-09/10; GenerationAI job lifecycle |
| Допуск | TECH plus partial VERIFY-FIRST |
| Техническая цель | Accepted task retains replayable input; done only persisted result; enqueue gap recoverable. |
| Подтверждаемые инварианты | Prompts/content/AI retry counts/tunables unchanged. |
| Предлагаемые изменения / варианты | Owner-local persist input and pending intent in existing SQL UoW, recover scheduling by task identity; status failed on policy-load error; bounded orphan diagnosis first. Alternatives existing task rows vs narrow obligation record. |
| Запрещённые изменения | AI/model/content rules, retry-count design A04-11, new global transaction framework. |
| Необходимые тесты | Lost external/enqueue/result persistence, crash each lifecycle boundary; accepted task reconstructs input; done readback exists; duplicate scheduling effect guarded. |
| Regression risks / parity | Current generated payload and existing retry policy parity. |
| Зависимости | WP-auth-admin; storage-harness; MIXED consumer effects gated. |
| Параллельность и leaf ownership | Task repo/scheduler/worker exclusive; ai-resource-budget same leaves serialize. |
| Project skills | backend, game-content, quality |
| Validators / Quality Gates | SQL enqueue fault/status readback + restart test. |
| Размер | Medium |
| Вопросы владельцу | Acceptance/done definitions; orphan cleanup versus retention authority? |

### WP-reward-once — Reward/durability replay decision and guarded execution

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-reward-once — Reward/durability replay decision and guarded execution |
| Исходные IDs | A03-01, A03-02, A03-05, A03-07, A05-01, A05-04, A07-18, A04-08 |
| Root causes и домены | RC-07/09; Combat, Loot, Inventory, Character |
| Допуск | MIXED — decision/verification first |
| Техническая цель | Сначала подтвердить once-only effect set; затем prevent interrupted-retry duplication без новых наград. |
| Подтверждаемые инварианты | XP/loot/durability amounts, late preorder eligibility, death semantics не выбирать. |
| Предлагаемые изменения / варианты | Phase0 owner invariant+source mapping; Phase1 per-operation durable marker/effect in existing owner UoW or resumable consequence stages; separate leaf child tasks after effect list approved. |
| Запрещённые изменения | Fix rewards formulas/caps/late-loot/death policy; replay before dedup proof; all-domain finalizer rewrite. |
| Необходимые тесты | Injected fail after each effect before marker/status; repeat/restart/no second agreed effect and completed consequences; death SQLrollback no prematurely authoritative corpse per approved contract. |
| Regression risks / parity | Exact previous valid rewards/XP/durability and live/simulation parity. |
| Зависимости | Owner decisions mandatory; WP-combat-commit/inventory-sync/storage-harness; loot-transfer semantic contract. |
| Параллельность и leaf ownership | NOT immediately executable. Each owner leaf split under one operation-contract integrator. |
| Project skills | combat, backend, game-content, quality |
| Validators / Quality Gates | Fault boundary matrix and agreed invariant assertions only. |
| Размер | Medium phase0; later leaf estimates separately |
| Вопросы владельцу | Which effects once-only? Late loot cutoff? Death publication timing and authoritative store? |

### WP-loot-transfer — Exact SQL source membership

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-loot-transfer — Exact SQL source membership |
| Исходные IDs | A05-02, A02-01, A05-14 |
| Root causes и домены | RC-07/11; Loot/Inventory/Expedition |
| Допуск | TECH-HARDENING |
| Техническая цель | Transfer only expected current source and preserve shared transaction. |
| Подтверждаемые инварианты | No loot eligibility/drop/quantity rule changed; UoW atomicity. |
| Предлагаемые изменения / варианты | Inventory-owned semantic transfer facade accepts exact source/version with transaction; false membership rejects/no-op according contract. SQL row locks/constraints as appropriate. |
| Запрещённые изменения | Перенести SQL commits внутрь чужого facade и разорвать UoW; новую loot policy. |
| Необходимые тесты | Correct source moves once; different corpse/run/character rejected; concurrent transfer only one accepted source; rollback entire shared operation. |
| Regression risks / parity | Existing item IDs/placement and wallet transaction parity. |
| Зависимости | WP-boundary-state shared facade; storage-harness; reward-once notneeded for exact source proof. |
| Параллельность и leaf ownership | Inventory repository leaves one owner; Expedition caller separate after facade. |
| Project skills | backend, quality |
| Validators / Quality Gates | Real SQL membership/rollback/concurrency test. |
| Размер | Small |
| Вопросы владельцу | Return conflict/rejected code and expected source relation authoritative? |

### WP-boundary-state — Semantic owners persistent state

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-boundary-state — Semantic owners persistent state |
| Исходные IDs | A02-01, A02-03, A02-04, A02-05, A02-07, A02-06, A02-09, A04-09, A06-08 |
| Root causes и домены | RC-11; Character/Inventory/Loot/Expedition adapters |
| Допуск | TECH-HARDENING |
| Техническая цель | Replace foreign SQL/Redis shape access with owner use-case facade preserving UoW. |
| Подтверждаемые инварианты | Same operation ordering/results; shared transaction session remains allowed. |
| Предлагаемые изменения / варианты | One approved cross-owner operation at time: Inventory transfer/projection or Character sync; inject facade at composition root. No mass files moves. |
| Запрещённые изменения | Storage repository as supposed public semantic API; gameplay extraction A02-06 without decision. |
| Необходимые тесты | Facade contract + caller negative foreign storage access validator; SQL rollback parity and no extra commit; current payload golden. |
| Regression risks / parity | Same end-to-end action and per-owner transaction count. |
| Зависимости | WP-loot-transfer/inventory-sync/ac-sync interfaces coordinated, not duplicated facades. |
| Параллельность и leaf ownership | Architecture contract first; owner leaves then caller leaves disjoint. |
| Project skills | project, backend, quality |
| Validators / Quality Gates | Targeted ownership import/schema validator with allowlisted composition/UoW. |
| Размер | Medium |
| Вопросы владельцу | Which first owner slice and existing external consumers must stay compatible? |

### WP-boundary-dto — Runtime DTO ownership and public contracts

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-boundary-dto — Runtime DTO ownership and public contracts |
| Исходные IDs | A02-08, A02-03, A02-04, A06-07 |
| Root causes и домены | RC-11/12; shared schemas, Inventory/Character |
| Допуск | TECH-HARDENING |
| Техническая цель | Runtime session internal; shared only actual cross-side messages. |
| Подтверждаемые инварианты | Serialized public DTO fields/validation and frontend annotation runtime intact. |
| Предлагаемые изменения / варианты | Move ownership only selected runtime schema; expose purpose-specific immutable projection; no duplicate DTO shadow; imports at owner facade. |
| Запрещённые изменения | Mass schema migration, silent serialization/field changes. |
| Необходимые тесты | Current public JSON/validation golden; actual frontend+backend import/schema contract; runtime DTO forbidden foreign imports but public projection accepted. |
| Regression risks / parity | Existing inventory/character action response parity. |
| Зависимости | boundary-state contracts; code compatibility decision and library owner source. |
| Параллельность и leaf ownership | Shared schemas one owner; callers leaf tasks after exact export contract. |
| Project skills | project, backend, quality |
| Validators / Quality Gates | Schema contract + import boundary scanner. |
| Размер | Small |
| Вопросы владельцу | Any external consumer imports runtime DTO and genuine compatibility requirement? |

### WP-combat-io — Combat repeated state IO

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-combat-io — Combat repeated state IO |
| Исходные IDs | A09-05, A09-01 |
| Root causes и домены | RC-15; Combat executor/snapshot storage |
| Допуск | TECH-HARDENING |
| Техническая цель | Reuse revision snapshot and delta persistence for same accepted exchange. |
| Подтверждаемые инварианты | Resolver randomness, actor/log order, modifiers and effects unchanged. |
| Предлагаемые изменения / варианты | After commit contract, measure representative exchange; reuse read snapshot within executor and persist only agreed dirty actors/history delta. Variant batching existing methods. |
| Запрещённые изменения | Новый resolver/AI formulas; skip changed actor fields, unverified cache. |
| Необходимые тесты | Same seed/state exact live+simulation outputs; real-store ops/bytes count before/after; stale revision test rejects cache. |
| Regression risks / parity | Full Combat outputs and archive logs golden. |
| Зависимости | WP-combat-commit; WP-combat-archive for history ownership. |
| Параллельность и leaf ownership | Same session manager leaves; sequential integration with correctness. |
| Project skills | combat, backend, quality |
| Validators / Quality Gates | Parity + deterministic IO counters; no production capacity claim. |
| Размер | Small |
| Вопросы владельцу | Target IO budget/workload; any actor update side effects in current full save? |

### WP-chat-fanout — Bounded WS slow-consumer isolation

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-chat-fanout — Bounded WS slow-consumer isolation |
| Исходные IDs | A09-04, A07-16 |
| Root causes и домены | RC-16; Chat WS transport |
| Допуск | TECH/abuse VERIFY-FIRST |
| Техническая цель | Slow receiver doesn't serialize all sends; resource lifecycle bounded. |
| Подтверждаемые инварианты | Legitimate message order/reconnect/authorization unchanged. |
| Предлагаемые изменения / варианты | Per-connection bounded send queue and explicit overflow handling; bounded connection/process budget only owner-agreed policy. Existing WS library capability inspect first. |
| Запрещённые изменения | Выбирать new game/chat UX loss/retention policy or unconditional disconnectthreshold by guess. |
| Необходимые тесты | One slow recipient: others progress in order; overflow/reconnect contract; disconnect cleanup; abuse probe isolated. |
| Regression risks / parity | Same delivered sequence for healthy receivers and membership gates. |
| Зависимости | WP-chat-access; owner overflow/rate limits; storage-harness only when persistence involved. |
| Параллельность и leaf ownership | WS transport leaf vs chat archive separate; bootstrap leaf coordinate. |
| Project skills | backend, quality |
| Validators / Quality Gates | Deterministic slow socket/lifecycle tests + observed finite buffers. |
| Размер | Small |
| Вопросы владельцу | Drop/disconnect/backpressure policy and budget? |

### WP-ai-resource-budget — GenerationAI long IO resources

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-ai-resource-budget — GenerationAI long IO resources |
| Исходные IDs | A09-09, A09-10 |
| Root causes и домены | RC-16; GenerationAI worker |
| Допуск | TECH-HARDENING |
| Техническая цель | No SQL connection held across avoidable external/image work; no event-loop block. |
| Подтверждаемые инварианты | Same result/input/job/status semantics and context ownership. |
| Предлагаемые изменения / варианты | Release transaction around external calls with explicit reload/version contract; bounded executor/offload normalization and cancellation. Use existing pools. |
| Запрещённые изменения | Prompts/image content changes; unbounded background jobs. |
| Необходимые тесты | Blocking provider/image fixture: unrelated jobs progress; pool released; timeout/cancel/restart persisted state consistent. |
| Regression risks / parity | Exact output bytes or agreed codec parity and job status. |
| Зависимости | WP-ai-durability and measured pool workload; owner limits. |
| Параллельность и leaf ownership | Same AI worker leaves integration sequential. |
| Project skills | backend, game-content, quality |
| Validators / Quality Gates | Pool/event-loop deterministic probes + lifecycle tests. |
| Размер | Small |
| Вопросы владельцу | Supported CPU/memory/cancel budget and provider timeout? |

### WP-browser-retention — Browser chat bounded history decision

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-browser-retention — Browser chat bounded history decision |
| Исходные IDs | A09-11 |
| Root causes и домены | RC-16; frontend Chat |
| Допуск | MIXED — decision/verification only |
| Техническая цель | Establish bounded buffer/history UX contract before implementation. |
| Подтверждаемые инварианты | Visible history/reconnect behavior not silently changed. |
| Предлагаемые изменения / варианты | Phase0 document actual append/history sources and owner limit policy; future isolated buffer change only after UX boundary approval. |
| Запрещённые изменения | Gameplay UI/UX redesign or silently discard history. |
| Необходимые тесты | Proposed after gate: long-session finite memory; load older history/order/scroll behavior as agreed. |
| Regression risks / parity | Existing user's visible messages/reconnect expectations. |
| Зависимости | Owner UX/retention decision; chat archive authoritative history. |
| Параллельность и leaf ownership | Deferred; frontend leaf separate from backend WS. |
| Project skills | frontend, quality |
| Validators / Quality Gates | Browser behavior evidence if separately approved. |
| Размер | Small phase0 |
| Вопросы владельцу | How much stays visible and how retrieves older history? |

### WP-runtime-isolation — Least privilege deployment config

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-runtime-isolation — Least privilege deployment config |
| Исходные IDs | A08-02, A08-08, A08-12, A08-13 |
| Root causes и домены | RC-04/05; Compose/provision/services |
| Допуск | TECH plus operational VERIFY-FIRST |
| Техническая цель | Explicit bindings/credentials/file modes/capabilities fit actual service needs. |
| Подтверждаемые инварианты | Non-root/TLS/existing queues and service operation preserve. |
| Предлагаемые изменения / варианты | Separate sub-slices bind local observability loopback; secure env temp/rename mode; service credential scope; optional filesystem/resource hardening after compatibility smoke. |
| Запрещённые изменения | Применять на VPS, rotate all secrets, break writable dirs/workerlimits by speculative constraints. |
| Необходимые тесты | Render intended binding/mode checks; each service reads required store; forbidden access denied if scoped; writable dirs/caps smoke. |
| Regression risks / parity | Local dev opt-in and deployment start operational contract. |
| Зависимости | Owner exposure/network/service credential matrix; supply-chain/runtime images. |
| Параллельность и leaf ownership | Compose/provision shared leaves one owner; independent app log/metrics leaves. |
| Project skills | release, backend, quality |
| Validators / Quality Gates | Rendered config + disposable service permission/startup smoke. |
| Размер | Medium |
| Вопросы владельцу | Actual operators/network exposure, writable dirs and per-service credentials? |

### WP-recovery-readiness — Operational recovery verification

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-recovery-readiness — Operational recovery verification |
| Исходные IDs | A08-15 |
| Root causes и домены | RC-09/13; backups/monitoring |
| Допуск | VERIFY-FIRST — no production action |
| Техническая цель | Obtain restore/alert evidence without declaring tested readiness from docs. |
| Подтверждаемые инварианты | No live writes/data disclosure. |
| Предлагаемые изменения / варианты | Read-only inventory of backup/monitor ownership; approved disposable sanitized restore exercise and alert synthetic test later. Record unknowns explicitly. |
| Запрещённые изменения | Production operations or claim recovery verified from repository only. |
| Необходимые тесты | Future approval: restore consistency/schema/media checks, recovery time, synthetic alert delivered to approved test sink. |
| Regression risks / parity | Existing backup artifacts remain untouched. |
| Зависимости | Owner target/sanitization/resource authorization; site migrations/schema scope. |
| Параллельность и leaf ownership | Independent evidence task, external operations separately authorized. |
| Project skills | release, quality |
| Validators / Quality Gates | Restore transcript + alert evidence, not code coverage. |
| Размер | Small verification |
| Вопросы владельцу | Есть ли backups, allowed isolated restore target и recovery objectives? |

### WP-transport-policy — Trusted proxy/scheme token paths

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-transport-policy — Trusted proxy/scheme token paths |
| Исходные IDs | A08-14, A08-06 |
| Root causes и домены | RC-04/06; proxy/front links |
| Допуск | VERIFY-FIRST |
| Техническая цель | Verify external scheme/forwarded trust to avoid HTTP bearer URLs. |
| Подтверждаемые инварианты | Supported TLS/proxy deployment and legitimate URL generation preserve. |
| Предлагаемые изменения / варианты | Read rendered proxy/header chain; controlled test host proves trusted scheme; future fixed trusted proxy/address policy if confirmed. |
| Запрещённые изменения | Change token/public link format or actual production proxy assumptions unverified. |
| Необходимые тесты | Forged forwarded headers untrusted rejected/ignored; trusted TLS chain generates HTTPS token links; redacted logs. |
| Regression risks / parity | Login/game WS bootstrapping and public links. |
| Зависимости | Owner actual proxy hops/domains; surface-isolation/log-redaction leaves shared Nginx. |
| Параллельность и leaf ownership | Read-only verify independent; actual Nginx edit one integrator. |
| Project skills | frontend, release, quality |
| Validators / Quality Gates | Controlled proxy scheme smoke with synthetic credentials. |
| Размер | Small verification |
| Вопросы владельцу | Actual TLS termination/proxy chain and forwarded trust list? |

### WP-browser-render — Unsafe-render sink evidence

| Поле | Контракт пакета |
| --- | --- |
| ID и имя | WP-browser-render — Unsafe-render sink evidence |
| Исходные IDs | A07-17 |
| Root causes и домены | RC-02/06; frontend render sinks |
| Допуск | VERIFY-FIRST |
| Техническая цель | Confirm untrusted input reaches HTML sink before selecting fix. |
| Подтверждаемые инварианты | Intended formatted server content contract preserve. |
| Предлагаемые изменения / варианты | Trace source→sink and escaping/allowlist sanitizer boundary; controlled harmless payload only isolated fixture. If confirmed future narrow safe text/sanitized rendering. |
| Запрещённые изменения | Mass frontend UX rewrite or presume every innerHTML exploit. |
| Необходимые тесты | Future test unknown text cannot become executable markup; expected trusted formatting intact. |
| Regression risks / parity | Current message/content formats. |
| Зависимости | Owner trusted HTML policy; dependency source sanitizer if needed. |
| Параллельность и leaf ownership | Frontend sink leaf independent after contract; no browser gameplay changes automatic. |
| Project skills | frontend, quality |
| Validators / Quality Gates | Source-sink fixture + browser render evidence on isolated app. |
| Размер | Small verification |
| Вопросы владельцу | Which payloads intended rich HTML and who owns sanitization? |

## Route-policy evidence: методы, callers и серверная граница

Статическое повторное чтение, без live ingress/probes. [app mounts](../../src/backend/app.py:53) и [Nginx generic proxy](../../deploy/nginx/site.conf.template:120) показывают потенциальную публичную цепочку; effective production неизвестен. [Existing service gate](../../src/backend/core/game_auth.py:58) возвращает fixed `frontend-site` без scopes; [get_current_user](../../src/backend/core/auth.py:16) always `is_superuser=False`; [BaseApiClient](../../src/frontend/core/api.py:93) добавляет internal service header всем запросам. Поэтому «добавить Depends(get_current_user) ко всему» не является server admin policy. Подпись/type/audience/expiry/session/selected-char checks [game_auth](../../src/backend/core/game_auth.py:134) сохранить.

В каждой строке последний столбец — предлагаемый acceptance contract, а не уже установленная permission policy. Авторитетный перечень callers/roles утверждается владельцем до кода. Actual root-relative prefixes указаны; edge `/api/` не доказывает публикацию `/exploration` или отдельных Chat app routes.

| IDs / пакет | Метод и path | Current check / недостающее | Consumer impact | Предлагаемая policy / positive + negative |
| --- | --- | --- | --- | --- |
| A07-01; WP-auth-game | GET `/api/game/combat/{char_id}/{view,snapshot,logs}`; POST `/{char_id}/{moves,feints/pin,result/continue}` | [Combat router](../../src/backend/features/combat/api/router.py:27) / [dependency](../../src/backend/features/combat/dependencies.py:23): orchestrator, без principal/owner. | Frontend [Combat bearer](../../src/frontend/integrations/backend_api/combat.py:18); worker не HTTP caller. | Game token+active selected character+owner/runtime participant; valid same DTO, anon/site/wrong owner/stale rejected до orchestrator. |
| A07-01 optional Legacy | GET `/api/game/rift/{char_id}/view`; POST `/{char_id}/{leave,travel/start,travel/tick,action,complete}` | [Rift router](../../src/backend/features/rift/api/router.py:31) / [dependency](../../src/backend/features/rift/dependencies.py:91): service без identity. | [Rift client bearer](../../src/frontend/integrations/backend_api/rift.py:7). | Only owner-approved Legacy support slice; same negative identity cases; A04-01 authoritative action/game-outcome поля отдельный MIXED/Legacy gate. |
| A07-02; WP-auth-config | GET `/api/internal/config`, `/{namespace}`; PATCH `/{namespace}/{key}`; DELETE `/{namespace}/{key}`, `/{namespace}` | [Config router](../../src/backend/features/game_config/api/router.py:6): key/value validation есть, caller policy нет. | [GameConfig client](../../src/frontend/integrations/backend_api/game_config.py:52) service header. | config.read/write/reset scopes; positive agreed caller retains validation/defaults; player/anonymous/read-only mutation denied до manager. |
| A07-03; WP-auth-admin | POST `/api/admin/generation-ai/news-covers`; GET `/tasks/{task_id}` | [GenerationAI](../../src/backend/features/generation_ai/api.py:23): DB/task dependencies без permission. | Cabinet/Studio producer; existing worker consumes trusted task identity. | content.generate/task.read before mutation/input/enqueue; denied produces no rows/jobs, approved preserves payload/status. |
| A07-03; WP-auth-admin | GET `/api/admin/monsters/generated`, `/generated/summary`; POST `/generated/rebuild/{plan,apply}`, `/generated/clans/{clan_id}/{regenerate-flavor,regenerate-member-images}`, `/generated/clans/regenerate-member-images`, `/generated/members/{member_id}/regenerate-image` | [Monsters router](../../src/backend/features/monsters/api/router.py:24): DI services, no caller gate. | [Studio admin client](../../src/studio/integrations/backend_api/admin_monsters.py). | Distinct content.read/rebuild.plan/rebuild.apply/generate capabilities; forbidden no provider/SQL/enqueue; positive current validation and result. |
| A07-03; WP-auth-admin | GET `/api/admin/combat-ai/simulation-runs`, `/{run_id}`; POST `/simulation-runs/{clear,clear-training,cleanup-stale,demo,family-pressure,family-pressure-batch,live-demo,live-demo-batch,train-synthetic,train-battle}` | [Simulation router](../../src/backend/features/combat/api/ai_simulation_router.py:36): DB dependencies no role scope. | [CombatAiTesting client](../../src/frontend/integrations/backend_api/combat_ai_testing.py:51) no bearer, inherited service header. | read/delete/launch/train capabilities; ordinary game user and read-only service denied before effect; permitted service result/job same. AI policy excluded. |
| A07-04/A08-03; WP-auth-internal | GET `/api/internal/combat/sessions`, `/sessions/{session_id}`; `/api/internal/{scenario,exploration}/sessions` | [Combat internal](../../src/backend/features/combat/api/internal_router.py:9), [Scenario](../../src/backend/features/scenario/api/internal_router.py:7), [Exploration](../../src/backend/features/exploration/api/internal_router.py:7): app-state managers no gate. | Frontend internal-session clients/Studio service callers. | Scoped diagnostics.read and approved projection/bounded work; direct backend anon/player denied; permitted caller parsing positive. |
| A07-04; WP-auth-internal | GET `/api/game/combat/analytics/{filters,rollups,drilldown,combat-summary}`, `/debug/raw/{combat_id}`; POST `/backfill` | [Analytics](../../src/backend/features/combat/api/analytics_router.py:20): no actor role; backfill mutates. | Studio analytics selected-source client. | Separate aggregate.read/raw.debug/backfill.write; source-readonly blocks write; normal player no implied raw access; authorized parsing retained. |
| A07-06; WP-chat-access | GET `/chat/history/{channel_type}/{scope_id}`, `/chat/dm/sessions/{session_id}/messages`; existing GET/POST `/chat/dm/sessions` | [Chat REST](../../src/backend/chat/api/router.py:16): JWT site sub UUID decoded; history `_char_id` not used for membership. | REST account UUID; [DM repo](../../src/backend/chat/repositories/session_repo.py:16) UUID members. | Membership before body hydration, private/group scope owner check; outsider/inactive member denied; member bodies/order retained; preserve already filtered DM list. |
| A07-07/08; WP-chat-access | WS `/ws/realtime`, envelope `chat.send` | [WS](../../src/backend/realtime/api/ws.py:87) validates Origin/game token/session; URL char ID used separately; [send](../../src/backend/realtime/api/ws.py:320) backfills scope without full policy. | Browser HttpOnly game cookie; REST UUID vs game char:int explicit mapping. | URL char equals verified selected char; channel/scope membership; client cannot system-publish. Negative wrongURL/foreignDM/group/system emits nothing; legit scope passes; existing Origin/token negatives retain. |
| A07-11; WP-auth-game | GET `/api/game/inventory/{char_id}/view`; POST `/{char_id}/{actions,close}` | [Inventory router](../../src/backend/features/inventory/api/router.py:25): auth+owner exists; [scope check](../../src/backend/core/auth.py:63) no-op for site token. | [Inventory client](../../src/frontend/integrations/backend_api/inventory.py:12) bearer already. | Mutations require active selected game session; account-only view policy owner decision. Preserve cross-user denial; site mutation/wrong selected denied, valid owner succeeds. |
| A07-13; WP-auth-game | POST `/exploration/{move,interact,use_service}`; GET `/exploration/{look_around,local_map}` | [Exploration](../../src/backend/features/exploration/api/router.py:18): char ID and gateway no principal. | [Exploration client](../../src/frontend/integrations/backend_api/exploration.py:20) bearer; prefix outside generic `/api/` means external ingress unknown. | Explicit game access or scoped service-delegated actor, no frontend-only trust; wrong/missing actor denied, actual client→ASGI positive; knowledge map policy excluded. |
| A07-12; WP-studio-readonly | POST Studio `/admin/combat-ai-testing/run`, `/admin/content-ops/{monster-rebuild-plan,monster-rebuild-apply,regenerate-clan-flavor,regenerate-clan-member-images,regenerate-visible-member-images,regenerate-member-image}` | [Studio app](../../src/studio/app.py:137): source selection not auth/readonly; action registration forwards mutators. | Selected-source HTTP clients; allow isolated local compute outside source connection. | Capability gate before any direct/indirect source write, local/prod selected source read-only; permitted analytical read positive, blocked mutation no HTTP write. Access policy separate owner gate. |
| A07-15/A08-04; WP-surface-isolation | Prefix `/api/dev/rift`: POST `/hex-test/start`, GET `/hex-test/{instance_id}/state`, POST `/hex-test/{instance_id}/{move,resolve-combat,next-floor}` | [Mount](../../src/backend/features/rift/api/router.py:179), [Hex routes](../../src/backend/features/rift/api/hex_test_router.py:20): default-on devflag/no auth; runtime dict unbounded. | Dev browser/testing consumer; production effective flags unknown. | Prod/unset off, approved dev opt-in positive; edge deny independent of backend gate. Hex quota/retention/geometric rules deferred experimental, unknown-ID scan budget only if admitted. |
| A08-05; WP-metrics-redaction | GET `/metrics` | [Metrics endpoint](../../src/shared/infrastructure/metrics_endpoint.py:12) no gate; [middleware](../../src/shared/infrastructure/metrics_middleware.py:23) raw-path label selected before call_next. | Approved internal scraper, current deployed scraper unknown. | Finite route labels+scrape policy; synthetic secret marker absent/unknownpaths bounded; approved scrape positive/unauthorized negative as decided. |

## Reliability evidence: authority, interruption и recovery gate

Технический инвариант хранит/доставляет уже принятое решение; игровой инвариант определяет, что именно должно быть принято. Их не смешивать. Live Redis и SQL checkpoint могут быть authoritative в разных фазах; таблица не назначает один universal master store. `WP-reward-once` нельзя исполнять до решения об identity/effect set и нельзя включать replay раньше dedup/recovery proof. Существующая SQL UoW не дробится ради красивого facade.

| IDs / пакет | Current anchors | Authoritative state | Repeat/failure window | Necessary acceptance / preserved game semantics |
| --- | --- | --- | --- | --- |
| A03-01/02; reward-once MIXED | [Finalizer](../../src/backend/features/combat/workers/tasks/victory_finalizer_task.py:69), [XP](../../src/backend/features/combat/runtime/services/experience_finalizer.py:84) | Redis live/AC; SQL Expedition pending; PG archive pointers/Mongo body. | active=0 before effects; failure leaves undiscoverable consequences; additive XP repeated. | Owner approves operation/effect identity and once semantics first; crash every effect/status boundary and restart; frozen valid reward amounts exactly retained. |
| A03-03/04/09; combat-commit | [Commit](../../src/backend/infrastructure/combat/managers/session.py:594), [create](../../src/backend/infrastructure/combat/managers/session.py:81) | Redis accepted combat revision/actors/queue/log/meta. | transaction=False commands; owner check separate; create resets same ID. MULTI does not rollback command runtime errors. | Actual primitive/server capability test; partial command fault, expired lease/stale writer, same-ID same/conflicting fingerprint cases; resolver/turn order unchanged. |
| A03-07; reward-once MIXED | [Durability](../../src/backend/features/inventory/services/inventory_service.py:197) | Item mechanics SQL, Redis inventory/AC projection. | Redis set→SQLcommit→ACsync→marker; interrupted repeat may reapply damage. | Agreed event identity and unchanged durability scope/amount; SQL dedup+effect UoW, repeatable projection; fail before/after each commit/marker and concurrent same event. |
| A05-01; reward-once MIXED | [Claim](../../src/backend/features/loot/workers/tasks/loot_claim_task.py:67) / [credit](../../src/backend/features/loot/workers/tasks/loot_claim_task.py:230) | SQL source balances/wallet; Redis cleanup cache. | Safe no processed guard; missing/insufficient source still credit payload; duplicate/crash may inflate. | Existing permitted debit equals credit, source absence/conflict policy owner-approved; real PG repeat/concurrent/absent source/batch faults. No new loot/economy rule. |
| A05-02; loot-transfer | [Item source](../../src/backend/features/loot/workers/tasks/loot_claim_task.py:214) | SQL ItemPlacement exact holder_type+holder_id. | Wide holder_type and missing rowcount/source can move foreign item. | Correct source succeeds, foreign corpse/system/loot_pending transitions follow approved existing contract; simultaneous claim/rollback preserve one UoW. |
| A05-03; inventory-sync | [Hydrate](../../src/backend/features/inventory/services/inventory_service.py:84), [flush](../../src/backend/features/inventory/services/inventory_service.py:168) | Redis latest accepted session; SQL checkpoint. | Full SET + old clean snapshot can erase new action/dirty mutation. | Real RedisJSON action/action/action-flush barriers; revision compare-clear, checkpoint failure/restart; no equip/use/formula changes. |
| A05-05; stream-recovery | [App Streams construction](../../src/backend/core/containers/redis.py:136); installed library bytes require source-provenance check | Redis Stream PEL transport; each effect owned separately. | Inspected consumer reads only `>`; failed pending not reclaimed; shipped version unknown. | Reclaim only after affected handler replay-safe proof; before/after effect/ACK crash+restart; bounded retry/DLQ, no broker exactly-once claim; fix canonical library owner. |
| A05-06/15; chat-archive | [Cursor](../../src/backend/chat/workers/archive.py:44), [write failures](../../src/backend/chat/workers/archive.py:101) | Redis body until archived; Mongo body/SQL navigation. | Cursor moves past failure; concurrent append/seq assumptions need actual Mongo. | Nth-write fail+restart+repeat no gaps/duplicates; real Mongo append/seq barrier gate before scheduling/drain optimization; history order/content unchanged. |
| A05-08/A04-12/13/18; ai-durability | [Scheduling](../../src/backend/features/generation_ai/workers/tasks.py:20), [service](../../src/backend/features/generation_ai/services.py:168) | SQL task status/identity; Mongo input/result; ARQ delivery. | Commit before enqueue, volatile scheduling list; input/result can lack durable obligation. | Accepted input reconstructible, done readable; fault after commit/enqueue/input/result→restart owner-local reconciliation; no retry counts/prompts/content changes. |
| A05-11; combat-readback | [Reader](../../src/backend/features/combat/services/result_archive_service.py:147), [SQL model](../../src/backend/infrastructure/combat/models/finalization.py:12) | PG identity/participants/pointer; Mongo payload. | row.finalization absent; caught as missing. | Persist→expire/remove isolated Redis→same authorized archived DTO; distinguish unavailable/notfound; missing combat outcome fallback not chosen. |
| A05-12; session-lifecycle | [Rotation](../../src/frontend/features/auth/services/site_auth_service.py:124), [persistence](../../src/frontend/features/auth/integrations/auth_persistence.py:67) | Site SQL refresh tokens. | Delete/new insert commits separated; concurrency/lostresponse policy open. | Single-store UoW fail insert preserves old; parallel/lostresponse fixtures according owner policy; no gameplay. |
| A05-13; site-migrations | [0001](../../src/frontend/alembic/versions/0001_site_schema_baseline.py:13), [0002](../../src/frontend/alembic/versions/0002_security_baseline.py:23), [ORM](../../src/frontend/features/auth/models/refresh_token.py:21) | SQL migration history. | Live create_all adds token_hash before later migration; actual deployed revisions unknown. | Isolated empty and actual supported baseline upgrades/ORM CRUD; no drop/stamp/wipe/rewritten applied history by assumption. |
| A06-03/04; storage-harness/test-controls | [Quality report](../06_testing_quality.md), [current runner](../../tools/dev/check.py) | Actual supported PG/RedisJSON/Mongo/Streams capability, not mock counter. | Component tests do not prove boundary atomicity/fault conservation. | Small opt-in disposable suites per selected invariant; synthetic fixture provenance; game rule expectation separately owner gated. |
| A09-01; combat-archive/combat-io | [History](../../src/backend/infrastructure/combat/managers/session.py:807) | Redis log identity/order. | Full HGETALL/reencode/HSET repeated, aggregate O(T²). | After commit/replay contract: exact old/new output and duplicate append, bytes/commands per delta; no production throughput assertion. |
| A09-02; ac-sync | [Scanner](../../src/backend/infrastructure/actor_state/managers/session.py:520) | AC Redis dirty state/revision. | Restart cursor0; cap selected does not cap examined; fairness uncertain. | No-candidate/all-hot/more-thanlimit and eventual coverage fixtures; bounds examined work; regen formula/rate unchanged, notification timing gate. |
| A09-03; chat-archive | [Batch cadence](../../src/backend/chat/workers/archive.py:20), [schedule](../../src/backend/chat/workers/archive.py:218) | Redis backlog→Mongo/SQL accepted archive. | 500/topic per10min≈0.833messages/s/topic arithmetic; actual capacity not measured. | Checkpoint/append proof first; bounded multi-batch drain under slow DB/backlog/retention tests; preserve ordering, no CCU inference. |
| A09-04; chat-fanout | [Fanout](../../src/backend/chat/services/connection_manager.py:19), [send→archive](../../src/backend/chat/services/message_service.py:39) | In-process subscribers; Redis archive buffer. | Sequential send slow receiver blocks followers; replicas split process audience. | Two controlled sinks/barrier/timeout/order/finite buffer; owner overflow policy; multi-process fanout verify/architecture decision separately, no automatic new service. |

## Границы исполнения

Legacy Rift restore/complete/dirty/seed/heart/outcome findings остаются в матрице как optional/deferred. Нет пакета развития Hex geometry/floors, World generation, combat formulas, progression/economy, новых skills/effects или gameplay UI. NO-ACTION и unnumbered context не создают обязательные задачи. `WP-browser-retention` — только согласование UX/history контракта; `WP-browser-render`, `WP-transport-policy`, `WP-recovery-readiness` сначала verification, не предрешённое исправление.



## Дополнительные associations из матрицы: narrow gates

Поле source IDs включает также related verification/owner-context из compact index. Association не означает, что один WP обязан закрыть все manifestations или получает разрешение на Legacy/mechanics. Для следующих связей основной допуск ограничен отдельно:

| Association | Допустимый slice / граница | Necessary tests / dependency |
| --- | --- | --- |
| A02-06/09 → boundary-state | Только ownership прежней policy и DI/orchestration separation выбранного consumer; никакие formulas/AI rules не меняются. Не переносить весь simulation module автоматически | Golden live/simulation DTO/core output; один выбранный semantic owner leaf, caller contract прежде files moves |
| O02-04 → ac-sync | Связь исключительно с generation/CAS proof как reusable test pattern. Legacy Rift completion остаётся optional после support decision; current WP не исправляет Rift | Future selected runtime real-store barrier; нет утверждения о подтверждённой corruption |
| A04-08 → reward-once | Knowledge cap и его wiring — MIXED gameplay gate, вне implementation. Association только owner-decision row, не изменение cap/default/XP | Owner выбирает existing cap contract отдельно; technical lifecycle tests не закрепляют новую reward сумму |
| A04-09 → boundary-state | Return/rejection contract уже существующего movement owner; отказ не выдаётся за success. Не задавать новые movement/World rules | Valid/refused gateway outcomes and no follow-up success effects; supported consumer decision |
| A04-10 → ai-durability | World cache publication/status — отдельный owner-local verification slice, общий принцип durable input/result. Не расширяет пакет до World generation | Existing required artifacts/versions перечислены owner; missing cache artifact cannot publish ready; World facade/status gates прежде изменения |
| A04-11 → ai-durability | Проверить meaning/units/owner двух retry limits; не выбирать новое количество попыток либо AI policy. Исполнение conflict fix лишь после documented current intended contract | Boundary retry case against approved unchanged policy, count comparison и accepted task recovery |
| A04-14 → test-controls | Stale offline World audit/helper — технический tool contract; не развитие World. Только выбранный поддерживаемый tool repair после owner applicability gate | Collection/import positive control и script dry-run на synthetic fixture; никакие генерации/real data writes автоматически |
| A05-14 → loot-transfer | Concurrent active Expedition — VERIFY-FIRST related shared SQL owner case; не exact-source defect и не автоматически one-active gameplay rule | Owner existing active uniqueness contract; isolated SQL barrier before deciding whether narrow constraint/lock package exists |
| A06-06/12 → test-controls | Здесь meaningful runner/app audit acceptance tests; actual CI edits принадлежат quality-provenance, hook/app source edits — supply-chain. Не дублировать leaf ownership | Same selected ref behavioral check and audited locked app manifest; no100%patch policy |
| A06-08 → boundary-state | Narrow owner facade/import/DTO validator, допускающий shared UoW и composition root. Отдельный signal, не scanner-wide blanket ban | Known foreign write/import rejected, legal facade/UoW accepted; tests owned test-controls co-review |
| A07-08/16 → session-lifecycle | Verified selected-char bootstrap binding technical; abuse/lifecycle budget A07-16 сначала VERIFY-FIRST. Channel member policy в chat-access, buffer policy chat-fanout | Wrong URL ID rejection+legit cookie reconnect; isolated stale sessions/resource lifecycle trace before new limits |

Эти secondary slices не увеличивают число37пакетов; после scope выбора они либо остаются verification/decision note, либо отдельно оцениваются как disjoint implementation leaf. Полное source severity/evidence/stage остаётся в [матрице](01_technical_findings_matrix.md).
