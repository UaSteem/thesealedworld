# Локальная работа с репозиторием для ИИ и художника

Инструкция позволяет скачать исходники, найти каталоги и графику, затем при необходимости запустить локальное окружение.
Для чтения, рисования и обсуждения правил сервер игры не нужен.
Доступ к production, токен Telegram-бота и ключи генерации для этих задач не требуются.

## 1. Скачать нужную ветку

Используйте ветку `develop`. Ветка GitHub по умолчанию может быть другой.

```powershell
git clone --branch develop --single-branch https://github.com/CodexDLC/thesealedworld.git
cd thesealedworld
git branch --show-current
git rev-parse HEAD
```

Первая проверка должна показать `develop`.
Сохраните результат `git rev-parse HEAD`: он определяет точный снимок для обсуждения.

Без Git скачайте [ZIP ветки develop](https://github.com/CodexDLC/thesealedworld/archive/refs/heads/develop.zip).
Распакуйте весь архив.
Откройте каталог, содержащий `pyproject.toml`, `uv.lock` и `src/`.
ZIP не содержит историю Git и локальные файлы владельца.
Готовые PDF и архивы передачи не входят в Git-снимок.
Для работы используйте исходные каталоги и изображения репозитория.

## 2. Начать без установки

Откройте следующие документы:

1. [AGENTS.md](../../../AGENTS.md) — инструкции проекта и маршруты навыков.
2. [CURRENT_GAME_UI.md](../../../CURRENT_GAME_UI.md) — указатель актуального клиента и графики.
3. [Мир и лор](../../game-design/designer/world/README.md) — текущее направление мира.
4. [ADR-0002](../../adr/0002-faction-city-district-progression.md) — города 12 фракций и границы согласованного решения.
5. [Развитие персонажа](../../game-design/library/rpg/attributes.md) и [навыки](../../game-design/library/rpg/skills/README.md).

Без запуска можно читать Python-каталоги, JSON и Markdown, просматривать SVG, PNG и WebP.
Можно рисовать варианты, подписывать предложения и обсуждать правила с владельцем проекта.
Наличие определения в каталоге не доказывает готовность всей игровой механики.

### Где искать данные

Пути в таблицах отсчитываются от корня репозитория.

| Задача | Источник |
| --- | --- |
| Типы предметов | `src/backend/features/items/resources/base_item/` |
| Общий реестр баз предметов | `src/backend/features/items/resources/bases.py` |
| Материалы, сырьё и аффиксы | `src/backend/features/items/resources/material/`, `raw_resource/`, `affixes/` |
| Изображения и варианты предметов | `src/backend/features/items/resources/visuals/` |
| Стартовые слепки персонажей | `src/backend/features/character/resources/starting_imprints.py` |
| Оружейные, тактические и другие навыки | `src/backend/features/game_catalog/skills/resources/definitions/` |
| Способности | `src/backend/features/game_catalog/combat/resources/abilities/definitions/` |
| Финты | `src/backend/features/game_catalog/combat/resources/feints/definitions/` |
| Ограничения выдачи финтов | `src/backend/features/game_catalog/combat/resources/feints/availability.py` |
| Действия боевых предметов | `src/backend/features/game_catalog/combat/resources/items/definitions.py` |
| Эффекты и триггеры | `src/backend/features/game_catalog/combat/resources/effects/`, `triggers/` |
| Концепция Симбиота и Даров | `docs/game-design/domains/gifts/` |

Способности из `abilities/definitions/debug.py` являются ранними тестовыми записями.
Не используйте их как окончательный набор доступных игроку способностей.
Название и короткий текст сверяйте с техническими полями той же записи.

### Где искать изображения

| Материал | Каталог |
| --- | --- |
| Графика текущего клиента | `src/frontend/static/images/game-client/` |
| Фоны помещений и кварталов | `src/frontend/static/images/game-client/places/` |
| SVG действий, статусов, способностей и финтов | `src/frontend/static/images/ui/combat-icons/` |
| Остальные SVG интерфейса | `src/frontend/static/images/ui/` |
| Аватары | `src/frontend/static/images/avatars/` |
| Исходные изображения предметов | `assets/item_art/originals/` |
| Очищенные SVG предметов | `assets/item_art/svg/` |
| Варианты и рендеры предметов | `assets/item_art/variants/`, `assets/item_art/renders/` |
| Общие мастера интерфейса и фонов | `assets/game_client_sources/` |
| Клиентские модули | `src/frontend/static/js/game/client/` |

Проверяйте manifests и attribution рядом с изображениями.
Логический ключ иконки в каталоге не всегда является прямым файловым путём.
Старые изображения в других каталогах `static/images/` могут сохраняться ради совместимости.
Их наличие не делает изображение актуальным стилевым референсом.

`archive/`, `output/` и `artifacts/` — локальные материалы владельца, исключённые из нового снимка.
В скачиваемом репозитории нельзя рассчитывать на их содержимое.
Отдельная мастерская `output/rift-art-lab/` не входит в репозиторий и не является его зависимостью.
Не пытайтесь установить игру из этой мастерской.

`game_ui_lab/` и `rift_lab/` исключены из передаваемого снимка.
Их отдельные приложения и тестовые каталоги остаются локальными у владельца.
Общие мастера клиента находятся в `assets/game_client_sources/`.
Не восстанавливайте отсутствующие Lab-каталоги из случайного старого архива.
Некоторые старые экспериментальные инструменты предполагают локальные Lab-данные.
Они не входят в описанный здесь путь установки и проверки клиента.

## 3. Установить зависимости Python при необходимости

Этот этап нужен для импорта каталогов, проверок и разработки Python-кода.
Для просмотра изображений этап не нужен.

`pyproject.toml` и `uv.lock` требуют Python не ниже 3.13.
Для совпадения с CI выберите Python 3.13.
CI и Dockerfile используют `uv` версии `0.11.19`.

Если Python уже установлен, установите `uv` через него:

```powershell
python -m pip install "uv==0.11.19"
```

Проверьте версию:

```powershell
uv --version
```

Если Python 3.13 ещё не установлен, установите его через `uv`:

```powershell
uv python install 3.13
```

Из корня репозитория установите зависимости по зафиксированному lock-файлу:

```powershell
uv sync --locked --python 3.13
```

Команда создаёт локальную `.venv`.
Группы по умолчанию: `dev`, `backend-runtime`, `frontend-runtime`, `tg-bot`.
Установка библиотеки Telegram не запускает бота и не требует его токена.
Не заменяйте зависимости произвольными версиями из старых инструкций.

Проверьте Python окружения:

```powershell
uv run --locked python --version
```

Для импорта чистых каталогов отдельный сервер не требуется:

```powershell
uv run --locked python -c "from src.backend.features.game_catalog.combat.resources.abilities import get_all_ability_catalog_entries; print(len(get_all_ability_catalog_entries()))"
uv run --locked python -c "from src.backend.features.game_catalog.combat.resources.feints import get_all_feint_catalog_entries; print(len(get_all_feint_catalog_entries()))"
```

Числа показывают наличие записей, а не готовность боя или баланса.
Не импортируйте приложение только ради чтения каталога.

## 4. Локальное окружение: когда оно действительно нужно

Docker нужен для проверки приложения с PostgreSQL, Redis, MongoDB и локальной почтой.
Для нового компьютера используйте отдельные локальные данные.
Не подставляйте адреса, файлы окружения или ключи production.

Базовая конфигурация находится в [deploy/docker-compose.yml](../../../deploy/docker-compose.yml).
Сценарии запуска описаны в [deploy/README.md](../../../deploy/README.md).

### Подготовить локальный файл окружения

Compose использует корневой `.env` через `env_file`.
Создайте собственный `.env` вручную.
Не копируйте `.env` или `.env.prod` владельца.
Готового локального `.env.example` в проекте нет.
`.env.prod.example` описывает другую, production-конфигурацию и не является обязательным шаблоном художника.

У `BackendSettings` и `FrontendSettings` есть локальные значения по умолчанию.
В минимальном локальном наборе нет обязательных полей настроек без значений по умолчанию.
Сам файл `.env` всё равно нужен Compose.

Следующая таблица перечисляет имена ключей, без секретных значений.

| Ключ | Когда нужен |
| --- | --- |
| `DEBUG` | Явно выберите локальный режим разработки. Значение по умолчанию — режим разработки. |
| `SECRET_KEY` | Общий локальный ключ подписи для frontend, backend и chat. Создайте собственный локальный ключ. |
| `BACKEND_INTERNAL_SERVICE_KEY` | Локальный ключ запросов frontend к backend. |
| `FRONTEND_INTERNAL_SERVICE_KEY` | Принимаемый backend ключ. Согласуйте его с `BACKEND_INTERNAL_SERVICE_KEY`. |
| `SITE_TO_GAME_SERVICE_KEY` | Резервный ключ backend, если `FRONTEND_INTERNAL_SERVICE_KEY` не задан. |
| `REDIS_PASSWORD` | Нужен при замене локального пароля Redis, заданного Compose по умолчанию. |
| `SITE_DATABASE_URL`, `GAME_DATABASE_URL`, `DATABASE_URL` | Compose задаёт контейнерные адреса. Для запуска Python вне Docker потребуются адреса хоста. |
| `REDIS_URL`, `MONGO_URL`, `MONGO_DATABASE` | Compose задаёт контейнерные подключения. Внешнему Python нужны локальные адреса хоста. |
| `BOT_TOKEN` | Обязателен только при запуске отдельного `tg-bot`. В рекомендованном ниже наборе бот отсутствует. |

При `DEBUG=False` валидаторы запрещают стандартные и development-ключи.
Эта инструкция не переводит окружение в production.

### Запустить только локальный набор

Обычный запуск всего Compose также включает Telegram-бота и фоновые обработчики.
Для первого просмотра используйте явный список сервисов без бота, Studio и генератора изображений.

```powershell
docker compose -f deploy/docker-compose.yml up -d --build postgres redis mongo mailpit backend frontend frontend-play chat combat-worker system-worker chat-archive-worker
docker compose -f deploy/docker-compose.yml ps
```

Compose также запустит зависимости `backend-migrate` и `site-migrate`.
`backend-migrate` применяет локальные миграции, создаёт Mongo-индексы и материализует каталог монстров.
Это изменяет локальные данные, а не только запускает HTTP-сервер.

Выбранный набор не запускает `tg-bot`, `studio`, `generation-ai-worker` и `combat-ai-simulation-worker`.
Внешняя генерация изображений и полноценная проверка всех игровых цепочек сюда не входят.

Проверьте контейнеры через `ps`.
Проверьте журналы нужного сервиса при ошибке:

```powershell
docker compose -f deploy/docker-compose.yml logs --tail 100 backend frontend frontend-play chat
```

Не публикуйте полный журнал без проверки содержимого.

Локальные адреса: сайт `http://127.0.0.1:8000`, игровой frontend `http://127.0.0.1:8003`, почта Mailpit `http://127.0.0.1:8025`.
Backend и chat доступны на портах 8001 и 8002; у обоих есть `/health`.

Прямые порты не подтверждают работу авторизации и cookies между frontend-поверхностями.
Для браузерной проверки входа используйте Nginx-слой из `deploy/README.md`:

```powershell
docker compose -f deploy/docker-compose.yml -f deploy/compose.nginx-test.yml up -d --build nginx-test combat-worker system-worker chat-archive-worker
uv run --locked python tools/deploy/nginx_smoke.py
```

Откройте `http://thesealed.localhost:8080`.
Игровая поверхность находится по адресу `http://play.thesealed.localhost:8080`.
Nginx-слой убирает прямые host-порты приложений.
Проверка маршрутов не заменяет ручную проверку аккаунта и игровой сессии.

Для остановки используйте `stop` с тем же набором Compose-файлов.
Не удаляйте volumes для обычной остановки.

## 5. Проверки для другого ИИ

Для проверки только документов и изображений серверный стек не нужен.
Некоторые клиентские pytest-проверки запускают JavaScript через Node.js.
Для них установите Node.js и проверьте `node --version`.
Для просмотра файлов и импорта Python-каталогов Node.js не требуется.
При изменении кода выберите проверки затронутого слоя по инструкциям проекта.

Справка существующего инструмента:

```powershell
uv run --locked python tools/dev/check.py --help
```

Примеры отдельных режимов:

```powershell
uv run --locked python tools/dev/check.py --lint
uv run --locked python tools/dev/check.py --types
uv run --locked python tools/dev/check.py --tests unit
```

Исторические hash-проверки корневого `archive/` выполняются только при наличии локального manifest.
В обычном clone они явно пропускаются; рабочие retirement-проверки остаются активны.
CSS-эталоны и мастера интерфейса, нужные обычным тестам, включены в снимок отдельно.

Для полного неинтерактивного прогона предусмотрен `--ci`:

```powershell
uv run --locked python tools/dev/check.py --ci
```

Такой прогон выполняет больше проверок и может потребовать подготовленное окружение.
`codex-core` входит в зависимости; отдельный checkout этой библиотеки рядом не требуется.
Простой запуск `python tools/dev/check.py` без режима не подтверждает прохождение проверок.

Для документации зависимости находятся в группе `docs`:

```powershell
uv sync --locked --group docs
uv run --locked --group docs mkdocs build --clean
```

Отсутствие ошибки установки не доказывает успешный запуск приложения.
Фиксируйте отдельно результат установки, проверок, локального запуска и ручного просмотра.

## Граница проверки этой инструкции

Команды сверены с `pyproject.toml`, `uv.lock`, CI, Dockerfile, Compose и текущими настройками приложения.
Повторная синхронизация существующего окружения по `uv.lock` проверена.
Запуск сервисов при подготовке инструкции не выполнялся.
Чистое окружение другого компьютера и полный игровой цикл не проверены.
