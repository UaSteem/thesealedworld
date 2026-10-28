---
name: turnbasedmmorpg-studio
description: Local analytical studio ownership, source switching, and read-only behavior in TurnBasedMMORPG. Use for src/studio work.
---

# TurnBasedMMORPG Studio

Studio is a local analytical cabinet and must never mutate the selected LOCAL/PROD data source. Local compute or explicitly triggered local dev simulation requires an effective local source (`request.state.source.kind`, cookie before environment fallback) and must be blocked for remote/read-only sources. Modules use the source-switcher contract.

## Choose the route

- **Use this domain from a caller or adjacent domain:** read [Consumer contract](references/contract.md). Stay within supported entry points and handle documented limits/errors.
- **Change this domain:** read [Properties and implementation guidance](references/properties.md), then only the relevant thematic references.

This stage separates existing guidance structurally. Verify implementation claims against current code, tests and configuration; missing contract details remain pending substantive refresh.
