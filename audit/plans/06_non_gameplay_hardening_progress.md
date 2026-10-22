# Последовательное исправление технических замечаний


Актуальный краткий остаток: [audit/remaining_work.md](../remaining_work.md).
Постоянная копия ревизии: [audit/reviews](../reviews/2026-10-22-infrastructure/README.md).
Этот файл сохраняет историю, а не заменяет краткий список.

Дата начала: 19.10.2026. Основание: аудиты 10 и 11, сверка текущего кода.

## Порядок работы

- Работать в текущей ветке, без создания отдельной ветки.
- С 22.10.2026 по прямому поручению владельца завершить оставшуюся инфраструктуру единым пакетом без остановок на мелких задачах. Без коммита, push и deploy; AG-05 отложен до подготовки merge в main.
- После итогового отчёта по оставшейся инфраструктуре остановиться; к рифтам переходить отдельной задачей.
- Не менять баланс, игровые правила, формулы и содержимое каталога.
- Не выполнять push, deploy или production operations без отдельного поручения.
- Старые отчёты сохранять как исторические; статус подтверждать текущим кодом и проверками.

## Очередь

| Шаг | Задача | Исходные ID | Статус |
| --- | --- | --- | --- |
| 1 | Авторизация API настроек, AI-генерации и симуляций; согласованные read/write callers | A07-02/03 | Исправлено и проверено; остановка до команды на шаг 2 |
| 2 | Воспроизводимые миграции сайта на пустой PostgreSQL и обновление существующей схемы | A05-13 | Исправлено и проверено; остановка до команды на шаг 3 |
| 3 | Токены и персональные данные в логах и метриках | A08-05/06/07 | Исправлено и проверено; остановка до команды на шаг 4 |
| 4 | Logout, expiry/revoke открытых WebSocket и атомарная ротация refresh | A07-10/16, A05-12 | Исправлено и проверено; остановка до команды на шаг 5 |
| 5 | Источники зависимостей, develop behavioral gate, artifact-to-deploy gate и права env-файла | A06-05/06/09/12, A08-09/10/11/12 | 5.1 A08-12, 5.2 A06-12, 5.3 A06-05, 5.4 A06-06, 5.5 A06-09 и 5.6 A08-09 и 5.7 A08-10 исправлены; 5.8 A08-11: локальные gates и реальные GitHub rules проверены; публикация workflow и перенос secrets отложены |
| 6 | Восстановление Streams pending с доказанной идемпотентностью эффектов | A05-05 | Транспортный recovery в quarantine исправлен и независимо проверен; без коммита. Автоповтор/доменная идемпотентность не заявлены |
| 7 | Надёжное принятие и восстановление GenerationAI; срок жизни SQL-транзакций | A04-11/12/13/18, A05-07/08, A09-09 | 7.1–7.8: retry/input/result/queue/reconciliation/transaction/running recovery items.text исправлены и проверены; не-item AI архивирован, без коммита |
| 8 | Производительность архива чата, backpressure, Mongo projection, предел истории вкладки | A09-03/04/08/11 | Отдельная будущая работа над альфой чата; scope уточнить, перед реализацией разделить |
| 9 | Адресная типизация и SQL/Redis/Streams/HTTP contract tests | AG-05, A06-03/07/08/11 | A06-03/07/08/11 проверены; AG-05:6адресных заходов,28подавлений отложены до подготовки merge в main |
| 10 | Проверяемое восстановление/alerts, service isolation, Studio access/read-only | A08-02/15, A07-12 | Локальный пакет завершён: restore/evidence checker, env/auth isolation и Studio guards; реальные roles/ACL/backup-alert rollout отложены до выпуска |
| 11 | Canonical HTTPS origin ссылок подтверждения почты | A08-14 | Локально исправлено в финальном пакете: canonical origin, Host/proxy negative contracts; deployment отложен |

## Шаг 1

Предыдущий выполненный пакет Mongo/диагностики/сетевых проверок сохранён отдельно:
`62fa488a` — `fix(platform): close diagnostics and chat audit contracts`.

Граница: `/api/internal/config`, `/api/admin/generation-ai`,
`/api/admin/combat-ai`. Monsters уже имеет собственные gates и в этот шаг не входит.
Nginx запрет остаётся отдельной защитой; direct backend также обязан проверять права.
Чтение допускает operator reader/writer, изменение только writer. Обычный site-service
key и игровой токен не предоставляют operator-доступ.

Режим совместимости: `replacement-only` для прежнего anonymous/service-key
доступа к этим privileged endpoints; fallback не сохраняется. Формат успешных
ответов, алгоритмы и игровые правила сохраняются.

В шаг не входят общий вход в Studio/read-only инфраструктурных клиентов,
жизненный цикл пользовательских сессий, логи, миграции и механика симуляции.
Существующие admin callers должны сохранить работу с явно настроенными
серверными operator credentials; production source Studio остаётся без записи.

Результат: router-level read gate и write gate на всех мутациях; существующие
admin callers переведены на явные operator keys, remote Studio mutations
блокируются до HTTP. Параметр header dependency переименован в `operator_key`,
чтобы не конфликтовать с path-параметром `{key}` у настроек; alias заголовка сохранён.

Проверки: **287 passed** в адресном наборе (изолированные doubles/HTTP transport,
без настоящего AI, DB и очередей). Состав набора:

- `tests/backend/features/test_privileged_operations_access.py`
- `tests/frontend/integrations/backend_api/test_operator_clients.py`
- `tests/backend/features/test_internal_routers.py`
- `tests/frontend/integrations/backend_api/test_game_config.py`
- `tests/backend/features/combat/test_ai_simulation_admin.py`
- `tests/frontend/features/cabinet/test_game_settings_module.py`
- `tests/frontend/features/cabinet/test_combat_ai_testing_module.py`
- `tests/backend/features/test_diagnostic_access.py`
- `tests/studio/test_operator_diagnostics.py`

Запуск: `.venv/Scripts/python.exe -m pytest <перечисленные пути> --no-cov -q`.
До реализации зафиксирован failure: anonymous config GET возвращал 200 вместо 403.
Проверены также положительные reader GET и writer POST GenerationAI/simulation,
superuser boundary frontend, отсутствие service-key fallback и remote write deny.
Ruff и scoped mypy (`--follow-imports=silent`) прошли для 12 затронутых source-файлов;
полный project gate не запускался.

Коммит шага: `fix(security): authorize privileged operational APIs` (на текущей ветке).
Точный SHA доступен через `git log -1 --format=%H -- <этот файл>`.
Дальнейшая работа остановлена до команды на шаг 2.

Дополнение настройки шага 1: по поручению владельца заполнены приватные `.env`
и `.env.prod`: разные local/prod read/write ключи, согласованные backend/frontend
значения; Studio получает local read/write и production read, без production write.
Прежние записи сохранены. Значения не выводились и не коммитятся. Для применения
production настроек владелец заменяет GitHub secret `ENV_FILE` содержимым `.env.prod`.
GitHub, production и перезапуск процессов в этом дополнении не выполнялись.
Проверка: 8 изолированных ASGI-запросов с ключами обоих файлов прошли
(anonymous deny, reader GET, reader mutation deny, writer mutation success).

## Шаг 2

По команде владельца исправлена A05-13. До изменения на одноразовой PostgreSQL 16
воспроизведён `DuplicateColumnError`: `0002` повторно добавляла `token_hash`, уже
созданный первой миграцией через актуальные ORM models.

`0001_site_schema_baseline` теперь содержит явный DDL девяти исходных таблиц:
raw refresh token, без последующих referral/email полей. Импорт live metadata
удалён; изменения ORM больше не меняют историческую схему. Ревизии `0002`–`0004`
сохранены. Новая `0005_site_index_names` переименовывает четыре исторических
индекса по текущему соглашению ORM, без пересоздания таблиц и изменения данных.
Уже канонические имена допускаются; неизвестные определения/дубли требуют
разбора и вызывают транзакционный отказ. Downgrade baseline больше не использует
`CASCADE`, поэтому конфликт с чужими объектами сохраняет их и откатывает миграцию.

Проверка: **9 passed** на реальной одноразовой PostgreSQL 16:

```powershell
$env:RUN_SITE_MIGRATION_POSTGRES='1'
.venv/Scripts/python.exe -m pytest tests/frontend/migrations/test_site_migrations_postgres.py --no-cov -q
```

Покрыты clean upgrade/repeat head, populated `0001`→head с сохранением данных
девяти таблиц и SHA-256 conversion refresh token, populated `0004`→`0005`,
канонические/конфликтующие индексы и их rollback, downgrade/reapply,
защита чужих объектов и независимость baseline от будущих ORM tables/columns.
Alembic comparison head с текущими ORM types/nullability/defaults/indexes/FK
не показал различий. Ruff check/format трёх Python-файлов и scoped mypy двух
миграций (`--follow-imports=silent`) прошли. Одноразовый контейнер удалён.

Ограничения: проверялась изолированная база, не копия production. Реальные базы,
`.env`, GitHub и deployment не менялись; полный project gate не запускался.
Downgrade ниже `0002` не восстанавливает raw refresh secrets из hash; существующие
refresh sessions при таком откате не сохраняются. Это не рекомендация откатывать БД.
Инструкция: `docs/ru/frontend/index.md`. Commit subject:
`fix(site): make schema migrations reproducible`.
Следующий шаг — только после отдельной команды владельца.

## Шаг 3

По команде владельца исправлены A08-05/06/07. Воспроизведены synthetic canary
утечки в raw URL metrics, Nginx access/request error logs и production exceptions
прежнего library setup. Реальные secrets, сообщения и логи не использовались.

- Metrics выбирают route template после routing, неизвестные пути сводят к
  `<unmatched>`, методы — к конечному набору с `OTHER`. Error paths учитывают
  status/duration и возвращают in-flight gauge к нулю. URL parameters не копируются
  в HTTP log context. App error/auth logs сохраняют безопасный `route_template`.
- Nginx на обоих публичных hosts запрещает `/metrics` (включая trailing slash
  и normalized encoded URI), private scraper endpoint сохранён. Access JSON
  содержит route family, generated request ID, method/status/bytes/timing/upstream,
  без raw URI/query/IP. HTTP error log отключён: Nginx не умеет редактировать
  credential-bearing request URLs в error text. Master/startup errors сохранены;
  диагностика request failures использует structured access records.
- Project production wrapper явно задаёт `diagnose=False`, `backtrace=False`,
  исключает exception message/chains/source/locals, сохраняет error type и
  file/function/line frames. Известные приватные fields удаляются рекурсивно,
  arbitrary objects не сериализуются через repr, unstructured library/access
  messages становятся `ExternalLogMessage`. Service/request/correlation context
  сохраняется. Email adapter и fallback callers не bind адрес/subject/body.
  Установленная и canonical `codex_core` не изменялись.

Общий адресный прогон: **81 passed**:

```powershell
$env:RUN_NGINX_CONTAINER_TEST='1'
.venv/Scripts/python.exe -m pytest tests/shared/test_http_route_privacy.py tests/shared/test_production_log_privacy.py tests/shared/test_logging_config.py tests/shared/test_log_task_wrapper.py tests/frontend/test_url_log_privacy.py tests/frontend/features/auth/test_auth_service.py tests/frontend/features/email/test_email_service.py tests/frontend/features/account/test_account_service.py tests/frontend/features/cabinet/test_messaging_bridge.py tests/deploy/test_nginx_log_privacy.py tests/deploy/test_network_boundaries.py --no-cov -q
```

Проверены ASGI success/error/404/405, bounded label cardinality, stdout и collector
JSON с canary locals/SMTP error/email/body/query, реальные Nginx access/error
records при 200/502, public metrics deny, сохранность HTTP/WS routing.
Ruff и scoped mypy затронутых source modules прошли; полный project gate не запускался.

Ограничения: debug сохраняет developer diagnostics; sanitizer не распознаёт
private data, произвольно переименованные в разрешённые fields, поэтому запрет
логирования PII для callers остаётся. Collector проверен как JSON sink,
не как реальная Grafana Cloud доставка. Исторические production logs не очищались.
Без deploy/restart текущие production processes не изменятся; `.env` не менялся.
Commit subject: `fix(observability): keep credentials out of logs and metrics`.
Шаг 4 не начат; нужна отдельная команда владельца.

## Шаг 4

По команде владельца исправлены A05-12, A07-10 и lifecycle/budget часть A07-16.
Исходные red проверки: две concurrent threshold rotation на реальной PostgreSQL
создавали два успешных successor token; browser logout не имел game revoke bridge;
actual ASGI socket продолжал получать notice после замены session slot.

- Site rotation: conditional `DELETE ... RETURNING` старого hash с user binding,
  insert нового hash и один commit. Конкурентный проигравший получает прежний
  `RefreshTokenNotFoundError`; определённый insert/commit failure выполняет rollback
  и сохраняет старую durable строку. Порог семи дней и healthy non-rotation сохранены.
  Signing выполняется до потребления токена. После успешного commit старый token
  не replayable: retry потерянного ответа отклоняется без второго successor.
- Browser logout вызывает internal `/game-lobby/logout-token` для обеих имеющихся
  signed game credentials, затем отзывает текущий site refresh (включая уже
  rotated request-state token). Очищаются все пять cookies в domain/host-only
  вариантах и middleware token state. Невалидная refresh-cookie не мешает отзыву
  valid access-cookie. Storage/backend failure возвращает 503 с `Retry-After`,
  credentials остаются для повтора. Gameplay actor release не выполняется.
- Game slot release/renew используют Redis Lua compare-and-delete/expire.
  Устаревший logout не удаляет replacement session; concurrent refresh больше
  не восстанавливает отозванную сессию через unconditional claim. Endpoint требует
  internal service key и валидный signed game token; char/user не берутся из
  произвольного browser body. Captured game HTTP/refresh credentials после отзыва
  отклоняются. Новые login claim semantics сохранены.
- Единственный active WS `/ws/realtime` использует общий guarded transport для
  receive, fan-out, notices, heartbeat и history replay. Access expiry → 4001;
  logout/replacement/Redis error → 4003. Idle monitor опрашивает раз в секунду с
  учётом expiry, Redis timeout — две секунды. Отписки и pending sends очищаются;
  query char_id сверяется с claims. Text budget 16 KiB UTF-8, token bucket
  20 frames/sec, burst 40; oversized/rate/binary → 1009/1008/1003.

Общий итоговый набор: **184 passed**. Включены реальные одноразовые PostgreSQL 16
и Redis 7, forced insert conflict и deferred COMMIT trigger failure, barrier
rotation race, 20 повторов logout/renew и 20 replacement races, service gate deny,
signed HTTP logout → actual WebSocket close, blocked send/slow storage cleanup.

```powershell
$env:RUN_SITE_AUTH_POSTGRES='1'
$env:TEST_REDIS_URL='redis://127.0.0.1:57020/0'
$env:TEST_REALTIME_REDIS_URL='redis://127.0.0.1:57020/0'
.venv/Scripts/python.exe -m pytest tests/backend/realtime tests/backend/features/game_lobby/test_game_token_flow.py tests/backend/infrastructure/actor_state/test_game_session_lock.py tests/backend/infrastructure/actor_state/test_game_session_lock_redis.py tests/backend/core/test_game_auth.py tests/backend/core/test_auth_session_replaced.py tests/frontend/features/auth/test_browser_logout.py tests/frontend/features/auth/test_refresh_rotation_postgres.py tests/frontend/features/auth/test_site_auth_service.py tests/frontend/features/auth/test_auth_service.py tests/frontend/features/auth/test_api_router.py tests/frontend/core/test_auth_middleware.py tests/frontend/game_features/session/test_game_token_state.py tests/frontend/game_features/session/test_game_keepalive_route.py --no-cov -q
```

Redis URL выше использован только для специально созданного disposable контейнера
без volumes/persistence на loopback; не подставлять действующую базу. PostgreSQL
fixture создаёт собственный контейнер. Все контейнеры после проверки удалены.
Ruff затронутых Python-файлов и scoped mypy девяти source modules прошли.
Полный project gate не запускался. Инструкция: `docs/ru/frontend/index.md`.

Границы: JSON `/auth/logout` остаётся site-only; captured stateless site access JWT
сохраняет прежний expiry, blacklist не добавлен. Неопределённый commit acknowledgement
не гарантирует rollback после реального commit. Redis authorization check не атомарен
с последующей сетевой доставкой; idle revoke имеет bounded polling delay. Frame
budget применяется после ASGI receive; wire limits сервера не менялись, новый
DoS audit не выполнялся. Реальные browser domains/production не проверялись.
`.env`, production и deployment не менялись; новые env variables не нужны.
Commit subject: `fix(auth): revoke game sessions and rotate refresh tokens atomically`.
Шаг 5 не начат; перед ним надо выбрать одну задачу из объединённой группы.

## Шаг 5.1

Права production env-файла. По команде владельца из группы выбрана только A08-12. Остальные находки шага 5
в этой итерации не исправлялись. Исходный SSH deploy записывал секрет сразу в
`.env`, не задавая права; permissive umask и прежний mode не ограничивались.

Workflow теперь устанавливает `umask 077`, создаёт приватный temp через `mktemp`
в том же каталоге и записывает env/image refs туда. После успешной подготовки
`chmod 600` и `mv -fT` атомарно заменяют `.env`, не следуя существующему symlink.
Владелец файла — SSH deploy user. При ошибке подготовки старый файл сохраняется,
EXIT trap удаляет temp. Registry login и Compose идут после завершения замены.
Настоящие `.env`, `.env.prod`, GitHub secrets и production не менялись.

Red: новый regression test на исходном shell block workflow падал для четырёх
сценариев. Green: **36 passed** в полном `tests/deploy`, включая четыре новых
реальных Linux filesystem cases: missing/regular/symlink/failed update. Проверены
mode открытого write descriptor при первом credential write (не только после
`chmod`), итоговые `0600`/owner, denied read для `nobody`, сохранение значений и
шести image refs, неизменная цель symlink, cleanup и old content при ошибке `sed`.

```powershell
$env:RUN_ENV_FILE_CONTAINER_TEST='1'
$env:RUN_NGINX_CONTAINER_TEST='1'
.venv/Scripts/python.exe -m pytest tests/deploy --no-cov -q
```

Тест исполняет точный env-writing block из YAML, останавливаясь до registry login;
только synthetic content, существующий локальный Linux image, одноразовый Docker
`--rm --network none`, без volumes и published ports. Реального SSH/deploy не было.
Production umask/ACL не проверялись; root/deploy user остаются доверенными.
Полный project gate не запускался. Пример/secret менять не нужно.
Commit subject: `fix(deploy): write production env with private permissions`.
Остановиться до команды на следующую отдельную задачу группы 5.

## Шаг 5.2

Выбрана только A06-12: область проверки pre-commit `pip-audit`. Прежний hook
сканировал собственное изолированное окружение: FastAPI/SQLAlchemy там отсутствуют,
хотя project `.venv` содержит версии 0.136.1/2.0.49. Исправление подготовлено:
local/system hook вызывает helper через `python -I`, helper выбирает interpreter
этого checkout `.venv` и запускает `python -I -m pip_audit`. Никаких sync/install,
изменений зависимостей, `uv.lock`, source policy или новых waiver IDs нет.
Семь прежних hook exceptions и timeout 15 сохранены. `pass_filenames: false`
исключает source paths из scanner input, `always_run: true` сохраняет gate.
Отсутствующие environment/scanner и scanner errors дают ненулевой exit.

Проверки: **8 passed**, включая настоящие временные venv и pre-commit CLI.
Synthetic application package 1.2.3 присутствует в scanner inventory, отсутствует
в outer environment; clean/advisory/error exit codes 0/1/2 передаются вызывающему.
Ruff, scoped mypy helper и pre-commit config validation прошли. При настоящем
repo pre-commit прошли остальные применимые hooks; project audit завершился 1.

```powershell
.venv/Scripts/python.exe -m pytest tests/tools/test_pip_audit_project.py --no-cov -q
.venv/Scripts/python.exe -m pre_commit run pip-audit --all-files
```

Live scanner сообщил 17 packages, 121 advisory rows / 76 unique IDs; aliases и
дубли не равны 121 независимым подтверждённым уязвимостям. Среди результатов:
`pydantic-settings 2.14.0` (`CVE-2026-58203`), `urllib3 2.7.0`
(`PYSEC-2026-4175/4176/4177`). `codex-ai` и `thesealedworld` пропущены scanner как
не найденные на PyPI — это unknown, не clean. Summary находится в ignored
`var/audit/a0612_project_audit_summary.json`, полный вывод hooks —
`var/audit/a0612_precommit_checks.txt`. Это аудит installed packages, не lock
export, не deployed image и не отдельная верификация применимости advisories.

Владелец не разрешал пропуск hook; вместо этого отдельно поручил обновить
уязвимые библиотеки при совместимости. Выполнено согласованное security-обновление
`pyproject.toml`/`uv.lock` и project `.venv`: новый audit hook теперь проходит
без `SKIP`, с прежними семью exceptions. `uv lock --check` и `uv pip check`
проходят; в рабочем окружении 153 совместимых packages.

Необходимые prerequisites: устаревший несуществующий local source `codex-ai`
удалён, используется уже заявленный published `codex-ai==0.2.4` как в Docker.
Совместимость используемых API и широких тестов проверена. Dev-only `graphifyy`
ограничен Python <3.14 согласно upstream metadata; Python3.13 остаётся поддержан.
Новыми override/waiver конфликтующие зависимости не маскировались.

Итог: **243 passed** в рабочем `.venv` с real disposable PostgreSQL/Redis/MongoDB,
ASGI/WebSocket/Nginx и новым hook. MkDocs build прошёл. В широком сравнении до/после
одинаково **943 passed, 17 skipped, 3 failed**: прежние stale site analytics tests
ожидают числовые значения вместо `—`. Новых регрессий не найдено, эти три теста
не менялись. Full project gate не заявляется зелёным. Контейнеры удалены.
Live project hook: `No known vulnerabilities found`; только сам unpublished
`thesealedworld` пропущен scanner, source приложения этим не аудируется.

Версии, команды и ограничения: [security update](07_dependency_security_update.md).
Commit subject: `fix(quality): audit project dependencies and apply security updates`.
Production и `.env` не менялись. Другие задачи группы 5 не выполняются без команды;
удаление broken source выше — prerequisite одобренного обновления, не аттестация CI.


### Дополнение: актуализация тестов аналитики сайта

По отдельному поручению владельца заменены три устаревшие проверки числовых
счётчиков боёв/сценариев/путешествий. Проверяется текущий контракт: `—`, пояснение
про Studio, корректные key/title и отсутствие HTTP-запросов через backend client.
Runtime не менялся. Проверки: модуль аналитики **7 passed**; прежний широкий набор
frontend/shared/studio/tg_bot/backend core/realtime/chat/generation_ai —
**946 passed, 17 skipped** (четыре warning). Прежних трёх сбоев больше нет.
Это адресная проверка и повтор прежнего набора, не полный project gate.
Локальный вывод: `var/audit/site_analytics_updated_tests.txt` (ignored).

## Шаг 5.3

**A06-05 — clean CI dependency install: исправлено и проверено.**

Несуществующий sibling source `codex-ai` удалён в предыдущем security update;
здесь подтверждена установка published `codex-ai==0.2.4` без соседнего checkout.
В `ci.yml` и `build-images.yml` все dependency `uv sync` и последующие `uv run`
используют `--locked`: manifest drift завершает job ошибкой, lock не обновляется.
Версии библиотек, manifest и lock в этой задаче не менялись.

Проверка 19.10.2026: новый одноразовый Linux-контейнер `python:3.13-slim`
(Python 3.13.16, uv 0.11.19), без bind mounts, host venv, credentials и siblings.
На момент установки скопированы только `pyproject.toml` и `uv.lock`:

- `uv sync --locked` и `uv pip check`: **157 packages, compatible**.
- `uv sync --locked --all-groups` и `uv pip check`: **176 packages, compatible**.
- Затем скопированы только `src`, `tests`, `tools`; сеть отключена для smoke.
  С project source path (`.:src`) прошли imports `codex_ai`, `codex_core`,
  `codex_platform`, `aiogram`, backend AI, frontend analytics и GenerationAI executor.
- `uv run --locked python` запускает pytest для `tests/shared`,
  `tests/frontend/features/cabinet/test_site_analytics_module.py` и
  `tests/backend/features/generation_ai`: **94 collected**, затем **94 passed**.
- В отдельной disposable-копии совместимое изменение manifest
  `rich>=13.9.4` → `rich>=13.9.3` при доступном registry: `uv sync --locked`
  возвращает **1**, явно сообщает `The lockfile ... needs to be updated`.
  SHA-256 lock не меняется; после восстановления manifest `uv lock --check --offline`
  проходит. Предварительные offline negative attempts зависели от resolver cache
  и не использованы как доказательство lock gate.

Артефакты (ignored): `var/audit/a0605-clean-install.txt`,
`a0605-clean-check.txt`, `a0605-clean-tests.txt`, `a0605-clean-negative.txt`.
Smoke harness: `var/audit/a0605-clean/check.py`. Временные контейнеры/образы удалены.
Hosted GitHub Actions и полный project gate не запускались; это доказательство
clean Linux dependency install/import/collection и узкого поведения, не full sign-off.
A06-06 behavioral gate, A06-09/A08-11 deploy gate, A08-09 action refs и более широкий
A08-10 Docker source/artifact provenance остаются отдельными задачами.
Production, gameplay, env и секреты не менялись. Остановка до следующей команды.


## Шаг 5.4

**A06-06 — behavioral gate для develop: исправлено и проверено.**

В `ci.yml` отдельный status `Develop Behavioral Tests` выполняет существующий
широкий набор frontend/shared/Studio/tg_bot/backend core/realtime/chat/GenerationAI.
Он запускается при push develop и PR с base develop (включая fork), независимо
от lint/types; ни `needs`, ни `continue-on-error` нет. Прежний lint/types status
сохранён и также охватывает PR develop. Full Quality and Docs остаётся на main
push/PR, поэтому PR develop не запускает второй полный прогон. Docker verification
job целиком сохранён и остаётся только на push main после quality.

Установка и запуск используют `--locked`. Test profile явно задаёт публичный
тестовый SECRET_KEY, ENVIRONMENT=testing и DEBUG=True: без локального `.env` и
production credentials. Попытка DEBUG=False обнаружила guard development signer
keys при collection; именно поэтому изолированный тестовый профиль явный.
Строгие production-settings тесты сами задают debug=False. Runtime не менялся.
`--no-cov` относится только к выбранному набору, full coverage threshold не менялся.

Проверка 19.10.2026: disposable Linux `python:3.13-slim`, Python 3.13.16,
чистый `uv sync --locked`, tracked source snapshot без bind mounts, локального
venv, `.env`, secrets, sibling checkout и настроенных внешних test services.
Точная команда из YAML и её env: **946 passed, 17 skipped, 8 warnings**, exit 0.
Negative proof: в disposable container временно добавлен один намеренно падающий
тест в выбранный `tests/shared`, затем выполнены те же argv/env без `-k` и иных
изменений: **1 failed, 946 passed, 17 skipped**, exit **1**. Probe удалён
в `finally`; в рабочий checkout не добавлялся.
17 тестов, которым нужны disposable service URLs, остаются пропущенными;
семантика реальных storage adapters этим gate не подтверждается.

Event/ref matrix проверяет push develop/main, PR develop/main, fork PR develop
с `refs/pull/.../merge` и нецелевой push: develop jobs только на develop,
full quality только на main, Docker только push main. Сравнение YAML подтвердило,
что весь Docker job неизменен. Локальные evidence: `var/audit/a0606-command.txt`,
`a0606-clean-install.txt`, `a0606-behavior-positive.txt`,
`a0606-behavior-negative.txt`, `a0606-event-matrix.json` (ignored).

Hosted workflow и required-check/branch-protection settings не запускались и
не проверялись; полный project gate не заявляется. Production, gameplay,
версии библиотек, env-файлы и секреты не менялись. A06-09/A08-11 deploy gate,
A08-09 action refs и более широкий A08-10 artifact provenance остаются отдельными
задачами. Остановка до следующей команды.


## Шаг 5.5

**A06-09 — привязка deploy к successful quality/build: исправлено локально.**

`Build Release Images` после Quality Gate и шести успешных build/push шагов
публикует manifest `release-images-<run_attempt>`. Он фиксирует repository,
run/attempt, source SHA, version и шесть digest outputs build action.
Manual deploy сохраняет `image_ref`, дополнительно требует `build_run_id`.
Первый job проверяет через authenticated Actions API точный workflow/repository,
completed success run, оба успешных jobs одной attempt, artifact origin/digest,
manifest identity и соответствие image_ref. Неизвестные, failed/cancelled,
foreign, просроченные, неполные и подменённые данные блокируются до SSH/SCP.
Bounded ZIP читается без extraction, API bearer не уходит signed storage URL.

В `.env` передаются immutable `ghcr.io/...@sha256:...`, deploy configs checkout
по проверенному build SHA. Tags после проверки не могут подменить deployment.
Старые builds без manifest больше не подходят: нужен новый successful build.
Retention 90 дней с учётом организации, rerun требует Re-run all jobs.
A08-09 mutable action roots, A08-11 approvals/ref/concurrency и более широкий
A08-10 source policy остаются отдельными задачами.

Проверка 19.10.2026: `pytest tests/deploy --no-cov -q` с
`RUN_ENV_FILE_CONTAINER_TEST=1 RUN_NGINX_CONTAINER_TEST=1` — **73 passed**.
В том числе 37 тестов promotion: successful SHA/version, failed/cancelled/pending,
foreign workflow/repository, skipped quality/failed build, wrong attempt,
expired/missing manifest, ref/source/digest mismatch, invalid immutable refs,
ZIP traversal, rerun race, malformed API, network failure без вывода токенов,
manifest CLI и запрет пересылки bearer signed download. Workflow graph проверяет
обязательный gate для обоих SSH jobs и config checkout по verified SHA.
Ruff check/format и focused mypy helper (1 source file) прошли.
Итоговая приёмка включает все Docker opt-in tests: настоящие Linux env
permissions и Nginx, а также положительный verify-CLI output test.
Evidence: `var/audit/a0609-deploy-tests.txt` и `a0609-mypy.txt` (ignored).

Hosted Actions, реальные GHCR build/push/download и production не запускались;
проверки API используют локальные fixtures по official API contract. Полный
project gate не заявляется. Gameplay, зависимости, production env и secrets
не менялись. После commit остановка до следующей команды владельца.


## Шаг 5.6

**A08-09 — immutable Actions/container references: исправлено и проверено локально.**

Все 30 external `uses` (девять Actions) используют полные 40-character commit SHA.
Официальные refs проверены через GitHub; исходные version tags оставлены в comments,
major не менялись. Прежний setup-uv pin сохранён, подтверждён tag v8.1.0.
Buildx явно закреплён на официальном stable v0.38.0 вместо runner/default latest.
Два setup-buildx jobs используют проверенный digest BuildKit driver image.

В 14 deploy-файлах закреплены 35 image references: Dockerfile FROM, внешний
Dockerfile frontend и literal Compose images. Вместе с BuildKit и CI hadolint это 15 уникальных
registry indexes/manifest lists. Digest каждого проверен по SHA-256 raw manifest;
все сохраняют Linux amd64 и arm64. Теги читаемы, включая `latest@sha256` для
прежних tools: выбор содержимого теперь определяет digest. Проектные images
остаются verified outputs A06-09, mutable fallback не добавлен.

Новый policy test сканирует все workflow/deploy YAML/Dockerfile, включая `# syntax`,
и запрещает mutable refs; image variables разрешены только шести verified project
outputs. Проверка Buildx требует explicit release и driver digest. Тест добавлен
в develop behavioral suite; её команда в testing strategy синхронизирована.
До pinning policy: **15 failed, 5 passed**; после: **24 passed**.

