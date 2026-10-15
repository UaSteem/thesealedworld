# Аудит 07/10 — Application Security Sealed World

Дата: **09.10.2026**. Объект: разрешённое локальное рабочее дерево `TurnBasedMMORPG`, HEAD `6ccc9256` **с уже существовавшими staged/unstaged/untracked изменениями**. Выводы относятся к прочитанным файлам рабочего дерева, а не только к commit. Проверка независима от предыдущих отчётов.

Режим: **защитный статический аудит**, согласно последнему уточнению владельца. Проверены маршруты, middleware, dependencies, DTO, сервисные и storage-контракты. Отчёт не содержит инструкций обхода защиты, эксплуатационных запросов или последовательностей атак. Production, публичные домены, реальные аккаунты, БД и внешние провайдеры не проверялись. Изменения приложения и защитные исправления не выполнялись.

## 1. Executive Summary

**Основной дефект — неодинаковое применение серверной авторизации.** Frontend защищает кабинет и формы, но это не защищает отдельно подключённые backend-маршруты. В текущем коде отсутствуют auth/ownership gates у игровых Combat/Rift API, конфигурационного API, нескольких административных API и диагностических API. Версионируемый Nginx-шаблон передаёт `/api/` напрямую backend; он не исключает эти группы. Это подтверждает дефект приложения и предусмотренную конфигурацией публикацию, **но не доказывает фактическую доступность production**: активный reverse proxy, firewall и окружение не исследованы.

Вторая группа — неполные проверки на границах уже аутентифицированных запросов: приватная история чата не проверяет членство, отправка сообщений не проверяет право на канал, WebSocket использует два разных источника идентификатора персонажа. Третья — целостность игрового состояния: игровой Rift DTO переносит внутренние управляющие поля в обычные player operations; site JWT допускается там, где требуется выбранный персонаж и активная игровая сессия.

Сохранены **13 подтверждённых статическим анализом дефектов**: 7 High, 6 Medium. Один из Medium касается backend-only Exploration с отдельно оговорённой неизвестной внешней доступностью; один из High — локальной Studio, не публичного production-приложения. Дополнительно зарегистрированы 5 рисков/наблюдений A07-14–18. **Подтверждённых эксплуатацией уязвимостей в этом отчёте нет; Critical не присваивалась.** Техническая severity отражает нарушение контракта, а не возраст продукта.

Необходимые защитные изменения для будущего общего плана: обязательная идентичность и ownership на всех player routes; отдельная административная/service policy; серверное определение результатов Rift; membership policy для истории, подписок и отправки чата; согласованный отзыв site/game sessions; изоляция Studio и принудительная read-only политика. Исправления в рамках аудита не вносились.

## 2. Threat model

Защищаемые активы: учётная запись и её сессии, персонажи и runtime-состояние, результаты боя, предметы/ресурсы/XP, приватные сообщения, конфигурация игры, генерационные задания и бюджет провайдера, административные отчёты. Проверка одного JWT не заменяет право на конкретный объект.

| Уровень доверия | Разрешённые операции и данные | Клиентские идентификаторы | Фактическая проверка / граница |
| --- | --- | --- | --- |
| Анонимный посетитель | Публичные страницы, вход/регистрация, явно публичный каталог | Email, формы, публичные catalog filters | Site auth handlers; у части backend routes обязательной идентичности нет — A07-01–04 |
| Зарегистрированный пользователь | Собственная учётная запись и список своих персонажей | `user_id`, character selection | Site user lookup; lobby internal DTO передаёт identity от доверенного frontend; деактивация проверяется не везде — A07-09 |
| Авторизованный игрок | Операции текущей game session | `char_id`, action, resource identifiers | Game JWT: подпись, audience/type/expiry; Redis session lock. Эти dependencies подключены не ко всем маршрутам |
| Владелец персонажа | Данные/действия своего персонажа в допустимом состоянии | `char_id`, `item_id`, `corpse_ids` | Inventory проверяет `(char_id, user_id)`; Character/Arena/City/Scenario передают user в owner-aware services. Combat/Rift owner context отсутствует |
| Участник группы/боя/Rift | Доступ к своей группе, участию, разрешённым переходам | `combat_id`, `rift_id`, `run_id`, `travel_id`, group IDs | Runtime проверяет часть состояния/participation; это не устанавливает владельца HTTP-запроса. Chat membership неполна |
| Модератор | Только делегированные операции модерации | Пользователь, сообщение, feedback/thread | В проверенном frontend кабинет закрывается `is_superuser`; отдельная завершённая moderator permission policy не установлена |
| Администратор | Live config, accounts, news, разрешённые служебные операции | `user_id`, `task_id`, `run_id`, keys | Frontend `AdminAuthMiddleware`; reusable Cabinet сам не реализует такую границу. Несколько backend admin groups не имеют gates |
| Внутренний сервис | Узкие вызовы lobby/admin integration | Site identity DTO, character IDs | `require_internal_service_key` действительно используется у lobby internal/admin_players; shared key не несёт granular permissions |
| Background worker | Только проверенные задания своего домена | Event payload, job IDs, actor IDs | Redis/ARQ считается доверенным транспортом; некоторые workers полагаются на upstream validation. Прямой публичный доступ к Redis не предполагался |
| AI/content provider | Возврат данных/изображений по серверному заданию | Generated text, metadata, assets | Выход провайдера — недоверенный контент; генерационный API нуждается в административной авторизации, render sinks требуют отдельной политики |
| Оператор Studio | Аналитическое чтение выбранного источника | `studio_source`, simulation/content IDs | Выбор source из allowlist, но app auth и read-only enforcement для HTTP actions отсутствуют — A07-12 |

Основные переходы привилегий: site login → site identity; выбор собственного персонажа → game token/session; frontend admin → внутренний backend API; HTTP action → domain service → worker; Studio source selection → backend выбранного источника. Для каждого такого перехода требуются отдельно установленный actor, область полномочий и проверяемое состояние. Source cookie и подпись user token не являются административным полномочием.

## 3. Attack surface inventory

Статический AST-подсчёт декораторов HTTP/WebSocket нашёл: **109 handlers в 21 файле backend/features; 5 в 2 файлах backend/chat; 1 backend/realtime; 93 в 25 файлах frontend; 3 в 2 файлах Studio shell/source selector**. Это количество объявлений, не число опубликованных URL: включены условные dev routes, не включены динамически собираемые Cabinet action routes и mounts. Telegram использует другой механизм handlers; ноль HTTP-декораторов не означает отсутствие Telegram entrypoints. Все группы ниже проверены на способ подключения; глубина сервисного анализа указана в находках и ограничениях.

