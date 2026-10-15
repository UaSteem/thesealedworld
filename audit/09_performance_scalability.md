# Аудит 09/10 — Performance, Scalability и Resource Efficiency

Дата: 09.10.2026. Объект: текущее рабочее дерево Sealed World / TurnBasedMMORPG, включая уже существующие незакоммиченные изменения. Режим: доказательный аудит без исправлений production code, конфигурации, схем и skills. Production, реальные Redis/PostgreSQL/MongoDB и AI-провайдеры не подключались.

## 1. Основной результат

**Оснований считать язык Python главным ограничением системы нет.** Сначала масштабирование ограничивают объём повторно передаваемых данных, последовательные обращения к Redis, фиксированная скорость архивирования чата и процессная модель WebSocket. CPU-участки существуют, но их нужно измерять отдельно от транспорта и очередей.

Наиболее существенные подтверждённые ограничения:

1. Combat на каждом batch с логами читает и сериализует всю накопленную историю. При одинаковом приросте журнала суммарная работа за бой растёт квадратично с числом batch.
2. Проверка восстановления vitals запускается каждые две секунды и может прочитать все AC-документы последовательными Redis-командами; `limit=100` ограничивает число найденных кандидатов, а не объём обхода.
3. Архиватор чата берёт только 500 сообщений с каждого потока раз в десять минут. Его номинальный потолок на один поток — 3000 сообщений/час, даже при мгновенных базах.
4. WebSocket-рассылка локальна одному процессу и последовательно ожидает каждого получателя. Добавление chat-процесса без изменения доставки разделит аудиторию комнат.
5. Повторная Character sync после очистки dirty-маркера запускает полное сохранение; middleware может поставить несколько таких задач до первого flush.

Это реальные свойства кода, а не доказательство уже случившейся деградации production. **CCU, RPS, p95/p99 и максимальное число игроков установить по этому аудиту нельзя.** Нет production traces, размеров реальных документов, сетевых RTT, EXPLAIN/ANALYZE и измерений железа.

Положительная основа: отдельные очереди и процессы для combat, system, GenerationAI и административных симуляций; Redis pipelines в нескольких горячих путях; пакетные SQL-чтения inventory; кеш готовых actor stats; ограничение волн боя; ограниченная история HTTP-чата; повторно используемый frontend HTTP client. Перенос всей системы на другой язык и контейнер на каждый домен не обоснованы.

## 2. Метод и границы доказательств

Применены AGENTS.md, cost-aware-delegation, project-skill-loader, ask-before-editing, project/backend/quality и специализированные combat/rift/frontend skills с относящимися к задаче references. Три read-only исследования покрыли combat, Rift/World/GenerationAI и frontend/chat; ведущий проверил инфраструктуру, Character/Inventory/Loot и ключевые выводы помощников по текущим исходникам.

Аудиты `01_project_inventory.md`, `02_architecture_boundaries.md`, `03_combat_runtime.md`, `04_rift_world_generation.md`, `05_persistence_consistency.md` использованы для навигации и отделения уже известных consistency-дефектов. В `audit/` результатов №6–8 на момент проверки не найдено. Graphify не использовался. Для реально делегированных операций прочитаны установленные `codex_platform`, `arq`, `redis`, `sqlalchemy` в `.venv/Lib/site-packages`; тождественность production-окружения этому окружению не проверялась.

Обозначения:

- **Факт** — текущий путь исполнения или воспроизведённое поведение метода.
- **Следствие** — строгая оценка количества операций/объёма; не измеренная latency.
- **Риск** — условный эффект, для оценки которого нужны профиль или нагрузка.
- **RT** — последовательный клиентский обмен с Redis. Pipeline с 100 командами считается одним execute/RT, но остаётся 100 серверными командами. Здесь не считаются TCP-пакеты, connect/TLS/retries и служебные команды протокола транзакции.

Пути и строки ниже относятся к текущему checkout. Severity отражает масштаб последствий при достижении описанной нагрузки, а не частоту инцидентов.

## 3. Фактическая модель нагрузки

Параметры: `P` — число сохранённых активных персонажей; `N` — actors в бою; `B` — AI actors; `I` — рассчитанные interactions; `E` — effects/modifiers; `H` — размер накопленной истории; `K` — предметы персонажа; `V,A` — узлы и рёбра Rift; `S` — все Rift sessions; `C` — подписчики комнаты; `M` — размер сообщения. Частоты игровых действий неизвестны.