Проверки 19.10.2026:

- `pytest tests/deploy --no-cov -q` с обоими Docker opt-ins и новым Nginx image:
  **97 passed**, включая A06-09 promotion, Linux env permissions и Nginx.
- **10** Compose projects/overlay combinations: `config --quiet --no-env-resolution`
  с пустым `--env-file` и синтетическими параметрами; реальные env не читались.
- Из минимального контекста без secrets успешно собран локальный Nginx image
  `a0809-nginx-check:local` из pinned base; именно он использован в Docker tests.
- Ruff check/format изменённых tests прошли. Full project gate и builds остальных
  runtime images не запускались; hosted Actions/production не проверялись.

Evidence (ignored): `var/audit/a0809-actions.json`, `a0809-setupuv.json`,
`a0809-buildx-version.json`, `a0809-images.json`, `a0809-policy-before.txt`,
`a0809-policy-after.txt`, `a0809-deploy-tests.txt`, `a0809-nginx-build.txt`,
`a0809-check/compose-results.json`.

Ограничения: pinned appleboy entrypoints скачивают versioned drone-ssh/scp release
assets без checksum; tool downloads, hosted runner, apt и PyPI build inputs не
становятся транзитивно immutable. Это закрытие объявленных Action/image refs,
не полная supply-chain attestation. A08-10 source policy и A08-11 approvals/ref/
concurrency остаются отдельными задачами. Gameplay, зависимости, env и secrets
не менялись; push/deploy не выполнялись. Остановка после commit до команды.


## Шаг 5.7 — файл задачи A08-10

Режим: с ревизором. Состояние: reviewed-awaiting-acceptance.
Рабочий каталог: `D:/Workspace/personal/pets/TurnBasedMMORPG`, ветка `develop`,
исходный commit `2ac758cf`, рабочее дерево перед задачей чистое.
Этот раздел — согласованный файл текущей задачи; отдельный конкурирующий план
не создаётся.

### Исходное задание и уточнения

Владелец: «Давай следующую задачу шага 5 — A08-10, согласование источников
зависимостей в CI и Docker. Так же по одной: исправляешь, проверяешь, коммитишь
и ждёшь команды дальше». Затем выбран режим: «Да — с ревизором и файлом задачи».
Ранее: текущая ветка без новой ветки, не менять gameplay; без push/deploy.
Историческая A08-10 и текущие Dockerfile/CI/manifest/lock — первичные материалы.

### Требования и ограничения

- [x] R1: выполнить только A08-10, согласовать dependency sources CI/Docker;
  остальные задачи очереди не выполнять. Источник: запрос владельца.
- [x] R2: сохранить текущую ветку, gameplay, env/secrets и production;
  проверить, закоммитить и остановиться без push/deploy. Источник: порядок владельца.
- [x] R3: вести требования/доказательства в этом файле, провести независимую
  ревизию перед итоговым отчётом. Источник: выбор владельца и task-review-gate.
- [x] R4: чистый CI и Docker используют согласованный published source из
  `pyproject.toml`/`uv.lock`; отсутствующий sibling и игнорирование источников
  не служат fallback. Источник: проверяемый контракт A08-10.
- [x] R5: подтвердить clean locked install/export, identity выбранных packages
  и hash provenance установленного Docker wheel; неверный lock/hash/source
  должен блокировать проверяемый путь. Источник: критерии исходной находки.

### Предположения и первоначальный план

Текущий manifest/lock уже не содержит local codex-ai source после A06-05.
Принимается существующий published набор версий; обновление app libraries и
перераспределение runtime groups не являются целью этой задачи.
Проверить шесть Python Dockerfile и CI, устранить различающийся source policy,
проверить в чистом Linux Python 3.13 без host venv/siblings/env, затем независимая
ревизия, исправление замечаний, commit и остановка. Hosted Actions и production
не запускать; локальные fixtures/одноразовые контейнеры допускаются для проверки.

### Выполнение и доказательства

| ID | Реализация | Ревизия | Доказательство |
| --- | --- | --- | --- |
| R1 | done | pass | Diff ограничен A08-10, gameplay/manifest/lock не менялись |
| R2 | done | pass | Ревизор проверил task commit на develop и чистое дерево; финальная запись MD-only |
| R3 | done | pass | Требования до реализации, независимый reviewer без истории |
| R4 | done | pass | 6 locked exports без source bypass; uv 0.11.19 в CI/Docker |
| R5 | done | pass | Реальные builders и wheel provenance; отказы lock/source/hash |

### Наблюдения исполнителя и приёмка ведущего

Изменения: все шесть exports используют `--locked` и project sources; явный
`--require-hashes`; uv `0.11.19` в CI и Docker. Default runtime groups и app
versions сохранены. Семь policy cases включены в develop behavioral suite.
В минимальном контексте manifest/lock (без src, env, siblings и host venv)
собраны реальные builder stages backend/frontend/tg (три export variants) на
Linux Python 3.13.16. Это builder tests, не шесть готовых runtime images.

В одноразовом backend builder: `uv sync --locked --all-groups --no-install-project`
успешен. `--no-install-project` исключает только editable project из минимального
контекста; это проверка CI dependency install, не полный hosted checkout/gate.
Проверочная force-reinstall `codex-ai==0.2.4` в созданном builder venv выполнена
с `pip --require-hashes --report` (не отчёт массовой установки всех packages):
URL соответствует wheel entry lock, SHA-256
`174fb2645df06ab33e8ded65bc6eefab48bd55df81ac63043cf9dd6684476f01`.
`pip check` прошёл, lock не менялся. Compatible manifest drift блокирует export
и sync с точной ошибкой `--locked`; missing sibling source блокирует оба пути;
неверный wheel hash блокирует pip. App versions/groups не менялись.

Ведущий: `pytest tests/deploy --no-cov -q` с обоими Docker opt-ins —
**104 passed**; Ruff check/format нового test прошли. Evidence (ignored):
`var/audit/a0810-deploy-tests.txt`, `a0810-{backend,frontend,tg}-build.txt`,
`a0810-verification.txt`, `a0810-context/verify.py`, `identity-summary.json`,
`pip-report.json`, `ci-clean-sync.txt`, `ci-identity.txt`, `stale-*.txt`,
`missing-source-*.txt`, `wrong-hash.txt`, `pip-check.txt` в том же context directory.

### Независимая ревизия и разбор замечаний

19.10.2026, отдельный агент `a0810_independent_review` с `fork_turns=none`.
Первоначально получил только исходные требования/ограничения и план, без отчёта
исполнителя. Первичный вердикт: R1/R3/R4/R5 pass; R2 partial только до commit.
Блокирующих замечаний нет. Самостоятельно выполнил 31 policy/reference tests,
в offline Linux builder проверил Python/uv, installed codex-ai version и совпадение
manifest/lock с checkout; сравнил тело exported requirements. Прочитал actual
builder logs, verify.py, pip report и точные negative logs, сверил URL/hash с lock.

Ограничения ревизора: hosted/full runtime/production не проверялись; полные
сетевые install/negative cases повторно не выполнялись. Его дополнительный
опыт со stale lock offline остановился на metadata cache miss и не используется
как доказательство lock gate; точный refusal подтверждён исходными online logs.
После фиксации первого заключения ревизору переданы точные claims C1–C7:
конфигурация и неизменность app versions/groups; три builder variants; external
CI deps с no-install-project; проверочная codex-ai wheel reinstall; точные
negative cases; root 104 tests и reviewer 31 tests; границы hosted/runtime/prod.
Все семь подтверждены, опровержений и неподтверждённых утверждений нет.
После commit ревизор отдельно проверил оставшийся R2: task commit существует
на develop, рабочее дерево чистое, scope не расширен. R2 pass; все R-ID закрыты.
Ревизор подтвердил: финальная запись этого результата через MD-only amend того
же task commit не требует повторной ревизии неизменённого кода. Итоговый SHA
определяется `git log -1` после amend, а не записывается внутрь самого commit.
Все commit hooks первого commit прошли, включая pip-audit и hadolint.
Три временных builder images удалены после проверки; evidence logs сохранены.
Следующая задача A08-11 не начиналась.

### Принятие пользователем

Ожидается. После ревизии состояние `reviewed-awaiting-acceptance`; только явное
принятие владельцем изменяет его на `accepted`.


## Шаг 5.8 — файл задачи A08-11

Режим: с ревизором. Состояние: reviewed-awaiting-acceptance.
Операционная проверка remote protections: unverified.
Каталог `D:/Workspace/personal/pets/TurnBasedMMORPG`, ветка `develop`,
исходный commit `65b8cc5c`; начальное дерево чистое.

### Исходное задание и уточнения

«Давай следующую задачу шага 5 — A08-11, ограничения и подтверждение
production-деплоя. С ревизором, так же по одной: исправляешь, проверяешь,
коммитишь и ждёшь команды дальше».
Ранее: без новой ветки, gameplay, push/deploy и production operations.
Режим выбран явно; повторный выбор не нужен. Этот раздел — файл текущей задачи.

### Требования и ограничения

- [x] R1: исправить только A08-11, сохранить предыдущие artifact/digest/source
  gates A06-09/A08-09/A08-10. Источник: запрос и очередь владельца.
- [x] R2: ограничения доверенного dispatch/source ref до обращения к production;
  main — production branch по действующему release-контракту. Источник: A08-11
  и project release skill. Должен сохраняться rollback проверенных main ancestors.
- [x] R3: отдельное подтверждение production через GitHub protected environment;
  отсутствие обязательных reviewers/недоступная проверка защиты не допускает
  SSH/SCP. Источник: approval-контракт A08-11; fail-closed — решение реализации.
- [x] R4: исключить одновременные production-деплои всех слоёв и отмену активного
  run новым run. Источник: serialization-контракт A08-11.
- [x] R5: проверить positive/negative ref/approval/graph/serialization policy;
  попытаться прочитать реальные GitHub protections и честно отделить локальные
  доказательства от недоступных hosted settings. Источник: исходная находка.
- [x] R6: требования и доказательства в MD, независимый reviewer без истории,
  итоговые claims сверить отдельно. Источник: явный режим владельца.
- [x] R7: текущая ветка, без gameplay/real env/secrets/production изменений;
  проверить, commit, отчёт и остановка без push/deploy. Источник: порядок владельца.

### Предположения и первоначальный план

Сохранить ручные inputs layer/build_run_id/image_ref, immutable images и checkout
configs по verified SHA. Dispatch только main; source SHA должен быть в истории
main, чтобы не ломать rollback. Gate approval — protected production environment
и проверка его реальных required reviewer rules перед SSH; только YAML environment
не считается достаточной защитой. Не вводить обязательного второго человека без
решения владельца: существующая self-review policy environment фиксируется как
операционная настройка, а не выдумывается.
Общий concurrency group на production, без per-layer/ref/run-id suffix, без
cancel-in-progress. Live FIFO/двойной deploy не запускать ради проверки.
Прочитать цепочку, реализовать минимальный fail-closed gate и тесты, проверить
предыдущие deploy-контракты, независимая ревизия, commit и остановка.

### Журнал уточнений и диагностики

Локальная read-only попытка `gh api` environment production и main protection
для CodexDLC/thesealedworld: gh exit 4, нет gh auth login/GH_TOKEN.
Секреты не искались и не выводились. Реальные rules остаются unknown;
эта недоступность не доказывает отсутствие защиты. GitHub connector fetch также
не поддерживает environment API URL. Настройки GitHub не менялись.

### Выполнение и доказательства

| ID | Реализация | Ревизия | Доказательство |
| --- | --- | --- | --- |
| R1 | done | pass | Artifact/digest/source gates сохранены |
| R2 | done | pass | Dispatch main, source main ancestor, control/config checkouts разделены |
| R3 | done | pass-local; remote unverified | required reviewers gate, remote settings unverified |
| R4 | done | pass-local; remote unverified | global concurrency policy, hosted serialization unverified |
| R5 | done | pass-local; remote unverified | локальные cases проверены; remote read недоступен |
| R6 | done | pass | Первичная ревизия и отдельная сверка C1–C7 подтверждены |
| R7 | done | pass | Reviewer проверил task commit на develop и чистоту дерева |

### Независимая ревизия и разбор замечаний

Отдельный fresh reviewer `a0811_independent_review`, `fork_turns=none`,
получил исходное задание, R1–R7 и первоначальный план без отчёта исполнителя.
Первичная ревизия окончательного кода: блокирующих findings нет.
R1/R2 pass; R3/R4/R5 pass локально с remote/hosted unverified; R6 partial до
сверки claims, R7 partial до commit. Reviewer независимо выполнил **82 tests**,
изучил цепочку context/ref → artifact outputs → environment rules → protected
job → повторная policy → selected configs → SSH/SCP, сверил официальный API
schema и Actions read permission. Diff-check прошёл. Remote protections, secret
scoping, admin bypass и живая serialization не подтверждены.

Наблюдения ведущего: окончательный полный `pytest tests/deploy --no-cov -q`
с RUN_ENV_FILE_CONTAINER_TEST=1 и RUN_NGINX_CONTAINER_TEST=1 — **149 passed**.
Scoped mypy helper, Ruff check/format прошли. Это local fixture/isolated Docker
checks; два production run ради проверки не запускались. Секреты и GitHub
settings не менялись. Evidence (ignored): `var/audit/a0811-deploy-tests.txt`,
`a0811-mypy.txt`, `a0811-implementer-tests.txt`; reviewer temp — `a0811-review*`.
После собственного первого заключения reviewer получил точные claims C1–C7:
trusted refs/rollback, environment и runtime checks, native concurrency без FIFO,
сохранение предыдущих gates, root 149 tests/mypy и reviewer 82 tests, реальные
remote settings unknown, self-review policy без обязательного второго человека.
Все подтверждены в заявленных пределах. R6 pass. R3–R5 отмечены только в границах
локального контракта; состояние настоящих GitHub protections остаётся открытым.
Финальные production approval/parallel runs и перемещение secrets не выполнялись.
После commit reviewer независимо проверил R7: commit существует на develop,
рабочее дерево чистое, семь файлов соответствуют A08-11. R7 pass. Commit hooks,
включая pip-audit, прошли. Фиксация этого заключения выполняется MD-only amend
того же local task commit; reviewer подтвердил отсутствие необходимости повторять
ревизию неизменённого кода. Итоговый SHA читается через git log после amend.
Локальные R1–R7 подтверждены в описанных пределах. Настоящие environment/main
protections, secret scoping/admin bypass и hosted serialization по-прежнему
unverified; полное operational закрытие A08-11 не заявляется. Следующие задачи
очереди не начинались; push/deploy/изменения GitHub settings не выполнялись.

### Принятие пользователем

Ожидается; после независимой ревизии — reviewed-awaiting-acceptance,
accepted только по явному принятию владельца.


### Продолжение A08-11: доступ к GitHub

Поручение владельца: «давай всё-таки настроим доступ к гиту так чтобы ты мог
настроить защиты ... это в целом доступно или нет?» Дополнение: сравнить MCP
GitHub и GitLab. Это продолжение открытой operational части A08-11, выбранный
режим с ревизором сохраняется, повторный выбор не требуется.

Требования: R8 — настроить пользовательскую авторизацию gh через официальный
browser flow, не просить пароль/токен в чате и не печатать credential; R9 — после
входа только прочитать фактические permissions/environment/main protections,
подготовить конкретные изменения защиты к review, без push/deploy; R10 — сравнить
доступные в чате tools с официальными MCP-возможностями, не устанавливая GitLab
и не меняя hosting проекта. Remote protection writes — после подготовки точного
результата и проверки прав; никакого автоматического назначения reviewers наугад.

План: web login с подтверждением владельцем; проверить auth/repository role;
прочитать rules и scope secrets (только metadata, не values); подготовить изменения
и независимую проверку. Сравнение MCP выполнено по официальным источникам;
у текущего connector нет environment/protection tools, gh пока не авторизован.
R8 pending; R9 pending; R10 done (обычная проверка документации, не подключение).

### Operational continuation 2026-10-20: protections

Owner explicitly authorized configuring GitHub protections after successful login.
R8: gh authenticated as CodexDLC; admin access confirmed. Commit/PR authorship stays
CodexDLC, no AI coauthor trailers. R9 extends to applying and reading back the
following concrete settings, without push/deploy or reading/writing secret values.
R11: main requires PR (zero human approvals for sole operator), strict required
Full Quality and Docs from GitHub Actions, admin enforcement, resolved conversations,
no force pushes/deletions. develop remains directly writable for current workflow.
R12: production requires CodexDLC approval, self approval allowed, admin bypass off,
custom deployment branch main only (no tags). Existing repository secrets untouched;
secret migration remains explicitly open. Current remote workflow predates local
A08-11: environment gate does not protect workflows until they reference it.
Plan: independently review JSON payloads in var/audit/a0811-remote, apply via API,
read back exact settings, independent verification, report limits and commit MD.
Live baseline: main/develop protected=false, zero environments, no repository
rulesets; four repository secret names ENV_FILE/HOST/SSH_KEY/USERNAME.
Remote CI main run 27161231761 has successful Full Quality and Docs.
R11/R12 implementation pending; independent verification pending.

### Applied configuration and independent verification

2026-10-20: all three API mutations succeeded. Required check app binding verified
against live check-runs (github-actions app15368). Separate GET readback assertions
passed for every configured field; ignored evidence: var/audit/a0811-remote/readback.json.
Fresh independent reviewer remote_protection_review (fork_turns=none) reviewed
neutral requirements and payloads before mutation, then independently fetched actual
settings and confirmed R11/R12 configuration. No blocking findings.

- [x] R8 user auth: done/pass (actual CodexDLC identity/admin access verified).
- [x] R11 main policy: done/pass, independent actual GET; PR count0, strict quality
  check, admins enforced, conversation resolution, force/delete prohibited.
- [x] R12 environment configuration: done/pass, independent actual GET; CodexDLC
  reviewer, self approval allowed, admin bypass disabled, branch main only.
- R9 actual remote configuration applied and verified; overall deployment behavior
  remains partial until updated workflow reaches main and repository secrets are
  migrated safely. No secret values read/written; four existing names unchanged.

Important limitation: current remote deploy workflow does not reference production
and therefore is not gated by this environment. No push, deploy, live denial trial,
credential migration or gameplay change occurred. develop remains unprotected and
writable intentionally for existing one-task-at-a-time workflow. Admin retains
ability to edit settings; enforcement covers ordinary branch/deployment operations.
State: reviewed-awaiting-acceptance for configuration, A08-11 operational partial.

### Следующий отдельный шаг: подключение workflow (2026-10-20)

Исходный запрос: «подключим workflow к защите production. С ревизором,
так же по одной задаче: проверяешь, коммитишь и ждёшь команды.
Сам деплой пока не запускай».
R13: проверить и подготовить подключение всех production SSH/SCP операций к
protected environment production; сохранить ручной запуск без deployment run.
R14: независимый reviewer; проверка, local commit, остановка. Secrets не менять.
R15: публикация не подразумевается из прежнего local-only порядка: выбор между
отдельным published PR (без merge) и local-only проверкой запрошен кнопками;
до ответа внешних git writes не выполнять.
План: сверить текущий local/remote workflow, проверить gate и тесты, независимая
ревизия; после выбора владельца выполнить только разрешённую часть и commit.
Наблюдение: local blob d0efd7a3cb59be932f508229d5b02f69fa771bdb уже содержит
подключение, remote main blob cec3408611b7a8952003c77230f53eb9030a80e5 отличается.
R13 implementation pending verification; R14/R15 pending.

### Отложено владельцем: обязательная проверка перед выпуском

2026-10-20 владелец решил: «можно пока пропустить этот этап, develop в main
пока рано заливать», затем остановил работу. По отдельному поручению оставлена
эта заметка для подготовки будущего выпуска. Публикация подключения отложена;
само наличие заметки не разрешает merge, push или deployment.

- [ ] При подготовке PR develop → main проверить, что итоговый
  `.github/workflows/deploy-production.yml` содержит `environment: production`
  у job со ВСЕМИ SSH/SCP операциями, включая проверку подключения.
- [ ] Перед выпуском повторно проверить реальные production rules: reviewer
  CodexDLC, разрешённая branch main, отсутствие admin bypass и выбранный self-review.
- [ ] После разрешённого слияния проверить опубликованный workflow в main;
  до этого НЕ считать approval действующим для старого remote workflow.
- [ ] Отдельно решить перенос ENV_FILE/HOST/SSH_KEY/USERNAME из repository secrets
  в production environment; значения GitHub обратно не отдаёт. Не удалять старые
  secrets до подготовки и проверки замены. Это остаётся открытым пунктом A08-11.

Подключение локально уже реализовано в d5218eef. Повторная проверка ведущего:
82 tests passed. Независимый workflow_connection_review подтвердил локальную
цепочку и отдельно выполнил 82 tests (exit 0); remote main без environment.
R13 local pass / remote deferred; R14 review pass; R15 pass (публикация отложена).
Новых изменений workflow, push/PR/merge/deploy не было. Эта запись — напоминание
в том же плане, а не завершение operational A08-11 и не новый этап реализации.


### Синхронизация сводок и граница работы над чатом — 20.10.2026

Поручение владельца: поставить подтверждённые галочки, зафиксировать сделанное;
чат считать ранней альфой и планировать его дальнейшую разработку отдельно.
R16: синхронизировать реестр 10, сводку 11 и очередь с уже проверенными
результатами, не закрывать отложенную публикацию/secret migration.
R17: сохранить отдельную будущую работу над чатом; шаг 8 — технический backlog,
а не полный план готовности чата. Новую реализацию сейчас не начинать.
План: исправить устаревшие текущие сводки; сохранить исторические свидетельства,
ссылки на evidence и прежние ограничения. Режим ревизии продолжения сохраняется.
Файл задачи по task-review-gate — этот существующий MD, разделы 5.7/5.8 и
operational continuation; отдельного дубликата в tasks/ не создавали.
Проверка синхронизации: независимый status_sync_review подтвердил R16/R17,
сверив diff, сохранённый API readback и commits d5218eef/06ef3471/183246e5.
Блокирующих замечаний нет; diff --check пройден. Новые tests/remote calls не нужны:
это фиксация ранее проверенных результатов, не повторная runtime-аттестация.
R16/R17 done/pass; reviewed-awaiting-acceptance. Изменения MD пока без commit.

## Шаг 6 — A05-05: Streams pending (20.10.2026)

Запрос владельца: «Да, A05-05, с ревизором». Уточнение: пока без коммита.
S6-R1: обработать зависшие accepted backend stream messages после crash/error;
доказать состояние сообщения через реальные Redis pending/restart tests.
S6-R2: не допустить повторных эффектов при неопределённом исходе первого handler;
не выдавать transport dedup marker за atomicity SQL/Redis/Mongo эффектов.
S6-R3: сохранить payload и идентичность stream/group/message для retry либо
разбора; учитывать trimming и сообщения, payload которых уже удалён.
S6-R4: подключить решение к действующему runtime, не править установленную
библиотеку; не менять gameplay, реальные данные, secrets, production.
S6-R5: тест сначала, профильные проверки и независимый fresh reviewer с отдельной
сверкой claims. Без commit/push/deploy. Три текущих MD правки сохранить.
Первоначальный план: проверить runtime hooks и consumer idempotency; выбрать
безопасный recovery вместо безусловного replay; воспроизвести отказ на isolated
Redis, реализовать адаптер, проверить оба runtime entrypoints и границы отказов.
Статус: requirements recorded; design in progress; implementation pending.

### Решение и границы S6

У существующих inventory/loot handlers нет общей доказанной транзакционной
идемпотентности всех эффектов. Поэтому recovery не вызывает handler повторно:
старый PEL переносится в отдельный quarantine hash для reconciliation.
Сохранение raw fields + source stream/group/id и ACK выполняются одним bounded
Redis Lua script с повторной проверкой pending/idle; удалённый payload получает
явный tombstone. Это обработка stranded transport state, НЕ автоматическое
завершение gameplay и НЕ exactly-once effects. Поздно завершившийся старый
handler также оставляет исход неизвестным; оператор сверяет authority перед retry.
Retention shared game stream: прежний MAXLEN удалял pending/unread тела, поэтому
автоматический destructive trim отключается во всех найденных backend publishers.
Компромисс: stream/quarantine растут до отдельной group-aware retention policy;
maxlen не является жёстким memory cap. Чат-продукт и tg_bot собственный recovery
не перерабатываются; chat runtime на shared game stream получает только adapter.
Исходные SQL/Mongo/Redis операции не меняются; swallowed handler errors остаются
отдельным ограничением. Проверки реального Redis используют одноразовый контейнер
redis:7-alpine на random loopback port, без persistence и подключения real config.

Реализация использует HSETNX envelope по исходному ID в group-specific hash:
при отказе XACK запись уже сохранена, повтор не создаёт дубликат и не перезаписывает
исходные данные. Lua ошибки не считаются транзакционным rollback.
Наблюдение ведущего: первый широкий прогон core/chat/realtime — 214 passed,
10 skipped и один ожидаемый fail старого MAXLEN expectation; обновляется контракт
сохранения сообщений. Scoped mypy нашёл два annotation-дефекта eval, исправляются.
Это промежуточные результаты, не финальная приёмка.


### S6: проверки окончательного кода

Исполнитель streams_recovery_design записал failing test до production edits:
ModuleNotFoundError нового recovery module; это structural RED, не real crash
RED. Затем собственный bus прогон — 30 passed, включая 9 real Redis scenarios.
Ведущий независимо выполнил окончательный broader command:
`RUN_STREAM_RECOVERY_REDIS_TESTS=1 python -m pytest tests/backend/core tests/backend/chat tests/backend/realtime --no-cov -q -o addopts=''`:
**230 passed, 3 skipped**, exit 0. Skips — отдельные opt-in Mongo archive и
Redis WS revocation проверки вне этого изменения; они не считаются pass.
Evidence: `var/audit/a0505-final-tests.txt`. Ruff check/format 10 изменённых
Python-файлов и scoped mypy 7 source-файлов прошли. Полный project gate не запускался.
Реальный Redis проверил before/after-effect cancellation+runtime restart,
parallel scanners/group isolation, fresh delivery, threshold, missing payload,
wrong quarantine type и XACK ACL failure после HSETNX с безопасным повтором,
сохранение pending/unread после публикации 301 событий при прежнем maxlen=2.
Это не OS kill, не crash Redis и не подтверждение cross-store exactly-once.
Первичная независимая ревизия streams_quarantine_review: code-correctness finding
нет, запросила lifecycle proof; добавлены реальные start/stop/restart tests,
финальная delta verification и claims check ожидаются. До них новых галочек нет.


### S6: независимая приёмка

Fresh streams_quarantine_review, fork_turns=none, получил нейтральные требования
S6-R1–R5 и первичные code/test paths без отчёта исполнителя. Первичный verdict:
R2–R4 pass, R1 требовал lifecycle proof. После добавления двух реальных Redis
runtime cancellation/restart cases reviewer независимо выполнил **19 tests**,
Ruff check/format 10 файлов и scoped mypy 7 source-файлов — pass.
Затем отдельно сверил точные claims C1–C6: runtime wiring; HSETNX-before-ACK и
no replay; MAXLEN removal и growth limitation; root 230 passed/3 skipped;
reviewer 19 cases и отсутствие OS/disk crash evidence; no commit/push/deploy.
Claims подтверждены в заявленных пределах, существенных замечаний не осталось.

- [x] S6-R1: старый PEL сохраняется для reconciliation, adapter/lifecycle Redis pass.
- [x] S6-R2: recovery не повторяет handler и не заявляет business exactly-once.
- [x] S6-R3: identity/raw payload, tombstone и повтор после ACK failure проверены.
- [x] S6-R4: три runtime entrypoints и два shared publishers; installed library
  и gameplay не менялись. Backend/quality skills сверены, противоречий не найдено.
- [x] S6-R5: профильные проверки, независимый review и claims check пройдены;
  test-first structural RED записан как наблюдение исполнителя. Commit не сделан.

Состояние S6: reviewed-awaiting-acceptance в transport/quarantine scope.
Автоматическое бизнес-восстановление, domain idempotency/reconciliation,
group-aware retention и Redis disk persistence не закрыты этой работой.
Тестовые Docker containers удалены; зависшие sandbox asyncio тест-процессы
точно идентифицированы по PID/command line и остановлены. Реальные stores не трогались.
Итоговые pre-commit checks по изменённым файлам прошли, включая markdownlint,
Bandit, pip-audit и detect-secrets; skip только для отсутствующих типов файлов.
Git diff --check чистый, index пустой, HEAD остаётся 183246e5. Без коммита.

## Шаг 7.1 — A04-11: единый retry budget GenerationAI (20.10.2026)

Запрос: «следующую задачу из шага 7 ... только одну ... с ревизором.
Пока без коммита, push и деплоя».
G71-R1: устранить cooldown, недостижимый SQL claim из-за расхождения между
schema retry limit (8) сервиса и сохранённым task.max_attempts.
G71-R2: сохранить существующее намерение schema retry до 8 и больший явно
заданный budget; обычные ошибки не получают расширение. Достигнутый предел terminal.
G71-R3: сначала failing regression, затем исправление и проверка реального SQL
attempt predicate через оба claim entrypoints. Провайдер AI не вызывать.
G71-R4: одна находка A04-11, independent reviewer/claims; остальные A04-12/13/18,
A05-07/08 и A09-09 сейчас не исправлять. Все существующие uncommitted изменения
сохранить. Без commit/push/deploy, реальных хранилищ и gameplay изменений.
План: воспроизвести достижение малого budget при schema failures; сохранять
эффективный budget в той же SQL transaction до cooldown; terminal и обычные ошибки
проверить отдельно; isolated PostgreSQL claim tests, профильный suite, review.
Статус: requirements recorded, implementation pending. Подзадачи шага 7 дальше
выполняются только по отдельной команде владельца.

G71: граница восстановления старых задач. Исправление действует при очередном
решении о cooldown и не массово переписывает уже застрявшие строки. Для старого
cooldown с исчерпанным прежним budget требуется явный re-enqueue с увеличенным
max_attempts после разбора оператором. Scanner/recovery scheduling A05-08 в эту
задачу не включён. Текущие запросы/real task rows не изменяются.
Наблюдение исполнителя RED до production edits: disposable PostgreSQL regression
получил saved.max_attempts=3 при ожидании8 после schema-error cooldown.
Далее выбран минимальный update tracked ORM task.max_attempts перед существующим
mark_cooldown/flush в той же transaction; schema-error классификация не меняется.


### G71: проверки ведущего

Окончательный source diff A04-11 — сохранение task.max_attempts=retry_limit перед
mark_cooldown. Claim SQL predicates и policy классификация не менялись.
Тесты: RUN_GENERATION_RETRY_POSTGRES_TESTS=1,
`python -m pytest tests/backend/features/generation_ai --no-cov -q -o addopts=''`
на isolated PostgreSQL16 — **52 passed**, exit0, 11 actual PostgreSQL cases.
Evidence: `var/audit/a0411-final-tests.txt`. На каждую попытку используется свежая
SQL session; обе claim-ветки проверены до terminal, включая not_before guards,
JSON budget3→8, explicit12, generic JSON/nonJSON и manual raised-budget recovery.
Mongo payload store изолирован double, AI provider не вызывается, ARQ Redis enqueue
не тестируется этой находкой. SQL/Mongo atomicity и scheduler recovery не заявлены.
Интеграционные tests opt-in RUN_GENERATION_RETRY_POSTGRES_TESTS=1; default CI
получает fast regression в существующем test_generation_ai_core.
Ruff3files/format services+new test и scoped mypy service прошли. Полный project
gate не запускался. Наблюдение RED исполнителя — tool0992ad, отдельный файл не
сохранён; независимо восстановить хронологию из финального дерева нельзя.
Независимая ревизия и отдельная claims сверка пока ожидаются; галочки не поставлены.