| Поверхность | Назначение / текущие gates | Требуемая граница |
| --- | --- | --- |
| Site `/login`, `/register`, `/logout`, `/auth/*` | Site auth, cookie/form CSRF; JSON API с явными tokens | Session lifecycle, active account, abuse controls |
| Frontend `/admin/*` | `AdminAuthMiddleware` + `AuthUserMiddleware`, общий CSRF | Superuser; отдельная policy для будущих moderator roles |
| Frontend account/play routes | Account/game middleware, route dependencies | Site identity либо game identity по явному контракту; не заменяют backend policy |
| `/api/game/combat/{char_id}/*` — 6 handlers | Только orchestrator dependency | Game access + selected character + owner + combat state; A07-01 |
| `/api/game/rift/{char_id}/*` — 6 handlers | Только player service dependencies | Game access + owner + Rift membership/state; A07-01/05 |
| `/api/internal/config` — 5 handlers | Manager/value validation, auth отсутствует | Admin/service permission для чтения и изменения; A07-02 |
| `/api/admin/combat-ai` — 12 handlers | DB/runtime/queue dependencies, auth отсутствует | Admin/simulation permission; A07-03 |
| `/api/admin/monsters` — 8 handlers | Service/DB dependencies, auth отсутствует | Content administration; A07-03 |
| `/api/admin/generation-ai` — 2 handlers | DB/repository dependencies, auth отсутствует | Generation permission и task visibility; A07-03 |
| `/api/admin/players` — 4 handlers | На каждом `require_internal_service_key` | Сохранить gate; service credentials обязательны и ограничены |
| `/api/internal/{combat,scenario,exploration}/sessions` — 4 handlers | Auth отсутствует | Internal/admin diagnostics; A07-04 |
| `/api/game/combat/analytics` — 6 handlers | Analytics service, auth отсутствует | Admin analytics; backfill — отдельное write permission; A07-04 |
| `/api/game/inventory` — 3 handlers | User dependency, game scope при наличии claims, owner query | Owner работает; необходим обязательный game context — A07-11 |
| Arena / City services / Character | User + conditional game scope; owner-aware services | Сохранить ownership, сделать token-context policy явной |
| Backend `/scenario` — 3 handlers | User, scope, `ensure_character_owner`; DTO extra forbidden | Owner/state/allowed scenario transition |
| Backend `/game-session` — 5 handlers | User/scope; dev-reset дополнительно key/debug | Owner/session policy; loot transaction/idempotency — пересечение A05 |
| Backend `/game-lobby` — 14 handlers | Внутренние key-gated и user-authenticated compatibility routes | Site identity для selection, ownership, session lock; контракт refresh/revocation |
| Backend `/exploration` — 5 handlers | Gateway dependency без actor identity | Backend auth + owner; внешняя публикация отдельно не доказана — A07-13 |
| Backend `/game/catalog/*` | Bootstrap требует user; public catalog views явно открыты | Отделить публичные projections от runtime/admin data; само отсутствие auth у публичного каталога не дефект |
| `/api/dev/rift/*`, hex test — 11 handlers | Условное включение `enable_dev_rift_routes` | Только изолированное dev окружение; A07-15 |
| `/chat/history/*`, `/chat/dm/*` — 4 business handlers | Bearer token, частичная привязка к пользователю | Membership before history/hydration; A07-06 |
| `/ws/realtime` | Game token, Origin, session lock на handshake | Signed actor везде, channel/membership policy, lifetime control; A07-07/08/16 |
| Legacy `/ws/chat` | В nginx есть location; действующий WS handler в исследованном дереве не найден | Не считать второй действующий auth boundary только из-за proxy location |
| Studio `/admin/*`, `/studio/source` | Динамические Cabinet routes, source cookie | Local access control + enforced read-only; A07-12 |
| Generated assets / static | StaticFiles либо нормализованный key и configured S3 endpoint | Фиксированная asset root, безопасные MIME/контент; нет установленного public upload API |
| Telegram bot | Telegram command/community/news integrations | Telegram identity/адресат; административные публикации и event payload отдельно от game identity |

Источники подключения: `src/backend/app.py:43–72`, `src/frontend/app.py:181–212`, `src/frontend/core/routing.py`, `src/backend/chat/app.py`, `src/studio/app.py:137–147`, `src/fastapi_cabinet/site.py:27–58`. Nginx-шаблон: `deploy/nginx/site.conf.template:120–131,142–173,260–271,282–313`.

**Важное различие:** backend `/exploration`, `/scenario`, `/game-session` не имеют `/api/` prefix. Нельзя автоматически переносить на них вывод о публичной маршрутизации всех `/api/`; в шаблоне остальные пути идут frontend. Прямой backend ingress и иные proxy configurations не проверены.

## 4. Authentication/session security

Пароли хешируются общим `src/shared/security/passwords.py:15–48`: PBKDF2-HMAC-SHA256, 390 000 итераций, случайная соль 16 bytes, constant-time comparison. Это подтверждение реализации, не оценка актуального стандарта стойкости. Login использует dummy hash для отсутствующего пользователя и проверяет `is_active` (`site_auth_service.py:18,66–70`). UserCreate не предоставляет клиенту поле superuser; credential material в отчёт не включён.

Site access проверяется через AuthX с проверкой типа токена. Game decoder отдельно проверяет подпись, HS256, `aud`, `token_type`, `exp` (`src/backend/core/game_auth.py:165–194`). При подключённом lock manager проверяется текущий `session_id`; game refresh также проверяет lock (`game_lobby/api/router.py:168–187`). Проверки `iss` в game decoder нет; независимого нарушения issuer boundary не установлено. Общий backend `get_current_user` допускает также site token, что создаёт A07-11; это отдельная policy-проблема, а не доказательство обхода криптографической подписи.

Site/game cookies: `HttpOnly`, `SameSite=Lax`, Secure определяется настройкой, domain настраиваемый (`auth_service.py:77–96`; `game_features/session/token_state.py:31–51`). Production Secure/domain и секреты не читались. Нельзя считать локальные значения доказательством боевой конфигурации.

Site refresh хранится сервером, проверяет срок и активность пользователя; rotation выполняется при приближении срока. Два commits и параллельная rotation уже отражены в **A05-12**. Новый подтверждённый security impact самой гонки rotation не установлен; номер не дублируется. Stateless access JWT не отзывается автоматически удалением refresh. Отдельные lifecycle defects: существующая access identity не проверяет inactive status (A07-09), browser logout не завершает game credentials/session (A07-10).

Модель email verification token существует (`frontend/features/auth/models/email_verification.py:12`), но завершённый verify/reset-password workflow и обязательная проверка verified status в исследованном auth API не установлены. Это незавершённая функциональная политика, не автоматически уязвимость. Password reset token security не объявляется проверенной.

## 5. Authorization/IDOR

| Identifier | Источник / проверенное использование | Результат |
| --- | --- | --- |
| `user_id` | Site lookup и internal lobby/admin DTO | На key-gated endpoints доверяется сервису; game JWT sub не равен admin permission |
| `char_id` | Path/query/body большинства game routes | Inventory/Scenario ownership есть; Combat/Rift нет identity gate; WS имеет конфликт источников |
| `combat_id`, `session_id` | Diagnostics, combat analytics, chat thread history | Diagnostics не авторизованы; DM messages не сверяют membership |
| `rift_id`, `run_id`, `travel_id` | Runtime context и job/report routes | Проверки связи runtime не заменяют owner; simulation runs — административные объекты без gate |
| `item_id` | Inventory session/layout и catalog | Ownership персонажа проверяется; проверка active game context неполна. Сам по себе item ID не доказал cross-user transfer |
| `corpse_ids` | Loot claim DTO и worker | Требуют location/entitlement и атомарного claim contract; прежние A05-01/02 сохраняются без нового проверенного сценария |
| `task_id` | AI task status | Task lookup без administrative gate — часть A07-03 |
| `thread_id` / DM `session_id` | Chat index/history repositories | Нет caller-membership filter — A07-06 |
| `message_id` | Возвращаемая история | Отдельный public mutation endpoint сообщения не установлен; нельзя приписывать ему IDOR без такого входа |

