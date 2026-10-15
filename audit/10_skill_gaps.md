# Аудит 10/10 — пробелы знаний, рабочих процедур и автоматических проверок

Дата: 09.10.2026. Объект — действующее рабочее дерево TurnBasedMMORPG и отчёты 01–09. Создан только этот отчёт. Код, тесты, CI, конфигурации, исходные аудиты и skills не изменялись; зависимости не устанавливались; реальные хранилища, внешние AI и production не подключались. Ссылки относительны этому файлу; номер в подписи обозначает строку проверенного источника.

## 1. Основной результат и границы

Нужны преимущественно уточнения существующих domain references и проверки устойчивых контрактов. Девять новых навыков по числу аудитов не обоснованы. Уже существующий audit-remediation соответствует разбору серии: он отделяет историческое свидетельство от текущего дефекта, требует четыре независимые оси классификации и различает Knowledge, Workflow и Enforcement. Сам отчёт не является планом внедрения и не разрешает исправления.

Стадия по текущему поручению — **pre-alpha**. Hex Rift — **experimental prototype**, старый Rift рассматривается отдельно как **legacy**. Названия «Production», «Alpha» и «используется» в старых аудитах, Compose и release guidance не подтверждают фактическую доступность игрокам или зрелость этих поверхностей. Настройка публичной надписи `alpha` — отдельный UI/release-контракт. Это ограничение существенно для urgency, а не отмена технических инвариантов ownership, conservation и корректного повторного применения.

**Статически перепроверены** существующие правила, конкретные противоречия guidance, владельцы API/Redis, состав fixture validator и CI predicates. **Исторические доказательства** игровых отказов и локальных прогонов сохраняются с исходными audit ID; здесь они не объявляются повторно воспроизведёнными. Для A04-07 статически перепроверена конкретная предпосылка: `_select_branch_source` строит candidates обходом `set[str]` и вызывает `rng.choice` без сортировки — [zone instance:848](../src/backend/features/rift/runtime/generation/zone_instance.py). Порядок строкового set может зависеть от `PYTHONHASHSEED` даже без явного вызова `hash()`. Историческая cross-process проба A04 здесь не повторялась. Наличие файлов и тестов не означает их успешного выполнения.

Различаем:

- **Knowledge** — устойчивое правило, модель состояния или утверждённая граница, которую агенту нужно знать.
- **Workflow** — повторяемая процедура проверки или принятия решения при изменении этого контракта.
- **Enforcement** — тест, validator или CI gate, который обнаруживает нарушение независимо от прочтения навыка.

Основы этого разделения уже есть в [skill-improvement:3](../.agents/skills/turnbasedmmorpg-audit-remediation/references/skill-improvement.md). «Не хватает проверки» не равно «агент не знает правило».

## 2. Что уже полезно и должно сохраниться

