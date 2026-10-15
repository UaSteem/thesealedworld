# Аудит 05/10 — Persistence, Data Consistency и отказоустойчивость

Дата: 09.10.2026. Объект: текущее рабочее дерево Sealed World / TurnBasedMMORPG, включая существующие незакоммиченные изменения. Режим: аудит; исправления исходников, тестов, конфигурации, миграций и skills не выполнялись. Production и реальные хранилища не подключались.

## 1. Executive Summary

Система имеет полезные локальные гарантии SQL, но **не гарантирует сохранение игровых инвариантов при повторе и частичном отказе всей операции**. Главная проблема — несовпадение границ принятия результата: SQL commit, изменение Redis, публикация события и завершение worker происходят отдельно, а постоянный маркер выполненной операции есть не во всех путях.

Redis нельзя считать только cache. До flush он содержит единственную актуальную копию части Character/Inventory/Rift; незавершённый Combat, очереди и ещё не архивированные сообщения также зависят от Redis. SQL позволяет восстановить предыдущий checkpoint, но не обязательно последнее принятое действие.

Выделены **13 новых подтверждённых дефектов или failure windows: 5 High и 8 Medium**. Ещё **2 находки имеют статус непроверенного риска**. Critical не установлен. «Подтверждённый failure window» означает наличие конкретной последовательности записей и достижимой границы сбоя в коде, а не воспроизведённый инцидент на production. Существующие A02/A03 сохранены под прежними ID.

Наиболее существенные новые результаты:

- Safe loot claim может повторно зачислить ресурс после SQL commit; списание из corpse не требует достаточного остатка. Передача предметов не сверяет точного SQL-владельца источника.
- Ошибочные Redis Streams messages остаются pending без найденного механизма повторного получения. Trim не учитывает незавершённую обработку.
- Chat archiver двигает cursor после ошибки Mongo/SQL, исключая запись из следующей попытки.
- Восстановление Rift не обрабатывает независимую потерю instance/session: либо не восстанавливает отсутствующий компонент, либо заменяет живой компонент старым snapshot.
- Combat archive reader обращается к удалённому SQL-полю вместо Mongo payload. Это отдельно от ранее найденных проблем записи архива.
- Site baseline создаёт текущую ORM-схему, после чего следующие миграции повторно добавляют уже созданные колонки. Чистый upgrade не согласован с текущими моделями.

Сильные решения: отдельные site/game SQL metadata и базы; единая SQL-транзакция для ряда переносов и Expedition cashout; блокировки кошелька и экспедиции; unique item placement; processed events для unsafe claim; стабильные Mongo identity/upsert; owner-aware release lock; явные Mongo schema versions. Их следует сохранить. Глобальная распределённая ACID-транзакция или смена архитектурного стиля для закрытия найденных окон не требуются.

## 2. Методология и охват

Прочитаны AGENTS.md, project/backend/quality instructions, storage-ownership, document-patterns, event-bus/redis-streams, testing strategy; специализированные Combat/Rift/release references применялись при соответствующих проверках. Использованы cost-aware-delegation, ask-before-editing и verified-execution. Три независимые read-only проверки покрыли Character/Inventory/Expedition, Combat/Rift и transport/Mongo/deploy; ведущий перепроверил ключевые источники и рассмотрел site persistence и SQL boundaries.

`audit/01_project_inventory.md`, `02_architecture_boundaries.md`, `03_combat_runtime.md` использованы для навигации и исключения повторных ID, не как доказательство текущего кода. Graphify не использовался. Проверены инфраструктурные managers/repositories, core sessions/containers/bus/ARQ, feature services/workers, chat, frontend auth/surveys/database, shared contracts, Alembic и deploy. Внешняя библиотека Streams проверена в установленной `.venv/Lib/site-packages/codex_platform`, поскольку project adapter делегирует ей обработку.

Формат доказательств ниже: `путь:строка` относительно корня репозитория. Диапазоны обозначают изученный блок. Важные номера проверены по текущим файлам; после дальнейших изменений они могут сместиться. Путь в `.venv` — локальный исполняемый dependency, а не исходник приложения. `uv.lock:541–550` закрепляет codex-platform 0.5.2; соответствие production-образа локальному окружению не проверялось.

Критерии: точка durable commit; источник истины в данный момент; проверка владельца; ресурс до/после операции; поведение повторного запуска; наличие durable repair payload. Не трактовались как гарантии комментарии «atomic», «idempotent», поле `revision` без CAS и `mongo_status` без replayer. Ограничения фактического тестирования приведены в §11.

## 3. Карта persistence и ownership

| Данные / роль | Владелец и источник истины | Формат, запись / чтение | Версия, retention, восстановление |
| --- | --- | --- | --- |
| Site accounts, refresh/email tokens, referrals, surveys, news, feedback, activity | Frontend/site PostgreSQL; не game DB | Отдельный Base schema `site`, ORM repositories/services; HTTP site reads | Alembic site; unique/FK; сроки tokens проверяются приложением; общего purge в просмотренном пути нет |
| Character identity, attributes, skills, progression | Character/game PostgreSQL для сохранённого состояния; AC Redis для ещё не синхронизированных изменений | SQL repositories/upsert; Redis JSON AC; dirty sync SQL ← AC | SQL schema_version там, где mixin подключён; AC dirty generation не является атомарным CAS; Redis loss возвращает checkpoint |
| Items и ресурсы | Items/Inventory/Expedition game PostgreSQL: ItemInstance, единственный ItemPlacement, ResourceBalance, ResourceWallet | ORM update/flush/commit, row locks в отдельных ресурсных путях | PK/unique и transaction logs; polymorphic holder не равен FK к каждому типу владельца; SQL — основание восстановления ownership |
| Inventory layout/equipment во время окна | Inventory Redis session до flush; SQL placements после commit | JSON snapshot `by_id/layout`, action → полный SET; repository.save_placements | TTL 1h; dirty marker без generation; из SQL восстанавливается последнее сохранённое размещение, не все принятые действия |
| Expedition risk/progress/processed events | Expedition SQL | Run row, JSON pending progress/processed_events, ResourceBalance; Redis active pointer/runtime — projection | Redis pointer/runtime 7d; SQL status/row lock; реконструкция corpse неполная |
| Combat active runtime | Combat Redis — единственная полная текущая копия | JSON actors/meta, queues, intents, deadlines, Lua/нетранзакционные pipelines | Lease 60s; runtime TTL; финальный payload Redis 24h; незавершённый бой из SQL summary не восстановить |
| Combat final result и analytics | Mongo full document + SQL searchable summary/pointer; Redis финализация — промежуточный источник для persist | Mongo upsert combat_id; SQL unique combat_id; reader должен пересечь обе границы | Документ schema_version; SQL mongo_status; автоматический полноформатный reader сломан (A05-11), recovery limited TTL (A03-12) |
| Rift catalog и membership | SQL catalog/membership — identity/участие; Mongo — heavy catalog/snapshot; Redis — актуальный run | Feature runtime integration, SQL repositories, Mongo upsert, JSON instance/session/presence | Instance/session TTL 1h независимо; Mongo schema_version проверяется; snapshot_version — счётчик, не CAS; restore A05-10 |
| Scenario | SQL quest definitions/state + Redis текущий ScenarioContext | Repository upsert; JSON SET NX при create, patch pipeline | TTL из ScenarioConfig/game config; SQL quest state не доказан полным checkpoint всех transient context fields |
| Presence, locks, actor commitments, transport snapshots | Redis infrastructure managers | Strings/sets/JSON, NX/EX/Lua в отдельных managers | Ephemeral leases/TTLs; могут быть пересозданы, но их потеря не доказывает безопасность продолжающегося stale worker |
| Core events/request-reply | Redis Streams и reply lists — transport, не постоянный ledger бизнес-операций | XADD/XREADGROUP/XACK, reply LPUSH/BRPOP; correlation id | Core stream maxlen 10000; reply TTL задаётся caller; PEL recovery отсутствует в изученной версии |
| ARQ jobs | Redis queues — pending execution | Отдельные combat/system/generation-ai/simulation queues, registered functions | Worker timeout/result retention не business idempotency; SQL→enqueue gap требует отдельного восстановления |
| Chat | Redis buffer до архива; Mongo bodies; game SQL chat thread/membership/message indexes | Websocket broadcast → XADD → cron Mongo append → SQL index | Buffer maxlen 5000/topic, cron каждые 10 min; Mongo bounded buckets, явного TTL cleanup нет; cursor bug |
| GenerationAI | SQL task identity/status; Mongo input/result/error payload — обязательный первичный источник тяжёлого запроса | Repository hydrate → handler → provider/asset write → domain persist → task done | Unique identity_key; schema/revision; SQL row без prompt не восстанавливает Mongo input; pending enqueue recovery не найден |
| Generated monster content | SQL identity/selection indexes; Mongo actor/tier documents; generated assets local/S3 | actor document upsert по stable key; strict tier/schema reader | Это не просто cache; Mongo loss лишает runtime исходных actor payloads; rebuild зависит от доступности исходных данных |
| Файлы/generated assets | Git assets — shipped content; generated local volume или S3 — байты результата | LocalGeneratedAssetStorage.put_bytes / S3 put_object, SQL/Mongo storage_key + URL | Hash-derived keys в отдельных task specs; нет общей транзакции bytes↔DB; backup/versioning/GC внешнего object storage не подтверждены |

