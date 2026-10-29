# CI/CD и слой управления деплоем

## Цель

Разделить эксплуатацию проекта на независимые слои, чтобы после сборки образов можно было перезапускать сайт, игру и инфраструктуру отдельно.

Главная цель: сайт должен оставаться живым, даже если игровой backend, workers или chat/ws перезапускаются.

Operational contract для границ ответственности и перезапуска описан в [контракте деплоя](deployment-contract.md).

## Слои

Production compose нужно вести к трем слоям:

```text
infra
  postgres
  redis
  networks
  volumes
  reverse proxy, если он нужен

site
  frontend/site
  site migrations/job

game
  backend/game api
  chat/ws
  arq workers
  game/chat migrations/job
```

Локально можно временно оставить один удобный `deploy/docker-compose.yml`. Разделение локального запуска можно делать позже, когда production split станет стабильным.

## Чат

Chat/ws сервис не должен подниматься только в момент логина персонажа.

Правильная модель:

```text
chat/ws process запущен вместе с game runtime
browser websocket подключается только когда пользователь вошел в игру/персонажа
```

Если игра на maintenance, site показывает недоступность игровых поверхностей, но site auth, public pages, cabinet и library продолжают работать.

## CI

На push и pull request проверяется весь репозиторий:

```text
lint
frontend tests
backend tests
shared tests
docs build
image build
```

Причина: код лежит в одном repository, shared contracts общие, frontend и backend могут ломать друг друга через DTO, tokens, headers и API clients.

## Versioned Images

Сборка образов должна быть привязана к версии и commit SHA.

Рекомендуемые теги:

```text
registry/turnbasedmmorpg-site:<version>
registry/turnbasedmmorpg-site:<git-sha>

registry/turnbasedmmorpg-game:<version>
registry/turnbasedmmorpg-game:<git-sha>

registry/turnbasedmmorpg-chat:<version>
registry/turnbasedmmorpg-chat:<git-sha>

registry/turnbasedmmorpg-worker:<version>
registry/turnbasedmmorpg-worker:<git-sha>
```

`latest` можно публиковать как удобный alias, но production deploy не должен зависеть только от `latest`.

Источник версии:

```text
git tag vX.Y.Z
или version из pyproject.toml для dev/pre-release сборок
```

Для production предпочтительнее release tag. Commit SHA нужен для точного rollback.

## Документация

Сборка документации является частью CI перед публикацией образов.

Минимальная цель:

```powershell
uv run mkdocs build --clean
```

Если документация не собирается, release image не должен считаться готовым.

## CD

После merge в `main` pipeline должен:

```text
1. прогнать проверки всего кода;
2. собрать документацию;
3. собрать immutable images;
4. запушить images в registry;
5. остановиться на manual deploy gate.
```

Production deploy запускается вручную. Нужны отдельные команды/джобы:

```text
deploy infra
deploy site
deploy game
deploy full
```

`deploy site` не должен перезапускать game api, chat/ws и workers.

`deploy game` не должен перезапускать site, кроме случаев явного изменения reverse proxy или общего env контракта.

## Compose Files

Целевая production форма:

```text
deploy/compose.infra.yml
deploy/compose.site.yml
deploy/compose.game.yml
deploy/compose.tg-bot.yml
deploy/compose.prod.yml        # optional aggregator
deploy/compose.local.yml       # optional local override later
```

Примеры команд:

```powershell
docker compose -f deploy/compose.infra.yml up -d
docker compose -f deploy/compose.site.yml up -d --pull always
docker compose -f deploy/compose.game.yml up -d --pull always
docker compose -f deploy/compose.tg-bot.yml up -d --pull always
```

Перед принятием compose changes нужно проверять:

```powershell
docker compose -f deploy/compose.infra.yml config
docker compose -f deploy/compose.site.yml config
docker compose -f deploy/compose.game.yml config
docker compose -f deploy/compose.tg-bot.yml config
```

## Management Layer

Под management layer здесь понимается не runtime module, а эксплуатационный слой проекта:

```text
release version
image build
image registry
compose layer selection
manual deployment gate
rollback target
docs build
```

Этот слой должен быть описан в документации и CI/CD, но не должен протекать в gameplay code.

## Rollback

Rollback должен быть возможен по commit SHA:

```text
site -> предыдущий site image sha
game -> предыдущий game/chat/worker image sha
infra -> только ручной rollback после отдельного плана
```

Game rollback требует осторожности из-за Redis sessions, workers и миграций. Для game deploy лучше иметь manual maintenance mode на site.

## Текущее состояние

Production split уже вынесен в отдельные compose-файлы:

```text
deploy/compose.infra.yml
deploy/compose.site.yml
deploy/compose.game.yml
deploy/compose.tg-bot.yml
deploy/compose.prod.yml
```

CI уже собирает документацию и проверяет Docker build. Release images собираются отдельным workflow, а production deploy запускается вручную через layer-specific workflow.

Следующий практический шаг перед реальным production rollout: проверить на сервере layer-specific деплой и подтвердить, что `deploy site` не трогает game services, а `deploy game` не трогает site service.

## Telegram: уведомления команды разработки

Существующий `tg-bot` принимает GitHub webhook через `POST https://thesealedworld.com/webhooks/github`.
На игровом поддомене этот путь возвращает 404.
Внутренний порт бота — 8091; compose не публикует его на хосте.
Отдельный бот и периодический опрос GitHub не нужны.

Интеграция выключена по умолчанию.
Для включения добавьте переменные из `.env.prod.example` в GitHub Actions secret `ENV_FILE`:

| Переменная | Значение |
| --- | --- |
| `GITHUB_WEBHOOK_ENABLED` | `True` |
| `GITHUB_WEBHOOK_SECRET` | Отдельный случайный секрет webhook |
| `GITHUB_WEBHOOK_REPOSITORIES` | `CodexDLC/thesealedworld`; несколько репозиториев через запятую |
| `GITHUB_WEBHOOK_BRANCHES` | `develop,main`; точные имена веток через запятую |
| `TELEGRAM_DEV_CHAT_ID` | `-1004387822347` |

Workflow `Deploy Production` при каждом запуске перезаписывает серверный `deploy/.env` содержимым Actions secret `ENV_FILE`.
Изменения только на сервере будут потеряны при следующем запуске workflow.
Редактируйте `ENV_FILE` через защищённые настройки GitHub; сохраните существующие переменные.
Не передавайте секрет через чат или командную строку.
Пустой секрет, выключенный Redis или пустой список разрешений блокируют запуск включённой интеграции.
Настройки новостного канала `TELEGRAM_CHANNEL_ID` сохраняют прежнее назначение.
Закрытая группа разработки исключена из публичной community feed независимо от включения webhook.

При первом включении обновите образ `tg-bot` и ingress-конфигурацию nginx из этой версии.
Конфигурация nginx включена в его Docker-образ и входит в слой `infra`.
Для адресного обновления nginx используйте серверные команды из каталога `deploy` с актуальной конфигурацией:

```sh
docker compose -f compose.infra.yml pull nginx
docker compose -f compose.infra.yml up -d --no-deps nginx
```

Сначала задайте `DOCKER_IMAGE_NGINX` из успешно завершённой сборки этого изменения.
Workflow `Deploy Production` с `layer=infra` обновляет весь infra-слой; это не nginx-only запуск.
Перезапуск остальных сервисов проекта не требуется.
После настройки ingress последующие изменения бота можно выкатывать отдельно через `Deploy Production`, `layer=tg-bot`.
Передайте `image_ref` опубликованного образа из успешного workflow `Build Release Images`.
Этот build workflow собирает `tg-bot` и nginx после Quality Gate.
Сам deploy workflow не проверяет статус сборки для переданного `image_ref`.
Запускайте deploy workflow с актуальной ветки `main`: deploy-конфигурация берётся из checkout выбранной ветки.
Поле `image_ref` меняет теги образов, а не checkout конфигурации.
При самостоятельном изменении внутреннего порта синхронно измените upstream nginx.
Эта инструкция описывает процедуру; её наличие не подтверждает выполненный деплой.

Добавьте repository webhook в GitHub Settings → Webhooks:

1. Укажите URL `https://thesealedworld.com/webhooks/github`.
2. Выберите Content type `application/json`.
3. Укажите тот же секрет в поле Secret.
4. Оставьте проверку SSL включённой.
5. Выберите события Pushes, Pull requests, Check runs, Workflow runs и Deployment statuses.
6. Проверьте успешный Ping в Recent Deliveries после запуска сервисов.

Бот должен состоять в указанной forum-группе и иметь право отправлять сообщения в открытые темы.
Настройки тем задают явные адреса; содержимое обычных сообщений не классифицируется автоматически:

| Назначение | ID темы | Автоматическая доставка |
| --- | --- | --- |
| Задачи и решения | 3 | Нет |
| Геймдизайн | 5 | Нет |
| Лор и мир | 7 | Нет |
| Графика | 9 | Нет |
| Баги | 12 | Нет |
| GitHub | 14 | Push и жизненный цикл PR |
| Деплой | 16 | Завершённые check/workflow и итоговые статусы deployment |

