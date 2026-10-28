# TurnBasedMMORPG Rift - consumer contract map

Use this route when consuming the domain without changing its internals. This map points to existing guidance; it is not a newly verified API specification. The structural split preserves the previous guidance snapshot. Current signatures, complete DTO schemas, errors and end-to-end examples still require a separate substantive refresh against code/tests. Do not infer availability from a planned or retired surface.

## Read for the consumer task

| Consumer task | Existing contract material | Boundary / detail to check |
| --- | --- | --- |
| Read generation metadata/movement language | [generation language](generation-language.md) | Master/node vocabulary and generation boundaries. |
| Choose existing runtime/prototype surface | [implementation boundaries](implementation-boundaries.md) | Legacy/dev/pre-alpha code anchors and hard stops; early base, not a final runtime API. |

## Pending contract detail

The preserved guidance explicitly treats Rift as an early base with separate legacy, dev-only and active progression stages. A final caller API, persistence model and combat-return contract are not approved by this map; resolving them requires the applicable stage/owner decisions.

## Before integrating

Read the linked material for the affected surface; confirm the owning public entry point, input/output DTOs, rejection or unavailable behavior and an applicable example in current code/tests. If those details are absent, record the gap rather than inventing an API or bypassing the owner. Internal changes follow [properties](properties.md).
