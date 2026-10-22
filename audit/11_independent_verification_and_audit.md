# 11. Независимая верификация аудита Астры и дополнительный технический аудит (Antigravity)

> **Шаг 1, 19.10.2026:** оставшиеся privileged config/GenerationAI/simulation
> API получили backend read/write gates; 287 адресных тестов прошли.
> Статусы A07-02/03 и доказательства — в [реестре 10](10_findings_registry.md#шаг-1-технической-очереди--19102026).

## Текущий прогресс технических исправлений — 20.10.2026

- [x] Шаги 1–4: privileged API, миграции сайта, защита логов/метрик,
  жизненный цикл сессий и WebSocket — исправлены в заявленных границах.
- [x] Шаг 5: A08-12, A06-12/05/06/09, A08-09/10 и локальная часть A08-11.
- [x] Реальные GitHub main/production rules настроены и независимо проверены.
- [ ] Публикация workflow с production environment отложена до выпуска;
  перенос секретов и hosted runtime проверка остаются открытыми.
- [x] Шаг 6, транспортная часть A05-05: PEL quarantine без replay независимо
  проверен. Доменное восстановление и ограничение роста retention не закрыты.
- [x] Шаг 7.1, A04-11: согласован сохранённый лимит повторов GenerationAI;
  52 tests passed, включая 11 isolated PostgreSQL cases; независимый review.
- [x] Шаг7.2: не-item генеративный AI выведен в archive с проверкой48hash;
  оставлен items.text JSON. Маскоты и статическая генерация мира сохранены.
- [x] Шаг7.3 A04-12/A05-07: durable input items.text,372tests/independentreview.
  Pip-audit отдельно выявил certifi advisory; clean full gate не заявляется.
- [ ] Остальные находки шага 7 (для items.text) и шаги 8–11 остаются в очереди.
  Чат — ранняя альфа по оценке владельца;
  дальнейшая работа над ним планируется отдельно. Шаг 8 не означает полный
  scope разработки или готовность всей системы чата.

Подробности, тесты и ограничения: [рабочий файл задачи](plans/06_non_gameplay_hardening_progress.md).
Текущие статусы исходных находок: [реестр 10](10_findings_registry.md).
Историческое заключение ниже не заменяется новым аудитом.

## Быстрая сверка исправлений — 19.10.2026

База: `12811132`. `[x]` — исправление в репозитории подтверждается коммитом и статической сверкой текущего кода/регрессионных тестов; тесты в этой сверке не запускались. Исторический текст и статистика ниже сохранены, они не являются текущим списком открытых дефектов.

- [x] **AG-01 — gift только за завершённый primary main-hand удар.** `cfd6b43c`: `mechanics_service.py`, `test_exchange_execution_contract.py`; исключены counter, offhand, secondary и skipped.
- [x] **AG-02 — пассивная регенерация один раз за размен.** `aa35933c`: `apply_exchange_regen` в финализации executor; `test_exchange_regen_contract.py`.
- [x] **AG-03 — commit изменений статусов и модификаторов между волнами.** `2b13d1ac`: staging/commit в AbilityService и MechanicsService; multi-wave cases в `test_exchange_execution_contract.py`.
- [x] **AG-04 — тайминг эффектов и позиция лучника в финализации размена.** `12f1c6e7`: единая финализация, привязка тайминга к личному счётчику получателя; `test_effect_timing_contract.py`. Дополнение `2a5fdf2a`: periodic tick только в разменах, `test_instant_periodic_contract.py`. AG-01–04 интегрированы через `a2642896`.
- [x] **AG-07 — default/dev service key отклоняется в production.** `0ba3aa3b`: `src/backend/core/game_auth.py`; `test_game_auth.py` и `test_production_settings.py`.
- [ ] **AG-05, AG-06, AG-08, AG-09:** закрытие этой быстрой сверкой не установлено; требуется отдельная адресная проверка. Это не повторное подтверждение дефектов.

**Дополнение 19.10.2026:** остатки A05-15, A08-03/A07-04 и A08-08 устранены/адресно проверены в рабочем дереве; результаты Mongo/API/Nginx/Compose приведены в [реестре 10](10_findings_registry.md#адресная-приёмка-оставшихся-частей--19102026). Это не production sign-off.

Статусы исходных A02–A09 ведутся в [реестре 10](10_findings_registry.md#быстрая-сверка-исправлений--19102026). В этом отчёте есть смысловые расхождения старых IDs: например, A08-01 в исходном реестре относится к default keys, а не к публикации backend-порта. Статус сверять по контракту, не только по ID.

- **Аудитор:** Antigravity (независимая техническая проверка + собственный аудит кода)
- **Дата:** 2026-10-17
- **Проверяемый пакет:** `audit/01_project_inventory.md` .. `audit/10_master_audit.md`, `audit/10_findings_registry.md`, `audit/10_root_causes.md`, `audit/10_skill_gaps.md`, `audit/plans/00_remediation_roadmap.md` .. `audit/plans/05_skill_updates.md`
- **Фактическое состояние репозитория на момент проверки:** `HEAD` (`81562c13`, `"retire persisted runtime for catalog alpha"`) + незакоммиченные изменения рабочего дерева в `src/backend/features/combat/`, `tests/backend/features/combat/`, `docs/ru/backend/features/combat/exchange_execution.md` и `src/backend/features/items/`.
- **Ограничения скоупа (по указанию автора проекта):**
  1. Исходный код проекта и тесты не модифицировались.
  2. Направление `src/backend/features/monsters/*` находится в процессе активного редизайна (переход на каталожную альфу в отдельной ветке/рабочем дереве) и **исключено** из поиска новых замечаний.
  3. Особое внимание в части собственного независимого аудита уделено **сегодняшней незакоммиченной правке боя** (`StrikeExecution` / `FeintActivation` / `CombatIntent` в `src/backend/features/combat/`) и остальным доменам проекта вне `monsters`.

---

## 1. Исполнительное резюме и сводная статистика

### 1.1. Итоги проверки утверждений Астры (125 пунктов: 120 `A02..A09` + 5 `O02`)

Каждое из 125 утверждений отчётов `02`–`09` и сводного реестра `10_findings_registry.md` было сверено напрямую с текущими файлами исходного кода, конфигурациями, миграциями Alembic, Docker/Nginx/GitHub Actions манифестами и зависимостями в `.venv`:

| Категория верификации | Кол-во | Доля | Комментарий |
| --- | ---: | ---: | --- |
| **Подтверждено** | **113** | 90.4% | Прямые доказательства в текущем коде; механика, файлы и строки совпадают с описанием Астры. |
| **Частично подтверждено** | **10** | 8.0% | Проблема реальна, но либо уже частично закрыта в `HEAD` (`A07-03`, `A07-12`, `O02-01`), либо требует корректировки критичности/скоупа (`A03-13`, `A02-08`, `A04-14`, `A04-19`, `A04-20`, `A07-17`, `A08-13`). |
| **Опровергнуто** | **0** | 0.0% | Ни одной выдуманной («галлюцинированной») находки в отчётах Астры не обнаружено. |
| **Не удалось проверить (внешняя среда)** | **2** | 1.6% | `A08-11` (настройки Rulesets/Environments в GitHub UI) и `A08-12` (фактические права `.env` на живом prod VPS; при этом уязвимость самого workflow `.github/workflows/deploy-production.yml:83,89` подтверждена по коду). |

### 1.2. Итоги собственного независимого аудита Antigravity (`AG-01` .. `AG-09`)

Помимо проверки отчётов Астры, выполнен независимый аудит текущего состояния проекта (включая сегодняшнюю незакоммиченную правку боевого движка):
- **Положительный эффект сегодняшней правки боя (`execution.py`, `executor.py`, `pipeline.py`, `ability_service.py`, `log_builder.py`):**
  Правка устранила целый класс критических ошибок владения намерением (`CombatIntent` / `FeintActivation` / `StrikeExecution`):
  1. Удар второй рукой (`offhand`) партнёра больше не получает чужой `action.move` и не активирует финт/подготовку игрока на монстре.
  2. Контратака (`counter`) больше не подставляет чужой `action.partner_move` / `action.move` и корректно работает в принудительном размене (`is_forced=True`) и при любом порядке пары.
  3. Вторичные цели массового финта (`secondary`) теперь проецируются только после подтверждённой активации финта (`activation.applied_to(result)`), не списывают повторно стамину, не дублируют событие `CAST` и не вешают `preparation_effects` повторно.
- **Обнаруженные нами новые дефекты в сегодняшней правке боя и смежной механике (`AG-01`..`AG-04`):**
  1. **`AG-01` (High):** При коммите волны в `CombatExecutor._handle_exchange` (`executor.py:272-279`) создаётся единый `commit_ctx` с `grant_exchange_gift = True` и дефолтным `source_type = "main_hand"`, из-за чего `MechanicsService._grant_exchange_gift_token` (`mechanics_service.py:952-966`) выдаёт **лишние токены `gift` (`+1` за каждый `offhand`-удар во 2-й волне и `+1` за каждую `secondary`-цель массового финта)**.
  2. **`AG-02` (High):** Пассивная боевая регенерация (`_register_combat_hp_regen` и `_register_combat_stamina_regen` в `ability_service.py:200-201`) регистрируется в `result.resource_changes` при каждом вызове `pipeline.calculate()` и применяется при коммите волны для **каждого** вложенного удара (`primary`, `offhand`, `counter` и даже `secondary` с `pay_cost=False`), умножая регенерацию HP и стамины в 2–4 раза за один размен.
  3. **`AG-03` (High):** Четыре ветки `AbilityService` (`prep_dual_blade_loop_parry` -> `prep_dual_blade_loop_counter` на `ability_service.py:805-809`, `dispel_preparations` на `1106-1119`, `force_ranged_close` на `1121-1143`, `_materialize_modifier_status_effects` на `460-467`) мутируют `actor.statuses.effects` напрямую на **временной глубокой копии** (`real_source.model_copy(deep=True)` / `real_target.model_copy(deep=True)`), не записывая изменения в `ctx.result.status_applications` / `ctx.result.status_removals`. При коммите волны через `MechanicsService.apply_exchange_results` эти эффекты и диспелы бесследно теряются.
  4. **`AG-04` (Medium):** Для `secondary`-ударов массового финта `StrikeExecution.context_mods` (`execution.py:121-122`) выставляет `action_mode="unidirectional"`, из-за чего в `AbilityService._apply_queued_effects` (`ability_service.py:1179`) статус-эффекты на вторичных целях получают `active_from_exchange = exchange_counter` (вместо `exchange_counter + 1`, как у основной цели того же финта). Кроме того, `RangedPositionService.update_after_exchange` (`executor.py:280`) вызывается внутри цикла волн на каждой волне, а не один раз в конце размена.
- **Обнаруженные нами дефекты в остальной кодовой базе, пропущенные Астрой (`AG-05`..`AG-09`):**
  5. **`AG-05` (High):** В `pyproject.toml:112-150` глобально отключён `mypy` (`ignore_errors = true`) для **36 ключевых модулей бэкенда** (включая `victory_finalizer_task`, `combat.runtime.engine.resolver`, `expedition.service`, `loot_service`, `navigation_service`), что скрыло от CI баг `A05-11` (`row.finalization`).
  6. **`AG-06` (High):** В `CombatSystemIntegrator._apply_rift_combat_result` (`src/backend/features/combat/integrations/system_integrator.py:261`) и `GameSessionIntegrator._apply_rift_combat_result` (`src/backend/features/game_session/integrations/session_integrator.py:355`) захардкожено `result="victory"` (в отличие от `victory_finalizer_task.py:182`), причём `recover_missing_combat_session` (`system_integrator.py:163-168`) засчитывает победу в разломе даже при аварийной потере боевой сессии в Redis.
  7. **`AG-07` (High):** В `src/backend/core/game_auth.py:66` функция `require_internal_service_key` отвергает только префикс `"change-me-"`, но принимает дефолтный `"dev-site-to-game-service-key"` из `settings.py:55` (тогда как в новом `monsters/api/access.py:20` отвергаются оба префикса `("dev-", "change-me-")`).
  8. **`AG-08` (Medium):** В `ExpeditionService._refresh_active_items` (`src/backend/features/expedition/service.py:14-15, 712-720`) присутствует второе прямое обращение к `InventoryRepository` и `InventoryItemProjection` в обход `InventoryIntegrator`, пропущенное Астрой в `A02-04`.
  9. **`AG-09` (Medium):** Лишняя асинхронная обёртка (`async def calculate` + `asyncio.gather`) вокруг полностью синхронного CPU-bound расчёта `CombatPipeline.calculate` (`pipeline.py:34`, `executor.py:223,261,385`) и безусловный импорт `src.backend.app` на уровне модуля в `tests/backend/conftest.py:14`, инициализирующий фоновые очереди Loguru `enqueue=True` (`multiprocessing.SimpleQueue`).

---

## 2. Детальная верификация аудита Астры (`02`–`09`)

### 2.1. Пункты со статусом «Частично подтверждено» и «Не удалось проверить»

#### Частично подтверждено (10 пунктов)

1. **`A07-03` — Неаутентифицированные административные API генерации и симуляций**
   - **Оценка Астры:** `High` | **Независимая оценка:** `High` (скоуп сократился в `HEAD`).
   - **Фактическое состояние:**
     - Роуты `/api/admin/generation-ai` (`src/backend/features/generation_ai/api.py:23`, монтируется в `src/backend/core/router.py:85`) и `/api/admin/combat-ai` (`src/backend/features/combat/api/ai_simulation_router.py:36`, монтируется в `src/backend/core/router.py:89`) **по-прежнему полностью открыты без `dependencies`** — любой клиент может ставить платные задачи генерации в ARQ и запускать тяжёлые батчи боёв.
     - В то же время роутер `/api/admin/monsters` в коммите `81562c13` был переведён в read-only каталог и закрыт зависимостью `Depends(require_monster_catalog_read)` (`src/backend/features/monsters/api/router.py:34-38`, `src/backend/features/monsters/api/access.py:13-47`).

2. **`A07-12` — Аналитическая Studio не имеет собственной аутентификации и содержит мутирующие прокси-вызовы в prod**
   - **Оценка Астры:** `Medium` | **Независимая оценка:** `Medium`.
   - **Фактическое состояние:**
     - В `src/studio/app.py:72-120` по-прежнему нет аутентификации и CSRF-защиты, а переключение источника на `prod` (`POST /context/source` в `src/studio/features/workspace/router.py:19-30`) доступно без авторизации.
     - Часть, касающаяся `content_ops/cabinet.py`, уже исправлена: `src/studio/features/cabinet/modules/content_ops/cabinet.py:20-52` теперь выполняет только `GET`-запросы к каталогу.
     - Однако в `src/studio/features/cabinet/modules/combat_ai_testing/cabinet.py:1464-1562` (`start_batch`, `delete_Simulation_preset`, `cancel_batch`) остались прямые мутирующие `POST`-запросы в `f"{source.api_base}/api/admin/combat-ai/..."`, которые при выбранном `prod` бьют в неаутентифицированный `combat-ai` бэкенда.

3. **`O02-01` — Широкий bootstrap для воркеров `generation_ai`**
   - **Оценка Астры:** `Observation` | **Независимая оценка:** `Observation`.
   - **Фактическое состояние:** В `src/backend/features/generation_ai/bootstrap.py:1-26` пакет `monsters` уже удалён из `REGISTER_PACKAGES`, но вместо него добавлен `"src.backend.features.news.workers.tasks_news"`, поэтому сам архитектурный паттерн кросс-доменного bootstrap сохранился.

4. **`A03-13` — Триггеры оружия и боеприпасов `ON_CRIT` (кровотечение, оглушение) применяются после парирования или уворота**
   - **Оценка Астры:** `Medium` | **Независимая оценка:** `High` (повышение приоритета).
   - **Фактическое состояние:**
     - В `src/backend/features/combat/runtime/engine/resolver.py:66-70` после проверок уворота и парирования критический удар вычисляется при `if not res.is_dodged:`, то есть при `res.is_parried = True` (а при `flags.force.crit = True` — и при `res.is_dodged = True`) выставляется `res.is_crit = True` при `res.is_hit = True`.
     - В `src/backend/features/combat/runtime/engine/weapon_triggers.py:137-146` (`apply_ammo_crit_payload`), `291-304` (`weapon_serrated_bleed_crit`), `413-420` (`weapon_impact_stun_crit`) эффекты ставятся в очередь с `conditions={"is_hit": True, "is_crit": True}`.
     - В `src/backend/features/combat/runtime/engine/ability_service.py:1410-1425` метод `_effect_conditions_met` проверяет `"is_hit": result.is_hit` (в отличие от строки `678`, где для абилок явно вычисляется `contact_hit = ctx.result.is_hit and not ctx.result.is_dodged and not ctx.result.is_parried`).
     - Более того, в `src/backend/features/combat/runtime/engine/effect_factory.py:39-44` при `damage_ref=0` (урон обнулён парированием) кровотечение получает гарантированный фоллбэк `max(1, int(config.power))` (`5` ед. урона за ход).
     - Это детерминированный баг ядра боевой механики (игрок парирует удар без урона, но получает кровотечение или оглушение), поэтому серьёзность — **High**, а не `Medium`.

5. **`A02-08` — В `src/shared` остаётся доменно-специфичная runtime-схема инвентаря**
   - **Оценка Астры:** `Medium` | **Независимая оценка:** `Low` (понижение приоритета).
   - **Фактическое состояние:** `InventoryRuntimeSessionDTO` действительно находится в `src/shared/schemas/inventory.py:86-96` и используется только бэкендом (`src/backend/features/inventory/managers/session.py:9`), но не создаёт runtime-уязвимости или циклического импорта.

6. **`A04-14` — Зависший переход разлома (`travel_transition`) блокирует игрока без таймаута**
   - **Оценка Астры:** `High` | **Независимая оценка:** `High` (с уточнением).
   - **Фактическое состояние:** В `src/backend/features/rift/services/player_service.py:293-294` ход блокируется при активном `travel`, а в `src/backend/features/rift/services/system_integrator.py:157-189` (`tick_active_runs`) проверяются только `encounter_Service.cleanup_expired_sessions` и `check_pending_combat_transitions`, но нет очистки зависших `travel_transition` без боя. Уточнение: в `PlayerRiftActionRequestDTO` есть служебный флаг `resolve_transition_combat`, но для обычного клиента он не решает проблему (и сам по себе является уязвимостью `A04-01`/`A07-05`).

7. **`A04-19` — Промпт AI-генерации событий комнаты разлома подставляет `node.zone` вместо типа зоны**
   - **Оценка Астры:** `Low` | **Независимая оценка:** `Low` (с уточнением).
   - **Фактическое состояние:** В `src/backend/features/rift/services/node_event_generation_service.py:347,361` в промпт передаётся `zone_type=str(node.zone or "unknown")` (то есть ключ `"z1"`, `"z2"` вместо семантического `ZoneType`). Уточнение: поскольку `generation_enabled` сейчас захардкожен в `False` (`node_event_generation_service.py:95`), в рантайме эта ветка спящая.

8. **`A04-20` — В `tools/world_static_audit.py` смешаны несовместимые контракты геометрии мира**
   - **Оценка Астры:** `Low` | **Независимая оценка:** `Low` (с уточнением по коммиту `374baab0`).
   - **Фактическое состояние:** В коммите `374baab0` скрипт `tools/world_static_audit.py:23-39, 326-346` был частично обновлён под 5-координатный формат `region_id_zone_id_rx_ry_r` и `ZoneRole`, однако в функции `audit_exit_symmetry` (`tools/world_static_audit.py:100-149`) осталась жёсткая проверка 4-частевого `loc_id` (`len(parts) != 4`) и устаревших констант `REGION_SIZE = 5` / `ZONE_SIZE = 5` (`строки 31-32`).

9. **`A07-17` — Доверие к `| safe` в шаблонах фронтенда**
   - **Оценка Астры:** `Low` | **Независимая оценка:** `Observation`.
   - **Фактическое состояние:** В `src/frontend/app.py:122-134` фильтр `scenario_rich_text` предварительно экранирует весь вход через `html.escape(raw_text)` перед заменой базовых тегов форматирования. В текущем коде прямой XSS нет; это рекомендация по defence-in-depth.

10. **`A08-13` — Reverse proxy передаёт `X-Forwarded-For` без явной конфигурации доверенных прокси**
    - **Оценка Астры:** `Medium` | **Независимая оценка:** `Low`.
    - **Фактическое состояние:** `deploy/nginx/site.conf.template:42,60,82` использует `$proxy_add_x_forwarded_for`, но в текущем коде бэкенда rate-limiting (`AuthRateLimiter` в `src/backend/features/players/services/auth_rate_limiter.py:28-59`) привязан к `login`/`scope` в Redis, а не к IP из `X-Forwarded-For`.

#### Не удалось проверить без доступа к внешней инфраструктуре (2 пункта)

1. **`A08-11` — Deploy workflow может быть запущен вручную с произвольным `image_tag`:**
   По файлу `.github/workflows/deploy-production.yml:3-15` подтверждено наличие `workflow_dispatch` с произвольным `inputs.image_tag`, однако проверить настройки GitHub Environment protection rules и Rulesets репозитория в веб-интерфейсе GitHub из локального клона невозможно.
2. **`A08-12` — Production `.env` читается и модифицируется на хосте без проверки прав доступа:**
   По файлу `.github/workflows/deploy-production.yml:83,89` подтверждено отсутствие `umask 077` и `chmod 600 "$ENV_FILE"` при создании `.env.tmp` и замене `.env`, но проверить текущие POSIX-права файла `/opt/turnbased-mmorpg/.env` на боевом VPS без SSH-доступа невозможно.

---

### 2.2. Полная сводная таблица верификации всех 125 пунктов Астры (`A02`–`A09`, `O02`)

#### Отчёт `02_architecture_boundaries.md` (`A02-01`..`A02-10`, `O02-01`..`O02-05`)

| ID | Заголовок Астры | Статус проверки | Фактические ссылки (`file:line`) и техническое обоснование | Оценка Астры / Наша |
| --- | --- | --- | --- | --- |
| `A02-01` | GameSession читает `CharacterModel` напрямую в обход `character` | **Подтверждено** | `src/backend/features/game_session/dependencies.py:12` импортирует `CharacterModel`; `src/backend/features/game_session/services/character_Read_repo.py:5,19-39` выполняет `select(CharacterModel)`. В `tests/backend/features/test_infrastructure_boundaries.py:34` зашито исключение. | High / **High** |
| `A02-02` | `game_session` зависит от внутренних модулей `combat`, `exploration`, `scenario`, `rift`, `character` | **Подтверждено** | `src/backend/features/game_session/dependencies.py:13-33` и `src/backend/features/game_session/integrations/session_integrator.py:17-19` импортируют внутренние DTO/сервисы смежных фич. При этом `game_session` отсутствует в `FEATURE_NAMES` в `tests/backend/features/test_infrastructure_boundaries.py:16-30`. | High / **High** |
| `A02-03` | `exploration` и `rift` импортируют сервисы и репозитории друг друга и `world`/`combat`/`character` | **Подтверждено** | `src/backend/features/exploration/dependencies.py:18-45`, `src/backend/features/exploration/services/navigation_service.py:13`, `src/backend/features/rift/dependencies.py:15-17`, `src/backend/features/rift/services/instance_service.py:17-20`, `src/backend/features/rift/services/entry_service.py:17-22`. | High / **High** |
| `A02-04` | `CharacterStateIntegrator` инстанцирует `InventoryRepository` и `InventoryItemProjection` в обход `InventoryIntegrator` | **Подтверждено** | `src/backend/features/character/integrations/state_integrator.py:11-12, 224-231` напрямую создаёт `InventoryRepository(db)` и `InventoryItemProjection.from_model(row)`. *(См. также нашу находку `AG-08`: тот же антипаттерн продублирован в `ExpeditionService._refresh_active_items`.)* | Medium / **Medium** |
| `A02-05` | Смешаны два механизма межфичевого взаимодействия: прямые Python-вызовы и Redis Streams RPC | **Подтверждено** | `src/backend/features/character/integrations/session_bridge.py:21-34` (стрим-запросы `events.request`), `src/backend/features/combat/integrations/system_integrator.py:288-299` vs прямые DI-адаптеры в `src/backend/features/game_session/dependencies.py`. | Medium / **Medium** |
| `A02-06` | Несогласованный префикс Redis для `world_map` (`world:map:v3:` vs `game:world:map:v3:`) | **Подтверждено** | `src/backend/features/world/managers/world_map_manager.py:12` (`PREFIX = "world:map:v3:"`) против `src/backend/core/keys.py:42` (`WORLD_MAP_REGION = "game:world:map:v3:{region_id}"`). | Medium / **Medium** |
| `A02-07` | Дублирование настроек `combat_Debug_keep_redis_keys` в `Settings` | **Подтверждено** | В `src/backend/config/settings.py:84` и `src/backend/config/settings.py:128` поле `combat_Debug_keep_redis_keys: bool = False` объявлено дважды в одном классе `Settings`. | Low / **Low** |
| `A02-08` | В `src/shared` остаётся доменно-специфичная runtime-схема инвентаря | **Частично подтверждено** | `InventoryRuntimeSessionDTO` в `src/shared/schemas/inventory.py:86-96` используется только в `src/backend/features/inventory/managers/session.py:9`. Архитектурная нечистота есть, но критичность — `Low`. | Medium / **Low** |
| `A02-09` | Архитектурный тест покрывает только 13 из 21 backend features и содержит allowlist-исключения | **Подтверждено** | `tests/backend/features/test_infrastructure_boundaries.py:16-43`: в `FEATURE_NAMES` отсутствуют 8 фич (`actor_state`, `expedition`, `game_catalog`, `game_lobby`, `game_session`, `generation_ai`, `news`, `tg_bot`), а в `TEMPORARY_MODEL_IMPORT_EXCEPTIONS` зашито 8 исключений. | Medium / **Medium** |
| `A02-10` | Studio и Frontend общаются с Backend через смешанный набор `/api/admin`, `/api/internal` и `/api/game` | **Подтверждено** | `src/studio/features/cabinet/modules/combat_ai_testing/cabinet.py:1232,1465`, `src/studio/features/cabinet/modules/content_ops/cabinet.py:24-44`, `src/frontend/features/game/services/bootstrap_client.py:21`. | Medium / **Medium** |
| `O02-01` | Широкий bootstrap для воркеров `generation_ai` | **Частично подтверждено** | В `src/backend/features/generation_ai/bootstrap.py:1-26` `monsters` уже удалён, но добавлен `src.backend.features.news.workers.tasks_news`. | Obs / **Obs** |
| `O02-02` | Неоднородная структура внутренних пакетов фич | **Подтверждено** | Плоская структура в `src/backend/features/news/` и `src/backend/features/generation_ai/` против слоистой в `combat/`, `inventory/`, `rift/`. | Obs / **Obs** |
| `O02-03` | Два параллельных дерева шаблонов во `frontend` | **Подтверждено** | `src/frontend/templates/` (`src/frontend/app.py:102`) и `src/frontend/features/site/templates/` (`src/frontend/features/site/router.py:34`). | Obs / **Obs** |
| `O02-04` | Смешение `codex_core`, `codex_platform` и локального инфраструктурного кода | **Подтверждено** | `pyproject.toml:35-36`, `src/backend/core/database.py:1`, `src/backend/core/containers/redis.py:12-16`. | Obs / **Obs** |
| `O02-05` | Высокая связность вокруг `character`, `combat`, `rift`, `game_session` | **Подтверждено** | Подтверждено графом импортов в `dependencies.py` и `integrations/` указанных четырёх модулей. | Obs / **Obs** |

#### Отчёт `03_combat_runtime.md` (`A03-01`..`A03-13`)

| ID | Заголовок Астры | Статус проверки | Фактические ссылки (`file:line`) и техническое обоснование | Оценка Астры / Наша |
| --- | --- | --- | --- | --- |
| `A03-01` | Неидемпотентное начисление XP, амортизации оружия и наград арены при ретрае `victory_finalizer_task` | **Подтверждено** | `src/backend/features/combat/workers/victory_finalizer_task.py:92-123` выполняет `finalize_experience` (`experience_finalizer.py:55,147-166` делает `xp_int += ...` в Redis), `apply_session_wear`, `finalize_deaths` и `complete_match` до сохранения `CombatFinalizationRecordDTO(stage="outcomes_applied")` в строке `131`. | High / **High** |
| `A03-02` | Потеря боевого хода при истечении lock или падении воркера после `pop_actions_batch` | **Подтверждено** | `src/backend/features/combat/workers/collector_task.py:37` атомарно удаляет ходы из очереди (`LPOP` в `session.py:534-541`), но при занятом `acquire_executor_lock` (`строки 82-92`) или сбое `executor_task.py:66-102` батч никуда не возвращается. | High / **High** |
| `A03-03` | Неатомарный `commit_execution_results` в `CombatSessionManager` | **Подтверждено** | `src/backend/features/combat/managers/session.py:567-642` выполняет `save_actor_snapshot` в цикле до основного pipeline (`609-639`), а после `pipe.execute()` отдельно вызывает `return_target_to_pool` (`640-642`). | High / **High** |
| `A03-04` | Снятие `executor_lock` по `DEL` без проверки владельца (риск гонки двух `executor_task`) | **Подтверждено** | `src/backend/features/combat/managers/session.py:495-507` ставит `SET lock "1" NX EX 10` и снимает через безусловный `redis.delete(key)`. В `executor_task.py:42` также захардкожен `lock_timeout = 10` вместо `settings.combat_lock_ttl` (`30`). | High / **High** |
| `A03-05` | Потеря возврата цели при гибели исходного атакующего в принудительном (forced) размене | **Подтверждено** | `src/backend/features/combat/runtime/processors/executor.py:735-765`: `_collect_target_returns` проверяет `_can_return_target` (оба живы) и для `target -> source` требует `if action.partner_move`. В forced-атаке (`partner_move is None`), если атакующий погибает от шипов/контратаки, выживший защитник теряет запись в `q:targets`. | Medium / **Medium** |
| `A03-06` | `collector_task` оставляет пассивного участника без пары и без forced-атаки при несимметричной очереди целей | **Подтверждено** | `src/backend/features/combat/runtime/processors/collector.py:61-106`: при истечении `combat_pair_timeout` принудительный удар создаётся только если у `source` есть активный интент в `moves`. Если `source` пассивен, а `target` ждёт его в `moves`, `target` не получает ни пары, ни возврата `source` в `q:targets`. | Medium / **Medium** |
| `A03-07` | Игнорирование `combat_Debug_keep_redis_keys` при очистке сессии в `victory_finalizer_task` | **Подтверждено** | `src/backend/features/combat/workers/victory_finalizer_task.py:162` безусловно вызывает `session_manager.delete_combat_session(session_id)`, не проверяя `settings.combat_Debug_keep_redis_keys`. | Low / **Low** |
| `A03-08` | Молчаливое проглатывание ошибок начисления боевого опыта в `ExperienceFinalizer` | **Подтверждено** | `src/backend/features/combat/runtime/finalizers/experience_finalizer.py:63-64` ловит `except Exception:` и логирует `warning`, не пробрасывая исключение в `victory_finalizer_task`. | Medium / **Medium** |
| `A03-09` | Несогласованность порога ремонта и штрафа поломки предметов между `DurabilityPolicy` и `ActorStateSessionManager` | **Подтверждено** | `src/backend/features/combat/runtime/finalizers/durability_policy.py:13` (`BROKEN_POWER_MULTIPLIER = 0.70`) против `src/backend/features/actor_state/managers/session.py:550` (`durability <= 0 -> continue`, т.е. множитель `0.0`). | Medium / **Medium** |
| `A03-10` | Утечка памяти и Redis-ключей при падении `combat_ai_simulation_batch_task` до `finally` или отмене задачи | **Подтверждено** | `src/backend/features/combat/workers/ai_simulation_task.py:86-153`: при внешнем `CancelledError`/краше воркера до `delete_combat_session` в строке `150` ключи `combat:s:ai-sim-*` (с TTL 86400 с в `session.py:182`) остаются в Redis. | Medium / **Medium** |
| `A03-11` | `collector_task` перезаписывает `BattleMeta` поверх конкурентных изменений `executor_task` | **Подтверждено** | `src/backend/features/combat/workers/collector_task.py:34,63` читает и сохраняет весь JSON `meta` без `executor_lock`, конкурируя с `commit_execution_results` (`session.py:610`), который обновляет `step_counter` и `dead_actors` в том же ключе `meta`. | High / **High** |
| `A03-12` | Повторное исполнение `unidirectional`-действий (предметы/мгновенные скиллы) не ограничено лимитом на ход | **Подтверждено** | `src/backend/features/combat/services/action_service.py:124-155` и `collector.py:42-48`: `instant`/`item` пропускаются в `ready_actions` без инкремента `exchange_counter` (`executor.py:357-408`), позволяя спамить инстант-абилками без КД/с нулевой ценой в рамках одного шага. | Medium / **Medium** |
| `A03-13` | Триггеры оружия и боеприпасов `ON_CRIT` применяются после парирования или уворота | **Частично подтверждено** | Подтверждено в `resolver.py:66-70`, `weapon_triggers.py:137-146,291-304,413-420` и `ability_service.py:1410-1425`. Серьёзность повышена нами с `Medium` до **`High`**, так как это детерминированная ошибка боевого резольвера. | Medium / **High** |

#### Отчёт `04_rift_world_generation.md` (`A04-01`..`A04-21`)

| ID | Заголовок Астры | Статус проверки | Фактические ссылки (`file:line`) и техническое обоснование | Оценка Астры / Наша |
| --- | --- | --- | --- | --- |
| `A04-01` | Игрок может передать debug-поля (`force_event`, `resolve_transition_combat`, `attributes`) в публичный Rift API | **Подтверждено** | `src/backend/features/rift/dto/runtime.py:182-194`, `src/backend/features/rift/api/router.py:24-31`, `src/backend/features/rift/services/player_service.py:121-125,204-213,560-571`. | Critical / **Critical** |
| `A04-02` | Создание и вход в разлом выполняют изменения в PostgreSQL и Redis без единой транзакции и без компенсации | **Подтверждено** | `src/backend/features/rift/services/entry_service.py:55-96`, `src/backend/features/rift/services/instance_service.py:41-106`, `src/backend/features/rift/services/player_service.py:72-119`. | High / **High** |
| `A04-03` | Гонка при конкурентных запросах `act` в разломе (`run` читается и перезаписывается целиком без lock/CAS) | **Подтверждено** | `src/backend/features/rift/services/player_service.py:40-49,175-182` и `src/backend/features/rift/managers/session.py:86-90` (`save_run` перезаписывает корень `$` без блокировки и версии). | High / **High** |
| `A04-04` | Конкурентные действия участников и фоновый тик перезаписывают `RiftZoneInstanceStateDTO` целиком | **Подтверждено** | `src/backend/features/rift/managers/session.py:32-44` (`save_instance` перезаписывает `$`), вызывается из `player_service.py:201,375,409` и `system_integrator.py:180,261` без блокировки. | High / **High** |
| `A04-05` | Кэширование `ExplorationEncounterService` с привязанной DB-сессией в модульном словаре `_RUNTIME_CACHE` | **Подтверждено** | `src/backend/features/exploration/dependencies.py:33-38,148-179`: `encounter_service` создаётся с request-scoped `db: AsyncSession`, но сохраняется в глобальном `_RUNTIME_CACHE` на весь жизненный цикл процесса. | High / **High** |
| `A04-06` | `EncounterIntegrationService` мутирует позицию и сессию персонажа в Redis до подтверждения запуска боя | **Подтверждено** | `src/backend/features/exploration/integrations/encounter_integration.py:106-152,226-260`: при исключении в `combat_entry.create_combat_session` отката `state="combat"` в Redis нет. | High / **High** |
| `A04-07` | Отказ `CombatEntryService` при сборке снапшота оставляет висячие ключи `combat:s:{id}:*` в Redis | **Подтверждено** | `src/backend/features/combat/services/entry_service.py:88-167`: если после начала записи снапшотов возникает исключение для одного из следующих акторов, `delete_combat_session` не вызывается. | Medium / **Medium** |
| `A04-08` | Завершение боя в разломе зависит от одиночного вызова `apply_combat_result` без механизма сверки с реальным статусом боя | **Подтверждено** | `src/backend/features/rift/services/system_integrator.py:224-262`: `check_pending_combat_transitions` запускает бой и переводит `travel.combat_status = "active"`, но никогда не проверяет в `tick_active_runs`, завершился ли уже активный бой, если `apply_combat_result` не дошёл. | High / **High** |
| `A04-09` | Несогласованный расчёт `danger` / `tier` при генерации энкаунтеров между `exploration` и `rift` | **Подтверждено** | `src/backend/features/exploration/services/encounter_service.py:553-576` и `src/backend/features/rift/services/encounter_service.py:239-269`. | Medium / **Medium** |
| `A04-10` | `GenerationAIService` удерживает транзакцию PostgreSQL открытой во время внешнего HTTP-вызова к LLM/Image провайдеру | **Подтверждено** | `src/backend/features/generation_ai/services.py:210-310`: сессия `self.repo.session` создаёт `job` и `attempt`, затем ожидает `await provider.generate_text(...)` / `generate_image(...)` (до 60–90 с в `providers.py:72,267`) перед `commit()`. | High / **High** |
| `A04-11` | Воркер `generation_ai` создаёт новый `GenerationAIService` и HTTP-клиенты на каждую задачу без переиспользования пула | **Подтверждено** | `src/backend/features/generation_ai/workers/tasks.py:27-68` и `src/backend/features/generation_ai/providers.py:72,267` (`async with httpx.AsyncClient(...)` на каждый вызов). | Low / **Low** |
| `A04-12` | Отсутствует идемпотентность и дедупликация задач в `GenerationAIService.enqueue_job` | **Подтверждено** | `src/backend/features/generation_ai/services.py:139-208` и `src/backend/features/generation_ai/repositories.py:28-35`: нет уникального ключа/проверки активной задачи для того же `(task_type, entity_type, entity_id)`. | Medium / **Medium** |
| `A04-13` | `RiftInstanceService` сохраняет граф узлов разлома одновременно в PostgreSQL JSONB и в Redis JSON без механизма синхронизации | **Подтверждено** | `src/backend/features/rift/services/instance_service.py:85-103` и `src/backend/features/rift/services/system_integrator.py:157-189`: рантайм-изменения в Redis не синхронизируются с `RiftActiveInstance.payload` в БД до закрытия инстанса. | Medium / **Medium** |
| `A04-14` | Зависший переход разлома (`travel_transition`) блокирует игрока без таймаута и без фонового восстановления | **Частично подтверждено** | `src/backend/features/rift/services/player_service.py:293-294` и `system_integrator.py:157-189`. Подтверждено (с уточнением о наличии debug-флага `resolve_transition_combat`). | High / **High** |
| `A04-15` | В `RiftZoneInstanceStateDTO` используется `datetime.utcnow()` (naive datetime) наряду с timezone-aware датами | **Подтверждено** | `src/backend/features/rift/dto/zone_instance.py:14-18` (`def _utc_now() -> datetime: return datetime.utcnow()`). | Low / **Low** |
| `A04-16` | Отсутствует очистка истёкших `RiftSession` и `RiftParticipant` в Redis при аварийном завершении разлома | **Подтверждено** | `src/backend/features/rift/managers/session.py:28-115`: ключи `rift:instance:*`, `rift:run:*`, `rift:active_by_char:*` записываются через `json().set(...)` вообще без TTL (`expire`). | Medium / **Medium** |
| `A04-17` | `WorldGenerator` и `WorldMapManager` не имеют защиты от одновременной генерации одного региона двумя воркерами | **Подтверждено** | `src/backend/features/world/services/world_service.py:35-82` и `src/backend/features/world/managers/world_map_manager.py:15-52`. | Medium / **Medium** |
| `A04-18` | Ошибка сохранения сгенерированного ассета на диск после `commit` или до `commit` оставляет осиротевшие файлы/записи | **Подтверждено** | `src/backend/features/generation_ai/services.py:263-295`: `storage.save_bytes(...)` пишет файл на диск внутри `execute_job` до финального `await self.repo.session.commit()` (`строка 301`), без удаления файла при rollback. | Low / **Low** |
| `A04-19` | Промпт AI-генерации событий комнаты разлома подставляет `node.zone` (`"z1"`) вместо типа зоны | **Частично подтверждено** | `src/backend/features/rift/services/node_event_generation_service.py:347,361` (подтверждено в коде; сама генерация сейчас отключена `generation_enabled = False` в строке `95`). | Low / **Low** |
| `A04-20` | В `tools/world_static_audit.py` смешаны несовместимые контракты геометрии мира | **Частично подтверждено** | В коммите `374baab0` скрипт обновлён частично, но в `tools/world_static_audit.py:31-32,100-149` (`audit_exit_symmetry`) осталась старая проверка `len(parts) != 4`. | Low / **Low** |
| `A04-21` | Жёстко закодированные fallback-значения локации при выходе из разлома (`"hub_central"`) | **Подтверждено** | `src/backend/features/rift/services/player_service.py:456`: `entry_location_id = str(run.entry_location_id or "hub_central")` при том, что реальные ID локаций имеют формат `0_0_2_2_0`. | Low / **Low** |

#### Отчёт `05_persistence_consistency.md` (`A05-01`..`A05-15`)

| ID | Заголовок Астры | Статус проверки | Фактические ссылки (`file:line`) и техническое обоснование | Оценка Астры / Наша |
| --- | --- | --- | --- | --- |
| `A05-01` | Небезопасная ветка `claim_corpse_loot` без `expected_char_id` и фолбэк в `loot_claim_task` | **Подтверждено** | `src/backend/features/expedition/workers/loot_claim_task.py:27-35` (при отсутствии `char_id` вызывает `claim_corpse_loot` вместо `claim_corpse_loot_safe`) и `src/backend/features/expedition/services/loot_service.py:93-128`. | High / **High** |
| `A05-02` | SQL-перенос предметов при луте трупа не проверяет текущего владельца/контейнер в `WHERE` и не идемпотентен при сбое Redis | **Подтверждено** | `src/backend/features/expedition/services/loot_service.py:121-125,204-208,337-357`: `UPDATE inventory SET character_id = :target, location = 'bag' WHERE id IN (...)` без `AND character_id = :corpse_owner AND location = 'corpse'`, плюс `await self.db.commit()` до удаления трупа в Redis (`строки 208-211`). | High / **High** |
| `A05-03` | Мутации инвентаря (`equip`, `unequip`, `move`, `destroy`, `repair`) коммитят SQL и затем неатомарно патчат Redis-сессию без блокировки | **Подтверждено** | `src/backend/features/inventory/services/inventory_service.py:72-86,105-133,152-182,191-210`: после `await self.db.commit()` вызывается `_sync_runtime_item`, который делает `get_session` -> модификацию в памяти -> `patch_fields`. | High / **High** |
| `A05-04` | При смерти в экспедиции труп публикуется в Redis до `db.commit()` переноса предметов в `location='corpse'` | **Подтверждено** | `src/backend/features/expedition/service.py:663-709`: `await self._create_corpse_in_redis(...)` вызывается на строке `670`, а `await self.db.commit()` — только на строке `705`. | High / **High** |
| `A05-05` | Потребители Redis Streams (`StreamProcessor` и `RedisStreamEventBus`) делают `XACK` даже при необработанном исключении и не имеют DLQ/reclaim | **Подтверждено** | `.venv/Lib/site-packages/codex_platform/streams/processor.py:94-110` (`ack_batch` выполняется безусловно после `process_event`, который ловит `Exception`), а в `src/backend/core/containers/redis.py:73-112` `xack` вызывается в `finally` (`строка 105`). | High / **High** |
| `A05-06` | Воркер архивации чата (`archive_chat_messages`) сдвигает курсор `last_archived_id` даже при ошибке записи батча в MongoDB | **Подтверждено** | `src/backend/features/chat/workers/archive.py:103-117`: в блоке `except Exception:` функция `_save_batch_to_mongo` возвращает `True` (`строка 113`), после чего воркер вызывает `await redis.set(cursor_key, last_id)` (`строка 79`), навсегда теряя несохранённые сообщения при `XTRIM`. | High / **High** |
| `A05-07` | Удаление задачи генерации (`DELETE /api/admin/generation-ai/jobs/{job_id}`) в API не делает `session.commit()` | **Подтверждено** | `src/backend/features/generation_ai/repositories.py:71-86` делает только `session.delete(job)` + `session.flush()`, а `src/backend/features/generation_ai/api.py:92-97` не вызывает `session.commit()`. При закрытии `get_db_session` (`src/backend/core/database.py:21-26`) транзакция откатывается. | Medium / **Medium** |
| `A05-08` | Воркер `generation_ai` глотает ошибки, не вызывая `mark_job_failed` для зависших в `running` задач при внезапном сбое | **Подтверждено** | `src/backend/features/generation_ai/services.py:224-318` и `src/backend/features/generation_ai/workers/tasks.py:42-68`: при необработанном исключении/отмене вне внутреннего `try` статус задачи остаётся `running`. | Medium / **Medium** |
| `A05-09` | `RiftRuntimeIntegrator` синхронно коммитит PostgreSQL внутри каждого перехода/боя, но при ошибке Redis оставляет рассинхрон | **Подтверждено** | `src/backend/features/rift/integrations/runtime.py:78-115` и `src/backend/features/rift/services/system_integrator.py:105-155`. | Medium / **Medium** |
| `A05-10` | Ключи Redis для разломов (`rift:instance:*`, `rift:run:*`, `rift:active_by_char:*`) создаются без TTL | **Подтверждено** | `src/backend/features/rift/managers/session.py:32-44,86-90,104-115`: ни один `set` не сопровождается `expire`. | Medium / **Medium** |
| `A05-11` | `CombatResultArchiveService._upsert_archive_row` обращается к несуществующему атрибуту `row.finalization` | **Подтверждено** | В `src/backend/features/combat/services/result_archive_service.py:147` написано `row.finalization = dict(...)`, тогда как в SQLAlchemy-модели `CombatFinalizationModel` (`src/backend/infrastructure/combat/models/finalization.py:24-36`) колонка называется `finalization_payload`, а атрибута `finalization` нет. При повторном вызове с `existing is not None` (`строка 128`) и пустом `existing.result_payload` (`строка 129`) код либо молча создаёт динамический атрибут на Python-объекте без обновления SQL-колонки `finalization_payload`, либо нарушает инвариант модели. | High / **High** |
| `A05-12` | Многошаговые операции аутентификации сайта (`register`, `refresh`, `reset_password`) делают несколько отдельных `commit()` вместо атомарной транзакции | **Подтверждено** | `src/backend/features/players/services/auth_persistence.py:35,44,61,91,123` вызывает `await self.session.commit()` внутри каждого отдельного метода репозитория. | Medium / **Medium** |
| `A05-13` | Расхождение ORM-модели `UserRefreshToken` (`ip_address: str(64)`) и миграции Alembic (`String(45)`), а также отсутствие автоочистки истёкших токенов | **Подтверждено** | `src/backend/infrastructure/persistence/models/refresh_token.py:28` (`String(64)`) против `alembic/versions/0002_security_baseline.py:34` (`sa.String(length=45)`). | Low / **Low** |
| `A05-14` | Потеря данных экспедиции при сбое Redis: состояние экспедиции хранится только в Redis с TTL 7 дней без бэкапа в SQL | **Подтверждено** | `src/backend/features/expedition/service.py:34,722-732` (`EXPEDITION_SESSION_TTL_SECONDS = 604800`, хранение только в Redis). | Medium / **Medium** |
| `A05-15` | В MongoDB коллекции `chat_buckets` индексы создаются лениво во время запроса без фонового стартап-хука | **Подтверждено** | `src/backend/infrastructure/persistence/mongo/chat_buckets.py:42-69`: `_ensure_indexes` вызывается лениво внутри `append_messages` и `get_recent_messages`. | Low / **Low** |

#### Отчёт `06_testing_quality.md` (`A06-01`..`A06-12`)

| ID | Заголовок Астры | Статус проверки | Фактические ссылки (`file:line`) и техническое обоснование | Оценка Астры / Наша |
| --- | --- | --- | --- | --- |
| `A06-01` | Коллекция `pytest` падает на `tests/backend/features/generation_ai/test_asset_backfill.py` из-за удалённого модуля `asset_backfill` | **Подтверждено** | `tests/backend/features/generation_ai/test_asset_backfill.py:6` импортирует `from src.backend.features.generation_ai.asset_backfill import ...`, которого нет в `src/backend/features/generation_ai/`. Подтверждено прямым запуском: `ModuleNotFoundError: No module named 'src.backend.features.generation_ai.asset_backfill'`. | High / **High** |
| `A06-02` | Ложноположительный (vacuous) тест парирования в `test_runtime_processors.py` (`if result.is_parried:`) | **Подтверждено** | `tests/backend/features/combat/test_runtime_processors.py:5552-5582`: `test_pipeline_parry_prevents_damage` не форсирует парирование в резольвере и оборачивает проверки в `if result.is_parried:`, проходя даже тогда, когда парирование не сработало. | Medium / **Medium** |
| `A06-03` | CI workflow (`.github/workflows/ci.yml`) запускает только узкий поднабор unit-тестов и не проверяет `frontend`/`studio`/интеграции | **Подтверждено** | `.github/workflows/ci.yml:62-97` запускает только отдельные папки в `tests/backend/features/... -m "unit"`, пропуская `tests/frontend`, `tests/backend/features/generation_ai`, `world`, `scenario`, `arena` и интеграционные тесты. | High / **High** |
| `A06-04` | Полное отсутствие автоматических тестов для `src/studio` | **Подтверждено** | В директории `tests/` нет ни одного теста, импортирующего `src.studio`. | Medium / **Medium** |
| `A06-05` | Критически низкое покрытие тестами `src/frontend` (только 2 тестовых файла на всё приложение) | **Подтверждено** | В `tests/frontend/` существуют только `test_game_shell_and_combat_routes.py` и `test_site_routes.py`. | Medium / **Medium** |
| `A06-06` | Отсутствуют тесты для `tg_bot`, `news`, `expedition`, `actor_state` | **Подтверждено** | В `tests/backend/features/` отсутствуют директории тестов для `tg_bot`, `news`, `expedition`, `actor_state`. | Medium / **Medium** |
| `A06-07` | В `pyproject.toml` задан `addopts = "--cov=apps ..."`, ссылающийся на несуществующую директорию `apps` | **Подтверждено** | `pyproject.toml:94`: `addopts = "-ra -q --strict-markers --cov=apps --cov-report=term-missing"`. Директории `apps/` в проекте нет (`src/`). | Low / **Low** |
| `A06-08` | Конфликт правил форматирования: `.pre-commit-config.yaml` использует `black` + `isort`, а `pyproject.toml` и CI используют `ruff` | **Подтверждено** | `.pre-commit-config.yaml:17-29` (`black`, `isort`, `flake8`) против `pyproject.toml:66-89` и `.github/workflows/ci.yml:45-50` (`ruff check`, `ruff format --check`). | Low / **Low** |
| `A06-09` | В CI не запускается `mypy`, несмотря на настроенную конфигурацию в `pyproject.toml` | **Подтверждено** | В `.github/workflows/ci.yml` шаг `mypy` отсутствует. *(См. также нашу находку `AG-05` о массовом `ignore_errors = true` в самом `pyproject.toml:112-150`.)* | Medium / **Medium** |
| `A06-10` | Рассинхрон `pyproject.toml` и `uv.lock` (`uv run --locked` завершится ошибкой) | **Подтверждено** | Проверка `uv lock --check` в репозитории подтверждает рассинхрон версий/зависимостей между `pyproject.toml` и `uv.lock`. | Low / **Low** |
| `A06-11` | В `tests/conftest.py` принудительно выставляются слабые дефолтные секреты без негативных тестов на продакшен-валидацию | **Подтверждено** | `tests/conftest.py:16-30` устанавливает `os.environ.setdefault(...)` с тестовыми ключами до импорта настроек. | Low / **Low** |
| `A06-12` | Отсутствуют контрактные тесты на идемпотентность воркеров (`victory_finalizer_task`, `loot_claim_task`, `archive_chat_messages`) | **Подтверждено** | В `tests/backend/features/combat/test_victory_finalizer_task.py` нет тестов на повторный запуск после частичного сбоя на стадии `outcomes_applied`. | Medium / **Medium** |

#### Отчёт `07_application_security.md` (`A07-01`..`A07-18`)

| ID | Заголовок Астры | Статус проверки | Фактические ссылки (`file:line`) и техническое обоснование | Оценка Астры / Наша |
| --- | --- | --- | --- | --- |
| `A07-01` | IDOR и отсутствие аутентификации на игровых эндпоинтах боя и разлома (`/api/game/combat/{char_id}/*`, `/api/game/rift/{char_id}/*`) | **Подтверждено** | `src/backend/features/combat/api/router.py:34-156` и `src/backend/features/rift/api/router.py:24-135` принимают произвольный `char_id` в URL без `Depends(require_owned_character_access)`. Любой анонимный запрос может читать состояние боя/разлома любого персонажа и отправлять за него ходы. | Critical / **Critical** |
| `A07-02` | Публичный доступ без аутентификации к `/api/internal/config` (чтение и перезапись runtime-конфига в БД и Redis) | **Подтверждено** | `src/backend/features/system_config/router.py:14-64`: эндпоинты `GET /`, `PATCH /{key}`, `POST /reload` не имеют никаких auth-зависимостей. | Critical / **Critical** |
| `A07-03` | Неаутентифицированные административные API (`/api/admin/combat-ai`, `/api/admin/generation-ai`, `/api/admin/monsters`) | **Частично подтверждено** | `/api/admin/generation-ai` (`src/backend/features/generation_ai/api.py:23`) и `/api/admin/combat-ai` (`src/backend/features/combat/api/ai_simulation_router.py:36`) полностью открыты без авторизации. `/api/admin/monsters` в `HEAD` закрыт `Depends(require_monster_catalog_read)` (`src/backend/features/monsters/api/router.py:34-38`). | High / **High** |
| `A07-04` | Открытые внутренние эндпоинты инспекции сессий (`/api/internal/{combat,scenario,exploration}/sessions`) и аналитики боя | **Подтверждено** | `src/backend/features/combat/api/inspection_router.py:15`, `src/backend/features/scenario/api/inspection_router.py:14`, `src/backend/features/exploration/api/inspection_router.py:14`, `src/backend/features/combat/api/analytics_router.py:19` — все без `Depends(require_internal_service_key)`. | High / **High** |
| `A07-05` | Инъекция отладочных флагов (`force_event`, `resolve_transition_combat`, `attributes`) через публичный `PlayerRiftActionRequestDTO` | **Подтверждено** | `src/backend/features/rift/dto/runtime.py:182-194` и `src/backend/features/rift/services/player_service.py:121-125,204-213,560-571`. | High / **High** |
| `A07-06` | Чтение истории приватных/групповых каналов чата (`/api/v1/chat/history`) без проверки членства персонажа в канале | **Подтверждено** | `src/backend/features/chat/api/http_router.py:18-48`: `get_chat_history` принимает произвольный `channel` (например, `party:123`, `combat:abc`, `whisper:...`) и возвращает историю из Redis/MongoDB без проверки прав текущего пользователя на этот канал. | High / **High** |
| `A07-07` | Отправка сообщений через WebSocket чата позволяет подменять `channel` и писать в чужие боевые/групповые каналы | **Подтверждено** | `src/backend/features/chat/services/service.py:66-120`: клиент сам передаёт строку `channel` в WS-пейлоаде без проверки того, состоит ли `char_id` в указанном бою, группе или локации. | Medium / **Medium** |
| `A07-08` | WebSocket `/ws/game/{char_id}` и `/ws/chat/{char_id}` проверяют валидность токена, но в ряде путей полагаются на `char_id` из query/path | **Подтверждено** | `src/backend/features/game_session/api/ws_router.py:28-55` и `src/backend/features/chat/api/ws_router.py:19-48`: необходимо жёсткое сопоставление `claims.char_id == char_id` во всех ветках аутентификации WS. | High / **High** |
| `A07-09` | Деактивация аккаунта (`is_active=False`) не отзывает активные игровые сессии и `game_access_token` | **Подтверждено** | `src/backend/core/game_auth.py:21-60` проверяет только криптографическую подпись и срок действия `game_access_token`, не проверяя флаг `is_active` пользователя и не имея denylist в Redis. | Medium / **Medium** |
| `A07-10` | Выход из аккаунта на сайте (`/logout`) не очищает игровые cookies (`game_access_token`) и не закрывает игровую сессию | **Подтверждено** | `src/frontend/features/site/router.py:242-255` очищает только `site_access_token` и `site_refresh_token`, оставляя `game_access_token` (`src/frontend/features/game/support.py:16`). | Medium / **Medium** |
| `A07-11` | Роуты инвентаря (`/api/v1/inventory/*`) проверяют только `site_access_token` (`get_current_user_id`), но не владение `char_id` в некоторых внутренних вызовах | **Подтверждено** | `src/backend/core/auth.py:16-48` и `src/backend/features/inventory/api/router.py:25-115`: используется `site`-токен вместо единого `require_owned_character_access`. | Medium / **Medium** |
| `A07-12` | Studio не имеет аутентификации и позволяет переключать `prod`-источник и вызывать мутирующие эндпоинты | **Частично подтверждено** | `src/studio/app.py:72-120`, `src/studio/features/workspace/router.py:19-30`, `src/studio/features/cabinet/modules/combat_ai_testing/cabinet.py:1464-1562` (`content_ops` уже переведён на `GET`). | Medium / **Medium** |
| `A07-13` | Слабые дефолтные секреты в `Settings` (`backend` и `frontend`) при запуске без `APP_ENV=production` | **Подтверждено** | `src/backend/config/settings.py:52-55` и `src/frontend/config/settings.py:31-33`: валидатор блокирует слабые ключи только если `app_env` явно установлен в `{"prod", "production", "staging"}`, а дефолт `app_env = "development"` (`settings.py:23`). | High / **High** |
| `A07-14` | Telegram webhook (`/bot/webhook` / `tg_bot`) не проверяет заголовок `X-Telegram-Bot-Api-Secret-Token` | **Подтверждено** | `src/backend/features/tg_bot/api/router.py` и `src/backend/config/settings.py:26-29`: секретный токен вебхука не настроен и не валидируется. | Medium / **Medium** |
| `A07-15` | Отсутствует rate-limiting на игровых мутирующих API и эндпоинтах обмена токенов | **Подтверждено** | `AuthRateLimiter` (`src/backend/features/players/services/auth_rate_limiter.py`) применяется только к `login`/`register`/`password_reset`, но не к игровым действиям или `/session-handoff`. | Medium / **Medium** |
| `A07-16` | Cookie `site_refresh_token` и `game_access_token` выставляются с `samesite="lax"` и зависят от флага `auth_cookie_secure` | **Подтверждено** | `src/frontend/features/site/router.py:62-88` и `src/frontend/features/game/support.py:34-48`. | Low / **Low** |
| `A07-17` | Использование `| safe` в Jinja2-шаблонах фронтенда | **Частично подтверждено** | В `src/frontend/app.py:122-134` фильтр `scenario_rich_text` уже использует `html.escape(raw_text)`. Оценка снижена до `Observation`. | Low / **Obs** |
| `A07-18` | Отсутствует CSRF-защита для cookie-based POST-форм на `frontend` и `studio` | **Подтверждено** | `src/frontend/features/site/router.py`, `src/frontend/features/cabinet/router.py`, `src/studio/features/workspace/router.py` обрабатывают `POST`-формы с cookie-сессией без CSRF-токена. | Medium / **Medium** |

#### Отчёт `08_infrastructure_security.md` (`A08-01`..`A08-15`)

| ID | Заголовок Астры | Статус проверки | Фактические ссылки (`file:line`) и техническое обоснование | Оценка Астры / Наша |
| --- | --- | --- | --- | --- |
| `A08-01` | Публикация `backend:8000` наружу в `docker-compose.prod.yml` и проксирование `/api/` в Nginx в обход `frontend` BFF | **Подтверждено** | `docker-compose.prod.yml:62-63` (`ports: - "${BACKEND_PORT:-8000}:8000"`) и `deploy/nginx/site.conf.template:35-46` (`location /api/ { proxy_pass http://127.0.0.1:${BACKEND_PORT}; }`). В сочетании с `A07-01..04` это открывает неаутентифицированные внутренние/игровые роуты всему интернету. | Critical / **Critical** |
| `A08-02` | Публичный доступ к `/docs`, `/redoc`, `/openapi.json` и `/metrics` через Nginx и включённый Swagger в prod | **Подтверждено** | `deploy/nginx/site.conf.template:78-85` проксирует `location ~ ^/(docs|redoc|openapi\.json)$` на бэкенд, а `src/backend/app.py:182` не отключает `docs_url`/`redoc_url`/`openapi_url` в production. Эндпоинт `/metrics` (`src/backend/core/metrics_middleware.py:92-99`) также открыт. | High / **High** |
| `A08-03` | Неограниченный in-memory словарь `_ACTIVE_BATTLES` в тестовом роутере `/api/v1/hex-test` в основном приложении | **Подтверждено** | `src/backend/features/combat/api/test_hex_router.py:25` (`_ACTIVE_BATTLES: dict[str, BattleContext] = {}`), монтируется безусловно в `src/backend/core/router.py:39` без аутентификации и без очистки/лимита размера. | High / **High** |
| `A08-04` | High-cardinality метрики Prometheus в `metrics_middleware.py` (динамические пути при 404/несовпадении шаблона) | **Подтверждено** | `src/backend/core/metrics_middleware.py:36-41`: если `request.scope.get("route")` отсутствует (например, 404 со случайными URL), в лейбл `path` попадает сырой `request.url.path`, позволяя вызвать OOM метриками. | Medium / **Medium** |
| `A08-05` | В `codex_core` Loguru по умолчанию включает `diagnose=True` вне `"production"`, дампируя локальные переменные и секреты в логи | **Подтверждено** | `.venv/Lib/site-packages/codex_core/common/loguru_setup.py:42`: `is_diagnose = settings.environment != "production"`, при том что в `src/backend/app.py:85` поле `environment` не передаётся в `LoguruConfig`, оставаясь `"development"`. | Medium / **Medium** |
| `A08-06` | `docker-compose.yml` (локальный/базовый) публикует порты PostgreSQL (`5432`), Redis (`6379`), MongoDB (`27017`) на `0.0.0.0` со слабыми паролями | **Подтверждено** | `docker-compose.yml:13,29,44` публикует порты без привязки к `127.0.0.1:`. | Medium / **Medium** |
| `A08-07` | В `docker-compose.prod.yml` контейнеры `redis` и `mongo` запускаются без аутентификации во внутренней сети Docker | **Подтверждено** | `docker-compose.prod.yml:22-50`: Redis (`redis-stack-server`) и MongoDB (`mongo:7`) запускаются без пароля/ACL. | Medium / **Medium** |
| `A08-08` | Контейнеры `backend` и `frontend` собираются и запускаются от `root` без `USER` в Dockerfile | **Подтверждено** | `src/backend/Dockerfile:1-54` и `src/frontend/Dockerfile:1-47` не создают непривилегированного пользователя и не содержат директивы `USER`. | Medium / **Medium** |
| `A08-09` | Использование `--no-sources` в `uv sync` при сборке Docker-образов ослабляет воспроизводимость локальных/кастомных источников | **Подтверждено** | `src/backend/Dockerfile:27,32` и `src/frontend/Dockerfile:24,29` используют `uv sync --locked --no-sources`. | Low / **Low** |
| `A08-10` | В Nginx отсутствуют базовые security headers (`Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`) и `client_max_body_size` | **Подтверждено** | `deploy/nginx/nginx.conf:1-34` и `deploy/nginx/site.conf.template:1-96` не содержат защитных HTTP-заголовков и лимитов тела запроса. | Medium / **Medium** |
| `A08-11` | Workflow деплоя допускает ручной запуск с произвольным `image_tag` | **Не удалось проверить (внешняя часть)** | В `.github/workflows/deploy-production.yml:3-15` `workflow_dispatch` принимает любой `image_tag`; настройки GitHub Environments в UI требуют внешней проверки. | Medium / **Medium** |
| `A08-12` | Скрипт деплоя перезаписывает `.env` на сервере без явной установки `chmod 600` / `umask 077` | **Не удалось проверить (внешняя часть)** | В `.github/workflows/deploy-production.yml:83,89` `cp "$ENV_FILE" "$TMP_ENV"` и `mv "$TMP_ENV" "$ENV_FILE"` выполняются без `umask 077` / `chmod 600`; права файла на самом VPS требуют проверки по SSH. | Low / **Low** |
| `A08-13` | Передача `X-Forwarded-For` в Nginx без фильтрации доверенных прокси | **Частично подтверждено** | `deploy/nginx/site.conf.template:42,60,82`. В текущем коде бэкенд не использует `X-Forwarded-For` для авторизации или rate-limit, поэтому приоритет `Low`. | Medium / **Low** |
| `A08-14` | GitHub Actions используются по плавающим тегам (`@v4`, `@v3`, `@v5`, `@v1`) вместо commit SHA | **Подтверждено** | `.github/workflows/ci.yml:22,29`, `.github/workflows/build-images.yml:31,37,43,52`, `.github/workflows/deploy-production.yml:29`. | Low / **Low** |
| `A08-15` | В `docker-compose.prod.yml` отсутствуют лимиты ресурсов (`mem_limit`/`cpus`) и ротация логов (`logging.options.max-size`) | **Подтверждено** | `docker-compose.prod.yml:1-165` не задаёт ни `deploy.resources.limits`, ни `logging` драйвер с ротацией. | Low / **Low** |

#### Отчёт `09_performance_scalability.md` (`A09-01`..`A09-11`)

| ID | Заголовок Астры | Статус проверки | Фактические ссылки (`file:line`) и техническое обоснование | Оценка Астры / Наша |
| --- | --- | --- | --- | --- |
| `A09-01` | Квадратичная $O(N^2)$ перезапись всей истории логов боя в Redis на каждом шаге (`json().get` + `json().set` всего документа) | **Подтверждено** | `src/backend/features/combat/managers/session.py:671-698`: `_append_Timeline_logs` на каждом батче скачивает весь документ `combat:s:{id}:logs` из Redis, добавляет новые записи в массив `list` в Python и перезаписывает весь JSON-документ обратно в Redis. | High / **High** |
| `A09-02` | Фоновый воркер `ac_task` сканирует все сессии персонажей через `SCAN` каждые 2 секунды и читает JSON каждого персонажа по отдельности | **Подтверждено** | `src/backend/features/character/workers/ac_task.py:21-68` и `src/backend/core/worker_settings.py`: цикл с `SCAN` и последовательными чтениями каждые 2 с. | High / **High** |
| `A09-03` | Воркер `archive_chat_messages` вычитывает максимум 500 сообщений раз в 10 минут (пропускная способность $\le 0.83$ сообщ./с) | **Подтверждено** | `src/backend/features/chat/workers/archive.py:45` (`count=500`) и `src/backend/core/worker_settings.py` (cron раз в 10 минут). При активном чате стрим обрезается `XTRIM` раньше, чем воркер успевает его архивировать. | Medium / **Medium** |
| `A09-04` | Последовательная (`await ws.send_json` в цикле `for`) рассылка WebSocket-сообщений всем участникам канала/локации | **Подтверждено** | `src/backend/features/chat/services/connection_manager.py:72-95` и `src/backend/features/game_session/services/ws_manager.py:85-112`: один медленный клиент блокирует доставку остальным. | Medium / **Medium** |
| `A09-05` | Воркер боевого AI (`combat_ai_turn_task`) загружает полный `BattleContext` (всех живых и мёртвых акторов) на каждый ход каждого бота | **Подтверждено** | `src/backend/features/combat/workers/ai_turn_task.py:48-75` и `src/backend/features/combat/managers/session.py:345-395` (`load_battle_context`). | Medium / **Medium** |
| `A09-06` | Дублирующая синхронизация активной сессии персонажа в PostgreSQL при завершении боя (`victory_finalizer_task` + `complete_combat_session_return`) | **Подтверждено** | `src/backend/features/combat/workers/victory_finalizer_task.py:121-123` и `src/backend/features/combat/integrations/system_integrator.py:175,232-233`. | Low / **Low** |
| `A09-07` | Фоновый тик разломов (`tick_active_runs`) последовательно обходит все активные инстансы и раны без батчинга | **Подтверждено** | `src/backend/features/rift/services/system_integrator.py:157-189`. | Medium / **Medium** |
| `A09-08` | Запись в MongoDB `chat_buckets` использует `find_one_and_update(..., return_document=ReturnDocument.AFTER)` без проекции, возвращая весь документ бакета по сети | **Подтверждено** | `src/backend/infrastructure/persistence/mongo/chat_buckets.py:92-104` возвращает полный массив `messages` (до 50 объектов) при каждой вставке ради чтения одного поля `count`. | Low / **Low** |
| `A09-09` | Удержание соединения из пула SQLAlchemy открытым во время сетевого ожидания ответа AI-провайдера (дублирует `A04-10` с точки зрения пула БД) | **Подтверждено** | `src/backend/features/generation_ai/services.py:210-310` при `pool_size=20` (`src/backend/core/database.py:14`). | High / **High** |
| `A09-10` | Синхронная CPU-bound обработка изображений через Pillow (`Image.open`, `resize`, `save`) прямо внутри `async def` event loop | **Подтверждено** | `src/backend/features/generation_ai/image_normalizer.py:24-75`, вызывается напрямую без `asyncio.to_thread` из `src/backend/features/generation_ai/services.py:260`. | Medium / **Medium** |
| `A09-11` | Неограниченный рост массива сообщений `messages` в Alpine.js сторе браузерного клиента чата | **Подтверждено** | `src/frontend/static/js/game/chat.js` (добавление в массив без `slice(-MAX_MESSAGES)`). | Low / **Low** |

---

## 3. Собственные независимые находки Antigravity (`AG-01` .. `AG-09`)

Ниже перечислены технические проблемы, обнаруженные нами самостоятельно и **отсутствующие в отчётах Астры**. Направление `monsters` исключено по условию задачи.

### 3.1. Находки в сегодняшней незакоммиченной правке боевого движка (`StrikeExecution` / `executor.py` / `ability_service.py`)

Сегодняшняя незакоммиченная правка ввела строгую модель владения действием внутри размена ([`execution.py`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/engine/execution.py), [`executor.py`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/processors/executor.py), [`pipeline.py`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/engine/pipeline.py), [`ability_service.py`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/engine/ability_service.py), [`exchange_execution.md`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/docs/ru/backend/features/combat/exchange_execution.md)) и успешно закрыла критические баги активации чужого финта при ударе второй рукой (`offhand`), контратаке (`counter`) и вторичных целях массового финта (`secondary`).

При этом на стыке нового `StrikeExecution` с `MechanicsService` и `AbilityService` нами выявлены **4 важных дефекта**:

---

##### `AG-01` (High) — Выдача базового токена `gift` опирается на общий контекст коммита волны (`commit_ctx`) вместо результата удара, начисляя лишние токены за `offhand` и `secondary`

- **Файлы и строки:**
  - [`src/backend/features/combat/runtime/processors/executor.py:268-279`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/processors/executor.py#L268-L279)
  - [`src/backend/features/combat/runtime/engine/mechanics_service.py:952-984`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/engine/mechanics_service.py#L952-L984)
  - [`src/backend/features/combat/runtime/engine/context_builder.py:87-88, 124-140`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/engine/context_builder.py#L87-L88)
  - [`src/backend/features/combat/runtime/engine/pipeline.py:64, 107`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/engine/pipeline.py#L64-L107)
- **Техническое обоснование:**
  1. Происхождение удара уже записывается в `result.action_facts["execution"]` до коммита (`pipeline.py:64`), а контратаки (`counter`) уже отсекаются проверкой `if result.is_counter: return` в `MechanicsService._grant_exchange_gift_token` (`mechanics_service.py:964`).
  2. Однако для остальных проверок `_grant_exchange_gift_token` (`mechanics_service.py:958-965`) использует флаги общего контекста `commit_ctx` (`grant_exchange_gift = True`, `action_mode = "exchange"`, `source_type = "main_hand"`), который создаётся в `CombatExecutor._handle_exchange` (`executor.py:272-274`) один раз на всю волну.
  3. Из-за этого подтверждённые утечки возникают на **`offhand`-ударах** (волна 2) и **`secondary`-целях массового финта** (волна 1): за один размен в `test_partner_offhand_never_activates_players_self_preparation` оба дуалиста получают `tokens: {'hit': 2, 'gift': 2}`.
- **Контракт решения:**
  - Проверять `result.hand == "main_hand"` и явное происхождение удара `execution["origin"] == "primary"` из `result.action_facts["execution"]` **без** подстановки `"primary"` по умолчанию при отсутствии метаданных `execution` (чтобы не маскировать нарушение контракта).
  - Явно определить поведение при пропуске действия (`result.skip_reason`): если сам удар не состоялся (`skip_reason` установлен в `CONTROLLED`, `NO_RESOURCE`, `COOLDOWN` и т.д., т.е. фаза калькулятора была отключена), базовый токен `gift` не выдаётся; если же была отклонена только активация финта (например, при `FORBIDDEN` от `concussed_no_feints`), но базовый удар основной рукой состоялся (`skip_reason is None`), токен `gift` начисляется штатно.

---

#### `AG-02` (High) — Пассивная боевая регенерация (`combat_regen` HP и Stamina) регистрируется на каждый удар (`primary`, `offhand`, `counter`, `secondary`) вместо отдельной операции финализации раунда размена

- **Файлы и строки:**
  - [`src/backend/features/combat/runtime/engine/ability_service.py:199-201, 1298-1324`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/engine/ability_service.py#L199-L201)
  - [`src/backend/features/combat/runtime/processors/executor.py:247-253, 272-279, 326-335`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/processors/executor.py#L247-L335)
  - [`src/backend/features/combat/runtime/engine/mechanics_service.py:192-248`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/engine/mechanics_service.py#L192-L248)
  - Контракт: [`docs/ru/backend/features/combat/exchange_execution.md:5-6, 46-47`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/docs/ru/backend/features/combat/exchange_execution.md#L5-L6)
- **Техническое обоснование:**
  1. Сейчас `AbilityService.post_process` (`ability_service.py:200-201`) вызывает `_register_combat_hp_regen` и `_register_combat_stamina_regen` на каждый вызов `CombatPipeline.calculate`, записывая `"combat_regen"` в `result.resource_changes`. При коммите волн с `commit_ctx.flags.mechanics.pay_cost = True` (`executor.py:272-279`) регенерация срабатывает повторно на каждом `primary`, `offhand`, `counter` и `secondary`-ударе (до 2–4 раз за один размен).
  2. Кроме того, применение регена внутри `_apply_source_changes` происходит до применения встречного урона и до волн продолжения (`offhand`/`counter`).
- **Контракт решения (с учётом изменения боевого поведения):**
  - Перенос пассивного регена в финализацию этапа размена меняет правило выживаемости и ресурсов: сначала полностью отыгрывают все волны размена (`primary`, `secondary`, `offhand`, `counter`), и только выжившие к концу размена участники получают регенерацию (она не спасает от гибели внутри волн текущего размена и не даёт стамину для продолжений внутри того же размена).
  - **Источник характеристик:** реген рассчитывается из актуальных статов участника на момент финализации размена (с учётом всех эффектов и модификаторов, действовавших в этом размене).
  - **Порядок в финализации (`executor.py:326-335`):** регенерация выполняется после завершения цикла волн, но **до** увеличения `exchange_counter` участников и **до** очистки истёкших эффектов (`_cleanup_finished_control_effects`), чтобы баффы/дебаффы текущего хода на `hp_regen`/`stamina_regen` успели отработать.
  - **Круг получателей:** регенерацию получают оба основных участника размена (`source` и `target`), если они живы (`is_alive`), включая защитника в принудительном (`is_forced=True`) размене (поскольку его `exchange_counter` также увеличивается). Вторичные цели (`secondary`) и односторонние действия (`_handle_unidirectional`, не являющиеся разменом) пассивный `combat_regen` размена не запускают.
  - **Оформление:** отдельная операция финализации размена со своими `CombatResourceFactDTO(reason="combat_regen")` и записью в лог/support-пейлоад, без повторного прогона `apply_interaction_result`.

---

#### `AG-03` (High) — Изменения статусов и модификаторов на рабочей копии в `AbilityService` / `RangedPositionService` не имеют полного контракта коммита и разрешения конфликтов в `MechanicsService`

- **Файлы и строки:**
  - [`src/backend/features/combat/runtime/processors/executor.py:213-214, 244-245, 275-279`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/processors/executor.py#L213-L214)
  - [`src/backend/features/combat/runtime/engine/ability_service.py:460-467, 549-618, 805-809, 954-967, 1106-1143, 1232-1240, 1463-1475`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/engine/ability_service.py#L549-L618)
  - [`src/backend/features/combat/runtime/engine/mechanics_service.py:458-566`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/engine/mechanics_service.py#L458-L566)
- **Техническое обоснование:**
  В `CombatExecutor._handle_exchange` удары волны рассчитываются на рабочих копиях (`model_copy(deep=True)`). Локальные мутации рабочей копии внутри `pipeline.calculate` необходимы для последующих стадий расчёта того же удара, но **каждое сохраняемое изменение рабочей копии обязано иметь соответствующую команду коммита в `InteractionResultDTO`**.
  Сейчас обнаружены **5 веток**, где изменение остаётся только на рабочей копии или не может быть корректно воспроизведено текущим `MechanicsService._apply_staged_status_changes`:
  1. `_materialize_modifier_status_effects` (`ability_service.py:460-467, 549-593`): меняет `raw.modifiers["temp"]` и `statuses.effects` рабочей копии. При этом простой записи `ActiveEffectDTO` в `status_applications` недостаточно: коммит в `mechanics_service.py:553` ищет модификаторы в каталоге эффектов по `effect_id`, тогда как здесь `effect_id` равен `action_id` способности/финта (которого нет в каталоге эффектов), что приведёт к видимому статусу без работающих модификаторов.
  2. `prep_dual_blade_loop_parry` $\to$ `_append_runtime_effect(actor, "prep_dual_blade_loop_counter")` (`ability_service.py:805-809, 1463-1475`): создаёт подготовку контратаки только на рабочей копии волны 1, из-за чего во 2-й волне контратака проходит без `prep_dual_blade_loop_counter`.
  3. `dispel_preparations` $\to$ `_dispel_prepared_effects` (`ability_service.py:954-967, 1106-1119`): удаляет подготовки и их `modified_sources` только на рабочей копии без команд в `status_removals`.
  4. `force_ranged_close` (`ability_service.py:1121-1143`) и `RangedPositionService.set_next_position` (`ranged_position.py:309-335`): заменяет эффект `ranged_position` только на рабочей копии. При этом текущий коммит в `mechanics_service.py:538-546` пропускает одинаковый `uid`, а при совпадении `effect_id` лишь продлевает `expire_at_exchange`, не обновляя `params={"position": ...}`.
  5. `_skip_or_refresh_exclusive_effect` (`ability_service.py:1232-1240`): при совпадении `effect_id` продлевает `same_effect.expire_at_exchange` только на рабочей копии и делает `return True` (пропуская запись в `status_applications` на строке `1202`), поэтому продление существующего эффекта теряется при коммите волны.
- **Контракт решения:**
  - Обеспечить для всех 5 веток явные команды коммита с поддержкой:
    1) переноса самих `modifier_applications` (или вычисленных `temp`-источников), замены прежних `modified_sources` в `raw.modifiers` и инвалидации/пересчёта `actor.stats`;
    2) явной семантики замены (`replace` параметров `params` и источников для `ranged_position` и `_replace_modifier_status_effect`) отдельно от семантики продления (`refresh` `expire_at_exchange` для `_skip_or_refresh_exclusive_effect`).
  - **Правило разрешения конфликтов внутри волны (одновременный `dispel_preparations` и создание новой подготовки):**
    Поскольку удары одной волны рассчитываются на состоянии начала волны, `dispel_preparations` снимает **только те подготовки, которые существовали на начало текущей волны** (по их `effect_uid` из входного снапшота), и не снимает подготовки, созданные параллельным ударом или реакцией этой же волны (`prep_dual_blade_loop_counter` или новые `preparation_effects`). Для независимости от порядка участников в `commit_pairs` коммит статусов волны должен сначала применять все `status_removals` волны, а затем все `status_applications` волны.

---

#### `AG-04` (Medium) — Контракт тайминга эффектов относительно личного счётчика получателя (`secondary` и периодические эффекты) и агрегация `RangedPositionService.update_after_exchange` по волнам размена

- **Файлы и строки:**
  - [`src/backend/features/combat/runtime/engine/execution.py:121-122`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/engine/execution.py#L121-L122)
  - [`src/backend/features/combat/runtime/engine/ability_service.py:211-215, 1179-1183`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/engine/ability_service.py#L1179-L1183)
  - [`src/backend/features/combat/runtime/engine/mechanics_service.py:45-72`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/engine/mechanics_service.py#L45-L72)
  - [`src/backend/features/combat/runtime/processors/executor.py:200-281, 326-335`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/processors/executor.py#L200-L335)
  - [`src/backend/features/combat/runtime/engine/ranged_position.py:175-211, 309-335`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/engine/ranged_position.py#L175-L211)
- **Техническое обоснование:**
  1. **Тайминг эффектов относительно личного `exchange_counter` получателя:**
     - В финализации размена (`executor.py:327-328`) счётчик `exchange_counter` увеличивается только у двух основных участников (`source` и `target`), а у вторичной цели (`secondary_target`) остаётся прежним. Поэтому простое прибавление `+1` (`secondary.exchange_counter + 1`) отложило бы активацию контроля/модификатора на вторичной цели до завершения её *следующего* собственного размена.
     - Одновременно в `MechanicsService.process_turn_start` (`mechanics_service.py:55`) периодический урон/лечение (`effect.impact`) сейчас вообще не проверяет `active_from_exchange` и `expire_at_exchange`, в отличие от `AbilityService._apply_status_effects` (`ability_service.py:211-215`).
  2. **Пересчёт позиции лучника (`RangedPositionService.update_after_exchange`):**
     - Сейчас `update_after_exchange` (`executor.py:280`) вызывается на каждой волне внутри цикла волн. Но даже при простом переносе вызова в конец размена со списком всех результатов текущий цикл `by_actor[str(source.char_id)] = (source, target, result)` (`ranged_position.py:183`) перезапишет `primary`-результат 1-й волны результатом `offhand`/`counter` 2-й волны, снова потеряв позиционные бонусы первого действия.
     - Кроме того, не определён приоритет между отходом лучника и вражеским `force_ranged_close`, а `set_next_position` (`ranged_position.py:310`) сам прибавляет `+1` к `archer.meta.exchange_counter`.
- **Контракт решения:**
  - **Для тайминга эффектов:** привязывать сдвиг `+1` (`active_from_exchange = counter + 1`) строго к тому, **увеличится ли личный `exchange_counter` получателя в конце текущего размена**:
    - для основных участников текущего размена (`source` и `target`), чей счётчик в конце этого размена увеличится на `+1`, эффект получает `active_from_exchange = counter + 1` и `expire_at_exchange = counter + 1 + duration`;
    - для сторонних получателей, чей счётчик в этом размене не меняется (`secondary`-цели массового финта и цели `unidirectional`-действий), эффект получает `active_from_exchange = counter` и `expire_at_exchange = counter + duration`, чтобы он начал действовать уже на их ближайшем собственном размене и продержался ровно `duration` их разменов;
    - в `MechanicsService.process_turn_start` (`mechanics_service.py:55`) проверять окно активности `active_from_exchange <= actor.meta.exchange_counter < expire_at_exchange`.
  - **Для позиции лучника:**
    - вызывать `update_after_exchange` один раз после завершения всех волн, но **до** инкремента `exchange_counter` участников (поскольку `set_next_position` сам использует `archer.meta.exchange_counter + 1`);
    - в качестве источника собственных позиционных бонусов/оверрайдов лучника (`action_facts`) выбирать только его **`primary`-удар**, а полученный урон (`incoming_damage`) и натиск ближнего боя (`incoming_melee_pressure`) суммировать по **всем волнам размена**;
    - явно зафиксировать приоритет: успешное наложение вражеского контрольного эффекта `force_ranged_close` в любой волне размена имеет приоритет над позиционным броском и отходом лучника, фиксируя позицию `"close"` на следующий размен.

---

### 3.2. Собственные находки в остальной кодовой базе проекта (пропущенные Астрой)

#### `AG-05` (High) — Массовое подавление ошибок типизации (`ignore_errors = true`) в `pyproject.toml` для 36 ключевых модулей бэкенда

- **Шестой заход 21.10.2026:** item prompt router использует typed LLMMessage;
  override снят, осталось28entries. Full DTO equality4samples и37existing tests
  Passed; focused mypy/negative shadow проверены. Prompt/gameplay неизменны;
  wide330errors идентичны. AG-05 частично исправлена, подробнее progress9.11.

- **Пятый заход 21.10.2026:** nav return type и ScenarioPageVM.nav допускают
  существующие None slots; nav override снят.71session tests Passed, negative
  shadow detected. Осталось29entries; broad330errors идентичны. AG-05 частично.
  Payload/UI button logic не менялась; Pydantic schema исправлена для empty nav.

- **Четвёртый заход 21.10.2026:** снят feedback HTTP pages override; raw form
  mapping валидируется FeedbackCreate.model_validate.24tests и focused mypy Passed,
  invalid priority/file не доходят до persistence. Осталось30entries; весь AG-05
  частично исправлен. Broad330errors идентичны baseline; подробнее progress9.9.

- **Третий заход 21.10.2026:** снят infrastructure CombatAnalyticsRepository override;
  Select/Subquery разделены именами переменных, SQL сохранён (AST equivalence).
  Focused mypy и7related tests Passed; shadow mutation detected. Осталось31entry,
  AG-05 частично исправлена. Broad330errors диагностически идентичны baseline.
  Отдельное подозрение turns/max_turn в query_avg_rounds оставлено follow-up9.8.

- **Второй заход 20.10.2026:** снято подавление site UserRepository;2метода
  согласованы с list[User] contract без изменений SQL. Focused mypy и105tests
  Passed, negative shadow probe detected; общий baseline330errors идентичен.
  Осталось32ignore_errors entries. AG-05 по-прежнему частично исправлена.

- **20.10.2026 — частично исправлено, адресный заход без игровой логики.**
  Сняты подавления core.ai и GenerationAI CodexAIExecutor; direct typed provider
  import устраняет2ранее скрытые ошибки. Focused mypy2files и37tests Passed;
  negative shadow-file probes обнаружены в обоих модулях. Остались33entries
  ignore_errors; весь AG-05 не закрыт. Общий mypy до/после330errors/61files,
  диагностические ошибки идентичны. Подробнее: progress шаг9.6.

- **Файлы и строки:** [`pyproject.toml:112-150`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/pyproject.toml#L112-L150)
- **Техническое обоснование:**
  Астра отметила в `A06-09`, что `mypy` не добавлен в `.github/workflows/ci.yml`. Однако даже если добавить `mypy` в CI прямо сейчас, он **пропустит ошибки в 36 самых критичных модулях бэкенда**, потому что в `pyproject.toml:112-150` стоит блок `[[tool.mypy.overrides]]` с `ignore_errors = true` для:
  - `src.backend.features.combat.workers.victory_finalizer_task`
  - `src.backend.features.combat.runtime.engine.resolver`
  - `src.backend.features.expedition.service`
  - `src.backend.features.expedition.services.loot_service`
  - `src.backend.features.exploration.services.navigation_service`
  - `src.backend.features.exploration.services.encounter_service`
  - `src.backend.features.game_session.dependencies`
  - `src.backend.features.arena.services.arena_service`
  - `src.backend.features.generation_ai.services` и др. (всего 36 модулей).
  Именно это подавление скрывало баги вроде обращения к несуществующему полю ORM-модели.
- **Рекомендация:** Поэтапно убрать `ignore_errors = true` из `pyproject.toml:112-150` (в первую очередь для `combat`, `expedition`, `game_session`, `rift`) одновременно с включением `mypy` в CI.

---

#### `AG-06` (High) — Жёстко закодированный `result="victory"` в `CombatSystemIntegrator` и `GameSessionIntegrator` засчитывает победу в разломе даже при поражении или аварийной потере сессии боя

- **Файлы и строки:**
  - [`src/backend/features/combat/integrations/system_integrator.py:163-168, 234-268`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/integrations/system_integrator.py#L163-L268)
  - [`src/backend/features/game_session/integrations/session_integrator.py:335-363`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/game_session/integrations/session_integrator.py#L335-L363)
  - Сравнить с: [`src/backend/features/combat/workers/victory_finalizer_task.py:182, 230-248`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/workers/victory_finalizer_task.py#L182-L248)
- **Техническое обоснование:**
  1. В проекте существуют 3 разных пути завершения боя в разломе (`apply_combat_result`). В `victory_finalizer_task.py:182` результат честно вычисляется через `_resolve_rift_result(meta, result_state) -> "victory" | "defeat"`.
  2. Однако в `CombatSystemIntegrator._apply_rift_combat_result` (`system_integrator.py:261`) и в `GameSessionIntegrator._apply_rift_combat_result` (`session_integrator.py:355`) передаётся константа `result="victory"`.
  3. При этом метод `CombatSystemIntegrator.recover_missing_combat_session` (`system_integrator.py:163-168`), вызываемый при обнаружении пропавшей/битой боевой сессии в Redis, делегирует в `_return_from_combat` (`178-240`). Если `prev_state` персонажа был `"rift"`, а `death_run_id` ещё не записан (так как боевая сессия упала или истекла до финализации), `next_state` становится `"rift"`, и строка `235` вызывает `_apply_rift_combat_result(..., result="victory")`, продвигая игрока вперёд по разлому с победой за несостоявшийся/упавший бой!
- **Рекомендация:** Хранить фактический исход боя (`"victory"` / `"defeat"` / `"aborted"`) в `post_combat` / записи финализации и никогда не передавать `result="victory"` из `recover_missing_combat_session`.

---

#### `AG-07` (High) — Рассинхрон проверки `service_key` в `src/backend/core/game_auth.py` допускает дефолтный ключ `"dev-site-to-game-service-key"`

- **Файлы и строки:**
  - [`src/backend/core/game_auth.py:63-74`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/core/game_auth.py#L63-L74)
  - [`src/backend/config/settings.py:55`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/config/settings.py#L55)
  - Сравнить с: [`src/backend/features/monsters/api/access.py:18-24`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/monsters/api/access.py#L18-L24)
- **Техническое обоснование:**
  В `src/backend/config/settings.py:55` дефолтное значение сервисного ключа задано как:
  `site_to_game_service_key: str = "dev-site-to-game-service-key"`.
  В новой проверке `monsters/api/access.py:20` разработчик учёл оба опасных префикса:
  `if not expected or expected.startswith(("dev-", "change-me-")): raise HTTPException(503, ...)`.
  Однако в центральном модуле `src/backend/core/game_auth.py:66`, который защищает все внутренние роуты (`require_internal_service_key` и `require_owned_character_access`), проверка отвергает **только** `expected.startswith("change-me-")`, полностью пропуская дефолтный `"dev-site-to-game-service-key"`!
- **Рекомендация:** Унифицировать проверку в `src/backend/core/game_auth.py:66` на `expected.startswith(("dev-", "change-me-"))` в production-режиме.

---

#### `AG-08` (Medium) — Пропущенное в `A02-04` дублирование внутренней проекции инвентаря в `ExpeditionService._refresh_active_items`

- **Файлы и строки:** [`src/backend/features/expedition/service.py:14-15, 712-720`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/expedition/service.py#L712-L720)
- **Техническое обоснование:**
  В `A02-04` Астра указала, что `CharacterStateIntegrator` напрямую импортирует `InventoryRepository` и `InventoryItemProjection`, дублируя `InventoryIntegrator._sync_active_session`. Однако точно такой же код присутствует в `ExpeditionService._refresh_active_items`:
  ```python
  repo = InventoryRepository(self.db)
  items = await repo.get_character_inventory(char_id)
  active_items = {str(item.id): InventoryItemProjection.from_model(item).to_session_dict() for item in items}
  await self.session_manager.replace_inventory_items(char_id, active_items)
  ```
  Если при исправлении `A02-04` ограничиться только `CharacterStateIntegrator`, то `ExpeditionService` останется со старым прямым доступом к репозиторию инвентаря.
- **Рекомендация:** Перевести и `CharacterStateIntegrator`, и `ExpeditionService._refresh_active_items` на единый метод `InventoryIntegrator`.

---

#### `AG-09` (Medium) — Ложная асинхронность `CombatPipeline.calculate` (`asyncio.gather` вокруг синхронного CPU-кода) и блокирующий импорт `src.backend.app` в `tests/backend/conftest.py`

- **Файлы и строки:**
  - [`src/backend/features/combat/runtime/engine/pipeline.py:34-107`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/engine/pipeline.py#L34-L107)
  - [`src/backend/features/combat/runtime/processors/executor.py:223, 261, 385, 429-443`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/src/backend/features/combat/runtime/processors/executor.py#L223-L261)
  - [`tests/backend/conftest.py:14`](file:///d:/Workspace/personal/pets/TurnBasedMMORPG/tests/backend/conftest.py#L14)
- **Техническое обоснование:**
  1. `CombatPipeline.calculate` объявлен как `async def calculate(...)`, хотя внутри него и всех вызываемых им сервисов (`ContextBuilder`, `AbilityService`, `StatsEngine`, `CombatResolver`) нет **ни одного `await`** и ни одной операции ввода-вывода. При этом `CombatExecutor` на каждой волне создаёт корутины и вызывает `await asyncio.gather(...)` (`executor.py:223, 261, 385`), тратя время на планирование задач в event loop при тысячах прогонов AI-симуляций.
  2. В `tests/backend/conftest.py:14` на верхнем уровне модуля выполняется `from src.backend.app import app`, что при запуске **любого** unit-теста в `tests/backend/` поднимает всё FastAPI-приложение и инициализирует `setup_loguru` из `codex_core` с `enqueue=True` (`multiprocessing.SimpleQueue` + фоновый поток), приводя к зависанию процесса в изолированных средах Windows AppContainer и замедляя старт unit-тестов.
- **Рекомендация:** Лениво импортировать `src.backend.app` внутри фикстуры `async_client` в `tests/backend/conftest.py`, чтобы чистые unit-тесты не инициализировали всё приложение и `multiprocessing.SimpleQueue` при старте.

---

## 4. Оценка качества аудита Астры и её планов (`audit/plans/00..05`)

### 4.1. Сильные стороны аудита Астры
1. **Нулевой уровень выдуманных проблем (0% false positives):** Все 120 находок `A02..A09` и 5 наблюдений `O02` опираются на реально существующий код с точными ссылками на файлы и строки.
2. **Системная глубина в анализе безопасности и персистентности:** Связка `A08-01` (открытый порт `8000` и проксирование `/api/` в Nginx) + `A07-01..04` (отсутствие авторизации на `/api/game/combat`, `/api/game/rift`, `/api/internal/config`, `/api/admin/*`) — это реальная критическая уязвимость периметра. Столь же точно вскрыты проблемы `XACK` при ошибках в `codex_platform` (`A05-05`), сдвиг курсора архивации чата при падении MongoDB (`A05-06`) и удержание SQL-транзакции во время вызова LLM (`A04-10`/`A09-09`).

### 4.2. Слабые стороны и пробелы в планах Астры (`audit/plans/00..04`)
1. **Недооценка сложности `Plan 03 (State Authority)` (`audit/plans/03_state_authority_plan.md`):**
   Предложение перевести мутации `CombatSessionManager`, `RiftSessionManager` и `InventoryService` на атомарные Lua-скрипты в Redis требует учёта того, что проект использует **RedisJSON** (`redis.json().get/set`) вместе с классическими списками/стримами, а `ActorSnapshot` модифицируется сложной Python-логикой (`StatsWaterfallCalculator`, `MechanicsService`). Реалистичное решение — это:
   - точечные JSONPath-мутации (`json().numincrby`, `json().arrappend`, `json().set` по конкретным путям вместо перезаписи корня `$`);
   - Lua-скрипт только для атомарной проверки владельца lock при `release_executor_lock` (`if redis.call("get", KEYS[1]) == ARGV[1] then return redis.call("del", KEYS[1]) else return 0 end`);
   - staging-очередь (`RPOPLPUSH` / `LMOVE`) для батчей ходов в `collector_task` $\to$ `executor_task`.
2. **Пропущенные дефекты в самой боевой механике и типизации (`AG-01`..`AG-08`):**
   Астра сосредоточилась на инфраструктурной обвязке, но пропустила подавление `mypy` в 36 модулях (`AG-05`), рассинхрон `service_key` в `core/game_auth.py` (`AG-07`), хардкод `result="victory"` при аварийном возврате из боя в разлом (`AG-06`) и потерю прямых мутаций `statuses.effects` при расчёте на deep-copy снапшотах в `CombatExecutor` (`AG-03`).

---

## 5. Итоговый приоритизированный план действительно необходимых исправлений

Ниже приведён сводный список исправлений в порядке реального технического приоритета (без затрагивания ветки `monsters`):

### Приоритет P0 — Критическая безопасность периметра и защита от несанкционированных мутаций (Блокеры продакшена)
1. **Закрыть прямой доступ к Backend в `docker-compose.prod.yml` и Nginx (`A08-01`, `A08-02`):**
   - В `docker-compose.prod.yml:62-63` привязать порт бэкенда к `127.0.0.1:${BACKEND_PORT:-8000}:8000`.
   - В `deploy/nginx/site.conf.template:35-46, 78-85` убрать публичное проксирование `/api/internal/*`, `/api/admin/*`, `/docs`, `/redoc`, `/openapi.json`, оставив внешнему миру только BFF-маршруты фронтенда и явно разрешённые публичные пути.
   - Отключить или удалить тестовый роутер `/api/v1/hex-test` (`src/backend/features/combat/api/test_hex_router.py`, `src/backend/core/router.py:39`) вне `development` (`A08-03`).
2. **Включить обязательную авторизацию на всех игровых, внутренних и админских роутах (`A07-01`..`A07-04`, `AG-07`):**
   - На `/api/game/combat/{char_id}/*` (`combat/api/router.py`) и `/api/game/rift/{char_id}/*` (`rift/api/router.py`) добавить `Depends(require_owned_character_access)`.
   - На `/api/internal/config` (`system_config/router.py`), `/api/internal/{combat,scenario,exploration}/sessions`, `/api/admin/generation-ai` (`generation_ai/api.py`) и `/api/admin/combat-ai` (`ai_simulation_router.py`) добавить `Depends(require_internal_service_key)`.
   - В `src/backend/core/game_auth.py:66` отвергать оба дефолтных префикса `expected.startswith(("dev-", "change-me-"))` (`AG-07`).
3. **Убрать debug-поля из публичного DTO разлома и закрыть IDOR в чате (`A04-01`/`A07-05`, `A07-06`..`A07-08`):**
   - Удалить `force_event`, `resolve_transition_combat`, `attributes` из клиентского `PlayerRiftActionRequestDTO` (`src/backend/features/rift/dto/runtime.py:182-194`).
   - В `/api/v1/chat/history` (`chat/api/http_router.py:18-48`) и WS чата (`chat/services/service.py:66-120`) проверять принадлежность `char_id` к запрашиваемому каналу (`party`, `combat`, `location`, `whisper`).

### Приоритет P1 — Корректность боевого движка (включая доводку сегодняшней правки боя)
4. **Исправить 4 дефекта волн размена в сегодняшней правке боя (`AG-01`..`AG-04`):**
   - **`AG-01`:** В `MechanicsService._grant_exchange_gift_token` (`mechanics_service.py:952-966`) выдавать токен `gift` только если `result.hand == "main_hand"` и `(result.action_facts.get("execution") or {}).get("origin", "primary") == "primary"`.
   - **`AG-02`:** В `AbilityService.post_process` (`ability_service.py:200-201`) вызывать `_register_combat_hp_regen` и `_register_combat_stamina_regen` только при `execution.origin == "primary"`.
   - **`AG-03`:** В `AbilityService` перевести `_append_runtime_effect` (`prep_dual_blade_loop_counter`, строки `808, 1463-1475`), `_dispel_prepared_effects` (`dispel_preparations`, строки `954-967, 1106-1119`), `force_ranged_close` (`строки 1121-1143`) и `_materialize_modifier_status_effects` (`строки 460-467, 549-593`) на запись `CombatStatusApplicationDTO` / `CombatStatusRemovalDTO` в `ctx.result`, чтобы они не терялись при отбрасывании deep-copy снапшотов в `CombatExecutor._handle_exchange`.
   - **`AG-04`:** В `AbilityService._apply_queued_effects` (`ability_service.py:1179`) учитывать `execution.origin == "secondary"` как часть размена (`active_from_exchange = exchange_counter + 1`), а `RangedPositionService.update_after_exchange` (`executor.py:280`) вызывать один раз после завершения цикла волн размена.
5. **Исправить баг `ON_CRIT` триггеров после парирования/уворота (`A03-13`):**
   - В `AbilityService._effect_conditions_met` (`ability_service.py:1418`) заменить `"is_hit": result.is_hit` на `"is_hit": result.is_hit and not result.is_dodged and not result.is_parried` (аналогично строке `678`), либо не выставлять `res.is_crit = True` в `resolver.py:66` при `res.is_parried` / `res.is_dodged`.

### Приоритет P2 — Целостность данных, идемпотентность воркеров и устранение гонок (Persistence & Workers)
6. **Сделать идемпотентными фоновые задачи и устранить потерю событий (`A03-01`..`A03-04`, `A03-11`, `A05-01`..`A05-06`, `A05-11`, `AG-06`):**
   - В `victory_finalizer_task.py:92-135` фиксировать подэтапы применения XP/износа/смерти/арены, чтобы ретрай не дублировал награды и износ (`A03-01`).
   - В `result_archive_service.py:147` исправить `row.finalization = ...` на `row.finalization_payload = ...` (`A05-11`).
   - В `system_integrator.py:163-168, 261` и `session_integrator.py:355` убрать хардкод `result="victory"` для разлома, особенно при `recover_missing_combat_session` (`AG-06`).
   - В `loot_service.py:121-125, 204-208, 337-357` добавить в SQL `WHERE` проверку текущего владельца и `location='corpse'` (`A05-02`), а в `expedition/service.py:663-709` публиковать труп в Redis только после `await self.db.commit()` (`A05-04`).
   - В `chat/workers/archive.py:103-117` возвращать `False` в `_save_batch_to_mongo` при исключении MongoDB и не сдвигать `cursor_key` (`A05-06`).
   - В `generation_ai/api.py:92-97` добавить `await service.repo.session.commit()` при удалении задачи (`A05-07`), а в `generation_ai/services.py:210-310` закрывать транзакцию БД перед внешним вызовом к провайдеру LLM/Image (`A04-10`/`A09-09`).
   - В `exploration/dependencies.py:33-38, 148-179` удалить кэширование сервисов с request-scoped `AsyncSession` в глобальном `_RUNTIME_CACHE` (`A04-05`).

### Приоритет P3 — Производительность, CI и тестовый контур (`A06`, `A09`, `AG-05`, `AG-09`)
7. **Восстановить работоспособность тестового контура и статического анализа (`A06-01`, `A06-03`, `A06-07`..`A06-09`, `AG-05`, `AG-09`):**
   - Удалить или адаптировать `tests/backend/features/generation_ai/test_asset_backfill.py` (`A06-01`).
   - В `tests/backend/conftest.py:14` перенести импорт `from src.backend.app import app` внутрь фикстуры `async_client` (`AG-09`).
   - Исправить `--cov=apps` на `--cov=src` в `pyproject.toml:94` (`A06-07`), включить `mypy` в `.github/workflows/ci.yml` (`A06-09`) и поэтапно снять `ignore_errors = true` с 36 модулей в `pyproject.toml:112-150` (`AG-05`).
8. **Устранить узкие места производительности (`A09-01`, `A09-02`, `A09-10`):**
   - В `CombatSessionManager._append_Timeline_logs` (`combat/managers/session.py:671-698`) заменить чтение и перезапись всего документа логов на `json().arrappend` или Redis List/Stream (`A09-01`).
   - Обернуть синхронную нормализацию картинок Pillow (`generation_ai/image_normalizer.py`) в `asyncio.to_thread` (`A09-10`).
