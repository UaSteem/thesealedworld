# Independent infrastructure review: neutral requirements

Original current request (RU): Запускай общую независимую ревизию всего накопленного
инфраструктурного пакета, исправляй замечания и перепроверяй. Без коммита, push,
деплоя и изменения рабочих данных. Потом отчитайся, и перейдём к рифтам.

Earlier scope: remediate technical audit findings outside gameplay, current branch,
no new branch. Work was accumulated uncommitted; no commit/push/deploy or real data.
After finishing individual tasks owner requested a single final independent review.
Do NOT accept prior implementation summaries as evidence.

Contracts to evaluate against actual code and original findings in audit/01..11:
1. Production/privileged API authorization, safe logging/metrics, token revoke/expiry
   and refresh concurrency; historical earlier commits may be part of plan background.
2. CI artifact/dependency/image gates and production environment constraints; publishing
   develop->main, production secret rollout and real operations explicitly deferred.
3. Redis pending recovery must preserve evidence/quarantine without unsafe domain replay.
4. Only items.text AI retained; other AI ordering consumers retired to archive with
   matching paths, mascot/static media retained. Durable input/result, bounded retries,
   SQL->queue and running recovery, Mongo reconciliation, provider outside SQL txn.
5. HTTP settings frontend/backend contracts, architecture/test-stage gates, real
   storage contracts with isolated adapters. No suppression merely to hide issues.
6. Restore drills PostgreSQL/Mongo/Redis must use disposable synthetic data and cleanup;
   evidence/freshness checker must not overstate production backup/alert verification.
7. Service network/env isolation; remove unnecessary auth and unrelated DB/provider
   secrets while retaining actual runtime defaults/overrides/empty semantics and
   queue/task/timeouts/policy/TTL contracts. Shared config splitting must preserve strict
   API/frontend auth; migration/settings imports must not bypass it globally.
8. Studio authenticated access, selected-source HTTP/SQL/Redis read-only enforcement;
   only explicitly allowed local compute; production source must never mutate.
9. Email token URLs from trusted canonical HTTPS origin in production, no untrusted
   Host/forwarded override; preserve bounded loopback dev semantics.
10. Dependency security updates compatible; no new blanket security/type exclusions.

Explicit deferrals: full chat alpha/performance project; remaining AG-05 typing until
preparing merge main; gameplay changes/balance/new monsters/rifts. Actual server DB
roles/Redis ACL/secret rotation, backup scheduling/offsite/retention/RPO/RTO/alert
receipts and production rollout cannot be claimed from local mocks. Assess whether
these boundaries accurately reflect implemented work, not whether server operations
were performed despite the prohibition.

Workspace develop, huge accumulated dirty tree: start git diff/status and untracked
files. Final42file manifest var/audit/final-infrastructure-scope.json is ONLY a starting
point, NOT whole accumulated scope. Include earlier uncommitted infrastructure and
AI retirement in src/archive/tests/deploy/tools/config. Avoid secrets: never read .env,
.env.prod/private keys or dump actual container configs/DBs. No production networking.
Reviewer must not modify source/tests/docs or spawn agents. May write private findings
and ordinary test artifacts under var/audit and var/pytest-review-*. Safe targeted unit
checks permitted; isolated disposable Docker checks only own volumes with cleanup.

Deliver initial independent verdict BEFORE looking at prior status/results prose.
Findings: severity, file:line, trigger/impact, requirement, minimal correction and
verification. Requirement table pass/partial/fail/unverified; distinguish actual bugs,
known operational boundaries and unrelated gameplay issues. Report coverage limits.
Later parent supplies claims for a separate evidence check. Do not hunt mandatory bugs.