| Нагрузка / известная частота | CPU, память и сериализация | I/O и рост |
| --- | --- | --- |
| HTTP / SSR, по действиям пользователя | DTO-validation, преобразование view models и Jinja; память на ответ | Site SQL/auth + последовательные backend HTTP; затем Redis/SQL по домену. Зависит от request rate, нет универсального числа запросов |
| WebSocket connect, один раз при соединении/переподключении | Registry и подписки O(числа topics), сериализация history | Проверка session lock, AC, chat state; загрузка DM tail. Память процесса O(connections + memberships + transport buffers), bytes/connection не измерены |
| Combat batch/exchange | O(I × работа snapshot/effects) + O(N × actor payload) + O(H) логов на commit | Full-context Redis load, action batch, commit, TTL, support/AI enqueue; точный участок в §5 |
| Один AI turn | Полный контекст N actors, validation, затем decision/scoring | Минимум `2N+2` Redis-команды, 2 RT только на context load. При B ботах повторяется B раз |
| Simulation/training, по admin request | Повторные in-memory бои; generations × candidates × scenarios × exchanges | Отдельная очередь и worker; SQL/Mongo результатов, часть тестовых окружений in-memory. Не production combat throughput |
| Rift generation, при создании instance | Bounded grid 16–49 cells; повторные BFS/branch scans; размер результата DTO O(V+A) | Создание Redis instance/session и membership; snapshot — последующий dirty flush. Не генерируется весь мир на каждом ходе |
| Rift travel tick/action, по запросам клиента | Копирование/validation и полная сериализация instance O(V+A) | AC + session + instance read, минимум две полные записи + два EXPIRE; дополнительные presence/dirty/response операции |
| World navigation | Работа с текущей локацией и соседями; не глобальный pathfinding на каждый шаг | Redis location/presence + AC update, events. Большое количество людей в одной локации увеличивает membership payload |
| Inventory open/action | Full DTO/view/projection O(K), полный JSON session при мутации | Warm path тоже читает SQL wallet; cold path один JOIN для всех items; session SET + EXPIRE, AC projection, events |
| Character sync, после dirty HTTP requests | Full AC validation; selective writes только при сохранённом marker | AC GET; SQL expedition lookup + selected repositories; clear dirty. Повтор без marker делает full sync |
| Loot generation/claim | CPU generation по числу предметов; claim по corpses/resources | Claim: отдельная SQL transaction на corpse, batched item UPDATE, по одному locked SELECT на resource; Redis cleanup после SQL |
| GenerationAI, по backlog | Provider I/O; image decode/resize/WEBP — sync CPU и пик памяти в изображениях | SQL claim/lock удерживается через provider, Mongo/asset writes; max 5 jobs на worker |
| Chat message | Один JSON для topic, O(C) send; browser хранит весь полученный список | Fan-out → XADD одного buffer stream. O(C×M) исходящих байтов, persistent buffer до примерно 5000 entries/topic |
| Chat archive, каждые 10 минут | JSON + обработка до 500 records/topic за запуск | Все stream keys SCAN, GET cursor + XREAD; последовательные PG/Mongo на сообщение, SET cursor для непустого batch |
| Vitals refresh, каждые 2 секунды | DTO каждого просмотренного AC; до 100 кандидатов | До P последовательных full JSON.GET плюс SCAN; notice вызывает новые HTTP-запросы статуса |
| System dirty sweeper, каждые 3 минуты | Поиск dirty inventory/knowledge/Rift, до 100 результатов каждого вида по default | SCAN + чтения документов + последовательные enqueue; обработка flush конкурирует с loot/sync в system queue |
| World bootstrap, при старте backend | Static seed + загрузка всех active nodes, сборка projection O(nodes) | SQL seed/upsert/read и единый Redis pipeline; startup cost, не per-player tick |

Доказательства расписаний: `src/backend/features/system/workers/arq.py:33`, `:62`; `src/backend/chat/workers/archive.py:215`. Публикуемый vitals notice является сигналом повторно получить HTTP fragment: `src/backend/realtime/integrations/notice_publisher.py:48`, `src/backend/features/system/workers/tasks/vitals_regen.py:43`.

## 4. Реестр подтверждённых ограничений

### A09-01 — High — история боя повторно читается и записывается целиком

`src/backend/infrastructure/combat/managers/session.py:606` вызывает `_merge_logs_by_turn`; `:807` читает HGETALL и декодирует все turns; `:828` добавляет новые записи и заново JSON-serializes все старые; `:629` пишет весь mapping обратно HSET.

На один commit это O(H) read/serialize/write; при T последовательных batch с одинаковым приростом журнала — O(T²) суммарного объёма. Сортировка turn keys добавляет работу поверх копирования. Redis hash не помогает, поскольку код не ограничивает чтение/запись затронутым turn. Растут network bytes, временные Python objects и Redis service time, даже если сам exchange между двумя actors остаётся небольшим.

Проба реальных методов с fake Redis: 100/500/1000 turns по пять синтетических записей дают примерно 71/355/710 тысяч байтов JSON values на очередной write; время только Python-сборки в основном зафиксированном прогоне 0,982/3,077/6,195 ms (§10). Это не end-to-end latency.

### A09-02 — High — частый глобальный AC scan и неполная fairness

`src/backend/infrastructure/actor_state/managers/session.py:520` начинает SCAN с cursor=0, последовательно читает `$` каждого AC (`:535–537`), проверяет state/vitals и прекращает после 100 подходящих. Cron — каждые две секунды. Presence соединения не проверяется: AC может жить шесть часов (`:41`), поэтому здесь `P` — сохранённые AC, а не гарантированно подключённые игроки.

Если кандидатов нет, обход всё равно полный. Если первые 100 сохраняют неполные vitals и порядок обхода стабилен, следующие проходы снова выбирают их. Cursor/rotation между запусками не сохраняется. Redis SCAN не гарантирует фиксированный порядок, поэтому утверждение — риск starvation, а не обязательная вечная блокировка всех остальных.

Проба исходного метода на 5000 полностью восстановленных fake AC: **50 SCAN + 5000 JSON.GET, 0 кандидатов** при искусственных страницах ровно по 100. Реальный SCAN count — hint, поэтому реальное число SCAN не обязано быть 50. При 1000/5000 неполных AC второй проход снова выбрал тот же первый набор 100 в стабильном fake. Ограничение чтений воспроизведено без сети.

### A09-03 — High — архивирование чата имеет низкий фиксированный потолок

`src/backend/chat/workers/archive.py:35–59` делает **один** XREAD с `_BATCH_SIZE=500` на stream за invocation, без drain loop. Cron `:215–223` — раз в десять минут, max_jobs=1. При успешно завершающемся каждом запуске номинальный максимум — 500/600 ≈ **0,833 сообщения/с на topic**. Это арифметический потолок конфигурации, не измеренная производительность базы.

Если приходит больше 500 сообщений за десятиминутный интервал, backlog этого topic устойчиво растёт. Redis buffer ограничен приблизительно 5000 entries (`src/backend/chat/services/message_service.py:45–52`, `src/backend/config/settings.py:85`); в итоге недоархивированные entries могут быть trimmed. Более быстрый PostgreSQL не снимает этот потолок. Если обработка многих topic не укладывается в период, эффективная пропускная способность ещё ниже.

Все streams обходятся целиком (`archive.py:116–124`), сообщения пишутся последовательно. Пустой stream стоит GET cursor + XREAD, непустой дополнительно SET cursor. Ранее найденный A05-06 про продвижение cursor после ошибки — отдельный consistency-дефект, здесь не считается новой находкой.

### A09-04 — High — процессный предел и задержка за медленным получателем WebSocket