| Решение / правило | Основание | Практический смысл |
| --- | --- | --- |
| Site владеет пользователями и site DB; backend — игрой и chat; связь через HTTP/contracts | [backend architecture:21](../.agents/skills/turnbasedmmorpg-backend/references/feature-architecture.md), [deployment contract:75](../docs/ru/management/deployment-contract.md), [frontend API:12](../src/frontend/core/api.py) | Не превращать frontend в пассивный JS-клиент и не переносить site identity в game DB по названию папки |
| Feature integrations и managers с явным key-space ownership | [project rules:18](../.agents/skills/turnbasedmmorpg-project/references/project-rules.md), [backend architecture:30](../.agents/skills/turnbasedmmorpg-backend/references/feature-architecture.md) | Правило уже есть; A02-03/06/07 не требуют повторить его новыми общими словами |
| Вычислительный Combat resolver имеет facade; simulation использует тот же executor | [resolver:25](../src/backend/features/combat/runtime/engine/resolver/__init__.py), [A03 strong decisions:375](03_combat_runtime.md) | Сохранять общий вычислительный контракт; native rewrite и отдельный combat microservice не следуют из размера кода |
| SQL unit of work, локальные dedup/lock механизмы, стабильные document identity и schema_version | [A05 strong decisions:410](05_persistence_consistency.md) | Эти гарантии локальны; не расширять их до exactly-once или распределённого ACID |
| Meaningful tests, риск-пропорциональные проверки, честный отчёт об исполнении | [testing:3](../.agents/skills/turnbasedmmorpg-quality/references/testing.md), [validation:3](../.agents/skills/turnbasedmmorpg-quality/references/validation.md), [A06 strong decisions:512](06_testing_quality.md) | Не вводить задним числом обязательные 100% patch coverage, Docker для pure math и тесты тривиального forwarding |
| Криптографическая game identity, проверенные owner/admin/CSRF/Origin границы | [A07 positive boundaries:320](07_application_security.md) | Пробел на другом route не делает эти механизмы отсутствующими; нужно проверять подключение к каждой поверхности |
| Раздельные worker queues, слойный deployment, non-root images, quality перед image build | [worker queues:67](../src/backend/features/combat/workers/arq.py), [CI:68](../.github/workflows/ci.yml), [A08 strong decisions:385](08_infrastructure_security.md), [A09 summary:19](09_performance_scalability.md) | Сохранить разделение нагрузок; не создавать контейнер для каждого feature ради формальной изоляции |

Историческая мотивация SQL/Mongo split документирована в [storage ownership:8](../.agents/skills/turnbasedmmorpg-backend/references/storage-ownership.md) и [document patterns:65](../.agents/skills/turnbasedmmorpg-backend/references/document-patterns.md). Мотивы всех остальных решений нельзя восстановить по одному наличию кода. `docs/game-design` хранит design intent, а planning — будущую/текущую работу: [game-design:7](../docs/game-design/README.md), [planning:3](../docs/planning/README.md). Отдельный реестр ADR в прочитанном корпусе не обнаружен; это ограничение поиска, а не доказательство отсутствия любых owner decisions.

## 3. Knowledge — отсутствующие или противоречивые сведения

### SG10-K1 — стадия Rift и навигационные anchors отстают от корпуса

**Подтверждено статически; guidance defect, техническая severity Low; legacy/experimental; актуализация при стабилизации guidance.** Правило approved stages outrank exploratory notes уже есть в [Rift skill:8](../.agents/skills/turnbasedmmorpg-rift/SKILL.md). Однако [implementation-boundaries:3](../.agents/skills/turnbasedmmorpg-rift/references/implementation-boundaries.md) объявляет первым/текущим этапом local harness, запрещает DB/models и ссылается в code span на отсутствующий `docs/planning/tasks/rift/approved_stages/phase_01_local_dev_harness.md`. В текущем коде есть игровые/dev routers, модели и snapshots: [Rift router:27](../src/backend/features/rift/api/router.py), [runtime snapshot:182](../src/backend/features/rift/integrations/runtime.py). Старый planning baseline сам называет себя dev prototype: [baseline:3](../docs/planning/tasks/rift/00_core_current_state.md). Combat guidance также ссылается на прежний `resolver.py`: [snapshots:8](../.agents/skills/turnbasedmmorpg-combat/references/snapshots.md); текущий facade — пакет.

Связи: A01 §10; A02-10; A04 §3. **Потенциальное направление:** короткая карта legacy Rift / Hex prototype / proposed world contracts с датой и источником owner decision; физические anchors отделить от утверждённого scope. Существование persistence не доказывает авторизацию исторического этапа и не отменяет ограничения пользователя. Workflow — повторная проверка source/stage при изменениях; Enforcement — link/path check, включая code spans. Новый Rift skill не требуется.

### SG10-K2 — frontend DB и shared cross-cutting policy сформулированы неоднозначно

