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

Production deploy принимает один `image_ref` и выставляет layer images:

```text
DOCKER_IMAGE_SITE=ghcr.io/<repo>-site:<image_ref>
DOCKER_IMAGE_GAME=ghcr.io/<repo>-game:<image_ref>
DOCKER_IMAGE_CHAT=ghcr.io/<repo>-chat:<image_ref>
DOCKER_IMAGE_WORKER=ghcr.io/<repo>-worker:<image_ref>
DOCKER_IMAGE_TG_BOT=ghcr.io/<repo>-tg-bot:<image_ref>
DOCKER_IMAGE_NGINX=ghcr.io/<repo>-nginx:<image_ref>
```

Для production rollback использовать commit SHA или release tag. `latest` может существовать как удобный alias, но не должен быть единственным production target.

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
