# Последовательное исправление технических замечаний

Дата начала: 19.10.2026. Основание: аудиты 10 и 11, сверка текущего кода.

## Порядок работы

- Работать в текущей ветке, без создания отдельной ветки.
- За один шаг исправлять только одну задачу ниже, проверять и коммитить.
- После отчёта остановиться и ждать команды владельца на следующий шаг.
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
| 5 | Источники зависимостей, develop behavioral gate, artifact-to-deploy gate и права env-файла | A06-05/06/09/12, A08-09/10/11/12 | 5.1 A08-12, 5.2 A06-12, 5.3 A06-05, 5.4 A06-06, 5.5 A06-09 и 5.6 A08-09 и 5.7 A08-10 исправлены; A08-11 ждёт команды |
| 6 | Восстановление Streams pending с доказанной идемпотентностью эффектов | A05-05 | Ждёт команды |
| 7 | Надёжное принятие и восстановление GenerationAI; срок жизни SQL-транзакций | A04-11/12/13/18, A05-07/08, A09-09 | Ждёт команды; перед реализацией разделить |
| 8 | Производительность архива чата, backpressure, Mongo projection, предел истории вкладки | A09-03/04/08/11 | Ждёт команды; перед реализацией разделить |
| 9 | Адресная типизация и SQL/Redis/Streams/HTTP contract tests | AG-05, A06-03/07/08/11 | Ждёт команды |
| 10 | Проверяемое восстановление/alerts, service isolation, Studio access/read-only | A08-02/15, A07-12 | Ждёт команды; перед реализацией разделить |
| 11 | Canonical HTTPS origin ссылок подтверждения почты | A08-14 | Ждёт команды; последствия через proxy ещё не воспроизведены |

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