### G71: независимая приёмка

Fresh generation_retry_review (fork_turns=none) получил исходное поручение,
нейтральные G71-R1–R4 и первичные paths без отчёта исполнителя. Проследил ORM
identity/get/hydration/flush/commit, самостоятельно проверил Ruff3files/mypy1source,
сверил сохранённый GREEN лог52/11PostgreSQL. Первоначальное замечание: integration
fixture должна быть opt-in; добавлен RUN_GENERATION_RETRY_POSTGRES_TESTS=1.
После первичного заключения отдельно сверил claims C1–C5: единый stored budget,
SQL claim reachability/terminal и отсутствие provider calls, focused checks,
отсутствие bulk repair и незатронутые соседние finding contracts, сохранённые
предыдущие dirty изменения. Claims подтверждены в доступных границах; хронология
RED атрибутирована исполнителю, не независимому проверяющему. Findings не осталось.

- [x] G71-R1: persisted budget/cooldown согласованы; PostgreSQL fresh-session claims pass.
- [x] G71-R2: schema8/explicit12, ordinary/nonJSON и exhausted terminal pass.
- [x] G71-R3: RED наблюдение исполнителя; ведущий52GREEN/11PostgreSQL и независимая
  проверка primary evidence; AI provider не использовался.
- [x] G71-R4: одна A04-11, существующие dirty изменения сохранены; no commit/push/deploy.

Состояние 7.1: reviewed-awaiting-acceptance. Остальные задачи шага7 не начаты.
После тестов только Ruff formatting exception literal и allowlist comment для
очевидного синтетического пароля одноразовой PostgreSQL; поведения не меняют.
Первый hook detect-secrets остановился на этом synthetic URL, не на настоящем
credential. Не менялись baseline/глобальные исключения scanner. Повтор всех hooks
по файлам задачи прошёл, включая pip-audit/Bandit/detect-secrets. Контейнеры удалены;
HEAD183246e5 и пустой index подтверждены, без коммита.

## Шаг 7.2 — оставить только AI-тексты предметов (20.10.2026)

Прямое поручение владельца: «код ... кроме текстов вынести в архив с теми же
путями только папка не src а архив ... выпиливаем вообще». Уточнение до этого:
остаются описания предметов, новости используют готовый набор маскотов.
Режим с ревизором продолжается; без commit/push/deploy. Это согласованное изменение
scope: вместо последовательного ремонта остальных AI-потребителей — их retirement.
AR-R1: в live runtime только items.text; по-прежнему name+description (изменение
формата на description-only не поручено). Worker/repository/JSON provider сохранить.
AR-R2: полностью убрать AI текста мира и image генерацию/news API/vision calls,
их producers/CLI, настройки и импорты; обычную карту/боевых ботов не менять.
AR-R3: source originals архивировать byte-identical: src/<path> → archive/<path>;
tools/<path> → archive/tools/<path>; tests → archive/tests/<path> для retired tests.
Смешанные модули перед правкой сохранить целиком по тому же правилу; live копия
содержит только оставшийся функционал. Без overwrite чужих архивов; manifest SHA256.
AR-R4: готовые маскоты, ручной выбор обложек и existing assets/storage-serving
сохранить; storage-only утилиты не считать image generator. Данные/SQL/realqueue
не удалять. Старые unsupported jobs terminal до provider, не слепой retry.
AR-R5: regression RED сначала, import/caller coverage, профильные tests и review
с отдельной claims сверкой. Все существующие dirty изменения сохраняются.
Replacement-only для убранных путей: без disabled fallback реализаций в src.
План: два исполнителя с раздельными файлами — central AI и world/tools; затем
интеграция, inventory по остаточным imports/calls, bytehash manifest, tests, review.
Проверенные абсолютные корни: D:/Workspace/personal/pets/TurnBasedMMORPG/src и
D:/Workspace/personal/pets/TurnBasedMMORPG/archive, оба внутри workspace.
Статус AR-R1–R5 pending, независимая приёмка до галочек обязательна.


### AR: реализация и проверки до claims review

Архив: `archive/ai_retirement_manifest.json`, 48 оригиналов с SHA256. `moved`
полностью убраны из live paths, `split` сохраняют полную исходную версию перед
очисткой смешанного модуля. Архивные paths точно заменяют src→archive; отдельные
tools/tests/docs сохраняют свой префикс под archive. Новый archive/.gitattributes
задаёт -text для raw-copy поддеревьев, чтобы Git не ломал provenance newline conversion.
Root archive contract: RED отсутствующего manifest → GREEN1pass после сборки.
Другие RED: registry/CoreAI surface и порядок terminal retirement передclaim
наблюдены исполнителями до соответствующих production edits.

Root broader command охватывал core, GenerationAI, items, world, retiredmonster
boundaries, Rift bootstrap, archive contract и frontend mascot cover library;
RUN_GENERATION_RETRY_POSTGRES_TESTS=1: **519 passed, 9 skipped, 1 failed**.
Failure: items/test_catalog_service.py::test_jewelry_power_is_flat_magic_armor_and_implicits_are_slot_profiles,
ожидание только mental_resistance, фактически также hp_regen. Standalone повтор
падает так же; git diff HEAD по src/backend/features/items и tests/backend/features/items
пустой. Каталог/тест не менялись этой задачей и gameplay fix не выполнялся.
Логи: var/audit/ai-retirement-final-tests.txt и ai-retirement-catalog-existing-failure.txt.
9 skipped — opt-in Redis recovery сценарии предыдущей задачи, не pass.
Отдельные исполнения: core168passed (включая20 realPG), world60passed;
reviewer послеfix34passed exit0. Provider ни в одном тесте не вызывался.

Root mypy10source: 1 error в game container — object not callable на неизменённом
HabitatClanPoolMaterializationResult из динамического monsters.public facade.
Сохранённая HEAD-версия game module даёт ту же ошибку на той же строке выражения;
baseline log var/audit/ai-retirement-baseline-mypy.txt содержит также ожидаемые
missing old-world-import/config от проверки старого файла в новом дереве.
Не выдавать это за clean full-project typing. Остальные9sources без ошибок.
Полный project gate не запускался. Ruff/live hooks прошли; EOFfix исправил одну
пустую строку и отдельный повтор прошёл. Архивы не auto-format, detect-secrets
по архивным оригиналам прошёл. Реальные базы/очереди/env/assets не менялись.

Дополнительная независимая находка P2: exhausted/future retired queued jobs не
могли claim. Исправление: transactional retire_unsupported_by_id перед обычнымclaim,
SKIPLOCKED, без attempt/timegates, только pending/cooldown unsupportedtype/output.
Terminal/running history сохраняется; SQL tests проверили rowlocks и20cases.
Не вводился массовый scanner/удаление очереди; меняется только будущая обработка
доставленных старыхjobs. Актуальная независимая claims review ожидается.


### AR: независимая приёмка и окончательное состояние

Fresh ai_retirement_review, fork_turns=none, получил исходное поручение и AR-R1–R5
без отчёта исполнителя. Выявил P2 preclaim retirement, исправление проверено по
новому SQL-коду и primary log20Postgrescases. Самостоятельный post-fix focused
прогон —34passed exit0. После первоначального verdict отдельно проверил C1–C7:
все48hash/mapping и attrs, root broad519/9/1 и standalone jewelryfailure с пустым
itemdiff, baseline HEAD game expression mypyerror, core168/20Postgres.
Итог: существенных замечаний к AI retirement не осталось, но fullprojectpass
не заявляется. Hooks/mypy10sources — наблюдения ведущего, не запуск reviewer.

- [x] AR-R1: только items.text/json; worker/repository и prior A04-11 fix сохранены.
- [x] AR-R2: удалённые generators/CLI/imports/flags отсутствуют в src/tools;
  обычный WorldGenerator и combat bots сохранены.
- [x] AR-R3: 48 byte-identical original copies, manifest, path mirror, Git -text.
- [x] AR-R4: mascot picker/готовые assets/storage retained; 2 frontend cover tests
  и archive contract вместе3passed. Доставленные unsupported jobs terminal до
  provider с rowlock; реальные очереди/данные не менялись.
- [x] AR-R5: RED и проверки, independentreview + отдельныеclaims, dirtyStreams
  сохранены. Commit/push/deploy не выполнялись; HEAD183246e5, index пустой.

Статус: reviewed-awaiting-acceptance для retirement scope, без полного project
sign-off из-за отдельно записанных catalog-test/type-facade failures. Архивtests
исторические, не импортируются как live suite. Project skills/backend/gamecontent
проверены: item-text legacy narrative contract сохранён; docs/core/ai обновлён.
Остальные исторические AI-аудиты не закрывать автоматически: items.text всё ещё
нуждается в durable input/result, scheduling recovery и SQL lifetime исправлениях.

## Исправление устаревшего теста украшений — 20.10.2026

Запрос владельца: обновить тест под текущий каталог, с ревизором, без изменения
баланса, commit/push/deploy.
J-R1: добавить ожидаемые intrinsic support keys hp_regen/en_regen/stamina_regen
для ring/amulet/earring, уже введённые commit27562385; точный набор ключей проверять.
J-R2: сохранить assertions type/slot/base_power и отсутствие пересечения с
аффиксами. Каталог/значения/runtime не менять, dirty предыдущих задач сохранить.
J-R3: воспроизведённый ранее RED (jewelry hp_regen mismatch), профильные tests,
независимый review и отдельная claims сверка. Режим с ревизором выбран явно.
План: три expected set правки, catalog+support и затем items suite, reviewer.
Реализация/проверка pending. Малую правку выполняет ведущий; отдельный агент
используется только как выбранный владельцем независимый reviewer.

J: результат и независимая приёмка. Ровно3 expected sets обновлены, sourceitems
и его ресурсы относительно HEAD не менялись; проверки точного set/type/slot/power
и affix disjoint сохранены. Ведущий: весь items suite **163 passed**,6.33s,
artifact var/audit/jewelry-test-fix.txt. Hooks по изменённым файлам прошли, включая
Ruff/format/Bandit/pip-audit/detect-secrets/markdownlint.
Fresh jewelry_expectation_review (fork_turns=none) проверил neutralrequirements,
самостоятельно выполнил target **1passed**, затем отдельно сверил точныеclaims.
Замечаний нет. J-R1/J-R2/J-R3 done/pass; reviewed-awaiting-acceptance.
Конкретный ранее записанный jewelry failure исправлен. Широкий AI-retirement
прогон целиком не повторялся; прежняя mypy ошибка facade не исправлена.
Без commit/push/deploy. Предыдущие uncommitted изменения сохранены.

## Шаг 7.3 — A04-12/A05-07: durable input items.text (20.10.2026)

Запрос: «A04-12 — сохранность входных данных для items.text ... одну задачу
с ревизором ... без коммита, push и деплоя».
IN-R1: задача items.text не принимается/не schedules без подтверждённого initial
payload; initial Mongo outage должен дать явный отказ, а не bare pending SQL row.
IN-R2: повторный enqueue/restart/claim не использует пустой или неподтверждённый
input при Mongo read failure/missing/malformed документе; без AI вызова и без
необоснованного расхода attempts. GET истории может возвращать SQL metadata.
IN-R3: не вводить fallback/dual source of truth; PostgreSQL metadata + Mongo heavy
input сохранить. Нельзя объявлять общую SQL/Mongo atomicity. Возможные orphan
Mongo docs после отказа SQL относятся к A04-18, не чистятся здесь автоматически.
IN-R4: failing test до source, real isolated SQL/Mongo boundary tests на startup
outage/read outage/restart, independentreview + claims. Провайдер/realstores/env
не трогать. Старый monster facade/my py type error остаётся отложенным до
игровой migration; все текущие dirty изменения/архив48hash сохранить.
План: failclosed creation до persistence SQL runnable row; strict input validation
на accepted/reused and claimed path; сохранить metadata history/retiredjob behavior;
fault injection actual isolatedDB adapters, полный relevant suite, review.
Статус IN-R1..R4 pending; без commit/push/deploy. Режим с ревизором выбран явно.

IN: независимый reviewer item_input_review проследил границу reuse и выявил
P2: мягкая hydration могла переписать SQL mongo_document_id до строгой проверки,
маскируя несовпадение Mongo document pointer. Исправляется разделением transient
payload hydration и authoritative SQL metadata: чтение не переписывает pointer.
Проверка должна включать отказ reuse с последующим catch+commit и неизменность
SQL pointer/schema. Это не восстановление/конвертация старых данных.

### IN: проверки ведущего

RED var/audit/a0412-red.txt: initial Mongo failure не вызвал исключение, service
вернул enqueue success. Исправление сохраняет подтверждённый input до SQL add,
а strict fetch перед reuse/claim происходит до изменения attempts/status.
Canonical identity пересчитывается по исходному input/prompt и SQL identity fields;
новые validation errors не печатают request. History hydration transient-only.

Ведущий: RUN_GENERATION_INPUT_STORE_TESTS=1 и RUN_GENERATION_RETRY_POSTGRES_TESTS=1,
`pytest generation_ai items core/test_ai_service privileged_operations archive_contract --no-cov -o addopts=''`:
**372 passed**, exit0,45.27s. var/audit/a0412-final-tests.txt.
Включены44new realSQL/Mongo cases и20existingSQL budget/retirement cases.
Faults воспроизводились коллекционными fault-injection adapters поверх изолированной
Mongo; успешное сохранение/restart проверены новыми SQL sessions/Mongo clients.
Это не потеря диска/OS-kill/репликационный failover, такие гарантии не заявлены.
Ruff check/format4files и scopedmypy3source pass; первое найденное annotation
несоответствие output_kind исправлено на явный json для live-only helper.
Фасад монстров не менялся, его error остаётся отложенным; полного projectgate нет.
Архив48hash проверен прежним контрактным тестом, архивные bytes не менялись.
Hooks по изменённым4файлам в процессе; independentclaims pending до галочек.


### IN: итог независимой приёмки

Fresh item_input_review, fork_turns=none: neutral IN-R1–R4 и primary code/testpaths
без отчёта исполнителя. Первичный source review выявил pointer hydration bypass;
исправление независимо прослежено и проверено actualSQL regression.
Самостоятельно выполнил44 isolatedSQL/Mongo tests, exit0. После первогоverdict
отдельно проверил claims C1–C6: root372/44new/20priorPG и REDartifact, sourceownership,
no fallback/cache, pointerimmutability, puremetadatahistory и целостностьarchive.
Замечаний не осталось. Mypy3sources подтверждён отдельно, Ruff/format4files —
по toolрезультатам ведущего. Общего projectgate и SQL/Mongo atomicity не заявляли.

- [x] IN-R1: подтверждённый initialwrite/readback перед SQLadd, explicit refusal.
- [x] IN-R2: fresh validated input до reuse/claim и attempts, corrupt/cache tests pass.
- [x] IN-R3: single durableinput store, SQLmetadata ownership, no automatic orphancleanup.
- [x] IN-R4: RED, реальный isolatedSQL/Mongo, independentreview/claims; без realprovider.

Состояние: reviewed-awaiting-acceptance для A04-12 input-contract scope.
Git HEAD183246e5 и пустойindex; Docker fixturecontainers удалены; без commit/push/deploy.
Статус hookchecks: все применимые прошли, КРОМЕ pip-audit. Scanner сообщил
certifi2026.4.22 GHSA-6q48-6c7w-9gw2, fix2026.10.19. Никакого skip/waiver/lockupdate
не делали: single-task scope сохранён, dependency finding оставлена отдельной.
Поэтому полный cleanquality не заявляется; source fix/372tests/review подтверждены.

## Отдельный шаг: security update certifi — 20.10.2026

Запрос владельца: обновить certifi, проверить совместимость и pip-audit;
без ревизора, commit/push/deploy, после отчёта остановиться. Режим ordinary check
явно выбран для текущих задач; общая независимая ревизия накопленного пакета позже.
C-R1: certifi2026.4.22 → исправленная2026.10.19 либо совместимая выше; закрепить
security floor и согласовать uv.lock/.venv. Другие package versions не менять.
C-R2: locked resolution, pip check, загрузка CA bundle/TLS context, адресные HTTP/AI
integration tests, существующий pip-audit hook без skip/новых исключений.
C-R3: все dirty code/archive48hash сохранить; без любых production операций.
План: сохранить before-lock/package inventory, добавить constraint certifi>=2026.10.19,
targeted uv lock upgrade, установить только certifi из lock в текущуюvenv,
сверить package delta и применить проверки. No reviewer requested.
Источник fixversion: https://github.com/advisories/GHSA-6q48-6c7w-9gw2 .
Статус C-R1..C-R3: выполнено, обычная проверка завершена.

- [x] C-R1: certifi2026.10.19 в uv.lock и .venv; constraint >=2026.10.19.
  Сравнение before/after lock и нормализованного installed inventory:
  единственная изменённая версия — certifi2026.4.22 → 2026.10.19.
- [x] C-R2: uv lock --check и pip check exit0; CA bundle существует,
  SSL context загрузил120 CA, httpx TLS client и requests Session создаются.
  Core AI/executor/frontend backend_api: 29passed,1 upstream Google deprecation
  warning, exit0. Существующий pre-commit pip-audit --all-files: Passed, exit0;
  прежние7 advisory exceptions сохранены, skip/новые исключения не добавлялись.
- [x] C-R3: source/archive и игровые данные не менялись этим шагом.
  Изменения шага: pyproject.toml, uv.lock и две записи audit/progress.
  Без ревизора, commit/push/deploy. После отчёта остановка.

Проверка локальная Windows/Python3.14; CI Linux/Python3.13 и реальные внешние
HTTPS endpoints не запускались. Историческая запись выше о блокировке pip-audit
описывает состояние до отдельного обновления; текущий hook прошёл.


## Шаг 7.4 — A04-13: durable result items.text — 20.10.2026

Запрос: исправить сохранность результатов items.text, проверить, остановиться.
Без ревизора, commit/push/deploy. Reviewer: not-requested.
R13-1: SQL done только после подтверждённой записи полного результата в Mongo;
ошибка записи/подтверждения не должна оставлять done даже при caught exception + commit.
R13-2: existing input document/pointer/schema/identity сохраняются; не создавать
замещающий документ из transient cache; проверить restart/readback и сбои.
R13-3: только инфраструктурный контракт, без изменения баланса/старого monster facade;
сохранить накопленные правки. SQL/Mongo atomicity, enqueue recovery A05-08,
orphan reconciliation A04-18 и lifetime transaction A09-09 — отдельные задачи.
План: RED isolated SQL/Mongo regression, strict acknowledged result write/readback,
перенос SQL completion после подтверждения, focused/wider tests и quality hooks.
Implementation: pending. Verification: pending. Проверяет ведущий.


### R13: реализация и обычная проверка

- [x] R13-1 implementation done / verification pass: mark_done не меняет SQL
  completion fields до подтверждённого result write/readback. _record_result_payload
  больше не подавляет storage error. RED: outage regression DID NOT RAISE до правки,
  var/audit/a0413-red.txt. GREEN: caught error + commit оставляет running без completed_at;
  service after apply уходит в cooldown/failed, не done.
- [x] R13-2 implementation done / verification pass: перед completion fresh input
  validation; result update только existing pointer+identity+schema, upsert=False;
  acknowledgement/matched_count и полное сравнение output/metadata/error при readback.
  Проверены outage/unacknowledged/no-match/missing readback/corrupt payload/metadata/
  pointer/identity/schema, удалённый input и новое Mongo client/SQL session чтение.
  Речь об отсутствии fallback именно в result write; error history имеет отдельный
  прежний контракт. Нет межхранилищной atomicity или provider exactly-once guarantee.
- [x] R13-3 implementation done / verification pass: gameplay balance, facade,
  production и архивные originals не изменялись этим шагом. Archive contract test
  включён в итоговый прогон. Index не пополнялся, commit/push/deploy не выполнялись.

Проверял ведущий, независимый reviewer not-requested.
Итог: 385passed,2 existing upstream deprecation warnings,47.90s, exit0;
в том числе57 isolatedSQL/Mongo input/result cases (13 новых) и20 priorPG cases.
Команда: RUN_GENERATION_INPUT_STORE_TESTS=1 RUN_GENERATION_RETRY_POSTGRES_TESTS=1;
pytest generation_ai + items + core/test_ai_service + privileged_operations_access
+ test_ai_archive_contract, --no-cov -o addopts='', disposable local stores.
Artifact: var/audit/a0413-final-tests.txt; first54 green: var/audit/a0413-green.txt.
Mypy3sourcefiles pass. Все применимые hooks4Python files Passed, включая pip-audit,
Bandit, Ruff/format и detect-secrets; var/audit/a0413-hooks.txt. Full project gate,
Linux CI, production и realAI не запускались. SQL transaction lifetime A09-09,
commit→enqueue A05-08 и orphan reconciliation A04-18 остаются открытыми.
Статус: checked-awaiting-acceptance. После отчёта остановка.


## Шаг 7.5 — A05-08: SQL commit → queue recovery — 20.10.2026

Запрос: исправить восстановление постановки после SQL commit; проверить и остановиться.
Без ревизора, commit/push/deploy. Reviewer not-requested, проверяет ведущий.
R08-1: committed live items.text pending/due cooldown с attempts < max_attempts
повторно доставляются после потери процесса/Redis enqueue failure; SQL — durable source.
R08-2: rollback/future/exhausted/running/terminal/retired не доставляются recovery;
ограниченная выборка, продвижение по backlog, безопасные дубликаты и повторные проходы.
R08-3: подключить recovery к реальному GenerationAI worker; тесты реальных SQL/Redis,
проверка regressions. Накопленные изменения сохранить; gameplay/provider/production не менять.
План: RED missing recovery test; SQL due-ID page + bounded cursor replay service;
ARQ stable IDs и cron at startup/every30s; fault/restart/concurrency tests и quality.
SQL/Mongo orphan reconciliation и recovery running after crash — отдельные задачи.
Implementation done / verification pass в указанном scope.

- [x] T-R1: explicit selectors; integration имеет приоритет над unit при двойной
  маркировке, unmarked → regression. External отмечены для Docker/Compose,
  GenerationAI stores, migrations/auth PostgreSQL, Streams Redis, chat Mongo,
  session-lock Redis и real WS Redis. Existing env/URL guards сохранены.
- [x] T-R2: no-cov только для3focused stages, suite использует исходный coverage74.
  Интерактивный runner по-прежнему спрашивает integration; --ci исполняет все4.
  Suite сознательно повторяет3stages. Общий coverage не измерялся.
- [x] T-R3: installed BaseCheckRunner command + synthetic real pytest collection:
  unit/integration/двойной marker/unmarked/external cases. Matrix4554collected:
  unit1682, integration41, regression2661, suite4384, external170. Disjoint union
  и отсутствие external в suite проверены assertions. Artifact a0611-matrix.json.
- [x] T-R4: 276passed/170deselected (19.45s), scoped hooks включая pip-audit Passed.
  Проверял ведущий; reviewer not-requested; checked-awaiting-acceptance.

Evidence в var/audit/: a0611-red.txt (исходный пустой selector), a0611-tests.txt
(70passed), a0611-final-tests.txt (276passed), a0611-hooks.txt; matrix-default.txt,
матрица json и воспроизводящий диагностический a0611_matrix.py. Временный helper
сначала неверно извлекал Python -m вместо pytest -m; исправлен до green-проверок.

Ограничение: обычный full collection падает из-за двух test_combat_actor_input.py
(character/runtime и monsters/instances/runtime), artifact a0611-collection.txt.
Diagnostic importlib дал другой старый bare import test_squad_selection_service
в monster difficulty test (a0611-matrix.txt). Поэтому final matrix использует
обычный import mode и --ignore только monsters/instances/runtime/test_combat_actor_input.py.
Это исключение НЕ внесено в config/runner/CI; полный gate остаётся незелёным.
Никаких тестов/Legacy файлов не удалено, gameplay не менялся. Полную переаттестацию
existing unit labels и collection repair оставить отдельной задачей.

Scope: pyproject test settings; external labels (15testmodules); новый runner/pytest
selection test; docs/testing_strategy и audit plan/registry. Предыдущие certifi/Pillow
и все накопленные uncommitted changes сохранены. Commit/push/deploy не выполнялись.
После отчёта остановка.


### R08: реализация и обычная проверка

- [x] R08-1 implementation done / verification pass: list_schedulable_ids читает
  SQL delivery intent из отдельной сессии worker recovery. replay_scheduling_page
  не меняет SQL при успешном/неуспешном enqueue. Cron зарегистрирован в реальном
  GenerationAIArqSettings при старте и second={0,30}. RED missing method доказан
  isolated SQL regression; var/audit/a0508-red.txt.
- [x] R08-2 implementation done / verification pass: только live json, due/budget
  predicates, bound1..1000 (runtime100), keyset cursor/wrap. Stable recovery job ID,
  SQL claim guard сохраняется; два concurrent Redis scans создают1 job. Проверены
  отсутствие committed visibility до commit/после rollback, future/terminal/running/
  exhausted/retired фильтрация; очередь удалена и восстановлена из неизменённой SQL.
  После первого SQL claim следующий duplicate claim не расходует попытку.
- [x] R08-3 implementation done / verification pass: 7 новых tests, включая actual
  SQL/Mongo/ARQ Redis adapters и actual worker function/wiring, isolated Docker fixtures
  с finally cleanup. Без настоящих provider calls/production; source archive hash
  contract проверен широким прогоном. Без миграций и изменения gameplay.

Проверял ведущий, reviewer not-requested. 392passed,2 existing upstream deprecation
warnings,54.87s,exit0. GenerationAI + items + core AI + privileged access + archive
contract; RUN_GENERATION_INPUT_STORE_TESTS=1 и RUN_GENERATION_RETRY_POSTGRES_TESTS=1,
--no-cov -o addopts=''. Artifact var/audit/a0508-final-tests.txt.
Первые recovery tests7passed: var/audit/a0508-green.txt. Mypy4sourcefiles pass:
var/audit/a0508-mypy.txt. Применимые pre-commit hooks5Pythonfiles Passed, включая
Ruff/format/Bandit/pip-audit/detect-secrets: var/audit/a0508-hooks.txt.
Full project gate/Linux CI/real deployment не запускались. Ограничения: at-least-once,
очередь/provider не exactly-once, cursor loss безопасно повторяет обход; длительность
обхода зависит от backlog/worker availability/ARQ result TTL. Running recovery после
process crash, orphan reconciliation A04-18 и transaction lifetime A09-09 не закрыты.
Статус checked-awaiting-acceptance. Без commit/push/deploy; после отчёта остановка.


## Шаг 7.6 — A04-18: Mongo reconciliation — 20.10.2026

Запрос: сверка/восстановление несвязанных Mongo-документов GenerationAI; исправить,
проверить, остановиться. Без ревизора/commit/push/deploy. Reviewer not-requested.
R18-1: bounded restart-safe сверка Mongo→SQL для live items.text/json; SQL authority.
R18-2: восстановить missing SQL pointer лишь при existing matching SQL row и valid
input/hash/schema, done требует valid result; не overwrite conflicting pointer,
не создавать SQL task из orphan Mongo, не применять результаты/не вызывать provider.
R18-3: orphan/conflict/uncommitted result сохраняются с диагностическим состоянием;
никаких delete/TTL. Grace window1h, conditional metadata updates, busy rows deferred.
R18-4: реальный worker wiring, isolated SQL/Mongo failure/rollback/restart tests,
регрессии/quality. Накопленные правки сохранить, реальные хранилища не трогать.
План: RED orphan/rollback test; adapter paging/CAS marks, feature reconciliation,
separate worker cron every5min; outcome checks and broader suite.
Предположение: orphan SQL acceptance восстановить из Mongo нельзя; только existing
row repair. Исторические image/assets вне live пути; их массовая очистка не входит.
Implementation done / verification pass в указанном scope.

- [x] T-R1: explicit selectors; integration имеет приоритет над unit при двойной
  маркировке, unmarked → regression. External отмечены для Docker/Compose,
  GenerationAI stores, migrations/auth PostgreSQL, Streams Redis, chat Mongo,
  session-lock Redis и real WS Redis. Existing env/URL guards сохранены.
- [x] T-R2: no-cov только для3focused stages, suite использует исходный coverage74.
  Интерактивный runner по-прежнему спрашивает integration; --ci исполняет все4.
  Suite сознательно повторяет3stages. Общий coverage не измерялся.
- [x] T-R3: installed BaseCheckRunner command + synthetic real pytest collection:
  unit/integration/двойной marker/unmarked/external cases. Matrix4554collected:
  unit1682, integration41, regression2661, suite4384, external170. Disjoint union
  и отсутствие external в suite проверены assertions. Artifact a0611-matrix.json.
- [x] T-R4: 276passed/170deselected (19.45s), scoped hooks включая pip-audit Passed.
  Проверял ведущий; reviewer not-requested; checked-awaiting-acceptance.

Evidence в var/audit/: a0611-red.txt (исходный пустой selector), a0611-tests.txt
(70passed), a0611-final-tests.txt (276passed), a0611-hooks.txt; matrix-default.txt,
матрица json и воспроизводящий диагностический a0611_matrix.py. Временный helper
сначала неверно извлекал Python -m вместо pytest -m; исправлен до green-проверок.

Ограничение: обычный full collection падает из-за двух test_combat_actor_input.py
(character/runtime и monsters/instances/runtime), artifact a0611-collection.txt.
Diagnostic importlib дал другой старый bare import test_squad_selection_service
в monster difficulty test (a0611-matrix.txt). Поэтому final matrix использует
обычный import mode и --ignore только monsters/instances/runtime/test_combat_actor_input.py.
Это исключение НЕ внесено в config/runner/CI; полный gate остаётся незелёным.
Никаких тестов/Legacy файлов не удалено, gameplay не менялся. Полную переаттестацию
existing unit labels и collection repair оставить отдельной задачей.

Scope: pyproject test settings; external labels (15testmodules); новый runner/pytest
selection test; docs/testing_strategy и audit plan/registry. Предыдущие certifi/Pillow
и все накопленные uncommitted changes сохранены. Commit/push/deploy не выполнялись.
После отчёта остановка.


### R18: реализация и обычная проверка

- [x] R18-1 implementation done / verification pass: Mongo adapter bounded page
  (runtime100, allowed1..1000), old live item/json/string IDs, grace1h; cursor/wrap,
  independent worker cron startup/every5min. Mongo failure не продвигает cursor.
- [x] R18-2 implementation done / verification pass: existing row lock SKIP LOCKED,
  validated input/schema/canonical hash/SQL pointer; done проверяет GeneratedItemTextDTO.
  SQL repair только missing pointer/schema/store metadata. Не меняет execution status,
  attempts или payload/application. Conflicting pointer не перезаписывается.
- [x] R18-3 implementation done / verification pass: orphan/conflict/result_pending_review
  — advisory Mongo classifications с timestamp, conditional compare snapshot. Нет delete,
  TTL, task recreation/provider calls. Busy/stale deferred; поздний commit очищает orphan
  observation, не блокировавший claim. Mark failure не допускает SQL pointer repair.
- [x] R18-4 implementation done / verification pass: 20 новых проверок, реальные isolated
  SQL/Mongo; initial Mongo survived SQL rollback, pointer recovery, valid/invalid done,
  uncommitted output, pointer/schema/identity/input/metadata/output conflicts, concurrent
  Mongo change и busy SQL, repair rollback/repeat, late SQL commit, marker outage/unack,
  worker paging/grace/cursor failure/wiring и bounds. Existing archive hashes pass.