Наличие отрицательной проверки владельца на одном endpoint не распространяется на соседние routes. Dependencies в Combat/Rift/analytics собирают сервисы и хранилища; они не являются скрытым источником authenticated principal (`combat/dependencies.py:23–66`, `rift/dependencies.py:91–116`).

## 6. Game-state integrity

Combat runtime сохраняет собственные проверки состояния, actor/target/action validity. Однако HTTP adapter не устанавливает пользователя, от имени которого вызван runtime (A07-01). Исправление только формулы или target validation не устраняет эту границу.

В обычном player Rift API используются DTO/runtime с `force_event`, `resolve_transition_combat` и `payload.attributes` (A07-05). Серверное решение о случайном событии, исходе переходного боя и характеристиках должно формироваться авторитетным runtime. Проверка `resolve_node_event` для текущего node combat уже есть — её нельзя представлять отсутствующей. Управление transition event также не означает управление всеми событиями node-entry.

Rift leave/complete содержит exit policy и objective checks (`player_service.py:104–128`), но не caller ownership. Последовательный completion и конкурентное двойное начисление — разные свойства: второе остаётся риском, связанным с A03-11/A04/A05. Inventory проверяет владение предметным контекстом, но допускает отсутствие active-character state (A07-11). Arena DTO/gateway не равны произвольной передаче клиентом результата боя; такой отдельный дефект не установлен.

Loot/resource consistency подробно зафиксирована в A05-01/02. Вновь прочитанный claim worker подтверждает, что эти инварианты требуют исправления, но результат persistence-аудита не переименован в подтверждённый security exploit. Прямой доступ к Redis или возможность произвольной отправки worker payload извне не предполагаются.

## 7. API/WebSocket security

Browser unsafe requests покрыты `CsrfMiddleware` (`frontend/app.py:208`; `frontend/core/csrf.py:16–24,130–147`). Исключение `/auth/*` само по себе не доказало CSRF: соответствующие JSON handlers используют явный bearer/refresh в body. Backend missing auth нельзя компенсировать frontend CSRF. В Studio нет аналогичной защиты и нет пользовательской auth boundary.

WebSocket проверяет точное совпадение Origin с configured allowlist, отсутствие Origin отвергается; cookie token имеет приоритет перед query fallback (`realtime/api/ws.py:68–76,98–133`). Это полезная защита браузерного handshake. Она не заменяет channel permissions. Для `player.notice` используются подписанные claims, поэтому **чтение чужих player notifications через URL `char_id` не подтверждено**; A07-08 касается chat bootstrap/zone и reverse mapping.

DTO ограничивает текст сообщения 500 символами; ограничение применяется после разбора envelope. В receive loop не найдено повторной проверки token expiry/session lock, а также прикладного rate limit. Реальные max frame size, upstream limits, активный nginx rate limiting, connection quotas не проверены. Это A07-16, без утверждения о доказанном отказе в обслуживании.

Query fallback для WS token увеличивает требования к redaction URL в access logs. Фактического журнала с credential не читали. Ошибки и debug payloads рассматриваются только как статическая поверхность; реальной утечки секретов через logs не заявляется. Глобальная permissive CORS policy в исследованных application entrypoints не установлена; отсутствие CORS вообще не является auth gate для прямого HTTP-клиента.

## 8. Injection/XSS/SSRF/file security

Поиск опасных sinks использовался как навигация, а не список CWE. В проверенной chat-ветке ORM строит выражения SQLAlchemy, Mongo collection/body references берутся из серверного индекса, клиентский текст выводится Alpine `x-text` (`chat/repositories/message_repo.py:36–49,111–126`; `chat/api/router.py:112–139`; `frontend/templates/shared/chat/main.html:928–1053`). Подтверждённая проблема этой ветки — права, а не SQL/Mongo injection или chat XSS.

Generated assets: key нормализуется, запрещаются родительские компоненты; local fallback проверяет resolved path относительно root; S3 destination формируется из configuration, bucket и нормализованного key (`frontend/integrations/generated_assets.py:68–86,127–139`). Общий local mount использует StaticFiles. Наличие file-serving route не доказывает path traversal. Публичный upload endpoint в исследованных handlers не установлен; отдельный upload scanner не выполнялся.

Оставлены на отдельную content-boundary проверку: `scenario.text|scenario_rich_text|safe` (`frontend/templates/game/domains/scenario/viewport/main.html:59`) и `innerHTML` в dev hex UI (`frontend/templates/game/test_hex_rift.html:565,602`). Фильтр в `frontend/app.py` добавляет разметку, но не является HTML sanitizer. Полный источник внешнего неадминистративного ввода до этих sinks не установлен; это A07-17, **не подтверждённая XSS**. Не каждый `innerHTML` опасен: часть получает собственные templates, escaped markup или константы.

Сетевые providers используют серверную конфигурацию; не установлен публичный произвольный URL input, непосредственно управляющий outbound request. Нет подтверждённых SSRF, command injection, Python eval injection, unsafe deserialization в исследованных внешних ветках. Redis `.eval` здесь используется для серверных Lua scripts и не является автоматически исполнением клиентского кода. Вендорские JavaScript eval/DOM calls не классифицированы без проверки собственного source/sink. Зависимости и CVE отдельно не аудировались.

## 9. Admin/Cabinet/Studio

Frontend `/admin` действительно закрыт для non-superuser (`features/cabinet/middleware/admin_auth.py:15–23`); app подключает middleware на site surface. Backend `/api/admin` — отдельное пространство маршрутов: middleware frontend его не защищает. `admin_players` использует внутренний ключ; monsters/generation/combat-ai/config такой проверки не имеют. Защитный контракт должен применяться на backend независимо от того, где находится пользовательская форма.

`fastapi_cabinet/site.py:27–58` собирает modules/actions без вызова permission provider. Наличие `AllowAllPermissionProvider`, sidebar permission metadata или скрытой кнопки не является выполненной server authorization. Для production frontend это компенсировано внешним superuser middleware, для Studio — нет.

Studio skill требует read-only для выбранного источника. Существующий reference содержит более старое описание local heavy compute; ни оно, ни имя `PROD READ-ONLY` не заменяют программный запрет. HTTP actions Studio вызывают backend mutators независимо от `source.kind`, среди них simulation/report clearing, training и content regeneration/rebuild. Postgres read-only role, даже если действительно настроена, не защищает HTTP backend writes. Redis registry создаёт обычный клиент; фактическая ACL не проверена (`studio/features/sources/postgres_readonly.py:38–49`; `redis_readonly.py:35–45`).

Studio не найдена в production compose, но dev compose публикует `9100:9100` и запускает сервер на `0.0.0.0` (`deploy/docker-compose.yml:274–306`). Это не доказывает доступ из интернета: host firewall/сеть неизвестны. Требуется локальная изоляция и собственная авторизация, а read-only source должна применяться к operations до обращения к backend (A07-12).

## 10. Workers и event trust

