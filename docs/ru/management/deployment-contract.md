# Контракт деплоя

## Цель

Production deploy разделен на независимые operational layers, чтобы сайт оставался доступным во время перезапуска или обслуживания игрового runtime.

Этот контракт фиксирует не только расположение файлов, но и допустимое поведение deploy-команд.

## Запись production env-файла

SSH deploy получает GitHub secret `ENV_FILE` как `ENV_FILE_CONTENT`. В каталоге
`/opt/turnbasedmmorpg/deploy` создаётся приватный временный файл (`umask 077`,
`mktemp`), в него записываются env и image refs. Только после успешной подготовки
он атомарно заменяет `.env` с правами `0600`, владельцем остаётся SSH deploy user.
Существующий symlink заменяется, его цель не перезаписывается. При ошибке
подготовки прежний `.env` сохраняется, временный файл удаляется через EXIT trap.
Содержимое файла не выводится. Compose запускается после замены.

Это контракт нового workflow, не подтверждение текущих прав на production host.
Он ограничивает чтение другими непривилегированными пользователями; root и сам
deploy user остаются в доверенной границе. GitHub secret и приватный `.env.prod`
из-за этого изменения обновлять не требуется.

## Операционная диагностика и аналитика

`/api/internal/{combat,scenario,exploration}/sessions` и
`/api/game/combat/analytics/*` требуют отдельный заголовок `X-Operator-Key`.
Backend получает `OPERATOR_READ_KEY` для чтения и независимый
`OPERATOR_WRITE_KEY` для backfill. Write key также разрешает чтение; read key
не разрешает `POST /api/game/combat/analytics/backfill`. Пустые, dev/default
ключи и совпадение с обычными site-service keys отклоняются. Совпадение
read/write ключей отключает write-доступ. Без настройки ключей эти маршруты
закрыты даже при прямом обращении к backend. Значения ключей задаются оператором
в окружении, не сохраняются в репозитории.

Те же права обязательны на `/api/internal/config`,
`/api/admin/generation-ai` и `/api/admin/combat-ai`: GET требует read-capability,
PATCH/DELETE/POST (включая reset, запуск/очистку симуляций и генерацию обложек)
требует write-capability. Gate находится на backend router и действует также
при прямом обращении, до работы с хранилищем или очередью.

Frontend admin callers получают явные серверные `BACKEND_OPERATOR_READ_KEY` и
`BACKEND_OPERATOR_WRITE_KEY`, соответствующие backend operator keys. Они не
подставляются из обычного site-service key, не приходят из браузерных форм и
не публикуются в HTML. Существующий `/admin` gate по superuser остаётся обязательным.
Пустые настройки оставляют privileged API закрытыми; реальные значения задаются
оператором отдельно. Backend `OPERATOR_*` и frontend `BACKEND_OPERATOR_*`
должны содержать одинаковые значения соответствующих read/write capabilities.

Для локальных операций Studio дополнительно допускается `LOCAL_OPERATOR_WRITE_KEY`.
У production source write key отсутствует; simulation/config clients запрещают
мутации выбранного удалённого источника до HTTP-запроса. Это не заменяет отдельную
задачу общего входа в Studio и read-only enforcement инфраструктурных клиентов.

При чтении диагностики Studio передаёт read key выбранного источника: `LOCAL_OPERATOR_READ_KEY`
или `PROD_OPERATOR_READ_KEY`. При переключении источника ключ другого источника
не используется. Обычный frontend service key не предоставляет диагностических
прав; site widgets не запрашивают операторские endpoints и показывают «—»
с пояснением о доступности диагностики в Studio.
Nginx по-прежнему запрещает internal/admin пути; проверка полномочий backend
действует независимо от proxy.

Списки сессий возвращают одну страницу (`limit=1..100`, по умолчанию 100),
принимают `cursor=0:0` и возвращают продолжение в `X-Next-Cursor`.
При продолжении сохранять тот же limit. Один запрос выполняет один SCAN и
не более limit чтений метаданных; пустая страница может иметь продолжение.
Это диагностический best-effort обход, не снимок и не точный счётчик всех
сессий: при изменении Redis keys возможны повторы/пропуски. Ответ детали боя
содержит только разрешённые operational поля, не произвольное содержимое meta.
Studio подписывает таблицы как ограниченную выборку и отмечает наличие
продолжения; автоматического полного сканирования из UI нет.

## Ownership Matrix