Проверял ведущий, reviewer not-requested. RED: missing reconciliation module,
var/audit/a0418-red.txt. First15green: var/audit/a0418-green.txt. После добавления
late-commit/failure tests первый широкий прогон410passed, var/audit/a0418-final-tests.txt.
Окончательный код после metadata/output и timezone checks: 412passed,2 existing
upstream deprecation warnings,62.63s,exit0; var/audit/a0418-final-v2-tests.txt.
Command: GenerationAI + items + coreAI + privileged access + archive contract,
RUN_GENERATION_INPUT_STORE_TESTS=1 / RUN_GENERATION_RETRY_POSTGRES_TESTS=1,
--no-cov -o addopts=''; одноразовые local Docker stores, finally cleanup.
Mypy6sourcefiles pass: var/audit/a0418-mypy.txt. Применимые hooks7Python files
Passed, включая Ruff/format/Bandit/pip-audit/detect-secrets: var/audit/a0418-hooks.txt.
Документация проверена markdownlint; full project gate/LinuxCI/realAI/production не запускались.

Ограничения: reconciliation Mongo→SQL, не backup recovery отсутствующего документа;
orphan без committed SQL acceptance не создаёт новую работу. Advisory mark может
пережить SQL rollback и исправляется следующим проходом. Старые image/assets,
документы вне live scope, running recovery и A09-09 transaction lifetime остаются
отдельно. Никакой destructive cleanup. Статус checked-awaiting-acceptance.
HEAD183246e5/index empty; без commit/push/deploy. После отчёта остановка.


## Шаг 7.7 — A09-09: AI вне SQL transaction — 20.10.2026

Запрос: убрать ожидание AI внутри SQL transaction, проверить и остановиться.
Без ревизора/commit/push/deploy, reviewer not-requested.
R09-1: request preparation + claim в короткой SQL transaction; commit и release
connection до provider await. Detached task input не должен лениво читать SQL.
R09-2: apply/result/retry в новой transaction после проверки running claim token
(id/revision/attempt/claimed_at). Stale response не применяется/не переписывает retry.
R09-3: duplicate delivery не запускает второй AI; provider failure/retry budgets и
A04-12/13/18/A05-08 guarantees сохраняются. Commit failure не вызывает provider.
R09-4: isolated SQL/Mongo tests проверяют открытую transaction/lock во время await,
reacquisition fencing, duplicate/failed commit/provider failure, regressions/quality.
Накопленные изменения сохранить. Running recovery после process death отдельно.
План: RED transaction probe; repository commit+detach/reacquire token, staged service
flow; tests/typing/hooks/docs. Implementation done / verification pass в указанном scope.

- [x] T-R1: explicit selectors; integration имеет приоритет над unit при двойной
  маркировке, unmarked → regression. External отмечены для Docker/Compose,
  GenerationAI stores, migrations/auth PostgreSQL, Streams Redis, chat Mongo,
  session-lock Redis и real WS Redis. Existing env/URL guards сохранены.
- [x] T-R2: no-cov только для3focused stages, suite использует исходный coverage74.
  Интерактивный runner по-прежнему спрашивает integration; --ci исполняет все4.
  Suite сознательно повторяет3stages. Общий coverage не измерялся.
- [x] T-R3: installed BaseCheckRunner command + synthetic real pytest collection:
  unit/integration/двойной marker/unmarked/external cases. Matrix4554collected:
  unit1682, integration41, regression2661, suite4384, external170. Disjoint union
  и отсутствие external в suite проверены assertions. Artifact a0611-matrix.json.
- [x] T-R4: 276passed/170deselected (19.45s), scoped hooks включая pip-audit Passed.
  Проверял ведущий; reviewer not-requested; checked-awaiting-acceptance.

Evidence в var/audit/: a0611-red.txt (исходный пустой selector), a0611-tests.txt
(70passed), a0611-final-tests.txt (276passed), a0611-hooks.txt; matrix-default.txt,
матрица json и воспроизводящий диагностический a0611_matrix.py. Временный helper
сначала неверно извлекал Python -m вместо pytest -m; исправлен до green-проверок.

Ограничение: обычный full collection падает из-за двух test_combat_actor_input.py
(character/runtime и monsters/instances/runtime), artifact a0611-collection.txt.
Diagnostic importlib дал другой старый bare import test_squad_selection_service
в monster difficulty test (a0611-matrix.txt). Поэтому final matrix использует
обычный import mode и --ignore только monsters/instances/runtime/test_combat_actor_input.py.
Это исключение НЕ внесено в config/runner/CI; полный gate остаётся незелёным.
Никаких тестов/Legacy файлов не удалено, gameplay не менялся. Полную переаттестацию
existing unit labels и collection repair оставить отдельной задачей.

Scope: pyproject test settings; external labels (15testmodules); новый runner/pytest
selection test; docs/testing_strategy и audit plan/registry. Предыдущие certifi/Pillow
и все накопленные uncommitted changes сохранены. Commit/push/deploy не выполнялись.
После отчёта остановка.


### R09: реализация и обычная проверка

- [x] R09-1 implementation done / verification pass: repository commit_claim_for_provider
  flushes prepared claim, captures frozen token, detaches task before commit, releases
  SQL transaction/connection, expires other loaded state. Both execution entrypoints
  use staged _execute_claimed_task. Provider snapshot has loaded fields and works
  with expire_on_commit=True/False; no SQL transaction and checkedout pool connections=0.
  Независимая SQL session читает committed running и получает row lock NOWAIT во время AI.
- [x] R09-2 implementation done / verification pass: reacquire_claim uses FOR UPDATE
  with running/id/revision/attempts/claimed_at/identity fence before apply/result/retry.
  5 ownership changes × success/failure =10 stale paths не меняют новый execution state,
  не применяют output и не создают чужой retry. Finalization остается caller commit.
- [x] R09-3 implementation done / verification pass: duplicate delivery during provider
  не вызывает второй AI, attempts остаются1. Claim commit failure propagates before AI;
  rollback оставляет pending/attempts0. Provider failures сохраняют обычные budgets,
  cooldown/failed и extended schema budget8. A04-12/13/18/A05-08 regression tests pass.
- [x] R09-4 implementation done / verification pass: 19 новых isolated SQL/Mongo cases,
  actual generation_ai_process_task с injected local executor/registry/store проверяет
  both commit points. Cancellation explicitly leaves committed running for separate
  recovery. Unit fake repository обновлён под новый processing boundary; A04-13 service
  fixture switched sessions.begin() → manual session + final commit, сохранив assertions.

Проверял ведущий, reviewer not-requested. RED: transaction probe приводит к failure
(result None после пойманной внутри service assertion); var/audit/a0909-red.txt.
First14green: var/audit/a0909-green.txt; ownership17: var/audit/a0909-owned-tests.txt.
Итог431passed,2 existing upstream deprecation warnings,69.75s,exit0;
var/audit/a0909-final-tests.txt. Command: generation_ai + items + coreAI + privileged
access + archive contract, RUN_GENERATION_INPUT_STORE_TESTS=1 и
RUN_GENERATION_RETRY_POSTGRES_TESTS=1, --no-cov -o addopts='', disposable local stores.
Mypy3sources pass: var/audit/a0909-mypy.txt. Применимые hooks6Pythonfiles Passed,
включая Ruff/format/Bandit/pip-audit/detect-secrets: var/audit/a0909-hooks.txt.
Documentation-only process_task ownership docstring добавлена после широкого прогона,
Ruff/format перепроверены; поведение не менялось. Markdownlint и diff whitespace проверены.
Full-project gate/Linux CI/realAI/production не запускались; archive hashes pass.

Processing владеет отдельной manual-commit session, не внешним begin/shared write UoW.
AI вынесен из transaction; SQL/Mongo result storage IO при финализации остаётся прежним.
Durable running после отмены/process death требует отдельного lease/recovery; нет
exactly-once provider guarantee. Gameplay balance и старый monster facade не менялись.
HEAD183246e5/index empty, без commit/push/deploy. Статус checked-awaiting-acceptance.
После отчёта остановка.


## Шаг 7.8 — running recovery после process crash — 20.10.2026

Запрос: восстановление зависших running GenerationAI; исправить/проверить/остановиться.
Без ревизора/commit/push/deploy; reviewer not-requested, проверяет ведущий.
LR-1: finite running lease, expiry recovery live items.text/json после committed claim;
не сбрасывать attempts, при exhausted budget terminal failure, очередь через A05-08.
LR-2: stale owner response/error не может apply/retry после expiry/requeue/new claim;
активные/new/locked rows не захватывать, concurrent sweeps безопасны и bounded.
LR-3: Mongo input/result проверить до requeue. Existing nonempty result сохраняется
для ручного разбора, без provider replay/overwrite; missing/corrupt input terminal
отказ. Mongo outage не доказывает corruption: rollback recovery и повтор позже.
LR-4: worker cron wiring, isolated SQL/Mongo/Redis recovery/crash/late-result tests,
regressions/quality/docs, сохранить accumulated work и не трогать реальные данные.
Выбранный план: fixed lease10min > worker timeout180s, без heartbeat/schema migration;
DB clock для production claims/expiry, bounded100 SKIP LOCKED sweep every minute,
SQL terminal diagnostics, provider reacquire проверяет также deadline.
Это at-least-once recovery, не exactly-once provider billing/application.
Implementation done / verification pass в указанном scope.

- [x] T-R1: explicit selectors; integration имеет приоритет над unit при двойной
  маркировке, unmarked → regression. External отмечены для Docker/Compose,
  GenerationAI stores, migrations/auth PostgreSQL, Streams Redis, chat Mongo,
  session-lock Redis и real WS Redis. Existing env/URL guards сохранены.
- [x] T-R2: no-cov только для3focused stages, suite использует исходный coverage74.
  Интерактивный runner по-прежнему спрашивает integration; --ci исполняет все4.
  Suite сознательно повторяет3stages. Общий coverage не измерялся.
- [x] T-R3: installed BaseCheckRunner command + synthetic real pytest collection:
  unit/integration/двойной marker/unmarked/external cases. Matrix4554collected:
  unit1682, integration41, regression2661, suite4384, external170. Disjoint union
  и отсутствие external в suite проверены assertions. Artifact a0611-matrix.json.
- [x] T-R4: 276passed/170deselected (19.45s), scoped hooks включая pip-audit Passed.
  Проверял ведущий; reviewer not-requested; checked-awaiting-acceptance.

Evidence в var/audit/: a0611-red.txt (исходный пустой selector), a0611-tests.txt
(70passed), a0611-final-tests.txt (276passed), a0611-hooks.txt; matrix-default.txt,
матрица json и воспроизводящий диагностический a0611_matrix.py. Временный helper
сначала неверно извлекал Python -m вместо pytest -m; исправлен до green-проверок.

Ограничение: обычный full collection падает из-за двух test_combat_actor_input.py
(character/runtime и monsters/instances/runtime), artifact a0611-collection.txt.
Diagnostic importlib дал другой старый bare import test_squad_selection_service
в monster difficulty test (a0611-matrix.txt). Поэтому final matrix использует
обычный import mode и --ignore только monsters/instances/runtime/test_combat_actor_input.py.
Это исключение НЕ внесено в config/runner/CI; полный gate остаётся незелёным.
Никаких тестов/Legacy файлов не удалено, gameplay не менялся. Полную переаттестацию
existing unit labels и collection repair оставить отдельной задачей.

Scope: pyproject test settings; external labels (15testmodules); новый runner/pytest
selection test; docs/testing_strategy и audit plan/registry. Предыдущие certifi/Pillow
и все накопленные uncommitted changes сохранены. Commit/push/deploy не выполнялись.
После отчёта остановка.


### LR: реализация и обычная проверка

- [x] LR-1 implementation done / verification pass: fixed10min RUNNING_LEASE,
  PostgreSQL clock_timestamp для default claim/reacquire/recovery. Expired live
  running rows выбираются bounded100 SKIP LOCKED; pending сохраняет attempts и
  повышает revision, очищает claimed_at/not_before. Exhausted становится failed.
  Cron реального worker startup/every minute; A05-08 доставляет committed intent.
- [x] LR-2 implementation done / verification pass: token fence проверяет deadline
  до/после row lock, а также прежние status/revision/attempts/claimed_at/identity.
  Exact expiry boundary, simulated lock wait across deadline, busy row/concurrent
  sweeps, backlog limit и old owner vs recovered new result проверены. Новый result
  и attempts2 не перезаписываются старым ответом. Действующие неистёкшие claims сохранены.
- [x] LR-3 implementation done / verification pass: fresh raw Mongo input/result,
  не tolerant hydration. Nonempty/malformed output → StoredResultNeedsReview, budget
  exhausted → LeaseAttemptsExhausted, missing/invalid input → InvalidDurableInput,
  old missing timestamp → MissingClaimTimestamp. Mongo не изменяется; outage/SQL
  rollback сохраняют running/revision/attempts. API history предпочитает SQL short
  diagnostic при старом другом Mongo error type. Не восстанавливает task из кеша.
- [x] LR-4 implementation done / verification pass: functional/storage, typing/lint/
  secret checks подтверждены. Первоначальный dependency gate был partial из-за Pillow;
  последующее отдельное обновление13.0.0 ниже подтвердило pip-audit Passed.
  Никаких skip/новых advisory exceptions; исходный failure report сохранён.

Проверял ведущий, reviewer not-requested. 17 новых tests, включая actual SQL/Mongo,
ARQ Redis delivery/worker wiring и lease-vs-job_timeout unit invariant.
RED missing recovery method: var/audit/running-recovery-red.txt. First lease + prior
boundary20passed: var/audit/running-recovery-green.txt. Contract run13passed/1failed
выявил tolerant hydration bug (malformed [] превращался в {}), исправлен raw read:
var/audit/running-recovery-contract.txt. Первый широкий процесс уже загрузил прежний
код и завершился447passed/1samefailure: var/audit/running-recovery-final-tests.txt.
Окончательный свежий прогон448passed,2 existing upstream deprecation warnings,
87.42s,exit0: var/audit/running-recovery-final-v2-tests.txt.
Command: GenerationAI + items + coreAI + privileged access + archive contract;
RUN_GENERATION_INPUT_STORE_TESTS=1 RUN_GENERATION_RETRY_POSTGRES_TESTS=1,
--no-cov -o addopts='', disposable local stores/finally cleanup. Archive hashes pass.
Mypy5sourcefiles pass: var/audit/running-recovery-mypy.txt. Ruff/format/Bandit/
detect-secrets/прочие применимые hooks pass, кроме pip-audit:8 advisories Pillow12.3.0,
scanner fix13.0.0, hookexit1. Полный отчёт var/audit/running-recovery-hooks.txt.
CVE-2026-112895/112400/112397/112896/112897/112395/112404/112899.
Это наблюдение scanner, отдельное dependency обновление не выполнялось. Application
package thesealedworld не проверяется PyPI scanner (not on PyPI); прежние7 exceptions
не менялись. Full project gate/Linux CI/realAI/production не запускались.

Ограничения: fixed lease без heartbeat, срок больше worker timeout; recovery задержка
зависит от availability/backlog. Provider мог выполнить внешний запрос до crash,
поэтому exactly-once/billing не гарантируется; израсходованная attempt не возвращается.
Existing stored result не replay автоматически, остаётся для ручного разбора. Никакого
Mongo delete/overwrite, новых SQL migrations либо gameplay balance/facade правок.
HEAD183246e5/index empty. Functional checked-awaiting-acceptance, общий quality partial
до отдельного Pillow security update. Без commit/push/deploy; после отчёта остановка.


## Отдельный шаг — Pillow security update — 20.10.2026

Запрос: Pillow до безопасной версии, совместимость и pip-audit; без ревизора,
commit/push/deploy, после отчёта остановиться. Reviewer not-requested.
P-R1: targeted Pillow12.3.0 →13.0.0 (fixversion предыдущего scanner); pyproject floor,
uv.lock и local .venv согласовать, другие package versions не менять.
P-R2: lock check/pip check, actual image processing/asset tests, existing pip-audit
без skip/new exceptions. Пакетное major обновление проверить на live PIL consumers.
P-R3: сохранить accumulated source/archive, не менять gameplay/assets/production.
План: before lock/env snapshots, targeted uv lock/install no-deps, delta checks,
focused tests/formats smoke/audit, документация результата. Implementation pending;
verification pending. Проверяет ведущий.


### P: реализация и обычная проверка

- [x] P-R1 implementation done / verification pass: backend-runtime floor Pillow>=13.0.0,
  uv.lock13.0.0 и .venv13.0.0. Before/after version maps подтверждают: единственный
  version delta — Pillow12.3.0 →13.0.0. uv lock --check и pip check exit0.
- [x] P-R2 implementation done / verification pass:28passed,1 existing Starlette
  deprecation warning,14.67s,exit0; var/audit/pillow13-tests.txt. Actual tileset template,
  asset storage/backfill, frontend serving и archive contract. Direct live src PIL
  consumers не найдены; remaining tools используют Pillow. Smoke PNG/JPEG/WebP
  encode/decode/resize/draw/exif transpose и actual slicer64 RGBA512×512 tiles/alpha
  mask0..255 прошли на synthetic4096×4096 PNG в TemporaryDirectory under var.
  slicer ROOT направлен во временный каталог; runtime write disabled; всё удалено
  контекстом TemporaryDirectory. Artifact var/audit/pillow13-image-smoke.txt.
  Существующий pre-commit pip-audit --all-files Passed,exit0, без новых exceptions:
  var/audit/pillow13-pip-audit.txt. Прежние7 advisory exceptions сохранены.
- [x] P-R3 implementation done / verification pass: production code/tools/assets и
  archive originals не менялись этим шагом; hash contract passed. Task changes:
  pyproject.toml,uv.lock и audit progress/registry. Без realAI/store/production операций.

Проверил ведущий, reviewer not-requested. Local Windows/Python3.14; Linux/Python3.13
CI и полный project gate не запускались. Dependency resolution177packages подтверждает
совместимость declared requirements; это не проверка всех редко используемых map tools.
Новых пакетов/других обновлений не добавлено. Raw snapshots var/audit/pillow-lock-before.toml
и pillow-env-before.json сохранены для delta checks. Historical running-recovery
pip-audit failure снят этим шагом; functional448 tests того шага не повторялись,
проверка обновления scoped28tests+image smoke. Статус checked-awaiting-acceptance.
Без коммита/push/deploy; после отчёта остановка.


## Шаг 9.1 — A06-07: frontend/backend config HTTP contract — 20.10.2026

Запрос: совместный HTTP-тест frontend-клиента и backend-роутера настроек;
исправить, проверить, после отчёта остановиться. Без ревизора/commit/push/deploy.
Reviewer not-requested. Проверяет ведущий.
H-R1: настоящий GameConfigApi → BaseApiClient → httpx ASGITransport → настоящий
backend config router/auth/serialization/manager; не независимые MockTransport payloads.
H-R2: DTO metadata/current/default, read/set/reset-key/reset-namespace и изоляция
namespace; 403 read/write/ordinary/no credentials, 404 missing, 422 invalid value;
ошибки не скрываются и не меняют storage. Реальные settings/balance не менять.
H-R3: negative producer/consumer drift доказуем: несовместимый required field,
route/auth/body mismatch обнаруживаются contract checks. Только synthetic config
и in-memory storage double; это HTTP boundary proof, не реальный Redis adapter proof.
H-R4: focused + related auth/config/client regression tests, hooks/docs; сохранить
accumulated work, без production/real stores/credentials и без gameplay/facade правок.
План: один совместный ASGI fixture, lifecycle/auth/validation/drift contract tests;
если runtime совместим — production код не менять; записать scope/evidence.
Implementation done / verification pass в указанном scope.

- [x] T-R1: explicit selectors; integration имеет приоритет над unit при двойной
  маркировке, unmarked → regression. External отмечены для Docker/Compose,
  GenerationAI stores, migrations/auth PostgreSQL, Streams Redis, chat Mongo,
  session-lock Redis и real WS Redis. Existing env/URL guards сохранены.
- [x] T-R2: no-cov только для3focused stages, suite использует исходный coverage74.
  Интерактивный runner по-прежнему спрашивает integration; --ci исполняет все4.
  Suite сознательно повторяет3stages. Общий coverage не измерялся.
- [x] T-R3: installed BaseCheckRunner command + synthetic real pytest collection:
  unit/integration/двойной marker/unmarked/external cases. Matrix4554collected:
  unit1682, integration41, regression2661, suite4384, external170. Disjoint union
  и отсутствие external в suite проверены assertions. Artifact a0611-matrix.json.
- [x] T-R4: 276passed/170deselected (19.45s), scoped hooks включая pip-audit Passed.
  Проверял ведущий; reviewer not-requested; checked-awaiting-acceptance.

Evidence в var/audit/: a0611-red.txt (исходный пустой selector), a0611-tests.txt
(70passed), a0611-final-tests.txt (276passed), a0611-hooks.txt; matrix-default.txt,
матрица json и воспроизводящий диагностический a0611_matrix.py. Временный helper
сначала неверно извлекал Python -m вместо pytest -m; исправлен до green-проверок.

Ограничение: обычный full collection падает из-за двух test_combat_actor_input.py
(character/runtime и monsters/instances/runtime), artifact a0611-collection.txt.
Diagnostic importlib дал другой старый bare import test_squad_selection_service
в monster difficulty test (a0611-matrix.txt). Поэтому final matrix использует
обычный import mode и --ignore только monsters/instances/runtime/test_combat_actor_input.py.
Это исключение НЕ внесено в config/runner/CI; полный gate остаётся незелёным.
Никаких тестов/Legacy файлов не удалено, gameplay не менялся. Полную переаттестацию
existing unit labels и collection repair оставить отдельной задачей.

Scope: pyproject test settings; external labels (15testmodules); новый runner/pytest
selection test; docs/testing_strategy и audit plan/registry. Предыдущие certifi/Pillow
и все накопленные uncommitted changes сохранены. Commit/push/deploy не выполнялись.
После отчёта остановка.


### H: реализация и обычная проверка

- [x] H-R1 implementation done / verification pass:41 cases в новом joint testfile,
  actual frontend GameConfigApi/OperatorApiClient/BaseApiClient → httpx ASGITransport
  → actual backend config router, operator auth, Pydantic body, JSON serializer и
  GameConfigManager. Не подменяются HTTP responses/_request/auth/manager. Только
  storage MemoryRedis; synthetic contract_http/contract_other configs и fake keys.
- [x] H-R2 implementation done / verification pass: metadata/Unicode/types/defaults,
  int/float/bool/str write+readback, key reset preserves other override, namespace reset
  preserves other namespace. Missing/service/wrong credentials и read capability на
  mutations получают403 before storage; write-only key читает через real auth.
  Read-only source с write credential отказывает before HTTP. Unknown namespace/key
  →404, invalid/malformed/out-of-range value →422, no storage mutations on errors.
- [x] H-R3 implementation done / verification pass:4 required fields producer rename
  обнаруживаются frontend DTO. Отдельный process-only mutation probe меняет current
  →renamed_current и запускает обычный positive metadata test: ожидаемый pytestexit1
  KeyError current. Probe wrapperexit0 подтверждает detection, production files не
  менялись: var/audit/a0607-mutation-probe.txt. Совместимость runtime не нарушена;
  исправлен coverage gap, runtime/balance не редактировались.
- [x] H-R4 implementation done / verification pass:207passed,1 existing Starlette
  deprecation warning,17.51s,exit0: var/audit/a0607-final-tests.txt. Новый41 + backend_api,
  backend game_config manager, privileged access/internal routers и cabinet settings.
  Command uses --no-cov -o addopts='' and local unique basetemp, без Docker/real stores.
  Hooks newPythonfile Passed, включая Ruff/format/Bandit/pip-audit/detect-secrets:
  var/audit/a0607-hooks.txt. Документы markdownlint; diff whitespace проверены.

Первый тестовый запуск38 setup errors из-за импорта экспортированного APIRouter
вместо module; fixture исправлен через import_module, production дефектом не являлся.
Artifact var/audit/a0607-first-tests.txt. Затем38green var/audit/a0607-green-tests.txt,
добавлены unknown-key/read-only-source cases, финальный41 включён в207green выше.
CI .github/workflows/ci.yml existing behavioral selector tests/frontend включает
новый файл; workflow не менялся, remote CI не запускался. Полный project gate/mypy
не запускались: production code/type contracts не изменялись. Real Redis semantics
и остальные frontend/backend APIs этим не подтверждены. Проверял ведущий,
reviewer not-requested; статус checked-awaiting-acceptance.
Task changes: новый testfile, testing_strategy.md и две audit/progress записи.
HEAD183246e5/index empty. Без коммита/push/deploy. После отчёта остановка.


## Шаг 9.2 — A06-08: architectural gate — 20.10.2026

Запрос: усиление архитектурных проверок, исправить/проверить/остановиться;
без ревизора/commit/push/deploy. Reviewer not-requested.
B-R1: AST gate для запрещённых frontend→backend и shared→service imports,
backend features→Redis key construction по game:/combat:/loot: roots, без Rift skip.
B-R2: synthetic violations (new subprefix/Rift/import variants) и allowed infrastructure/
semantic integration/contracts доказывают различение, comments/docstrings не violations.
Business idempotency token CombatDurabilityDamageRequest.idempotency_key — не Redis
key; учитывать semantic context вместо blanket file exceptions.
B-R3: actual src scan и behavioral CI wiring; не устранять gate failure через broad
allowlist/игровой refactor, не менять баланс/monster facade/Legacy support policy.
B-R4: focused/regression tests, quality/docs, сохранять accumulated work; stop afterwards.
План: RED synthetic cases, bounded AST visitor + existing gate replacement, source
scan, explicit CI selector и regression guard, quality/docs. Полнота всех architecture
invariants не заявляется (ORM/domain semantics/dynamic code требуют отдельных checks).
Implementation done / verification pass в указанном scope.

- [x] T-R1: explicit selectors; integration имеет приоритет над unit при двойной
  маркировке, unmarked → regression. External отмечены для Docker/Compose,
  GenerationAI stores, migrations/auth PostgreSQL, Streams Redis, chat Mongo,
  session-lock Redis и real WS Redis. Existing env/URL guards сохранены.
- [x] T-R2: no-cov только для3focused stages, suite использует исходный coverage74.
  Интерактивный runner по-прежнему спрашивает integration; --ci исполняет все4.
  Suite сознательно повторяет3stages. Общий coverage не измерялся.
- [x] T-R3: installed BaseCheckRunner command + synthetic real pytest collection:
  unit/integration/двойной marker/unmarked/external cases. Matrix4554collected:
  unit1682, integration41, regression2661, suite4384, external170. Disjoint union
  и отсутствие external в suite проверены assertions. Artifact a0611-matrix.json.
- [x] T-R4: 276passed/170deselected (19.45s), scoped hooks включая pip-audit Passed.
  Проверял ведущий; reviewer not-requested; checked-awaiting-acceptance.

Evidence в var/audit/: a0611-red.txt (исходный пустой selector), a0611-tests.txt
(70passed), a0611-final-tests.txt (276passed), a0611-hooks.txt; matrix-default.txt,
матрица json и воспроизводящий диагностический a0611_matrix.py. Временный helper
сначала неверно извлекал Python -m вместо pytest -m; исправлен до green-проверок.

Ограничение: обычный full collection падает из-за двух test_combat_actor_input.py
(character/runtime и monsters/instances/runtime), artifact a0611-collection.txt.
Diagnostic importlib дал другой старый bare import test_squad_selection_service
в monster difficulty test (a0611-matrix.txt). Поэтому final matrix использует
обычный import mode и --ignore только monsters/instances/runtime/test_combat_actor_input.py.
Это исключение НЕ внесено в config/runner/CI; полный gate остаётся незелёным.
Никаких тестов/Legacy файлов не удалено, gameplay не менялся. Полную переаттестацию
existing unit labels и collection repair оставить отдельной задачей.

Scope: pyproject test settings; external labels (15testmodules); новый runner/pytest
selection test; docs/testing_strategy и audit plan/registry. Предыдущие certifi/Pillow
и все накопленные uncommitted changes сохранены. Commit/push/deploy не выполнялись.
После отчёта остановка.


### B: реализация и обычная проверка

- [x] B-R1 implementation done / verification pass: pure AST validator в
  tools/validators/architecture.py, без импорта application modules при source scan.
  Frontend backend imports, shared service imports, features redis imports и executable
  game:/combat:/loot: prefixes распознаются, включая новые subspaces и Rift без skip.
  Static/relative/aliased/literal dynamic imports; constants/fstrings/concat; syntax
  error fail closed. Отчёт file/line/rule без raw key payload.
- [x] B-R2 implementation done / verification pass:27 synthetic/self/wiring cases,
  allowed infrastructure manager/semantic integration/sharedDTO/docstrings/business
  DTO operationidentity. Исключение только backend feature combat identity в
  CombatDurabilityDamageRequest.idempotency_key; nested Redis call и game key в
  том же field не исключаются. Никаких file/baseline/feature allowlists.
- [x] B-R3 implementation done / verification pass: existing manager-location tests
  сохранены, blanket key test заменён actual src scan. Actual src passes без runtime
  правок. CI develop-behavior теперь явно выбирает test_infrastructure_boundaries.py,
  helper tests уже внутри tests/backend/core. tools/validators/run.py вызывает тот же
  checker до добавления fixture errors. Wiring regression guard проверяет подключения.
- [x] B-R4 implementation done / verification pass: последний focused35passed,
  var/audit/a0608-tightened-tests.txt; итоговый regression219passed/6skipped,24.36s,
  exit0, var/audit/a0608-final-v2-tests.txt. Scope: helper/source gate + prior config
  HTTP contract + tests/deploy. Skips:4 env-permissions,1 network,1 nginx logs — existing
  opt-in Docker checks не включались (для изменения AST/CI selection не требовались).
  Scoped mypy architecture.py pass, var/audit/a0608-mypy.txt. Применимые hooks5files
  Passed, including YAML/Ruff/format/Bandit/pip-audit/detect-secrets:
  var/audit/a0608-hooks.txt. Markdownlint и diff whitespace pass.

RED missing module: var/audit/a0608-red.txt (synthetic fixture syntax поправлен перед
этим запуском, не runtime finding). First23green var/audit/a0608-first-tests.txt;
первый широкий217passed/6skipped var/audit/a0608-final-tests.txt; после tightening
semantic context добавлены2 tests и окончательный219green выше. Проверял ведущий,
reviewer not-requested, checked-awaiting-acceptance. Full project gate/remote CI и
real stores не запускались. Source validator отдельно type-checked; общий старый
monster facade mypy issue не исправлялся.

Не заявляется полный enforcement всех правил проекта: computed imports, произвольные
runtime key factories/flow/Lua/TTL, ORM и domain-state semantics остаются вне checker.
Не запрещались все feature→infrastructure imports: composition/integrations и выбор
Legacy поддержки требуют собственных контрактов. Никаких gameplay/data/monster refactors,
archive originals или новых зависимостей. Task scope: validator/run,2testfiles,CI
selection, testing_strategy и audit/progress. HEAD183246e5/index empty.
Без коммита/push/deploy. После отчёта остановка.


## Шаг 9.3 — A06-11: test stages — 20.10.2026

Запрос: разделение уровней тестирования; исправить/проверить/остановиться,
без ревизора/commit/push/deploy. Reviewer not-requested.
T-R1: unit stage имеет непустой selector; отдельные integration/regression scopes,
explicit external opt-in без смешивания уровней и без автоматического запуска Docker.
Не выдавать unmarked backlog за unit; существующие tests не терять.
T-R2: общий suite/coverage gate с исходным fail_under74 сохраняется. Выборочные
stages без глобального coverage threshold, full suite проверяет его отдельно.
T-R3: actual installed codex_core BaseCheckRunner command construction + collection
matrix доказать, negative markers/overlap/source scope fixtures проверить.
T-R4: related focused tests/quality/docs; real settings/gameplay не менять,
сохранить accumulated work. Полную переаттестацию всех существующих unit labels
и устранение Legacy collection errors не включать в задачу.
План: RED runner selection config, explicit markers/stages; external labels для
известных disposable storage tests, suite isolation; actual collection/report/tests.
Unit/integration/regression partitions непересекаются; suite intentionally aggregate.
External stage запускается явным pytest -m external с existing per-suite env flags,
не добавляется к default runner stages (--ci автоматически запускает все stages).
Implementation done / verification pass в указанном scope.