**Подтверждено статически; guidance defect Low; pre-alpha/shared infrastructure; при стабилизации границ.** [Frontend architecture:29](../.agents/skills/turnbasedmmorpg-frontend/references/feature-architecture.md) запрещает frontend доступ к databases, а следующая строка поручает ему site-owned repositories и Alembic. [Project rules:58](../.agents/skills/turnbasedmmorpg-project/references/project-rules.md) ограничивает shared моделями/enums, хотя shared содержит security/logging/metrics, используемые обеими сторонами. A01 §10 и O02-02 отделяют полезные cross-cutting utilities от misplaced runtime DTO (A02-08).

**Потенциальное направление:** уточнить site DB ownership и запрет прямого game DB access; явно решить допустимость небольших cross-cutting utilities, сохранив запрет backend-internal DTO и domain orchestration в shared. Enforcement — направленные imports/DTO consumer checks с адресными исключениями. Автоматическое удаление shared helpers и единый запрет любых DB в frontend не обоснованы.

### SG10-K3 — authority/checkpoint/rebuild модель неполна для активного runtime

**Подтверждено расхождение документов и кода; guidance defect Low; pre-alpha runtime, legacy Rift; при стабилизации persistence.** [Storage ownership:8](../.agents/skills/turnbasedmmorpg-backend/references/storage-ownership.md) объявляет PostgreSQL source of truth и запрещает Mongo authority для progression/result/membership; [project rules:77](../.agents/skills/turnbasedmmorpg-project/references/project-rules.md) определяет live AC Redis. Реальный Rift integration прямо говорит «runtime is stored in Redis» и сохраняет Mongo backup: [runtime:68](../src/backend/features/rift/integrations/runtime.py), [snapshot:199](../src/backend/features/rift/integrations/runtime.py). A05 §3/7 описывает unsynced AC, SQL checkpoints, Mongo документы и Redis-derived caches отдельно.

**Потенциальное направление:** доменная таблица live authority / durable checkpoint / projection / restore source / accepted loss window; последствия TTL и dirty generations. Это уточнение гарантий, а не предложение объявить Redis общей durable истиной. Workflow — проверять crash между mutation, dirty marking, flush и clear; Enforcement — domain restore/version tests. Не требуется новый универсальный storage skill.

### SG10-K4 — граница Studio selected source и local compute недоговорена

**Подтверждено статически; guidance defect Low, возможные последствия защищены отдельной A07-12; dev-only; до следующей работы со Studio sources.** [Studio entrypoint:8](../.agents/skills/turnbasedmmorpg-studio/SKILL.md) запрещает запись в любой selected source, включая local. [Ownership reference:65](../.agents/skills/turnbasedmmorpg-studio/references/ownership-readonly.md) запрещает prod writes, но строки 72–74 разрешают local heavy compute. Local compute вне selected source само по себе не нарушает read-only контракт; reference не отделяет такой канал явно. Current code выбирает base URL selected source и вызывает mutators: [_api:67](../src/studio/features/cabinet/modules/combat_ai_testing/cabinet.py), [clear/train:1516](../src/studio/features/cabinet/modules/combat_ai_testing/cabinet.py). Label `READ-ONLY` и read-only SQL DSN не ограничивают HTTP writes.

**Потенциальное направление:** один owner contract для selected source; отдельно решить, существуют ли local compute actions вне source connection. До такого решения более слабое описание reference не является разрешением нарушать entrypoint. Workflow — матрица source × HTTP action; Enforcement — deny tests/central capability gate и реальные DB/Redis permissions при соответствующей задаче. Существующего Studio skill достаточно.

### SG10-K5 — два правила помещают correlation context в разные слои

**Подтверждено статически; guidance defect Low; shared event infrastructure; при следующей правке event guidance.** [Streams:59](../.agents/skills/turnbasedmmorpg-backend/references/redis-streams.md) требует handler «extracts nothing, builds nothing, catches nothing»; [Streams:96](../.agents/skills/turnbasedmmorpg-backend/references/redis-streams.md) запрещает handler касаться `correlation_id`. [Logging:54](../.agents/skills/turnbasedmmorpg-quality/references/logging.md) требует каждый handler устанавливать correlation context и очищать его в finally. Это буквальное противоречие, независимо от runtime дефектов A02-07.