Основные anchors: `src/backend/core/database/session.py:10–75`, `src/frontend/core/database/base.py:17–18`, `src/frontend/config/settings.py:50–53`, `src/backend/config/settings.py:36–42`; `src/backend/features/items/models/instance.py:66` и последующие models; `src/backend/infrastructure/actor_state/managers/session.py:41–71,119–171`; `src/backend/infrastructure/inventory/managers/session.py:9–38`; `src/backend/infrastructure/expedition/managers/session.py:8–45`; `src/backend/infrastructure/rift/managers/instance.py:16–28`, `session.py:14–31`; `src/backend/infrastructure/scenario/managers/session_manager.py:23–71`.

Generated assets: `src/backend/features/generation_ai/asset_storage.py:54–135,153–194`; task URL construction `:24–38`; generated actors `src/backend/infrastructure/monsters/actor_documents.py:46–76,89–126`. `src/shared` содержит DTO/enums/contracts и не является отдельным владельцем записи в БД.

## 4. PostgreSQL и транзакции

### 4.1. Общие границы

Обе базы используют AsyncSession, `expire_on_commit=False`, `autoflush=False`, `pool_pre_ping=True`. `get_db` выдаёт session, откатывает при исключении, но **не делает автоматический commit**. `get_session_context` коммитит после успешного блока и откатывает исключение. Backend дополнительно имеет manual context без автоматического commit (`backend/core/database/session.py:20–75`; frontend counterpart `:20–45`). Это разумное разделение, но внутренний repository.commit уже необратим для внешнего context: поздний rollback не откатит ранний commit.

Явный `isolation_level` и SQLAlchemy `version_id_col` в изученных source paths не найдены. Нельзя утверждать, что production имеет SERIALIZABLE или иной конкретный server default: сервер не опрошен. `RevisionMixin.bump_revision` лишь увеличивает поле (`backend/core/database/base.py:36–41`), сам по себе не предотвращает lost update.

### 4.2. Реальные инварианты

- `ItemPlacement.item_id` — PK: одна текущая placement row на instance. Это предотвращает две одновременные SQL-строки владения, но не неправильный перенос существующей строки (A05-02).
- ResourceBalance имеет уникальность комбинации holder/storage/resource; wallet — строка персонажа. Claim блокирует существующие balance/wallet (`loot_claim_task.py:247–248,307–314`), однако lock не заменяет проверку достаточного остатка (A05-01).
- Expedition safe sync блокирует run, переносит предметы, переводит balance в кошелёк, очищает pending progress и меняет status в одной SQL единице работы (`expedition/service.py:130–166,372–466`). Progression/skill repositories используют additive UPSERT. Это хорошая граница; проблема внешних Redis effects рассматривается отдельно.
- Unsafe claim включает processed key в SQL row экспедиции под lock (`loot_claim_task.py:203–211,271–274`). Защита зависит от той же найденной активной экспедиции: её нельзя переносить на safe branch или на сменившийся lifecycle run без проверки.
- Site registration создаёт User и ReferralReward до одного commit; IntegrityError приводит к rollback, повтор referral code ограничен пятью попытками (`frontend/features/auth/integrations/auth_persistence.py:33–59`). Email, referral code, token hash уникальны. SurveyResponse.send_id unique (`frontend/features/surveys/models/survey.py:70–79`) обеспечивает один ответ даже при гонке pre-check; дружелюбный conflict response отдельно не гарантирован.

### 4.3. Несколько commits в бизнес-операции

| Операция | Фактические границы | Результат при частичном сбое |
| --- | --- | --- |
| Character create | SQL session_pending row commit → отдельный imprint/attrs/skills/items commit → AC/scenario → финальное состояние | Есть компенсационный cleanup, но hard crash не исполняет except; полный durable saga/reconciler не установлен |
| Loot batch | Отдельный SQL context на каждый corpse → после всех SQL transfers удаление из Redis | Успех первого corpse переживает ошибку второго; повтор safe batch опасен A05-01 |
| Inventory flush | repository.commit внутри service, затем clean Redis snapshot; внешний context может commit ещё раз | SQL сохранение и Redis clean разделены; concurrent snapshot может быть затёрт A05-03 |
| Combat finalizer | Redis inactive → Character/Expedition effects → finalization payload → Rift/Inventory effects → enqueue archive | Общей фиксации нет; A03-01/02/07 остаются действительными |
| Site refresh rotation | DELETE старого token + commit → INSERT нового + commit | Падение между commits лишает сессию refresh token (A05-12) |
| GenerationAI | Request PG/Mongo → PG commit → ARQ; worker domain/result writes → PG commit → follow-ups enqueue | SQL task переживает enqueue failure, но автоматического rescheduler не найдено (A05-08) |

Character creation anchors: `src/backend/features/game_lobby/services/character_creation_service.py:46–108`, `integrations/system_integrator.py:231–343,721–742`. Delete проверяет ownership/confirmation, чистит scenario/rift/AC, переносит items в system, удаляет Character и коммитит (`integrations/system_integrator.py:606–620,704–742`). SQL relationship cascades: `character/models/character.py:51–83`; unique имени `:26–29`. SQL и Redis удаления не образуют общую транзакцию; успешность компенсации после hard crash не проверена.

## 5. Redis/RedisJSON

### 5.1. Атомарность и принятие действия

Одна Redis-команда/Lua-script имеет локальную границу. Последовательность `JSON.SET`, `EXPIRE`, `SADD` такой границы не имеет. `pipeline(transaction=False)` группирует доставку команд, но не делает операцию неделимой. Это важно для Combat commit (`infrastructure/combat/managers/session.py:594–650`, A03-03), AC patches (`actor_state/managers/session.py:119–160`) и Scenario patch (`scenario/managers/session_manager.py:63–71`). Ошибка/разрыв может оставить частичный набор полей/индексов/TTL.

Полный JSON SET также атомарен только как замена значения: read-modify-write двух клиентов теряет одну правку. Inventory сохраняет весь session (`inventory/services/inventory_service.py:84–112,168–179`); Rift session restore тоже делает полный SET. CAS и fencing для этих путей не найдены.

Dirty — сигнал синхронизации, не долговечный журнал. AC patch и mark выполняются отдельно; clear сравнивает generation до отдельной записи (A03-10). Inventory и Rift имеют собственные независимые окна A05-03/09. Sweeper помогает только пока ключ и dirty signal ещё существуют. TTL/eviction может удалить их до flush.

### 5.2. TTL и очистка