- [x] T-R1: explicit selectors; integration имеет приоритет над unit при двойной
  маркировке, unmarked → regression. External отмечены для Docker/Compose,
  GenerationAI stores, migrations/auth PostgreSQL, Streams Redis, chat Mongo,
  session-lock Redis и real WS Redis. Existing env/URL guards сохранены.
- [x] T-R2: no-cov только для3focused stages, suite использует исходный coverage74.
  Интерактивный runner по-прежнему спрашивает integration; --ci исполняет все4.
  Suite сознательно повторяет3stages. Общий coverage не измерялся.
- [x] T-R3: installed BaseCheckRunner command + synthetic real pytest collection:
  unit/integration/двойной marker/unmarked/external cases. Matrix4554collected:
  unit1682, integration41, regression2661, suite4384, external170. Disjoint union
  и отсутствие external в suite проверены assertions. Artifact a0611-matrix.json.
- [x] T-R4: 276passed/170deselected (19.45s), scoped hooks включая pip-audit Passed.
  Проверял ведущий; reviewer not-requested; checked-awaiting-acceptance.

Evidence в var/audit/: a0611-red.txt (исходный пустой selector), a0611-tests.txt
(70passed), a0611-final-tests.txt (276passed), a0611-hooks.txt; matrix-default.txt,
матрица json и воспроизводящий диагностический a0611_matrix.py. Временный helper
сначала неверно извлекал Python -m вместо pytest -m; исправлен до green-проверок.

Ограничение: обычный full collection падает из-за двух test_combat_actor_input.py
(character/runtime и monsters/instances/runtime), artifact a0611-collection.txt.
Diagnostic importlib дал другой старый bare import test_squad_selection_service
в monster difficulty test (a0611-matrix.txt). Поэтому final matrix использует
обычный import mode и --ignore только monsters/instances/runtime/test_combat_actor_input.py.
Это исключение НЕ внесено в config/runner/CI; полный gate остаётся незелёным.
Никаких тестов/Legacy файлов не удалено, gameplay не менялся. Полную переаттестацию
existing unit labels и collection repair оставить отдельной задачей.

Scope: pyproject test settings; external labels (15testmodules); новый runner/pytest
selection test; docs/testing_strategy и audit plan/registry. Предыдущие certifi/Pillow
и все накопленные uncommitted changes сохранены. Commit/push/deploy не выполнялись.
После отчёта остановка.


## Шаг 9.4 — конфликт имён test_combat_actor_input — 20.10.2026

Запрос: исправить конфликт двух test_combat_actor_input.py и проверить сбор всех
тестов. Без игровой логики, ревизора, commit/push/deploy; после отчёта остановка.
Reviewer not-requested. Небольшое переименование выполняет ведущий локально.
C-R1: устранить import mismatch без изменения содержимого тестов и src.
C-R2: full collection без ignore/importlib обходов, focused execution обоих файлов.
План: переименовать monster test в test_monster_combat_actor_input.py, проверить
байтовую идентичность, выполнить collection и focused tests; записать результат.
Implementation pending / verification pending.


Результат: implementation done / verification pass; checked-awaiting-acceptance.
- [x] C-R1: только переименование monster test; байтовая идентичность до/после
  подтверждена. Source/gameplay и содержимое обоих тестов не менялись.
- [x] C-R2: `.venv/Scripts/python -m pytest --collect-only -q --no-cov -o addopts=''`
  без ignore и изменения import mode: **4558 tests collected**, exit0,21.65s.
  Это включает4ранее исключённых monster cases; прежний collection blocker снят.
  Оба модуля вместе: **15passed**,1.41s. Ruff check и format --check Passed.
Evidence: var/audit/test-module-names-collection.txt и test-module-names-tests.txt.
Проверял ведущий; independent reviewer not-requested. Полное исполнение4558tests
и global coverage не запускались; full project gate не заявляется.
Commit/push/deploy не выполнялись. После отчёта остановка.

## Шаг 9.5 — A06-03: реальные storage/broker contracts — 20.10.2026

Запрос: одна инфраструктурная задача, без ревизора, commit/push/deploy и изменений
игровой логики; исправить, проверить, после отчёта остановиться.
Reviewer not-requested; исполнитель проверяет adapter contract без source changes.
S-R1: добавить отсутствующее подтверждение RedisJSON wire roundtrip, server TTL
и частичного pipeline отказа через настоящий ActorCommitmentManager.
S-R2: opt-in external integration suite, disposable Redis Stack, unique container,
random loopback port, no volumes/application URLs/secrets; unconditional cleanup.
S-R3: сопоставить с уже существующими SQL/Mongo/Streams suites и не заявлять
полное закрытие A06-03, если snapshot/index/ownership/fencing остаются непроверены.
План: добавить isolated RedisJSON fixture и три representational adapter tests;
выполнить новый suite и существующий Streams suite, проверить collection/quality.
Implementation pending / verification pending. Исходные накопленные правки сохраняются.
Дополнение согласованного scope: ведущий отдельно добавляет
`tests/backend/infrastructure/mongo/test_task_document_index_contract.py`, используя
существующие disposable input_databases/stores fixtures. Проверка Mongo unique
(document_kind, task_id), rejection duplicate, idempotent index bootstrap и BSON
roundtrip; только infrastructure tests, без src/gameplay изменений.

Результат RedisJSON: implementation done / focused verification pass.
- [x] S-R1: настоящий ActorCommitmentManager + RedisService + Redis Stack JSON.GET/SET:
  Unicode/nested/null roundtrip, section/batch missing result, actual TTL expiry/recreate;
  WRONGTYPE в середине pipeline не теряет соседние документы и не сообщает broken
  запись как saved; read pipeline возвращает None только для failing key.
- [x] S-R2: RUN_REDISJSON_CONTRACT_TESTS=1, unique ephemeral Docker container,
  random127.0.0.1port, persistence disabled, no volumes; finally force cleanup.
- [x] Новый suite: **3passed**,4.53s. Evidence: var/audit/a0603-redisjson.txt.
  Full storage/broker matrix и остальные результаты дописывает ведущий.


Интегральный результат A06-03: implementation done / verification pass в границах
representative infrastructure suite; checked-awaiting-acceptance, reviewer not-requested.
- [x] Mongo дополнение: repeated index bootstrap, repo BSON roundtrip, server
  DuplicateKeyError, два конкурентных insert дают ровно одного победителя.
- [x] S-R3: карта real proofs записана в testing_strategy. Историческое отсутствие
  real contracts устранено. Все Legacy/gameplay SQL ownership predicates,
  все Mongo snapshot families и business replay-idempotency не сертифицированы.
  Это доменные ограничения, не повод выдавать весь storage слой за проверенный.
- [x] Новые2Mongo+3RedisJSON:5passed,14.83s (a0603-new-contracts.txt).
- [x] Existing pending quarantine + input durability + retry PostgreSQL:
  86passed,33.07s (a0603-existing-storage.txt).
- [x] Existing running recovery + document reconciliation + provider transaction
  boundary + schedule recovery:56passed/7deselected,58.03s (a0603-recovery-storage.txt).
  Итого147passed без повторного учёта первого3RedisJSON smoke.
- [x] Full collection без ignore/importlib overrides:4563collected,exit0,26.76s
  (a0603-collection.txt). Default `not external` исключает все5новых тестов;
  focused empty selection exit5 ожидаем, не выдаётся за successful test execution.
- [x] Ruff и scoped pre-commit hooks включая pip-audit Passed (a0603-hooks.txt).
  Temporary Docker containers очищены (проверено docker ps -a name filters).

Исполнитель RedisJSON — внутренний помощник; ведущий проверил файл и повторно
выполнил3теста вместе с Mongo. Это обычная проверка, не independent review.
Mongo tests/общие проверки/итоговая фиксация — ведущий. Source/gameplay/баланс,
real application settings и архивы не менялись. Scope:2new testfiles,
testing_strategy,registry,progress. HEAD183246e5/index empty.
Полное исполнение4563tests, global coverage и full project check не запускались.
Без коммита/push/deploy. После отчёта остановка.


## Шаг 9.6 — AG-05: адресная типизация AI adapter — 20.10.2026

Запрос: одна задача AG-05, без reviewer/commit/push/deploy, без игровой логики;
исправить, проверить и остановиться. Reviewer not-requested.
Y-R1: снять ignore_errors только с инфраструктурной AI boundary: core.ai и
GenerationAI CodexAIExecutor. Исправлять типы без Any/cast/ignore заглушек.
Y-R2: сохранить runtime behavior, не менять игровые consumers/monster facade.
Y-R3: positive mypy и negative typed mutation должны показать, что ошибки этих
модулей больше не подавляются; выполнить связанные tests и quality.
План: baseline, diagnostic config без2исключений, минимальные typing fixes если
нужны, убрать2entries из pyproject, mypy/tests/hooks. Остальной AG-05 backlog
остаётся отдельными заходами; не объявлять массовый ignore блок закрытым.
Implementation pending / verification pending.


Результат AG-05, первый адресный заход: implementation done / verification pass;
checked-awaiting-acceptance. Массовое снятие остальных подавлений не выполнено.
- [x] Y-R1: из ignore_errors удалены core.ai и generation_ai.integrations.codex_ai_executor
  (35→33module entries). Диагностика без подавлений выявила2ошибки core.ai:
  lazy root export codex_ai.GeminiProvider имеет static type object, не callable/type.
  Импорт заменён на codex_ai.providers.gemini.GeminiProvider; executor source не менялся.
  Никаких новых Any/cast/type-ignore/TYPE_CHECKING обходов или подавлений не добавлено.
- [x] Y-R2: старый lazy import и новый direct import дают один и тот же class object
  (identity assertion). Вызовы/provider settings/JSON behavior не менялись.
  37existing tests Passed,5.35s; no provider requests. Игровые/monster consumers не менялись.
- [x] Y-R3: focused mypy2sourcefiles Passed. Shadow-file mutation (return str вместо
  int в двух temporary copies) даёт2return-value errors, exit1 — оба модуля проверяются.
  Mutation отсутствует в source. Scoped hooks включая pip-audit Passed.

Evidence var/audit/ag05-{baseline,probe,focused,negative,tests,final-wide,hooks}.txt.
Широкий mypy src/tools: до и после330errors/61files,2244checked source files;
sorted error diagnostics идентичны (не только количество). Это текущий baseline,
не прежний исторический single monster-facade finding. Общий mypy/full gate не green.
Два stale override для archived world/monster prompts дают unused section notes;
они и игровые подавления оставлены следующими отдельными задачами.
Проверял ведущий локально: небольшая правка без делегирования/reviewer.
Scope: ai.py import,2entries pyproject,progress и историческийaudit11 status.
Без commit/push/deploy. После отчёта остановка.


## Шаг 9.7 — AG-05: site UserRepository — 20.10.2026

Запрос: один инфраструктурный участок, без игровой логики, reviewer/commit/push/
deploy; исправить, проверить, после отчёта остановиться. Reviewer not-requested.
U-R1: снять ignore_errors с frontend.features.auth.repositories.user_repository;
исправить выявленные типы без новых Any/cast/ignore подавлений.
U-R2: сохранить SQL predicates, auth/account поведение, без игровых данных/логики.
U-R3: focused mypy, negative shadow probe и related tests; сравнить broad baseline.
План: diagnostic config, минимальная правка repository typing/collection contract,
снять1override; tests/hooks/report. Небольшой участок выполняет ведущий локально.
Implementation pending / verification pending.


Результат второго адресного захода AG-05: implementation done / verification pass,
checked-awaiting-acceptance; reviewer not-requested.
- [x] U-R1: снят1ignore_errors entry UserRepository (33→32). Без подавления были
 2return-value errors: SQLAlchemy Sequence[User] против обещанного list[User].
 get_pending_testers/get_approved_testers теперь возвращают list(...), как соседние
 list_page/list_referrals. Никаких новых Any/cast/ignore или ослабления annotation.
- [x] U-R2: SQL select/where/order/commit неизменны. Auth/account/cabinet regression:
 105passed/5external deselected,10.79s. Игровые данные, исходники и правила не менялись.
- [x] U-R3: focused mypy1file Passed. Negative --shadow-file добавляет несовместимый
 return str вместо int только в временную копию: return-value error/exit1 подтверждён.
 Широкий mypy src/tools:330errors/61files/2244sources, sorted diagnostic set полностью
 идентичен предыдущему baseline. Общий mypy и full project gate не green.
 Evidence var/audit/ag05-users-{probe,focused,negative,tests,wide,hooks}.txt.
 Scoped hooks включая pip-audit Passed; Markdown/diff checks проверены отдельно.

Проверял ведущий локально. Source scope: только UserRepository2return lines;
configuration:1override entry; audit11/progress statuses. Остальные32подавления
AG-05 остаются следующими адресными задачами. Нет commit/push/deploy.
После отчёта остановка.


## Шаг 9.8 — AG-05: infrastructure analytics repository — 21.10.2026

Запрос: один инфраструктурный участок без игровой логики/reviewer/commit/push/
deploy; проверить и остановиться. Reviewer not-requested.
A-R1: снять ignore_errors с infrastructure.combat.repositories.analytics_repository;
устранить Select→Subquery assignment conflict отдельными variable names без Any/cast.
A-R2: сохранить исходный SQL/поведение. Отдельное подозрительное max_turn при label
turns в query_avg_rounds не исправлять под видом typing; зарегистрировать follow-up.
A-R3: focused mypy, negative shadow probe, regression tests и broad baseline comparison.
План:1override removal, local variable rename, AST equivalence+tests/hooks/report.
Малая правка выполняется ведущим локально. Implementation pending/verification pending.


Результат третьего адресного захода: implementation done / verification pass,
checked-awaiting-acceptance. Проверял ведущий, reviewer not-requested.
- [x] A-R1: удалён1override (32→31); query_avg_rounds использует source_query для
 Select и subq для Subquery. Нет новых Any/cast/ignore/typing обходов.
- [x] A-R2: AST до/после идентичен после обратного rename source_query→subq.
 SQL, filters, labels и возврат данных не менялись. Игровая логика не затронута.
- [x] A-R3: focused mypy1file pass; shadow mutation return str вместо int detected,
 exit1. Related analytics ingestion/dashboard tests7passed,9.54s. Broad mypy
 330errors/61files/2244sources; sorted error diagnostic set идентичен прошлому.
 Общий mypy/full project gate не green. Scoped hooks включая pip-audit Passed.
Evidence: var/audit/ag05-analytics-{probe,focused,negative,tests,wide,hooks}.txt;
исходная копия before.py хранится только в ignored var/audit.

Отдельный follow-up (не исправлен): query_avg_rounds строит select с turns label,
затем обращается к subq.c.max_turn. Related7tests не доказывают исполнение этого
конкретного SQL-метода. Также связывание таблиц и смысл средней требуют отдельной
диагностики; никаких выводов о корректности аналитических данных не делалось.
Scope: infrastructure analytics_repository local variable rename,1pyproject entry,
audit11/progress. Остальные31ignore entries сохраняются. Нет commit/push/deploy.
После отчёта остановка.


## Шаг 9.9 — AG-05: feedback HTTP validation boundary — 21.10.2026

Запрос: один инфраструктурный участок, без gameplay/reviewer/commit/push/deploy;
проверить, после отчёта остановиться. Reviewer not-requested.
F-R1: снять feedback.routes.pages ignore_errors, устранить UploadFile|str|None
аргумент priority через явную DTO validation boundary, без Any/cast/ignore.
F-R2: сохранить успешный submit и прежний invalid form response, без gameplay.
F-R3: focused mypy+negative shadow, form validation regression и broad baseline.
План: FeedbackCreate.model_validate(raw mapping),1override removal,tests/hooks.
Небольшую правку ведущий делает локально. Implementation pending/verification pending.


Результат четвёртого адресного захода: implementation done / verification pass,
checked-awaiting-acceptance; reviewer not-requested, проверял ведущий.
- [x] F-R1: feedback.routes.pages снят с ignore_errors (31→30). Сырые form values
 проходят FeedbackCreate.model_validate(mapping); существующий priority nullable
 string/pattern contract сохранён, UploadFile отклоняется Pydantic до persistence.
 Новых Any/cast/ignore и ослабления DTO не добавлено.
- [x] F-R2:24tests Passed,6.01s, включая2new HTTP negative cases: invalid priority
 string и multipart file. Возвращают200/error form, repository не создаётся.
 Existing successful submit/redirect проходит. Игровые правила/данные не менялись.
- [x] F-R3: focused mypy1file Passed; negative shadow return str вместо int detected.
 Wide mypy330errors/61files/2244sources; sorted diagnostics идентичны предыдущим.
 Full project mypy/gate не green. Scoped hooks включая pip-audit Passed.
 Evidence var/audit/ag05-feedback-{probe,focused,negative,tests,wide,hooks}.txt.
Scope: feedback pages DTO construction,1pyproject entry,2regression cases,
audit11/progress. Остальные30ignore entries сохраняются. Commit/push/deploy не было.
После отчёта остановка.


## Шаг 9.10 — AG-05: nullable navigation data contract — 21.10.2026

Запрос: один инфраструктурный участок без gameplay/reviewer/commit/push/deploy;
проверить, остановиться. Reviewer not-requested. Scope: presentation data typing
nav.py, только return annotation, без маршрутов/кнопок/решений доменов.
N-R1: убрать nav override, указать существующее None для пустых slots в return type.
N-R2: runtime AST/поведение сохранить; не добавлять Any/cast/ignore; текущий Any
в payload не расширять. N-R3: mypy/negative shadow/tests/hooks/baseline comparison.
План: nullable annotation,1override removal,related session tests,report.
Малую правку ведущий выполняет локально. Implementation pending/verification pending.
Diagnostic world_static_audit не выбран: найденные2ошибки затрагивают старые domain
integration calls; их устранение вне этого захода, source tool не менялся.

Уточнение до зависимой правки: broad mypy выявил consumer ScenarioPageVM.nav с
тем же неверным non-nullable type. Scope включает его annotation и regression
на принятие существующего scenario empty nav. Pydantic validation теперь допускает
существующий payload, это исправление presentation schema, не gameplay.


Результат пятого адресного захода: implementation done / verification pass,
checked-awaiting-acceptance. Ведущий проверил, reviewer not-requested.
- [x] N-R1: nav override снят (30→29), existing None slots отражены в return type.
- [x] N-R2: body AST nav.py идентичен после удаления annotations; buttons/branches
 не менялись. Consumer ScenarioPageVM.nav annotation согласована с nullable slots.
 Это меняет Pydantic schema: существующий scenario empty nav больше не отклоняется.
 Не заявляется полная runtime identity Pydantic-модели; gameplay не менялся.
 Нет новых Any/cast/ignore; старый payload Any не расширялся.
- [x] N-R3: focused mypy nav Passed; shadow return str вместо int detected.
 Broad first revealed1consumer mismatch, исправлен annotation ScenarioPageVM;
 final330errors/61files/2244sources, sorted diagnostics идентичны previous baseline.
 71session tests Passed,5.31s, включая новый consumer field validation regression.
 Проверка использует TypeAdapter реального поля, не полный scenario route proof.
 Scoped hooks включая pip-audit Passed. Full project mypy/gate не green.
Evidence var/audit/ag05-nav-{probe,focused,negative,tests,wide,final-tests,final-wide,hooks}.txt.
Scope:2annotations,1override entry,1regression test,audit11/progress. Остальные29
подавлений остаются. Нет commit/push/deploy. После отчёта остановка.


## Шаг 9.11 — AG-05: item prompt adapter DTO — 21.10.2026

Запрос: один инфраструктурный участок, без gameplay/reviewer/commit/push/deploy;
исправить, проверить, остановиться. Reviewer not-requested.
P-R1: снять item prompts.router override и исправить2list-item errors через
настоящий LLMMessage DTO, без Any/cast/ignore/ослабления annotations.
P-R2: тексты промпта/payload/role/serialization и игровые правила неизменны.
P-R3: focused mypy/negative shadow, before-after model_dump equality,tests/hooks
и broad baseline comparison. Малую правку ведущий выполняет локально.
План: typed message construction,1override removal,adapter regression,report.
Implementation pending/verification pending.


Результат шестого адресного захода: implementation done / verification pass,
checked-awaiting-acceptance; ведущий проверил, reviewer not-requested.
- [x] P-R1: item prompt router override снят (29→28).2dict list-item errors
 устранены явным LLMMessage construction; никаких Any/cast/ignore добавлений.
- [x] P-R2:4complete before/after PromptResult.model_dump(mode=json) comparisons
 Passed (empty/nested source_context/Unicode+null+bool+float/key ordering).
 System/user prompt strings, roles, JSON serialization неизменны. Нет provider
 requests или изменений gameplay/catalog/payload. Source change: DTO import+2constructors.
- [x] P-R3: focused mypy1file Passed; negative shadow return str вместо int detected.
 37existing AI adapter/core/retirement tests Passed,4.53s. Широкий mypy330errors/
 61files/2244sources: sorted diagnostic set идентичен previous baseline.
 Scoped hooks включая pip-audit Passed. Full project mypy/gate не green.
Evidence var/audit/ag05-item-prompt-{probe,focused,negative,equivalence,tests,wide,hooks}.txt.
Малое изменение проверено differential DTO сравнениями и существующими tests;
новые зеркалящие реализацию тесты не добавлялись. Scope:item prompts router,
1pyproject entry,audit11/progress. Остальные28подавлений остаются.
Без commit/push/deploy. После отчёта остановка.

## Шаг 10.1 — A08-15: isolated PostgreSQL restore drill — 21.10.2026

Запрос: AG-05 отложить до слияния в main; следующий шаг инфраструктуры по одной
задаче, без reviewer/commit/push/deploy/gameplay. Reviewer not-requested.
D-R1: opt-in external drill использует только собственный disposable PostgreSQL
container, synthetic site/game базы; без рабочих volumes/env/URL/secrets/network ports.
D-R2: custom pg_dump и pg_restore в новые отдельные базы проверяются по Unicode
данным, ограничениям/индексам и продолжению sequence; базы не смешиваются.
D-R3: повреждённый dump даёт ошибку, cleanup собственного container выполняется
в finally; образ уже локальный postgres:16-alpine, pull запрещён.
D-R4: реальный Docker прогон и scoped lint/collection; результат не означает
настройку operational backup или production restore. Состояние pending/pending.
План: self-contained external test, положительный restore и negative archive,
настоящее выполнение, фиксация доказательств. Проверяет исполнитель.

Результат isolated drill: implementation done / verification pass;
checked-awaiting-acceptance, проверяет исполнитель, reviewer not-requested.
- [x] D-R1: новый tests/deploy/test_postgres_restore_drill.py запускает только
 собственный UUID container: network none, без ports/mounts/env application,
 PGDATA tmpfs, postgres:16-alpine --pull=never; teardown rm --volumes с проверкой.
- [x] D-R2: site.members и game.objects в разных synthetic source/restore DB:
 custom archive, реальные Unicode rows,3 indexes,unique/not-null/check rejection,
 sequence продолжает с3после удалённой2; исходные базы сохраняют1строку.
- [x] D-R3: corrupt archive pg_restore nonzero; target public schema остаётся
 пустой. Нельзя ошибку восстановления засчитать как успешный drill.
- [x] D-R4: RUN_POSTGRES_RESTORE_DRILL=1 .venv/Scripts/python.exe -m pytest
 tests/deploy/test_postgres_restore_drill.py --no-cov -o addopts='' -q:
 1passed10.68s; opt-in unset1skipped0.05s; ruff check/format --check Passed.
 Evidence var/audit/a0815-restore-drill.txt. Container cleanup проверен тестом.
Проверяется PostgreSQL16→16 synthetic schema/data logical restore; не production
migrations, roles/ACL, extensions, cross-store consistency, RPO/RTO или backup
scheduler. A08-15 operational остаётся частично открытым. Без commit/push/deploy.


Уточнение владельца 21.10.2026: оставшуюся типизацию AG-05 (28override entries)
отложить до подготовки слияния в main. Продолжаем шаг10, по одной задаче; не
возвращаться к массовому typing до release preparation без отдельной команды.
Следующая очередь шага10 после10.1:
- 10.2 A08-15: backup/restore contract остальных durable stores и production backup
 schedule/storage/retention/RPO/RTO/alerts evidence — разбить по одному действию,
 operational facts пока неизвестны, не выдавать local synthetic proof за prod.
- 10.3 A08-02: service/network/credential isolation, отдельно от backup и secret
 publication перед release; scope уточнить по текущему compose.
- 10.4 A07-12: Studio access и selected-source read-only enforcement; отдельно.
- Затем шаг11 A08-14: canonical HTTPS email origin/proxy behavior.
Эти пункты не реализованы в10.1 и не запускаются до следующей команды.

Ведущий прочитал весь новый drill и проверил139deploy regressions (2.61s,
11external deselected), scoped hooks/pip-audit Passed. Docs deployment объясняет
opt-in и ограничения. Reviewer not-requested, checked-awaiting-acceptance.
No src/gameplay/settings/working data changes. Scope:1new external test,
deployment docs,audit registry/progress. Commit/push/deploy не выполнялись.

Окончательный повторный запуск ведущим:1restore drill Passed,10.02s, включая
проверку cleanup (var/audit/step10-restore-final.txt).139deploy regression Passed
(var/audit/step10-deploy-regression.txt). Scoped hooks:step10-restore-hooks.txt.
Markdownlint/Ruff/diff whitespace Passed. Это обычная проверка, не независимая
ревизия. Full project gate/coverage не запускались. После отчёта остановка.

## Шаг 10.2 — A08-15: isolated MongoDB restore drill — 21.10.2026

Запрос владельца: проверка восстановления MongoDB в изолированном контейнере;
без ревизора, коммита, push и деплоя, рабочие данные не трогать.
Режим reviewer not-requested; проверяет исполнитель.
M-R1: только UUID disposable mongo:8 --pull=never, network none, без ports,
рабочих volumes/env/URLs; /data/db и /data/configdb tmpfs, unconditional cleanup.
M-R2: synthetic source → archive → новая отдельная target DB; канонический EJSON
проверяет Unicode/nested/null/BSON date/ObjectId/int64; source не меняется.
M-R3: compound unique index сохраняется и отвергает duplicate; TTL metadata
сохраняются; namespace isolation. Corrupt archive обязан вернуть nonzero;
atomic restore, production backup или cross-store consistency не заявляются.
M-R4: реальный opt-in RUN_MONGO_RESTORE_DRILL=1 external test и scoped quality;
без opt-in тест skip. Статус implementation pending / verification pending.
План: добавить self-contained drill рядом с PostgreSQL, выполнить локально,
проверить opt-in/collection/Ruff, записать наблюдения и ограничения, остановиться.

Результат шага 10.2: implementation done / verification pass;
checked-awaiting-acceptance, проверяет исполнитель; reviewer not-requested.
- [x] M-R1: tests/deploy/test_mongo_restore_drill.py создаёт только UUID mongo:8
 container --pull=never --network=none с tmpfs обеих data directories, без ports
 и application configuration. Finally rm --force --volumes и exact-name absence.
- [x] M-R2: gzip mongodump --archive и mongorestore nsFrom/nsTo в новую DB;
 канонический EJSON документов/collection names/indexes равен source snapshot.
 Явно проверены $oid/$date/$numberLong (9007199254740993), Unicode/nested/null.
 Source snapshot до/после неизменен, target до restore отсутствует.
- [x] M-R3: compound unique index реально отвергает duplicate с11000;
 restored TTL expireAfterSeconds=3600; у документов отсутствует expiresAt,
 expiry не ожидается. Corrupt archive nonzero, corrupt target collections=0;
 source/restored snapshot после failed restore не изменены.
- [x] M-R4: финальный RUN_MONGO_RESTORE_DRILL=1 .venv/Scripts/python.exe -m pytest
 tests/deploy/test_mongo_restore_drill.py --no-cov -o addopts='' -q:
 1passed18.27s (var/audit/mongo-restore-drill-final.txt); первый1passed19.30s;
 opt-in unset1skipped0.13s; Ruff check и format --check Passed.
Результат доказывает только MongoDB8→8 synthetic logical restore с data/indexes,
не production backup configuration, users/roles, PITR/oplog, cross-store
consistency, atomic failure rollback или RPO/RTO. Отсутствие collections после
заведомо неверного header не доказывает rollback partially applied archives.
Рабочие данные, src/gameplay/settings не затронуты; commit/push/deploy не было.


Ведущий прочитал финальный MongoDB drill и проверил связанные deploy contracts:
139passed/12external deselected,3.55s (var/audit/step102-deploy-regression.txt).
Docs deployment добавляет opt-in команду и ограничения, registry A08-15 обновлён
как partial operational evidence. AG-05 по-прежнему отложен до подготовки main.
Проверка исполнителя — обычная, не independent review; reviewer not-requested.
Первый hook прогон отметил изменённые файлы во время параллельной записи плана;
pip-audit при этом сообщил no known vulnerabilities. Повтор hooks выполнен после
завершения правок; итоговый artifact step102-mongo-hooks-final.txt.
Scope:1new external test,deployment docs,registry/progress. Рабочие данные/src/
gameplay/config не менялись. Никаких commit/push/deploy. Full project gate/coverage
не запускались; после отчёта остановка.

Окончательный повтор ведущим:1passed14.70s, artifact
var/audit/step102-mongo-final-lead.txt; cleanup absence assertion прошёл.
Итоговые scoped hooks/pip-audit Passed. Markdownlint/diff whitespace проверены.
Статус checked-awaiting-acceptance, independent reviewer not-requested.

## Шаг 10.2b — A08-15: isolated Redis RDB restore drill — 21.10.2026

Запрос владельца: проверить восстановление Redis в изолированном контейнере;
без ревизора, коммита, push и деплоя, рабочие данные не трогать.
Reviewer not-requested; обычную проверку выполняет исполнитель.
R-R1: только UUID disposable Redis Stack containers/volumes --pull=never,
--network=none, без ports, host binds, application env и рабочих данных; cleanup.
R-R2: synthetic SAVE RDB загружается новым Redis process; string/hash/set/list/
zset/RedisJSON и Streams entries/group cursor/pending должны сохраниться.
R-R3: absolute TTL deadline не продлевается, expired key после restore отсутствует;
corrupt RDB завершает новый server nonzero без PONG. Без business replay.
R-R4: реальный opt-in RUN_REDIS_RESTORE_DRILL=1 external test, default skip,
Ruff и запись результатов. AOF/PITR/production backup не заявляются.
План: создать focused drill, проверить новые процессы и реальные данные,
выполнить opt-in/default checks, записать ограничения и остановиться.
Статус implementation pending / verification pending.

Результат Redis шага 10.2b: implementation done / verification pass;
checked-awaiting-acceptance, reviewer not-requested, проверяет исполнитель.
- [x] R-R1: UUID source/restored/corrupt/writer containers и два UUID volumes;
 --pull=never --network=none, без ports/host binds/application env. Finally
 удаляет exact containers/volumes с absence assertions и synthetic dump file.
- [x] R-R2: SAVE artifact скопирован в pytest tmp_path до shutdown; exact RDB
 возвращён в собственный volume, новый isolated Redis Stack process загружает его.
 Проверены Unicode string, hash/set/list/zset, nested/null/boolean JSON,
 Streams entries, XINFO GROUPS cursor/metadata и XPENDING id/owner/delivery count.
 Elapsed pending idle time исключено из сравнения как изменяемое время.