`src/backend/chat/services/connection_manager.py:19–23` хранит подписчиков только в памяти процесса. `:76–88` выполняет `await send_text` последовательно. `src/backend/chat/services/message_service.py:39–52` ждёт broadcast до XADD buffer. Следовательно, медленный socket задерживает следующих подписчиков в этом broadcast и запись отправленного сообщения в buffer; это не обязательно блокирует весь event loop, но удерживает конкретный message workflow.

Проба реального `broadcast_topic`: до освобождения первого fake socket второй send даже не начинается (§10). Application-level bounded outbound queue, timeout/drop policy на получателя в этом методе отсутствуют.

Текущий `deploy/compose.game.yml:81–108` запускает один chat uvicorn. Если просто добавить второй процесс/реплику, комнатная рассылка не попадёт к подписчикам другого процесса: buffer используется для архива, а не межпроцессной live-доставки. Это подтверждённый барьер такого способа масштабирования, не заявление о уже сломанной текущей одно-процессной установке.

### A09-05 — Medium — combat повторно загружает весь бой для каждого AI и сохраняет всех actors

`src/backend/features/combat/integrations/session_integration.py:339–390` читает meta, затем строит snapshots всех actors. `src/backend/infrastructure/combat/managers/session.py:551–557` отправляет `2N` JSON.GET и LRANGE всей action queue в одном pipeline. Каждый `ai_turn_task` делает такой load (`src/backend/features/combat/workers/tasks/ai_turn_task.py:51`). Для B ботов один цикл решений имеет O(BN) команд/payload/validation; при B≈N появляется квадратичный рост по составу боя.

Executor commit также serializes каждый actor (`session_integration.py:416–440`), независимо от того, участвовал ли он в batch. На actor идут семь mutation commands для текущего payload; затем обновляются TTL всех actors/moves. Детальный подсчёт — §5. Pipeline уменьшает RT, но не эту работу Redis и не bytes.

Лишний LRANGE результат `global_queue` сразу пропускается при сборке BattleContext (`session_integration.py:360–362`), а executor читает отдельный action batch. Это лишняя передача, но штатный collector ограничивает очередь порогом 50, а не допускает заведомо бесконечный Q (`runtime/processors/collector.py:13`, `:54–56`).

### A09-06 — Medium — дубли sync превращаются в повторные полные SQL writes

Middleware после каждого запроса с character id проверяет dirty и enqueue без стабильного job id (`src/backend/core/middleware.py:30–54`). Пока первая задача не очистила marker, следующие запросы способны поставить новые задачи. ARQ при отсутствии `_job_id` генерирует UUID (`.venv/Lib/site-packages/arq/connections.py:148`).

`src/backend/features/character/integrations/system_integrator.py:117–120` возвращает `dirty_targets=None` и для отсутствующего/чистого marker. В `:55–83` это означает полное сохранение, а не skip. Проба исходного метода: первый dirty target `character` вызвал только character write; повтор после clear вызвал character, attributes, skills, progression и symbiote. Это вызовы repositories, не измеренное число SQL statements. На unsafe expedition часть writes намеренно пропускается.

Здесь performance amplification отделено от ранее отмеченных гонок dirty generation/CAS. Увеличение system concurrency само по себе не убирает лишнюю работу.

### A09-07 — Medium — Rift tick переписывает instance, flush обходит чужие sessions

`src/backend/features/rift/services/player_service.py:218–228` сохраняет полный instance и session при runtime update. Stores делают JSON.SET `$` и отдельный EXPIRE (`src/backend/infrastructure/rift/managers/instance.py:25–28`, `session.py:25–45`). Для базовой пары записей это **четыре команды и четыре последовательных RT**. Instance передаётся целиком даже для персонального изменения travel; рост при увеличении карт/частоты — O(players × ticks × instance bytes).

Flush одного run вызывает snapshot instance (`features/rift/integrations/runtime.py:287–298`), который ищет sessions через `list_by_instance` (`:182–217`). Реализация `infrastructure/rift/managers/session.py:146–162` сканирует все session keys и GET-ает документы до фильтра по instance. При редких совпадениях один flush стоит O(S) чтений всех Rift sessions. Несколько dirty участников одного instance могут повторно создать общий snapshot: coalescing по instance в sweeper нет (`system/workers/tasks/dirty_sweeper.py:71–78`).

Текущие presets малы (§8), поэтому High для этого пути без профиля не назначается. Snapshot содержит один instance плюс sessions/presence, а не доказанную отдельную полную копию графа на каждого участника.

### A09-08 — Medium — Mongo chat возвращает растущий bucket после каждой записи

`src/backend/infrastructure/mongo/chat_buckets.py:59–83` делает find_one_and_update с `ReturnDocument.AFTER` **без projection**, затем использует только message_count. В ответе приезжает и весь массив messages. Для bucket с n сообщениями сопоставимого размера суммарно передаётся O(n²×M) за его заполнение; текущий nominal cap — 1000 сообщений (`:11`, `:53`, `:84`). Это ограниченная, но доказанная write/read amplification.

Кроме того, каждый append ищет shard с нуля (`:46–55`), проверяя и обновляя уже закрытые shards; максимум 100 попыток. History reader группирует refs по bucket, но затем последовательно делает find_one и получает весь messages array (`:90–108`). Это не SQL N+1 на каждый message: это до одного Mongo query на каждый уникальный bucket страницы. При редких refs к большим buckets передача значительно больше самой страницы.

### A09-09 — Medium — GenerationAI удерживает SQL connection/transaction через долгую внешнюю работу

`src/backend/features/generation_ai/repositories.py:132–157` claim-ит row `FOR UPDATE SKIP LOCKED`, flush-ит, но не commit-ит. `services.py:81–105` затем выполняет provider generation и apply_result. Commit находится только после `process_task` в `workers/tasks.py:20–35`.

