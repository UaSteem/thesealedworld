---
name: turnbasedmmorpg-frontend
description: Frontend routes, templates, design system, game UI, public site, and cabinet in TurnBasedMMORPG. Use for frontend implementation or visual changes.
---

# TurnBasedMMORPG Frontend

Frontend owns browser routes, view models, templates, static assets and the site database (`tbmmorpg_site`). It must never access the game database, Redis game state, Mongo game collections or backend internals directly; game interaction uses typed Backend HTTP/WS API clients. Reuse shared CSS and preserve shell/component ownership.

Before adding or retaining a workaround as the chosen design, follow [the workaround decision rule](../turnbasedmmorpg-project/references/compatibility-decisions.md); it also covers assets, rendering, prototypes and labs. Discuss an unresolved bypass before implementing it; do not re-approve an already explicit owner choice.

## Choose the route

- **Use this domain from a caller or adjacent domain:** read [Consumer contract](references/contract.md). Stay within supported entry points and handle documented limits/errors.
- **Change this domain:** read [Properties and implementation guidance](references/properties.md), then only the relevant thematic references.

This stage separates existing guidance structurally. Verify implementation claims against current code, tests and configuration; missing contract details remain pending substantive refresh.