| Семейство | Фактический срок / механизм | Что теряется или восстанавливается |
| --- | --- | --- |
| AC | 6h, renew create/update/patch; `actor_state/managers/session.py:41–71,119–128,762–763` | SQL checkpoint остаётся; несинхронизированные витальные/state изменения не доказаны восстановимыми |
| Inventory | 1h, renew set/patch/touch; `inventory/managers/session.py:9–38,80–84` | SQL list rebuild работает, latest dirty equipment/layout может откатиться |
| Expedition pointer/runtime | 7d; `expedition/managers/session.py:8–45` | SQL run остаётся; runtime projection можно пересоздать, corpse path имеет A05-04 |
| Rift instance и session | По 1h, каждый ключ обновляется отдельно | Истечение не синхронно; A05-10 опровергает достаточность проверки одного instance |
| Combat finalization | 24h payload; persist worker выходит при missing; A03-12 | Архив при своевременном persist остаётся; поздний persist без payload не восстанавливает полный результат |
| Loot | Hidden default 24h; activated delay 900s + public 3600s; empty 300s | Намеренное истечение loot допустимо по правилам; ранняя потеря Redis при SQL-owned corpse требует repair |
| Player corpse | Default 86400s configurable | Потеря до `corpse_expires_at` отличается от штатного завершения retention |
| Scenario | Default 24h, TTL из ScenarioConfig/game config (`scenario/game_config.py:8`) | Transient context cleanup; полнота SQL resume требует отдельного интеграционного теста |

Loot TTL anchors: `loot/integrations/loot_integration.py:29–76`; corpse save — JSON/expire/location index последовательно, `infrastructure/loot/managers/loot_manager.py:50–55`; player corpse `expedition/service.py:229–236,552–604`.

### 5.3. Persistence конфигурация

`deploy/compose.infra.yml:23–39` задаёт Redis Stack и named `/data` volume, но command содержит только запуск и password. Явной политики AOF/appendfsync/RDB, maxmemory/eviction в этом файле нет. Это **не доказательство отключённого persistence**: image defaults и фактический CONFIG не исследованы. Однако volume сам по себе не подтверждает ни RPO, ни восстановление последних acknowledged writes. Для этого необходимы runtime configuration, restart test и restore drill в изолированной среде.

## 6. MongoDB

`MongoClientProvider` создаёт AsyncMongoClient с URL и serverSelectionTimeoutMS (`infrastructure/mongo/client.py:10–36`). Явные writeConcern/readConcern/retryWrites не задаются здесь; URI и topology production не проверялись. Поэтому majority durability/replica-set failover нельзя считать подтверждёнными. Compose запускает один `mongod --auth --quiet` с volume, без replica-set command (`deploy/compose.infra.yml:40–60`).

| Семейство | Identity / schema / writes | Реальная роль и ограничения |
| --- | --- | --- |
| Combat | unique combat_id; `$set` upsert; indexes по времени/типу/location/winner | Full finalization/analytics; повтор заменяет документ, а не immutable insert-only archive; SQL summary недостаточно для полной реконструкции |
| Rift runtime snapshots | unique document_kind + instance; deterministic `_id`; schema version строго проверяется | Последний snapshot, не история версий. `snapshot_version` пишется без compare predicate; конкурентный старый flush может заменить новый |
| Rift catalog | Mongo heavy catalog document + SQL searchable identity | Потеря Mongo не равна потере производного cache; восстановление требует generated/catalog sources |
| Chat buckets | deterministic bucket `_id`, time/shard indexes; `$push` сообщений, count/closed | Bodies — первичные данные. Bucket time window не является TTL retention; явных expireAfterSeconds indexes нет |
| GenerationAI documents | unique task_id/document kind, initial input + result/error updates, schema_version | Единственная сохранённая полная спецификация task; SQL status не компенсирует missing payload |
| Generated actors | stable actor key, schema/tier validation | Runtime-ready actor payloads; SQL references не заменяют heavy document |

Anchors: `infrastructure/mongo/combat_documents.py:19–43`; `infrastructure/rift/repositories/snapshots.py:22–91`; `infrastructure/mongo/chat_buckets.py:30–86,112–130`; `infrastructure/generation_ai/task_documents.py:43–139`; `infrastructure/monsters/actor_documents.py:46–126`. Общий index bootstrap `infrastructure/mongo/bootstrap.py:21–46` вызывается deployment migration job. Создание индекса в коде не доказывает его наличие на уже работающем сервере, но исполняемый механизм существует.

В просмотренных repositories нет общей cleanup/retention задачи для Combat/AI/snapshots/chat buckets. Ограничение числа сообщений в bucket не ограничивает общий объём коллекций. Chat append также требует real-Mongo проверки (§13): unit fake не доказывает корректность update operators и seq allocation.

## 7. Межхранилищные workflows

### 7.1. Combat

Redis exchange commit → `active=0` → experience/Character state/Expedition death или progress → finalization payload в Redis → Rift completion → durability → привязка finalization к персонажу → archive job → Mongo document → SQL summary/pointer. Точный хвост порядка: `victory_finalizer_task.py:117–129`.

`victory_finalizer_task.py:69–108,133–134` устанавливает inactive до downstream effects и ловит исключение. Уже выполненный effect не откатывается. Повтор может повторить XP (A03-01); ошибка оставляет неполный lifecycle (A03-02). `finalization_persist_task.py:27–49` требует Redis payload; ingestion `runtime/analytics/ingestion.py:102–136` пишет full Mongo document. Повтор Mongo upsert по combat_id полезен, но SQL unique не защищает все предыдущие effects. Persisted result существует независимо от того, способен ли его читать UI: A05-11 ломает именно reader. Точка принятия игрового исхода сейчас не сведена к одному durable finalization state machine.

### 7.2. Rift

SQL catalog/membership → Mongo catalog/snapshot → Redis instance/run/presence; gameplay меняет Redis; flush читает instance + sessions + presence → Mongo snapshot → SQL snapshot refs. Restore берёт latest Mongo по instance, затем SET instance, SET sessions, rebuild presence (`rift/integrations/runtime.py:182–276`). Это несколько reads/writes без общего snapshot lock/version CAS. Mongo success + SQL failure оставляет pointer/version рассогласованными; Redis dirty clear после snapshot может потерять новую мутацию. Encounter completion проверяет active encounter identity, затем раздельно обновляет instance/run/presence (`:410–416,479–498`, A03-11). Минимальная модель восстановления должна учитывать отсутствующие компоненты и версии, а не только наличие instance.

### 7.3. Inventory / Loot

Generated ItemInstance/placement и ResourceBalance → Redis corpse/preorder → выбор claim из Redis → SQL transfer/credit → Redis corpse subtraction → inventory cache invalidation/notice. `loot/services/loot_service.py:332` формирует claim из runtime; worker выполняет SQL первым (`loot_claim_task.py:67–93`). Это правильное намерение, но SQL должен быть авторитетом допустимого количества/владельца, иначе stale/repeated snapshot дублирует ресурсы. Принятый HTTP/enqueue ответ не равен выполненному claim. Safe replay A05-01, owner predicate A05-02; late preorder сохраняет A03-05.

Обычный equip/unequip принимается в Redis раньше SQL flush. Inventory изначально читается из SQL (`inventory_service.py:132–158`), но после action уже является dirty runtime, а не чистой projection. Cache deletion после loot может пересечься с таким dirty runtime; этот дополнительный interleaving не воспроизводился и не объявлен отдельным доказанным дефектом.

### 7.4. Character / Expedition

Character SQL → AC Redis → mutations+dirty → sync SQL → compare/clear dirty. `character/integrations/system_integrator.py:42–85` специально не заменяет persistent XP/skills/free-XP snapshot при active/death_pending Expedition: pending progress имеет отдельного owner. Это полезная защита от преждевременного закрепления risk rewards.

Expedition `accumulate_progress` SQL pending JSON → AC mirror (`expedition/service.py:103–128`); safe sync блокирует run и закрепляет имущество/ресурсы/XP (`:130–166,372–466`). Death переводит run в death_pending (`:173–217`), формирует corpse (`:219–274`), respawn завершает run и восстанавливает location/vitals (`:276–308,620–679`). SQL row locking сериализует часть этого lifecycle, но Redis effects и dirty sync вне той же транзакции; race death/respawn/AC sync нуждается в controlled test. Нельзя объявлять смерть атомарной только по наличию row lock.

### 7.5. Chat

Realtime broadcast → XADD buffer → cron XREAD от cursor → Mongo bucket append → SQL message index → cursor SET. Пользователь может увидеть сообщение до durable buffer (`message_service.py:42–65`). Cursor не является consumer-group ACK и сейчас двигается даже при failure (`archive.py:44–59`). SQL write_failed содержит status/pointer, но не original body (`:101–113`); это мониторинг отказа, не восстановимый outbox. Mongo success + crash до SQL/cursor создаёт replay и потенциальный duplicate append. Чат не даёт exactly-once archive или гарантии «увидел = попало в историю».