Проверены контракты upstream API, которые создают generation/simulation и игровые задания, а также обсуждённые в A03–A05 reward/loot flows. **Service DTO, пришедший через защищённый транспорт, всё равно требует бизнес-проверки.** Для очередей важны actor identity, право на операцию, state version и idempotency key, а не только Pydantic shape.

Подтверждённый пробел на входе: administrative AI handlers создают/коммитят задания и передают их планировщику без установленного admin principal (`generation_ai/api.py:31–57`; `combat/api/ai_simulation_router.py:135–185`). Worker не может восстановить отсутствующее решение об авторизации. Требуется закрыть producer API и передавать минимальный verified command; повторное чтение authoritative state особенно важно для наград, ownership и уже завершённых операций.

Loot worker применяет resource deltas и условную idempotency policy (`loot/workers/tasks/loot_claim_task.py:195–273`); это подтверждение актуальности A05-01, не доказательство нового публичного пути. Combat finalization replay/XP, Streams pending recovery, Rift completion concurrency остаются связаны с предыдущими аудитами. Без завершённой проверки входной policy нельзя считать любой внутренний event доступным пользователю.

Telegram community feed принимает сообщения Telegram и публикует внутреннее событие (`tg_bot/features/telegram/community_feed/logic/orchestrator.py:24–83`); соответствующий downstream consumer с изменением game state в исследованном коде не установлен. News HTML создаётся из административных новостей. Отдельной установленной смены actor/user identity через Telegram не найдено; это ограниченная проверка, не аттестация всей внешней Telegram конфигурации.

## 11. Выполненные проверки

1. Прочитаны задание, AGENTS.md, `cost-aware-delegation`, `security-review` и применимые project skills backend/quality/studio; профильные Combat/Rift/frontend references использовались при распределённой проверке. Навигация по audit 01–05 сверялась с текущими исходниками, не принималась как доказательство.
2. Статически сопоставлены application mounts, router prefixes, handler dependencies, middleware и Nginx-шаблон. AST-проход по Python-исходникам завершился успешно и дал числа §3; application modules для этого не импортировались.
3. Для A07-01–13 проверены конкретные route/service contracts. Основные результаты помощников перепроверены ведущим чтением соответствующих router/auth/runtime/chat/Studio файлов. Production reachability не выводилась только из названия маршрута.
4. Статически изучены security tests: `tests/backend/core/test_game_auth.py`, `test_auth_session_replaced.py`, `tests/frontend/core/test_csrf.py`, `test_security_headers.py`, `tests/backend/realtime/test_ws_handler.py`, `test_chat_bridge.py`, Rift router tests и simulation admin tests. Наличие тестов и их assertions подтверждено, **pytest в этом аудите не запускался**.
5. До уточнения режима были начаты ограниченные in-process проверки с подменой хранилищ. Основная TestClient-проверка остановлена до результата; два импортных probe помощника также остановлены. Они не дали доказательств HTTP-поведения. Один завершившийся до уточнения безсетевой DTO/parser probe лишь подтвердил принятие существующей формы chat DTO; он не считается воспроизведением уязвимости. После уточнения выполнялись только чтение/AST-анализ и подготовка отчёта.
6. Не запускались production app lifespan, нагрузочные/конкурентные проверки, реальные DB/Redis/ARQ операции, публикации, провайдеры, удалённые scanners или внешние HTTP-проверки. Исправления, тестовые файлы, конфигурации, credentials, migrations и skills не изменялись; единственный намеренно созданный артефакт — этот отчёт.

Наблюдаемая проблема запуска локального probe не трактуется как дефект приложения. Ранее изменённые пользователем файлы не очищались, git configuration не изменялась; для read-only Git использовалась process-local `safe.directory` настройка.

## 12. Подтверждённые дефекты

Статус **«подтверждённая ветка кода»** означает непосредственно установленный отсутствующий gate или неверный контракт; он не означает успешную эксплуатацию или наблюдаемую production-утечку. Указанные tests — критерии будущего исправления, не новые выполненные тесты. Severity не зависит от доступности реальных пользовательских данных: все дефекты можно проверять на синтетических fixtures.

### A07-01 — High — Combat и Rift player API не устанавливают пользователя и владельца

- **Класс:** CWE-306 / CWE-862, broken access control. Поверхность alpha; Rift experimental runtime. Требуемые route-привилегии сейчас отсутствуют; предусмотрены игрок, owner и участник текущего runtime.
- **Входы/контракт:** Combat view/snapshot/logs/moves/feints/result и Rift view/leave/travel/action/complete используют path `char_id`. Path идентификатор используется как actor selector без связывания с authenticated principal.
- **Доказательства:** `src/backend/features/combat/api/router.py:26–139`; `combat/dependencies.py:23–50`; `combat/services/session_service.py:143–166,188–204`; `src/backend/features/rift/api/router.py:31–97`; `rift/dependencies.py:91–116`; `rift/services/player_service.py:89–101,130–157`. Backend registration `app.py:64,68`, middleware `:47–49` не добавляют auth gate.
- **Нарушение/последствия:** граница request → owner-controlled character state отсутствует. Данные и изменения боевого/Rift состояния не ограничены правом вызывающего. Бизнес-проверки существования runtime не заменяют ownership.
- **Статус/условия:** подтверждённая ветка кода, высокая уверенность. Требуются доступность backend route и существующий runtime; публикация `/api/` предусмотрена шаблоном. Реальная production доступность неизвестна. Реальные данные для проверки не нужны; влияет на текущие игровые тесты; блокер публичной beta.
- **Минимальная защита:** обязательный game access dependency, selected-character scope, owner/membership query до чтения/мутации; единственная policy для всех siblings.
- **Regression criteria:** анонимный, неверный token context, другой owner, несоответствующий selected character отклоняются до service/storage; корректный owner сохраняет штатные действия.

### A07-02 — High — Runtime config API не требует административного права

- **Класс:** CWE-306 / CWE-862. Поверхность shared/alpha; запросы не требуют identity, хотя intended роль — admin/internal config service.
- **Входы:** `/api/internal/config` и namespace/key operations; клиентские namespace, key, value.
- **Доказательства:** `src/backend/features/game_config/api/router.py:6–64`; `src/backend/infrastructure/game_config/manager.py:162–186`; `src/backend/app.py:53`. `set` проверяет зарегистрированный key/value и записывает Redis; auth проверок нет.
- **Нарушение/последствия:** право менять общую конфигурацию не отделено от обычного HTTP-доступа. Возможны несанкционированные изменения разрешённых параметров/сброс overrides; это не произвольная Redis key injection.
- **Статус/условия:** подтверждённая ветка кода, высокая уверенность; нужен работающий manager и доступ к route. Production ingress не проверен. Реальные данные не нужны; может менять результаты текущих тестов; beta blocker.
- **Минимальная защита:** mandatory config read/write policy, узкая service identity, аудит изменений; исключение internal prefix из public ingress как дополнительный слой.
- **Regression criteria:** отсутствие/неподходящее полномочие не вызывает manager; только authorised config writer меняет валидные значения; неизвестные keys и неверные values по-прежнему отклоняются.

### A07-03 — High — Administrative generation/content/simulation API без auth gate

