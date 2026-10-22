# AI

## Оставшийся генеративный сценарий

`items.text` создаёт название и описание предмета в JSON-формате.
Очередь GenerationAI, сохранение input/result и JSON-провайдер остаются.
Боевые боты и симуляции — отдельные локальные алгоритмы; они не используют LLM.

Заказ картинок, AI-обогащение мира, обложки новостей и vision-проверка картинок
выведены из live-кода. Для новостей сохраняется выбор подготовленных маскотов.
Обычная генерация/загрузка мира и уже существующие assets сохраняются.

## AIService

`src/backend/core/ai.py` предоставляет JSON-вызов через `codex_ai.GeminiProvider`.
Без настроенного provider генерация JSON не выполняется; worker фиксирует ошибку
по существующей retry policy. `GEMINI_API_KEY` и текстовая модель всё ещё нужны
для оставленного сценария предметов. Не удалять их при очистке image-настроек.

## Архив

Исходники удалённых генераторов и исходные версии смешанных файлов сохранены
в `archive/` с заменой корня `src` на `archive`. Архив исторический, импортировать
его из приложения или запускать его утилиты как актуальные нельзя.
Карта переносов и SHA-256: `archive/ai_retirement_manifest.json`.

Это retirement кода. Production данные, готовые картинки и реальные очереди
этой операцией не удаляются.

## Сохранность входа items.text

Задача принимается только после подтверждённой Mongo-записи и проверки
сохранённого запроса. SQL runnable row создаётся после этой проверки. При отказе
начальной записи/чтения постановка завершается ошибкой, а не задачей без input.

Перед повторной постановкой и каждым claim вход заново читается из Mongo:
проверяются принадлежность задаче, схема, SQL-указатель, структура запроса и hash
исходного input/prompt. При недоступном или повреждённом документе handler не
запускается и новая попытка не расходуется. Память старого процесса не является
запасным источником входных данных. GET истории может вернуть SQL metadata.

Это не распределённая транзакция SQL/Mongo: после успешной Mongo-записи и отказа
SQL возможен несвязанный документ. Его reconciliation,
разрыв commit → enqueue и автоматическая повторная доставка — отдельные задачи.


## Сохранность результата items.text

SQL-статус `done` выставляется только после подтверждённой Mongo-записи полного
JSON-результата и metadata, с чтением и сравнением сохранённых полей. Запись
результата обновляет существующий документ по SQL-указателю, task identity и
schema; missing input не восстанавливается из transient ORM cache этим путём.
Перед completion вход проверяется заново. Ошибка записи/подтверждения выходит
из repository; обычный сервис переводит попытку в cooldown/failed по её бюджету.
Даже если вызывающий код перехватил ошибку и сделал SQL commit, repository не
оставляет `done` или completion timestamp от неудачной записи.

Это гарантия порядка подтверждения, а не SQL/Mongo distributed transaction:
успешная запись Mongo может пережить SQL rollback. Уже применённый доменный текст
при Mongo outage не объявляется потерянным; повторная попытка может снова вызвать
provider. Exactly-once generation/application не гарантируются; восстановление
running по сроку владения описано ниже. Реальные данные не исправляются
автоматически; позднейшая потеря Mongo требует отдельного backup/recovery процесса.


## Восстановление SQL commit → ARQ

GenerationAI worker при старте и каждые30 секунд запускает recovery постановки.
SQL pending/due cooldown строка items.text/json с оставшимся бюджетом попыток
является долговечным намерением доставки. Новый процесс находит её независимо от
утраченного списка в памяти и от результата первоначального enqueue.

Один проход читает не больше100 ID в отдельной короткой SQL-сессии, закрывает её
до Redis операций и ставит jobs с устойчивыми ARQ IDs. Keyset cursor продвигается
по ID и сбрасывается после конца backlog; потеря cursor безопасна. При падении
Redis, исключении или enqueue None строка SQL не удаляется и не меняется,
следующий обход повторит доставку. Завершённые/failed/cancelled/running, future,
exhausted и retired задачи recovery не ставит. Неуспех одного enqueue не блокирует
остальную страницу. Mongo/provider при сканировании не вызываются.