- [x] R-R3: PEXPIRETIME long key совпадает с исходным absolute deadline;
 short key положительный PTTL до и после SAVE, отсутствует после restore;
 corrupt RDB отдельного volume завершает server nonzero, exec PING неуспешен,
 log подтверждает Wrong signature и Fatal error loading DB. Good target сохранён.
- [x] R-R4: RUN_REDIS_RESTORE_DRILL=1 pytest focused final1passed24.13s,
 var/audit/redis-restore-drill-final.txt; prior1passed23.43s.
 Unset opt-in1skipped0.09s var/audit/redis-restore-drill-default.txt;
 Ruff check/format --check passed. Первый прогон упал лишь на неправильном
 ожидании слова RDB в log; assertion исправлен на фактическую loading error.
Результат ограничен synthetic Redis Stack7.2.0-v14 RDB same-version restore,
не production backup, AOF/PITR, users/ACL, cross-store consistency, business replay,
failover или migration versions. Рабочие данные/gameplay/src не затронуты.
Никаких commit/push/deploy; полный project gate/coverage не запускался.


Ведущий прочитал финальный Redis drill: frozen SAVE RDB переносится через
собственный временный файл/volume, новый Redis process, без working data.
139deploy regressions Passed/13external deselected,2.54s
(var/audit/step102b-deploy-regression.txt). Scoped hooks включая pip-audit Passed
(var/audit/step102b-redis-hooks.txt); docs/registry границы evidence обновлены.
Проверял исполнитель и ведущий в обычном режиме, не independent reviewer.
Scope:1new external drill,deployment docs,registry/progress; src/gameplay/settings
не менялись. AG-05 отложен до подготовки main, остальные operational пункты
A08-15 (schedule/offsite/retention/RPO/RTO/alerts и coherent cross-store recovery)
не закрыты; A08-02 isolation и A07-12 Studio остаются отдельными задачами.
Full project gate/coverage не запускались. Без commit/push/deploy.

Окончательный повтор ведущим:1passed25.28s, artifact
var/audit/step102b-redis-final-lead.txt, включая cleanup asserts. Markdownlint/
diff whitespace Passed. Status checked-awaiting-acceptance, reviewer not-requested.
После отчёта остановка.

## Шаг 10.3 — A08-02: edge/data network boundary — 21.10.2026

Запрос: одна задача изоляции сервисов, без ревизора, commit/push/deploy;
рабочие данные и игровую логику не трогать. Reviewer not-requested.
- N-R1: nginx/certbot не имеют общей сети с postgres/redis/mongo;
 HTTP upstreams доступны nginx через отдельную edge сеть.
- N-R2: сохранить application/storage DNS, workers/provider egress, volumes,
 images, env delivery и все production Compose layers/tools/bot/certbot helper.
- N-R3: проверять allow/deny topology и sanitized resolved Compose config,
 без запуска production stack или изменения host firewall/running containers.
План: сохранить tbmmorpg-network как data/application bridge, добавить
 tbmmorpg-edge для proxy/upstreams, init containers network_mode:none;
 проверить конфигурации и deploy regressions. Общие env secrets и роли
 хранилищ отдельный scope; полное A08-02 не заявлять.
Статус implementation pending / verification pending.

Результат A08-02 edge/data tranche: implementation done / verification pass,
checked-awaiting-acceptance; проверяет исполнитель, reviewer not-requested.
- [x] N-R1: nginx/certbot только tbmmorpg-edge; frontend/frontend-play/backend/chat
 dual-network; PostgreSQL/Redis/Mongo, migrations/workers/bot только прежняя
 tbmmorpg-network. У nginx и stores нет общей bridge network.
- [x] N-R2: имена data network, volumes, images, env delivery сохранены;
 bridge data network не internal:true, существующий provider/S3/Telegram egress
 не запрещён. Init файловых volumes явно network_mode:none, implicit default
 network не создаётся. Certbot shell/systemd используют edge default.
 Tools остаются на external data network; bot references не менялись.
- [x] N-R3: test_service_isolation.py 11passed2.35s, включая 4 negative topology
 mutations и 5 sanitized Docker Compose config resolutions: root include,
 infra+site, infra+game, все layers, все layers+tools; manual profiles включены.
 Evidence var/audit/a0802-topology.txt. Не читались .env/services env files.
- [x] Deploy regression 145passed16deselected3.14s до добавления последних двух
 external config cases; var/audit/a0802-deploy.txt. Ruff check/format passed.
Никаких stack up, работающих containers/networks/host firewall/data не меняли;
проверен только desired Compose contract, не live production connectivity.
Для применения требуется позднейшее recreate затронутых containers: существующий
 nginx продолжает старую topology до deploy. Shared env credentials, broad app
 access к stores, database roles и outbound least privilege отдельный scope;
полное operational закрытие A08-02 не заявляется. Игровая логика не менялась.
Без commit/push/deploy; full project gate/coverage не запускались.


Ведущий прочитал Compose/test/helper diff; тесты без production startup:
41passed/1nginx opt-in skipped,5.41s (step103-network-final.txt), включая
service isolation и существующие public/private edge/port contracts.
Test_source_topology + mutation случаи проверяют отсутствие общего network
proxy/stores, наличие upstream edge и отсутствие implicit default bridge.
5resolved Compose config используют sanitized env + empty env file, не реальные
secrets. CLI config не является запуском Docker stack или proof live blocking.
Docs deployment-contract и deployREADME initial certbot command обновлены.
Shared env_file/DB roles/application-to-stores broad access не устранены.
Nginx/certbot защита вступит в силу только при будущем recreate контейнеров;
текущая running topology не проверялась/не менялась. Рабочие данные/gameplay/src
не затронуты. No commit/push/deploy. AG-05 остаётся отложенным до main preparation.

Финальный обычный deploy suite ведущим:145passed/18external deselected,2.95s
(step103-deploy-final.txt);41network tests включают часть этих145 и не складываются
с ними как distinct coverage. Scoped hooks/pip-audit Passed (step103-hooks.txt),
Markdownlint/diff whitespace Passed. Reviewer not-requested,
checked-awaiting-acceptance. Full project gate/coverage не запускались.
Без commit/push/deploy; после отчёта остановка.

### Шаг 10.3b — A08-02: секреты tg-bot — 21.10.2026

Режим: без ревизора, commit/push/deploy. Только Compose и контрактные тесты;
рабочие данные, исходники приложения и игровая логика не меняются.

- [ ] Убрать broad env_file у production tg-bot; явно передавать только BotSettings.
- [ ] Сохранить обязательный SECRET_KEY, backend service key, runtime/logging knobs
  и прежние forced defaults; не менять имена настоящих секретов.
- [ ] Проверить sanitized Compose config с полным fake env и canary secrets,
  defaults/empty/false, а также парсинг BotSettings без .env и клиентов.
- [ ] Выполнить адресные тесты и deploy regression; зафиксировать ограничения.

Production workflow создаёт deploy/.env и запускает Compose из deploy: default
.env обеспечивает interpolation. Для нестандартного DEPLOY_ENV_FILE оператору
нужен явный --env-file: service env_file сам по себе interpolation не задаёт.

Результат 10.3b: implementation done / verification pass; reviewer not-requested.
- [x] У tg-bot удалён env_file; environment содержит все и только canonical aliases
  текущего BotSettings. SECRET_KEY оставлен: обязательное поле модели, не rotation.
- [x] Сохранены прежние forced production DEBUG/Redis/group настройки, приоритет
  GAME_STREAM_NAME и BACKEND_BASE_URL; logging/owner/throttling/updates/timeout
  получают прежние model defaults, explicit empty не подменяется default.
  BACKEND_API_KEY использует null pass-through: unset остаётся None, empty — empty.
- [x] 4 focused tests passed5.06s (a0802-bot-env.txt): static allowlist, sanitized
  real Compose config defaults/overrides/empty, fresh-process BotSettings parsing
  с _env_file=None. Canary credentials текущих PostgreSQL/Mongo/AI/S3/SMTP/site
  service/operator полей не попадают в resolved tg-bot. Container startup нет.
- [x] Deploy regression146passed21external deselected4.30s
  (a0802-bot-deploy.txt); Ruff check/format pass. Focused tests включают один
  static test, уже входящий в146: эти числа не складываются как distinct cases.

Остальные production app env_file не изменялись. Это только tg-bot tranche,
не полное закрытие A08-02; общий SECRET_KEY/Redis URL/backend credential по-прежнему
доступны bot как явно разрешённые настройки. Runtime данные/контейнеры не менялись.
Защита начнёт действовать только после будущего recreate. No commit/push/deploy.


Ведущий прочитал final Compose/test diff: no broad env_file у tg-bot, explicit
BotSettings fields, optional backend key pass-through сохраняет None vs empty.
10focused bot+isolation tests Passed,11.71s (step103b-bot-final.txt), включает4
Compose/settings boundary tests.146deploy regressions уже включают static allowlist
case; counts не складываются как distinct coverage. Sanitized CLI не запускает
контейнеры, не подтверждает реальные service permissions или live runtime env.
Docs deployment-contract и registry обновлены: central host.env/interpolation
сохраняется; остальные runtime services пока получают common env_file.
Внешние client API не вызываются, рабочие данные/gameplay/src не менялись.
AG-05 отложен до main preparation. No reviewer/commit/push/deploy.


Итог hooks ведущего: Ruff/format/YAML/Markdown Passed; detect-secrets первоначально
отметил fake credential canaries — помечены inline pragma:allowlist secret только
для synthetic литералов; повтор detect-secrets Passed. Никаких настоящих секретов
не добавлено и baseline не ослаблялся.
Pip-audit НЕ прошёл: installed virtualenv21.7.13 имеет4reported advisories:
CVE-2026-113726 (fix21.14.4), CVE-2026-113776/113732 (fix21.14.2),
CVE-2026-113725 (fix21.14.7). Artifact step103b-hooks.txt.
Это отдельный dependency follow-up; версии/lock/exceptions в этом scope не менялись.
Полного green hooks/gate не заявляю. Implementation done; verification partial
из-за dependency audit; functional scope passed, reviewer not-requested.
Docs/registry current status и ограничения сохранены. Diff whitespace и Markdown
Passed; index пуст. После отчёта остановка, без commit/push/deploy.


## Шаг 10.3c — virtualenv security update — 21.10.2026

Запрос: обновить virtualenv до безопасной версии, проверить compatibility и
pip-audit; без reviewer/commit/push/deploy, после отчёта остановиться.
V-R1: minimum21.14.7 закрывает4reported advisories; targeted lock upgrade,
сохранить накопленные edits и не обновлять unrelated dependencies.
V-R2: проверить installed version/pip check, реальное создание disposable venv
без app/network seeds, pre-commit работа. V-R3: pip-audit без новых exceptions.
Reviewer not-requested, небольшое dependency update выполняет ведущий локально.
PyPI21.14.7 JSON подтверждает release exists/non-yanked/Python>=3.9 и поддерживает
Python3.13/3.14; источник https://pypi.org/pypi/virtualenv/21.14.7/json.
План: snapshots, constraint+targeted lock, targeted install,smoke/hooks/audit/report.
Implementation pending/verification pending.


Результат virtualenv update: implementation done / verification pass,
checked-awaiting-acceptance; reviewer not-requested, проверял ведущий локально.
- [x] V-R1: constraint>=21.14.7, lock и installed virtualenv21.14.7. Только3package
 blocks изменены против snapshot:virtualenv21.7.13→21.14.7, distlib0.4.0→0.4.4,
 packaging26.2→26.3 (required minimum upstreamdistlib>=0.4.3,packaging>=26.3).
 Остальные dependency versions/blocks идентичны, накопленные certifi/Pillow и
 AG-05/CI/compose изменения сохранены. Первый uv lock получил Windows1224 lock,
 повтор успешно записал targeted lock; обходов/удалений файлов не было.
- [x] V-R2: uv lock --check pass; pip check no broken requirements. Создан no-seed
 disposable virtualenv на текущем CPython3.14.3, interpreter исполнен, cleanup.
 Fresh isolated PRE_COMMIT_HOME с local language:python hook успешно создал новое
 окружение и исполнил Python3.14.3 (не просто reuse старого cached hookenv).
 Smoke report helper первоначально неверно ожидал version у editable project;
 исправлен до успешного запуска. Virtualenv cache migration warning сохранил old
 cache location, но создание/исполнение hook успешны; user cache вручную не меняли.
 Dependency source contract7tests Passed,0.16s. Python3.13 здесь не запускался;
 совместимость release с ним объявлена upstream PyPI metadata, не local run proof.
- [x] V-R3: штатный pre-commit pip-audit Passed,4virtualenv advisories устранены,
 никаких новых ignore-vuln/exceptions не добавлено. Scope hooks Passed.
Evidence var/audit/virtualenv-{lock,install,lock-check,pip-check,smoke,audit,
 dependency-tests,hooks}.txt и virtualenv-lock-before.toml.
Source/gameplay/workingdata, branch/commit не менялись. Обновлены только3пакета
local .venv, constraint/lock и audit/progress status. No commit/push/deploy.
Full project gate/coverage не запускались. После отчёта остановка.

## Шаг 10.3d — A08-02: chat-archive-worker env allowlist — 21.10.2026

Запрос: разделить секреты ещё одного сервиса, без reviewer/commit/push/deploy;
рабочие данные и gameplay не менять. Reviewer not-requested.
AR-R1: удалить общий env_file только у chat-archive-worker; сохранить существующие
DB/Redis/Mongo/DEBUG overrides и реально поддерживаемые настройки инфраструктуры.
AR-R2: сохранить production validation без development ключей: SECRET_KEY и
FRONTEND_INTERNAL_SERVICE_KEY / SITE_TO_GAME_SERVICE_KEY остаются необходимыми
из-за общего BackendSettings, хотя архиватор не обслуживает authentication.
Это явный остаточный shared-settings долг, не закрытие всех A08-02.
AR-R3: исключить AI/S3/SMTP/bot/operator секреты; проверить synthetic Compose
canaries и defaults/overrides/empty semantics, actual worker import без .env и
подключений к рабочим хранилищам. Implementation pending / verification pending.
План: source trace, explicit allowlist, sanitized config/schema/import tests,
focused/deploy regression и scoped hooks. Проверяет исполнитель, не ревизор.

Результат исполнителя 10.3d: implementation done / verification pass,
checked-awaiting-acceptance, reviewer not-requested.
- [x] AR-R1: только chat-archive-worker лишён общего env_file; 16-key allowlist
 сохраняет 7 исходных overrides, logging4, DATABASE_ECHO, Mongo timeout, 3authkeys.
 SQL engine не использует inherited pool knobs; mandatory REDIS_URL исключает
 fallback Redis host/password, ARQ берёт URL. Бизнес-код не изменён.
- [x] AR-R2: production DEBUG False; реальные BackendSettings singleton и archive
 module импортированы свежим процессом с SettingsConfigDict(env_file=None) до
 импорта, без worker startup/connection. Valid frontend key и emptyfrontend+
 validsitefallback проходят; default/missing auth и dev-secret отклоняются.
 Optional authkeys null pass-through сохраняет missing vs explicit empty.
- [x] AR-R3: sanitized Compose --env-file и DEPLOY_ENV_FILE указывают только
 synthetic файл; canary AI/S3/SMTP/bot/operator не попадают в archive environment.
 Defaults, overrides, empty logging сохранены; empty numeric timeout отклонён,
 не заменён новым default. 8archive+4bot=12passed,26.86s; deploy nonexternal
 147passed/28deselected,4.36s. Счётчики пересекаются, не складываются.
 Ruff check/format pass. Evidence var/audit/archive-env-final.txt,
 archive-deploy.txt. Initial sandbox tmp_path permission error устранён выбором
 project-local basetemp и разрешённым local execution; actual focused run green.
 Никаких containers/clients startup, рабочих данных, gameplay, commit/push/deploy.
 A08-02 partial: SQL/site URL и shared validator authkeys остаются; role ACL и
 service-specific settings разделение отдельно. Реальный deployment не проверен.


Итог ведущего: прочитан Compose/test diff,13tests Passed,23.25s (8archive-env
контрактов+5existing archive regressions), step103d-final-tests.txt. Это повторная
обычная проверка, не independent review. Существующие bot4tests в отчёте исполнителя
и deploy static cases пересекаются с другими counts, не суммировать как distinct.
147обычных deploy Passed/28external deselected подтверждены artifact archive-deploy.txt.
Scoped hooks включая pip-audit Passed (step103d-hooks.txt), Markdownlint/diff
whitespace Passed. Docs deployment-contract и audit registry обновлены.
16explicit env keys: сохранены original DB bindings (включая site URL) и mandatory
shared production authkeys; их удаление/DB roles/Redis ACL/settings split здесь
не выполнялись. Общие secrets у других runtime services остаются. Host deployment
.env/interpolation сохранён, current running env не меняется без future recreate.
Рабочие данные/src/gameplay не изменены, AG-05 по-прежнему отложен до main.
Implementation done/verification pass в указанном scope; checked-awaiting-acceptance,
reviewer not-requested. Full project gate/coverage не запускались. Без commit/push/
deploy, после отчёта остановка.

Уточнение hooks evidence: initial step103d-hooks.txt имел detect-secrets false
positive на synthetic-fallback-key в test fixture (остальные hooks/pip-audit pass).
Помечен только этот synthetic literal, Ruff format выполнен; финальный
step103d-secrets-final.txt Passed. Baseline/реальные secrets rules не ослаблялись.
Итоговая комбинация scoped checks pass, а не исходный hook invocation exit0.

## Шаг 10.3e — A08-02: site-migrate env allowlist — 21.10.2026

Запрос: секреты одного дополнительного сервиса; без reviewer/commit/push/deploy,
рабочих данных и gameplay. Reviewer not-requested; проверяет исполнитель.
SM-R1: удалить общий env_file только site-migrate, сохранить site DB binding,
DEBUG False, production auth validation, supported logging/database echo.
SM-R2: исключить game DB/Redis/provider/S3/SMTP/bot/operator/root DB secrets.
Общие SECRET_KEY/BACKEND_INTERNAL_SERVICE_KEY остаются из-за FrontendSettings
production validator; их ротация и рефакторинг settings вне задачи.
SM-R3: synthetic Compose config + fresh actual Alembic offline SQL без .env,
сетевых подключений и записи БД; defaults/overrides/empty и invalid auth cases.
Implementation pending / verification pending.
План: trace Alembic→FrontendSettings/session/model imports; explicit allowlist;
санитизированные контрактные тесты, focused/deploy regression и scoped checks.

Результат исполнителя 10.3e: implementation done / verification pass,
checked-awaiting-acceptance, reviewer not-requested.
- [x] SM-R1: site-migrate без env_file;10 явных env keys. DATABASE_URL и
 SITE_DATABASE_URL привязаны только к site URL; DEBUG False, authkeys и4logging
 поля+DATABASE_ECHO сохранены. entrypoint/image/network прежние.
- [x] SM-R2: game DB/Redis/backend URL удалены только у migration service.
 Alembic env использует settings.database_url; frontend session создаёт engine
 без connect, model_imports только site ORM. Shared production authkeys остаются
 техническим долгом; DBroles/settings validator не менялись.
- [x] SM-R3:8 контрактных тестов Passed17.21s; synthetic Compose env/canaries,
 fresh FrontendSettings+database import, production reject missing/internal dev
 key/dev secret, defaults/overrides/empty logging, reject empty boolean.
 Actual Alembic offline SQL до0001_site_schema_baseline содержит site.auth_users/
 articles и не game таблицы; socket connections запрещены guard в subprocess.
 Это проверка migration startup/config и baselineSQL, НЕ online head migration.
 Fullhead offline unsupported:0002 требует SELECT.fetchall; initial attempt
 failed3 cases на этом ограничении, migrations не менялись. Final8 green.
 Evidence var/audit/site-migrate-env-final.txt; initial site-migrate-env.txt.
 Deploy nonexternal148passed35deselected5.24s, site-migrate-deploy.txt.
 Containers не запускались, рабочие .env/DB не читались, gameplay не менялся.
 A08-02 остаётся partial; другие runtime services/sharedauth/DBroles отдельно.
 Без reviewer/commit/push/deploy; применение только при будущем recreate.
Scoped hooks compose.site.yml+newtest Passed (including pip-audit, detect-secrets,
Ruff, Bandit), evidence var/audit/site-migrate-hooks.txt. Full project gate/coverage
не запускались. Финальная formatter-only правка убрала лишнюю пустую строку EOF.


Ведущий прочитал source trace Alembic env→frontend settings/session/model_imports
и final Compose/test diff.8адресных tests Passed15.35s (step103e-final-tests.txt),
с реальным offline baselineSQL и socketconnectguard; никаких DBwrites/network
connections или чтения application.env в subprocess. Это не proof fullhead
online migration.148обычных deploy regressions исполнителя подтверждены
site-migrate-deploy.txt,35external deselected; counts не суммировать без overlap.
Ведущий scoped hooks/pip-audit/detect-secrets Passed (step103e-hooks.txt).
Docs deployment-contract и registry обновлены. Shared frontend authkeys остаются
из-за общего settingsvalidator; ротации/roleACL/settings split не было.
Scope:1service mapping compose.site,1newtest,docs/registry/progress. Предыдущие
network/init и env changes сохранены; src/gameplay/migrations/workingdata не менялись.
Implementation done/verification pass в этом scope; checked-awaiting-acceptance,
reviewer not-requested. AG-05 отложен доmain; full project gate/coverage не запускались.
Нет commit/push/deploy, после отчёта остановка.

### Шаг 10.3f — A08-02: backend-migrate env isolation — 21.10.2026

Режим: без ревизора, commit/push/deploy; рабочие данные/gameplay не трогать.
BM-R1: только backend-migrate убрать общий env_file, оставить game SQL/Mongo,
DEBUG False, shared validator authkeys, SQL echo/Mongo timeout/logging settings.
BM-R2: исключить site SQL/Redis и AI/S3/SMTP/bot/operator/root DB secrets;
не менять src, миграции, роли или другие сервисы.
BM-R3: synthetic Compose config/canaries и fresh actual settings/manage/Alembic
baseline offline SQL/Mongo bootstrap imports с запретом network и dotenv.
План: trace startup consumers; explicit mapping; defaults/overrides/empty/auth
validation tests; targeted/deploy regression и scoped quality checks.
Implementation pending / verification pending.

Результат исполнителя 10.3f: implementation done / verification pass,
checked-awaiting-acceptance, reviewer not-requested.
- [x] BM-R1: backend-migrate без env_file;14 явных env keys. DATABASE_URL и
 GAME_DATABASE_URL только game URL; Mongo URL/database, DEBUG False, shared auth,
 DATABASE_ECHO/Mongo timeout и4logging settings сохранены. Entrypoint не менялся.
- [x] BM-R2: SITE_DATABASE_URL/REDIS_URL и чужие AI/S3/SMTP/bot/operator/root DB
 secrets не передаются. manage upgrade→Alembic env→game session/model imports
 использует settings.database_url; ensure-mongo-indexes→bootstrap→lazy provider
 использует mongo URL/database/timeout. Source/settings/migrations не менялись.
 Shared authkeys остаются из-за production validator; roleACL/settings split отдельно.
- [x] BM-R3:10 focused tests Passed44.41s, backend-migrate-env-final.txt.
 Sanitized Compose env/canaries, no host application.env; fresh actual manage/settings/
 game engine imports, Alembic baseline offline SQL с chat tables и без site tables;
 socket connect forbidden. Actual Mongo bootstrap registers6real repositories over
 local collection stub; provider URL/database/timeout asserted without driverclient.
 Defaults/overrides/empty logging/auth fallback valid; missing/dev auth/dev secret,
 empty boolean/timeout rejected. Это НЕ online head migration или index DBwrites.
 Deploy nonexternal149passed42deselected4.85s (before2extra external validation cases;
 nonexternal set unchanged), backend-migrate-deploy.txt. Ruff check/format Passed.
 Контейнеры не запускались, рабочие DB/env/gameplay не затронуты. Full gate/coverage
 не запускались; A08-02 partial, изменения применятся при будущем recreate.
 Без reviewer/commit/push/deploy; после отчёта остановка.


Ведущий прочитал final mapping/test/startup trace.10tests Passed32.13s
(step103f-final-tests.txt:8initialenv+2existing Mongo bootstrap), final10env cases
исполнителя подтверждены backend-migrate-env-final.txt (44.41s), включая2additional
invalid-service/empty-echo. Parent deploy149passed/44external deselected4.24s
(step103f-deploy-final.txt); counts пересекаются, не складывать как distinct.
Mongo actualprovider остаётся lazy _clientNone;6actualregisteredrepositories
созданы поверх StubDatabase. Это wiring/settings proof, не indexwrite/liveDBtest.
Game baseline offlineSQL действительно генерируется без network; online migration
не запускается. Docs/registry status обновлены. Source/gameplay/migrations,
workingdata/credentials/roles не менялись. Sharedauth requiredkeys сохраняются,
settings split и другие сервисы остаются отдельным A08-02scope. AG-05 отложен.

Итоговые scoped hooks включая pip-audit/detect-secrets Passed (step103f-hooks.txt),
Markdownlint/diff whitespace Passed. Implementation done/verification pass в
указанномscope, checked-awaiting-acceptance; independent reviewer not-requested.
Scope:1service mapping,1newtest,docs/registry/progress. Full project gate/coverage
не запускались; index пуст, no commit/push/deploy. После отчёта остановка.

## Шаг 10.3g — A08-02: generation-ai-worker secrets — 21.10.2026

Режим: без независимого ревизора, коммита, push и деплоя; рабочие данные
и игровая логика не меняются. Один сервис за заход.

- [x] GA-R1: заменить общий env_file явным allowlist GenerationAI worker;
  сохранить SQL/Mongo/Redis, Gemini key/model, logging, stream и runtime policy
  settings, production auth validator. Site DB и чужие секреты исключить.
- [x] GA-R2: synthetic Compose canaries и fresh actual worker import без .env,
  setup logging/startup/provider/network; defaults/overrides/empty и invalid auth/
  numeric settings. Контейнеры и реальные настройки не использовать.
- [x] GA-R3: focused и deploy regression, Ruff; ведущий завершил scoped hooks.
  Shared auth/DB roles и другие сервисы остаются отдельно; A08-02 partial.

План: проследить worker → shared ARQ container → settings/tasks/AI facade,
изменить только mapping сервиса, добавить тесты, выполнить проверки и отчёт.

Результат исполнителя 10.3g:

- [x] GA-R1: generation-ai-worker получает 20 явно перечисленных settings.
  Сохранены game SQL (DATABASE_URL/GAME_DATABASE_URL), Redis, Mongo database/timeout,
  production DEBUG=False и обязательные shared authkeys, SQL echo, 4 logging fields,
  Gemini key/model, GAME_STREAM_NAME/MAXLEN и COMBAT_AI_POLICY_PATH. Последние
  runtime settings нужны общему ArqWorkerContainer; gameplay/policy не менялись.
  Site DB, OpenAI/Openrouter, S3/SMTP/bot/operator/root credentials исключены.
  Источник: generation workers/arq.py → core/arq.py + arq_container.py → settings;
  tasks → get_manual_session_context → game database/session и Mongo payload store;
  AIService → GeminiProvider(settings.gemini_api_key, settings.gemini_model).
- [x] GA-R2: 12 focused tests Passed61.33s, generation-env-final.txt. Actual worker
  импортирован в fresh child с SettingsConfigDict(env_file=None), отключённым
  setup_arq_worker_logging и запрещёнными socket connect/connect_ex/create_connection.
  Startup/cron/task execution не запускались. RedisSettings/queue/task tuple/3cron
  bindings проверены; AIService forwarding проверен FakeProvider без SDK/provider I/O.
  Defaults/overrides/empty/missing Gemini и модель, logging, streams/policy passthrough;
  fallback auth допустим, missing/dev auth/dev secret/empty numeric/bool отвергаются.
  Synthetic Compose canaries не содержат рабочих credentials; контейнеров нет.
- [x] GA-R3: deploy nonexternal150passed55deselected4.37s,
  generation-deploy-tests.txt; Ruff check/format Passed. Первый sandbox tmp_path
  permission failure был до выполнения env cases; финальный прогон с project-local
  basetemp выполнен с успехом. Scoped hooks выполняет ведущий отдельно.

Shared validator authkeys пока остаются, settings split/DB roleACL/остальные сервисы
отдельно; A08-02 partial. Изменения начнут действовать при будущем recreate.
Рабочие данные, source/gameplay, volumes/images/roles не менялись. Full project gate
и coverage не запускались. Без reviewer/commit/push/deploy; после отчёта остановка.

Приёмка ведущего: проверены mapping и тесты; 37 AI regression tests Passed
(step103g-ai-regression.txt). Scoped pre-commit Passed, включая pip-audit,
detect-secrets, Bandit, Ruff и Markdownlint (step103g-hooks.txt).

## Шаг 10.3h — A08-02: system-worker secrets — 21.10.2026

Исходный запрос: разделить секреты ещё одного сервиса, без ревизора/коммита/push/
деплоя; рабочие данные и игровую логику не трогать. Один сервис: system-worker.

- [x] SW-R1: убрать общий env_file, оставить только доказанные settings startup/
  task consumers и shared production auth validator; не менять source/commands/
  images/networks/volumes/roles/реальные .env.
- [x] SW-R2: synthetic Compose canaries + fresh actual worker import без dotenv,
  logging/network/startup/task execution; проверить defaults/overrides/empty,
  bindings и отказы invalid production auth/numeric settings.
- [x] SW-R3: focused tests, deploy regression, Ruff и отчёт; ведущий выполнил hooks.

План: проследить system arq/shared container и зарегистрированные задачи, изменить
только service allowlist; добавить regression contract, выполнить проверки.

Результат исполнителя 10.3h:

- [x] SW-R1: system-worker переведён на allowlist20settings. Сохранены gameSQL,
  Redis, Mongo/database/timeout, shared production authkeys, DEBUG=False, echo,
  logging4, GAME_STREAM_NAME/MAXLEN, COMBAT_AI_POLICY_PATH,
  DEFAULT_SYMBIOTE_NAME и GAME_REFRESH_TOKEN_EXPIRE_MINUTES. Последние два
  сохраняют уже существующие overrides без изменения gameplay/source.
  Удалены siteDB и Gemini/Openrouter/OpenAI/S3/SMTP/bot/operator/root credentials.
  Trace: system arq→base_startup→ArqWorkerContainer→build_redis_managers
  создаёт GameSessionLockManager (TTL). Character tasks/integrators/model default
  используют default_symbiote_name. Rift flush session task пишет snapshot через
  get_mongo_provider; SQL tasks используют game get_session_context. Common events
  и notice publisher используют game_stream_name. apply_runtime_environment_overrides
  использует combat_ai_policy_path. В registered task graph character/inventory/
  exploration/rift/system/loot/expedition и infrastructure AIService/provider/key
  consumers не найдены; AI API ключи этим task graph не используются.
- [x] SW-R2:12 focused tests Passed33.98s, system-env-final-v3.txt. Synthetic CLI
  Compose, no actual .env; early SettingsConfigDict env_file=None + logging disable
  и socket connect/connect_ex/create_connection forbid до actual worker import.
  Проверены RedisSettings, queue, task tuple,2cronbindings; settings default/override/
  empty semantics, production auth fallback и invalid secrets/auth/numeric/bool.
  Actual GameSessionLockManager(None).ttl_seconds и CharacterSymbiote column default
  отражают override. Ни startup, tasks, AI/network, контейнеры, DB не запускались.
