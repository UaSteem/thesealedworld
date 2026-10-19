# Frontend

`src/frontend/` — server-side site-web FastAPI service. Он рендерит публичный
сайт, account/auth flow, cabinet/admin surfaces, library и game-facing browser
views.

В текущей архитектуре имя `frontend` историческое: по ownership это site-web
service, а не только browser code.

## Ownership

Frontend/site владеет:

- public site pages;
- auth pages и user/account flow;
- cabinet/admin rendering;
- library pages;
- Jinja/HTMX templates и site/game-facing browser views;
- frontend routes, forms, services, view models и static assets;
- typed backend API clients under `src/frontend/integrations/backend_api/`;
- site-owned database models/repositories;
- Alembic миграциями для `site` schema;
- graceful unavailable state для game-backed страниц, когда backend/game
  недоступен.

Frontend/site не владеет:

- gameplay rules;
- combat/scenario/exploration runtime;
- game workers;
- game/chat schemas;
- прямым импортом backend internals.

## Current Feature Shape

Site-owned features живут в:

```text
src/frontend/features/
```

Game-facing browser orchestration живет в:

```text
src/frontend/game_features/
```

HTTP-клиенты к game backend живут в:

```text
src/frontend/integrations/backend_api/
```

## Site Database

Frontend Alembic и database infrastructure находятся в:

```text
src/frontend/alembic/
src/frontend/alembic.ini
src/frontend/core/database/
```

Site models принадлежат `site` schema. Backend/game models не импортируются в
frontend database layer.

Историческая `0001_site_schema_baseline` фиксирует девять таблиц до hashed
refresh tokens, referrals и email verification. Она использует явный DDL и не
импортирует текущие ORM models. Новые поля добавляются отдельными ревизиями.
`0005_site_index_names` переименовывает четыре исторических индекса под текущее
соглашение имён; уже канонические имена допускаются, конфликтующие/дублирующие
индексы требуют ручного разбора до миграции.

Изолированная проверка на PostgreSQL (Docker должен быть запущен, локальный
образ `postgres:16-alpine` — доступен):

```powershell
$env:RUN_SITE_MIGRATION_POSTGRES='1'
.venv/Scripts/python.exe -m pytest tests/frontend/migrations/test_site_migrations_postgres.py --no-cov -q
```

Suite создаёт собственный временный контейнер без volumes на случайном loopback
порту и удаляет его после проверки. Реальные DSN и `.env` не читаются. Проверяются
чистый upgrade, upgrade с данными `0001` и `0004`, повторный upgrade, соответствие
head текущим ORM columns/types/nullability/defaults/indexes/FK и rollback.

Downgrade до `0001` удаляет referral/email данные и не может восстановить исходные
refresh secrets из SHA-256: сессии потребуют повторного входа. Downgrade до `base`
удаляет site-данные; отсутствие `CASCADE` защищает чужие объекты — конфликт
откатывает транзакцию миграции. Это проверки изолированной схемы, не разрешение
на rollback или изменение действующей базы.

## Завершение и обновление сессий

Browser `POST /logout` отзывает обе присутствующие game credentials через
внутренний backend endpoint, затем текущий site refresh token. Если middleware
уже выполнил ротацию, используется новый токен из request state. При успехе
удаляются site/game access/refresh и active-character cookies, включая domain и
legacy host-only варианты; middleware не выставляет их повторно. При недоступном
backend/хранилище возвращается 503 с `Retry-After`, credentials сохраняются для
повтора. Logout не освобождает игровой actor и не меняет gameplay state.

Game session revoke и продление refresh выполняются Redis compare-and-delete /
compare-and-expire: старый session ID не может удалить новый вход или восстановить
отозванный slot. Site refresh с оставшимся сроком больше семи дней сохраняется;
при сроке не больше семи дней старый hash удаляется и новый добавляется одной SQL транзакцией.
Из конкурентных ротаций успешна одна. После успешного commit повтор старого токена
отклоняется, включая потерю ответа; это не replay успешного refresh.

Активный WebSocket route — `/ws/realtime`. Он проверяет game access expiry и
текущий session ID на входящих/исходящих операциях и фоновым monitor раз в секунду
с учётом expiry; Redis check ограничен двумя секундами. Expiry закрывает сокет
кодом 4001, logout/replacement/ошибка хранилища — 4003. Отписки и pending sends
очищаются. Transport budgets: 16 KiB UTF-8 на text frame, 20 frames/sec с burst 40;
binary frames отклоняются. Frame budget действует после ASGI receive; wire limits
сервера не менялись. Redis check — точка авторизации, не атомарная сетевая доставка.

JSON API `/auth/logout` принимает только site refresh token и остаётся site-only.
Ранее скопированный stateless site access JWT сохраняет прежний срок действия;
этот шаг не вводит blacklist site JWT. Для game tokens отзыв session slot
прекращает HTTP/refresh доступ и завершает открытый WebSocket.

## Разделы

- [Дизайн веб-интерфейса](interface_design/index.md)
- [Game Features](game_features/index.md)
- [Site Features](site_features/index.md)
- [Integrations](integrations.md)
- [Middleware](middleware.md)
