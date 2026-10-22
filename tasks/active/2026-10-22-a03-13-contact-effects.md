# A03-13 / A06-02: контактные crit-эффекты

Запрос: реализовать исправление A03-13 и тесты, включая A06-02.
Режим: независимая ревизия запрошена пользователем после обычной проверки; independent-review: pass.
Уточнение: «подключай проверяй» — проверить текущую реализацию независимым ревизором, исправить замечания в рамках A03-13/A06-02.
Уточнение: повторно проверить runtime после устранения RiftZoneRuntimeDTO и завершить независимую проверку; пользователь разрешил коммит только этой задачи, без push.

## Требования
- R1: Парирование и уклонение отменяют контактные crit-эффекты оружия и боеприпасов.
- R2: Блок сохраняет контакт, в том числе при нулевом итоговом уроне.
- R3: Сохранить hit/crit, боевые токены и порядок расчёта критических мутаций.
- R4: Исправить ложноположительный setup A06-02; проверить успешный trigger и positive control, bleed/stun/ammo, события и логи по применимости.
- R5: Без публикации, миграций и изменения посторонних файлов; коммит A03-13/A06-02 разрешён последним запросом пользователя.

## План
1. Добавить регрессии и зафиксировать падение на текущей реализации.
2. Ввести отдельное условие контакта для очереди контактных crit-эффектов.
3. Прогнать целевые и смежные combat-тесты, проверить diff и обновить результаты.

## Статус
R1–R4: implementation done; focused verification passed.
R5: implementation done; verification passed.
Состояние: reviewed-awaiting-acceptance; full-project gate not run.
Проверка: исполнитель contact_fix выполнил тесты; ведущий проверил итоговый scoped diff, требования и diff-check. Независимый contact_reviewer завершил runtime-перепроверку текущей реализации после устранения ошибки импорта.

## Реализация и доказательства
- `is_contact = is_hit and not is_dodged and not is_parried` добавлен в проверку условий и очередь crit-эффектов оружия/боеприпасов; crit stage, mutations, hit/crit и токены сохранены.
- Условно отклонённые payload удаляются из `applied_effects` до материализации: публичный лог больше не показывает отменённые эффекты.
- A06-02: прежний тест с RNG, отключавшим trigger, заменён матрицей 18 случаев (bleed/stun/ammo × parry/dodge/block/block_zero/crit/noncrit). Проверяются успешный trigger attempt, статусы, status applications, события, публичный результат и токены.
- block_zero использует нулевой исходный damage base; существующий clamp сохраняет минимум 1 при положительном raw damage даже после полного поглощения. Формула урона не менялась.

## Проверки
- RED до production edits: `.venv/Scripts/python.exe -m pytest tests/backend/features/combat/test_runtime_processors.py -k contact_crit_effects -q --no-cov`: 6 failed (ожидаемое применение bleed/stun/ammo после parry/dodge), 12 passed.
- GREEN после правки: тот же файл с `-k 'contact_crit_effects or archery_crit_queues'`: 19 passed, 265 deselected.
- `.venv/Scripts/python.exe -m ruff check` по двум production-файлам и test_runtime_processors.py: passed. Изменённая матрица отформатирована; постороннее форматирование отменено.
- Combat suite: `.venv/Scripts/python.exe -m pytest tests/backend/features/combat -q --no-cov`: 945 passed, 30 failed, 5 skipped. Общая зелёная проверка не достигнута; посторонние ошибки session/finalization не исправлялись.
- Runtime + resolver contract: 282 passed, 3 failed. Причина всех трёх: существующие session-тесты вызывают commit_session без обязательных owner/exchange_id/expected_actions; это не затронутый контракт. Проверка без этих трёх: 282 passed, 3 deselected (6.29s).
  Команда: `.venv/Scripts/python.exe -m pytest tests/backend/features/combat/test_runtime_processors.py tests/backend/features/combat/runtime/engine/test_resolver_trigger_contract.py --no-cov -q -o addopts='' --tb=short -k 'not test_commit_session_persists_step_and_actor_exchange_counters and not test_session_integration_round_trips_stamina_state and not test_commit_session_sends_dead_actor_prune_and_alive_counts'`.
- `uv run` недоступен из-за прав на настроенный внешний cache; использован локальный `.venv/Scripts/python.exe`. Asyncio тесты запускались вне sandbox из-за блокировки ProactorEventLoop внутри sandbox.
- Full-project gate, production и внешние сервисы не проверялись; коммит/публикация/миграции не выполнялись.

## Независимая ревизия по дополнительному запросу
Ревизор: contact_reviewer, GPT-6.1 Sol High, отдельный агент без истории чата; read-only.
Actionable findings в A03-13/A06-02 не обнаружены. Изменения реализации после ревизии не потребовались.

| Требование | Вердикт | Доказательство |
| --- | --- | --- |
| R1 | pass (static) | ON_CRIT weapon/ammo payload → contact condition → post-process filter → statuses/events/logs |
| R2 | pass (static) | is_contact не исключает block и не зависит от damage_final |
| R3 | pass | Порядок стадий/мутаций/токенов не менялся; resolver contract test прошёл |
| R4 | partial | 18 сценариев используют реальный каталог, успешный trigger attempt и positive controls; текущий runtime-прогон не собрался |
| R5 | pass within scope | Ревизор не менял файлы, не запускал сервисы и не выполнял коммит/публикацию |

Текущая независимая проверка: `.venv/Scripts/python.exe -m pytest tests/backend/features/combat/runtime/engine/test_resolver_trigger_contract.py --no-cov -q -o addopts=''` → 1 passed in 9.83s.
Целевые runtime-тесты не собраны: `ImportError: cannot import name 'RiftZoneRuntimeDTO' from 'src.backend.features.rift.dto'` по цепочке test_runtime_processors → arq_container → infrastructure/rift/managers/instance.py, вне затронутых A03-13 файлов. Этот сбой не исправлялся в рамках ревизии.
Предыдущие 19/19 и 282/282 — исторические результаты исполнителя, а не подтверждённый текущий независимый runtime pass.

## Завершение независимой проверки и подготовка коммита
Импорт RiftZoneRuntimeDTO больше не блокирует сборку. contact_reviewer независимо выполнил:
- `.venv/Scripts/python.exe -m pytest tests/backend/features/combat/test_runtime_processors.py -k 'contact_crit_effects or archery_crit_queues' --no-cov -q -o addopts='' --tb=short` → 19 passed, 265 deselected (6.97s).
- `.venv/Scripts/python.exe -m pytest tests/backend/features/combat/test_runtime_processors.py tests/backend/features/combat/runtime/engine/test_resolver_trigger_contract.py --no-cov -q -o addopts='' --tb=short` → 285 passed (10.40s), без исключений.
Итог ревизора: findings отсутствуют, R1–R4 pass по текущему коду и runtime; независимая проверка A03-13/A06-02 завершена. R5 проверяется ведущим по составу коммита.
Ведущий повторил scoped Ruff и diff-check: pass. Полный tools/dev/check.py не запускался: его quality-command выполняет pre-commit --all-files с auto-fix по общему дереву, содержащему изменения других задач. Использованы целевые проверки и штатные commit hooks.
Коммит ограничивается двумя production-файлами, contact/ammo hunks test_runtime_processors.py и этим MD. Посторонние commit_session hunks остаются в рабочем дереве; push не разрешён и не выполняется.
