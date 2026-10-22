# Testing Strategy

This document describes the project testing approach. Use current code, tests, and `pyproject.toml` as the source for executable checks and thresholds.

## Test Pyramid

TurnBasedMMORPG is a production application, not a standalone library. The target pyramid is:

1. Unit tests: isolated domain and service logic.
2. Integration tests: database, Redis, API, event bus, and feature boundaries.
3. E2E tests: browser/game flows after the migration and refactor stabilize.

During active migration, new code should start with clean unit tests. Integration and E2E coverage should be added once the moved feature boundaries are stable.

## Coverage Targets

The long-term coverage target is 90% or higher. The enforceable threshold is the current `fail_under` value in `pyproject.toml` (74 at this revision).

### Development and Coverage Guidance

When developing with AI agents, strict rules apply to prevent technical debt:

1. **Changed behavior:** Add tests for observable behavior and meaningful edge cases introduced or modified by the task. For a tested refactor or contract migration, establish the new contract with a failing test before production edits.
2. **Coverage scope:** Keep the configured project threshold; use patch and local coverage to find gaps that matter to the changed behavior. Do not require an arbitrary percentage or unrelated surrounding coverage expansion for every edit.
3. **Legacy code:** Test specific behavior and edge cases; avoid dummy tests written only to increase line counts.
4. **Critical boundaries:** Give auth/session, migrations, configuration parsing, and state transitions stronger focused tests and integration coverage where behavior crosses a real boundary.

Coverage configuration lives in `pyproject.toml` under `[tool.coverage.report]`. Do not put `--cov-fail-under` in pytest `addopts`.

Recommended pytest addopts shape:

```toml
addopts = "--tb=short --cov=src --cov-report=term-missing"
```

## Dependency Audit Hook

The local `pip-audit` hook runs `tools/dev/pip_audit_project.py`. The helper
selects this checkout's existing `.venv` interpreter explicitly and invokes
`python -I -m pip_audit`, not the interpreter of an isolated pre-commit environment.
It does not install/sync packages or modify `uv.lock`. A missing environment,
missing scanner or scanner error fails the gate. Source filenames are not passed
to pip-audit; the hook always runs and preserves its existing seven vulnerability
exceptions and 15-second service timeout.

From the prepared project environment:

```powershell
python -m pre_commit run pip-audit --all-files
```

This checks installed application/development packages, not a reproducible lock
export or a deployed image. Scanner-skipped unpublished distributions remain
unknown. A successful hook is not proof that every private distribution or
production artifact is vulnerability-free. Newly reported advisories fail the
hook; do not add exceptions or upgrade unrelated dependencies merely to make a
tooling change pass. Review those findings as a separate task.

Security-fix floors live in `tool.uv.constraint-dependencies`, preserving upstream
requirements rather than overriding conflicts. Commit `uv.lock` with manifest
updates. `codex-ai==0.2.4` resolves from its published distribution, matching the
Docker source policy; the obsolete sibling-checkout path is removed. The dev-only
`graphifyy` dependency is installed only on Python <3.14, as required by its metadata.

## Develop Behavioral Gate

`CI / Develop Behavioral Tests` runs independently of lint/types on pushes to
`develop` and pull requests targeting `develop`, including fork PRs. Its fixed
suite covers frontend, shared contracts, Studio, Telegram adapters, backend
core/realtime/chat and GenerationAI. It uses only checked-in source plus a clean
`uv sync --locked`; no local `.env`, GitHub secrets or external services are
required. Tests requiring disposable PostgreSQL/Redis/Mongo URLs skip when those
URLs are absent; this gate does not attest real storage adapter semantics.

The isolated application profile sets `ENVIRONMENT=testing`, a public test-only
`SECRET_KEY`, and `DEBUG=True`. The explicit debug profile allows development
signer defaults without production credentials; production validation tests
still construct their own strict settings. It does not change application or
production configuration.

The exact command is:

```sh
uv run --locked python -m pytest tests/frontend tests/shared tests/studio tests/tg_bot tests/backend/core tests/backend/realtime tests/backend/chat tests/backend/features/generation_ai tests/deploy/test_immutable_references.py tests/deploy/test_dependency_sources.py --no-cov -q
```

Any nonzero pytest exit fails this separate status; it has no dependency on the
lint job and no `continue-on-error`. This is a selected behavioral suite, so
`--no-cov` avoids applying the repository-wide coverage target to partial paths.
The full quality/docs job and its existing coverage policy remain on pushes to
`main` and PRs targeting `main`; Docker verification remains push-to-main only.
Repository required-check/branch-protection settings and hosted runs must be
verified separately; defining this status does not enforce a merge restriction.

## Test Layout

Tests live outside `src/` under the repository-level `tests/` package.

The target structure separates application layers first, then feature domains:

```text
tests/
  conftest.py
  backend/
    conftest.py
    core/
      redis/
      bus/
      database/
    features/
      auth/
      game_lobby/
      actor_state/
      scenario/
      combat/
      inventory/
      exploration/
      world/
  frontend/
    conftest.py
    core/
    features/
      auth/
      game_lobby/
      cabinet/
    integrations/
      backend_api/
  shared/
    conftest.py
    schemas/
    enums/
```

When a domain grows, split by test level inside the domain:

```text
tests/backend/features/game_lobby/
  unit/
  integration/
```

For small domains, keeping test files directly under the domain folder is acceptable until the split improves clarity.

## Naming

Use explicit names that describe behavior:

```text
test_character_session_manager.py
test_game_lobby_creation.py
test_backend_game_lobby_api.py
```

Prefer one behavior per test. Avoid broad scenario tests that assert many unrelated details.

## Fixtures

Use layered fixtures:

- `tests/conftest.py`: global pytest setup shared by every layer.
- `tests/backend/conftest.py`: backend app, DB, Redis, event bus, auth helpers.
- `tests/frontend/conftest.py`: frontend app/client/template helpers.
- `tests/shared/conftest.py`: shared schema and enum helpers.
- domain-local `conftest.py`: only when the domain needs reusable setup.

### Test Doubles over Heavy Mocks

For AI-assisted development, **In-Memory Doubles (Fakes)** are vastly superior to heavy `MagicMock`/`patch` configurations.

- Avoid relying on complex `unittest.mock` assertions for infrastructure like Redis or the Database.
- Instead, create or reuse simple `InMemoryRepository` or `FakeRedisService` classes that store data in Python `dict`s and implement the same Protocol.
- This ensures tests execute quickly, verify actual logical transitions, and prevent agents from writing brittle, configuration-bound tests. Patch objects where they are used only if a Fake is unavailable.

## Current Development Rule

While migration is ongoing:

- write unit tests first;
- keep tests deterministic and isolated;
- avoid E2E until the UI and backend contracts settle;
- add integration tests for Redis/DB/API only when the behavior crosses a real boundary;
- do not depend on `temp/` in tests except as donor reference comments or fixtures during transitional work.

## Exclusions

Use `pragma: no cover` only for branches that cannot be exercised without breaking isolation, such as:

- defensive `except ImportError` blocks;
- explicit `raise ImportError` compatibility branches;
- environment-specific fallback paths that are covered by deployment smoke checks instead.

Do not exclude ordinary error handling just because it is inconvenient to test.

## Quality Gate

Use the project quality runner for full checks:

```powershell
uv run python tools/dev/check.py
```

Focused development runs may use direct pytest commands, for example:

```powershell
uv run pytest tests/backend/features/game_lobby -m unit
```

Before merging larger feature work, run the full quality gate and include integration tests for every touched external boundary.


## Joint config HTTP contract (A06-07)

`tests/frontend/integrations/backend_api/test_game_config_http_contract.py` connects
real `GameConfigApi` / `OperatorApiClient` / `BaseApiClient` to the real backend
config router through `httpx.ASGITransport`. Backend auth dependencies, JSON body
validation, serialization and `GameConfigManager` run together. Only Redis storage
is an in-memory get/set/NX double. Fixtures register synthetic config namespaces;
no gameplay defaults, real keys, application lifespan or external stores are used.

The suite covers DTO metadata and types, update/readback, key/namespace reset,
namespace isolation, read/write capability separation, 403/404/422 propagation,
read-only source denial and required-field producer drift. Denied mutations must
not reach storage; invalid values must leave state unchanged. This is HTTP-boundary
proof, not Redis wire/persistence proof or browser E2E coverage. Other clients and
routers require their own joint contracts.

Run from the repository root without Docker or opt-in environment flags:

```powershell
uv run --locked pytest tests/frontend/integrations/backend_api/test_game_config_http_contract.py --no-cov -q
```

These tests are marked integration and are included by the existing behavioral CI
selection of `tests/frontend`. Global coverage configuration is unchanged.


## Static ownership gate (A06-08)

`tools/validators/architecture.py` parses Python AST without importing application
modules. It checks frontend imports of backend internals, shared imports of service
code, feature imports of raw Redis clients, and executable Redis-root literals
(`game:`, `combat:`, `loot:`) in frontend/shared/backend feature code. New subspaces of these roots
are covered without adding literal prefixes. Rift has no blanket exclusion;
comments/docstrings do not count as executable key construction.

A narrow semantic exception permits combat operation identity in
`CombatDurabilityDamageRequest.idempotency_key`; it does not permit Redis calls
nested in that value, other game roots, or arbitrary file-level exceptions.
Infrastructure managers and semantic feature integrations remain allowed.
The checker handles static/relative imports, aliases and literal importlib imports;
it reports file/line/rule and fails on syntax errors in the checked surfaces.

