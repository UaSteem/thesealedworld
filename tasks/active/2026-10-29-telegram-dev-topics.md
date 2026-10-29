# Telegram: темы команды разработки

Статус: локально реализовано и независимо проверено; runtime-проверки ожидают выполнения. Итог ревизора фиксирует ведущий.

## Исходный запрос

Пользователь хочет подключить уведомления GitHub и деплоя к существующему игровому боту, используя наработку https://github.com/CodexDLC/telegram_notifier_bot . Уточнение: бот должен использовать штатную поддержку топиков codex_bot; если библиотека не используется, исправить интеграцию.

## Требования

| ID | Требование | Реализация | Проверка |
| --- | --- | --- | --- |
| R1 | Проверить использование codex_bot и штатную поддержку тем; исправить выявленные пробелы подключения | done | pass (исполнитель, локально) |
| R2 | Направлять технические сообщения в группу -1004387822347: задачи/решения 3, геймдизайн 5, лор/мир 7, графика 9, баги 12, GitHub 14, деплой 16 | done | pass (исполнитель, локально) |
| R3 | Принимать push-события GitHub, без периодического опроса репозитория | done | pass (исполнитель, локально) |
| R4 | Существующая отправка через feature-механизм, сохранив news media/edit/unpublish и личный UI | done | pass (исполнитель, локально) |
| R5 | PR по repo+number обновляет своё сообщение opened → merged; ID хранится в Redis | done | partial: HTTP/модель pass; реальный Redis unverified |
| R6 | Исправить фактические ошибки полного CI и подтвердить полный gate и новый remote run | done | pending: итог полного gate и remote CI |

## Первоначальный план

1. Проверить зависимость, контейнер, DTO и отправители библиотеки и игры.
2. После выбора режима проверки определить минимальные изменения штатной интеграции тем и уведомлений.
3. Проверить маршрутизацию и изоляцию тем тестами; отдельно отметить отсутствие или наличие живой проверки и деплоя.

## Диагностика

- pyproject.toml содержит codex-bot>=0.3.0; BotContainer наследует BaseBotContainer; фабрика использует BotBuilder.
- В канонических исходниках библиотеки UnifiedViewDTO и ViewSender поддерживают message_thread_id; ключ координат публичного чата учитывает тему.
- Локальный TelegramMediaSender игры отправляет сообщения и фото напрямую через aiogram и не принимает message_thread_id. Это отдельная цепочка публикации новостей; она сама по себе не доказывает отсутствие поддержки тем в остальном боте.
- Последующая проверка установленных и канонических исходников подтвердила codex-bot 0.3.1 и точные sender APIs (см. уточнения ниже). Ничего не отправлено в Telegram, runtime-конфигурация не изменена.

## Уточнения и режим

- Пользователь выбрал независимого ревизора; исполнитель не проводит независимую приёмку.
- R4: существующую отправку Telegram привести к системе фич бота, сохранив новости (медиа, редактирование, снятие публикации) и личный UI.
- Не деплоить, не отправлять Telegram сообщения, не читать секреты .env.

## Инженерные решения (не дополнительные требования пользователя)

- Установлен codex-bot 0.3.1. FeatureDiscoveryService и BaseBotContainer остаются точками композиции. Feature delivery принимает штатный UnifiedViewDTO с message_thread_id для явной адресации сообщений, использует существующий container.bot. ViewSender поддерживает topic UI, но заменяет координаты chat:topic и подавляет ошибки отправки; для подтверждаемой append-only ленты его контракт непригоден.
- Перенести существующий news media transport внутрь delivery feature; единственный caller announcements получает delivery через get_feature, старый container.media_sender удалить. Сохранить ключи news:<article>.
- GitHub feature запускает aiohttp POST /webhooks/github на 0.0.0.0:8091 через Dispatcher startup/shutdown. Выключено по умолчанию; включение требует HMAC secret и Redis.
- Разрешён origin CodexDLC/thesealedworld (подтверждён git remote); ветки develop/main конфигурируемы. Push/PR → github=14; завершённые check_run/workflow_run и terminal deployment_status → deploy=16. Остальные темы — явная адресация.
- Redis delivery key + TTL, token-fenced lease/commit/release. При неуспехе Telegram/Redis — 503, без успешного ACK; повтор доставляет снова. Crash между send и commit допускает повтор (не exactly-once). GitHub не повторяет failed deliveries автоматически; требуется ручной Redeliver.