На каждый активный job SQL transaction и connection остаются занятыми через AI I/O, обработку assets и Mongo. При `max_jobs=5` возможно до пяти таких транзакций на worker. Изоляция worker защищает API event loop, но не общие ресурсы PostgreSQL. Влияние на lock wait/vacuum/pool — риск, для которого нужен профиль; «SQL запрос медленный» здесь не утверждается. SKIP LOCKED предотвращает ожидание занятого task при claim, но не сокращает время уже удерживаемого connection.

### A09-10 — Medium — image normalization синхронно занимает GenerationAI event loop

`src/backend/features/generation_ai/integrations/codex_ai_executor.py:90–98` вызывает обычную функцию нормализации из async path. `image_normalization.py:42–58` выполняет PIL load/convert/resize и WEBP encode `method=6`. Во время этого вызова другие coroutines данного worker не получают управление; `max_jobs=5` не означает пять CPU-ядер.

Decode также держит исходные bytes, pixel buffers, преобразованное изображение и output. Память зависит от распакованных dimensions, а не только размера загруженного файла. Функция имеет быстрый возврат для уже подходящего WEBP без resize (`:25–34`), поэтому CPU-стоимость не приписывается каждому job безусловно. Дополнительная одно-проходная синтетика помощника приведена отдельно в §10.

### A09-11 — Medium — browser chat не ограничивает историю живой вкладки

В `src/frontend/templates/shared/chat/main.html:6–13`, `:176–200`, `:269` сообщения добавляются в массивы каналов без найденного удаления старых entries. Видимые списки выводятся целиком через x-for (`:921–1035`). При длительной открытой вкладке JS memory растёт с количеством принятых сообщений, а DOM активного канала — с длиной списка. Ограничение backend history page не ограничивает накопление live messages. Browser heap/DOM profiling не выполнялся, конкретный объём RAM и Core Web Vitals неизвестны.

## 5. Combat: стоимость операции и готовность вычислительного ядра

### 5.1. Команды и реальные последовательные ожидания

Подсчёт ниже — на выбранные методы, **не на весь HTTP move**; lifecycle, locks, enqueue, callbacks и conditional branches добавляют операции.

| Участок | Redis commands | RT / ожидания |
| --- | --- | --- |
| Load BattleContext | 1 meta + 2N JSON.GET + 1 LRANGE = `2N+2` | 2: meta, затем pipeline |
| Read action batch | 1 LRANGE | +1 |
| Commit actor state, обычный actor payload | `7N` mutations | В одном общем commit pipeline |
| Логи в commit | 1 HGETALL + 1 HSET при наличии логов | HGETALL добавляет отдельный RT; HSET входит в pipeline |
| Прочие commit операции | LTRIM; optional analytics HSET, dead-target EVAL, target returns ARRAPPEND, meta HSET | В том же pipeline; число зависит от результата |
| TTL после commit | 1 meta HGETALL + `5+2N` EXPIRE | Ещё 2 RT: meta, TTL pipeline |

Таким образом, commit с логами — **4 RT** внутри manager: logs read → commit pipeline → meta read → TTL pipeline. Базовая load+batch+commit последовательность — **7 RT**, до учёта lock и остальной orchestration. Нельзя превращать `7N` mutations в `7N` сетевых ожиданий: они pipelined. Нельзя и называть pipeline одной Redis-командой.

Для N=2/10/50 только загрузка контекста содержит 6/22/102 команды, сохраняя два RT. Только actor mutations плюс TTL EXPIRE — 23/95/455 команд, без logs/meta/actions. Это арифметика исходного кода, не benchmark Redis.

Lua на queue/moves и pruning сокращает переходы и обеспечивает атомарность отдельных действий, но работа скрипта всё равно выполняется Redis; большие JSON decode/loops внутри Lua нельзя считать бесплатными. См. `infrastructure/combat/managers/session.py:474–545`, `:635`. Pipeline commit не является whole-exchange atomic commit; этот correctness-вопрос уже описан A03-03.

### 5.2. CPU, actors, effects и interactions

`CombatResolver` делегирует `runtime/engine/resolver/orchestrator.py:38–73`: последовательность hit/crit/evasion/parry/block/damage/healing имеет early returns. Для фиксированного набора правил чистая арифметика одной пары не сканирует всех игроков мира.

Реальная стоимость выше арифметики: context construction, effects/triggers, cached/dirty stats, result facts, logs и snapshots. `runtime/engine/stats_engine.py:74–86` повторно использует stats, если они есть и не dirty; dirty вызывает полный recalculation. Следовательно, неправильно утверждать полный recalculation для каждой пары безусловно.

`runtime/processors/executor.py:224–252` ограничивает waves тремя, но внутри каждой создаёт глубокие копии source/target для runnable interactions. Память пика — исходный BattleContext плюс snapshots и results текущей wave; примерно O(N×actor_size + wave_interactions×actor_size + logs/results). Размер actor растёт с effects, loadout, modifiers, skills и explanation. Periodic effects и cleanup также обходят effects (`:592–628`). Area targets и ответные взаимодействия увеличивают I; ограничение числа waves не равно фиксированному числу interactions.

`CombatPipeline.calculate` объявлен async, но внутри `runtime/engine/pipeline.py:32–82` нет await. `asyncio.gather` в executor поэтому не делает расчёт параллельным на CPU и не позволяет прервать длинный calculate до его возврата. Это локальный CPU-bound участок combat worker, а не доказанная блокировка API-процесса.

### 5.3. AI, support analytics и finalization

AI сначала загружает общий бой, затем выбирает действие. Поэтому при росте команды сначала стоит измерять hydration/validation vs scoring; сам decision algorithm не доказан главным bottleneck. Policy и детерминированный pipeline пригодны для изолированных in-memory benchmarks; вход должен фиксировать actors/effects/candidate moves и seed.

Support analytics вынесены из immediate result path в ARQ, но находятся в **той же combat queue**, что executor/AI/finalizer (`workers/arq.py:25–33`). На каждый support result создаётся DTO/fact и выполняется append (`runtime/support/result_support_task.py:15–25`). Это снижает работу непосредственно внутри exchange, но не её суммарную стоимость и не гарантирует latency при заполнении очереди support jobs.

