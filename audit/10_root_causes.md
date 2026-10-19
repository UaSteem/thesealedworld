# Аудит 10/10 — Системные причины и связи между находками

> **Обновление 19.10.2026:** исторический анализ; текущие отметки исправлений по коммитам см. в [реестре](10_findings_registry.md#быстрая-сверка-исправлений--19102026). Закрытие отдельного проявления не означает устранения всей системной причины.

Дата сопоставления: **09.10.2026**. Репозиторий: Sealed World / TurnBasedMMORPG. Объект — текущее рабочее дерево, включая существующие пользовательские изменения. Основание — отчёты [01](01_project_inventory.md), [02](02_architecture_boundaries.md), [03](03_combat_runtime.md), [04](04_rift_world_generation.md), [05](05_persistence_consistency.md), [06](06_testing_quality.md), [07](07_application_security.md), [08](08_infrastructure_security.md), [09](09_performance_scalability.md). Это межаудитное сопоставление, **не новый security-аудит и не план реализации**.

## 1. Основной вывод и границы доказательств

Выделено **17 системных механизмов**. Они объясняют повторяющиеся классы проблем, но не превращают связанные находки в один дефект или одну задачу. Самые существенные связи проходят через HTTP-authority, принятие многошаговой операции, версию живого состояния, долговечную доставку и доказательность проверок. Другой класс — повторная работа с полными документами и отсутствие бюджета на просмотренные объекты, очередь и получателя. Смена языка, дробление всех features на сервисы и повышение общего coverage сами по себе эти механизмы не устраняют.

Системная причина ниже — наблюдаемый механизм, который воспроизводится в нескольких путях, либо общий контракт между слоями. Это не утверждение о мотивах автора, истории принятия решений или отсутствии инженерной дисциплины. Указание направления стабилизации не задаёт очередь, сроки, исполнителя, выбранную архитектуру или разрешение на изменения.

Отчёты относятся преимущественно к одному дню и dirty tree с базовым HEAD `6ccc9256`; одинаковый HEAD не доказывает тождественность содержимого всех исследованных снимков. Здесь выборочно заново прочитаны актуальные маршруты/auth, finalizer, Combat commit/log manager, Loot transfer, Character dirty operations, Rift restore/flush, GenerationAI payload/schedule, Chat cursor/buckets, CI, migrations и archive reader. Где нового исполнения не было, результат не называется воспроизведением. Production, базы, registry, GitHub protections, реальные secrets, tunnel и действующий ingress не проверялись. Остальные file/line anchors сохраняют происхождение из соответствующего аудита.

Оси оценки сохраняются независимо:

| Ось | Как применять эту сводку |
| --- | --- |
| Техническая severity | Брать у исходного ID с его условиями; родительская причина не получает автоматически максимальную severity всех детей |
| Доказательность | Различать код, подтверждённое окно отказа, локальную пробу и гипотезу гонки; перечисление одного ID в двух причинах не усиливает доказательство |
| Стадия | Pre-alpha/alpha paths, Experimental Hex, Dev-only Studio/local Compose, Legacy player Rift/offline helpers и Shared infrastructure оценивать отдельно |
| Срочность | Следует из доступности и ущерба. Публичную административную границу следует проверить до дальнейшей публикации; experimental concurrency обычно относится к стабилизации соответствующего домена |

**Production state unknown.** Конфигурация репозитория показывает предполагаемый ingress, а не состояние VPS. Развёрнутые образы и overrides неизвестны. Предполагаемая публичная достижимость high-impact API требует отдельной разрешённой проверки владельцем; отчёт не объявляет компрометацию. Pre-alpha не делает сломанный ownership допустимым, но влияет на срочность. Неподключённый генератор и старый dev-переход не приравниваются к сломанному текущему пользовательскому пути.

**Термины Rift:** старый player runtime, описанный в 04/07 как experimental, — **Legacy относительно текущего Hex-направления**. Его поддержка и фактическая публикация неизвестны; наличие кода и routers не доказывает ни активную поддержку, ни отключение. Hex — отдельная Experimental/Dev-only поверхность. Эта разница сохраняется при оценке срочности и не меняет историческую классификацию исходных отчётов.

## 2. Проверка исходных гипотез

| Гипотеза | Результат сопоставления | Где разобрана |
| --- | --- | --- |
| Неравномерная авторизация | Подтверждена в adapters; отсутствие gate, недостаток membership и lifecycle credentials — разные нарушения | RC-01, RC-03; ingress/dev — RC-04 |
| Идемпотентность многошаговых операций | Подтверждён разрыв между identity операции, эффектом и маркером; completed repeat часто защищён, interrupted repeat — нет | RC-07; версия/CAS — RC-08 |
| Восстановление между хранилищами | Подтверждены разные acceptance/recovery gaps; общего distributed ACID не требуется для вывода | RC-09, RC-10 |
| Проверки настоящих хранилищ | В текущем suite не обнаружена репрезентативная real-PG/RedisJSON/Mongo/Streams защита; внешние suites неизвестны | RC-12 |
| Quality gates | Gate существует, но событие/ref, semantic invariant и artifact provenance охвачены неодинаково | RC-13; clean install — RC-14 |
| Зависимости CI | Подтверждён missing sibling source; различие Docker resolution не доказано как подмена пакета | RC-14 |
| Повторная полная сериализация | Подтверждена для Combat history/actors, Rift instance, Mongo chat и повторного Character sync; стоимость server/network не измерена | RC-15 |
| Dev/internal/public boundaries | Подтверждены default-on/mount/proxy и локальные bindings; Studio source label не обеспечивает read-only | RC-04; API policy — RC-01 |
| Дрейф документации | Подтверждены stale stage/anchors и неполная stable docs; связь с возникновением каждого runtime defect остаётся интерпретацией | RC-17 |

## 3. Системные причины

### RC-01 — Полномочие не является обязательной частью контракта входного адаптера

**Связанные ID:** A07-01, A07-02, A07-03, A07-04, A07-06, A07-07, A07-13; частично A07-12 и A08-03. Домены: Combat, Rift, GameConfig, GenerationAI, Monsters, analytics, Exploration, Chat, Studio.

**Механизм.** Router/service принимает идентификатор объекта либо подходящий по форме payload, но право вызывающего проверяется отдельной необязательной dependency, upstream UI или вообще отсутствует. Для Chat login существует, но membership и разрешённый channel/scope не входят в общий access decision. Ошибка «нет principal» и ошибка «principal не имеет права на объект» имеют общий пробел контракта, но требуют отдельных policy и проверок.

**Evidence:** `src/backend/features/rift/api/router.py:31–97` и `src/backend/features/combat/api/router.py:26–139` — player routes без caller dependency; `src/backend/features/game_config/api/router.py:6–64`; `src/backend/features/generation_ai/api.py:23–70`; `src/backend/chat/api/router.py:16–47,88–98`; `src/backend/realtime/services/chat_bridge.py:78–91`. Текущий Rift router перепроверен: mount игрового router без auth сохраняется. Backend skill уже требует owner check (`.agents/skills/turnbasedmmorpg-backend/references/feature-architecture.md:26` и раздел Core Rules); незнание правила не установлено как причина.

**Компенсации:** frontend admin middleware, корректные internal-key gates у Lobby/AdminPlayers, game JWT/session lock и owner checks у ряда features; Runtime guards проверяют участие/состояние. Они не защищают соседний самостоятельно опубликованный adapter.

**Уверенность:** высокая в статическом пропуске проверок; неизвестна фактическая production экспозиция. Стадии — alpha/pre-alpha gameplay, Legacy player Rift, experimental simulation, dev-only Studio. **Возможное направление:** явный контракт actor + operation + object scope для каждого adapter; проверка и на backend, и на ingress. Это несколько независимых owner-policy участков, не одна универсальная auth-функция и не один duplicate.

### RC-02 — Граница команды и серверного факта размыта

**Связанные ID:** A04-01 = A07-05; A04-02; контекст A02-02/A03-11. Домены: Rift player commands, Combat return/recovery, Character snapshot.

**Механизм.** Диагностический контроль события/характеристик попадает в player DTO, а восстановление неизвестного outcome создаёт положительный факт. Добавление login не устраняет доверие к `force_event`, client outcome и attributes. Наличие/отсутствие runtime — факт хранения, из которого нельзя выводить победу.

**Evidence:** `src/backend/features/rift/dto/runtime.py:17–23`; `src/backend/features/rift/runtime/actions/dispatcher.py:46–62,199–205`; `src/backend/features/rift/runtime/navigation/screen_builder.py:772–785`. Текущий `src/backend/features/combat/integrations/system_integrator.py:259–267` по-прежнему передаёт `result="victory"` в общий return path. A04-02 локально подтвердил открытие ворот при missing combat с fake stores; здесь проба не повторялась.

**Компенсации:** player service запрещает ручное завершение текущего node combat, Rift сопоставляет active encounter ID и различает defeat/victory. Это ограничивает конкретные ветви; transition harness и unknown outcome остаются другими путями.

**Уверенность:** высокая для статического контракта и результата исходной локальной пробы. Стадия — Legacy player Rift. **Направление:** разделение разрешённых player commands, diagnostic overrides и authoritative server facts; отдельная семантика unknown/missing outcome. A04-02 и A04-01 независимы: один — recovery interpretation, другой — client authority.

### RC-03 — У account, selected character и живого соединения нет единого lifecycle полномочий

**Связанные ID:** A07-08, A07-09, A07-10, A07-11; A07-16 — дополнительный непроверенный lifecycle риск. Домены: Site Auth, Lobby, Inventory, frontend session middleware, Realtime.

**Механизм.** Site JWT, game JWT, cookies, game lock, URL actor и WebSocket имеют разные границы отзыва/выбора. Успешная подпись устанавливает identity, но не обязательно active account, выбранного персонажа и действующую session authority. Logout/disable не транслируется одинаково всем потребителям.

**Evidence:** заново прочитан `src/backend/core/auth.py:16–38,63–68`: site/game tokens допустимы, `is_active=True` конструируется локально; без game claims scope check возвращается. Другие anchors: `src/backend/realtime/api/ws.py:123–169`; `src/frontend/features/auth/routes/pages.py:137–150`; `src/frontend/game_features/session/middleware.py:56–98`; auth lookup/refresh paths из A07-09.

**Компенсации:** JWT signature/audience/expiry, game-session replacement lock, inventory ownership, login/refresh active-account check. Они существенны: A07-11 не доказывает cross-user IDOR, A07-08 не доказывает чужие player notices.

**Уверенность:** высокая для split identity/lifecycle; WebSocket long-lived abuse — риск, реальная browser/domain/revocation конфигурация неизвестна. Shared/alpha поверхности. **Направление:** явные разные типы полномочий и определённая задержка revocation/logout для HTTP, refresh и WS; один проверенный actor источник. Cookies cleanup, account revocation и game-only mutation — самостоятельные части общего контракта.

### RC-04 — Назначение среды не превращается в fail-closed publication policy

**Связанные ID:** A07-14 ↔ A08-01; A07-15 ↔ A08-04; A07-04 ↔ A08-03; A07-12; A08-08. Домены: settings, Nginx, Compose, Rift/Hex, Studio, internal APIs.

**Механизм.** `internal`, `dev`, `read-only` и `DEBUG=False` обозначают намерение, но сами не определяют mount, network bind, secrets validity и HTTP write permissions. Environment defaults позволяют собрать более широкую поверхность, чем подразумевает stage label.

**Evidence:** текущий `src/backend/features/rift/api/router.py:179–190` включает dev и Hex только по flag; `src/backend/config/settings.py:59` default True. `deploy/compose.game.yml:43–54` не доказывает выключение flag при выключенном DEBUG. `deploy/nginx/site.conf.template:120–131,260–271` проксирует общий `/api/`. `src/studio/app.py:137–147` и `src/studio/features/cabinet/modules/content_ops/cabinet.py:321–336,416–423` допускают write controls; local binds — `deploy/docker-compose.yml:9–14,294–295`. A08-01 проверил принятие known defaults без реального `.env`.

**Компенсации:** flag позволяет выключить dev routes; production Compose публикует только Nginx, не host-порты БД/app; source allowlist в Studio; Nginx limits; Hex Redis TTL. TTL не очищает process-global instances, allowlist не делает destination read-only.

**Уверенность:** высокая по versioned configuration; production values/overlays/firewall неизвестны. Dev-only/Experimental отделены от предполагаемого production ingress. **Направление:** environment invariants для security-critical settings, явные publication allowlists и read-only enforcement на operation/source. Secret defaults, dev mount, internal proxy и Studio writes не дедуплицируются между собой.

### RC-05 — Разделение процессов не закреплено минимальными полномочиями runtime principals

**Связанные ID:** A08-02; контекст A08-12/A08-13 и A07-12. Домены: Site/Game/Chat/Workers/Bot, SQL, Redis, Mongo, assets, host deployment.

**Механизм.** Полный env bundle и общая сеть дают нескольким процессам доступ к чужим данным/провайдерам; ограничения principal и post-compromise ресурсов слабее физической границы контейнера. Это увеличивает последствия исходного compromise, но не доказывает сам compromise.

**Evidence:** `deploy/compose.site.yml:39–54,85–99`; `deploy/compose.game.yml:43–54,124–134`; `deploy/compose.tg-bot.yml:8–25`; `deploy/compose.infra.yml:108–111`; `.env.prod.example:41–58`. Дополнительные независимые controls: `.env` creation без закреплённого mode — `deploy-production.yml:72,77–83`; container hardening gaps — A08-13.

**Компенсации:** непривилегированный appuser, отсутствие privileged/host socket/namespace, отдельные site/game SQL metadata и БД, отсутствие production host ports у datastores. Реальные DB/IAM grants, umask и daemon policy неизвестны.

**Уверенность:** высокая по общим env/network, средняя по effective blast radius. Shared infrastructure; A08-12 — host-условный риск. **Направление:** соответствие runtime identity фактическим нуждам, отдельный контроль secret file и ресурсов. Least-privilege grants, file mode и resource limits остаются разными проверяемыми участками.

### RC-06 — Диагностические данные выходят из request/runtime без отдельного контракта чувствительности

**Связанные ID:** A08-05, A08-06, A08-07; A07-16 — только query-token контекст. Домены: frontend tokens, shared metrics/logging, Nginx, email, installed logging library.

**Механизм.** Исходный URL и exception locals рассматриваются как полезный diagnostic context и сохраняются без ограничения на bearer/PII. Разные sinks имеют разные audiences и retention, поэтому закрытие одного канала не закрывает остальные.

**Evidence:** `src/shared/infrastructure/metrics_middleware.py:23–40,45–50` выбирает path до routing; `src/shared/infrastructure/metrics_endpoint.py:12–17` публикует metrics; заново прочитан `deploy/nginx/nginx.conf:20–31` с `$request_uri`. `src/shared/infrastructure/logging_config.py:42–56` делегирует setup; установленный `codex_core/common/loguru_setup.py:287–296` — production sink without diagnose=False. A08 canary подтвердил synthetic locals disclosure в установленной версии, не в production image.

**Компенсации:** TLS, feature flag email, TTL/consume policy email tokens, login для account change, WS query fallback преимущественно diagnostic. Они уменьшают последствия, но JSON escaping не является redaction. Account takeover и реальная утечка не доказаны.

**Уверенность:** высокая для алгоритма/config/canary; deployment library и реальные logs неизвестны. Shared/alpha, часть flows feature-dependent. **Направление:** sensitivity-aware projections, cardinality policy и sink-specific redaction/access. Metrics, Nginx и Loguru — три independent defects, не дубликаты «утечки токенов».

### RC-07 — Identity операции и запись о её применении не охватывают весь бизнес-эффект

**Связанные ID:** A03-01, A03-04, A03-07, A04-05, A04-06, A05-01; риски A04-16/A07-18/A05-15. A05-02 — смежный отдельный source-entitlement defect. Домены: Combat rewards/create, Rift entry/travel/complete, Inventory durability, Loot, Chat append.

**Механизм.** Stable event ID/lock либо completed marker иногда есть, но они не атомарны с authoritative effect или отсутствуют в одной ветви. Повтор после полного завершения и повтор после частичного commit — разные случаи. В создании runtime тот же request может повторно создать UUID или destructive reset; повтор start не проверяет допустимость state transition.

**Evidence:** текущий `victory_finalizer_task.py:69–108` вызывает additive XP без общего operation ledger; `infrastructure/combat/managers/session.py:81–108` пересоздаёт keys. `inventory/services/inventory_service.py:197–235` — SQL durability commit до marker. Заново прочитан `loot/workers/tasks/loot_claim_task.py:203–269`: processed check только unsafe, safe wallet получает payload delta. `rift/services/entry_service.py:86`, navigation `screen_builder.py:134–347`; `rift/services/player_service.py:192` — heart reward risk.

**Компенсации:** unsafe processed events, SQL wallet locks, unique item placement, stable durability key, active encounter guard, sequential completed no-op. Row lock сериализует два неправильных начисления; unique item row не обеспечивает точный источник.

**Уверенность:** высокая для additive/reset/commit-marker путей; concurrent heart/Chat replay — не воспроизведённые риски. Alpha/pre-alpha и Legacy player Rift. **Направление:** effect identity у authoritative owner, conditional source/state transitions и понятный interrupted-retry contract. Combat XP, safe resources, durability и Rift entry не становятся одной task: разный authoritative state и разные regression criteria. A05-02 должен сохранить собственный exact holder/rowcount инвариант даже после dedup.

### RC-08 — Lease, dirty marker и snapshot version не образуют атомарный договор записи

**Связанные ID:** A03-03, A03-09, A03-10, A03-11; A04-15/A04-17; A05-03/A05-09/A05-12; A05-14/A05-15 — риски других single-store boundaries. Домены: Combat, Character, Inventory, Rift, Site refresh, SQL active Expedition.

**Механизм.** Read/check/write разбиты; whole-document replacement не проверяет captured revision, clean acknowledgement не связан атомарно с той версией, а lease ownership проверен отдельно от commit. Серверный pipeline объединяет транспорт, но не делает связанный exchange единым transition. У SQL refresh два commits разрывают одну rotation.

**Evidence:** заново прочитаны `src/backend/infrastructure/combat/managers/session.py:594–650` (`transaction=False`, actors/logs/trim/meta отдельно); `src/backend/infrastructure/actor_state/managers/session.py:119–171` (generation read, затем patch); `src/backend/features/rift/integrations/runtime.py:287–298` (flush, затем clear). Inventory full SET/flush — `inventory_service.py:84–112,168–179`; Site refresh — `auth_persistence.py:67–74`. Executor read-before-lock — `executor_task.py:59–71,120–127`.

**Компенсации:** owner-aware lease release, generation precheck, Lua intent/exchange registration, SQL row locks/unique constraints в отдельных путях, Rift restore lock. Они полезны, но не защищают epoch при commit и не блокируют новую mutation между compare и clear. MULTI также не обещает rollback всех RedisJSON runtime errors.

**Уверенность:** высокая в отсутствии атомарного контракта; конкретное concurrent corruption у A03-09/10/11 и A05-14/15 — гипотеза/обоснованный риск. Shared runtime, Legacy player Rift и Site Auth отдельно. **Направление:** version-aware owner mutations и acknowledged revision; выбор serial execution, CAS/fencing или SQL transaction зависит от конкретного агрегата. Один механизм reasoning, несколько независимых implementations. Без устранения RC-07 безопасный retry этого механизма не гарантирован.

### RC-09 — Статус принятия/завершения расходится с восстанавливаемыми данными и последствиями

**Связанные ID:** A03-02/A03-12, A04-03/A04-04/A04-10/A04-11/A04-12/A04-13, A05-04/A05-06/A05-07/A05-10; контекст A08-15. Домены: Combat archive/finalization, Rift membership/snapshot/restore, World projection, GenerationAI, Chat archive, Expedition corpse.

**Механизм.** Active/done/cursor/membership или доступная projection подтверждает больше, чем уже сохранено и может быть восстановлено. Error path подавляет исключение либо recovery считает наличие одного компонента достаточным. Redis до flush содержит последнюю принятую state, поэтому слово cache скрывает реальную durability boundary. Retry budget также раздвоен между claim и service, оставляя нетерминальный, но недоступный cooldown.

**Evidence:** текущий finalizer `victory_finalizer_task.py:71,110–134` закрывает бой до завершения и подавляет exception. `generation_ai/repositories.py:221–259,261–270` принимает missing payload/ошибку; `services.py:216` и repository claim `:104–121` — разные retry limits. Текущий Rift restore `runtime.py:245–265` считает instance достаточным и SET-ает все sessions; initial-save path — `entry_service.py:54`, runtime `:55,148`. Текущий Chat cursor `archive.py:44–59` проходит ошибочную запись. Corpse publish до commit — `expedition/service.py:238–268`.

**Компенсации:** SQL source-of-truth guidance, Mongo pointers/status/schema versions, restore lock, Redis finalization cache, processed death marker, SQL archive identity, World validation. Они показывают частичную recovery infrastructure. Сам marker/status не содержит lost input/body; presence rebuild по stale sessions не восстанавливает новую версию.

**Уверенность:** высокая по reachable windows; crash/TTL на real stores не исполнялись. Stage — shared lifecycle и Legacy player Rift; backups/RPO/RTO неизвестны. **Направление:** явно определить acceptance checkpoint, pending obligations и component-wise recovery; прочитать архив через текущий owner contract; сохранить unknown outcome. Early finalizer close, chat cursor, initial Rift snapshot и GenerationAI input имеют разные минимальные исправления: это общая семейная причина, не dedup.

### RC-10 — Commit эффекта и доставка следующего шага не связаны долговечным обязательством

**Связанные ID:** A03-05/A03-06/A03-12, A04-18 (enqueue часть), A05-05/A05-08. Домены: core Streams/ARQ, Combat support/loot/freeze, GenerationAI scheduling.

**Механизм.** После commit следующий payload/список pending существует в памяти, job/event enqueue не завершает durable handoff, freeze не знает ожидаемые seq. На consumer стороне ошибка оставляет PEL, но loop читает новые сообщения; retention не учитывает незавершённую обработку. Это два разных места потери работы: отсутствие durable producer obligation и отсутствие transport redelivery.

**Evidence:** `combat/workers/tasks/executor_task.py:127–175`; `combat/runtime/analytics/finalization_builder.py:25–30`; `loot/events/__init__.py:52–59` и post-combat router `:257–283`. Текущий `generation_ai/services.py:168–175` очищает in-memory list до enqueue, worker `tasks.py:32–34` коммитит раньше. `src/backend/core/containers/redis.py:136–164` включает installed StreamRuntime; A05-05 прочитал `codex_platform/streams/processor.py:180–222`, `consumer.py:90–94` (`>` без reclaim). Версия production не установлена.

**Компенсации:** Redis Streams PEL, request/reply correlation и TTL, ARQ queues, SQL task identity/claim, отдельные workers. PEL сохраняет transport state, но сам не выполняет replay; успешный enqueue не обеспечивает analytics barrier; ordinary ARQ exception не равен бесконечному retry.

**Уверенность:** высокая по producer windows и локально установленному consume loop, средняя по end-to-end effects. Shared infrastructure/alpha, Legacy player Rift consumers. **Направление:** durable handoff/reconciliation и контролируемая delivery lifecycle с retention/retry budget; effect dedup до включения replay. Library reclaim должен оставаться отдельной owner task от Combat facts и SQL→ARQ handoff. Зависимость RC-07 → безопасный RC-10 retry принципиальна.

### RC-11 — Semantic feature ownership заменяется внутренним storage/wiring контрактом

**Связанные ID:** A02-01–09; поведенческие проявления A03-01/10/11, A05-01/02/04, A09-06/07 — связаны, но не дубликаты. Домены: Expedition, Character, Inventory, Loot, GameSession, Combat, Rift, shared/core.

**Механизм.** Consumer знает чужие ORM tuples, constructor graph, RedisJSON paths, worker names и transport response details. Gameplay policy частично живёт в storage/core, runtime DTO выглядит cross-side contract. Из-за этого locus ownership не совпадает с местом изменения инварианта; feature rename/factory/storage change затрагивает несколько соседей.

**Evidence:** `expedition/service.py:372–465`; `loot/workers/tasks/loot_claim_task.py:214–269`; `rift/dependencies.py:137`; finalizer `:191–205,294–313`; `character/integrations/character_state_integrator.py:244–254`; `game_session/integrations/session_integrator.py:263–303`; `combat/events/__init__.py:37–57`; `src/shared/schemas/inventory.py:86–101`; `ai_simulation_service.py:54–2108` и live private helper import `ai_turn_task.py:10`.

**Компенсации:** domain-grouped infrastructure, semantic integrations в ряде features, отдельный resolver без I/O, shared DTO, общий executor для live/simulation, полезная общая SQL transaction Expedition transfer. Последнюю нельзя разрушать ради формального межfeature event split.

**Уверенность:** высокая по static coupling; причинная связь с конкретной аварией — интерпретация, не доказательство. Shared backend, Legacy player Rift / experimental AI отдельно. **Направление:** semantic owner contracts и локальная factory/wiring responsibility при сохранении transaction scope. God-object cohesion, DTO location, raw paths и transport leakage имеют разные обязанности и не считаются одним defect с одним move-files решением.

### RC-12 — Проверки свидетельствуют о вызове компонента сильнее, чем об инварианте реальной границы

**Связанные ID:** A06-02/A06-03/A06-04/A06-07; A06-11 — taxonomy контекст; известные failures A03/A04/A05. Домены: game lifecycle, SQL/RedisJSON/Mongo/Streams, HTTP frontend/backend, Combat trigger setup.

**Механизм.** Happy path, mocks и независимые reply fixtures обходят источник риска: server wire/constraints, второй вызов, partial failure, actual producer→consumer contract. Negative assertion без positive-control precondition проходит, даже когда проверяемый trigger не активирован. Это не означает бесполезность unit tests.

**Evidence:** `tests/backend/conftest.py:10–128,146–169`; `tests/backend/infrastructure/mongo/test_bootstrap.py:11–39`; bus `test_producer.py:1–60`; frontend `test_game_settings_module.py:18–20,257–401`; backend `test_internal_routers.py:105–164`. A06-02 локально исполнил `test_runtime_processors.py:5556–5571`: штатная RNG заглушка отключает trigger, успешные условия выявляют A03-13. Lifecycle samples A06-04 не проверяют repeated reward/fault/recovery.

**Компенсации:** большое покрытие чистых calculations/DTO, stateful fakes, TestClient/MockTransport, validators, общий live/simulation executor. Они дают быстрые узкие доказательства. Не найденная real-store suite ограничена текущим checkout; внешняя suite неизвестна. Отложенный browser E2E соответствует текущей стратегии и не новый High defect.

**Уверенность:** высокая по inspected suite и A06 controlled probe; полная инфраструктурная correctness не измерена. Shared QA всех стадий. **Направление:** представительная защита опасных adapter contracts, controlled sequence/fault cases и reached-precondition controls. A06-02 нельзя закрыть одним real-DB suite; A06-03 нельзя закрыть добавлением только mock tests. Synthetic timing и fake calls никогда не считать server capacity.

### RC-13 — Автоматический gate проверяет ограниченную проекцию политики

**Связанные ID:** A06-01/A06-06/A06-08/A06-09/A06-10/A06-11/A06-12; partial overlap A08-11. Домены: pytest collection, architecture scan, develop/main CI, security hook, deployment promotion.

**Механизм.** Наличие hook/threshold/stage не равнозначно правильным event/ref, input set, semantic invariant и artifact association. Название unit скрывает весь corpus; literal prefix scan не покрывает новый key space; dependency audit hook видит своё environment. Сломанный импорт останавливает gate, а develop вообще не запускает behavioral stage.

**Evidence:** текущие `.github/workflows/ci.yml:3–10,19–66` и `pyproject.toml:200–205` подтверждены чтением. `tests/backend/features/generation_ai/test_asset_backfill.py:6` всё ещё импортирует отсутствующий script; здесь collection не повторялась. `tests/backend/features/test_infrastructure_boundaries.py:62–77` — ограниченный scan/Rift skip. `.pre-commit-config.yaml:39–61`; `deploy-production.yml:16–20,29–44,91–110`. A06-10 — threshold 74 без branch/patch gate, **не нарушение текущей политики**.

**Компенсации:** main/release full runner включает tests/security/extra checks; release build зависит от quality, coverage threshold исполняется; CI contents:read и pinned setup-uv. GitHub required statuses/approvals неизвестны. Broken gate fail-closed, не доказанный обход; deployed image_ref не проверен workflow provenance, но оператор уже имеет deploy права.

**Уверенность:** высокая по configuration и исторической collection; medium по effective promotion governance. Shared QA/CI/release. **Направление:** проверяемая связь policy → event/ref → inputs → checked artifact. Collection repair, behavioral trigger, architecture enforcement и package audit scope независимы; не требуют автоматически новой patch-% политики.

### RC-14 — Проверка и сборка не получают один воспроизводимый источник зависимостей/artifact

**Связанные ID:** A06-05 ↔ A08-10; A08-09; A06-09/A08-11 — promotion dependency. Домены: uv, installed codex libraries, Docker, Actions, GHCR/deploy.

**Механизм.** Готовая локальная venv скрывает внешний sibling source; workflow получает один checkout, а Docker выключает source overrides. Mutable references дальше не устанавливают неизменяемое соответствие проверенного исходника shipped bytes. Clean install problem и provenance problem разные, но последняя проверка невозможна без первой ясной source policy.

**Evidence:** заново прочитан `pyproject.toml:28,34–35,50`, CI checkout/sync `ci.yml:24–35,48–59`; `uv.lock:470–471`; backend/frontend/chat/worker Dockerfiles `:9–13` с `--no-sources`; `tools/dev/check.py:8–20` machine-specific runner fallback. Mutable privileged Actions/image refs — `deploy-production.yml:34,53,65`, `build-images.yml:59–77`; digest association не заявлен.

**Компенсации:** lockfile, version/SHA image tags, setup-uv commit SHA, nonzero quality blocks build; locally inspected codex-core runner. SHA **tag** не доказывает неизменяемый image digest, installed dependency не доказывает production bytes. Реальный registry resolution и hosted install не выполнялись; dependency confusion/подмена не доказаны.

**Уверенность:** высокая по missing-source contract, средняя по фактическому resolution/artifact divergence. Shared dev/CI/build, production state unknown. **Направление:** явный доступный pinned source и проверяемая цепочка source→wheel/image→quality→promotion. Missing-path slice A06-05/A08-10 совпадает, но полные ID остаются отдельными: Docker policy difference расширяет A08-10. A08-09 также требует собственной проверки.

### RC-15 — Горячая операция работает с полным агрегатом при малом изменении

**Связанные ID:** A09-01/A09-05/A09-06/A09-07/A09-08. Домены: Combat history/actors/AI, Character sync, Rift tick/snapshot, Mongo chat.

**Механизм.** Storage/view representation используется как единица горячего чтения/записи: новая запись журнала перечитывает всю history, один AI строит весь BattleContext, персональный travel сериализует instance, duplicate clean sync становится full save, append bucket возвращает весь растущий массив. Pipelines уменьшают RTT, но не bytes/validation/server commands.

**Evidence:** текущий Combat manager `session.py:606,629,807–832` подтверждает full history merge/HSET; `session_integration.py:339–390,416–440`; `character/integrations/system_integrator.py:55–83,117–120`; `rift/services/player_service.py:218–228`; `rift/managers/instance.py:25–28`; текущий Mongo `chat_buckets.py:59–83` возвращает AFTER без projection и использует только count.

**Компенсации:** bounded queue, cached actor stats, pipelines, small Rift presets 4×4…7×7, chat bucket nominal cap 1000, SQL batched inventory reads, isolated simulation queue. Поэтому ограничения отличаются по масштабу; small Rift не становится High на основании Combat history.

**Уверенность:** высокая в O(history), O(B×N) и bounded bucket amplification; A09 fake method probes подтверждают операции/байты на fixture, не production latency. Shared runtime; player Rift Legacy. **Направление:** единица чтения/записи соответствует изменению и требуемому invariant; delta/projection/coalescing возможны только при сохранении RC-07/08/09. Оптимизация log append, Mongo return projection и clean-sync semantics — разные изменения, не общий rewrite.

### RC-16 — Ограничен результат/число jobs, но не весь объём работы и накопления

**Связанные ID:** A09-02/A09-03/A09-04/A09-07/A09-09/A09-10/A09-11; A08-04/A08-13 и A08-05 cardinality — смежные проявления других boundaries. Домены: AC sweeper, chat archive/fanout/browser, Rift flush, GenerationAI SQL/CPU, Hex.

**Механизм.** `limit=100` ограничивает найденных кандидатов, не просмотренные keys; один batch/cron не гарантирует arrival rate ниже drain rate; sequential receiver связывает workflow с slow sink; in-memory history/instances не имеют retention; max_jobs не задаёт CPU/connection budget. Async coroutine может выполнять sync CPU или держать SQL transaction во время provider I/O.

**Evidence:** `actor_state/managers/session.py:520–545`; `chat/workers/archive.py:20–59,218–223` — 500/topic раз в 10 минут; `chat/services/connection_manager.py:19–23,76–88`; `rift/managers/session.py:146–162`; `generation_ai/repositories.py:132–157`, service `:81–105`, worker `tasks.py:20–35`; `generation_ai/integrations/image_normalization.py:42–58`; `frontend/templates/shared/chat/main.html:176–200,921–1035`.

**Компенсации:** отдельные worker queues/processes, bounded archive pages/buckets, Nginx limits, ARQ max_jobs/timeouts, small maps, chat history HTTP page limit. Timeout требует возврата event loop; Redis instance TTL не удаляет local dict; browser live history не ограничивается backend history page.

**Уверенность:** высокая в algorithm/config boundaries; fairness starvation, exhaustion, pool/vacuum latency и browser memory/DOM величины требуют measurements. Номинальный chat cap 500/600 ≈ 0,833 сообщения/с/topic — арифметика расписания, не benchmark БД. **Направление:** explicit examined-work/drain/retention/slow-consumer/connection/CPU budgets и доменные метрики. Это самостоятельные владельцы и проверки; отсутствующий global CCU не превращается в дефект Python или требование разнести все containers.

### RC-17 — Stage и contract evolution не отражаются одинаково во всех источниках знания

**Связанные ID:** A02-10, A04-14, A06-01; наблюдения A01 §§9–10. A05-11/A05-13 — независимые runtime/schema compatibility свидетельства, не доказанное следствие документации.

**Механизм.** Stage reference, physical anchor, helper/test import и действующий code shape расходятся. Stable docs presence не означает готовую спецификацию; generated graph хранит прошлое дерево. В persistence особенно важно различать текущую ORM-модель, историческую migration и reader contract, но сами ошибки этих contracts нельзя списать на stale prose.

**Evidence:** `.agents/skills/turnbasedmmorpg-rift/references/implementation-boundaries.md:1–20` описывает initial harness/no DB, текущие `rift/api/router.py:31–97` и `infrastructure/rift/models.py:12` уже существуют. A01 установил 67 docs-заглушек и 815 missing Graphify source paths; граф не пересобирался. `tools/world_static_audit.py:230` stale constructor; `test_asset_backfill.py:6` stale script. Текущий `result_archive_service.py:147–153` читает отсутствующее `row.finalization`, тогда как model `finalization.py:12–36` содержит Mongo pointer. Текущий site baseline `0001_site_schema_baseline.py:13–24` использует live create_all; `0002_security_baseline.py:23–29` затем добавляет уже имеющийся token_hash.

**Компенсации:** AGENTS skill navigation, source-first rule, docs/planning vs docs/ru distinction, audit IDs/explicit evidence, MkDocs build и tests. Link check не обнаруживает semantic stale stage; наличие кода не доказывает утверждённое решение владельца о Rift stage.

**Уверенность:** высокая в расхождении; средняя/низкая в общей исторической причине возникновения и unknown authorization history. Pre-alpha planning, Legacy player Rift, legacy/offline helpers и shared maintenance отдельно. **Направление:** проверяемая актуализация owner-approved stage и consumers при evolution, immutable historical migrations, архивная navigation по текущему payload contract. Исправление skills, archive reader и migration baseline имеют разные владельцев и не дедуплицируются в «обновить документацию».

## 4. Реестр пересечений, дубликатов и зависимостей

**Duplicate** означает одну непосредственную причину, одно совместимое исправление и проверку. **Overlap** — общий участок/механизм, но не полностью совпадающий объём. **Dependency** — один invariant нужен для безопасной работы другого. Во всех случаях сохраняются исходные ID и исходные оценки.

| ID/группа | Связь | Что сохраняется отдельно |
| --- | --- | --- |
| A04-01 ↔ A07-05 | Duplicate: player commands несут diagnostic/server-authority поля | Security классификация A07 и gameplay evidence A04; не объединять с A07-01 auth |
| A04-12 ↔ A05-07 | Duplicate initial GenerationAI Mongo input acceptance | Исходные High/Medium расходятся: разные последствия/охват; не пересчитывать автоматически в два дефекта |
| A04-17 ↔ A05-09 | Duplicate captured snapshot → unconditional dirty clear | A05 усиливает evidence до failure window; оба ID сохраняются, не новое real-store воспроизведение |
| A03-11 ↔ A04-15 | Overlap: non-atomic Rift completion guard/writes | A04-15 concurrency и A03-11 partial consequence/presence; риск не повышается до инцидента |
| A04-02 ↔ A03-11/A02-02 | Связанное новое evidence, не duplicate всей группы | Synthetic victory доказана отдельной локальной пробой; race и constructor coupling имеют другие invariants |
| A04-18 ↔ A05-08 | Частичное пересечение: совпадает commit→enqueue gap | Orphan asset/Mongo before rollback часть A04-18 остаётся отдельным риском компенсации |
| A07-04 ↔ A08-03 | Частичное пересечение: совпадает internal-session exposure участок | Analytics read/backfill/raw-debug и bounded scans шире общего auth/proxy slice |
| A07-14 ↔ A08-01 | Duplicate known-default keys acceptance; A08 усиливает static config evidence | Production misconfiguration остаётся неизвестной; startup validation не устраняет missing auth A07-02/03 |
| A07-15 ↔ A08-04 | Overlap default-on dev exposure | A08 добавляет independent unbounded process-global Hex retention/CPU; одного flag недостаточно для allowed dev workload |
| A06-05 ↔ A08-10 | Partial overlap: missing CI sibling source slice совпадает; полные ID не объединяются | Docker no-sources parity/provenance — дополнительная неопределённость A08 |
| A06-09 ↔ A08-11/A08-09 | Overlap promotion provenance | Unknown external approvals/ref permissions, concurrency и mutable Actions имеют самостоятельные controls |
| A07-18 ↔ A03-01/A04-16/A05-01/02 | Повторная security-risk ссылка, не новый подтверждённый exploit | A05-02 exact SQL source независим от reward ledger; A04-16 concurrency/fault остаётся risk |
| A03-10 ↔ A05-03/A05-09 | Одна systemic revision family, **не duplicate** | Character, Inventory и Rift реализуют разные mutation/flush paths; три owner contracts |
| A03-02 ↔ A03-01 | Dependency: recovery retry требует effect idempotency | Early close и duplicate XP — два дефекта; journal/retry alone может увеличить ущерб |
| A05-05 ↔ A03/A05 rewards | Dependency: redelivery требует business dedup | Transport reclaim не исправляет XP/resource/durability; reward ledger не возвращает pending messages |
| A03-03/09 ↔ A09-01/05 | Shared commit surface, независимые correctness/performance | Delta serialization не доказывает atomic commit/fencing; atomic commit не устраняет full history amplification |
| A05-06 ↔ A09-03 | Независимые Chat archive defects | Cursor error path и fixed drain cap различны: исправление одного не гарантирует ни другого |
| A05-15 ↔ A09-08 | Shared Mongo append, независимые вопросы | Real-server validity/seq/dedup — risk; AFTER full-bucket amplification — static performance факт |
| A05-11 ↔ A03-12 | Независимые archive read/write defects | Reader обращается к отсутствующему полю даже после успешного persist; freeze/TTL проблемы относятся к записи |
| A03-13 ↔ A06-02 | Runtime defect + слабый regression control | Contact semantics и vacuous test — разные изменения; test evidence не заменяет engine fix |
| A07-12 ↔ A08-08/A08-02 | Overlap development/live-source trust boundary | Studio app writes/auth, host bind и shared credentials — независимые условия/controls |
| A08-05 ↔ A08-06 ↔ A08-07 | Общая sensitivity family, **не duplicate** | Public metrics, access logs и exception locals — разные audiences и sinks |

Отчёты содержат исторические заявления об отсутствии соседних аудитов: A08 говорит, что A07 ещё отсутствовал; A09 — что 06–08 не найдены. Сейчас все 01–09 существуют. Эти фразы описывают момент исходной работы и не используются как ограничение текущей дедупликации.

## 5. Независимые локальные дефекты и неподтверждённые архитектурные требования

Не каждый дефект имеет доказанную общую первопричину. Следующие случаи сохраняют собственный leaf invariant и не поглощаются системным названием:

| ID | Непосредственный механизм / граница вывода |
| --- | --- |
| A03-08 | Policy setup вне simulation failure handler; связан с lifecycle RC-09, но не duplicate большого simulation cohesion A02-09 |
| A03-13 | Crit contact-effect conditions сохраняют accuracy/crit после parry/dodge; это engine семантика, не Redis/retry/auth defect |
| A04-07 | Seeded RNG выбирает из hash-order set; cross-process determinism не следует из наличия seed |
| A04-08 | DI integration не сохраняет redis attribute, cap отключён в обычной сборке; требуются wiring доказательства, а не новый permission layer |
| A04-09 | Gateway игнорирует False результата move; transition success должен соответствовать фактической позиции |
| A04-10 | Incremental/полная публикация World не удаляет stale keys и не обновляется всеми writers; GC, cache invalidation и publish-before-SQL-commit — разные участки |
| A04-11 | Два retry-limit владельца дают unclaimable cooldown; нельзя дедуплицировать с missing enqueue A05-08 |
| A05-02 | Точный SQL holder и rowcount отсутствуют; даже единственное применение stale claim может быть неверным |
| A05-11 | Archive reader не использует текущий Mongo payload contract; данные могут существовать, а screen fallback возвращает None |
| A05-12 | Refresh delete/create разделены двумя SQL commits; single-store transactional rotation, не cross-store outbox |
| A05-13 | Historical baseline зависит от live ORM; clean migration conflict установлен статически, реальный upgrade не исполнялся |

A04-19 относится к неподключённому внешнему World generator; A04-20 — dev Hex/старому next_floor при текущем single-floor heart layout; A04-21 требует решения о персональном fog-of-war. Они не получают invented production blocker. A07-17 не подтверждает XSS без доступного untrusted source. A08-14 требует effective proxy trust/email feature проверки. A08-15 описывает отсутствие operational evidence, а не доказанное отсутствие backups/alerts. Наличие observation не разрешает автоматически изменить game-design или infrastructure policy.

## 6. Что это сопоставление позволяет и чего ещё не устанавливает

Выводы позволяют обсуждать stabilization directions по инвариантам: обязательное полномочие, server authority, одно применение эффекта, version-safe state mutation, recoverable acceptance/delivery, evidence настоящей границы, воспроизводимая build chain и bounded work. Они не задают согласованный implementation plan. Перед выбором объёма остаётся установить конкретные approved stages, реальную публикацию API/dev поверхностей, зависимости installed runtime от shipped image и operational protections.

A06 дал завершённую выборку 362 passed с exit 1 из-за 38,39% глобального coverage; это **не текущий общий coverage**. Его широкий 1707 PASSED run был незавершён. Async sandbox socketpair limitation не переносится в verdict Combat deadlock. A09 timings/counts/bytes получены на synthetic fixtures и fake I/O; CCU, RPS, p95/p99, стоимость сетевых Redis/SQL/Mongo операций, browser RAM и server capacity остаются неизвестны. В этом сопоставлении новые tests, benchmarks, сервисы и production probes не запускались.

Создан только `audit/10_root_causes.md`. Исходные аудиты, код, tests, CI, skills, dependencies, данные и Git не изменялись.