- **Класс:** CWE-306 / CWE-862. Поверхность shared/alpha + experimental AI simulation; admin prefix не ограничивает доступ.
- **Входы:** `/api/admin/monsters`, `/api/admin/generation-ai`, `/api/admin/combat-ai`; content IDs, `task_id`, `run_id`, generation/simulation parameters.
- **Доказательства:** `generation_ai/api.py:23–70`; `monsters/api/router.py:24–150`; `monsters/services/generated_rebuild_service.py:47–49,223`; `combat/api/ai_simulation_router.py:35–185`; `combat/services/ai_simulation_service.py:64`; `infrastructure/combat/repositories/ai_simulation_repository.py:141–149`; `backend/app.py:54,56,67`. Gates отсутствуют и на router, и на include, и в просмотренных service constructors.
- **Нарушение/последствия:** право создавать затратные служебные задания, перестраивать content и очищать simulation reports не привязано к admin principal. Task/status и content details также читаются без такой policy. Наличие лимита размера batch не устраняет отсутствие разрешения.
- **Статус/условия:** подтверждённые ветки кода, высокая уверенность. Для выполнения конкретных операций нужны соответствующие DB/queue/providers; отсутствие запущенного worker не защищает read/delete handlers. Стоимость и доступность production providers неизвестны. Реальные пользовательские данные не нужны; влияет на тестовый контент/ресурсы; beta blocker.
- **Минимальная защита:** единый fail-closed admin/service dependency плюс permissions на generation, rebuild, report maintenance; task visibility; bounded jobs и audit actor.
- **Regression criteria:** без права не вызываются DB mutations/enqueue/provider; read/status требуют appropriate permission; admin_players key gate остаётся работающим.

### A07-04 — Medium — Internal session diagnostics и combat analytics без доступа по роли

- **Класс:** CWE-862 / CWE-200. Поверхность shared/alpha diagnostics. Caller identity отсутствует.
- **Входы:** `/api/internal/combat/sessions`, scenario/exploration sessions, `/api/game/combat/analytics/*`; session/combat ID, filters, pagination.
- **Доказательства:** `combat/api/internal_router.py:27–57`; `scenario/api/internal_router.py:10–12`; `exploration/api/internal_router.py:10–12`; `infrastructure/scenario/managers/session_manager.py:79–107`; `infrastructure/exploration/managers/session_manager.py:51–77`; `combat/api/analytics_router.py:21–137`; `combat/dependencies.py:53–66`; `combat/services/analytics_dashboard_service.py:224–237` (`raw_debug`).
- **Нарушение/последствия:** internal runtime metadata, character/session identifiers и сырая аналитика не отделены от public API. Analytics backfill также выполняет служебную операцию без write permission. Наличие пользовательских secrets в этих ответах не утверждается.
- **Статус/условия:** подтверждённая ветка кода, высокая уверенность; наличие соответствующих session/analytics records и route access. Production данные не читались. Для проверки достаточно fixtures; влияет на конфиденциальность текущих тестов; beta blocker.
- **Минимальная защита:** administrative/internal read gate, отдельный backfill permission, минимальные projections, отсутствие raw debug в публичном API.
- **Regression criteria:** список, detail, filters, drilldown и backfill последовательно применяют одну policy; неизвестный ID не раскрывает чужой объект; user principal не получает internal metadata.

### A07-05 — High — Player Rift DTO допускает клиентское управление серверными решениями

- **Класс:** CWE-602 / CWE-841. Поверхность experimental runtime, подключённый к player API; не ограничивается dev router. Независим от A07-01: остаётся проблемой после добавления login/owner gate.
- **Недоверенные поля:** `force_event`, action type `resolve_transition_combat`, result и `payload.attributes`. Они предназначены для серверных решений/diagnostics, но находятся в player contracts.
- **Доказательства:** `rift/dto/runtime.py:17–19`; `rift/api/router.py:64–87`; `rift/services/player_service.py:64–101`; `rift/runtime/actions/dispatcher.py:46–62,104–205`; `rift/runtime/navigation/screen_builder.py:233–261,608–645,772–785`.
- **Нарушение/последствия:** выбор transition event, разрешение переходного боя и значения характеристик могут определяться недоверенным DTO вместо server state. Нарушается целостность прохождения и проверки препятствий. Нет доказательства возможности изменять постоянные базовые характеристики персонажа через это поле.
- **Уточнение:** `player_service.py:96–97` блокирует прямое завершение текущего node combat; transition и node-entry — разные механизмы. Находка не утверждает отсутствие всех проверок события.
- **Статус/условия:** подтверждённая ветка кода, высокая уверенность; требуется соответствующее активное состояние Rift. Не предполагает реальные данные; влияет на игровые тесты; blocker для beta с этой системой.
- **Минимальная защита:** отдельный player command DTO с allowlist; результат боя только от authoritative combat service, attributes только из snapshot; диагностические overrides изолировать в dev API.
- **Regression criteria:** player DTO не принимает серверные outcome/attribute overrides; переход завершается только от проверенного combat result; исходные node guards сохраняются. Пересечение **A04-01**, новый вывод — security classification и проверка player-route границы, а не новый независимый дефект.

### A07-06 — High — История приватных чатов не проверяет членство

- **Класс:** CWE-639 / CWE-862. Поверхность alpha chat. Нужен действительный site bearer token; одного login недостаточно для private thread.
- **Входы:** history по channel/scope и DM messages по session UUID; поля выбирают thread, но caller identity не используется в access decision.
- **Доказательства:** `src/backend/chat/api/router.py:16–47,88–98`; `src/backend/chat/repositories/message_repo.py:36–49,111–126`. В handlers authenticated dependency сохраняется в `_char_id`, затем не участвует в проверке membership перед SQL/Mongo hydration.
- **Нарушение/последствия:** приватная история и системные/group области не защищены принадлежностью к conversation. Глобальные общедоступные каналы должны иметь отдельную явную policy, а не общий запрет/разрешение.
- **Статус/условия:** подтверждённая ветка кода, высокая уверенность; нужны существующий private thread и соответствующий identifier. Production history не читалась. Fixtures достаточны; влияет на тестовые переписки; beta blocker.
- **Минимальная защита:** единый resolver thread access с membership/recipient/location policy до загрузки индексов и bodies; actor ID из verified identity.
- **Regression criteria:** nonmember, inactive member и чужой system recipient получают отказ; member получает только допустимую историю; list/detail/hydration соблюдают одну policy.

### A07-07 — High — Chat send не проверяет разрешённый канал и scope

- **Класс:** CWE-862 / CWE-863. Поверхность alpha realtime/chat; нужен действительный game token и принятый handshake.
- **Контракт:** клиент определяет `channel`/`scope_id`; shape validation допускает служебные/private каналы, но permission check не выполняется.
- **Доказательства:** `src/backend/realtime/dto/envelope.py:20–29`; `realtime/api/ws.py:325`; `realtime/services/chat_bridge.py:78–91`; `src/backend/chat/services/message_service.py:13–42`.
- **Нарушение/последствия:** обычный message input не отделён от права отправлять в system/private/group scope. Адресация, сохранение и публикация могут не соответствовать членству отправителя; фактическая live доставка зависит от существующих подписок. Sender identity остаётся подписанной — не утверждается произвольная замена JWT sub.
- **Статус/условия:** подтверждённая ветка кода, высокая уверенность; требуется работающий chat/realtime. Проверка parser не является доказательством доставки. Реальные данные не нужны; влияет на текущие чаты; beta blocker.
- **Минимальная защита:** server-owned system publisher; allowlist пользовательских каналов; scope из server session либо явный membership check; одинаковая policy для live broadcast и archive.
- **Regression criteria:** игрок не публикует в служебный канал; nonmember не пишет в private/group scope; current zone и membership проверяются до buffer/broadcast; длина текста остаётся ограниченной.