Finalizer собирает весь combat document; persistence worker делает Mongo upsert и SQL finalization/ingestion (`workers/tasks/finalization_persist_task.py:28–44`). `infrastructure/mongo/combat_documents.py:25–35` на каждый upsert сначала выполняет пять create_index calls и возвращает полный stored document. Уже существующие индексы не обязательно перестраиваются; подтверждена дополнительная коммуникация, а не пять rebuild. Финальный document и аналитика растут с историей боя. Фактический максимальный BSON размер не измерен; приближение к лимиту документа нужно проверять размером serialization, не числом turns на глаз.

### 5.4. Симуляции и training

Отдельная очередь `tbmmorpg:arq:combat_ai_simulation`, worker max_jobs=1; timeouts: live simulation 180 s, synthetic training 900 s, battle/family training 2400 s (`workers/ai_simulation_arq.py:21–32`). Compose включает этот worker отдельным profile (`deploy/compose.game.yml:163–179`). Если profile выключен, enqueue не означает наличие исполняющего consumer; actual deployment не проверялся.

Training растёт как generations × candidates × scenarios × выполненные exchanges (`services/ai_simulation_service.py:1073–1095`, `:1289–1326`). Synthetic training использует to_thread (`workers/tasks/ai_simulation_task.py:203–216`); это освобождает event loop, но не обещает multicore acceleration Python CPU под GIL и не гарантирует остановку underlying thread по cancellation. Battle training не имеет такого offload. Раздельный процесс уже защищает короткий live combat от прямого CPU-blocking симуляцией; общий host CPU/Redis/DB остаётся общим.

## 6. Redis: ресурсная модель и транспорт

### 6.1. Commands, payload и latency

AC `patch_fields(k)` — k JSON.SET + EXPIRE в одном pipeline (`actor_state/managers/session.py:119–128`). `mark_dirty` добавляет отдельный GET marker и pipeline из SET marker + EXPIRE. Полная замена Inventory — JSON.SET + EXPIRE в два последовательных ожидания (`inventory/managers/session.py:25–28`). Dirty inventory scan читает и Pydantic-validates каждый полный документ до обнаружения dirty (`:64–78`).

Loot generation обходит monsters и сохраняет corpses последовательно (`features/loot/services/loot_service.py:59–108`). Выпавший equipment запрашивается через отдельный Items request/reply с timeout=15s (`:181`, `:235`; `features/loot/integrations/loot_integration.py:99–136`); это добавляет event/worker wait, а не только CPU выбора loot. `infrastructure/loot/managers/loot_manager.py:50–55` на corpse делает четыре последовательные команды: JSON.SET, EXPIRE, SADD location index, EXPIRE index. Чтение loot локации — один SMEMBERS и затем по одному последовательному GET каждого corpse (`:115–131`), O(числа corpses), включая ещё не видимые. Частота этого пути и размеры corpse не измерены; добавлять его к каждому combat exchange безусловно нельзя.

При кросс-VPS размещении задержка последовательной цепочки примерно включает сумму её RT, передачу bytes, Redis service time и ожидание очереди. Локальные времена §10 **не включают ни один сетевой RTT**. Выгодность batching определяется отдельно от JSON size: один огромный pipeline может уменьшить RT и одновременно увеличить peak memory и задержку остальных клиентов.

### 6.2. Streams и request/reply

`core/containers/redis.py:58–69`, `:150–162` по default создаёт десять consumer groups одного game stream. Каждая группа получает каждое stream entry, даже если её dispatcher не имеет handler для типа; это O(groups × event rate) decode/dispatch/ACK. Processor обрабатывает records одного consumer последовательно (`.venv/Lib/site-packages/codex_platform/streams/processor.py:180–218`). Долгий handler удерживает очередь своей группы, а выполняющийся в backend процессе sync CPU занимает его event loop.

Обычный `GameEventProducer.publish`: XADD, затем отдельный XTRIM — две команды/RT (`core/bus/producer.py:21–22`, `:60–67`). Default maxlen=10000 (`config/settings.py:81`). Request path делегирует raw producer, который делает XADD + BRPOP и не вызывает этот trim (`core/bus/producer.py:28–39`; dependency `streams/producer.py:99–105`). Reply — LPUSH + optional EXPIRE. BRPOP удерживает connection на время ожидания ответа. Если идут только request-события без иных trimming publishers, данный путь сам retention не обеспечивает; в смешанной нагрузке последующие publish могут его ограничить.

Количество bytes на stream entry не фиксировано. Maxlen ограничивает entries, не память в байтах; pending/replies, ARQ job keys и serialized payload также занимают Redis. Отсутствие reclaim уже отражено A05-05; повторный audit не выдаёт это за новый performance-дефект.

### 6.3. Memory и горячие ключи

Оценка структуры, без выдуманных MB/player:

`Redis memory ≈ AC(P×ac_bytes) + Inventory(open_sessions×inventory_bytes) + Combat(actors + moves + targets + logs + analytics) + Rift(instances + sessions + presence) + stream entries + PEL + ARQ backlog/results + chat buffers + connection/allocator overhead`.

Параметр `open_sessions` включает TTL-сессии, не только видимые окна. AC default TTL=6h, combat active TTL=1h/history=24h, Rift instance TTL=1h; refresh продлевает lifetime. TTL ограничивает время неиспользования, но не объём живого длинного боя. Chat XADD ограничивает число сообщений topic; в просмотренном message/archiver path не установлен автоматический TTL удаления самого buffer и cursor, поэтому число когда-либо созданных topics важно отдельно от CCU.

Горячие ключи: общий game stream, Redis queue sorted sets ARQ, global chat buffer, per-combat logs/targets, часто меняемый shared Rift instance. Персонажи распределены по отдельным ключам, но один Redis instance по compose всё равно обслуживает общую работу. `deploy/compose.infra.yml` не задаёт явного application maxmemory/eviction budget; actual server config неизвестен. Нельзя назвать Redis «только cache»: до persistence в нём есть авторитетное runtime state.

## 7. PostgreSQL/MongoDB: доказанные формы запросов, не выдуманная медленность