**Потенциальное направление:** согласовать owner транспорта и tracing wrapper, сохранив thin application handler. Enforcement должен проверять семантическую границу/context isolation, а не число строк 3/10. Не нужна отдельная logging architecture.

## 4. Workflow — процедуры неполны

### SG10-W1 — повтор, частичный отказ и recovery не превращены в явный lifecycle checklist

Источники: A03-01/02/03/04/06/07; A04-03/05/06/11/12/13; A05-01/04/05/06/08/09/10; A06-03/04. Общая тема повторяется в наградах, completion, dirty flush, archive и enqueue, но это **разные owner operations**, не одна причина с одним исправлением. [Document patterns:88](../.agents/skills/turnbasedmmorpg-backend/references/document-patterns.md) уже требует SQL fact → document → write status → retry/backfill. [Quality testing:5](../.agents/skills/turnbasedmmorpg-quality/references/testing.md) уже требует integration для внешних границ. Не отсутствует сам принцип надёжности; отсутствует достаточно конкретный общий способ его доказать.

**Потенциальное направление:** при изменении lifecycle перечислять operation identity, authoritative preconditions, commit point, duplicate behavior, error after every external effect, recovery owner и durable scheduling. Для lease отдельно различать owner-aware release и fencing on commit. Для Streams — delivery, ack, pending reclaim, poison message, retention и duplicate handling; flat envelope и BLPOP reply не обеспечивают recovery. Severity исходных дефектов сохраняется в аудитах; срочность зависит от доступности pre-alpha контракта. Enforcement — focused fault/retry tests, а реальные adapter guarantees требуют изолированных RedisJSON/SQL/Mongo/ARQ integration tests. Устанавливать такие среды в рамках этого отчёта не разрешено.

### SG10-W2 — authorization matrix шире существующего character owner правила

Источники: A07-01/02/03/04/05/06/07/08/11/12/13; A08-03/04. [Backend architecture:26](../.agents/skills/turnbasedmmorpg-backend/references/feature-architecture.md) уже требует `current_user.id == character.user_id`. В текущих player/admin routers имеются handler/DTO dependencies без общего actor/admin principal: [Combat router:27](../src/backend/features/combat/api/router.py), [Rift game router:28](../src/backend/features/rift/api/router.py), [GenerationAI router:23](../src/backend/features/generation_ai/api.py). Это подтверждает необходимость route-by-route проверки; production reachability здесь не проверена.

**Потенциальное направление:** для нового/изменённого route зафиксировать public/player/admin/internal/dev audience, verified principal, active game session, resource owner/membership, HTTP/WS trust source и допустимые server-authoritative поля. Chat membership и administrative generation не покрываются одним character ID check. Enforcement — route-policy inventory и негативные тесты с чужим actor/scope, отсутствующим principal, site/game token substitution и запрещёнными DTO полями. Не требуется новый project security skill: обычная разработка относится к backend/frontend owners, отдельный новый security review — к глобальному security-review.

### SG10-W3 — clean-checkout/release provenance и recovery proof неполны

Источники: A06-05/06/09/12; A08-09/10/11/15. [Release deployment:41](../.agents/skills/turnbasedmmorpg-release/references/deployment.md) уже требует whole-repo quality, immutable images и manual deployment. [Quality validation:5](../.agents/skills/turnbasedmmorpg-quality/references/validation.md) уже предупреждает о внешнем runner. Но локальная готовая venv не подтверждает clean install; manual dispatch не подтверждает protected approval или successful quality выбранного image. Current [CI:3](../.github/workflows/ci.yml) запускает PR только для main, [develop job:19](../.github/workflows/ci.yml) ограничен lint/types.