### A07-08 — Medium — WebSocket chat bootstrap не связывает URL character ID с claims

- **Класс:** CWE-863 / CWE-639. Поверхность alpha realtime; валидный game token нужен.
- **Контракт:** verified `claims.character_id` используется для lock/connection; отдельный URL `char_id` используется для actor name/location и reverse map.
- **Доказательства:** `realtime/api/ws.py:87–91,123–169`; корректная notice адресация — `realtime/services/connection_manager.py:39–70`, `notice_service.py:45–80`.
- **Нарушение/последствия:** session chat metadata/zone subscriptions могут не соответствовать подписанному actor. Reverse mapping также не имеет единого identity source. Чужие `player.notice` этим расхождением не подтверждены.
- **Статус/условия:** подтверждённая ветка кода, высокая уверенность; наличие active actor metadata и соответствующего chat state. Реальные данные не нужны; может влиять на зонные чаты и корректность identity в тестах; beta blocker.
- **Минимальная защита:** убрать отдельный actor selector либо отвергать несовпадение; все bootstrap reads и mappings из verified claims.
- **Regression criteria:** mismatched URL ID не влияет на sender name/location/topics/map; notices и reconnect остаются привязаны к claims.

### A07-09 — Medium — Деактивация учётной записи не применяется ко всем действующим сессиям

- **Класс:** CWE-613 / CWE-863. Поверхность shared site/game; ранее выданная сессия деактивированного пользователя.
- **Доказательства:** login/refresh gate `site_auth_service.py:66–70,107–111`; existing access lookup `auth_service.py:103–108`; bearer lookup `auth/dependencies/providers.py:50–64`; backend identity `core/auth.py:20–38` устанавливает active без site lookup; game refresh `game_lobby/api/router.py:168–187` проверяет session lock, не account status.
- **Нарушение/последствия:** административное отключение аккаунта не имеет общей немедленной силы для existing access/game session. Доступ ограничивается сроком/lock, но не самим изменением `is_active`.
- **Статус/условия:** подтверждённая ветка кода, высокая уверенность; нужен access/game session, выданный до отключения. Конкретный production TTL и внешнее принудительное освобождение lock не проверены. Синтетических пользователей достаточно; важно для тестовой модерации; beta blocker.
- **Минимальная защита:** единая active/revocation policy, session version/revocation event либо authoritative lookup с определённой задержкой; отключение связанных game locks и WS sessions.
- **Regression criteria:** disable после выдачи credentials блокирует site lookup, refresh, game action и продление session в установленный срок; активный пользователь работает штатно.

### A07-10 — Medium — Browser logout не завершает game session

- **Класс:** CWE-613. Поверхность shared site/play; ранее вошедший браузер с активной game session.
- **Доказательства:** `frontend/features/auth/routes/pages.py:137–150` очищает site и active-character cookie, не game token cookies; `game_features/session/token_state.py:31–51`; `game_features/session/middleware.py:56–98`; `game_features/rift/routes/pages.py:72–254`; backend refresh lock contract выше.
- **Нарушение/последствия:** пользовательский выход из сайта не означает завершение действующего игрового доступа. Game-cookie consumer и refresh middleware не требуют заново действующую site identity во всех путях.
- **Статус/условия:** подтверждённая ветка кода, высокая уверенность; активная game session и сохранённые cookie, соответствующие domain/path. Actual browser/domain production не тестировались. Реальные данные не нужны; влияет на exit/re-login tests; beta blocker для единого logout UX.
- **Минимальная защита:** явно определить общий logout: очистка game cookies на правильных domain/path, освобождение/revocation game session, завершение WS; если выходы раздельные, явно закрепить это в security/product contract.
- **Regression criteria:** после общего logout site/game HTTP, refresh и WS не сохраняют полномочия завершённой сессии; проверить оба host surfaces и legacy cookies.

### A07-11 — Medium — Inventory принимает site token вне выбранной game session

- **Класс:** CWE-863 / CWE-841. Поверхность alpha inventory/shared auth; валидный site token владельца персонажа.
- **Доказательства:** `backend/core/auth.py:20–38,63–68`; `inventory/api/router.py:42–54,80–83`; `inventory/services/inventory_service.py:84–112,134–154,424–431,466–467`. При отсутствии game claims scope check возвращается; отсутствие active-character state не запрещает действия; inventory session может восстанавливаться из stored items.
- **Нарушение/последствия:** owner check работает, но полномочие владельца аккаунта не отделено от права действовать текущей выбранной game session. Возможны изменения inventory собственного неактивного персонажа вне этого контракта; cross-user IDOR здесь не установлен.
- **Статус/условия:** подтверждённая ветка кода, высокая уверенность; собственный персонаж/предметы и соответствующий inventory state. Fixtures достаточны; влияет на session/state tests; beta blocker до определения обязательного game context.
- **Минимальная защита:** game-only dependency на gameplay mutations, обязательная active session, отказ при неизвестном state; site/account операции выделить отдельно.
- **Regression criteria:** site token не даёт gameplay permission; game token другого selected character отвергается; правильный owner/current character работает; owner query сохраняется.

### A07-12 — High — Studio не обеспечивает auth/read-only contract

- **Класс:** CWE-306 / CWE-862. Поверхность **dev-only Studio**, при source prod возможна работа с выбранным backend; не объявляется публичной production-уязвимостью Studio.
- **Контракт:** source cookie выбирает allowlisted source; Cabinet actions вызывают mutating backend clients без собственного auth gate и без запрета source writes.
- **Доказательства:** `studio/app.py:137–147`; `fastapi_cabinet/site.py:27–58`; `studio/features/source_selector/middleware.py:25–39`; `studio/features/cabinet/modules/combat_ai_testing/cabinet.py:1463,1510–1558`; `content_ops/cabinet.py:321–336,416–423`; `frontend/core/api.py:21–29,93–97`; `frontend/integrations/backend_api/combat_ai_testing.py:60–66` (`clear_runs/clear_training_runs`). Local publication — `deploy/docker-compose.yml:274–306`.
- **Нарушение/последствия:** аналитический локальный интерфейс не ограничен чтением и не устанавливает оператора. Labels и DB read-only role не защищают отдельный backend HTTP transport. Он также использует inherited service credentials там, где backend требует их.
- **Статус/условия:** подтверждённая ветка кода, высокая уверенность. Нужен запущенный доступный Studio; воздействие на prod source дополнительно требует работоспособного source/tunnel и backend permissions. Реальная сеть/tunnel/ACL не исследованы. Реальные данные не нужны; влияет на dev tests; blocker эксплуатации Studio рядом с live source, не самостоятельный blocker развёртывания beta без Studio.
- **Минимальная защита:** loopback publication, собственная auth/CSRF boundary, read-only backend identity и enforcement по operation/source до HTTP; remove/segregate mutating controls согласно действующему Studio contract.
- **Regression criteria:** unauthorised caller отвергается; выбранный read-only source никогда не получает write calls, включая indirect action routes; source allowlist не допускает произвольного destination.