| Путь | Фактический query pattern / индексы | Оценка и предел вывода |
| --- | --- | --- |
| Inventory cold load | Один JOIN ItemInstance/ItemPlacement с holder filters, ORDER BY position/name/id, без LIMIT (`features/inventory/repositories/items.py:19–39`) | Нет N+1 на item в этом read. Загружается O(K) rows и JSON fields. Large inventories увеличивают bytes/memory/sort; query plan не измерен |
| Inventory warm open/action | get_wallet SQL даже при Redis session hit, optional expedition wallet (`services/inventory_service.py:134–166`) | Redis session не делает окно полностью SQL-free. Проекции/view/session сериализуются целиком |
| Inventory flush/durability | Сначала batch SELECT placements или instances IN(...), затем ORM updates/flush (`repositories/items.py:70–109`) | O(K) materialization. Нельзя по одному flush приписать один SQL UPDATE или K RT: это зависит от ORM batching/изменённых rows |
| Item indexes | PK item_id; отдельные indexes holder_type, holder_id, storage_type (`features/items/models/instance.py:64–83`) | Возможность composite index надо проверять EXPLAIN на реальном распределении; текущие индексы не доказывают full scan |
| Loot claim | Transaction на corpse, batched placement UPDATE, R отдельных locked resource SELECT (`features/loot/workers/tasks/loot_claim_task.py:196–274`, `:303–320`) | O(corpses + resources) запросов, ресурсы читаются последовательно. Wallet/run locks сериализуют конфликтующие действия одного владельца |
| ResourceBalance | Unique holder_type/holder_id/storage_type/resource_key (`features/items/models/instance.py:85–100`) | Поддерживает часть holder lookup. Claim не фильтрует storage_type; selectivity и реальный план неизвестны |
| Character | Expedition lookup + selected snapshot/upsert writes; skills записываются одним multi-row UPSERT (`features/character/integrations/system_integrator.py:42–114`, `features/character/repositories/skill.py:26–40`) | Full-sync дубли подтверждены A09-06; N+1 по каждому skill в этом upsert нет |
| GenerationAI | By-id indexed claim с SKIP LOCKED; много отдельных status/priority/entity indexes (`features/generation_ai/models.py:13–42`) | Риск долгой transaction A09-09. Цена каждого индекса на writes реальна, но «индексов слишком много» без workload не утверждается |
| Chat history | SQL LIMIT≤100, `(thread_id, created_at)` index (`chat/models/message.py:66–70`, `chat/repositories/message_repo.py:111–127`) | Размер страницы bounded; затем Mongo bucket hydration A09-08. DM session list без pagination (`message_repo.py:64–78`) растёт с историей контактов |
| Combat Mongo | combat_id unique, finished_at и composite dimensions; full document upsert/read (`infrastructure/mongo/combat_documents.py:18–35`) | Индексируемый lookup; rollup `find` возвращает полные documents, limit=1000 (`:42–69`), поэтому память зависит от размера боёв, не только limit |
| Chat Mongo | `_id` lookup, thread/bucket/scope indexes, buckets nominal ≤1000 messages | Bounded count не равен bounded BSON bytes; нет доказанного production document overflow. Retention по времени отсутствует в перечисленных create_index, TTL policy надо задать отдельно при проектировании |

`src/backend/core/database/session.py:11` создаёт async engine с pre_ping, но без явных pool_size/max_overflow. Установленная SQLAlchemy имеет defaults 5+10 и timeout=30s (`.venv/Lib/site-packages/sqlalchemy/pool/impl.py:74–76`). Это **на engine/process**, не один глобальный pool всей системы. Репликация API/workers умножает потенциальные connections. Site имеет отдельный engine, даже если SQL server общий. Server max_connections и фактический checkout wait не измерены.

Backend Redis client создаётся без явного max_connections (`core/containers/redis.py:79–82`); установленная redis asyncio pool подставляет `2**31` как effectively unbounded default (`.venv/Lib/site-packages/redis/asyncio/connection.py:1054–1063`), если URL не переопределяет настройку. Mongo provider переиспользует lazy AsyncMongoClient, передавая server selection timeout (`infrastructure/mongo/client.py:25–33`); явных application pool budgets в этом конструкторе нет. URI/server overrides не исследовались. Это **не доказанное исчерпание пулов**, а незаданный/непроверенный capacity contract.

## 8. Rift, World и экспериментальный Hex

Действующий Rift использует небольшие presets 4×4…7×7, с active nodes 12…25 (`features/rift/resources/json/zone_assembly_presets.json:5`, `:77`, `:145`, `:213`). Все четыре выбирают `main_path_branches` (`:37`, `:105`, `:173`, `:241`). Этот путь возвращается из `features/rift/runtime/generation/zone_instance.py:306–320`: для защищённых узлов выполняются BFS (`:415–424`), а при росте ветвей повторно сканируются открытые узлы (`:426–438`, `:494–501`, `:848–865`). Одна BFS стоит O(V+A), но суммарная генерация не обязана быть линейной из-за повторов. `_build_void_mask` — альтернативная fallback-ветка, она не добавляется к стоимости этих presets. При bounded размерах до 49 cells не доказана необходимость отдельного generation-сервиса. Главный повторяющийся расход — runtime I/O A09-07.

World bootstrap по default refresh_static_seed=True (`features/world/services/bootstrap_service.py:29–61`), загружает static village 225 nodes (`loaders/village_loader.py:95–156`), затем все active nodes и полную projection (`services/cache_service.py:26–32`). `infrastructure/world/location_store.py:35–44` формирует один pipeline без chunking. Это O(nodes) CPU/memory/commands при startup. Для 225 nodes ограничено; увеличение мира/числа одновременно стартующих реплик увеличит нагрузку на общие хранилища. `core/containers/game.py:68–75` подключает этот путь при backend bootstrap.

