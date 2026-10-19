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
| 2 | Воспроизводимые миграции сайта на пустой PostgreSQL и обновление существующей схемы | A05-13 | Ждёт команды |
| 3 | Токены и персональные данные в логах и метриках | A08-05/06/07 | Ждёт команды |
| 4 | Logout, expiry/revoke открытых WebSocket и атомарная ротация refresh | A07-10/16, A05-12 | Ждёт команды |
| 5 | Источники зависимостей, develop behavioral gate, artifact-to-deploy gate и права env-файла | A06-05/06/09/12, A08-09/10/11/12 | Ждёт команды; перед реализацией разделить на отдельные задачи |
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