Push принимается только для `refs/heads/<разрешённая-ветка>`; удаление веток и теги пропускаются.
PR фильтруется по целевой ветке и репозиторию.
События PR `opened`, `reopened`, `synchronize`, `closed`, `edited`, `ready_for_review`, `converted_to_draft` обновляют карточку своего PR.
Ключ карточки включает группу, тему, репозиторий и номер PR.
Старые `updated_at` пропускаются; состояние `merged` не откатывается задержанным событием.
При одинаковом `updated_at` немерженные события обрабатываются в порядке получения.
Push всегда создаёт отдельное сообщение.

Check/workflow уведомления требуют `completed`, разрешённую head-ветку и итог `success`, `failure`, `timed_out`, `action_required`, `cancelled` или `startup_failure`.
Deployment уведомления требуют разрешённую branch-ref и статус `success`, `failure` или `error`.
SHA-only deployment refs пропускаются: payload не доказывает принадлежность разрешённой ветке.
Check/workflow/deployment уведомления создают отдельные сообщения.

HMAC SHA-256 проверяется по исходным байтам до чтения JSON.
Некорректная подпись возвращает 401; некорректный payload — 400; неподдерживаемое событие — 202.
Неуспешная доставка или запись Redis возвращает 503.
Общий бюджет Redis, Telegram и подтверждения — 8 секунд.
Одновременные события PR ожидают свободный локальный lease в пределах этого бюджета.

GitHub не повторяет failed deliveries автоматически: используйте Recent Deliveries → Redeliver после устранения причины.
Подробности: [Handling failed webhook deliveries](https://docs.github.com/en/webhooks/using-webhooks/handling-failed-webhook-deliveries).
Успешные `X-GitHub-Delivery` хранятся 7 дней; координаты PR — 180 дней после изменения карточки.
Redis commit и освобождение lease проверяют токен владельца.
Redis не может отменить отправку Telegram после потери lease.
Сбой между успешной отправкой Telegram и commit Redis может создать повтор при Redeliver.
Гарантия exactly-once не предоставляется.

Отправка принадлежит discovery-фиче `delivery` и использует существующий экземпляр Bot.
Для адресации используется штатный `UnifiedViewDTO.message_thread_id`.
Новости сохраняют `SenderManager` и ключи `news:<article_id>`; медиа, редактирование и снятие публикации сохраняются.
Личный UI продолжает использовать `ViewSender`.
Публичный `ViewSender.send` установленной `codex-bot 0.3.1` синхронизирует UI темы по `chat:topic`.
У него нет параметра явного ID карточки PR и контракта передачи ошибок доставки вызывающему коду.
Поэтому notification transport внутри фичи реализует явный send/edit и сообщает ошибки webhook.

Проверка локального среза:

```powershell
.venv/Scripts/python.exe -m pytest tests/tg_bot --no-cov -q
```

Тест реального Redis требует явно выделенную тестовую базу через `TG_BOT_TEST_REDIS_URL`.
Тест использует уникальные ключи и удаляет только собственные ключи; `FLUSHDB` не применяется.
Без этой переменной Redis-тест пропускается; модель Redis в unit-тестах не доказывает Lua/TTL на сервере.

## Generated Assets и S3

Сгенерированные изображения должны ссылаться на канонический `storage_key` и публичный URL под
`/static/generated-assets/<storage_key>`. Production может хранить bytes в S3-compatible Object Storage,
но код и база не должны зависеть от прямых bucket URLs.

Для Hetzner Object Storage в Nuremberg использовать примерный контракт:

```env
ASSET_STORAGE_BACKEND=s3
ASSET_PUBLIC_BASE_URL=/static/generated-assets
ASSET_S3_BUCKET=thesealedworld-generated-assets
ASSET_S3_REGION=nbg1
ASSET_S3_ENDPOINT_URL=https://nbg1.your-objectstorage.com
ASSET_S3_ACCESS_KEY_ID=<secret>
ASSET_S3_SECRET_ACCESS_KEY=<secret>
```

Когда `ASSET_STORAGE_BACKEND=s3`, frontend отдаёт `/static/generated-assets/<storage_key>`
из Object Storage. Не сохранять прямые provider bucket URLs в статьях, монстрах или future generated
content: публичный контракт сайта остаётся `/static/generated-assets/...`.

Перед переносом production assets сначала выполнить dry-run:

```powershell
uv run python scripts/backfill_generated_assets_to_s3.py --local-root var/generated-assets --dry-run
```

Реальный backfill должен копировать файлы, а не регенерировать изображения. Старый volume нужно оставить
как rollback/cache минимум на один release.