Внешний `WorldRegionNodeGenerator` содержит пересчёт average coordinates внутри key для min (`features/world/runtime/node_graph.py:137–138`): формально O(V²) на выбор start. Но `LLMWorldGenerator.run` не вызывает его в просмотренном текущем пути (`services/generator_service.py:105–126`). Это observation об offline/будущем генераторе, **не дефект текущего per-player navigation**. Межпроцессная проблема seed уже отмечена A04-07; без измерения повторных генераций она не превращается в новый performance finding.

Hex Rift — dev/experimental путь. Builder допускает до 12 попыток (`features/rift/runtime/hex/generation/builder.py:643–668`), bounded DFS с лимитами states и копиями paths (`:1048–1150`). Синхронный start вызывается из async dev endpoint (`api/hex_test_router.py:30–65`), значит крупный dev generation способен занять API event loop. Router включается только dev mode (`api/router.py:181–186`). Отсутствие полной новой реализации не считается performance defect production.

## 9. Worker architecture и frontend

### 9.1. Где долгие задачи действительно влияют на короткие

| Процесс/очередь | Конкурентность / timeout в коде | Важная граница |
| --- | --- | --- |
| Backend API + Streams runtimes | Один uvicorn entrypoint без заданного `--workers` в compose | CPU в handler/SSR-backend operation и stream callback может задерживать HTTP того же процесса |
| Combat | max_jobs=30, 60s, keep_result=0 | Executor, AI, support, finalizer и persistence делят очередь и event loop |
| System | max_jobs=20, 60s, keep_result=5 | AC/Inventory/Rift flush, loot, vitals и sweeper конкурируют здесь |
| GenerationAI | max_jobs=5, 180s, keep_result=30 | Внешний provider не занимает combat coroutine; SQL/Redis/host и sync image CPU остаются ресурсами |
| Combat AI simulation | max_jobs=1, 180/900/2400s | Административная длинная задача задерживает следующие административные simulation jobs; процесс уже отдельный |
| Chat archive | max_jobs=1, cron 10 min | Последовательный drain, shared PG/Mongo/Redis |

Источники: `features/combat/workers/arq.py:23`, `:66–73`; `features/system/workers/arq.py:53–64`; `features/generation_ai/workers/arq.py:36–45`; `features/combat/workers/ai_simulation_arq.py:21–32`; `deploy/compose.game.yml:39`, `:142–221`.

`max_jobs` ограничивает in-flight jobs, **не размер backlog и не число CPU-ядер**. Таймаут coroutine требует возврата управления event loop; синхронный расчёт может отложить cancellation. ARQ ordinary exception не равен бесконечному автоматическому retry; поведение уже исследовано A05. Увеличивать concurrency до измерения Redis service time, SQL pool waits и memory/job рискованно.

Application backpressure частично есть: action queue threshold collector, single simulation job, page/batch limits. Общего доказанного admission budget по ARQ backlog в изученных enqueue paths нет. Отдельные очереди уже существуют; дополнительное разбиение domain containers без метрик не предлагается.

### 9.2. SSR, статические ресурсы и запросы браузера

`src/frontend/game_features/session/services/session_context_builder.py:86–98` сначала ждёт enter, затем строит state. Exploration последовательно запрашивает status → optional inventory → look-around → local-map (`:135–155`); Rift status → optional inventory → view (`:237–249`). Это подтверждённый HTTP waterfall, но не все операции доказанно независимы: перед параллелизацией нужно сохранить state/ordering contract. Shared AsyncClient с timeout=10s уже переиспользуется (`frontend/app.py:148`, `frontend/core/api.py:61–86`). Суммарный page latency включает эти зависимости; фактические timings не измерялись.

Catalog init каждый full shell получает bootstrap до сравнения manifest с IndexedDB (`frontend/static/js/game.js:60–95`, `:477–481`; `frontend/game_features/game_catalog/routes/bootstrap.py:13–20`). Это лишний network/auth/backend hop даже при готовом локальном cache; размер/компрессия ответа в браузере не измерены.

Nginx выставляет `/static/` годовой immutable cache (`deploy/nginx/site.conf.template:113–118`, `:253–258`), что полезно для повторных загрузок. Однако часть URLs стабильна, например vendor/status assets (`frontend/templates/game/base_game.html:29–42`), а static_version применяется выборочно (`frontend/core/renderer.py:106–123`). Это прежде всего риск устаревшего клиента после релиза, не доказательство медленной загрузки. Сильный cache следует оценивать вместе с версионированием URL.

Jinja rendering, HTMX fragment replacement, CSS/JS parsing и image decode требуют отдельного browser/server profile. Здесь не измерены Core Web Vitals, bundle execution, layout shifts, cache hit rate, compression ratio или memory/socket. Выдуманных чисел для них нет.

## 10. Выполненные локальные пробы

Сохранён воспроизводимый вспомогательный файл `audit/09_performance_probes.py`. Он не импортирует приложение, не подключает хранилища, не создаёт event loop, не меняет production files. Он извлекает выбранные **неизменённые методы** из текущего исходника через AST и подставляет in-memory Redis/DTO/repository/socket doubles. Все awaitables в основных пробах завершаются в памяти; fake socket использует вручную управляемую остановку coroutine.

Команда: `python -B -u audit/09_performance_probes.py` из корня репозитория, завершилась с exit code 0. Первичные успешные запуски до переноса файла выполнены под временным именем `.codex_tmp/a09_performance_probe_20261009.py`. Среда: Windows, системный CPython 3.13; project venv декларирует CPython 3.14.3. Эти времена нельзя напрямую переносить на Linux production.

### 10.1. Реальные log methods, fake Redis

Каждый существующий turn: пять JSON-log entries с текстом 100 ASCII-символов. Добавляется одна новая запись следующего turn. Eleven iterations, первый исключён, медиана остальных десяти; измерены decode/sort/merge/re-encode, не реальный HSET/Redis/network. Fixture не растёт между repetitions.

| Turns до append | Сумма bytes JSON values для нового HSET | Медиана Python ms, основной прогон |
| --- | ---: | ---: |
| 100 | 70 592 | 0,982 |
| 500 | 354 592 | 3,077 |
| 1000 | 709 593 | 6,195 |