## Актуальный план

1. Зафиксировать red test новости → delivery feature до production рефактора.
2. Delivery feature + карта тем; GitHub formatter/filter + HMAC HTTP + Redis adapter.
3. Lifecycle, env/compose и инструкция настройки; nginx меняет ведущий отдельно.
4. Focused tests (HMAC, фильтры, длина/escape, повторы, fencing, append-only, news regression, startup); реальный Redis adapter test при доступном локальном runtime.
5. Передать ведущему изменения и результаты для независимой ревизии.


### Уточнения после диагностики

- Пользователь уточнил: отправитель должен обновлять сообщение при известных координатах; PR opened → merged должен обновлять тот же message ID из Redis. Push остаются отдельными сообщениями. Не смешивать этот сценарий с пользовательским /start UI.
- Полная проверка installed/canonical sender surface: публичны ViewSender.send(UnifiedViewDTO), UnifiedViewDTO.send(message), SenderManager.get_coords/update_coords/clear_coords. MessageCoordsDTO существует, но публичный ViewSender его не принимает; old_message_id принимает приватный _process_message. Feature transport использует тот же container.bot; библиотечный feature lifecycle, DTO и SenderManager сохраняются. PR state (message ID, event version) хранится в owning Redis adapter вместе с fenced entity lock, чтобы commit был атомарным. Это инженерное решение из-за отсутствия публичного entity-upsert/error-propagation API.
- Закрытая dev group исключается из community feed до обработки содержимого/публикации в stream.
- Начальная настройка ingress требует обновить nginx config (ведущий); последующие bot-only updates не требуют перезапуска всей игры.


## Реализация и наблюдения исполнителя — 2026-10-29

- Discovery features: `delivery` владеет news transport и notification send/edit; `github_notifications` владеет HTTP, фильтрами и подтверждением доставки. Старый `src/tg_bot/sender` и `container.media_sender` удалены; re-export не оставлен.
- PR entity state включает message ID, updated_at и merged; ключ изолирован по группе/теме/repo/PR. Delivery и entity lease захватываются атомарно; commit/release требуют актуальный owner token. Обычный overlap ожидает освобождения lease в общем бюджете 8 секунд. Старое updated_at/откат merged пропускаются; одинаковые updated_at без merged обрабатываются по порядку получения.
- Telegram edit transient failure возвращает ошибку без нового send; fallback допускается только для действительно отсутствующего/недоступного для редактирования сообщения. `message is not modified` — успех.
- Реальный startup/shutdown aiohttp проверен на локальном порту внутри теста. Весь runtime использует тот же экземпляр Bot, без второго bot token/polling GitHub.
- Конфигурация безопасна по умолчанию (выключено); HMAC обязателен. Бот/Redis/Telegram ошибки не превращаются в успешный ACK.
- Новости сохранили координаты и media/edit/unpublish. Dev group исключена из community feed до чтения текста/публикации Redis.
- Инструкция добавлена в `docs/ru/management/deployment.md`: первоначальный bot+nginx ingress update, дальнейший отдельный tg-bot deployment, разрешения тем, GitHub subscriptions, manual Redeliver, TTL и пределы гарантий.

### Проверки исполнителя