- [x] SW-R3: deploy nonexternal151passed66deselected3.85s,
  system-deploy-final.txt. Ruff check/format Passed. Ведущий отдельно выполнил
  system/queue regression12passed5.72s (step103h-system-regression.txt); counts
  пересекаются/имеют разный scope, не складывать как distinct project suite.
  Scoped hooks/registry/docs завершает ведущий. Full project gate/coverage не запускались.

Follow-up (закрыт в 10.3i): предыдущий generation-ai-worker также использует общий container
и GameSessionLockManager TTL, но его allowlist ещё не пропускает
GAME_REFRESH_TOKEN_EXPIRE_MINUTES (и CharacterSymbiote model import имеет
DEFAULT_SYMBIOTE_NAME). В этом system-only заходе прежний сервис не менялся;
проверить/preserve эти overrides отдельной следующей задачей.
Shared authvalidator/DBroles/settings split и другие сервисы остаются отдельно;
A08-02 partial. Working data/.env/source/gameplay/images/networks/roles не менялись.
Без reviewer/commit/push/deploy; результат применится при будущем recreate.

Приёмка ведущего: mapping и regression tests прочитаны; scoped pre-commit Passed
(step103h-hooks.txt), включая pip-audit, detect-secrets, Bandit, Ruff и Markdownlint.
Diff whitespace Passed, index пуст. Режим: checked-awaiting-acceptance,
independent reviewer not-requested; полный project gate не заявляется.

## Шаг 10.3i — Generation worker: два shared overrides — 21.10.2026

Запрос: закрыть хвост generation-ai-worker; без ревизора, коммита, push и деплоя.
Рабочие данные и игровую логику не менять. Малая адресная правка выполняется локально.

- [x] GF-R1: передать DEFAULT_SYMBIOTE_NAME и GAME_REFRESH_TOKEN_EXPIRE_MINUTES
  с прежними defaults и сохранением явных пустых значений.
- [x] GF-R2: проверить synthetic Compose и actual model default/lock TTL без сети,
  startup и задач; проверить отказ пустого numeric TTL; выполнить scoped hooks.

План: расширить только generation mapping и существующие isolation tests,
проверить, обновить документацию и статус хвоста. Reviewer not-requested.

Результат локального исполнителя: GF-R1 implementation done / verification pass.
Allowlist теперь 22 поля; defaults SYSTEM и 720 сохранены через `${VAR-default}`.
GF-R2: 13 адресных tests Passed53.58s (step103i-generation.txt), включая actual
CharacterSymbiote column default и GameSessionLockManager TTL, defaults/overrides/
empty-name и rejection empty numeric TTL. FakeProvider/socket guard сохранены;
startup/tasks/контейнеры/рабочие credentials не использовались. Deploy regression
151passed67deselected4.14s (step103i-deploy.txt); Ruff check/format Passed.
Scoped hooks Passed (step103i-hooks.txt), включая pip-audit/detect-secrets/Bandit/
Ruff/Markdownlint; diff whitespace Passed, index пуст. Режим checked-awaiting-acceptance.
Общая A08-02 остаётся partial; full project gate не запускался. Без коммита/push/
деплоя, рабочие данные и source/gameplay не менялись; после отчёта остановка.

## Шаг 10.3j — A08-02: combat-worker secrets — 21.10.2026

Исходный запрос: ещё один сервис secrets isolation, одна задача, без ревизора,
коммита/push/deploy; рабочие данные и игровую логику не трогать. Scope combat-worker.

- [x] CW-R1: убрать общий env_file и лишние credentials/siteDB, сохранить все
  startup/task/shared-container consumers и defaults/empty semantics. Source,
  commands/images/networks/roles/.env и simulation-worker не менять.
- [x] CW-R2: synthetic Compose canaries + fresh actual worker import с ранним
  dotenv/logging disable/socketguard; queue/task/settings/modeldefault/lockTTL
  bindings, invalid auth/numerics; без startup/tasks/provider/network/контейнеров.
- [x] CW-R3: focused tests + deploy regression + Ruff; результаты/ограничения.

План: trace combat arq→shared container/tasks/local-policy dependencies, explicit
allowlist, contract tests и доказательства. Независимый ревизор not-requested;
ведущий завершает docs/registry/hooks.

Результат исполнителя 10.3j (обычная проверка, reviewer not-requested):

- [x] CW-R1 implementation done / verification pass: combat-worker20fieldallowlist
  без env_file/siteDB/Gemini/Openrouter/OpenAI/S3/SMTP/bot/operator/root credentials.
  Сохранены gameSQL+Redis+Mongo,DEBUG=False,sharedauthvalidator keys,echo/Mongotimeout,
  logging4,game streams,policy path,symbiote name,refresh TTL. Все изменённые
  settings pass-through сохраняют missing-vs-empty семантику прежнего BackendSettings.
  Trace: arq→base_startup→ArqWorkerContainer→Redis managers/GameSessionLockManager,
  game eventproducer; character/scenario consumers→default_symbiote_name;
  finalization_persist_task→game get_session_context+CombatDocumentRepository/Mongo,
  victory_finalizer_task→RiftRuntimeSnapshotRepository/Mongo. AiProcessor→
  MonsterCombatBrain→PolicyStore(local JSON policy), APIprovider/key consumers
  в combat/task/integrations и затронутых infrastructure не найдены. Simulation
  worker не менялся. Source/gameplay/commands/images/networks/roles/.env неизменны.
- [x] CW-R2 implementation done / verification pass:12tests Passed45.00s,
  combat-env-final.txt. Ранний SettingsConfigDict(env_file=None), logging disable
  и socket connect/connect_ex/create_connection forbid перед fresh actualworker import.
  Queue/RedisSettings/7actualfunctions/maxjobs30/jobtimeout60/keep_result0,
  startup/shutdown bindings, actual modeldefault и lockTTL проверены. PolicyStore
  _resolve_path(None) проверен без load/cache/file generation. Defaults/overrides/
  empty, productionauthfallback, invalid secrets/auth/empty numeric/bool cases.
  Synthetic canaries/CLICompose, без startup/tasks/AI/DB/network/контейнеров/real.env.
  RED доmapping:1expected failure env_file present (combat-env-red.txt).
- [x] CW-R3 implementation done / verification pass:deploy nonexternal152passed
  78deselected4.10s (combat-deploy-final.txt),Ruffcheck/formatPassed. Ведущий отдельно
  выполнил queue-routing/victory-finalizer regression15passed5.06s(step103j-runtime.txt),
  не суммировать эти counts как distinct fullsuite. Scopedhooks/docs/registry ведущий.

A08-02partial:sharedvalidator auth,DBroleACL/settingssplit и остальные сервисы отдельно.
Изменения начнут действовать при будущем recreate; workingdata не трогались.
Fullprojectgate/coverage не запускались. Без reviewer/commit/push/deploy;
состояние checked-awaiting-acceptance в этомscope, послеотчёта остановка.

Проверка ведущего: mapping/test прочитаны, documentation/registry обновлены.
Scoped pre-commit Passed (step103j-hooks.txt), включая pip-audit, detect-secrets,
Bandit, Ruff и Markdownlint. Diff whitespace Passed, index пуст.
Independent reviewer not-requested; полный project gate не заявляется.

## Шаг 10.3k — A08-02: combat-ai-simulation-worker secrets — 21.10.2026

Исходный запрос: secrets isolation ещё одного сервиса, без ревизора/коммита/push/
деплоя; рабочие данные и игровую логику не менять. Scope только simulation worker.

- [x] CS-R1: заменить общий env_file доказанным allowlist; сохранить sharedcontainer/
  task consumers, defaults/empty overrides. Source/profile/commands/images/network/
  roles/.env и gameplay не менять; unused siteDB/foreign credentials исключить.
- [x] CS-R2: synthetic Compose с явным simulation profile, fresh actual worker
  import с ранним dotenv/logging disable/socketguard;4wrapped tasks/timeouts/maxtries,
  queue/maxjobs/keepresult,actualmodeldefault/TTL/policypath. Без startup/tasks/
  training/provider/network/контейнеров.
- [x] CS-R3: focused tests, deploy regression, Ruff, результат/ограничения.

План: trace simulation arq→tasks→services/training/sharedcontainer; mapping only,
контрактный тест и доказательства. Ведущий owns docs/registry/hooks; reviewer
not-requested. A08-02 целиком здесь не закрывается.

Результат исполнителя 10.3k:

- [x] CS-R1 implementation done / verification pass: simulation worker20fieldallowlist
  вместо env_file; siteDB/Gemini/Openrouter/OpenAI/S3/SMTP/bot/operator/root credentials
  исключены. Сохранены gameSQL/Redis/Mongo/database/timeout/sharedauth/DEBUG=False,
  echo/logging4/game streams/policy path/symbiote name/sessionTTL и missing-vs-empty
  settings semantics. Profile combat-ai-simulation, command/images/network unchanged.
  Trace ai_simulation_arq→4tasks→CombatAiSimulationRunService/local training/simulation
  →game get_session_context+runrepository, Redis progress; shared base_startup→
  container→managers/eventproducer/modelimports, Mongo repositories can be reached
  через local battle lifecycle. PolicyStore читает COMBAT_AI_POLICY_PATH. В этой
  цепочке AIService/LLMprovider/APIkey/siteDB consumers не найдены; live_simulator
  settings.decision_interval_multiplier — локальный BehaviorProfileSettings,
  не BackendSettings/env. Source/gameplay/training/policy content не менялись.
- [x] CS-R2 implementation done / verification pass:12focused Passed36.37s,
  simulation-env-final.txt. Compose CLI --profile combat-ai-simulation явно включён;
  static assertion profile unchanged. Actualfreshworker import с early dotenv/logging
  disable и socket connect/connect_ex/create_connection forbidden. Проверены queue,
  RedisSettings,4actualwrappedfunctions/timeouts180/2400/900/2400,maxtries1,maxjobs1,
  jobtimeout2400,keepresult0,startup/shutdown bindings,modeldefault,lockTTL,policy
  path resolution безload. Defaults/overrides/empty/invalidprodkeys/numeric failures.
  Дополнительно direct policy module import после cosmetic cleanup проверен через
  overrides1passed11deselected5.75s(simulation-import-final.txt). No startup/tasks/
  training/AIprovider/network/DB/контейнеры/real.env. RED доmapping1expectedfailure
  env_file present (simulation-env-red.txt).
- [x] CS-R3 implementation done / verification pass:deploy nonexternal153passed
  89deselected3.98s(simulation-deploy-final.txt),Ruffcheck/formatPassed. Parentselected
  routing/registration13passed41deselected6.07s(step103k-routing.txt); не складывать
  counts в distinct fullsuite. Ведущий завершает docs/registry/scopedhooks.

A08-02partial:sharedauthvalidator,DBroles/settingssplit и другие сервисы отдельно.
Workingdata/.env/source/gameplay/roles не менялись. Изменения применятся при будущем
recreate; Fullprojectgate/coverage не запускались. Reviewer not-requested,
checked-awaiting-acceptance вscope; без commit/push/deploy, послеотчёта остановка.

Проверка ведущего: mapping и test прочитаны; docs/registry обновлены.
Scoped pre-commit Passed (step103k-hooks.txt), включая pip-audit, detect-secrets,
Bandit, Ruff и Markdownlint. Diff whitespace Passed, index пуст.
Полный project gate не заявляется, independent reviewer not-requested.

## Шаг 10.3l — A08-02: chat secrets — 21.10.2026

Исходный запрос: ещё один сервис secrets isolation без ревизора/коммита/push/deploy;
рабочие данные и игровую логику не трогать. Scope chat (REST+realtime gateway).

- [x] CH-R1: убрать broad env_file/unused credentials/siteDB только после trace;
  сохранить actual auth/WS/stream/chat/storage/logging consumers и missing/empty
  semantics. Source/gameplay/commands/images/networks/roles/.env неизменны.
- [x] CH-R2: synthetic Compose canaries и fresh actualapp import с ранним dotenv/
  logging disable/socketguard; routes/authconfig/originpolicy/settings defaults/
  overrides/invalid values. Без lifespan/startup/DB/provider/network/контейнеров.
- [x] CH-R3: focused tests/deploy regression/Ruff; доказательства/ограничения.

План: trace chat.app/lifespan/routes/security/gameauth/realtime/storage consumers,
явный mapping и контрактные тесты. Ведущий owns docs/registry/hooks; reviewer
not-requested, A08-02 целиком не закрывается.

Результат исполнителя 10.3l:

- [x] CH-R1 implementation done / verification pass: chat30fieldallowlist вместо
  env_file; исключены siteDB и Gemini/Openrouter/OpenAI/S3/SMTP/bot/operator/root
  credentials. Trace app→RESTrouter→gameSQLChatThread/ChatSessionRepository+Mongo
  ChatBucketRepository; core.security AuthX использует secret/algorithm/tokenlocations/
  access minutes/refresh days. RealtimeWS→gameauth secret/algorithm/gameTTL;
  bootstrap_realtime→GameSessionLockManager TTL; WS origins/pinginterval/timeout.
  Lifespan→Redis + StreamRuntime(name/group/worker/pendingidle/scancount), MessageService
  buffermaxlen; Mongo timeout/database и SQL echo,4logging settings сохранены.
  GAME_STREAM_MAXLEN/chat_history_tail/policy/symbiotename/STREAM_ENABLED_GROUPS
  не имеют actual readers в app graph и не передаются: lifespan explicitly sets
  enabled_groups=None; WS tail — codeconstant50. Ничего из этого source не менялось.
  Group/worker сохраняют прежние ${CHAT_*:-default}, origins прежний explicit
  interpolation, новые passthrough settings сохраняют missing-vs-empty semantics.
- [x] CH-R2 implementation done / verification pass:16focused Passed60.66s,
  chat-env-first.txt. Fresh actualappimport с early SettingsConfigDict(env_file=None),
  setup_logging no-op и socket connect/connect_ex/create_connection forbidden.
  Проверены REST/WS/metrics/health route registrations,actual AuthX config/tokenTTL,
  GameSessionLock TTL,origin exactpolicy rejecting missing/hostile origins,
  sharedsettings defaults/overrides/empty and prodinvalid auth/numeric failures.
  STREAM_ENABLED_GROUPS injection excluded despite hostfakevalue. CSV origins и
  empty origins отвергаются существующим pydantic-settings JSONSource доfieldvalidator:
  accepted syntax JSONarray, parser/source в этомscope не исправлялся.
  RED доmapping1expectedfailure env_file present(chat-env-red.txt). После green
  изменены только cosmetic diagnostic/test name, Ruff повторно Passed; no behaviorchange.
  Без lifespan/startup/HTTP/DB/provider/network/контейнеров/working.env.
- [x] CH-R3 implementation done / verification pass:deploy nonexternal154passed
  104deselected4.40s(chat-deploy-final.txt),Ruffcheck/formatPassed. Parentrealtime/chat
  regression78passed2skipped1warning3.51s(step103l-realtime.txt); realRedis session
  revocation/replacement/logout cases skipped:TEST_REALTIME_REDIS_URL absent.
  Counts разных scope не суммировать какdistinctfullsuite. Ведущий owns hooks/docs/
  registry. Fullprojectgate/coverage и live WS/session/lifespan не запускались.

A08-02partial:sharedauthvalidator/DBroles/settingssplit/remainingservices отдельно.
Workingdata/gameplay/source/commands/images/networks/roles/.env неизменны.
Эффект после будущего recreate. Reviewer not-requested,checked-awaiting-acceptance
вscope; без commit/push/deploy, послеотчёта остановка.

Проверка ведущего: mapping/test прочитаны; docs/registry обновлены. Scoped
pre-commit Passed (step103l-hooks.txt), включая pip-audit, detect-secrets, Bandit,
Ruff и Markdownlint. Diff whitespace Passed, index пуст. Независимый ревизор
not-requested; полный project gate не заявляется.

## Шаг 10.3m — A08-02: backend secrets — 22.10.2026

Запрос: разделить секреты backend, без ревизора/коммита/push/deploy; рабочие данные
и игровую логику не трогать. Scope только backend Compose environment.

- [x] BE-R1: заменить общий env_file явным списком после trace app/lifespan/
  containers/routes/events; сохранить все используемые auth/operator/catalog/
  Gemini/world/streams/storage/runtime overrides и defaults/empty semantics.
- [x] BE-R2: synthetic Compose canaries и fresh actual app import с отключёнными
  dotenv/logging/network, без startup/DB/provider/контейнеров; defaults/overrides/
  invalid production settings и actual route/auth/AI forwarding contracts.
- [x] BE-R3: focused tests, deploy regression и Ruff; результаты и ограничения.

Source/gameplay/commands/images/networks/.env неизменны. План: trace consumers,
mapping, synthetic tests, проверки и отчёт. Reviewer not-requested;
ведущий owns docs/registry/hooks. A08-02 целиком здесь не закрывается.

Результат исполнителя 10.3m:

- [x] BE-R1 implementation done / verification pass: backend получает 40 явных
  settings. Сохранены game SQL/Mongo/Redis, shared production authkeys, JWT TTL/
  algorithm/locations, operator/catalog read/write keys, logging/SQL echo/Mongo
  timeout, Streams name/maxlen/group/worker/enabled groups/pending recovery,
  default symbiote/lock TTL, dev-rift flag, world auto-generation/mode, Gemini
  key/model и policy path. REALTIME_ALLOWED_ORIGINS explicit binding сохранён.
  Trace: backend.app → lifespan → RedisContainer/GameFeatureContainer/AIContainer;
  core.security/game_auth/operator_auth, monsters.api.access, rift.api.router,
  character/scenario model/defaults, infrastructure.mongo and actor-state manager.
  AIContainer создаёт AIService, поэтому Gemini key/model здесь нужны и сохранены.
  Site DB и Openrouter только объявлены в BackendSettings, runtime consumers нет.
  build_generated_asset_storage определён/экспортирован, но runtime callers после
  image retirement отсутствуют; S3/asset credentials исключены. Неиспользуемые
  monster migration/old flavor/bootstrap materialization/chat/app host fields
  не расширяют environment. Entry point, volumes, networking и source не менялись.
- [x] BE-R2 implementation done / verification pass:19focusedtests Passed85.05s
  (backend-env-final.txt). Actual app import uses early no-dotenv/no-logging/socket
  guards. Route/AuthX/modeldefault/lockTTL/operator keys and Gemini forwarding to
  FakeProvider checked; no lifespan/DB/provider calls. Defaults/overrides/empty,
  missing Gemini, partial/invalid stream groups, invalid production auth/numerics/
  world mode and JSON-only origins/locations verified. Policy export at app import
  checked, including bundled trained default vs explicit empty setdefault behavior.
- [x] BE-R3 deploy nonexternal155passed122deselected4.60s,
  backend-deploy-final.txt; Ruff check/format Passed. Ведущий отдельно выполнил
  auth/queue regression102passed1warning12.90s(step103m-auth.txt); counts разных
  scope не складывать в distinct fullsuite. Scoped hooks завершает ведущий.

Shared auth/settings split/DB roles и другие сервисы остаются A08-02 partial.
Рабочие данные, source/gameplay, real.env и роли не менялись. Применение после
будущего recreate, не текущий runtime change. Full project gate/coverage не запускались.
Reviewer not-requested; no commit/push/deploy; после отчёта остановка.

Проверка ведущего: mapping и tests прочитаны, docs/registry обновлены. Scoped hooks
(step103m-hooks.txt): Ruff/format/YAML/Markdownlint/Bandit/detect-secrets Passed.
Pip-audit FAILED: установленный virtualenv21.14.7, CVE-2026-113722, fix21.14.9.
Это новый dependency follow-up, не изменение backend environment; зависимости,
исключения и baseline в этом заходе не менялись. Полный hook gate не green.
Diff whitespace Passed, index пуст. Backend scope checked-awaiting-acceptance,
общий dependency gate partial; independent reviewer not-requested.

## Шаг 10.3n — virtualenv 21.14.9 — 22.10.2026

Запрос: обновить virtualenv до 21.14.9, проверить совместимость и pip-audit.
Без ревизора/коммита/push/deploy; после отчёта остановка. Малая правка локально.
- [x] VN-R1: targeted constraint/lock/install, сохранить остальные зависимости.
- [x] VN-R2: pip check/lock check, disposable venv и свежий pre-commit Python hook.
- [x] VN-R3: pip-audit без новых исключений, записать результат.

План: snapshot, release metadata, targeted update, smoke/dependency tests/hooks.
Source/gameplay/рабочие данные не менять. Reviewer not-requested.

Результат: implementation done / verification pass, checked-awaiting-acceptance;
проверял ведущий локально, independent reviewer not-requested.
Constraint >=21.14.9, lock и установленный пакет 21.14.9. Сравнение со snapshot
virtualenv-21149-lock-before.toml подтверждает изменение только virtualenv package
block; остальные версии/blocks идентичны. Targeted install изменил один пакет.
PyPI metadata https://pypi.org/pypi/virtualenv/21.14.9/json: non-yanked, Python>=3.9,
классификаторы Python3.13/3.14. Локально проверен Python3.14.3; 3.13 не запускался.
Pip check и uv lock --check Passed. No-seed disposable venv создан, interpreter
исполнен, окружение удалено после проверки exact path внутри var/audit.
Fresh PRE_COMMIT_HOME создал новое Python hook environment; hook Passed.
Dependency-source contracts7passed0.24s. Scoped hooks Passed, включая pip-audit и
detect-secrets; CVE-2026-113722 больше не блокирует gate, исключения не добавлялись.
Evidence: var/audit/virtualenv-21149-{lock,install,lock-check,pip-check,smoke,
precommit-smoke,dependency-tests,hooks}.txt. Старый отчёт failure10.3m исторический.
Source/игровая логика/рабочие данные не менялись. Full project gate не запускался.
Без коммита/push/deploy; после отчёта остановка, следующая A08-02 задача отдельно.

## Шаг 10.3o — A08-02: frontend site secrets — 22.10.2026

Запрос: разделить секреты frontend, без ревизора/коммита/push/deploy; рабочие данные
и игровую логику не менять. Scope только frontend(site), не frontend-play.

- [x] FE-R1: заменить broad env_file явным списком после trace site app/auth/email/
  feedback/backend clients/assets/settings; сохранить потребляемые overrides и
  missing/empty semantics. Source/commands/images/networks/volumes/.env не менять.
- [x] FE-R2: synthetic Compose canaries и fresh actual site app import с ранним
  dotenv/logging disable/socketguard; auth/cookie/SMTP/client/settings contracts.
  Без lifespan/startup/email/DB/provider/network/контейнеров.
- [x] FE-R3: focused tests, deploy regression, Ruff; результаты/ограничения.

План: trace consumers, explicit mapping, synthetic contracts, проверки и отчёт.
Reviewer not-requested, ведущий owns docs/registry/hooks; A08-02 partial.

Результат исполнителя 10.3o:

- [x] FE-R1 implementation done / verification pass: frontend(site) получает
  60 явных переменных. Удалены общий env_file, GAME_DATABASE_URL и чужие Mongo/
  AI/bot/root credentials. Site SQL/Redis, auth/service/operator keys, SMTP,
  cookie/CSRF/JWT/cache TTL, play availability URLs/timeout, logging, SEO/release/
  templates/static/generated paths и S3 serving settings сохранены.
  Nullable passthrough сохраняет Python defaults при отсутствии и явные empty
  values. S3 нельзя исключать: app configure_generated_asset_serving вызывается
  при импорте, site_ops также использует S3 configuration; factory/SDK проверен
  через Fake boto3.client, без запросов. SMTP get_email_service создаётся без send.
  Redis нужен NewsRepository (REDIS_URL publisher), backend operator keys нужны
  admin cabinet clients. FrontendSettings не объявляет domain_name/game_stream_name:
  env overrides этих getattr fallback раньше не принимались, они не добавлены.
  Play-only app_host/port/realtime URL/active-character и game-token cookie flags/
  symbiote/dev-rift settings не передаются. Frontend-play service не менялся.
- [x] FE-R2 implementation done / verification pass:14 адресных tests Passed46.81s
  (frontend-env-final.txt). Synthetic Compose без real.env, fresh actual site app
  import с ранним SettingsConfigDict(env_file=None), logging disable и socket
  connect/connect_ex/create_connection guard. Проверены site routes, отсутствие
  game session route, AuthX, actual auth/CSRF cookie secure/domain, backend client,
  SMTP constructor, S3 factory forwarding и missing credentials fail-before-SDK,
  defaults/overrides/empty/invalid production secrets/numerics/lists/enums.
  GENERATED_ASSETS_DIR всегда временный, setup не создаёт directories рабочих
  assets. PYTHONPATH child=root+root/src соответствует Docker /app:/app/src и
  использует vendored src/fastapi_cabinet; первоначальный import failure из-за
  test path исправлен без установки dependencies/stubs/изменения source.
  Первоначальный static test ошибочно исключал нужный SMTP_PASSWORD; исправлен.
- [x] FE-R3 implementation done / verification pass:deploy nonexternal156passed
  135deselected4.38s(frontend-deploy-final.txt), Ruff check/format Passed. Parent
  site regression44passed1warning5.24s(step103o-site.txt), counts разных scope не
  суммировать как distinct fullsuite. Scoped hooks завершает ведущий после freeze.

Без lifespan/startup/отправок email/S3 requests/DB/контейнеров/working.env.
Source/gameplay/commands/images/networks/volumes/roles не менялись. Эффект после
будущего recreate. Shared auth/DB roles/остальные сервисы остаются A08-02 partial.
Full project gate/coverage не запускались. Reviewer not-requested,
checked-awaiting-acceptance в scope; без commit/push/deploy, после отчёта остановка.

Проверка ведущего: mapping и actual-site contracts прочитаны, docs/registry обновлены.
Scoped hooks (step103o-hooks.txt): pip-audit, Ruff/format, YAML, Markdownlint и Bandit
Passed. Detect-secrets первоначально отметил synthetic SMTP password и test-mode
error label; добавлены inline allowlist pragma только к двум тестовым литералам.
Повтор detect-secrets Passed (step103o-secrets-recheck.txt), Ruff/format Passed.
Baseline/сканер/настоящие секреты не менялись. Diff whitespace Passed, index пуст.
Независимый ревизор not-requested; полный project gate не заявляется.


## Шаг 10.3p — A08-02: frontend-play secrets — 22.10.2026

Запрос: разделить секреты frontend-play; без ревизора/коммита/push/deploy,
рабочие данные и игровую логику не менять. Scope только frontend-play.

- [x] FP-R1: заменить broad env_file доказанным allowlist; сохранить play cookies/
  session/WS/backend clients/assets/site-auth/renderer overrides и defaults/empty.
  Не переносить SMTP/operator credentials без actual play consumer.
- [x] FP-R2: synthetic Compose/fresh actual play app import с отключёнными dotenv/
  logging/socket I/O; routes/auth/game cookies/CSRF/backend client/assets settings.
  Без lifespan/startup/email/S3/DB/provider requests и контейнеров.
- [x] FP-R3: focused tests/deploy regression/Ruff, результаты и ограничения.

План: trace play dependencies, mapping, synthetic contract и проверки. Source,
commands/images/networks/volumes/.env не менять. Reviewer not-requested;
ведущий owns docs/registry/hooks, A08-02 partial.

Результат исполнителя 10.3p:

- [x] FP-R1 implementation done / verification pass: frontend-play получает
  48 явных настроек. Сохранены site SQL, shared site-auth JWT/service key/header,
  auth/game/active-character cookie flags/domain, CSRF, backend/WS/site URLs,
  symbiote/dev-rift flags, renderer SEO/release/analytics, logging, templates/
  static/generated paths и actual S3 serving config. Nullable passthrough сохраняет
  Python defaults и explicit empty values. REALTIME_WS_URL сохраняет прежний
  Compose fallback на PLAY_PUBLIC_BASE_URL, включая явно пустой REALTIME_WS_URL.
  Site DB нужен AuthUserMiddleware/FrontendAuthService refresh и presence rollup;
  все game queries выполняются typed backend HTTP clients, не game SQL.
  Удалены общий env_file, GAME_DATABASE_URL, REDIS_URL, Mongo/AI/bot/root и SMTP/
  backend operator credentials. NewsRepository Redis publisher доступен только
  site handlers; RedisFrontendAuthUserCache не создаётся нигде в src/frontend,
  AuthPersistence содержит только SQL UserRepository/TokenRepository. SMTP factories
  и cabinet operator clients не вызываются play routes; cabinet не включается
  при surface=play. S3 сохранён: общая app generated-asset serving и CSP его используют.
  Frontend(site) mapping идентичен snapshot frontend-play-site-before.json;
  команды, образы, mounts и сети сохранены.
- [x] FP-R2 implementation done / verification pass:15 адресных tests Passed50.15s
  (frontend-play-env-final.txt), first selected5passed22.86s. Synthetic Compose,
  ранние dotenv/logging disable и socket connect/connect_ex/create_connection
  guard, child PYTHONPATH=root+src соответствует Docker /app:/app/src. Actual
  play app routes включают game-lobby/session, не login/account/admin; AuthX,
  actual site-auth/game/active-character/CSRF cookie writers, backend API client,
  S3 factory через fake boto3 без SDK calls, missing S3 failure-before-client,
  defaults/overrides/empty/invalid secrets/bools/lists/enums и realtime fallback
  проверены. SMTP/operator fields остаются defaults и не получают canaries.
  Generated asset directory временный во всех cases; рабочие assets не трогались.
- [x] FP-R3 implementation done / verification pass:deploy nonexternal157passed
  149deselected4.55s(frontend-play-deploy-final.txt), Ruff check/format Passed.
  Parent play routing/cookies/lobby/assets regression47passed1warning4.95s
  (step103p-play.txt); counts разных scope не суммировать как distinct fullsuite.
  Scoped hooks/docs/registry завершает ведущий после freeze.

Без lifespan/startup/HTTP/email/S3/DB/provider requests/контейнеров/real.env.
Source/gameplay/roles не менялись. Эффект после будущего recreate; shared auth/
DB roles/settings split остаются A08-02 partial. Full project gate/coverage не
запускались. Reviewer not-requested, checked-awaiting-acceptance в scope;
без commit/push/deploy, после отчёта остановка.

Проверка ведущего 10.3p: mapping и actual play contracts прочитаны; docs/registry
обновлены. Scoped pre-commit Passed (step103p-hooks.txt), включая pip-audit,
detect-secrets, Bandit, Ruff, YAML и Markdownlint. Diff whitespace Passed, index пуст.
Независимый ревизор not-requested; полный project gate не заявляется.


## Шаг 10.3q — Generation worker: разделение runtime/auth settings — 22.10.2026

Запрос: убрать ненужные auth-ключи generation-ai-worker через разделение настроек.
Без ревизора/коммита/push/deploy. Gemini и игровую логику не менять, рабочие данные
не трогать. Scope: только устранение auth зависимости GenerationAI worker.

- [x] GS-R1: отдельный ограниченный runtime config без auth полей и валидатора;
  GenerationAI worker не требует SECRET_KEY/FRONTEND_INTERNAL_SERVICE_KEY/
  SITE_TO_GAME_SERVICE_KEY. API и другие entrypoints сохраняют строгую auth validation.
- [x] GS-R2: сохранить Gemini/model, хранилища, queues/cron/concurrency, default/
  empty semantics и runtime policy/symbiote/lock TTL, без gameplay изменений.
- [x] GS-R3: RED перед production edits, fresh worker import и isolated startup
  dependency wiring с fakes; API/other-worker negative auth tests и regression checks.

План: trace transitive imports; выделить runtime settings и пересоединить общие
инфраструктурные consumers, сохранив auth config для API entrypoints. Удалить три
auth env поля только у GenerationAI. Проверить без real.env/сетевых/DB/provider I/O.
Reviewer not-requested; parent owns docs/registry/hooks. Implementation pending.

