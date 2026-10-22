# Independent infrastructure review — post-initial evidence

Initial verdict remains immutable in `independent-infrastructure-initial.md`.
This supplement records findings discovered after it, then claims validation.

## IR-03 — P1 / High — migration/refresh fixture may migrate the working database

- Requirements R5/R7: real storage contracts must use isolated adapters/resources;
  no working-data mutation is authorized.
- Location: `tests/frontend/migrations/test_site_migrations_postgres.py:89-91`
  (BOOTSTRAP), `:97-110` (migrate); current consumer
  `src/frontend/alembic/env.py:14` and `src/frontend/core/database/session.py:7`.
- Trigger: enable RUN_SITE_MIGRATION_POSTGRES or RUN_SITE_AUTH_POSTGRES after the
  settings split. Fixture creates a disposable PostgreSQL, but the subprocess
  overrides only the retired `src.frontend.config.settings.settings` dependency.
  Alembic and session construction now read `src.frontend.config.database`.
- Impact: fixture's disposable URL is ignored for actual migration. The subprocess
  inherits DATABASE_URL and reads the repository .env; upgrade/downgrade can target
  configured working site data. Without a working DB it fails instead. Refresh
  concurrency tests import and reuse this same fixture and are also affected.
- Safe independent proof (no connection): extracted the literal current BOOTSTRAP,
  disabled dotenv, set inherited DATABASE_URL to a synthetic `db.invalid` sentinel,
  passed a different synthetic loopback disposable URL in argv, intercepted
  `sqlalchemy.ext.asyncio.async_engine_from_config` before it creates/connects an
  engine, then called actual Alembic command.upgrade. Observed:
  `uses_disposable_url False`; `uses_inherited_sentinel_url True`;
  `stopped before any network connection`.
- The dangerous opt-in migration/refresh tests were **not run** by this reviewer.
  Previously passed synthetic restore drills use psql/docker explicit private DBs,
  not this fixture, and remain valid.
- Minimal fix: adapt BOOTSTRAP to the new database configuration boundary, disable
  dotenv and inherited DB values in child processes, and assert the effective
  connection target equals the owned disposable URL before migration.
- Verification: competing inherited sentinel URLs cannot change the target; real
  disposable migration and auth rotation tests pass; only owned containers removed.
- Related scan: no other tests replace config.settings via sys.modules/ModuleType;
  all uses of this BOOTSTRAP (migrate and schema_diff) require correction.

R5/R7 status becomes **fail** until IR-03 is fixed. This supplements rather than
rewrites the original partial evidence assessment.

## Additional completed checks

- Logging/privacy rerun with actual setup_logging: 46 passed, 1.34s. Earlier seven
  harness-induced failures are not product findings.
- All resolved Compose env/import checks are in progress; no running service
  operation is part of that suite.

## Claims received after initial verdict

Source: `var/audit/independent-review-claims.md`. Initial judgments below apply to
the code before IR-01/IR-02/IR-03 corrections; re-review will be recorded separately.

| Claim | Judgment | Evidence / qualification |
|---|---|---|
| C1 accumulated package implemented, local only | refuted in completeness | Scope exists and operational deferrals are appropriate, but IR-01/02/03 prevent a complete local implementation/sign-off. No unsafe game-stream replay found. |
| C2 settings split preserves required behavior and strict HTTP auth | refuted in integration completeness | Worker/migration settings separate credentials and production validators remain strict. IR-02 breaks clean CI imports and IR-03 breaks the real migration test consumer. Remaining env matrix still being checked; roles/ACLs correctly unverified. |
| C3 items.text durable lifecycle complete | refuted | IR-01 actual SQL/Mongo reproducer demonstrates domain apply without durable result; retirement, input checks, provider transaction release and recovery mechanisms otherwise observed. |
| C4 Studio app boundaries only | confirmed | Code tracing, middleware/wrapper tests and actual disposable PG read-only rejection. Does not prove server roles or resist arbitrary malicious Python. |
| C5 canonical email origin | confirmed | Settings/service/route and passing tests use trusted configuration, enforce HTTPS with bounded debug loopback exceptions. |
| C6 local evidence checker and three synthetic restore drills | confirmed | Reviewer independently ran the three store drills successfully and inspected checker scope. No operational backup/alert claim accepted. |
| C7 historical broad nonexternal counts and three failures | insufficient for entire attribution | Artifact final-suite.txt confirms 4490 passed / 3 failed / 316 deselected / 4 warnings / 599.08s and exact named failures. It is not an independent rerun, and unchanged-HEAD causation needs source comparison, not the count alone. |
| C8 historical hooks/types/docs/check results | insufficient pending artifact review | Scope-limited claims can be verified from named logs; not accepted from summary alone. Full gate remains unverified/deferred. |
| C9 no commit/push/deploy/working-data changes | insufficient for historical absolute | Reviewer performed no such actions and independently inspected current dirty baseline; cannot establish every prior action from current tree. IR-03 establishes risk in a test fixture, not evidence that a working DB was actually modified. |

