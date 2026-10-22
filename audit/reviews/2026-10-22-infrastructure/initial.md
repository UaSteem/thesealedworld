# Independent infrastructure review — initial verdict

Reviewer: independent subagent, 2026-10-22. Baseline develop HEAD
`183246e5279a257c140c4a059a5b56d4c65dfefc` plus accumulated tracked/untracked
infrastructure changes. Initial verdict recorded **before receiving implementer
claims or reading prior completion conclusions**. Requirements source:
`var/audit/independent-infrastructure-requirements.md`.

**Verdict: changes required; two confirmed Medium/P2 defects.** This is local
review of the requested non-gameplay remediation, not production acceptance.
The final42 manifest was not used as a coverage boundary: inventory included
GenerationAI retirement/archive, queue recovery, shared settings consumers,
CI/deploy gates, auth/WS, HTTP contracts, Studio, restore tooling and dependencies.

## Findings

### IR-01 — P2 / Medium — failed AI result persistence commits the applied item

- Requirement: R4, durable result and coherent cross-store failure handling.
- Location: `src/backend/features/generation_ai/services.py:144-150`;
  commit at `src/backend/features/generation_ai/workers/tasks.py:40`.
- Trigger: provider succeeds; actual `ItemTextTaskHandler.apply_result` flushes
  item/template updates; `repository.mark_done` cannot persist/confirm Mongo
  output. The catch writes cooldown in the same SQL transaction. Worker commits.
- Impact: item becomes generated/ready, including template-linked updates, while
  durable output is absent and task is cooldown/failed. Retry invokes provider
  again and may overwrite visible text. A partial handler failure has the same
  missing rollback boundary. This is not just an in-memory fake observation.
- Independent proof: `var/audit/test_review_generation_result.py` uses real
  disposable PostgreSQL/Mongo and actual item apply/repository code, replacing
  only provider response/build-request and injecting `record_result` failure.
  A fresh SQL session reads `('unrecorded result', 'generated', 'ready',
  'cooldown', {})`; the last value is durable Mongo output. Reproducer passed
  (1 test, 7.99s), confirming the defect. Both disposable containers cleaned up
  through the reviewed fixture.
- Minimal correction: define rollback/savepoint semantics for apply + completion
  before recording retry, retaining the committed claim/fencing contract. Merely
  swapping apply and mark_done is insufficient for partial apply failures and
  Mongo-success/SQL-failure ambiguity.
- Verify: real SQL item/template changes remain unchanged on result persistence
  failure and partial apply failure; retry state is durable; successful apply and
  completion commit together; stored ambiguous Mongo results remain reviewable.

### IR-02 — P2 / Medium — main/release CI environment cannot import strict settings

- Requirement: R2, executable CI/dependency/artifact quality gates.
- Location: `.github/workflows/ci.yml:105-108` and
  `.github/workflows/build-images.yml:37-40`.
- Trigger: clean GitHub runner executes the full quality gate with DEBUG=False
  and SECRET_KEY, but no FRONTEND_INTERNAL_SERVICE_KEY/SITE_TO_GAME_SERVICE_KEY
  or BACKEND_INTERNAL_SERVICE_KEY. No committed .env supplies them.
- Impact: BackendSettings and FrontendSettings reject their development defaults
  during test-module imports; main/release test collection cannot succeed even
  after the separately deferred AG-05 type issues are fixed.
- Proof: independently instantiated/imported both settings modules with dotenv
  disabled, exact workflow DEBUG/SECRET_KEY/ENVIRONMENT and service-key variables
  absent. Both raised ValidationError with `Production settings cannot use default
  or development secret keys`. Installed BaseCheckRunner.run_command passes
  inherited env (no test overrides); project conftests do not supply these keys.
- Minimal correction: explicitly give the isolated CI tests synthetic non-default
  service keys. Keep production validators strict; do not add a testing bypass.
- Verify: clean-process collection under each workflow's declared env and negative
  production settings tests; do not claim this alone passes the full main gate.

## Requirement table

