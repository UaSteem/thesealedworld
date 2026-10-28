# TurnBasedMMORPG Studio - consumer contract map

Use this route when consuming the domain without changing its internals. This map points to existing guidance; it is not a newly verified API specification. The structural split preserves the previous guidance snapshot. Current signatures, complete DTO schemas, errors and end-to-end examples still require a separate substantive refresh against code/tests. Do not infer availability from a planned or retired surface.

## Read for the consumer task

| Consumer task | Existing contract material | Boundary / detail to check |
| --- | --- | --- |
| Query a selected source through a client/module | [source switcher modules](source-switcher-modules.md) | request.state.source, cookie/env precedence, source-aware base URL and unavailable-backend handling. |
| Use analytical/source access safely | [ownership readonly](ownership-readonly.md) | Read-only source boundary and permitted local compute. |
| Run/diagnose the local cabinet | [operation](operation.md) | Local operation; detailed [smoke/operations](studio-smoke-and-operations.md). |

## Pending contract detail

The preserved source-switcher and operation references describe an earlier module/connectivity snapshot. This stage has not rechecked the current module inventory, concrete source clients or each module response/error shape; those details remain pending substantive refresh.

## Before integrating

Read the linked material for the affected surface; confirm the owning public entry point, input/output DTOs, rejection or unavailable behavior and an applicable example in current code/tests. If those details are absent, record the gap rather than inventing an API or bypassing the owner. Internal changes follow [properties](properties.md).