### 7.6. GenerationAI и assets

Request spec → SQL identity/status + Mongo input → SQL commit → ARQ task id → claim SQL row `FOR UPDATE SKIP LOCKED` → hydrate Mongo → provider → bytes local/S3 → handler.apply_result/domain writes → Mongo result + SQL done → SQL commit → enqueue follow-ups. Anchors: `generation_ai/api.py:39–54`, `repositories.py:31–61,103–157,228–259`, `services.py:41–108,168–175`, `workers/tasks.py:18–34`.

Публикация здесь означает доступный asset URL и применение результата handler-ом; собственного обязательного Streams publish результата не найдено. Для news handler apply_result возвращает None (`tasks_news.py:33–34`), SQL task/URL доступен через status API. Нельзя утверждать автоматическую публикацию статьи. Ошибка initial Mongo допускает pending task без input (A05-07). PG→enqueue разрыв (A05-08) отличается от provider retry. Running claim в worker не коммитится отдельно до external call: hard crash обычно откатывает текущую SQL-транзакцию, поэтому «любой crash навсегда оставляет running» здесь не доказан. External bytes/provider side effect при rollback SQL уже может существовать; orphan/repeated generation — остаточный риск.

## 8. Redis Streams и ARQ

`GameEventProducer` — adapter; publish затем trim (`core/bus/producer.py:16–26,60–67`), request delegating (`:28–39`), publish_reply (`:41–43`). Correlation id маршрутизирует ответ и сам по себе не dedup key бизнес-операции. Потерянный ответ/timeout не отменяет обработку запроса. При повторе с новым correlation id возможен повтор side effect; даже прежний correlation id не становится автоматически durable result ledger.

Установленный processor ACK-ает после callback, а при exception оставляет entry pending (`.venv/Lib/site-packages/codex_platform/streams/processor.py:180–222`). Consumer читает только `>` (`consumer.py:90–94`). В изученном runtime не найден reclaim loop; comments о recovery не исполняют recovery. Worker crash после записи до ACK создаёт ambiguous result: бизнес-эффект мог сохраниться, а entry останется PEL. Добавление reclaim должно сопровождаться idempotency consumers; иначе A03/A05 replay дефекты станут чаще проявляться. Dead-letter/bounded retry для этого пути не установлен.

ARQ queue names заданы в `core/arq.py:11–16`; general defaults max_jobs=20, timeout=60, keep_result=5 (`:82–89`), GenerationAI max_jobs=5, timeout=180, keep_result=30 (`generation_ai/workers/arq.py:37–45`). Combat регистрирует collector/executor/finalizer/support/persist и имеет свою queue. System dirty sweeper регистрирует/вызывает flush tasks; inventory sweeper может заново поставить существующий dirty key (`inventory/workers/tasks/session_tasks.py:43–71`). Это ограниченный repair mechanism, а не recovery всех lifecycle operations.

**Обычное исключение ARQ не равно автоматическому повтору любой задачи.** В установленном `.venv/Lib/site-packages/arq/worker.py:610–634` Retry и разрешённая cancellation идут в retry branches, а обычное Exception — в finished/failed. Например RuntimeError из loot transfer (`loot_claim_task.py:78`) не доказывает обещанный комментарием автоматический retry. Повторы возможны через explicit reschedule, cancellation/restart или повтор клиента; отсутствие повтора ведёт к незавершённости, а наличие — требует idempotency. Keep_result не является сроком business dedup ledger. При полном Redis loss очереди/PEL/replies исчезают независимо от сохранённых SQL rows.

## 9. Конкурентность и failure matrix

| Сценарий | Фактическая защита | Остаточный результат / статус | Проверка |
| --- | --- | --- | --- |
| Два inventory action | Каждый JSON SET целиком атомарен | Last writer стирает предыдущую правку; A05-03 window | Barrier после обоих get, разные item actions, real RedisJSON |
| Два claimant одной награды | Wallet/balance row locks; unique item placement | Safe resources кредитуются при zero source; A05-01; item loser может получить false success A05-02 | Две SQL sessions, один corpse, сумма до/после |
| Повтор Combat finalizer | Inactive flag, частичные downstream markers | XP повторяется; A03-01; lifecycle частичен A03-02 | Дважды один combat_id, assert XP один раз |
| Повтор Loot claim / partial batch | Unsafe run processed hash | Safe path без marker; prior corpse SQL commits сохраняются | Сбой после первого commit и перед Redis remove |
| Death одновременно respawn | Expedition row locks/status checks | AC patch/SQL/Redis не единая граница; дополнительная гонка не воспроизведена | Pause после SQL read/перед AC patch, сравнить final run/HP/location/corpse |
| Dirty sync одновременно AC update | Generation pre-check | Не CAS, A03-10 | Мутация между generation read и clear |
| Inventory action во время flush | Commit SQL placements | Clean SET старого snapshot затирает новый; A05-03 | Pause после snapshot read, затем action и resume flush |
| Rift mutation во время snapshot | Dirty marker, Mongo upsert | Без compare-clear; A05-09 | Мутация после capture до clear, следующий sweep обязан её сохранить |
| TTL одного Rift компонента | Restore lock, Mongo snapshot | A05-10: session-only loss не чинится; instance-only loss откатывает живые sessions | Удалить по одному ключу в test instance |
| Worker restart после частичной записи | У отдельных SQL операций transaction/unique | Нет общей finalization/claim recovery; Streams pending не читается | Kill worker на commit/ACK/enqueue границах |
| Mongo outage | Timeout/status flags | Chat cursor skip; AI input loss; Combat archive ждёт Redis payload только до TTL | Fault Mongo write + restore, доказать eventual body/result |
| PostgreSQL outage | Rollback текущей transaction | Ранее Redis/Mongo/bytes effects не откатываются; chat cursor всё равно может уйти вперёд | Fail commit, проверить phantom corpse/orphan doc/marker |
| Redis outage | Exceptions, SQL rows остаются | SQL→runtime/enqueue gap; dirty-only state может исчезнуть при потере storage | Disconnect/restart на локальном стенде, восстановить из checkpoint |
| Клиент reconnect после timeout | Session/token identifiers | Timeout не доказывает cancel; claim/XP могут повториться | Drop response после успешного effect, retry same operation |
| Два worker одной сущности | SQL locks, Redis owner lease для отдельных путей | Lease release не fence commit; A03-09; double active expedition A05-14 risk | Истечь lease, запустить второй, возобновить первый |
| Event после удаления runtime | Missing checks в отдельных handlers/tasks | Может стать skip/no-op; permanent outcome/repair не гарантирован | Deliver delayed finalization/loot event после cleanup |
| Safe SQL transfer commit, Redis corpse missing | SQL ownership сохранён | Cache rebuild/notice не доказывают корректный claim replay | Fault mark_items_claimed, повтор, invariant total resources |
| Chat Mongo append успешен, SQL commit падает | SQL rollback; Mongo append не откатывается | Duplicate body при replay, risk A05-15 | Crash и retry того же message_id |

Эти сценарии — спецификация будущих проверок, кроме явно отмеченных локальных результатов §11. Реальные Redis/PG fault injections в этом аудите не выполнялись.

## 10. Миграции, backup и recovery

Site и game используют разные Alembic directories/config/env и отдельные metadata; site include_schemas=True. Game migration job выполняет `upgrade && ensure-mongo-indexes && rebuild-monsters --apply`, затем backend ждёт успешного завершения (`deploy/compose.game.yml:17–35,73–78`). Это исполняемый порядок, не доказательство rollback safety. Новый контейнер не стартует при ошибке job, однако уже сделанные SQL/Mongo/rebuild effects не откатываются общей транзакцией.

Game имеет единственный `0001_game_schema_baseline.py`, который импортирует **текущую** Base и вызывает create_all (`:12–24`). На базе, уже отмеченной baseline, Alembic не переисполнит её из-за новых ORM fields. Startup create_all (`core/containers/database.py:9–13`, `core/database/session.py:78–83`) также не является историей ALTER существующих таблиц. Соответствие deployed schema текущим models не установлено; нужен upgrade test со старого snapshot. Downgrade baseline вызывает drop_all и DROP SCHEMA CASCADE (`:27–29`): это не механизм отката релиза с сохранением данных.