| Слой | Владеет | Миграции | Допустимый restart scope | Rollback target |
| --- | --- | --- | --- | --- |
| `infra` | Postgres, Redis, Nginx, certbot helper, networks, volumes | Нет прикладных миграций | Только infra-сервисы | Ручной rollback после отдельного плана |
| `site` | `frontend` / site-web, `frontend-play` / play surface, site static/generated assets mount | `site` schema через frontend Alembic | `site-migrate`, `frontend`, `frontend-play` | Предыдущий `site` image SHA |
| `game` | Backend/game API, chat/ws, ARQ workers, game runtime mounts | `game` и `chat` schemas через backend migration command | `backend-migrate`, `backend`, `chat`, workers | Предыдущие `game`, `chat`, `worker` image SHA |
| `tg-bot` | Telegram polling worker, Redis Stream news announcements | Нет прикладных миграций | `tg-bot` | Предыдущий `tg-bot` image SHA |

## Границы перезапуска

- `deploy site` не должен перезапускать `backend`, `chat` или workers.
- `deploy game` не должен перезапускать `frontend`.
- `deploy infra` не должен выполняться как побочный эффект site/game deploy.
- `deploy full` допустим только как осознанный full-stack rollout.
- Layer-specific deploy не должен использовать `--remove-orphans`, потому что соседние слои используют тот же Compose project name и могут быть ошибочно удалены как orphan-сервисы.

## Compose Files

Production deploy использует:

```text
deploy/compose.infra.yml
deploy/compose.site.yml
deploy/compose.game.yml
deploy/compose.tg-bot.yml
deploy/compose.prod.yml
```

`compose.prod.yml` является агрегатором для проверки или осознанного full-stack сценария и включает `infra`, `site`, `game` и `tg-bot`. Он не должен становиться обычной командой для site-only, game-only или tg-bot-only деплоя.

## Image Contract

Production deploy требует `build_run_id` успешного **Build Release Images** и
`image_ref`: полный commit SHA или version из manifest именно этого run.
`latest`, сокращённый SHA и произвольный tag не принимаются.

После Quality Gate и успешной публикации всех шести образов build workflow
сохраняет artifact `release-images-<run_attempt>` с `release-images.json`.
Manifest содержит repository, run ID/attempt, source SHA, version и digest каждого
образа из outputs `docker/build-push-action`. Публикация manifest при ошибке
любого build step не выполняется.

Первый job deploy обращается к authenticated GitHub Actions API с `actions: read`.
До любого SSH/SCP он проверяет repository и workflow identity, successful completed
run, успешные Quality Gate и Build and Push Images текущей попытки, origin и
SHA-256 архива manifest, совпадение manifest с run и выбранным `image_ref`.
Любая API/network ошибка, отсутствующий/просроченный artifact, неполный список
(более 100 jobs/artifacts) или несовпадение блокируют продолжение. Manifest
читается из ограниченного ZIP без извлечения файлов; API token не передаётся
на signed storage URL. Перед выдачей разрешения повторно проверяется run attempt.

В `.env` попадают только проверенные immutable references, например:

```text
DOCKER_IMAGE_SITE=ghcr.io/<repo>-site@sha256:<64 hex characters>
DOCKER_IMAGE_GAME=ghcr.io/<repo>-game@sha256:<64 hex characters>
DOCKER_IMAGE_CHAT=ghcr.io/<repo>-chat@sha256:<64 hex characters>
DOCKER_IMAGE_WORKER=ghcr.io/<repo>-worker@sha256:<64 hex characters>
DOCKER_IMAGE_TG_BOT=ghcr.io/<repo>-tg-bot@sha256:<64 hex characters>
DOCKER_IMAGE_NGINX=ghcr.io/<repo>-nginx@sha256:<64 hex characters>
```

Deploy configs checkout использует проверенный source SHA того же build,
а не текущий HEAD dispatch branch. Изменение GHCR tag после проверки не меняет
выбранные image digests. Rollback выбирает предыдущий успешный build run с
доступным manifest, а также его SHA/version. Старые builds без manifest не имеют
fallback; сначала нужен новый successful Build Release Images. Artifact хранится
90 дней (организационная retention policy может сократить срок). Для rerun
использовать **Re-run all jobs**: gate требует оба успешных jobs одной попытки.