`tests/backend/core/test_architecture_validator.py` exercises synthetic forbidden
and allowed sources. `tests/backend/features/test_infrastructure_boundaries.py`
scans the current source tree and retains manager-location regression checks.
Both are included in develop behavioral CI. The full fixture validator also calls
this gate; no application startup, real stores or generated archive scan is needed.

```powershell
uv run --locked pytest tests/backend/core/test_architecture_validator.py tests/backend/features/test_infrastructure_boundaries.py --no-cov -q
```

This is a bounded static rule set, not a Python sandbox or complete architecture
proof. Computed imports, arbitrary runtime key factories, Lua/TTL data flow and
domain/ORM ownership semantics require separate analysis and tests. It does not
approve Legacy refactors or change gameplay boundaries.


## Уровни запуска (A06-11)

`tools/dev/check.py` использует установленные команды `codex_core`: unit,
integration, regression, затем suite. В интерактивном режиме integration остаётся
подтверждаемой стадией; `--ci` запускает все четыре без вопроса.

| Стадия | Выборка pytest | Покрытие |
| --- | --- | --- |
| unit | `unit and not integration and not external` | `--no-cov` |
| integration | `integration and not external` | `--no-cov` |
| regression | `not unit and not integration and not external` | `--no-cov` |
| suite | `not external` | Общее покрытие, исходный порог 74% |

Если тест помечен одновременно unit/integration, он относится к integration.
Неразмеченные тесты остаются в regression: это backlog классификации, а не
утверждение об их изолированности. Suite намеренно повторяет объединение трёх
выборок ради общего coverage gate. Существующие unit labels не переаттестованы.

Для выборочного запуска: `.venv/Scripts/python -m pytest -m unit --no-cov`;
используйте полное выражение из таблицы для точной выборки стадии runner.
Docker/реальные PostgreSQL, MongoDB и Redis отмечены `external`, включая проверки
Compose CLI. Запускать их отдельно: `pytest -m external --no-cov` и включить
соответствующий `RUN_*` opt-in из docstring теста. По умолчанию многие такие тесты
пропускаются; skipped не означает проверенный контракт. External не входит в
автоматические стадии, даже если в окружении уже выставлен opt-in.
Прямой `pytest` без selector сохраняет прежнее поведение и существующие skip guards.

Разделение выборок не исправляет ошибки collection или упавшие тесты. Полный
coverage gate считается пройденным только после успешного исполнения suite.


## Реальные storage/broker contracts (A06-03)

Набор подтверждает репрезентативные инфраструктурные границы. Он не сертифицирует
каждый gameplay/Legacy repository, ownership predicate или distributed transaction.
Все перечисленные suites отмечены `external`; запускать отдельно с `--no-cov`.

| Граница | Тесты | Что проверяется |
| --- | --- | --- |
| RedisJSON | `tests/backend/core/redis/test_redisjson_contract.py` | ActorCommitmentManager wire, sections/batch, TTL, WRONGTYPE partial pipeline |
| MongoDB | `tests/backend/infrastructure/mongo/test_task_document_index_contract.py` | Настоящий unique index, concurrent duplicate rejection, bootstrap, BSON |
| SQL/Mongo | GenerationAI `test_input_durability.py`, `test_retry_budget_postgres.py` | Durable input/result, SQL claim/retry, write denial |
| SQL/Mongo/queue | GenerationAI recovery/transaction/reconciliation suites | Rollback, row locks, concurrent recovery, stale owner, post-commit enqueue |
| Redis Streams | `tests/backend/core/bus/test_pending_quarantine_redis.py` | Pending quarantine, restart, competing scanners, ACK failure, no blind replay |

Для RedisJSON включить `RUN_REDISJSON_CONTRACT_TESTS=1`; используется
`redis/redis-stack-server:7.2.0-v14`. Для Mongo suite включить
`RUN_GENERATION_INPUT_STORE_TESTS=1`: переиспользуются disposable PostgreSQL/Mongo
fixtures, не application connection URLs. Retry SQL требует
`RUN_GENERATION_RETRY_POSTGRES_TESTS=1`; Streams — `RUN_STREAM_RECOVERY_REDIS_TESTS=1`.
Контейнеры имеют уникальные имена и случайные loopback-порты, очищаются в `finally`.
Не передавать рабочие URL. Эти tests не запускают AI provider и не меняют баланс.

Пример: `pytest tests/backend/core/redis/test_redisjson_contract.py -m external --no-cov`
после явного включения соответствующего opt-in. Green unit/fake tests по-прежнему
не доказывают SQL dialect, BSON wire или server atomicity. Ошибка Redis pipeline
проверяется настоящим WRONGTYPE; отказ Mongo write в GenerationAI дополнительно
инъецируется поверх настоящих хранилищ и не моделирует сетевой partition сервера.