Site baseline имеет ту же зависимость от live metadata; последующие 0002/0003/0004 добавляют token_hash/referral/email fields, уже присутствующие в модели. Конкретный конфликт clean install — A05-13. Повтор `upgrade head` на успешно применённой истории обычно ограничивается revision state, но это не исправляет конфликт первой установки и не доказывает rolling compatibility.

Репозиторный поиск по deploy/.github/tools не обнаружил исполняемых pg_dump/pg_restore/mongodump/mongorestore/AOF backup workflows. `deploy/compose.infra.yml:12–14,30–31,48–49` содержит volumes; `.github/workflows/deploy-production.yml:104–129` — deployment compose commands. Преддеплойный backup/restore gate не найден. Документ `docs/audits/2026-10-04-deploy-ci-follow-up.md:16` уже упоминает отсутствие gate; это не новый дублирующий defect ID. Внешние серверные backups могут существовать — они не исследованы. RPO/RTO, offsite copy, retention, encryption и фактическая restore readiness остаются неподтверждёнными.

| Полная потеря | Что сохраняется в других хранилищах | Что автоматически не восстановлено / что нужно доказать |
| --- | --- | --- |
| Redis | SQL characters/items/wallets/runs; Mongo persisted combat/rift/chat/AI | Latest dirty actions, active combat, unarchived chat, queue events/jobs; Rift частичный restore broken; нужен reconciler и согласованная checkpoint policy |
| Game PostgreSQL | Mongo heavy docs; Redis transient | Ownership/membership/ресурсная истина отсутствует; Mongo не substitute relational backup; восстановление только из проверенной SQL backup |
| Site PostgreSQL | Некоторые cookies/cache, game account IDs | Accounts/auth/referrals/news/surveys; game DB не содержит полноценной site copy |
| Mongo | SQL summaries/pointers/status; Redis до TTL | Полные archive bodies/AI prompts/generated actor payloads и snapshots; SQL statuses не дают содержимое для backfill |
| Generated local volume/S3 objects | SQL/Mongo metadata, некоторые task inputs | URL останется, bytes исчезнут; regeneration зависит от inputs/provider и не гарантирует идентичный результат |
| Неудачный deployment | Предыдущий image может остаться доступен | Не доказана совместимость старого image с новой схемой; destructive downgrade запрещён как автоматический rollback |

## 11. Тесты и фактические результаты

### Выполнено в этом аудите

1. Ограниченный pytest с `.venv/Scripts/python.exe -B`, `PYTHONDONTWRITEBYTECODE=1`, `-o addopts='' -p no:cacheprovider -q`: `tests/backend/core/database/test_session.py`, `test_session_config.py`, `tests/frontend/core/test_site_database.py`. Завис на setup первого async test; остановлен, exit 1. Не pass и не assertion failure приложения.
2. Диагностический повтор тех же файлов с `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, `-p pytest_asyncio.plugin -p pytest_mock -o faulthandler_timeout=20`: stack после 20s показал `socket.accept → _fallback_socketpair → asyncio.proactor_events._make_self_pipe → pytest_asyncio._scoped_runner`. Остановлен, exit 1. Тело проверяемого async теста не выполнено. Окружение/Windows event-loop initialization ограничивает проверку; конфигурация не менялась.
3. С отключённым autoload выполнена команда:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
.\.venv\Scripts\python.exe -B -m pytest tests/backend/core/database/test_session_config.py tests/frontend/core/test_site_database.py -o addopts='' -p no:cacheprovider -q
```

Результат: **2 passed, 1 warning, 1.29s, exit 0**. Warning `Unknown config option: asyncio_mode` ожидаем при отключённом async plugin. Эти тесты подтверждают настройку database_echo и регистрацию site metadata, но не SQL transactions/concurrency.

4. Локальная read-only introspection ORM без подключения к БД:

```python
from src.backend.infrastructure.combat.models.finalization import CombatFinalization
print(hasattr(CombatFinalization, 'finalization'))       # False
print(hasattr(CombatFinalization, 'mongo_document_id'))  # True
```

Exit 0. Подтверждает несовпадение reader/model в A05-11; не end-to-end архивный тест.

### Что есть в suite и чего это не доказывает

| Tests | Подтверждаемый контракт при успешном запуске | Непокрытая здесь гарантия |
| --- | --- | --- |
| `tests/backend/core/database/test_session.py` | Mock commit/rollback/close calls | Реальный PG rollback, isolation, deadlock |
| `tests/backend/features/inventory/test_inventory_service.py`, `test_inventory_repository.py`, `test_inventory_worker_tasks.py` | Actions/layout/flush orchestration | Concurrent action/flush и реальные RedisJSON semantics |
| `tests/backend/features/loot/test_loot_claim_task.py`, `test_loot_claim_notice.py` | Cache clearing/notice path | SQL source conservation, duplicate transfer, crash after commit |
| `tests/backend/features/character/test_session_persistence_service.py` | Session persistence cases | AC compare-clear interleaving, lost Redis state |
| `tests/backend/features/expedition/test_expedition_notices.py` | Lifecycle notices and orchestration | Real concurrent death/respawn/duplicate active run |
| `tests/backend/features/rift/integrations/test_runtime_integration.py:409,462,489,544` | Snapshot refs, existing-instance short path, restore lock/presence, dirty clear | Missing session with existing instance; newer session with missing instance; dirty change while snapshot |
| `tests/backend/features/generation_ai/test_generation_ai_core.py:329,370,388,573` | No heavy SQL fields; Mongo payload; defer enqueue until commit | Payload outage, durable enqueue reconciliation, crash after provider write |
| `tests/backend/core/bus/test_streams_migration.py` | Wiring and mocked request/reply | Real PEL reclaim/ACK after crash/trim backlog |
| `tests/backend/infrastructure/mongo/test_bootstrap.py` | Index bootstrap dispatch | Реальный Mongo update/unique/write concern |

`tests/backend/conftest.py` FakeRedis выполняет pipeline последовательно над dict и моделирует TTL отдельной таблицей, без настоящего истечения/RedisJSON server errors. Поэтому такой suite не может доказать multi-key atomicity, Lua/CAS correctness или crash durability.

Будущий минимальный fault suite: real PostgreSQL rollback и two-session barriers; real Redis Stack Lua/CAS и частичный pipeline; duplicate event; kill after commit before ACK/enqueue; TTL component expiry; Mongo outage до/после append; clean-install и previous-version migration; worker restart; cross-store reconciliation с проверкой суммы ресурсов и единственного owner. Это рекомендации для последующего плана стабилизации, тесты не добавлялись.

## 12. Новые подтверждённые дефекты

### A05-01 — High — Safe loot claim не сохраняет количество ресурсов при повторе

**Статус:** подтверждённый failure window; статическое доказательство, без real-PG воспроизведения. **Домены:** Loot/Inventory/Expedition, PG+Redis+ARQ. **Уверенность:** высокая.

`loot/workers/tasks/loot_claim_task.py:203–211` проверяет processed marker только для active unsafe expedition. В `:230–269` списание источника сопровождается полным начислением payload delta; `_consume_corpse_resource_balances :303–320` допускает отсутствующий balance и недостаток через continue/max(0). SQL context завершается до Redis removal `:67–93`. Поэтому commit → crash/повтор payload выдаёт ресурсы повторно даже при нулевом SQL source. В batch первый corpse уже committed до ошибки следующего. Row lock лишь сериализует два лишних начисления.

**Инвариант:** выдано не больше списанного; одна claim identity применяется один раз. **Последствие:** создание валюты/ресурсов. **Минимум:** durable SQL claim key в той же транзакции, точная проверка остатка/фактического списания; Redis removal повторяемый. **Тесты:** duplicate safe claim, two claimants, insufficient/absent source, crash после первого batch commit. Guard active-run не считается универсальным ledger при переходе в safe state.

### A05-02 — High — Loot SQL transfer не проверяет точный источник предмета

**Статус:** подтверждённый дефект проверки ownership. **Домены:** Loot/Items/Inventory, PG+Redis. **Уверенность:** высокая.

В `loot_claim_task.py:213–228` UPDATE ограничен item_id и широким holder_type (`corpse/system/loot_pending`), без holder_id конкретного corpse и проверки изменённых строк. Payload формируется из Redis (`loot/services/loot_service.py:332`), который может устареть. Предмет, позже оказавшийся в другом corpse/system placement, всё ещё удовлетворяет условию; предмет уже у другого персонажа не переносится, но worker продолжает Redis subtraction и notice успеха.