**Потенциальное направление:** отдельно доказать clean dependency resolution, идентичность source policy в CI/image build, связку image digest ↔ commit ↔ quality result ↔ Compose/schema revision, restart boundaries и restore drill. Repository/environment policies и реальный recovery status остаются unknown. Enforcement — конкретные CI predicates/provenance/isolated migration checks, а не новая формулировка «всегда запускай тесты». Сохранять main `needs: quality`, non-root images и разделение слоёв.

### SG10-W4 — производительность и детерминизм не имеют общего доказательного языка

Источники: A09-01/02/03/04/05/06/07/08/09/10/11, A04-07 со статически перепроверенной предпосылкой. [Generation determinism:13](../.agents/skills/turnbasedmmorpg-game-content/references/generation-determinism.md) уже отделяет template identity от prompt richness; это не спецификация cross-process world seed. [Document patterns:9](../.agents/skills/turnbasedmmorpg-backend/references/document-patterns.md) уже различает bounded artifacts и unbounded streams. Отдельные очереди не доказывают backpressure, fairness, bounded history или отсутствие event-loop блокировки.

**Потенциальное направление:** для горячего пути описывать единицу нагрузки, рост payload/commands, drain/arrival rate, retention, slow consumers, transaction lifetime и measurable budget. Для deterministic generator — seed serialization, algorithm/rules version, stable ordering и RNG scope; внешние AI тексты/изображения не обещать детерминированными по seed. Enforcement — небольшие независимые complexity/budget и cross-process determinism tests там, где контракт утверждён. Production capacity/RPS из этих аудитных синтетических проб не выводится; native rewrite не обоснован.

## 5. Enforcement — правила есть, независимые сигналы ограничены

| ID | Существующее правило и текущая защита | Недостающий сигнал / возможное направление | Граница ложных выводов |
| --- | --- | --- | --- |
| SG10-E1 | Managers/feature integrations, tests на физическое расположение: [boundary tests:7](../tests/backend/features/test_infrastructure_boundaries.py) | Узкие направленные import checks, raw key/path ownership, backend-only DTO consumers; A02-01/03/04/05/06/07/08, A06-08 | Нынешний prefix test пропускает Rift и проверяет ограниченный список [boundary tests:63](../tests/backend/features/test_infrastructure_boundaries.py); не запрещать допустимый composition root и любой infrastructure import |
| SG10-E2 | Fixture validator действительно проверяет items/skills/scenario: [validator:12](../tools/validators/run.py) | Утверждённые World/Hex graph invariants, schema/resource/version parity; A04-14/19/20 | Не объявлять отсутствующий сезонный runtime сломанным и не применять legacy traversal контракт к Hex prototype без решения |
| SG10-E3 | DTO/unit fakes, negative auth paths и настоящая domain logic; A06 §4/5/15 | Shared backend response ↔ frontend parse contracts, route deny matrix; lifecycle faults и настоящие adapter semantics; A06-02/03/04/07 | Dict-based FakeRedis не доказывает wire serialization, Lua/WATCH/TTL; тест с неактивированной precondition может пройти при существующем дефекте |
| SG10-E4 | Global coverage threshold, main quality и image `needs: quality`: [CI:43](../.github/workflows/ci.yml), A06 §7/8 | Develop behavioral gate, clean checkout, миграция из empty schema, application dependency audit вместо hook env, provenance выбранного deploy ref | Threshold не доказывает branch/patch coverage; отсутствие patch policy само по себе не High (A06-10 Observation); hosted results неизвестны |
| SG10-E5 | Logging no-PII правило [logging:43](../.agents/skills/turnbasedmmorpg-quality/references/logging.md), origin/cookies/key checks, A07/A08 strengths | Fail-closed config/dev route guards; redacted exception/log/metrics labels; resource/source permissions; A08-01/03/04/05/06/07 | `.env`/network/runtime settings не читались; репозиторная конфигурация не является снимком production; нельзя печатать реальные ключи ради подтверждения |
| SG10-E6 | Короткие skills и ссылки на references; AGENTS требует актуальный source | Link/path checker для markdown и code-span anchors; narrow drift review при schema/API/workflow changes, особенно K1/K4/K5 | Link existence не подтверждает смысловую актуальность, approved stage или историческое owner permission |