1. Refactor red: `pytest tests/tg_bot/test_delivery_feature.py --no-cov -q` до production изменения упал ожидаемо с `AttributeError: container.media_sender`; после миграции проходит. Контрактный тест GitHub PR до реализации webhook упал на отсутствии модуля orchestrator; финальный HTTP-тест доказывает opened→merged edit одного ID.
2. Финальный `.venv/Scripts/python.exe -m pytest tests/tg_bot --no-cov -q`: **39 passed, 1 skipped, 4.27s**. Skip — явно выделенная база `TG_BOT_TEST_REDIS_URL` не задана. Покрыты HMAC/tamper/body limit, repo/ref/event/topic filters, PR lifecycle/isolation/stale order, append-only push, overlap wait, retry/dedupe/failed commit, transient edit, 8s budget, discovery/lifecycle, news regression, dev privacy.
3. `.venv/Scripts/python.exe -m ruff check src/tg_bot tests/tg_bot`: **pass**.
4. `.venv/Scripts/python.exe -m ruff format --check src/tg_bot tests/tg_bot`: **82 files already formatted**.
5. `.venv/Scripts/python.exe -m mypy --follow-imports=silent src/tg_bot/core/config.py src/tg_bot/features/telegram/delivery src/tg_bot/features/telegram/github_notifications src/tg_bot/infrastructure/redis/github_deliveries.py`: **11 files, no issues**. Это focused type check, не full gate.
6. `git diff --check` по файлам исполнителя: **pass** (предупреждение нормализации CRLF docs не является ошибкой).

В этом Windows sandbox asyncio инициализация зависала даже на `asyncio.run(asyncio.sleep(0))`. Локальные runtime pytest запущены с разрешённой эскалацией; отказа auto-review не было. Внешние сервисы не вызывались.

### Проверки ведущего (переданы исполнителю)

- `tests/deploy/test_bot_env_isolation.py --no-cov -q`: **4 passed**, включая `docker compose config` defaults/overrides/empty без Docker daemon.
- `tests/deploy/test_bot_env_isolation.py tests/deploy/test_network_boundaries.py tests/deploy/test_service_isolation.py tests/deploy/test_nginx_log_privacy.py --no-cov -q -m 'not external'`: **34 passed**.
- Nginx route настроен ведущим отдельно: main exact `/webhooks/github` → `tg-bot:8091`; play exact path →404; body1MiB, proxy retries off.

### Ограничения доказательств

- Модель Redis в unit tests не доказывает реальные Lua, TTL или сетевые гонки. Opt-in интеграционный тест реализован с UUID namespace и удалением только собственных ключей. Реальный Redis runtime недоступен (Docker daemon выключен); adapter integration **unverified**.
- `nginx -t`, полный `tools/dev/check.py`, живые Telegram/GitHub, production secret/setup, build и deploy **не выполнены**.
- Crash/потеря lease между Telegram send и Redis commit допускает повтор. Exactly-once не заявляется. После неуспеха нужен GitHub manual Redeliver.
- Независимую ревизию и её итоговый статус добавляет ведущий; пользовательская приёмка ещё не получена.

## Независимая ревизия

Ревизор: отдельный внутренний агент `telegram_review`, без истории чата, только чтение и проверки. Первоначальное заключение зафиксировано до передачи черновых утверждений ведущего; затем проверены документация и утверждения отчёта. Существенных дефектов не обнаружено.

| Требование | Независимое заключение | Предел доказательства |
| --- | --- | --- |
| R1 | pass | Installed/canonical codex_bot, discovery, container и DTO проверены |
| R2 | pass локально | Карта семи тем, направления GitHub/деплой и исключение dev group проверены |
| R3 | pass локально | HMAC, allowlists, HTTP lifecycle, ingress и отсутствие GitHub polling |
| R4 | pass локально | Feature-доставка новостей с прежними media/edit/unpublish; личный UI по неизменённой цепочке, без живого /start |
| R5 | partial | HTTP + modelRedis + Bot mock подтверждают одно сообщение на PR, изоляцию, конкуренцию, stale guard и ошибки; реальные Redis Lua/TTL/fencing остаются unverified |

Собственный запуск ревизора: `.venv/Scripts/python.exe -m pytest tests/tg_bot tests/deploy/test_network_boundaries.py -q --no-cov` — **70 passed, 2 skipped**, exit 0. Пропущены real Redis adapter и runtime nginx. Документация и четыре существенных утверждения черновика подтверждены с указанными пределами. Финальные изменения исполнителя после ревизии — форматирование и фиксация отчёта, без изменения поведения.

