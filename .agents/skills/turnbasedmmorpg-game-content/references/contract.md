# TurnBasedMMORPG Game Content - consumer contract map

Use this route when consuming the domain without changing its internals. This map points to existing guidance; it is not a newly verified API specification. The structural split preserves the previous guidance snapshot. Current signatures, complete DTO schemas, errors and end-to-end examples still require a separate substantive refresh against code/tests. Do not infer availability from a planned or retired surface.

## Read for the consumer task

| Consumer task | Existing contract material | Boundary / detail to check |
| --- | --- | --- |
| Use item definitions/resources | [items](items.md) | Items, affixes, scaling and text resources; verify owning DTOs before integration. |
| Use character skill IDs and surfaces | [skill contracts and migration](skill-contracts-and-migration.md) | Normalized values, DTO ownership and known disagreements; [IDs and progression](skill-ids-and-progression.md). |
| Use monster definitions or encounters | [monster abilities and compatibility](monster-abilities-and-compatibility.md) | Definition/Combat compatibility; encounter callers use the [Monsters contract](../../turnbasedmmorpg-monsters/references/contract.md). |
| Use lore/generated content | [lore interface](lore-interface.md) | Public library rules; [generation identity/determinism](generation-determinism.md). |

## Pending contract detail

The preserved materials cover catalog definitions and selected skill surfaces, but do not provide one complete inventory of public catalog/item/lore consumers with current DTOs, error behavior and end-to-end examples. That inventory remains pending the next refresh.

## Before integrating

Read the linked material for the affected surface; confirm the owning public entry point, input/output DTOs, rejection or unavailable behavior and an applicable example in current code/tests. If those details are absent, record the gap rather than inventing an API or bypassing the owner. Internal changes follow [properties](properties.md).