Это не размер ActorSnapshot, не весь RSS и не BSON/Redis allocation. Предыдущий успешный прогон дал 0,703/3,502/6,388 ms; проверка сохранённого воспроизводителя — 0,699/3,997/7,300 ms. Разброс показывает, почему малый синтетический тест нельзя выдавать за SLA. Строгий вывод о суммарном O(T²) основан на повторной полной истории в коде, не на подгонке этих трёх точек.

### 10.2. AC scanner

| Fake AC | Состояние | SCAN / pass | JSON.GET / pass | Кандидаты |
| --- | --- | ---: | ---: | ---: |
| 100 | Все full | 1 | 100 | 0 |
| 1000 | Все full | 10 | 1000 | 0 |
| 5000 | Все full | 50 | 5000 | 0 |
| 1000 / 5000 | Все non-full | 1 | 100 | 100 |

Mock SCAN возвращает точно 100 keys/page; DTO validation подменена простой проверкой. Измерены вызовы и selection, не скорость Pydantic/Redis. При стабильном порядке повторный pass выбирает те же 100 non-full records.

### 10.3. Clean sync и slow socket

Исходный Character integrator с mocked repositories: `dirty target character → [character]`; после clear: `clean repeat → [character, attributes, skills, progression, symbiote]`.

Исходный broadcast с двумя fake sinks: до освобождения slow sink вызван только `slow_start`; после освобождения порядок `slow_start, slow_end, fast_start, fast_end`. Время сети не моделировалось.

### 10.4. Дополнительная ограниченная синтетика и неудачные запуски

Помощник отдельно измерил image normalization на однотонных PNG 512²/1024²/2048²: один непрогретый проход дал примерно 77/82/359 ms. Это иллюстрация sync CPU-участка; маленькая выборка, простое изображение и отсутствие реалистичного набора не позволяют выводить production distribution. Эти числа не используются для capacity расчёта.

Попытки полноценных async probes не завершились. Контрольный запуск с `faulthandler.dump_traceback_later(5, exit=True)` показал ожидание `socket.accept` внутри Windows `_fallback_socketpair` при создании asyncio event loop. Запуски остановлены; это ограничение данной среды, **не найденное зависание production combat**. Поэтому полный executor/AI/Pydantic benchmark и инфраструктурные integration/load tests не заявляются выполненными. Широкий pytest suite не запускался: production code не менялся, а инфраструктурные результаты не требовалось подменять mocks.

## 11. Что можно оптимизировать и что сначала измерить

Ниже — выводы о готовности и необходимые доказательства для этапа после завершения всех десяти аудитов; **исправления и план реализации не применялись**.

| Область | Готовность / следующий доказательный замер |
| --- | --- |
| Combat log persistence | Изолированный manager, воспроизведённая amplification; проверять bytes/commit и history length, сохраняя turn order и retry semantics |
| Actor load/commit | Можно отдельно измерять validation, full JSON payload, touched actors и число pipelines; batching/delta требуют сохранения exchange consistency |
| Pure resolver/stats | Хорошая граница для deterministic microbench; сначала profile representative effects/abilities и доли CPU. Переписывание на native code пока не обосновано |
| AI context | Измерить B×N hydration отдельно от candidate scoring; кешировать можно только с доказанным snapshot/version contract |
| AC/dirty sync | Есть воспроизводимые лишние чтения/записи; измерять scans examined/selected, duplicate enqueue и SQL writes per dirty generation |
| Chat archive | Прежде всего проверить drain budget against arrival rate, oldest-entry age и retention safety; nominal cap уже установлен арифметически |
| WebSocket | Slow-consumer stress test с bounded outgoing queues, память/connection; межпроцессная доставка должна быть решена до добавления процессов |
| Rift | Снимать instance/session bytes на обычный tick и keys examined per flush; при текущих малых картах не нужна предварительная смена генератора |
| SQL/Mongo | EXPLAIN/ANALYZE на изолированной копии реалистичного распределения, returned bytes, locks/transaction age, pool checkout wait; индексы не подбирать только по названиям полей |
| GenerationAI | Отдельные timings provider/normalize/storage/transaction lifetime и RSS по dimensions; queue rate/concurrency согласовывать с общими ресурсами |
| Frontend | Browser waterfall, long-session heap/DOM и JS CPU; серверные HTMX timings отдельно от сети до backend |

Для capacity модели нужны: arrival rate каждой операции, CPU ms/op, bytes/Redis command, число последовательных RT, queue wait/oldest job age, Redis memory/key families, SQL pool wait и transaction duration, Mongo bytes/document, event-loop lag. HTTP counters/histograms уже объявлены в `src/shared/infrastructure/metrics.py:9–24`; наличие определений не доказывает, что все эти доменные метрики собираются и доступны в deployment.

Нагрузочный сценарий должен независимо варьировать: число коротких боёв, длину одного боя, actors/ботов/effects, idle AC без кандидатов, hot chat topic и slow consumers, число Rift instances/sessions, размер inventory, coexistence generation jobs. Иначе один общий RPS скрывает разные ограничения.

Для CPU-процесса оценка загрузки имеет вид `sum(arrival_rate_i × CPU_seconds_i)`; для последовательного consumer — arrival rate должен быть ниже измеренной service rate; для очереди важна не только средняя utilization, но burst и долгие jobs. Подставлять в эти формулы отсутствующие production значения нельзя.

## 12. Итоговый статус

Установлены **11 подтверждённых performance/scalability ограничений: 4 High и 7 Medium**. Отдельно описаны риски pool budgets, Streams retention/dispatch, startup, экспериментального Hex и статики; они не выданы за воспроизведённые production инциденты. Critical не установлен.

Главный вывод для следующего этапа: сначала уменьшать доказанную повторную работу и проверить бюджеты очередей/транспорта; оценивать ускорение Python-математики по её фактической доле после профилирования. Модульные границы позволяют делать это локально без обязательного дробления монолита.

Добавлены только этот отчёт и автономный воспроизводитель аудита. Production code, tests suite, deployment, базы и operational skills не изменялись; обновление skills не требуется. Существующие пользовательские изменения сохранены.
