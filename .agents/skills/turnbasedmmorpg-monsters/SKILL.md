---
name: turnbasedmmorpg-monsters
description: Monster encounter orders, admission, candidate readiness, instance assembly and consumer contracts in TurnBasedMMORPG. Use for the Monsters domain or callers integrating with it; use game-content for item definitions and combat for battle execution.
---

# TurnBasedMMORPG Monsters

Keep admission/composition inside Monsters. Callers use its order/result contract; never transfer minion/senior budgets, relax mandatory ranks, substitute solo for rejected group mode, or enable retired runtime as fallback. Preparation, selection and runtime instance delivery are distinct. Exact Character GS and seeded selection follow the consumer contract; live Combat delivery and caller migration must be verified before claiming availability.

## Choose the route

- **Use this domain from a caller or adjacent domain:** read [Consumer contract](references/contract.md). Stay within supported entry points and handle documented limits/errors.
- **Change this domain:** read [Properties and implementation guidance](references/properties.md), then only the relevant thematic references.

This stage separates existing guidance structurally. Verify implementation claims against current code, tests and configuration; missing contract details remain pending substantive refresh.