Доставка at-least-once: прямой enqueue и recovery могут пересечься. Стабильный ID
подавляет дубликаты recovery в ARQ, а перед выполнением всегда остаётся обычный
SQL claim с row lock/status/not_before/attempts guard. Recovery не расходует
попытки. Существующий ARQ result может временно блокировать повторный ID;
после его TTL последующий обход повторит постановку. При backlog больше страницы
задержка зависит от числа страниц и доступности worker/SQL/Redis,30 секунд не SLA.

Rollback не создаёт видимой recovery задачи. Падение после SQL commit либо потеря
очереди не требуют сохранности памяти исходного процесса. Running lease recovery
и Mongo reconciliation описаны отдельно ниже; exactly-once provider не гарантируется.


## Сверка Mongo-документов GenerationAI

Отдельный cron GenerationAI worker при старте и каждые5 минут сверяет live
items.text/json документы с SQL. Grace window —1 час с последнего payload write;
одна страница —100 документов, keyset по строковому _id, cursor в worker context.
После конца страницы обход продолжается, после конца backlog начинается заново.
Неизвестные legacy types/нестроковые IDs и документы без updated_at не включаются
в этот live recovery contract. Старые image/assets не удаляются и не мигрируются.

Если SQL task существует, свободна для row lock, input/hash/schema/identity
валидны и SQL mongo_document_id отсутствует, указатель восстанавливается.
Существующий отличный указатель не перезаписывается. Для done дополнительно
проверяется схема GeneratedItemTextDTO. Исполнение задачи, attempts и доменный
текст не меняются. Сохранённый output без SQL done помечается result_pending_review:
наличие Mongo output не доказывает commit применения текста.

Результат сверки сохраняется в advisory поле reconciliation.state и агрегируется
в событии GenerationAiDocumentsReconciled. orphan означает отсутствие видимой
committed SQL строки; conflict — несовпадение identity/pointer/schema/payload.
Документы сохраняются полностью, без delete/TTL. Ни orphan, ни conflict не создают
новую SQL задачу и не вызывают provider. Это список для ручного разбора, а не
доказательство разрешённого удаления. Поздний SQL commit будет замечен следующим
обходом, метка станет linked; advisory поле не блокирует обычный claim.

Marker пишет conditional update по исходному snapshot; конкурентное изменение
даёт stale и откладывает ремонт. Busy SQL rows пропускаются. При отказе SQL/Mongo
проход прерывается без продвижения cursor. Marker может пережить SQL rollback:
он не является authority и исправляется повторной сверкой. Reconciliation не
восстанавливает потерянный Mongo из transient cache, не обеспечивает SQL/Mongo
atomicity; running восстанавливает отдельный lease механизм ниже. Массовой очистки реальных
хранилищ этим изменением нет.


## Границы SQL-транзакций при ожидании AI

Processing использует отдельную manual-commit SQL session. Claim, проверка durable
input и построение request выполняются в первой транзакции. Перед provider await
claim фиксируется как running; snapshot задачи отсоединяется от ORM, соединение
возвращается в pool. Другие загруженные ORM объекты expire, чтобы финализация
читала свежие данные. Открытого SQL transaction/row lock во время AI нет даже
при expire_on_commit=True; detached snapshot не выполняет lazy SQL reads.

После ответа открывается новая транзакция и блокируется только всё ещё running
строка с прежними task ID, revision, attempts, claimed_at и identity_key.
Устаревший ответ или ошибка не применяются и не меняют чужой retry. Дубликат
доставки видит committed running и не вызывает provider повторно. При отказе
claim commit provider вообще не вызывается. Provider exceptions обрабатываются
в новой owned transaction с прежним retry budget/cooldown контрактом.

Caller (GenerationAI worker) фиксирует final apply/result либо retry и затем
отправляет followups; SQL-based recovery очереди сохраняется. process_task и
claim_and_process_next владеют промежуточным claim commit: их нельзя оборачивать
во внешний session.begin() или вызывать на сессии с несвязанными изменениями.
Enqueue-only операции этого контракта не меняют. SQL/Mongo подтверждение результата
при финализации остаётся прежним; вынесено именно ожидание AI, не весь storage IO.