**Инвариант:** transfer только из заявленного текущего SQL holder; подтверждение соответствует фактическому transfer. **Последствия:** неверный получатель или false-success claim; PK предотвращает дублирование строк, не эти ошибки. **Условия:** stale/replayed queued claim после другого lifecycle transition. **Минимум:** точный разрешённый source transition, rowcount/RETURNING и ledger; отдельно определить допустимое initial loot_pending состояние. **Тесты:** другой corpse, discarded system, zero-row transfer, два claimant.

### A05-03 — Medium — Inventory snapshot/flush не сериализованы

**Статус:** подтверждённый failure window; interleaving не запускался. **Домены:** Inventory/Character, Redis+PG. **Уверенность:** высокая в отсутствии atomic revision, средняя в частоте.

`inventory/services/inventory_service.py:84–112` читает session и пишет полный JSON через `infrastructure/inventory/managers/session.py:20–28`. Два действия над одним snapshot заменяют друг друга. `flush_session :168–179` сохраняет placements и коммитит SQL, после чего SET-ает прочитанный snapshot clean. `inventory/workers/tasks/session_tasks.py:22–39` дополнительно clear_dirty после выхода из context. Новая action между чтением и clean SET исчезает из runtime; новый dirty signal может быть очищен.

**Инвариант:** принятое действие не теряется при следующей записи другого запроса. **Последствие:** откат экипировки/размещения, несогласованный loadout. Это не доказательство дублирования item instance. **Минимум:** per-character serialization либо revision/CAS для action и compare-clear для flush. **Тесты:** action/action и action/flush barriers, проверка SQL и AC loadout после следующего sweep. Независимый путь от A03-10.

### A05-04 — Medium — Death corpse публикуется до SQL commit, repair неполон

**Статус:** подтверждённый failure window. **Домены:** Expedition/Loot/Character, PG+Redis. **Уверенность:** высокая.

`expedition/service.py:238–257` переносит SQL items/resources и выставляет processed marker; `:259–268` пишет Redis corpse/session до `_maybe_commit` (либо до commit внешнего context). SQL commit failure оставляет phantom runtime. После успешного SQL commit ранняя потеря corpse Redis до business expiry не исправляется повтором: `:224–227` возвращает already_finalized, не rebuild.

**Инвариант:** доступный corpse соответствует durable source; преждевременно потерянная projection восстанавливаема. **Последствия:** ложная добыча/недоступное имущество; при A05-01 phantom resource claim усиливает ущерб. Штатное истечение заданного corpse_ttl не объявляется дефектом. **Минимум:** SQL-first durable transition, повторяемая публикация/rebuild из SQL до corpse_expires_at. **Тесты:** fail commit после Redis save; удалить Redis corpse до expires_at; повтор finalization сохраняет состав и identity.

### A05-05 — High — Streams pending не восстанавливаются

**Статус:** подтверждённый failure window установленного dependency. **Домены:** все consumers core bus, Redis. **Уверенность:** высокая локально; production version не проверена.

`core/containers/redis.py:136–164` подключает StreamRuntime. `.venv/Lib/site-packages/codex_platform/streams/processor.py:180–222` оставляет ошибку в PEL; `consumer.py:90–94` читает только `>`. Найденный consume loop не reclaim-ит pending. Crash после read или handler failure лишает сообщение последующей штатной обработки; после успешного side effect до ACK неизвестно, выполнено ли оно. `core/bus/producer.py:60–67` trim maxlen может удалить ещё нужный payload.

**Инвариант:** принятый transport message либо завершён, либо доступен для контролируемого retry/dead-letter. **Последствия:** зависшие lifecycle/rewards, утрата событий при retention. **Минимум:** исправление owner library — reclaim idle pending, retry budget/DLQ/операторский replay; retention с учётом незавершённой обработки; бизнес-dedup. **Тесты:** real Redis crash-before/after effect, restart consumer, XPENDING и trim backlog; доказать eventual outcome и отсутствие двойного эффекта.

### A05-06 — High — Chat archive cursor пропускает неуспешную запись

**Статус:** подтверждённый дефект error path. **Домены:** Chat, Redis+Mongo+PG. **Уверенность:** высокая.

`chat/workers/archive.py:44–59` присваивает new_last_id до `_archive_payload`, ловит exception и всё равно SET cursor. `_archive_payload :101–113` при Mongo error пишет SQL write_failed без тела. Следующий XREAD начинается после записи: восстановление Mongo не повторяет original body. `chat/api/router.py:112–139` не может вернуть отсутствующий Mongo content.

**Инвариант:** checkpoint не проходит мимо необработанных durable messages. **Последствие:** постоянные пробелы истории при временной недоступности хранилища. **Условия:** один Mongo/SQL failure в batch. **Минимум:** advance только успешного непрерывного префикса или durable failed-message queue с payload; идемпотентная запись при replay. **Тесты:** одноразовый outage на N-й записи, retry, все исходные bodies и уникальные message ids в истории. Broadcast-before-XADD (`message_service.py:42–65`) — дополнительное окно до архива: видимость не означает сохранение; включить Redis XADD fault в тот же acceptance suite.

### A05-07 — Medium — GenerationAI принимает task без сохранённого input

**Статус:** подтверждённый failure window. **Домены:** GenerationAI/content, PG+Mongo+ARQ. **Уверенность:** высокая.

`generation_ai/repositories.py:228–247` подавляет initial Mongo error, отмечает write_failed и возвращает task; `:31–61` сохраняет pending. SQL model `models.py:20–48` не содержит prompt/input. Service `services.py:41–67` schedules pending без проверки mongo_status. Hydrate `repositories.py:249–259` возвращает bare row при missing Mongo. Например news handler читает `task.input_payload` (`tasks_news.py:18–24`). После выхода request исходная полная spec может не существовать ни в одном durable store.

**Инвариант:** принятая к исполнению task имеет восстановимый вход. **Последствия:** невыполнимая/неправильно восстановленная генерация, потеря пользовательского запроса; не доказана потеря игровых ресурсов, поэтому Medium. **Минимум:** не принимать/schedule до durable payload либо сохранять recoverable input в outbox; повтор должен восстановить payload, а не только reset status. **Тесты:** outage initial write → restart → input recovery/exact rejection без orphan pending; Mongo read outage отдельно.

### A05-08 — Medium — GenerationAI pending/cooldown теряется между commit и enqueue

**Статус:** подтверждённый failure window. **Домены:** GenerationAI, PG+ARQ Redis. **Уверенность:** высокая.

`generation_ai/api.py:52–54` и `workers/tasks.py:32–34` сначала commit, затем schedule. `services.py:168–175` держит pending ids в памяти и очищает список перед enqueue; worker registry `workers/arq.py:37–45` не содержит scanner due SQL rows. Crash/Redis failure оставляет durable pending/cooldown без job. Ручная повторная отправка может помочь, но автоматической recovery гарантии нет.

**Инвариант:** committed schedulable task eventually получает исполнителя. **Минимум:** SQL outbox или периодический re-enqueue due rows с idempotent job identity, метрикой lag и claim locks. **Тесты:** kill after commit, Redis enqueue exception, follow-up gap, последующий scanner запускает task ровно по бизнес-контракту.

### A05-09 — Medium — Rift snapshot flush очищает новую dirty-мутацию

**Статус:** подтверждённый failure window; не real-Redis repro. **Домены:** Rift, Redis+Mongo+PG. **Уверенность:** высокая по последовательности.

`rift/integrations/runtime.py:287–299` проверяет marker, вызывает flush_runtime_snapshot, затем clear_dirty. `infrastructure/rift/managers/session.py:115–125` пишет dirty/clean без generation compare. Изменение после snapshot capture до clear останется вне Mongo и без сигнала нового flush.

**Инвариант:** подтверждение сохранения версии G не очищает изменение G+1. **Последствие:** rollback прогресса к старому snapshot после Redis loss. **Минимум:** mutation+generation атомарно, compare-clear конкретной captured version; версия snapshot не должна регрессировать. **Тесты:** mutation barrier во время snapshot и два flush workers. Общая первопричина похожа на A03-10, но это самостоятельный Rift checkpoint path.