### A07-13 — Medium — Backend Exploration не имеет actor/ownership dependency

- **Класс:** CWE-306 / CWE-862. Поверхность alpha backend integration; **публичная доступность именно этого prefix не подтверждена**.
- **Контракт/доказательства:** `src/backend/features/exploration/api/router.py:17–77` принимает `char_id` в DTO/query и вызывает gateway; `exploration/dependencies.py` `build_exploration_gateway` собирает runtime без user; `exploration/gateway/exploration_gateway.py:30–96`; `backend/app.py:72` подключает router без service identity.
- **Нарушение/последствия:** backend adapter доверяет выбранному character ID без подтверждённого пользователя или сервиса; внутренний character state не устанавливает право вызывающего. Дефект существует и для frontend-to-backend contract.
- **Статус/условия:** подтверждённая ветка кода, высокая уверенность в gate omission, ограниченная уверенность во внешней достижимости. `/exploration` в основном nginx не попадает под `/api/`; необходим доступ непосредственно к backend или иной routing. Никакой такой production ingress не проверялся. Синтетических данных достаточно; влияет на интеграционные тесты; требуется закрыть до beta либо доказать и закрепить service-only boundary.
- **Минимальная защита:** явная user/game identity+owner либо строго внутренний service contract с verified actor и deny public routing; frontend validation недостаточна.
- **Regression criteria:** router отклоняет вызовы без выбранного identity mode; чужой owner и неверный character scope не достигают gateway; тест публикации подтверждает ожидаемый ingress.

## 13. Непроверенные риски и наблюдения

| ID / severity | Основание | Что не установлено | Защитное направление и критерий проверки |
| --- | --- | --- | --- |
| **A07-14 / High, условный риск конфигурации** | Usable development defaults JWT/service key: `backend/config/settings.py:49,54–55`, `frontend/config/settings.py:30,55`; internal validator `backend/core/game_auth.py:58–69` не отвергает этот development default; compose env files optional (`deploy/compose.site.yml:39–54`, `compose.game.yml:43–55`) | Реальные production значения; отдельные secret/bootstrap controls. Значения ключей не приводятся | Fail-closed production startup при отсутствующем/known-default секрете; разные purposes/scopes. Тест startup validation без реальных credentials. Shared поверхность; beta blocker, если production действительно использует defaults |
| **A07-15 / Medium, dev exposure risk** | `enable_dev_rift_routes` default True (`backend/config/settings.py:59`), условный mount `rift/api/router.py:195–206`; hex test endpoints не имеют отдельной identity boundary | Эффективное значение production flag и действующая публикация | Default-off, запрет включения в production, access policy для dev. Tests уже проверяют выключение; нужен deployment assertion. Dev-only по назначению; не автоматически isolated по коду |
| **A07-16 / Medium, lifecycle/abuse risk** | Handshake checks есть, повторной проверки expiry/lock и прикладного rate limiting в receive loop не найдено (`realtime/api/ws.py:213–251`); query-token fallback | Живые server frame limits, proxy quotas, поведение длительных соединений, logs redaction; нет доказанного DoS или token leak | Ограниченный lifetime/renewal, session revocation, application quotas/size budgets, redaction. Проверять отдельно в изолированной среде по будущему поручению; alpha/shared |
| **A07-17 / Observation, unsafe-render sinks** | Scenario `safe` и hex UI `innerHTML`, §8 | Доступный обычному пользователю источник недоверенного HTML и влияние CSP | Определить allowed rich text, sanitizer/escaping на sink, content-provider fixtures. Не объявлять XSS без source boundary; shared/dev content |
| **A07-18 / Medium, повторное применение rewards** | Rift reward до завершения cleanup (`rift/services/player_service.py:114–128,160–205,241–248`), loot conditional idempotency; пересечения A03-01/11, A05-01/02 | Конкретный конкурентный interleaving, внешний delivery contract и реальный эффект в текущем окружении | Authoritative claim/completion transaction, idempotency для всех веток, compare-and-set/version; будущие concurrency tests. Alpha/experimental; не новый подтверждённый exploit |

Для всех строк реальные пользовательские данные не требуются. Они могут влиять на локальные/игровые тесты при выполнении указанных условий. Наличие rate-limit gap само по себе не доказывает практическую нагрузочную атаку. Наличие known development fallback не доказывает компрометацию production.

## 14. Пересечения с аудитами №2–5

| Предыдущий вывод | Независимая проверка в A07 | Решение о дублировании |
| --- | --- | --- |
| A02-01, A02-03 — storage ownership/raw runtime state | Security ownership caller и ownership storage — разные понятия. Проверены API identity gates и server contracts | Не превращены автоматически в security findings |
| A03-01 — повторное XP, A03-03/04 — runtime atomicity | Эти инварианты важны, но обычному внешнему пользователю не приписан прямой доступ к finalizer/Redis | Сохранены ссылки; A07-18 только риск |
| A03-11 — Rift completion concurrency | Completion/reward ordering остаётся существенным | Никакого нового воспроизведения или доказанного повторного начисления |
| **A04-01 — client-controlled Rift decisions** | Перепроверены реальные player routes, dependencies и dispatcher; есть и обычный API, и отдельный dev API | A07-05 — security view той же первопричины; в общем плане считать одним исправлением |
| A04-02 — default victory | Различены node guard и transition placeholder | Отражено внутри A07-05, не отдельная находка |
| A04-08 — XP cap и другие gameplay defects | Ошибка баланса не автоматически нарушение security boundary | Не повышены до уязвимостей без дополнительного основания |
| A05-01/02 — loot resource/source transfer | Read-only повторное чтение producer/worker подтверждает важность atomic entitlement | Не присвоен новый номер подтверждённой уязвимости; A07-18 |
| **A05-12 — refresh rotation** | SELECT/delete/create и concurrent rotation остаются прежней проблемой; дополнительных фактов о компрометации нет | Не дублируется. A07-09/10 — другие contracts: deactivate/logout |
| A05-05/06/07/08 — delivery и generation persistence | Потеря/повтор сообщения не означает отсутствие access control | A07-03 касается producer authorization, а не прежнего persistence failure |

## 15. Положительные security boundaries