| ID | Status | Independent evidence / limits |
|---|---|---|
| R1 privileged API, telemetry, token/session lifecycle | partial | Reviewed operator capabilities, metrics templates, refresh SQL rotation, WS guard; auth/WS/privileged tests passed in targeted run. Logging/privacy separately 46/46 passed. Real refresh concurrency tests skipped without its opt-in; no live edge/runtime acceptance. |
| R2 CI/artifact/dependency/production gates | fail | SHA/digest/reference/provenance/policy tests pass; workflow source inspected. IR-02 blocks clean full main/release test environment. No remote CI or publication exercised. |
| R3 Redis pending evidence, no unsafe game replay | pass | Actual installed stream processor traced; backend/chat use quarantine adapter, retain source payload, ACK after HSETNX, no destructive trim. Real disposable Redis pending tests passed. Operator reconciliation/retention remains operational. |
| R4 retained items.text, durable lifecycle, archive | fail | Archive/retirement tests, registry/consumer tracing, durable input, claim/reacquire, scheduling and running/document recovery reviewed. IR-01 confirmed on actual PostgreSQL/Mongo. Full external AI recovery matrix not yet rerun. |
| R5 HTTP, architecture, stage and storage gates | partial | HTTP contract and selected adapter tests pass; AST validator and installed stage runner inspected. Full tools/dev/check.py, total coverage and complete storage matrix not run. No new blanket suppressions found. |
| R6 synthetic restore + evidence limits | pass | Independent PostgreSQL, MongoDB, Redis RDB restore drills passed in own disposable resources; evidence checker tests passed. Checker verifies file/hash/time claims, explicitly cannot establish real backup/alert operations. |
| R7 service env/network/config isolation | partial | All Compose allowlists/topology inspected; unit/config/import checks pass, runtime settings separate API credentials, migration imports inspected. Full external resolved-environment matrix pending; live roles/ACL/rotation excluded. |
| R8 Studio auth and selected-source reads | pass | Auth/host/origin/cookie/HTTP allowlist and SQL/Redis wrappers traced to app; boundary tests pass; disposable PostgreSQL rejects mutating CTE/function in read-only transaction. Server role/ACL configuration unverified as explicitly deferred. |
| R9 trusted email HTTPS origin | pass | Config and service origin validation, request route construction and tests checked: Host/forwarded headers are not used; loopback HTTP requires debug permission. Delivery not claimed. |
| R10 dependency updates/no blanket exclusions | partial | Lock/config inspected; certifi/virtualenv/Pillow constraints updated, mypy exclusions reduced, no new broad security exclusions. Targeted runtime tests pass. No network vulnerability feed or complete installed/lock security audit rerun. |

## Checks and boundaries

- Harness: `var/audit/independent_review_runner.py` disables dotenv before project
  imports, uses synthetic auth environment, no source/test modifications.
- Broad focused command: runner over tests/deploy, tests/studio,
  tests/backend/features/generation_ai, tests/backend/core/bus, generation/migration
  settings, AI archive, email origin and game-config HTTP contract, with
  `-m 'not external' --no-cov -o addopts= -p no:cacheprovider`:
  **394 passed, 293 deselected**. Windows sandbox asyncio stalled; terminated and
  repeated outside sandbox using project-local basetemp (132.75s).
- Auth/WS/privileged + shared + opt-in synthetic restore/Redis run:
  **287 passed, 7 skipped, 7 failed** (85.52s). All 7 failures were caused by the
  review harness replacing setup_logging. Corrected the harness (not product)
  and reran all tests/shared with real logging: **46 passed** (1.34s).
- IR-01 private reproducer: **1 passed** means the undesired durable state was
  reproduced, not that implementation is correct.
- No production networking, .env/private secret reading, working databases,
  existing container mutation, commit, push, deploy or source/docs/tests edits.
  Only private review artifacts and ordinary test artifacts written.
- Full project quality/coverage/security/remote build and production operations
  are unverified. Gameplay and chat performance expansion remain out of scope.
  Full original historical conversations were unavailable; completeness checked
  against neutral requirements and original audit finding contracts, not prior
  implementer completion prose.

Further checks and claims validation must be recorded separately, preserving this
initial verdict. Source freeze may be lifted for IR-01/IR-02 fixes now.