### A05-10 — Medium — Rift restore считает instance достаточным и перезаписывает живые sessions

**Статус:** подтверждённый дефект partial-restore contract с двумя проявлениями. **Домены:** Rift, Redis+Mongo+SQL membership. **Уверенность:** высокая.

`rift/integrations/runtime.py:172–180` при missing session вызывает restore по SQL membership. Restore `:245–250` возвращает True, если instance существует, не восстанавливая session; повторный require снова падает. Обратный случай: missing instance → Mongo snapshot → безусловный SET всех sessions (`:255–265`, `infrastructure/rift/managers/session.py:25–31`). Живая session S1 после snapshot S0 заменяется S0. Независимый TTL instance/session по 1h делает partial expiry достижимым.

**Инвариант:** восстановление отсутствующего компонента не игнорирует его отсутствие и не уничтожает более новое живое состояние. **Последствия:** недоступность run либо откат navigation/encounter progress; дублирование материальных rewards этим finding не доказано, поэтому Medium. **Минимум:** восстанавливать компоненты по identity/version, не перезаписывать newer live data; presence строить по фактически выбранным sessions. **Тесты:** session-only expiry; instance-only expiry при S0/S1; interruption restore между SETs; повтор восстановления.

### A05-11 — Medium — Archive reader обращается к несуществующему SQL payload

**Статус:** подтверждённый дефект; локальная ORM introspection выполнена. **Домены:** Combat results, Redis+PG+Mongo. **Уверенность:** высокая.

`combat/services/result_archive_service.py:147–153` делает `dict(row.finalization or {})`. `infrastructure/combat/models/finalization.py:12–35` имеет summary/pointer/mongo_status, но не finalization. Exception подавляется `result_archive_service.py:37–39`. Полный payload сохранён в Mongo (`combat/runtime/analytics/ingestion.py:102–136`), reader его не читает. Поэтому после Redis miss именно этот архивный fallback возвращает None даже при успешном archive persist.

**Инвариант:** сохранённый архив читается после удаления runtime/cache. **Последствие:** потеря доступа к отчёту после исчезновения Redis finalization и live runtime, не доказанная потеря самих rewards/данных Mongo. При ещё живом runtime существует отдельный fallback по истории (`combat/services/session_service.py:311–319`); он не исправляет SQL archive reader. **Минимум:** SQL identity/access lookup → Mongo full document; явный unavailable/error вместо silent missing. **Тесты:** persist → удалить Redis → read original actors/report/rewards; Mongo outage; missing SQL pointer. Независим от A03-12 (write/TTL race).

### A05-12 — Medium — Site refresh rotation имеет два commits

**Статус:** подтверждённый failure window. **Домены:** Site Auth, site PostgreSQL. **Уверенность:** высокая.

`frontend/features/auth/services/site_auth_service.py:124–127` удаляет старый refresh и затем вызывает create_tokens; `integrations/auth_persistence.py:67–74` коммитит delete и create отдельно. Сбой между ними оставляет пользователя без refresh. Параллельные запросы, прочитавшие старую строку до delete, также могут независимо создать новые tokens: SELECT не блокирующий, delete rowcount не проверяется (`repositories/token_repository.py:25–34`). Threshold 7 дней уменьшает частоту, не закрывает boundary.

**Инвариант:** смена credential либо сохраняет старый, либо фиксирует новый как одну операцию. **Последствие:** принудительный повторный вход после сбоя; конкурентные rotation требуют отдельной политики. Это persistence-находка, не самостоятельный security audit. **Минимум:** owner operation rotate в одной SQL transaction с lock/conditional consumption. **Тесты:** fail insert нового token после delete, два параллельных refresh на threshold, lost response retry.

### A05-13 — High — Site clean migration конфликтует с live ORM baseline

**Статус:** подтверждённый статический дефект migration chain; реальный upgrade не выполнялся. **Домены:** Site PostgreSQL/deployment. **Уверенность:** высокая.

`frontend/alembic/versions/0001_site_schema_baseline.py:12–24` импортирует текущие models и create_all. Текущая RefreshToken уже содержит token_hash и не содержит token (`frontend/features/auth/models/refresh_token.py:15–24`). Следующая migration `0002_security_baseline.py:22–31` безусловно ADD token_hash и SELECT старый token. На свежей базе baseline создаст token_hash, затем 0002 повторно добавляет ту же колонку. Аналогично current User имеет referral/email fields (`models/user.py:26–32`), а 0003/0004 снова их добавляют (`0003_referrals.py:29–39`, `0004_email_verification.py:21–26`).

**Инвариант:** история migrations воспроизводимо строит schema на пустой базе. **Последствие:** чистый deployment/восстановление на новую БД блокируется; состояние существующего production upgrade не устанавливалось. **Минимум:** зафиксировать historical baseline DDL и согласовать последующие revisions; не применять blind stamp/drop к существующим данным. **Тесты:** empty PG → upgrade head; historical schema → upgrade; повтор head; schema diff без приложения create_all. Отдельно game live baseline требует evolution test, но не получает дублирующий ID без конкретной deployed mismatch.

## 13. Непроверенные риски

### A05-14 — Medium — Конкурентное создание двух active Expedition

**Статус:** непроверенный риск. **Домены:** Expedition/Inventory, PG+Redis. **Уверенность:** средняя; SQL schedule обоснован, entrypoint serialization полностью не доказана.

`expedition/service.py:85–100` читает active run FOR UPDATE и создаёт новый при отсутствии. `repository.py:25–65` блокирует найденную строку, но пустой результат не даёт row lock; `models.py:37` имеет обычный index, не unique live-run constraint. При двух входах без внешней сериализации обе транзакции могут создать run, а Redis pointer last-write-wins (`service.py:357–370`); newest LIMIT 1 скрывает ранний run.

**Инвариант:** один live run на персонажа. **Последствия:** разветвление pending rewards/ownership. **Минимум при подтверждении:** partial unique по live statuses либо lock Character до проверки, обработка conflict. **Проверка:** две реальные SQL sessions с barrier после no-row SELECT; затем lifecycle обоих run и contents. До такого теста не объявляется наблюдавшейся потерей.

### A05-15 — Medium — Mongo chat append/seq не доказан конкурентно и повторно корректным

**Статус:** непроверенный риск real-Mongo поведения; известная неидемпотентная структура запроса. **Домены:** Chat, Mongo+PG. **Уверенность:** средняя.

`infrastructure/mongo/chat_buckets.py:48–86` читает count, строит message.seq, затем `$push` и `$inc`, возвращая post-update count как ссылку для SQL. Два writers могут взять одинаковый предварительный count. Нет message-id dedup, поэтому replay после Mongo success/SQL rollback может append-нуть второй экземпляр. Кроме того, initial update содержит `messages` и в `$setOnInsert`, и в `$push`: допустимость такого path combination должна быть проверена настоящим сервером, не fake.

**Инвариант:** SQL bucket/seq однозначно указывает исходное сообщение; один message_id не размножается при retry. **Последствия:** duplicate/неверный body либо write failure; точный серверный результат не измерялся. **Минимум:** атомарное выделение seq, проверенный server-valid update, dedup по message identity. **Тесты:** first insert настоящего Mongo, concurrent append, replay после commit failure, bucket boundary. Single worker max_jobs=1 уменьшает одну локальную гонку, но не доказывает отсутствие других writers/restart replay.

Дополнительные ограничения без нового дефектного ID: AOF/RDB и backup RPO неизвестны; rolling schema compatibility не проверена; Mongo snapshot version не CAS; Scenario resume completeness, Character hard-crash compensation, cross-store death/respawn и orphan generated bytes требуют отдельных fault tests. Наличие этих возможностей не означает уже произошедшую порчу данных.

## 14. Пересечения с аудитами №2–3