Режим совместимости: `compatibility-required` для существующих новостей и личного UI; старый container.media_sender и исходный src/tg_bot/sender удалены, callers переведены на discovery-фичу delivery. Дублирующего старого пути не оставлено.

Итог: локальная реализация независимо проверена; интеграционная приёмка реального Redis и серверного запуска открыта. Пользовательская приёмка не получена. В рамках этой задачи внешние сообщения, коммиты, публикация и deploy не выполнялись.

## Изолированный перенос на main — 2026-10-29

Пользователь поручил выполнить доступные действия на GitHub. Ведущий готовит отдельный PR в `main`; публикация и серверный запуск разделены.

- Рабочая копия: `C:\Users\prime\.codex\worktrees\telegram-dev-notifications\TurnBasedMMORPG`.
- Основа: `origin/main`, `6ccc92561c633f618eb7ee082c36caa44a1400f7`.
- Ведущий перенёс только изменения этой задачи; `tests/deploy/test_network_boundaries.py` и соседние изменения develop не переносились.
- Исходная рабочая копия `D:\Workspace\personal\pets\TurnBasedMMORPG` на этом этапе не изменялась.
- Добавлен самостоятельный `tests/tg_bot/test_webhook_ingress.py`: точный HTTPS main-route, 404 игрового хоста, подписанные заголовки/body, ограниченные timeout/body, запрет proxy retries, только внутренний порт, выключенные Compose/example defaults.
- Точный URL настройки: `https://thesealedworld.com/webhooks/github`.

### Совместимость с фактическими main workflows

Проверены `.github/workflows/build-images.yml`, `deploy-production.yml`, `ci.yml`, compose и nginx Dockerfile из этой рабочей копии. Pipeline не изменялся.

- `Build Release Images` собирает `tg-bot` и nginx после Quality Gate; запускается вручную либо тегом `v*`.
- `Deploy Production` поддерживает `layer=tg-bot`, но не проверяет успешность build для указанного `image_ref`.
- Checkout deploy-конфигурации берётся из выбранной ветки workflow, а не `image_ref`; инструкция требует актуальный `main` и опубликованный образ успешной сборки.
- `layer=infra` обновляет весь infra-слой. Для initial nginx-only обновления инструкция содержит адресные `docker compose ... pull nginx` и `up -d --no-deps nginx`.
- Nginx template встроен в образ; одной перезагрузки старого образа недостаточно.
- Каждый deploy перезаписывает серверный `deploy/.env` содержимым Actions secret `ENV_FILE`. Настройки webhook нужно добавить именно в этот источник, сохранив остальные переменные.
- В main CI matrix `docker-build` нет tg-bot; это существующее ограничение, pipeline из develop не переносился.

### Повторная проверка в main-worktree

Все команды запускались с CWD этой рабочей копии и `PYTHONPATH=<main-worktree>;<main-worktree>/src`. Использован существующий интерпретатор `D:/Workspace/personal/pets/TurnBasedMMORPG/.venv/Scripts/python.exe`. Прямая проверка `tg_bot.__file__` подтвердила путь `src/tg_bot` внутри main-worktree.

- `-m pytest tests/tg_bot --no-cov -q`: **43 passed, 1 skipped, 5.26s**. Skip — opt-in реальный Redis. Это новый самостоятельный прогон на main, не результат develop.
- `-m ruff check src/tg_bot tests/tg_bot`: **pass**.
- `-m ruff format --check src/tg_bot tests/tg_bot`: **83 files already formatted** после форматирования нового ingress-теста.
- `-m mypy --follow-imports=silent src/tg_bot/core/config.py src/tg_bot/features/telegram/delivery src/tg_bot/features/telegram/github_notifications src/tg_bot/infrastructure/redis/github_deliveries.py`: **11 source files, no issues**.
- `git diff --check`: **pass**.

На этом этапе исполнитель не читал секреты, не коммитил, не публиковал PR, не создавал repository webhook и не выполнял deploy. Реальный Redis, nginx runtime, живые GitHub/Telegram и полный gate по-прежнему не проверены. Независимый scope audit main-переноса выполняется отдельно.

