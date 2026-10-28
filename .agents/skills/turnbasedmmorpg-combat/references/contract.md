# TurnBasedMMORPG Combat - consumer contract map

Use this route when consuming the domain without changing its internals. This map points to existing guidance; it is not a newly verified API specification. The structural split preserves the previous guidance snapshot. Current signatures, complete DTO schemas, errors and end-to-end examples still require a separate substantive refresh against code/tests. Do not infer availability from a planned or retired surface.

## Read for the consumer task

| Consumer task | Existing contract material | Boundary / detail to check |
| --- | --- | --- |
| Supply snapshots and loadout data | [snapshots](snapshots.md) | Snapshot fields, producers, normalized skills and resolver ownership; examples in the reference. |
| Consume trigger DTOs/catalog keys | [trigger contracts](trigger-contracts.md) | Trigger identity and DTO boundary; [log rendering](trigger-log-rendering.md). |
| Interpret combat math and known limitations | [known issues and checks](known-issues-and-checks.md) | Known discrepancies and checks; formula ownership: [resolver math](resolver-math.md). |

## Pending contract detail

Session creation, participant commitments, ready/finalization events and post-combat result consumption are not described as a complete caller lifecycle in the preserved guidance. Documenting that consumer contract is pending the next refresh; the math and trigger references do not substitute for it.

## Before integrating

Read the linked material for the affected surface; confirm the owning public entry point, input/output DTOs, rejection or unavailable behavior and an applicable example in current code/tests. If those details are absent, record the gap rather than inventing an API or bypassing the owner. Internal changes follow [properties](properties.md).
