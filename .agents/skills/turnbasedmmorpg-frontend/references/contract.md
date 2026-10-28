# TurnBasedMMORPG Frontend - consumer contract map

Use this route when consuming the domain without changing its internals. This map points to existing guidance; it is not a newly verified API specification. The structural split preserves the previous guidance snapshot. Current signatures, complete DTO schemas, errors and end-to-end examples still require a separate substantive refresh against code/tests. Do not infer availability from a planned or retired surface.

## Read for the consumer task

| Consumer task | Existing contract material | Boundary / detail to check |
| --- | --- | --- |
| Use game data and page/fragment responses | [feature architecture](feature-architecture.md) | Typed Backend clients, session context, view models and explicit unavailable/NO_DATA states. |
| Reuse shared components and tokens | [design system](design-system.md) | Shared component/CSS rules; gameplay [viewport contract](game-viewport-contract.md). |
| Integrate gameplay layout/theme | [game interface foundations](game-interface-foundations.md) | Gameplay rules; [theme tokens](game-theme-tokens.md) and [responsive preview](responsive-preview.md). |

## Pending contract detail

Ongoing frontend changes have not been refreshed in this stage. Complete page/fragment and session-context input/output shapes, supported browser actions and their unavailable/error states remain to be mapped against the current implementation.

## Before integrating

Read the linked material for the affected surface; confirm the owning public entry point, input/output DTOs, rejection or unavailable behavior and an applicable example in current code/tests. If those details are absent, record the gap rather than inventing an API or bypassing the owner. Internal changes follow [properties](properties.md).