1. **Game token decoder** проверяет подпись, алгоритм, audience, тип и expiry. Dispatch по непроверенному payload используется только для выбора decoder; actual game decoder выполняет криптографические проверки.
2. **Single-session lock** проверяется для game HTTP identity и WS handshake; game refresh не должен оживлять уже заменённую session. Отсутствие lock manager в stripped test setup не нужно переносить на production без проверки lifespan wiring.
3. **Inventory ownership** реально ограничен `(char_id, user_id)`, не UI-фильтром. Scenario вызывает `ensure_character_owner` для initialize/resume/step. Эти checks нужно сохранить при устранении token-context gaps.
4. **Admin players** последовательно требует internal service key на всех четырёх handlers. Сравнение ключа constant-time, пустой ключ не принимается. Требуется отдельно устранить риск defaults, а не убирать эту защиту.
5. **Frontend cabinet** закрыт `is_superuser` middleware, отдельно от presence sidebar/button. CSRF применяется к обычным unsafe browser forms, cookies HttpOnly/SameSite настроены в коде.
6. **WebSocket Origin** проверяется до принятия рабочей сессии; malformed/invalid/stale auth имеет отдельные rejection paths. Player notice recipients берутся из claims.
7. **Chat text rendering** в проверенном основном UI использует `x-text`; message DTO ограничивает длину. SQL/Mongo history получает typed server references. Это снижает injection surface, но не компенсирует membership gap.
8. **Rift exit/node safeguards** проверяют exit policy, objective и node combat completion; утверждение «Rift вообще ничего не проверяет» неверно. Server result callback дополнительно проверяет active encounter/combat mismatch (`rift/integrations/runtime.py:410`).
9. **Generated assets** имеют нормализацию keys/root containment и configured destinations. Source switcher Studio допускает только `local`/`prod`, а не произвольный URL.
10. **Тестовые заготовки** уже покрывают token type/audience/expiry, неверный service key, CSRF и Origin/stale handshake. Их можно расширить route-level deny cases; наличие этих тестов не доказывает подключение dependency ко всем routes.

## 16. Реестр находок

Здесь «код» — статически подтверждённый дефект, «риск» — условный или недостаточно проверенный эффект. Для High/Critical не используются недоказанные утверждения об успешной эксплуатации.

| ID | Severity | Статус | Поверхность | Нарушенная граница | Beta / требуемое решение |
| --- | --- | --- | --- | --- | --- |
| A07-01 | High | Код | alpha/experimental | Request → владелец Combat/Rift | Blocker: обязательный game principal/owner |
| A07-02 | High | Код | shared/alpha | Public API → live config | Blocker: admin/service policy |
| A07-03 | High | Код | shared/experimental | Request → privileged jobs/content | Blocker: permission до DB/queue |
| A07-04 | Medium | Код | shared/alpha | Public → internal analytics/session data | Blocker: restricted projections/roles |
| A07-05 | High | Код, пересечение A04-01 | experimental player runtime | Player DTO → server outcome/attributes | Blocker для Rift: authoritative commands |
| A07-06 | High | Код | alpha chat | Login → private conversation | Blocker: membership resolver |
| A07-07 | High | Код | alpha realtime/chat | Player message → privileged/private channel | Blocker: channel/scope permission |
| A07-08 | Medium | Код | alpha realtime | Claims actor → chat bootstrap actor | Blocker: единый identity source |
| A07-09 | Medium | Код | shared | Disabled account → existing sessions | Blocker: active/revocation contract |
| A07-10 | Medium | Код | shared site/play | Logout → game credentials | Blocker для общего logout contract |
| A07-11 | Medium | Код | alpha inventory | Site identity → selected game actor | Blocker: game-only mutation policy |
| A07-12 | High | Код, dev-only | Studio | Analytical/read-only → backend writes | Blocker Studio у live source; не доказанная public prod surface |
| A07-13 | Medium | Код, ingress неизвестен | backend integration | Caller → Exploration actor | Закрыть backend boundary, закрепить ingress |
| A07-14 | High | Условный config risk | shared | Environment → signing/service trust | Blocker при defaults; production неизвестен |
| A07-15 | Medium | Config/dev exposure risk | dev-only | Dev feature → published routes | Default-off + production assertion |
| A07-16 | Medium | Lifecycle/abuse risk | shared realtime | Handshake → long-lived authority | Lifetime/quotas/log policy |
| A07-17 | Observation | Source boundary не установлена | content/dev | Data → executable markup | Content policy; не confirmed XSS |
| A07-18 | Medium | Concurrency risk, пересечения | alpha/experimental | Repeated delivery → rewards | Idempotent transaction; прежние A03/A05 |

**Точная сводка confirmed:** 13 строк A07-01–13, **7 High и 6 Medium**. Высокая severity A07-12 относится к техническому нарушению Studio при выполнении условий доступности, а не к утверждению о её production-развёртывании.

## 17. Ограничения исследования

- Итоговая доказательная база статическая. Нет successful exploit claims, runtime authorization certification, production incident statements или доказанного ущерба. Описания дефектов не являются инструкциями обхода.
- Шаблон deployment показывает предусмотренное routing, но не running configuration. Не читались реальные env/credentials, firewall, reverse proxy state, tunnel, Mongo/Redis ACL, cloud permissions или production logs. Полный infrastructure audit остаётся №8.
- Рабочее дерево уже содержало множество изменений; line anchors могут сдвинуться при последующей работе. Report ссылается на прочитанное состояние 09.10.2026, а не на clean baseline.
- AST-инвентарь охватывает объявления; динамические Cabinet registration, conditional mounts и middleware проверялись дополнительно вручную. Это не гарантия полного runtime route graph. Не утверждается построчный аудит каждого из 202 объявлений handlers frontend/backend features и всех workers.
- Основная глубина — authentication, API authorization, game DTO, chat/WS и Studio. Content rendering, Telegram и outbound providers исследованы выборочно; отсутствие доказанной injection не означает отсутствие любых injection defects.
- Не запускались полный suite, dependency advisory scanner и нагрузочные/concurrency проверки. Existing tests прочитаны, но их зелёный статус не заявляется. Проверка password strength относительно текущих рекомендаций и внешних CVE не проводилась.
- В безопасном static режиме severity основана на code effect и необходимых условиях. Неизвестный публичный ingress особенно оговорён для Exploration и Studio. Реальные пользовательские данные для дальнейших regression checks не требуются.
- Production code, tests, settings, credentials, migrations и skills оставлены без намеренных изменений. Обнаруженные несоответствия guidance — в частности Studio read-only и стадия Rift — зафиксированы; навыки не актуализировались в рамках запрета пользователя.

### Application Security Health Summary

| Область | Оценка | Основание |
| --- | --- | --- |
| Authentication | Частично выстроена; lifecycle неполон | Подпись/type/audience/expiry есть; inactive/logout/default-key policy требует работы |
| Authorization | Не готова к публичной beta | Несколько подключённых player/admin/internal API без обязательных gates |
| Game-state integrity | Существенные дефекты | Rift player contracts доверяют outcome/attributes; selected session policy неполна |
| API security | Неоднородна | Frontend CSRF и owner checks работают, backend sibling routes остаются вне общей policy |
| WebSocket security | Сильный handshake, неполные permissions | Origin/game session checks есть; chat scope и actor binding нарушены |
| Input validation | Есть shape/type constraints, не хватает semantic validation | Typed DTO не устанавливает membership или серверность результата; XSS/SSRF не подтверждены |
| Admin isolation | Недостаточна | Cabinet superuser gate не защищает отдельно подключённый backend admin API; Studio не enforced read-only |
| Worker trust | Зависит от незавершённых producer boundaries | Очередь не заменяет авторизацию; reward/idempotency остаются вопросами A03–A05 |
| Security test readiness | Хорошая база unit checks, недостаёт route matrix | Нужны anonymous/nonowner/wrong-context/admin-scope tests на фактическом mounted app; suite в A07 не запускался |

Отчёт пригоден для независимого review перечисленных code contracts и последующего единого плана после серии аудитов. Готовность production к публичному доступу этим исследованием не подтверждена.