Это предложения к владельцам существующих checks. Не требуется заменять все fakes реальными сервисами, строить общий mutation harness или запрещать любой большой класс. Validator/CI/test изменения не выполнены.

## 6. Совместимость audit-remediation и границы будущих изменений

| Проверяемое свойство | Результат |
| --- | --- |
| Исторические аудиты, dirty tree, четыре независимые оси | Соответствует: [classification:3](../.agents/skills/turnbasedmmorpg-audit-remediation/references/finding-classification.md). В частности совпавший HEAD не гарантирует одинаковое дерево |
| Pre-alpha / Experimental / Dev-only / Legacy | Поддержаны: [classification:11](../.agents/skills/turnbasedmmorpg-audit-remediation/references/finding-classification.md). Пример «current alpha» иллюстративный; текущая пользовательская стадия имеет приоритет |
| Дубликаты по причине/исправлению/проверке | Соответствует: [root cause:7](../.agents/skills/turnbasedmmorpg-audit-remediation/references/root-cause-analysis.md). Поэтому W1 не объединяет все окна в одну implementation task |
| Knowledge / Workflow / Enforcement; отсутствие project security skill | Соответствует: [skill improvement:5](../.agents/skills/turnbasedmmorpg-audit-remediation/references/skill-improvement.md). Не следует автоматически создавать security skill |
| Report-only scope, запрет production/skills/code/tests/CI/install | Соответствует: [remediation skill:27](../.agents/skills/turnbasedmmorpg-audit-remediation/SKILL.md). Явное авторизованное действие пользователя имеет приоритет; разрешённый отчёт выполнен без дополнительного approval |
| Template implementation plan | Не применялся: [report template:3](../.agents/skills/turnbasedmmorpg-audit-remediation/references/report-template.md) предназначен для запрошенного проекта плана. В этом отчёте нет порядка внедрения, задач с трудоёмкостью или обещания исправлений |

Совместимость достаточная; изменение remediation skill сейчас **не требуется**. Его надо применять, а не заменять новым «аудитом навыков». Будущее редактирование project guidance относится к global project-skills-maintainer и [project maintenance:3](../.agents/skills/turnbasedmmorpg-project/references/agent-skill-maintenance.md), только в отдельно разрешённом scope.

## 7. Маршрутизация предложений и неопределённости

Project rules — K2/K3 и E1; backend — W1/W2 и key-space/transport/authority; frontend — K2 и cross-side E3; quality/testing — K5, W1/W4, E1–E6; release — W3 и источник публичной stage label; Combat — snapshot anchors, lifecycle/lease/parity; Rift — K1 и legacy/Hex separation; Studio — K4; game-content — template identity и утверждённый deterministic generation contract. Отдельный project security skill, новый общий orchestration framework, массовая смена storage или новый performance service **не требуются по имеющимся доказательствам**.

Не установлены: полный исторический реестр owner approvals; фактическая production/публичная доступность; внешние GitHub protection/environment settings; реальная storage ACL; свежий общий coverage; hosted CI/install/image build result; нагрузочные пределы; restore SLO; полноценный сезонный world runtime. Внутреннее наличие файлов и старый Graphify не заменяют эти доказательства. Ссылка на отсутствующий approved-stage файл — дефект навигации, а не основание отменить существующую реализацию или выдумать одобрение.

Прочитаны все девять исходных отчётов по summary, карте исполнения/контрактов, реестрам находок, ограничениям и разделам сильных решений; необходимые claims о guidance сверены с текущими skills, routers, managers, validator и CI. Локальные прогоны из аудитных отчётов не повторялись. Итоговая проверка этого артефакта — существование ссылок и корректность указанных source anchors; функциональная верификация будущих исправлений остаётся отдельной задачей.
