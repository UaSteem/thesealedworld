---
name: turnbasedmmorpg-studio
description: Local analytical studio ownership, source switching, and read-only behavior in TurnBasedMMORPG. Use for src/studio work.
---

# TurnBasedMMORPG Studio

Studio is a local analytical cabinet. It must not write to a selected source, including local and production.
Modules use the source switcher contract instead of coupling to local or production endpoints.

## Read the relevant reference

| Task | Reference |
| --- | --- |
| Studio ownership and read-only behavior | [references/ownership-readonly.md](references/ownership-readonly.md) |
| Source switcher, backend access, new module | [references/source-switcher-modules.md](references/source-switcher-modules.md) |
| Local running, diagnosis, checks | [references/operation.md](references/operation.md) |
| Concrete layout, settings, source flow | [references/studio-architecture.md](references/studio-architecture.md) |
| Smoke test, failures, SSH tunnel | [references/studio-smoke-and-operations.md](references/studio-smoke-and-operations.md) |

Read the referenced details for the task at hand. Verify implementation claims against current code and tests.
