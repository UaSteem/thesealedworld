---
name: turnbasedmmorpg-quality
description: Risk-proportionate tests, code checks, logging, and log diagnosis in TurnBasedMMORPG. Use for verification or debugging logs.
---

# TurnBasedMMORPG Quality

Choose checks for changed behavior and risk. Report exact commands and results; do not claim unrun checks passed.
The full checker delegates base steps to an external codex_core runner; inspect its available implementation before asserting those steps.

## Clean Verification & Test Semantics (SG10-W3)

- **Test Doubles vs Adapter Semantics**: In-memory fakes (`FakeRedis`) validate pure domain flow and mock plumbing, but do not prove wire serialization, TTL expiration, Lua script semantics, or transactional fencing. Concurrency and storage contract boundaries require dedicated adapter integration tests.
- **Clean Quality Gate**: Choose a reproducible environment and risk-proportionate checks. For full-project sign-off run `tools/dev/check.py`; when its dependencies are absent, report focused linter/type/test equivalents and the unrun gate explicitly. A focused pass is not a full-project sign-off.

## Read the relevant reference

| Task | Reference |
| --- | --- |
| Tests or coverage scope | [references/testing.md](references/testing.md) |
| Project validation commands | [references/validation.md](references/validation.md) |
| Logger calls or event context | [references/logging.md](references/logging.md) |
| Log investigation without implementation request | [references/log-diagnosis.md](references/log-diagnosis.md) |
| Current check commands | [references/check-commands.md](references/check-commands.md) |

Read the referenced details for the task at hand. Verify implementation claims against current code and tests.
