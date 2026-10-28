# TurnBasedMMORPG Monsters

Keep the domain isolated behind its contract. Callers describe encounter type, location tier, difficulty, solo/group mode, one family, seed, optional player GS and optional complete profile override for tests/events. Monsters owns admission and composition. Profiles define two independent point pools: minions, and seniors (veteran/elite/boss), with allowed ranks and mandatory minimums. Builtin minion budgets scale by player GS divided by the measured reference GS of the location tier, capped by the profile; missing player GS rejects explicitly. Senior budgets retain separate capped step bonuses. Points never transfer between pools. Canonical unique variants preserve independent budgets and required ranks; only maximal feasible size and one fewer are retained, respecting the overall minimum (builtin goblins: three). Selection is seeded without maximizing spend. The API lazily caches request-neutral readiness and compact variant references in Redis for 86400 seconds, with fenced single-builder coordination. Only the overall squad has a minimum size; minions have no mandatory minimum; monster GS does not select rosters. Tags stay internal and group profiles reject explicitly. Do not move these rules into Rift, World or Studio.

Read only the reference needed:

| Task | Reference |
| --- | --- |
| Call Monsters from another domain; external order/result | [Consumer contract](../references/consumer-contract.md) |
| Replace retired Rift/Exploration consumers or align live player GS | [Consumer migration handoff](../../../../docs/ru/backend/features/monsters/consumer_migration.md) |
| Change internals, Studio validation or domain workflow | [Domain map and workflow](../references/domain-workflow.md) |

Preparation returns a ready pool and configurations; selection returns a complete concrete squad or rejection. Neither creates runtime instances. Keep these stages distinct. Do not enable retired persistence/generation as a fallback. Formula, balance, database and Combat changes require their own authorized scope.

The catalog alpha and detached probes are accepted. Character now uses canonical physical-v5 GS, the same model as diagnostic probes. Orders use its exact float score and version, never Arena's rounded matching value. Old-scale data is reset rather than converted. Actor issuance and Rift/Exploration consumer migration remain pending. Follow the migration handoff before claiming an encounter can enter live Combat; do not remove retirement guards.