Отмена worker/процесса после первого commit оставляет durable running claim.
Возврат таких задач в обработку выполняет lease/recovery контракт ниже.
Это не гарантирует exactly-once provider call
и не отменяет необходимость ручного разбора result_pending_review.


## Возврат зависших running по сроку владения

Execution lease —10 минут, с запасом относительно ARQ job_timeout180s. Heartbeat
не нужен при этом фиксированном worker deadline: ответ, пришедший после lease,
не имеет права применяться. Production claim/expiry используют PostgreSQL clock,
а не время машины worker. Claimed_at вместе с revision/attempts/identity остаётся
claim token; отдельных таблиц/миграций для lease нет.

GenerationAI worker при старте и каждую минуту выполняет bounded100 SKIP LOCKED
сверку expired running live items.text/json. Fresh/locked/retired/terminal задачи
не захватываются. Если durable input валиден, output пустой dict и остались attempts,
строка становится pending: attempts не сбрасываются, revision повышается,
claimed_at/not_before очищаются. SQL commit фиксирует delivery intent; обычный
A05-08 recovery затем ставит её в ARQ. Сбой Redis не теряет это намерение.

При исчерпанном бюджете задача terminal failed (LeaseAttemptsExhausted).
Missing/corrupt input даёт InvalidDurableInput, старый running без claimed_at —
MissingClaimTimestamp с grace по created_at. Непустой либо некорректный raw Mongo
output даёт StoredResultNeedsReview: документ сохраняется без изменений, provider
повторно не запускается автоматически. Это ручной разбор, а не удаление результата.
Mongo outage прерывает и откатывает SQL batch: недоступность не считается corruption.
Recovery diagnostics хранятся в SQL short errors; admin GET показывает их, когда
сохранённый Mongo error относится к другому типу предыдущей ошибки.

Provider reacquire проверяет lease deadline до и после получения SQL row lock.
Старый ответ/ошибка не могут завершить задачу ни после истечения срока, ни после
requeue/new claim. Recovery не меняет игровой баланс и не применяет output.
Повторные проходы/SQL rollback безопасны. Отдельного гарантированного SLA нет:
тайм-аут lease и доступность worker/SQL/Mongo/Redis/backlog определяют задержку.
Exactly-once обращения и списания provider не гарантируются: после падения неизвестно,
успел ли внешний сервис выполнить запрос. Попытка уже израсходована и не возвращается.


## Атомарность применения и retry после ревизии

После повторного получения running claim обработчик применяет результат,
сохраняет completion и создаёт SQL followups внутри одного savepoint. Если handler
частично выполнил SQL, отказала запись результата Mongo или flush completion/
followups, savepoint откатывает изменения предмета/шаблона/связанных SQL строк.
Только после rollback записывается retry/failed; caller может безопасно commit
этого состояния. Добавленные pending followup IDs также удаляются при rollback.
Идентификаторы задачи сохраняются до savepoint, поскольку rollback expire ORM state.

Это не распределённая транзакция SQL+Mongo. Подтверждённый или неоднозначно
подтверждённый Mongo output после SQL rollback сохраняется для reconciliation/
ручного разбора. Его нельзя удалять или считать SQL completion только по наличию
Mongo-документа. Provider по-прежнему выполняется вне SQL transaction; budget,
claim fencing и отсутствие гарантии exactly-once не меняются.


Перед новым claim (по ID или очередной строке) проверяется raw Mongo output.
Непустой либо некорректный output останавливает автоматическую обработку:
SQL-задача становится failed с StoredResultNeedsReview до увеличения attempts,
документ Mongo целиком сохраняется. Это защищает от повторного provider call и
перезаписи результата после ambiguous acknowledgement или SQL rollback.
Пустой валидный output сохраняет обычный retry; Mongo outage не считается пустым
результатом и не разрешает обработку. Ручной разбор не означает auto replay.