Это связь результата quality/build с promotion, не криптографическая attestation
всей supply chain. Production ref/approval/concurrency policy описана ниже;
реальные настройки GitHub и доступность образов требуют отдельной проверки.
Hosted Actions и production этой локальной проверкой не подтверждаются.
Форматы API: [artifacts](https://docs.github.com/en/rest/actions/artifacts),
[workflow jobs](https://docs.github.com/en/rest/actions/workflow-jobs).

## Immutable Actions и внешние образы

Внешние `uses` в workflow закреплены полными commit SHA; комментарий сохраняет
исходный version tag. Литеральные `image` в Compose, Dockerfile `FROM` и внешний
Dockerfile frontend (`# syntax`) используют `tag@sha256:<digest>`. Digest относится
к multi-platform index: Linux amd64 и arm64 остаются доступны. Проектные
`DOCKER_IMAGE_*` по-прежнему получает gate успешной сборки, описанный выше.
В обоих Docker build jobs также закреплены Buildx `v0.38.0` и image BuildKit driver.
CI helper hadolint использует отдельный проверенный image digest.

Смена upstream tag теперь не обновляет эти ссылки автоматически. Для обновления
нужно сверить SHA с официальным GitHub repository (annotated tag разрешать до
commit), а image digest — с registry; проверить SHA-256 raw manifest/index и
поддерживаемые платформы, изменить pin и прогнать deploy-тесты и Compose config.
Новый pin не означает проверку отсутствия уязвимостей. Проверка
`tests/deploy/test_immutable_references.py` запрещает mutable ссылки и включена
в develop behavioral gate; full quality также собирает этот файл.

Граница проверки — объявленные Actions и container references. У закреплённых
appleboy Actions entrypoint скачивает версионированные `drone-ssh 1.8.2` и
`drone-scp 1.8.0` release assets без checksum. Buildx и setup Actions также могут
скачивать инструменты; hosted runner, apt repositories и PyPI build inputs этой
фиксацией не замораживаются. Это не полная транзитивная attestation и не доказательство
побитовой воспроизводимости сборки. Контракт Python sources описан ниже (A08-10).

Синтаксис и границы: [GitHub Actions pinning](https://docs.github.com/en/actions/reference/security/secure-use),
[Dockerfile frontend digest](https://docs.docker.com/build/buildkit/frontend/).

## Источники Python-зависимостей CI и Docker

CI и все шесть Python Dockerfile используют uv `0.11.19`, один manifest и
`uv.lock`. CI выполняет `uv sync --locked`; Docker — `uv export --locked`
с учётом объявленных project sources, без `--no-sources` и без `--frozen`.
Несогласованный manifest/lock блокирует установку/export; отсутствующий source
не заменяется молча опубликованным пакетом.

Текущий `codex-ai==0.2.4` и остальные внешние packages разрешены из published
PyPI sources, записанных в lock. После export Docker pip устанавливает
requirements с `--require-hashes`. Export сохраняет hashes, а package versions
и выбранный архив должны соответствовать lock. При неверном хеше установка
завершается ошибкой. Для проверки установленного wheel можно использовать
`pip install --report <report.json>` и сверить URL/`archive_info.hashes.sha256`
с wheel entries в lock.

Состав окружений намеренно различается: CI jobs включают dev/docs группы, а
Docker использует существующие `--no-dev --group ... --no-emit-project` flags
и прежние default runtime groups. Согласование sources не меняет библиотечные
версии и не перераспределяет runtime groups. Local project editable install
в CI и отсутствие project package в export — ожидаемое различие.

`tests/deploy/test_dependency_sources.py` проверяет согласованность инструмента,
locked export и hash checking. Он включён в develop behavioral gate. Это контракт
Python dependency resolution, не фиксация apt repositories, build-tool archives,
hosted runner и не полная воспроизводимость конечного production image.

Форматы: [uv locking/export](https://docs.astral.sh/uv/concepts/projects/sync/),
[pip hash checking](https://pip.pypa.io/en/stable/topics/secure-installs/),
[pip installation reports](https://pip.pypa.io/en/stable/reference/installation-report/).

## Production ref, подтверждение и serialization

`Deploy Production` запускают вручную из `main`. Проверка runtime context
требует `workflow_dispatch` и `refs/heads/main`. Verified image source SHA должен
быть текущим main или его предком: сравнение `<source_sha>...main` требует
`ahead`/`identical` и merge-base, равный source SHA. Поэтому rollback на ранее
проверенную main-сборку допускается, а develop/tag/divergent source — нет.

Порядок: artifact verifier → проверка production policy → job с
`environment: production` → повторная policy check после approval → SSH/SCP.
Environment обязан уже иметь непустое `required_reviewers` rule с валидными
User/Team reviewers и явной `prevent_self_review` policy. Отсутствие environment,
пустые rules, malformed ответ, 403/404 или network error завершают gate ошибкой.
Автоматически созданный environment без защиты не даёт обхода. Само подтверждение
job обеспечивает GitHub; helper проверяет конфигурацию, а не подменяет approval.
Значение self-review выводится без имён reviewers; требование второго оператора
этот commit не вводит.

После approval сначала checkout контрольного кода из dispatch commit; он повторно
проверяет main ancestry и environment rules. Только затем checkout verified source SHA
для передачи его `deploy/`. Старому rollback-релизу не требуется содержать новый helper.
SSH preflight теперь шаг того же protected job, поэтому второго approval нет.
Inputs `layer`, `build_run_id`, `image_ref` сохранены; layer дополнительно проверяется
до обращения к серверу.

Workflow использует один постоянный concurrency group `production` для всех
слоёв и refs, `cancel-in-progress: false`. Следующий запуск не прерывает активный.
Это не обещание FIFO: GitHub может заменить ожидающий pending run; внешние ручные
SSH-действия и другие workflows без этой группы блокировкой не охвачены.

### Настройка GitHub перед использованием

В repository Settings → Environments проверить `production`: required reviewers,
осознанный выбор self-review/admin-bypass policy и deployment branches только
`main`. Production credentials (`HOST`, `USERNAME`, `SSH_KEY`, `ENV_FILE`) хранить
в environment secrets и не дублировать без необходимости в repository secrets,
иначе сторонний workflow может иметь отдельный путь к тем же credentials.
Защиту main и права изменения workflow также администрирует владелец.
Это checklist для владельца, не утверждение о текущих remote settings.

Локально GitHub CLI не авторизован, поэтому реальные environment/branch rules
не прочитаны и не менялись. Проверки используют fixtures по API contract; живые
approval, concurrency и deployment не запускались. Деплой остаётся заблокированным,
если проверка требуемых rules не проходит; считать remote protections активными
только по наличию YAML нельзя.

Контракты платформы: [environments API](https://docs.github.com/en/rest/deployments/environments),
[approval и concurrency](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/control-deployments).

## Env и Secrets

При `DEBUG=False` backend и frontend отказываются запускаться с пустыми,
пробельными, `change-me-*` или `dev-*` ключами подписи и межсервисной авторизации.
На backend явно заданный primary internal key имеет приоритет; legacy key
используется только при отсутствии primary. Невалидный primary не обходится
через legacy fallback. В debug-режиме остаются локальные dev-настройки.

В локальных `docker-compose.yml`, `docker-compose.db.yml` и observability overlay
публикация внутренних сервисов ограничена `127.0.0.1`. Публичный Nginx на обоих
host-ах возвращает 404 для служебных API `/api/internal`, `/api/admin` и
Swagger/OpenAPI; кабинет `/admin`, публичный API и WebSocket-маршруты сохраняются.
Проверка конфигурации не является деплоем или разрешением перезапуска сервисов.

Deploy workflow получает production `.env` из GitHub secret `ENV_FILE` и записывает его на сервер перед запуском Compose.

Локальный приватный `.env.prod` служит источником этого secret: после изменения
capabilities нужно заменить содержимое `ENV_FILE` целиком. Изменение локального
файла само по себе не обновляет GitHub или уже запущенные процессы. `.env` и
`.env.prod` не коммитятся; `.env.prod.example` содержит только пустые поля.

Правила:

- secrets не хранить в репозитории;
- значения `.env` с символом `$` экранировать как `$$`, иначе Docker Compose применит interpolation;
- site/game deploy может читать общий `.env`, но не должен перезапускать чужой слой из-за изменения переменной без явного full/infra плана.
- `BOOTSTRAP_CONTENT_MATERIALIZATION_ENABLED=True` разрешает backend startup синхронизировать статический/world/rift generated content без внешних AI-вызовов;
- `BOOTSTRAP_AI_GENERATION_ENABLED=False` является production default: backend startup не должен ставить AI generation tasks автоматически, даже если materialization создала локальные generated rows.

## Runtime Boundary

- Код из `src/` не должен зависеть от `deploy/`.
- `deploy/` не должен импортировать gameplay/runtime internals напрямую.
- Взаимодействие deploy layer с runtime происходит через published operational contracts: image tags, env vars, entrypoints, health endpoints и migration commands.

## Service Boundary

Production runtime разделен на site и game layers:

- `frontend` / site-web владеет public site, auth/account, cabinet, library,
  site templates/static и `site` schema migrations.
- `frontend-play` запускает тот же site image с `FRONTEND_SURFACE=play` и
  обслуживает gameplay entry/lobby под отдельным public host.
- `backend` / game владеет gameplay APIs, runtime state, workers, game catalog,
  chat/ws и `game` + `chat` schema migrations.
- Site обращается к game backend через typed HTTP clients и internal service key.
- Backend не рендерит public site.
- Site должен оставаться доступным при restart/maintenance game runtime.
- Nginx обязан маршрутизировать основной public domain на `frontend`, а play
  domain на `frontend-play`; оба host-а проксируют `/api/`, `/chat/`,
  `/ws/chat` и `/ws/realtime` в game/chat слой.
- Generated asset URLs остаются site-facing контрактом `/static/generated-assets/<storage_key>`.
  S3/Object Storage является backend storage implementation detail; прямые provider URLs не являются
  каноническими значениями для статей, монстров или будущих generated assets.

## Проверки перед деплоем

```powershell
docker compose -f deploy/compose.infra.yml config
docker compose -f deploy/compose.site.yml config
docker compose -f deploy/compose.game.yml config
docker compose -f deploy/compose.tg-bot.yml config
docker compose -f deploy/compose.prod.yml config
```

Для certbot profile:

```powershell
docker compose -f deploy/compose.infra.yml config --services
docker compose -f deploy/compose.infra.yml --profile manual config --services
```

`certbot` должен отсутствовать в обычном списке сервисов и появляться только с `--profile manual`.


## Сетевая граница публичного proxy (A08-02)

Production Compose отделяет HTTP edge от сети приложений и хранилищ.
Nginx и certbot не должны иметь общей Docker network с PostgreSQL, Redis или
MongoDB. При этом nginx должен видеть все HTTP upstream: `frontend`,
`frontend-play`, `backend`, `chat`. Эти HTTP-сервисы подключаются к обеим сетям;
workers и migrations не требуют доступа из edge.

Это ограничивает прямую сетевую достижимость хранилищ из proxy. HTTP upstream
остаются доверенной границей и имеют доступ к данным; такая схема не защищает
от компрометации backend, SSRF с его правами или обхода авторизации API.
Разделение `env_file`, DB roles, Redis ACL и секретов остаётся отдельной работой.
Сети сохраняют исходящий доступ: блокировка provider/S3/Telegram не является
частью этого изменения.

Изменение файлов не меняет сеть уже работающих контейнеров. При будущем
разрешённом rollout требуется пересоздание затронутых контейнеров и проверка
фактических network attachments; простой restart не доказывает изоляцию.
Существующие volumes и данные не переименовываются. Этот шаг не запускает
production deploy и не отключает текущие подключения вручную.


Имена сетей: `tbmmorpg-edge` — proxy/HTTP upstream, `tbmmorpg-network` —
приложения/хранилища. Certbot initial issue, renewal helper и systemd unit
используют edge. Volume init jobs работают с `network_mode: none`.
Старое имя data-сети и существующие volume names сохраняются. Административные
инструменты остаются в data-сети и требуют отдельного контроля доступа.


## Allowlist окружения Telegram bot (A08-02)

Production `compose.tg-bot.yml` передаёт только явные ключи `environment`,
не весь общий `env_file`. В bot не должны попадать PostgreSQL/Mongo root URLs,
SMTP, AI-provider и S3 credentials или дополнительные operator-ключи других сервисов.
Настройки bot/auth/Redis/API и предусмотренные параметры логирования/поведения
перечисляются явно по контракту `BotSettings`.

Общий deployment `.env` на хосте остаётся входом интерполяции Compose: workflow
создаёт его в каталоге deploy с прежними ограничениями доступа. Удаление
service `env_file` не означает удаление этого файла, разделение GitHub secrets
или ротацию значений. При ручном запуске с другим файлом требуется штатный
`docker compose --env-file <файл> ...`, иначе значения не станут входом
интерполяции только от установки `DEPLOY_ENV_FILE`.

Изменение применяется при будущем пересоздании bot, текущие контейнеры не
трогаются. Остальные сервисы пока сохраняют прежнюю передачу env; общий
`SECRET_KEY`, Redis credentials и backend API credentials бота остаются
самостоятельными границами для дальнейшего разделения/прав. Это не полное
закрытие A08-02 и не подтверждение текущего окружения на сервере.


## Allowlist окружения chat-archive-worker (A08-02)

Production архиватор чата получает 12 явных настроек вместо общего
`env_file`. Подключения PostgreSQL/Redis/Mongo и поддерживаемые настройки
логирования, SQL echo и Mongo timeout сохраняются. AI-, S3-, SMTP-, Telegram-
и operator-секреты не должны попадать в окружение этого worker.

Архиватор использует существующие RuntimeSettings без auth-полей.
`SECRET_KEY`, `FRONTEND_INTERNAL_SERVICE_KEY` и `SITE_TO_GAME_SERVICE_KEY`
не передаются и не требуются; строгая auth-проверка API сохраняется. Алгоритм
архивирования, cron, функции и max_jobs не меняются. Проверки используют
синтетическое окружение и startup/shutdown с подставным Redis без рабочих данных.
Ротация credentials, роли БД и Redis ACL остаются отдельными задачами.
SITE_DATABASE_URL исключён: архиватор использует game SQL и не нуждается в site DB.

Исходный deployment `.env` остаётся входом Compose interpolation. При будущем
rollout нужно пересоздать только затронутый worker и проверить его эффективное
окружение; в текущей задаче контейнеры/credentials/рабочие данные не меняются.


## Allowlist окружения site-migrate (A08-02)

Production `site-migrate` получает отдельный явный список вместо общего env-файла.
Alembic использует site `DATABASE_URL`; игровые DB/Redis подключения и backend
API URL этому entrypoint не требуются. Они не передаются migration-контейнеру,
как и AI/S3/SMTP/Telegram/operator credentials.

Сохраняются site URL, production DEBUG, поддерживаемые параметры SQL echo и
логирования: всего 8 DB/logging настроек. Alembic использует DatabaseSettings
без SECRET_KEY/BACKEND_INTERNAL_SERVICE_KEY. FrontendSettings наследует общие
DB поля и сохраняет строгую auth-проверку HTTP runtime. Роли БД и смена ключей
требуют отдельного operational применения.

Это изменение доставки окружения при будущем запуске migration-контейнера.
Текущие базы, схема и миграции в этой задаче не изменяются; SQL может генерироваться
в offline-проверке без исполнения. Остальные site/play/API сервисы пока требуют
собственных allowlists; host deployment `.env` остаётся источником интерполяции.


## Allowlist окружения backend-migrate (A08-02)

`backend-migrate` получает явный список для entrypoint `upgrade` и
`ensure-mongo-indexes`. Ему нужны игровые SQL и Mongo подключения, production
валидация и поддерживаемые настройки логирования/SQL echo/Mongo timeout.
Site DB, Redis и AI/S3/SMTP/Telegram/operator-секреты этому migration-контейнеру
не передаются: цепочка миграций и bootstrap индексов их не использует.

Migration entrypoints используют RuntimeSettings: 11 настроек без API auth-ключей.
BackendSettings разрешается только для HTTP runserver и сохраняет production
auth validation. Это не ротация ключей и не least-privilege DB roles. Command,
образы, volumes и код миграций сохраняются.
Изменение окружения применяется при будущем запуске нового migration-контейнера;
рабочие SQL/Mongo базы и их индексы в этой задаче не меняются.

Проверки на синтетическом окружении подтверждают сборку настроек/импортов и,
где поддерживается, offline SQL. Они не заменяют online migration и проверку
реальных grants. Прочие API/worker сервисы требуют отдельного разделения env.


## Allowlist окружения generation-ai-worker (A08-02)

`generation-ai-worker` использует явный список переменных вместо общего
`env_file`. Его Gemini credentials/model сохраняются: это рабочий provider
для `items.text`. SQL/Mongo/Redis, логирование и используемые shared-worker
настройки передаются явно через runtime-конфигурацию без API auth-полей.
Включены `DEFAULT_SYMBIOTE_NAME` и `GAME_REFRESH_TOKEN_EXPIRE_MINUTES`, которые
читаются моделью CharacterSymbiote и менеджером блокировки общего контейнера.
Список содержит 19 настроек; отсутствие значения сохраняет прежний default,
явно пустое значение передаётся валидатору без подмены default.
Чужие AI-provider, S3/SMTP/Telegram/operator/root DB credentials не должны
попадать в окружение worker.

Это ограничение доставки секретов, а не смена провайдера или отключение
генерации. Отсутствующий/пустой Gemini key сохраняет прежнее поведение AIService;
проверки не делают реальных provider-запросов и не запускают задачи генерации.
`SECRET_KEY`, `FRONTEND_INTERNAL_SERVICE_KEY` и `SITE_TO_GAME_SERVICE_KEY`
этому worker не передаются. Общие инфраструктурные потребители читают отдельные
runtime settings; BackendSettings сохраняет строгий production auth-validator.
GenerationAI, system-worker, combat-worker и combat-ai-simulation-worker передают
runtime settings явно; остальные ARQ entrypoints сохраняют проверку
BackendSettings при настройке logging. Пропуска проверки через env-флаг нет.
Права БД и authkeys остальных сервисов остаются отдельной работой. Gemini,
очередь, cron, startup-операции, образы и volume mounts сохраняются.

Host `.env` остаётся источником Compose interpolation; применение требует
будущего пересоздания worker. Работающие контейнеры, данные, секреты на хосте
или в GitHub не изменяются.

## Allowlist окружения system-worker (A08-02)

`system-worker` получает 17 явных runtime-настроек вместо общего `env_file`.
Сохраняются game SQL, MongoDB, Redis, логирование, SQL echo, Mongo timeout,
game stream и runtime policy path. `SECRET_KEY`, `FRONTEND_INTERNAL_SERVICE_KEY`
и `SITE_TO_GAME_SERVICE_KEY` не передаются и не требуются при импорте или startup.
Entrypoint явно использует RuntimeSettings; строгая auth-проверка API сохраняется.
`DEFAULT_SYMBIOTE_NAME` и `GAME_REFRESH_TOKEN_EXPIRE_MINUTES` передаются явно:
их используют зарегистрированные задачи и создаваемые общим контейнером managers.
Настройки игровой логики и их значения этим изменением не меняются.

Site DB, AI-provider, S3/SMTP/Telegram/operator/root credentials не передаются.
Права хранилищ и authkeys остальных сервисов остаются отдельной работой.
Host `.env` остаётся источником Compose interpolation. Применение требует будущего
пересоздания worker; работающие сервисы, данные и расписание задач не изменяются.
Проверки используют синтетические настройки и startup/shutdown с подставными
адаптерами; реальные worker, сетевые запросы и подключения к БД не запускаются.

## Allowlist окружения combat-worker (A08-02)

`combat-worker` получает 17 явных runtime-настроек вместо общего `env_file`.
Game SQL, MongoDB и Redis сохранены. `SECRET_KEY`, `FRONTEND_INTERNAL_SERVICE_KEY`
и `SITE_TO_GAME_SERVICE_KEY` больше не передаются: entrypoint явно использует
RuntimeSettings, а строгая auth-проверка API сохраняется. Сохраняются logging, SQL echo,
Mongo timeout, game streams, `COMBAT_AI_POLICY_PATH`, `DEFAULT_SYMBIOTE_NAME`
и `GAME_REFRESH_TOKEN_EXPIRE_MINUTES`. Значения и поведение игровых настроек
не меняются; боевой AI использует локальную policy, а не ключи LLM-провайдеров.

Site DB и AI-provider/S3/SMTP/Telegram/operator/root credentials не передаются.
Authkeys остальных сервисов и роли хранилищ остаются отдельной работой. Очередь,
задачи, параллелизм, образы, сеть и игровая логика сохраняются. Применение окружения требует будущего пересоздания
контейнера; работающие сервисы и данные этим шагом не меняются.

## Allowlist окружения combat-ai-simulation-worker (A08-02)

`combat-ai-simulation-worker` получает 17 явных runtime-настроек вместо общего
`env_file`. `SECRET_KEY`, `FRONTEND_INTERNAL_SERVICE_KEY` и
`SITE_TO_GAME_SERVICE_KEY` не передаются и не требуются: entrypoint явно использует
RuntimeSettings. Строгая auth-проверка API сохраняется. Сохраняются game
SQL/MongoDB/Redis, logging/echo/Mongo timeout, game streams, local policy path и общие
переопределения symbiote name/lock TTL. Site DB и ключи внешних AI-провайдеров,
S3/SMTP/Telegram/operator/root в окружение не передаются.

Профиль `combat-ai-simulation`, очередь, четыре задачи, таймауты и ограничения
повторных попыток/параллелизма сохраняются. Код симуляции и обучения не меняется.
Тесты проверяют конфигурацию, импорт и startup/shutdown с подставными адаптерами.
Симуляции, обучение, реальные сетевые подключения и рабочие БД не запускаются.
Auth остальных сервисов и роли хранилищ
остаются отдельной работой; применение требует будущего пересоздания контейнера.

## Allowlist окружения chat (A08-02)

`chat` получает явный список настроек вместо общего `env_file`. Сохраняются
game SQL/MongoDB/Redis и обязательные shared-validator authkeys, настройки JWT
для REST и realtime, разрешённые Origin и ping-интервалы, Streams consumer group/
worker name/pending recovery, буфер сообщений, logging и используемые общие
настройки хранилищ. Переопределения должны сохранять прежнюю обработку пустых
значений; CHAT_STREAM_CONSUMER_GROUP/CHAT_WORKER_NAME остаются Compose aliases.
`REALTIME_ALLOWED_ORIGINS` передаётся JSON-массивом: текущий settings loader
отклоняет CSV и пустую строку. Этот контракт здесь не изменяется.

Site DB и посторонние AI/S3/SMTP/Telegram/operator/root credentials исключаются
из доставки окружения после проверки цепочки потребителей. REST/WS routes,
авторизация, сообщения и протоколы не меняются. Тесты используют синтетическое
окружение и импорт приложения без lifespan, рабочих БД и сетевых подключений.
Shared auth и роли хранилищ остаются отдельными задачами; применение окружения
требует будущего пересоздания контейнера.

## Allowlist окружения backend (A08-02)

`backend` использует явный список переменных вместо общего `env_file`.
Сохраняются game SQL/MongoDB/Redis, JWT и межсервисная авторизация, operator/
monster catalog keys, Gemini key/model для существующего AIContainer, параметры
Streams, logging и используемые world/runtime overrides. Наличие административных
ключей в этом сервисе необходимо его API; их значения и права здесь не меняются.

Site DB и посторонние SMTP/Telegram/root DB/provider/S3 credentials не передаются.
После отключения генерации изображений у S3 factory нет runtime callers в backend;
Gemini остаётся используемой зависимостью и сохраняется явно.
Host `.env` остаётся источником Compose interpolation; применение окружения требует
будущего пересоздания контейнера. Source, игровая логика, endpoints и startup
не меняются; проверки используют синтетические настройки без lifespan/БД/сети.
Общие ключи авторизации и роли хранилищ остаются отдельной частью A08-02.

## Allowlist окружения frontend site (A08-02)

Сервис `frontend` с `FRONTEND_SURFACE=site` получает явный список настроек вместо
общего `env_file`. Сохраняются site SQL, Redis для публикации событий новостей,
JWT/cookie/CSRF, backend API credentials (включая operator keys кабинета), SMTP,
параметры URL, SEO/release и используемые пути/логирование.

S3 credentials сохраняются: frontend обслуживает generated assets через S3 reader,
в отличие от backend после отключения заказа изображений. Это не новые ключи и
не ротация. Game SQL, MongoDB, AI-provider, Telegram и root DB credentials в site
окружение не передаются. `frontend-play` в этом заходе не меняется.

Тесты используют синтетические credentials и импорт настоящего site-приложения
без lifespan, писем, рабочих БД и сетевых запросов. UI, маршруты, auth и gameplay
не меняются. Применение требует будущего пересоздания контейнера; shared keys и
права хранилищ остаются отдельной работой.

## Allowlist окружения frontend-play (A08-02)

`frontend-play` получает явный список переменных вместо общего `env_file`.
Site SQL сохраняется для общего слоя аутентификации/refresh; игровые данные
по-прежнему запрашиваются через backend API. Передаются нужные JWT/cookie/CSRF,
game cookie flags, realtime URL, backend service key, renderer/release/SEO/path
и S3 generated-assets настройки, включая существующие runtime overrides.

Redis URL/credentials, game SQL, MongoDB, SMTP, backend operator keys, AI-provider,
Telegram и root DB credentials play-сервису не передаются: их потребителей в
зарегистрированной play-цепочке нет. Импорт site-модулей общим приложением сам
по себе не делает site-only обработчики активными в play surface.

Тесты импортируют настоящую play surface с синтетическими credentials, root+src
PYTHONPATH и временным assets-каталогом; без lifespan, рабочих БД, писем и сетевых
запросов. Source/gameplay, протоколы, маршруты и настройки работающих контейнеров
не меняются. Применение требует будущего пересоздания; shared keys и роли БД
остаются отдельной частью A08-02.


## Завершение локального инфраструктурного пакета

Backend/site migration entrypoints используют DB/runtime configuration без API
signing/session/internal keys. Backend-migrate получает 11 настроек, site-migrate
8 DB/logging настроек; HTTP API по-прежнему проверяют свои auth credentials.
Chat-archive-worker больше не получает site DB URL. Это не изменение игровых
алгоритмов или схемы данных.

Studio требует отдельный `STUDIO_ACCESS_TOKEN`: username HTTP Basic — `studio`,
пароль — значение этой переменной. Без токена сервер отвечает 503, без правильной
авторизации 401. Используйте loopback/SSH tunnel или HTTPS, разрешённый Host и
same-origin формы. Production source не допускает мутации; локальные compute
операции ограничены явным списком. Клиенты SQL используют read-only transactions,
Redis предоставляет читающие команды, HTTP ограничен выбранным источником.
Эти ограничения не заменяют отдельные read-only credentials хранилищ.

Почтовые ссылки используют только проверенный `SITE_BASE_URL`. Для production
при включённом email это HTTPS origin без userinfo/path/query/fragment. Host и
forwarded headers запроса не выбирают адрес ссылки. В debug разрешён локальный
HTTP; пустое значение использует стабильный localhost:8000.

Перед выпуском выполнить единый
[операционный список](infrastructure-release-checklist.md). Не установлены
production backup/alerts, не переключены существующие DB roles/Redis ACL и не
применены новые allowlists к работающим контейнерам.


## Чистое окружение CI и изоляция проверок миграций

Quality steps используют явные синтетические signing/internal service keys при
DEBUG=False. Эти значения нужны только для импорта строгих настроек и контрактных
тестов; они не являются production credentials и не меняют validators. Проверки
читают env непосредственно из обоих workflow и отдельно проверяют отказ без keys.

Opt-in site migration/auth tests разрешают только зарегистрированный disposable
loopback PostgreSQL URL своего fixture. Дочерние процессы не читают dotenv и не
наследуют database overrides; перед SQLAlchemy connect проверяется owning
DatabaseSettings URL. Изменение settings owner требует обновления этого harness,
а не подмены устаревшего config.settings. Рабочие базы для этих тестов запрещены.