### Claims evidence follow-up

- C7: **confirmed as the previous recorded run**, not a current full-suite pass.
  `final-gameplay-diagnosis.txt` shows the same three failures on a selected rerun.
  Independent git diff checks found inventory implementation/tests, actor session
  manager and test fake, loot resources/tests, starter registry/families unchanged
  against reviewed HEAD. `CharacterSessionManager.set_items_projection` explicitly
  sets `$.metrics.gear_score_version` while the two tests assert no metrics member;
  registry includes golem_foundry while loot profiles omit it. This substantiates
  the named pre-existing contracts; no gameplay fix requested or performed.
- C8: **confirmed as bounded historical evidence**, not an independent global gate.
  `final-infrastructure-hooks.txt` records applicable hooks Passed except the stated
  synthetic Basic-auth fixture secret detection; `final-secrets-recheck.txt` says
  Detect secrets Passed. `final-docs-build-confirm.txt` records successful MkDocs;
  `final-validators.txt` records fixture validation. Scoped mypy logs report success
  for 6 isolation, 35 Studio, and 4 email source files. Current diff reduces mypy
  exclusions, leaves CVE ignore lists unchanged; no blanket exclusion introduced.
- C9 narrowed by parent to this review/fix round and explicit owned synthetic
  resources is supportable for actions observed by this reviewer. No claim that
  all historical server data state has been independently attested.

## Independent re-review, first correction cycle

- Resolved Compose env/import and service isolation checks: **136 passed,
  18 deselected, 566.86s**. Synthetic environment, Compose config and subprocess
  imports only; no existing running services changed.
- RedisJSON actual disposable RedisStack contract plus architecture/test-stage
  checks: **32 passed, 10.48s**.
- IR-01 original independent SQL/Mongo proof copied to
  `test_review_generation_result_fixed.py`, with positive rollback expectation:
  actual state `(original, not_requested, mechanical_ready, cooldown, {})`.
  This plus the implementation's eight real fault/success cases and core tests:
  **22 passed, 22.65s**. SQL savepoint correctly reverses partial handler/domain
  writes and completion before retry; the original finding's immediate leak is fixed.
- IR-01 remains open for the next retry: independent two-attempt real SQL/Mongo
  proof `test_review_generation_ambiguous_retry.py`, **1 passed, 9.66s**, confirms
  Mongo lost-ack first attempt retains result-1 with original SQL/cooldown, then
  fresh actual processing calls provider again and replaces it with result-2:
  `(provider_calls=2, item=result-2, SQL=done, Mongo=result-2)`.
  A nonempty raw output guard is required before another provider claim, matching
  the existing StoredResultNeedsReview recovery boundary; immediate preservation
  alone does not keep ambiguous evidence available for review. Parent notified.
- IR-03 independent actual Alembic engine capture now reports
  `uses_disposable_url True`, `uses_inherited_sentinel_url False`, and stops before
  any network connection. Reviewed registered fixture URLs, subprocess env allowlist,
  disabled dotenv, actual database boundary and guarded engine factories. Real
  disposable migration/auth tests were authorized only after this proof and are
  now running; no earlier unsafe fixture execution was performed by reviewer.
- IR-02/IR-03 safe guards: **17 passed, 16.05s**. Both workflow-declared
  production-like environments import strict settings and collect representative
  tests; removing synthetic service keys still fails validation. IR-02 is closed
  locally. IR-03 actual Alembic capture, wrong-target rejection, unregistered URL
  rejection and inherited configuration isolation pass. Full CI remains unrun.
- IR-03 actual owned PostgreSQL migration and refresh rotation/concurrency suite:
  **14 passed, 103.67s**. Clean/repeated upgrade, historical baseline, downgrade,
  schema comparison and token transaction cases ran only after the independent
  target capture. IR-03 is closed; R1 real refresh gap is now independently checked.
