# Independent infrastructure review — final re-review

2026-10-22, develop HEAD `183246e5279a257c140c4a059a5b56d4c65dfefc`
plus the accumulated uncommitted package and reviewed corrections.
Initial independent verdict is preserved in `independent-infrastructure-initial.md`;
later IR-03 and first correction evidence in `independent-infrastructure-supplement.md`.
Original neutral contract: `independent-infrastructure-requirements.md`.

**Local verdict: the three review findings are closed. No remaining actionable
defect established within the reviewed infrastructure scope.** This is conditional
local acceptance, with the explicit operational/full-gate limits below.

## Finding closure

| Finding | Final state | Independent proof |
|---|---|---|
| IR-01 P2, domain SQL writes survive failed AI completion | closed after two correction cycles | Actual SQL savepoint wraps apply/completion/followups; rollback precedes retry. Original private SQL/Mongo oracle now observes original/not_requested/mechanical_ready + cooldown and empty output. The second oracle confirms lost Mongo ack does not cause a second provider call: original item, terminal failed/StoredResultNeedsReview, attempts=1, retained result-1. Both claim paths guard raw nonempty/malformed output; matrix verifies complete Mongo document equality. |
| IR-02 P2, clean CI settings imports fail | closed | Both workflow quality steps declare matching synthetic service keys. Isolated strict settings imports/collection pass; removing keys still triggers production validation. No global validator bypass. |
| IR-03 P1, migration fixture can select working DB | closed | Original independent engine-capture oracle changed from inherited sentinel to exact disposable target before any connection. Fixture registration, loopback UUID target checks, env filtering, dotenv disabling and guarded factories reviewed. Actual migrations/auth concurrency then pass in owned temporary PostgreSQL. |

No source/tests/docs were edited by this reviewer. Private reproductions remain
under `var/audit`; original failing-state artifacts were not replaced.

## Requirements, final local status

| ID | Status | Evidence and boundary |
|---|---|---|
| R1 privileged API, telemetry, token/session lifecycle | pass | Targeted auth/WS/privileged checks, real logging/privacy, and real PostgreSQL refresh concurrency/failure tests pass. Live edge acceptance not performed. |
| R2 CI/artifact/dependency/production gates | partial | Local workflow/settings/provenance/policy checks pass; IR-02 fixed. Remote CI/build/publish and full project gate not executed. Known AG-05 typing/gameplay failures remain explicitly deferred. |
| R3 Redis pending evidence, no unsafe game replay | pass | Runtime producer/processor wiring inspected; real Redis quarantine tests pass. Operational reconciliation/retention remains operator work. |
| R4 retained items.text lifecycle and retirement/archive | pass | Entire GenerationAI suite including real SQL/Mongo/Redis input, retry, scheduling, claim/provider, running recovery and reconciliation, plus two independent oracles: 200 passed. No actual external AI provider invoked. |
| R5 HTTP, architecture, stages, isolated storage checks | partial | Targeted contracts, architecture/stage gates and real adapter suites pass; IR-03 fixed. Complete project quality gate/coverage was not rerun. |
| R6 synthetic restore and evidence boundaries | pass | Independent PostgreSQL/Mongo/Redis restore drills pass. Evidence checker scope is file/hash/time attestations, without server backup/alert attestation. |
| R7 service env/network/config isolation | pass | Resolved environment/import/topology suite: 136 passed, 18 deselected. Real migration target verified. Actual server roles, ACLs and secret rollout excluded. |
| R8 Studio auth and selected-source reads | pass | App guards/wrappers traced and tested; disposable PostgreSQL rejects mutating CTE/function. Server permissions and arbitrary hostile Python are outside the app-level claim. |
| R9 trusted canonical email origin | pass | Config/service/route tests pass; production HTTPS and bounded debug loopback behavior verified. Actual email delivery excluded. |
| R10 dependency security compatibility | partial | Lock/config and exclusion changes reviewed; targeted runtime checks pass. Parent's final project-venv pip-audit hook Passed was independently read; no second vulnerability scan or full security audit performed. |

## Revised claims

Source: `independent-review-final-claims.md`, received after initial verdict.

| Claim | Judgment | Qualification |
|---|---|---|
| F1 SQL rollback and preserved ambiguous output | confirmed | Actual stores plus independent two-attempt oracle; no replay and no overwritten evidence. |
| F2 strict CI synthetic environment | confirmed | Both workflow environments and negative production-key tests checked. |
| F3 isolated migration/auth fixture | confirmed | Applies to the reviewed fixture and its consumers; no assertion about unrelated future tests. Capture before connection and actual owned PostgreSQL checks pass. |
| F4 Studio/email/restore limits retained | confirmed | App/local claims match source and observed checks; operational work remains deferred. |
| F5 historical broad run versus current targeted evidence | confirmed | 4490/3 is the previous recorded run, not a new independent complete-suite result. Current targeted evidence and final hook log were checked separately. |
| F6 current session action boundaries | confirmed for observed review/fix actions | Own synthetic resources used; no provider/email/production operations observed. Historical absolute server state cannot be established from checkout. |

Initial C1-C3 completeness objections are resolved within these local boundaries.
C4-C6 remain confirmed; C7-C8 are bounded historical logs; C9 retains its narrowed
current-session meaning. No full production completion is inferred.

## Independent test evidence

Runs overlap; counts must not be added as a count of unique tests.

- Initial broad focused nonexternal infrastructure: 394 passed / 293 deselected.
- Auth/WS/privileged/shared plus real restore/Redis: 287 passed / 7 skipped;
  seven extra failures were solely the review harness logging stub. All shared
  tests then reran with real logging: 46 passed. No product failure concealed.
- Resolved Compose env/import/service isolation: 136 passed / 18 deselected.
- Actual RedisJSON plus architecture/stages: 32 passed.
- Corrected CI and migration target guards: 17 passed, 16.05s.
- Actual disposable PostgreSQL migration/auth: 14 passed, 103.67s.
- Final entire GenerationAI suite + both independent corrected oracles:
  **200 passed, 1 upstream google-genai deprecation warning, 112.02s**.
- Parent's final 13-file hook evidence, independently read from
  `independent-review-fix-hooks.txt`: applicable YAML/Ruff/format/Markdownlint,
  Bandit, project-venv pip-audit, detect-secrets and whitespace checks Passed.
  This is verified execution evidence supplied by parent, not a second reviewer run.
- The original initial IR-01 reproducer and intermediate ambiguous-retry reproducer
  passed by asserting the defect; they are diagnostic evidence, not passing product tests.

Windows sandbox asyncio stalls were terminated; affected checks reran with approved
escalation and project-local basetemp. Fixtures create uniquely named owned containers
and clean them in finally blocks. No existing containers were changed.

## Remaining limits

No commit/push/deploy, remote CI, real provider/email, working database, private dotenv,
server secret rollout, DB role/Redis ACL, backup scheduling/offsite/retention/RPO/RTO,
alert receipt or full quality/coverage gate. Parent's current pip-audit hook passed;
the reviewer did not duplicate that vulnerability scan.
Gameplay fixes, rifts, chat performance and remaining AG-05 types are outside this
review. Those are explicit deferrals, not silently accepted production guarantees.
