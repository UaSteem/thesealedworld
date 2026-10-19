# Совместимое security-обновление зависимостей

19.10.2026. Дополнительная команда владельца при завершении шага 5.2:
обновить отмеченные scanner библиотеки, если они совместимы. Не использовать
пропуск audit hook или новые vulnerability exceptions.

## Изменения

| Package | До | После |
| --- | --- | --- |
| aiohttp | 3.13.5 | 3.14.4 |
| aiosmtplib | 5.1.0 | 5.1.2 |
| anyio | 4.13.0 | 4.14.2 |
| cryptography | 47.0.0 | 50.0.0 |
| idna | 3.13 | 3.15 |
| msgpack | 1.1.2 | 1.2.1 |
| multidict | 6.7.1 | 6.9.1 |
| Pillow | 12.2.0 | 12.3.0 |
| pip | 26.1 | 26.2 |
| pyasn1 | 0.6.3 | 0.6.4 |
| pydantic-settings | 2.14.0 | 2.14.2 |
| PyJWT | 2.13.0 | 2.15.0 |
| pymongo | 4.17.0 | 4.18.2 |
| python-multipart | 0.0.27 | 0.0.31 |
| Starlette | 1.0.1 | 1.3.1 |
| urllib3 | 2.7.0 | 2.8.0 |
| virtualenv | 21.2.4 | 21.7.13 |

Для совместимости aiohttp обновлён aiogram 3.28.2 → 3.31.0, не меняя codex-bot.
Обязательные transitives: python-discovery 1.2.2 → 1.6.4, yarl 1.24.2 → 1.25.1.
При all-groups проверке найдены и исправлены дополнительные docs advisories:
mkdocs-material 9.5.49 → 9.7.7, pymdown-extensions 10.21.3 → 11.0.1; добавлен
их backrefs 8.1. Security floors закреплены constraints и прямыми bounds,
без overrides upstream требований.

Removed source prerequisite: несуществующий local `codex-ai` override заменён
уже заявленным published `codex-ai==0.2.4`, как в Docker. Прежняя установка
0.2.5.dev0 не соответствовала manifest. Используемые provider API совместимы;
неиспользуемый dev-only `input_images` параметр не переносился в приложение.
Dev-tool graphifyy требует Python <3.14: добавлен marker, убирающий несовместимую
установку на локальном Python 3.14, сохраняя поддержку на Python 3.13.

Изучены [breaking changes cryptography](https://cryptography.io/en/50.0.2/changelog/):
приложение не использует удалённые aliases/decrepit cipher API. JWT, сертификаты
Nginx и provider imports проверены локальными тестами, не реальными AI запросами.

## Проверки

- Изолированный кандидат перед установкой: ordinary `uv lock --check`,
  `uv pip check`, actual audit и MkDocs build прошли. Источник не зависел от
  sibling checkout, `--no-sources` для финальной проверки не требовался.
- Широкий набор до/после: **943 passed, 17 skipped, 3 failed** в обоих случаях.
  Три прежних `test_site_analytics_module` ожидают 2/1/0 вместо актуального `—`.
  Новых regression failures не найдено; эти тесты не изменялись.
- Рабочий `.venv`: **243 passed**. Набор 184 тестов шага 4 дополнен
  `tests/backend/chat`, `tests/deploy`, `tests/tools/test_pip_audit_project.py`.
  Включены одноразовые PostgreSQL 16, Redis 7, MongoDB 8, настоящий Nginx,
  concurrent Mongo append/replay, SQL commit failure, logout/refresh/WS revoke.
- Root `uv pip check`: **153 packages, all compatible**.
- Root `uv lock --check`: passed; `uv sync --locked --all-groups` применён.
- Root `pre_commit run pip-audit --all-files --verbose`: passed,
  `No known vulnerabilities found`, без `SKIP` и новых waiver IDs.
  Scanner пропускает unpublished project `thesealedworld`; это не audit его кода.
- Root MkDocs build прошёл, 9.32s; оставшиеся INFO про nav и deprecation warning
  TestClient/httpx не изменяют результат. Полный project gate не запускался.
- Временные PostgreSQL/Redis/MongoDB контейнеры удалены. При установке завершены
  проверенные зависшие pytest прошлых проверок, удерживавшие DLL в Windows.

Широкий набор:

```powershell
.venv/Scripts/python.exe -m pytest tests/frontend tests/shared tests/studio tests/tg_bot tests/backend/core tests/backend/realtime tests/backend/chat tests/backend/features/generation_ai --no-cov -q --maxfail=5
```

Операционные логи/evidence сохранены локально в ignored `var/audit/`:
`dependency_baseline_tests.txt`, `dependency_candidate_tests.txt`,
`dependency_updated_integration_tests.txt`, `dependency_updated_audit_hook.txt`,
`dependency_updated_docs.txt`; candidate metadata — `dependency_candidate/`.

Production, `.env`/GitHub secrets, игровые правила и provider API не менялись.
Проверен Windows Python 3.14; universal lock учитывает Python 3.13/другие платформы,
но новые production images в этом шаге не собирались и не деплоились.
