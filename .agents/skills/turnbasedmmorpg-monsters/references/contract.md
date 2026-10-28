# TurnBasedMMORPG Monsters - consumer contract map

Use this route when consuming the domain without changing its internals. This map points to existing guidance; it is not a newly verified API specification. The structural split preserves the previous guidance snapshot. Current signatures, complete DTO schemas, errors and end-to-end examples still require a separate substantive refresh against code/tests. Do not infer availability from a planned or retired surface.

## Read for the consumer task

| Consumer task | Existing contract material | Boundary / detail to check |
| --- | --- | --- |
| Prepare/select through public exports | [consumer contract](consumer-contract.md) | Order/result fields, linked JSON examples, rejection reasons, cached API wiring and infrastructure errors. |
| Replace retired Rift/Exploration callers | [consumer_migration](../../../../docs/ru/backend/features/monsters/consumer_migration.md) | Migration handoff and pending instance/consumer work; public exports alone do not prove availability. |

## Pending contract detail

The existing consumer contract is the detailed starting point. Runtime actor issuance and Rift/Exploration migration remain marked pending in that snapshot; this split has not verified their live completion. Confirm those boundaries before using a selected squad in Combat.

## Before integrating

Read the linked material for the affected surface; confirm the owning public entry point, input/output DTOs, rejection or unavailable behavior and an applicable example in current code/tests. If those details are absent, record the gap rather than inventing an API or bypassing the owner. Internal changes follow [properties](properties.md).