Результат исполнителя 10.3q: implementation done / verification pass в scope,
reviewer not-requested. RuntimeSettings содержит только shared runtime fields,
не имеет secret_key/frontend_internal_service_key/site_to_game_service_key/operator/
catalog auth полей. BackendSettings наследует common поля и сохраняет прежние
auth/consumer-group validators без изменения условий; API, chat и остальные
worker entrypoints по-прежнему отвергают missing production auth.

Shared consumers переподключены к runtime_settings as settings: SQL/Mongo,
core ARQ/container/AI, symbiote model/schema/repository/integrator, scenario sysactor,
lock TTL и notices stream name. Изменены только configuration imports, не алгоритмы.
GenerationAI logging явно получает runtime config. Logging остальных worker по
умолчанию лениво импортирует BackendSettings и сохраняет validation gate.
Asset-storage factory больше не импортирует API settings при импорте generation
package; прежний default config разрешается лениво при вызове factory. В registry
items.text этого вызова нет. Dummy keys/env selectors/auth skip flags не добавлялись.

Только generation-ai-worker удалены три auth env поля: allowlist теперь19settings.
Gemini/model и19runtime bindings сохранены; другие service mappings не менялись.
Чистый AST helper для deploy harnesses объединяет поля runtime.py/settings.py,
не импортирует singleton;7existing backend harnesses обновлены для inherited fields.

Проверки:

- RED:1expected failure7deselected1.38s — worker импорт без auth падал на прежнем
  BackendSettings validator (step103q-red.txt), до production edits.
- Runtime/auth final10passed32.76s(step103q-settings-complete.txt): fresh actual
  worker + load_orm_models без импорта API settings;6authenticated entrypoints
  missing-auth reject, valid backend auth accept, generation→API same-process reject.
  Actual generation startup/base container и shutdown wiring исполнены с fake
  Redis/config/producer/provider adapters; Mongo/SQL config проверен без connections.
  Windows event loop self-pipe создан до socket guard, далее все application I/O
  запрещены; первое startup harness failure было локальным self-pipe, не app I/O.
- Generation Compose/settings13passed62.43s(step103q-generation.txt): absenceauth,
  hostileauthcanaries не доставляются, Gemini FakeProvider forwarding, defaults/
  overrides/empty/missing key/typed failures, queue/tasks/cron/model default/TTL.
- Cross-backend defaults/overrides14passed75deselected81.38s
  (step103q-env-regression.txt). Deploy nonexternal157passed149deselected4.20s
  (step103q-deploy.txt). Source/gameplay behavior guards preserved.
- Scoped mypy18sourcefiles Success(step103q-mypy.txt), без новых ignore/noqa.
  Ruff check/format28files Passed; scope list var/audit/step103q-scope.json.
- Parent regression234passed135skipped2warnings13.14s(step103q-parent.txt), skips
  opt-in real SQL/Mongo/Redis GenerationAI/realtime; это не full integration proof.

Нет real.env reads, рабочих DB/provider/network requests, production startup или
данных. Gemini facade/provider API, gameplay, queues/cron/concurrency неизменны.
API и другие worker env delivery сохраняются; shared keys/DB role ACL отдельные.
Full project gate/coverage не запускались, scoped hooks завершает ведущий после READY.
Без reviewer/commit/push/deploy; после отчёта остановка.

Приёмка ведущего 10.3q: runtime/API split, consumer imports, lazy asset config и
startup/negative contracts прочитаны; docs/registry обновлены. Scoped hooks
(step103q-hooks.txt): YAML/JSON/Ruff/format/Markdownlint/Bandit/pip-audit Passed.
Trailing-whitespace исправил пробелы плана; повтор Passed. Detect-secrets отметил
только synthetic Gemini fixture; inline pragma добавлена к одному тестовому
литералу, повтор Passed (step103q-secrets-recheck.txt), Ruff/format Passed.
Настоящие secrets, baseline, исключения и зависимости не менялись.
Compatibility-required: значения env, API auth validation и Gemini contracts
сохранены; прежняя worker auth dependency удалена без bypass/profile env flags.
Diff whitespace Passed, index пуст; checked-awaiting-acceptance, reviewer
not-requested. Общая A08-02 остаётся partial, full project gate не заявляется.


## Шаг 10.3r — system-worker: убрать auth dependency — 22.10.2026

Запрос: убрать ненужные auth-ключи system-worker через существующий runtime split.
Без ревизора/коммита/push/deploy; рабочие данные и игровую логику не менять.

- [x] SY-R1: system entrypoint явно использует RuntimeSettings; удалить только
  его SECRET_KEY/FRONTEND_INTERNAL_SERVICE_KEY/SITE_TO_GAME_SERVICE_KEY delivery.
- [x] SY-R2: сохранить SQL/Mongo/Redis, logging, stream/policy, symbiote/TTL и
  queues/functions/cron/concurrency/timeout/result contracts без gameplay изменений.
- [x] SY-R3: RED перед production edits; fresh import/load ORM/startup/shutdown
  с fakes без auth/сетевых/DB/provider I/O, same-process API gate и strict остальные
  entrypoints; scoped env/deploy/regression/type/lint checks.

План: доказать старую auth dependency тестом, переподключить logging config и
убрать три env поля у system; адаптировать лишь затронутые contracts. Не менять
другие entrypoints/env delivery, RuntimeSettings и actual task implementations.
Reviewer not-requested; parent owns docs/registry/hooks. Implementation pending.

Результат исполнителя 10.3r: implementation done / verification pass в scope.
System worker использует существующий runtime_settings через явный logging config;
RuntimeSettings, shared helper и task implementations не менялись. Только system
Compose mapping удалены SECRET_KEY, FRONTEND_INTERNAL_SERVICE_KEY и
SITE_TO_GAME_SERVICE_KEY: allowlist20→17. Другие env mappings/entrypoints неизменны.
Queues/functions/cron/max_jobs20/job_timeout60/keep_result5 сохранены.

Trace system arq → character/inventory/exploration/rift/system/loot task imports и
load_orm_models не импортируют API settings после существующего 10.3q split.
SQL/Mongo/Redis/common-container settings, default_symbiote_name, lock TTL и policy/
stream overrides сохранены; body игрового кода не менялся. System startup не
создаёт AI service/provider; auth/Gemini credentials ему не нужны и не доставляются.

Проверки:

- RED до production edits:1expected failed12deselected2.37s — fresh system import
  без auth падал на BackendSettings production validator (step103r-red.txt).
- Runtime/auth final12passed56.40s(step103r-settings.txt). System actual import и
  load_orm_models без API settings, startup/base-container/shutdown с fake adapters,
  отсутствие AI calls; system→API same-process gate. Generation contracts прежние.
  System удалён из старого strict negative списка намеренно;5remaining auth entrypoints
  missing-auth reject, valid API auth accept. Никакого validation bypass.
- System env12passed54.64s(step103r-system-env.txt):17fields, absent/dev/hostile auth
  canaries не передаются, runtime defaults/overrides/empty и invalid typed fields,
  actual RedisSettings/8functions/2cron schedules/maxjobs/timeout/keepresult/modelTTL.
- Deploy nonexternal157passed149deselected4.41s(step103r-deploy.txt).
- Scoped mypy1sourcefile Success(step103r-mypy.txt), без новых ignores/noqa.
  Ruff check/format3files Passed. Exactscope:var/audit/step103r-scope.json.

Fresh subprocess: early dotenv disable и socket guard; Windows internal event-loop
self-pipe создан до guard, затем все application I/O запрещены. Нет real.env,
working DB/provider/network requests, рабочего startup, данных или gameplay edits.
API/chat/combat/simulation auth contracts и другие worker delivery остаются как были;
общая A08-02 partial, shared keys/DBroles отдельно. Full project gate/coverage не
запускались. Parent выполняет system/API regressions и scoped hooks после READY.
Reviewer not-requested; no commit/push/deploy, после отчёта остановка.

Parent system/API regression106passed1warning11.34s(step103r-parent-retry.txt).
Первый sandbox запуск остановлен после stall на collection; escalated retry с
project-local basetemp завершился успешно. Это не production/data запуск.

Приёмка ведущего 10.3r: прочитаны entrypoint, environment contracts и
startup/auth guards. Scoped hooks всех 7 файлов Passed: YAML, Ruff/format,
Markdownlint, Bandit, pip-audit с прежними исключениями, detect-secrets и
whitespace (step103r-hooks.txt). Зависимости, scanner baseline и исключения
не менялись. Рабочие данные, gameplay, commit/push/deploy не затрагивались.
Статус checked-awaiting-acceptance, reviewer not-requested. Full project gate
не запускался; применение в работающих контейнерах отложено. После отчёта стоп.


## Шаг 10.3s — combat-worker: убрать auth dependency — 22.10.2026

Запрос: убрать ненужные auth-ключи combat-worker; без ревизора/коммита/push/deploy,
игровую логику и рабочие данные не менять. Scope только combat-worker.

- [x] CB-R1: явно использовать existing runtime_settings для logging; удалить
  только его SECRET_KEY/FRONTEND_INTERNAL_SERVICE_KEY/SITE_TO_GAME_SERVICE_KEY delivery.
- [x] CB-R2: сохранить SQL/Mongo/Redis, local policy/TTL/symbiote/streams/logging,
  queue/7functions/maxjobs30/timeout60/keepresult0 и startup/shutdown wiring.
- [x] CB-R3: RED до production edits; fresh combat import/load ORM/startup
  с fakes без auth/сетевых/DB/provider I/O, same-process API gate, оставшиеся
  authenticated entrypoints strict; scoped tests/deploy/lint/type проверки.

План: trace task imports, RED; logging config и3envfields combat only, адаптация
затронутых tests. No RuntimeSettings/helper bypass/dummy keys/игровых body edits.
Другие entrypoints/env delivery не менять. Reviewer not-requested; parent owns
docs/registry/hooks. Реализация и адресные проверки завершены.


Использован существующий RuntimeSettings явно в logging combat-worker. Только
его allowlist сокращён с 20 до 17 полей: три API auth-ключа больше не передаются.
RuntimeSettings, helper и API validators не менялись; игровые task bodies,
очередь, семь functions, maxjobs30/timeout60/keepresult0 сохранены.

Проверки и доказательства (var/audit/step103s-*.txt):

- RED: новый fresh import до production edits упал на BackendSettings auth
  validation (1 failed, 14 deselected, 1.89s; red.txt).
- Runtime/auth: 14 passed, 67.42s (settings.txt); combat импортирует все tasks
  и ORM без API settings. Actual startup/shutdown проверены с fake adapters:
  CombatSessionIntegration, CombatExecutor, AiProcessor и их dependency wiring.
  Combat→API в одном процессе не ослабляет auth gate; simulation остаётся strict.
- Combat Compose environment: 12 passed, 51.21s (combat-env.txt), включая canary
  auth exclusion и runtime defaults/queue/contracts. Обычный deploy: 157 passed,
  149 deselected, 4.12s (deploy.txt).
- Parent ARQ/API/combat regression: 114 passed, 1 warning, 11.59s (parent.txt).
- Scoped mypy: Success, 1 source file (mypy.txt). Ruff и format --check: Passed,
  три Python-файла. Новые suppressions не добавлялись.

Проверки используют sanitized env и fakes: рабочие DB, provider и игровые
операции не вызываются. Windows asyncio self-pipe создаётся до socket guard;
application adapters защищены от внешнего I/O. Контейнеры не запускались,
рабочие данные не менялись. Полный project gate/coverage не запускался.
A08-02 в целом partial: shared keys и DB roles остаются отдельными задачами.
Parent выполняет scoped hooks после READY. Reviewer not-requested;
commit/push/deploy не выполнялись. После отчёта остановка.

Приёмка ведущего 10.3s: entrypoint, startup/auth contracts и environment tests
прочитаны; docs/registry обновлены. Scoped hooks 7 файлов Passed, включая
Ruff/format, YAML, Markdownlint, Bandit, detect-secrets и pip-audit с прежними
исключениями (step103s-hooks.txt). Зависимости, baseline и исключения не менялись.
Статус checked-awaiting-acceptance; reviewer not-requested. Full project gate
не запускался, operational rollout отложен, A08-02 partial. Без рабочих данных,
gameplay edits, commit/push/deploy; после отчёта остановка.


## Шаг 10.3t — combat-ai-simulation-worker: убрать auth dependency — 22.10.2026

Запрос: один инфраструктурный заход без ревизора, коммита, push и deploy;
игровую логику, simulation/training execution и рабочие данные не трогать.

- [x] SIM-R1: existing runtime_settings явно для logging; только simulation
  allowlist удалить SECRET_KEY/FRONTEND_INTERNAL_SERVICE_KEY/SITE_TO_GAME_SERVICE_KEY.
- [x] SIM-R2: сохранить profile, четыре tasks с timeout180/2400/900/2400,
  maxtries1/maxjobs1/jobtimeout2400/keepresult0, очередь и runtime contracts.
- [x] SIM-R3: RED до production edits; fresh import/load ORM, actual startup
  и shutdown с fakes без external I/O, same-process API strict gate; scoped
  runtime/env/deploy/lint/type проверки.

План: failing no-auth import; explicit logging config и три env fields только
этого worker; адаптировать runtime/env contracts. Runtime/helper/API validator
не менять, dummy keys и bypass не добавлять. Parent owns docs/registry/hooks.
Reviewer not-requested; implementation done, verification pass (исполнитель).


Только logging entrypoint использует existing runtime_settings; simulation
allowlist20→17 без трёх API auth keys. Profile/task bodies/timeouts/queue/limits
сохранены. RuntimeSettings/helper/API validators и другие delivery не менялись.

Доказательства var/audit/step103t-*.txt:

- RED:1 failed14deselected1.31s, ожидаемый BackendSettings auth gate (red.txt).
- Fresh simulation import/load ORM/startup/shutdown с guarded fakes:3passed
  13deselected20.99s(first.txt); task/simulation/training не запускались.
- Полные runtime/API contracts:16passed84.15s(settings.txt); API/settings/chat
  остаются strict, включая API после simulation import в том же процессе.
- Sanitized Compose environment:12passed49.70s(env.txt); ordinary deploy:
  157passed149deselected3.75s(deploy.txt).
- Parent logging/queue/API:103passed1warning10.39s(parent.txt), без simulation.
- Scoped mypy:Success1source(mypy.txt); Ruff/format:Passed3Pythonfiles.

Dotenv отключён; рабочие DB/provider не вызываются, контейнеры не запускаются.
Startup wiring проверен с fakes, реальные storage semantics не проверялись.
Full project gate/coverage не запускался. A08-02 остаётся partial; shared keys
и DB roles отдельно. Parent hooks после READY. Без ревизора, коммита, push,
deploy и изменений рабочих данных/игровой логики. После отчёта остановка.

Приёмка ведущего 10.3t: прочитаны runtime/startup/auth contracts и source diff;
docs/registry обновлены. Scoped hooks 7 файлов Passed, включая YAML, Ruff/format,
Markdownlint, Bandit, pip-audit с прежними исключениями и detect-secrets
(step103t-hooks.txt). Зависимости, baseline и исключения не менялись.
Статус checked-awaiting-acceptance, reviewer not-requested. Full project gate
не запускался; operational rollout отложен, A08-02 partial. Без gameplay edits,
симуляций/обучения, рабочих данных, commit/push/deploy; после отчёта стоп.


## Шаг 10.3u — chat-archive-worker: убрать auth dependency — 22.10.2026

Запрос: один заход без ревизора, коммита, push/deploy, изменений игровых
алгоритмов и рабочих данных. Actual streams не архивировать.

- [x] ARC-R1: archive использует existing runtime_settings as settings; только
  его три API auth-ключа удалить из allowlist16→13. SITE_DATABASE_URL оставить.
- [x] ARC-R2: сохранить algorithm/cron10min/functions/maxjobs/Redis defaults.
- [x] ARC-R3: RED до production edits; fresh import/loadORM и fake Redis
  startup/shutdown, same-process strict API; runtime/env/deploy/lint/type checks.

План: failing no-auth import, заменить owning settings dependency и три env
поля, адаптировать contracts. Runtime/helper/API validators не менять. Parent
owns docs/registry/hooks; reviewer not-requested, implementation done; verification pass (исполнитель).


Archive singleton заменён на runtime alias; Compose только archive16→13 без
трёх API auth keys, SITE_DATABASE_URL оставлен для отдельной задачи. Algorithm,
cron10min/functions/maxjobs/Redis semantics не менялись. Extra auth consumer в
ChatThreadRepository/models не обнаружен; Runtime/helper/API validators прежние.

Результаты var/audit/step103u-*.txt:

- RED:1failed16deselected2.43s ожидаемый BackendSettings auth gate(red.txt).
- Runtime/auth:19passed93.98s(settings.txt), включая fresh archive import/ORM,
  actual startup/shutdown с fake Redis и API strict после archive в том же процессе.
- Sanitized Compose archive:8passed23.07s(env.txt); ordinary deploy157passed,
  149deselected4.44s(deploy.txt).
- Parent archive-fakes/ARQ/API:108passed1warning9.86s(parent.txt).
- Scoped mypy:Success1source(mypy.txt); Ruff/format:Passed3Pythonfiles.

Actual streams не архивировались; dotenv отключён, application network guarded,
рабочие DB/provider и контейнеры не запускались. Storage semantics и full project
coverage/gate не проверялись. A08-02 partial: shared keys/DB roles отдельно.
Без ревизора/коммита/push/deploy/игровых изменений/рабочих данных. Parent scoped
hooks после READY, после отчёта остановка.

Приёмка ведущего 10.3u: source diff, startup/auth contracts и env tests прочитаны;
docs/registry обновлены. Scoped hooks 7 файлов Passed, включая YAML, Ruff/format,
Markdownlint, Bandit, pip-audit с прежними исключениями и detect-secrets
(step103u-hooks.txt). Зависимости, baseline и исключения не менялись.
Статус checked-awaiting-acceptance, reviewer not-requested. Full project gate
не запускался, operational rollout отложен, A08-02 partial. Без рабочих данных,
gameplay edits, commit/push/deploy; после отчёта остановка.

## Финальный инфраструктурный пакет — 22.10.2026

Запрос владельца: закончить весь оставшийся инфраструктурный план, затем перейти
к рифтам. Укрупнение заменяет прежнее ограничение одной мелкой задачей за заход.
Режим прежний: без независимого ревизора, коммита, push, deploy и рабочих данных.
Игровую логику не менять. Чат alpha/AG-05 сохраняют прежние явные отсрочки.

- [x] FIN-R1: проверить остаток A08-02 и завершить безопасные локальные изменения;
  права хранилищ/credentials готовить без применения к рабочим данным.
- [ ] FIN-R2: завершить локальные backup/restore/alert contracts A08-15;
  неизвестные production RPO/RTO/schedule/offsite не выдумывать.
- [x] FIN-R3: A07-12 Studio access и selected-source read-only enforcement.
- [x] FIN-R4: A08-14 canonical HTTPS email origins/proxy с проверками.
- [x] FIN-R5: свести актуальные статусы очереди, выполнить общие проверки,
  отделить verified local result от deferred operational rollout.

План: три непересекающихся исполнителя (A08-02, Studio, email); ведущий — backup/
alerts, интеграция и общие проверки. Общие docs/registry/progress редактирует
только ведущий. Reviewer not-requested; implementation/verification pending.

### FIN: локальная реализация и evidence

- FIN-R1 implementation done / verification pass в локальном scope: migrations
  используют DB/runtime settings без API auth, архиватор без site DB URL; allowlists
  backend-migrate11/site-migrate8/archive12. 55 env cases и24runtime/DB contracts
  Passed. Opt-in Mongo new-user provisioning проверен реальным disposable Mongo,
  CRUD/index разрешены, cross-DB/admin/duplicate user запрещены. Существующие
  пользователи не менялись; PG/Redis live grants unverified.
- FIN-R2 implementation done / verification pass для local evidence contract:
  recovery_check CLI32tests Passed, scoped mypy Passed;3restore drills Passed59.91s.
  Fixture validators Passed. Backup schedule/offsite/retention, согласованное
  cross-store recovery и доставка alerts остаются operational unverified.
- FIN-R3 implementation done / verification pass: Studio auth/Host/Origin,
  selected-source HTTP guard, SQL read-only transactions, Redis read facade.
  49Passed1opt-in skipped; отдельный PostgreSQL drill1Passed4.86s; mypy35files.
  STUDIO_ACCESS_TOKEN обязателен, отдельные read-only DB roles ещё не аттестованы.
- FIN-R4 implementation done / verification pass: canonical SITE_BASE_URL только
  HTTPS production/loopbackHTTPdebug, no request Host/proxy origin;33tests Passed,
  scoped mypy4sourcefiles Passed. Реальная почта/proxy rollout не выполнялись.
- FIN-R5 verification complete / partial overall: общий4493-test nonexternal suite
  завершён; scoped hooks и итоговая сверка выполнены. MkDocs build Passed12.97s (navigation warnings сохранены).

Результаты исполнителей: var/audit/final-isolation.md, final-studio.md, final-email.md.
Scope42files: var/audit/final-infrastructure-scope.json. Проверял ведущий и
исполнители в обычном режиме; независимый reviewer не запрашивался.

Операционный остаток собран в docs/ru/management/infrastructure-release-checklist.md:
применение allowlists/credentials/roles/ACL, backup policy и alerts, публикация
workflow/main и smoke. Это не новые локальные микрозадачи. Чат alpha и AG-05
сохраняют отдельную согласованную отсрочку; игровые изменения не включены.

### FIN: приёмка ведущего и границы закрытия

Ведущий прочитал settings split, migration entrypoints, source-scoped Studio
clients/auth middleware, canonical email helper и provisioning tool. Обновлены
README и проектная operational reference Studio (по project-skills-maintainer).
42-file scoped hooks: YAML, Ruff/format, Markdownlint, Bandit, pip-audit Passed.
Detect-secrets нашёл только invalid synthetic Basic-URL в негативном email-тесте;
inline pragma на одном литерале, targeted rerun Passed. Baseline, зависимости,
исключения и auth policy не ослаблялись. Diff whitespace Passed, index пуст.

Три игровых сбоя воспроизведены отдельно (final-gameplay-diagnosis.txt,3failed4.47s):
два inventory tests ожидают отсутствие metrics, тогда как HEAD уже инвалидирует
metrics.gear_score_version при смене items; golem_foundry есть в HEAD starter
registry, но его loot profile отсутствует. Inventory/session/catalog/profile/test
bodies не менялись инфраструктурным пакетом; единственная ранее накопленная
character configuration правка — import runtime_settings. Gameplay fixes не входят.

Локальные FIN-R1/R3/R4 подтверждены. FIN-R2 partial operational: готов checker и
restore contracts, но schedule/offsite/retention/реальная доставка alerts не могут
считаться закрытыми без серверного применения. Live grants/ACL FIN-R1 также
unverified. Не выдавать этот пакет за operational закрытие A08-02/A08-15.
Чат alpha, AG-05 и production workflow publication сохраняют прежние отсрочки.
Обязательные операции собраны одним release checklist, не требуют продолжения
микрозадач в текущей локальной серии. Следующая предметная работа — рифты.
Без commit/push/deploy, рабочих данных и новых игровых изменений.

Окончательный общий прогон:4490passed/3failed/316external-deselected/4warnings,
599.08s (final-suite.txt). Все3failures — отдельно доказанные прежние игровые
контракты выше, новых инфраструктурных failures нет. Без coverage: full project
sign-off и прохождение глобального coverage threshold не заявлены; AG-05 typing
по-прежнему отложен. MkDocs final11.75s Passed; новые operational страницы в nav.
Статус local checked-awaiting-acceptance / operational partial; reviewer not-requested.


## Общая независимая ревизия накопленного пакета — 22.10.2026

Запрос владельца: «Запускай общую независимую ревизию всего накопленного
инфраструктурного пакета, исправляй замечания и перепроверяй. Без коммита, push,
деплоя и изменения рабочих данных. Потом отчитайся, и перейдём к рифтам».

- [x] REV-R1: независимый новый ревизор проверяет весь накопленный infrastructure
  diff и связанные contracts по исходному плану; не только последний42file batch.
- [x] REV-R2: существенные замечания исправить с доказательной перепроверкой;
  gameplay/balance, реальные secrets/данные/production не менять.
- [x] REV-R3: claims сопоставить с независимыми результатами, отложенный operational
  scope явно отделить; записать финальный verdict и отчёт.

План: neutral requirements packet → fresh independent review read-only → fixes
и focused checks → targeted re-review + claims verification → общие hooks/отчёт.
Reviewer requested; implementation pending / verification pending.

### REV: первоначальное независимое заключение

Новый независимый ревизор зафиксировал verdict до получения claims:
var/audit/independent-infrastructure-initial.md. Changes required, два Medium/P2:

- IR-01 (GenerationAI durable result): apply_result изменяет ItemInstance/template
  до Mongo mark_done. При отказе Mongo catch сохраняет cooldown, worker commit
  сохраняет уже применённый предмет без durable output. Воспроизведено настоящими
  disposable PostgreSQL/Mongo: item generated/ready, task cooldown, output пуст.
  Требование: rollback/savepoint apply+completion до retry; partial apply failure
  тоже не должен сохранять эффекты. Простая перестановка вызовов недостаточна.
- IR-02 (CI executable gates): quality steps ci.yml/build-images.yml выставляют
  DEBUG=False/SECRET_KEY, но не внутренние service keys Backend/FrontendSettings.
  В чистом CI без dotenv настройки не импортируются. Требование: явные synthetic
  test service keys в workflow при сохранении строгой production validation.

Независимые начальные проверки:394focusedPassed; auth/WS/restore/Redis287Passed
7Skipped7harnessFailures, затем corrected sharedlogging harness46Passed.
Реальный IR01 reproducer1Passed означает воспроизведение дефекта, не исправление.
Sourcefreeze снят только для IR01/02 fixes; выполняют два исполнителя без общих
файлов. Claims C1–C9 переданы ревизору только после initialverdict.
IR01 implementation pending/verification pending; IR02 pending/pending.

### REV: дополнительное подтверждённое IR-03

IR-03 High/P1 — isolation fixture реальных site migration/auth тестов устарел
после DatabaseSettings split. BOOTSTRAP подменяет только config.settings, Alembic
и DB session читают config.database.database_settings. Безопасный independent
engine interception (без connection, dotenv disabled, synthetic inherited URL)
подтвердил: Alembic использует inherited URL вместо URL disposable PostgreSQL.
Opt-in migration/auth tests запрещено запускать до исправления и re-review.
Рабочие данные этим proof не читались и не менялись.

Разрешённый fix: updated owning database_settings fixture, early dotenv disable,
sanitized DB env и before-connect assertioneffectiveURL. Проверить все dependents
в auth/rotation tests; regression должен доказать отказ неправильному URL до I/O.
IR03 implementation pending/verification pending. Исполнитель IR02 также владеет
IR03 test harness, отдельный агент не запускается. Source production не меняется.

### REV: targeted re-review и второй цикл IR-01

IR01 savepoint независимо проверен:22Passed (исходный positive oracle+8realcases+
core). Но отдельный двухпопыточный real SQL/Mongo proof показал: после ambiguous
Mongo ack SQL rollback сохраняет item original/cooldown и Mongo result-1, следующий
claim снова вызывает provider и заменяет документ result-2/done. Сохранность сразу
после exception недостаточна для ручного разбора. Дополнение IR01 требует raw
output guard в claim_by_id/claim_next до новой попытки: nonempty/malformed output
сохраняется, задача становится terminal StoredResultNeedsReview, provider не
вызывается автоматически. Это второй fix cycle IR01, без automatic replay.

IR02 executor8CIcontracts/197deployPassed, IR03 executor9safeguardtestsPassed;
реальные site tests до независимой проверки не запускались. Ревизор повторил
прежний engine interception: disposableURL=True/inheritedsentinel=False, stopped
beforeconnection. Только после этого разрешил свой owned PostgreSQL migration/auth
прогон. Production code для IR03 не менялся, новый fixture блокирует чужие URL.
Claims C7/C8 подтверждены как исторические логи и unchanged-HEAD game contracts;
C9 сужен до действий текущей ревизии/фиксов, не исторического server attestation.

### REV: IR02/IR03 независимое закрытие

Ревизор закрыл IR02 strict-env/negative guard проверками. IR03: сначала независимый
enginecapture доказал disposableURL=True/inheritedsentinel=False без connection;
затем реальный owned PostgreSQL migration+auth rotation/concurrency/failure набор
14Passed103.67s. Только после guards запускались реальные адаптеры, рабочие DB
не использовались. IR02/IR03 implementation done / independent verification pass.

IR01 cycle2 raw-output guard SOURCESTABLE: formal12realcasesPassed; независимый
полный GenerationAI+original positive/2attempt oracles выполняются. Состояние
IR01 ещё pending final independent verification. Revised claims F1–F6 переданы
после initial/закрытия отдельных findings; originalverdict не переписывается.

### REV: окончательное независимое заключение

Ревизор: новый GPT-6 Astra, не участвовал в реализации; первоначальное заключение
зафиксировано до получения claims, initial/supplement не переписаны.
Final report: var/audit/independent-infrastructure-final.md.

| Finding | Исправление | Независимая перепроверка |
| --- | --- | --- |
| IR-01 Medium/P2 | SQL savepoint apply/completion/followups, rollback before retry; raw-output guard обоих claims, SQL-only StoredResultNeedsReview без новой попытки/перезаписи Mongo | Closed: original SQL/Mongo positive oracle, second-retry oracle и полный GenerationAI набор200Passed112.02s |
| IR-02 Medium/P2 | Synthetic service keys только в quality env двух workflow; строгие validators сохранены | Closed: exact YAML env imports/collection и negative production guards |
| IR-03 High/P1 | Owning DatabaseSettings fixture, sanitized env/no dotenv, registered disposable URL и guards перед engine connect | Closed: independent sentinelcapture и реальные owned PostgreSQL migration/auth14Passed103.67s |

Дополнительно независимо:136resolved-environment/import testsPassed18deselected;
32RedisJSON/architecture/stage testsPassed; CI+isolationguards17Passed16.05s.
Наборы пересекаются, числа не складывать как unique total. 200AI tests включают
два private independent positive oracles и реальные SQL/Mongo/Redis контракты;
внешний AI provider не вызывался. Parent13filehooks прочитаны ревизором: applicable
YAML/Ruff/format/Markdownlint/Bandit/pip-audit/detect-secrets/whitespacePassed.
Mypy изменённых2AI sourcesPassed; CI/test source RuffPassed. Не добавлены новые
blanket suppressions, baseline/security exceptions или testing auth bypass.

Final reviewer verdict: три findings CLOSED; новых actionable defects в reviewed
infrastructure scope не установлено. F1–F6 confirmed в явно ограниченном local/
observed смысле. R1/R3/R4/R6/R7/R8/R9 local pass, R2/R5/R10 partial из-за remote/
full quality-coverage/security limits, а не оставшегося подтверждённого дефекта.
Исторический4490passed/3gamefail прогон не объявляется новым final fullsuite.

Статус: reviewed-awaiting-acceptance, REV-R1/R2/R3 implementation done /
independent verification pass. Production/workingDB/secret rollout/roles/ACL,
backup schedule/offsite/retention/alert receipt и full quality/coverage gate не
аттестованы. Во время этой ревизии использованы только собственные disposable
fixtures; историческое состояние сервера из checkout доказать невозможно.
HEAD183246e5279a257c140c4a059a5b56d4c65dfefc сохранён; commit/push/deploy не делались.
Игровые три старых failures, чат alpha и AG-05 остаются отдельными отложенными
задачами. После отчёта переход к рифтам отдельным предметным заданием.