| Существующий ID | Независимая перепроверка persistence | Итог этого этапа |
| --- | --- | --- |
| A02-01 | Expedition пишет ItemPlacement/ResourceBalance/Character progression (`service.py:372–466`) | Ownership boundary остаётся; общую полезную SQL transaction при будущем разделении нельзя разрушать |
| A02-03 | AC raw schema/patches и dirty coordination (`actor_state/managers/session.py:119–171`) | Причина широкого read-modify-write surface; не новый ID |
| A03-01 | Finalizer → experience → expedition accumulate (`victory_finalizer_task.py:69–108`, `experience_finalizer.py:69–92`, `expedition/service.py:103–128`) | Duplicate XP остаётся подтверждённым |
| A03-02 | Inactive до side effects, exception caught (`victory_finalizer_task.py:69–71,133–134`) | Частичная finalization не repaired общим durable journal |
| A03-03 | Redis commit pipeline transaction=False (`infrastructure/combat/managers/session.py:594–650`) | Неатомарный contract подтверждён; crash test не выполнен |
| A03-04 | Create перезаписывает keys/очередь (`infrastructure/combat/managers/session.py:81–108`) | Duplicate creation остаётся destructive |
| A03-07 | Durability SQL commit до marker (`inventory/services/inventory_service.py:197–235`) | Window повторного урона предметам сохраняется |
| A03-09 | Snapshot read до lease; owner check отдельно от commit (`executor_task.py:59–71,118–127`, manager `:918–933`) | Fencing risk сохраняется, не повышен до воспроизведённого инцидента |
| A03-10 | Dirty generation pre-check/clear отдельно; sync SQL перед clear | Риск AC lost dirty сохраняется; A05-03/09 — независимые Inventory/Rift реализации |
| A03-11 | Rift completion раздельно instance/session/presence (`rift/integrations/runtime.py:479–498`) | Риск partial completion; A05-10 касается другого, restore path |
| A03-12 | Redis payload TTL, missing payload skip, Mongo→SQL persist (`finalization_persist_task.py:27–49`) | Archive recovery ограничена; A05-11 — новый reader mismatch |

Также A03-05 (late loot preorder) и A03-06 (support enqueue gap) согласуются с общей причиной «effect/transport boundary без durable replay», но не перенумеровываются. Имеющиеся проблемы не включены в число 13 новых подтверждённых находок.

## 15. Сильные решения

1. **Разделение site/game:** отдельные metadata/settings/migration trees предотвращают случайное представление site auth как игровой resource DB. Cross-side calls идут через API/contracts; общей SQL transaction между базами ожидать не следует.
2. **SQL unit of work и rollback:** contexts корректно отделяют auto/manual commit; repositories часто делают flush. Сохранять это и уточнять owner transaction вместо массового добавления commits.
3. **ItemPlacement PK и resource unique:** полезный фундамент conservation; точный source predicate и ledger дополняют его, не требуют нового storage engine.
4. **Expedition cashout в общей SQL границе:** предметы/ресурсы/progression/state закрепляются согласованно внутри PG. Перенос междоменных writes по A02-01 должен сохранить этот инвариант.
5. **Unsafe loot processed marker под run lock:** работающий локальный dedup для определённого lifecycle. Расширять покрытие safe/replay transitions, а не удалять механизм.
6. **NPC effect identity:** `npc/repositories.py:48–70` использует INSERT ON CONFLICT DO NOTHING с unique idempotency key. Это хорошая точка claim; атомарность конкретных внешних effects всё равно проверяется отдельно.
7. **Stable document identities и schema validation:** unique combat_id, Rift instance snapshot identity, AI task identity, generated actor schema/tier checks помогают безопасному повтору и явному отказу на несовместимой форме.
8. **Combat Lua/owner-aware release:** локальные queue transition и release не удаляют чужую lease. Это следует сохранить при добавлении fencing на commit.
9. **SQL-backed rebuild projections:** Inventory load из placements/wallet, Rift restore из snapshots и SQL membership — разумные границы. Исправлять partial restore/versions, не отказываться от runtime Redis.
10. **Commit до GenerationAI enqueue:** верное направление для видимости task worker-у; дополнить durable retry постановки. Смена порядка обратно на enqueue-before-commit ухудшит контракт.

Допустимые компромиссы: heavy Mongo documents, Redis runtime, bounded reply TTL, deferred analytics и non-transactional UI caches сами по себе не дефекты. Недопустимо лишь обещать больше durability/idempotency, чем обеспечивают конкретные owner operations.

## 16. Реестр находок

| ID | Severity | Статус | Краткий инвариант |
| --- | --- | --- | --- |
| A05-01 | High | Подтверждённый failure window | Safe loot ресурсы не создаются при replay |
| A05-02 | High | Подтверждённый дефект | SQL transfer проверяет точного source owner |
| A05-03 | Medium | Подтверждённый failure window | Inventory accepted action не стирается concurrent snapshot |
| A05-04 | Medium | Подтверждённый failure window | Corpse соответствует committed SQL и восстанавливается до expiry |
| A05-05 | High | Подтверждённый failure window | Pending Streams message имеет retry/dead-letter путь |
| A05-06 | High | Подтверждённый дефект | Chat checkpoint не пропускает failed body |
| A05-07 | Medium | Подтверждённый failure window | AI accepted task имеет durable input |
| A05-08 | Medium | Подтверждённый failure window | SQL pending eventually попадает в очередь |
| A05-09 | Medium | Подтверждённый failure window | Rift dirty clear относится только к captured version |
| A05-10 | Medium | Подтверждённый дефект | Partial restore не теряет newer live component |
| A05-11 | Medium | Подтверждённый дефект + ORM probe | Archive читается после Redis miss |
| A05-12 | Medium | Подтверждённый failure window | Refresh rotate — единая durable операция |
| A05-13 | High | Подтверждённый статический дефект | Clean site migration строит schema последовательно |
| A05-14 | Medium | Непроверенный риск | Один live Expedition на персонажа |
| A05-15 | Medium | Непроверенный риск | Chat Mongo message identity/seq корректны при replay/concurrency |

Классификация отражает последствия, а не число используемых хранилищ. План исправлений сознательно не составлен: минимальные направления и regression contracts собраны для общей стабилизации после всей серии аудитов.

## 17. Ограничения исследования

Не проводились production reads/writes, реальные migrations/restore, подключения к PG/Redis/Mongo/S3, сетевые fault injections, длительные concurrency/load tests. Не установлены фактические isolation level, Mongo URI concerns, Redis persistence/eviction runtime config, backup schedule и deployed revisions. Существующие пользовательские изменения сохранены; выводы относятся к рабочему дереву, не обязательно к production.

Async tests ограничены Windows event-loop setup; два прошедших sync tests не являются доказательством отказоустойчивости. Подтверждение большинства windows — прослеженный code path с точной границей сбоя. Статические выводы о migration/reader отличаются от сценариев, для которых нужны реальные interleavings. Не делается вывод о полной корректности всех неупомянутых feature paths. В частности, arena rating write API имеет признаки отсутствия общей replay защиты, но runtime caller применения match result в рассмотренном пути не установлен — новый defect ID не присвоен.

Никакие fixes и обновления skills не применены; operational alignment не изменился. Единственный создаваемый артефакт этого аудита — данный отчёт.

### Persistence Health Summary

| Измерение | Оценка и доказательная граница |
| --- | --- |
| Data integrity | **Требует стабилизации:** SQL source conservation нарушается safe loot replay/owner checks; PK и row locks полезны, но недостаточны |
| Transaction safety | **Локально хорошая, сквозная частичная:** UoW/rollback есть; ранние commits и внешние эффекты разделены |
| Idempotency | **Неравномерная:** unsafe run/NPC/stable upserts против отсутствия safe claim/XP/global finalization ledger |
| Redis state consistency | **Уязвима к interleaving и partial expiry:** dirty-only truth, nontransactional pipelines, snapshot overwrite, отсутствие fencing |
| Cross-store recovery | **Неполная:** Rift restore и Combat archive reader имеют конкретные дефекты; status flags не всегда содержат repair payload |
| Event delivery reliability | **Недостаточно подтверждена:** локальный Streams PEL не reclaim-ится; retention и lost replies требуют business dedup |
| Migration safety | **Есть подтверждённый дефект clean site upgrade:** live ORM baseline конфликтует с последующими revisions; rolling не проверен |
| Backup/restore readiness | **Не подтверждена:** volumes существуют, executable backup/restore gate и drill в рассмотренных файлах не найдены |
| Testability | **Хорошая изоляция unit, недостаточные доказательства storage guarantees:** real-PG/RedisJSON/Mongo fault suite необходим; текущий async запуск заблокирован setup окружения |