## Независимая проверка изолированного PR в main

Повторный ревизор telegram_review проверил diff от main 6ccc9256: scope и совместимость pass, новых существенных дефектов нет. Собственный запуск tests/tg_bot в main-worktree: 43 passed, 1 skipped (реальный Redis). Проверены main lockfile codex-bot 0.3.1, точечный ingress test, ENV_FILE source и nginx-only инструкция. Game, CI и зависимости main не менялись. Merge/build/deploy не выполнялись.

## Подготовка коммита

Pre-commit обнаружил B104 для локального default и три синтетических строки теста: default изменён на127.0.0.1 (compose явно сохраняет0.0.0.0), false positives помечены точечными allowlist-комментариями. Независимый ревизор подтвердил отсутствие регрессии и реальных секретов. Повторный прогон ведущего после изменения:43passed1skipped,5.08s. Pip-audit проверял собственный cacheenv: только его certifi/filelock обновлены до2026.10.19/4.2.1; зависимости и hooks репозитория не менялись. Проверки не отключались. GitHub connector при create-tree вернул403 Resource not accessible by integration; публикация проверяется через штатный Git Credential Manager без извлечения токенов.

## Исправление CI PR #5

Пользователь сообщил о падении Full Quality and Docs и потребовал проверить причину. Продолжение той же задачи с независимым ревизором. Просмотр защиты веток временно отложен, настройки GitHub не менялись.

R6: исправить фактические ошибки CI, воспроизвести полный gate в чистом окружении выбранной ветки и подтвердить результат новым GitHub Actions запуском. Не отключать проверки и не маскировать advisories. Минимальные исправления зависимостей и окружения hooks входят в устранение этого падения.

Исходный запуск: head fb7436571b99e99486551ff8a3426e141e0b78aa, run40962702681/job123759317008. Документация прошла;2757tests passed,77.93% coverage. Упали полный Mypy (factory.py:65 ContainerProtocol.get_feature отсутствует), pip-audit hook (pip26.0.1) и repository audit (194 advisories в21пакете). Локальная узкая проверка не включала factory.py, а изменение только cacheenv не воспроизводилось на чистом CI.

План: ведущий исправляет тип фабрики и запускает полный gate; исполнитель обновляет минимальные подтверждённые dependency constraints/lock и fresh-hook зависимости; ревизор проверяет исправления. Перед изменением типа локальный mypy factory.py воспроизвёл точный attr-defined failure.

### Результат исправления CI

Тип build_bot привязан к фактическому BotContainer; повторный mypy той же фабрики прошёл. Обновлены уязвимые прямые зависимости и минимальные transitive constraints с uv.lock; advisory ignores удалены. Pip-audit hook задаёт pip>=26.2 и прошёл из нового PRE_COMMIT_HOME. Markdownlint закреплён на стабильном Node24.19.0: автоматический выбор Node27 alpha ломал создание hook environment.

Полный повторный запуск `uv run python tools/dev/check.py --ci` в собственной Python3.13.6 .venv этой рабочей копии завершился exit0, ALL CHECKS PASSED. Лог: telegram-full-quality-final.log в артефактах чата. Все hooks, полный mypy (1544 файлов), аудит без исключений, fixtures и docs прошли;2757 passed,1 skipped,8 warnings,coverage77.92%,105s. Локальный hadolint helper пропускает Docker-проверку при недоступном daemon; Linux CI остаётся обязательным подтверждением. Реальные Redis/nginx/Telegram и deploy по-прежнему не проверены. Независимый ревизор проверяет итог; следующий шаг — commit/push и новый GitHub Actions запуск.

Независимая приёмка correction-среза: telegram_review подтвердил pass для push и повторного Linux CI, новых существенных дефектов и bypass проверок нет. Ревизор самостоятельно прочитал финальный лог и подтвердил полный набор проверок, тип фабрики, constraints/lock и Node pin. Linux CI pending.
