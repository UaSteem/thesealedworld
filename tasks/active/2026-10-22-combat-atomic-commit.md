# A03-03/04/09: Combat create and exchange persistence

- Mode: independent reviewer, explicitly selected by user.
- State: in-progress.
- Base: fa2f2664; pre-existing untracked tasks/ must be preserved.

## Original request

«Реализуй исправление A03-03/04 вместе с fencing A03-09, с независимым ревизором. Сначала зафиксируй требования и план в MD, затем внеси изменения и проверь на реальном RedisJSON. Без коммита и деплоя.»

## Requirements

- [ ] R1: Exchange acceptance keeps actors, consumed queue prefix, targets, logs, analytics and meta consistent; failure must not expose partial accepted changes.
- [ ] R2: Repeated creation of the same combat ID preserves progress; same request is idempotent, conflicting request is rejected; incomplete creation has safe recovery.
- [ ] R3: Commit atomically checks lease owner and expected revision; stale executors cannot write. Retrying an accepted exchange cannot apply it twice.
- [ ] R4: Preserve resolver formulas, action ordering, gameplay outputs and unrelated changes.
- [ ] R5: Run meaningful isolated real RedisJSON integration checks, including failure, duplicate create, concurrent/stale writers and retry; independent reviewer checks implementation and final claims.
- [ ] R6: No commit, push or deployment; use disposable test storage only.

## Assumptions

Fingerprint uses stable creation inputs/commitment identities, excluding regenerated timestamps. Atomicity does not imply Redis disk durability or cross-service transactions. MULTI/Lua runtime errors do not themselves provide rollback.

## Initial plan

1. Inspect current manager, lifecycle, integration, executor and test infrastructure.
2. Establish regression tests before changes; choose a RedisJSON primitive preserving all-or-consistent acceptance, fencing and replay identity.
3. Implement manager-owned atomic create/commit and propagate result/expected revision/owner through callers; preserve gameplay.
4. Run focused tests and disposable real RedisJSON fault/concurrency tests; inspect diff.
5. Independent read-only review, address findings, recheck affected behavior and verify final claims.

## Execution and evidence

- Environment check: Docker Server 29.7.2 and local Redis Stack 7.2.0-v14 available. Disposable existing RedisJSON harness: `$env:RUN_REDISJSON_CONTRACT_TESTS='1'; .venv/Scripts/python.exe -m pytest tests/backend/core/redis/test_redisjson_contract.py -q --no-cov` — 3 passed; lead executed with Docker sandbox escalation.
- Executor reported 5 expected failures from new real RedisJSON regressions before production changes, including duplicate create resetting HP. Final verification pending.
- Unrelated concurrent finalization work appeared during execution: `experience_finalizer.py`, `test_finalization_recovery.py`, `tmp-finalization-red.txt`, and the separate finalization task MD. Preserve and exclude from this task's acceptance; initially only tasks/ was untracked.
- Lead independently ran the expanded `test_atomic_session_redis.py` suite with `RUN_REDISJSON_CONTRACT_TESTS=1` on disposable Redis Stack: 12 passed in 11.75s. This preceded the final append-log race fix and extra creation/legacy tests, so final recheck remains pending.
- Independent reviewer `/root/combat_reviewer` (GPT-6 Astra High) started with original request/requirements/initial plan and current source, without executor conclusions. Review pending.
- Concurrent unrelated Rift changes later temporarily broke imports through `core.arq_container` (`RiftZoneRuntimeDTO` missing). Record any affected verification as blocked rather than modifying the other task.
- Completed reviewed snapshot: lead and independent reviewer each ran 18 real RedisJSON tests successfully; reviewer ran 323 focused tests successfully and scoped Ruff passed. Reviewer P1 runtime analytics omission was corrected by deriving facts with existing support DTO/builder before staged commit; real wrongtype+all-live-dumps+retry test confirms correction. All reviewer findings resolved for that snapshot.
- Final stable-tree verification attempt detected source restoration during pytest: 9 owned source/test paths changed hashes; run invalid for acceptance (323 passed/19 failed against mixed old/new APIs). Both agents deny any baseline restoration. Do not attribute mixed-state failure to the reviewed implementation; do not claim current live tree verified.
- Preserved implementation snapshot under `tmp/codex/atomic-commit-preserved/` (relative paths retained). Asked owner to pause other writers before recovery/final stable-tree verification. Review result remains valid only for reviewed snapshot; task not complete until workspace stabilized.

| ID | Implementation | Verification | Evidence |
| --- | --- | --- | --- |
| R1-R6 | pending | pending | — |

## Independent review

Pending. Reviewer receives original request, requirements and initial plan without completion claims.

## User acceptance

Pending.
