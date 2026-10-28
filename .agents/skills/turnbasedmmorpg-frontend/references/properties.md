# TurnBasedMMORPG Frontend

Frontend owns browser routes, page and fragment orchestration, view models, templates, static assets, and the site database (`tbmmorpg_site`: accounts, auth, news, surveys, site Alembic migrations).
Frontend is strictly forbidden from directly accessing the game database (`tbmmorpg_game`), Redis game state, or Mongo game collections; all game interaction must go through typed Backend HTTP/WS API clients.
Reuse shared design classes before creating new CSS; preserve the established shell and component ownership.

## Read the relevant reference

| Task | Reference |
| --- | --- |
| Battle report in persistent chat area (independent of chat delivery) | [combat report contract](../../turnbasedmmorpg-combat/references/tactical-states-and-report.md) |
| Routes, view models, API clients | [../references/feature-architecture.md](../references/feature-architecture.md) |
| Shared components and CSS tokens | [../references/design-system.md](../references/design-system.md) |
| Game shell, canvas frame, desktop sizing, any gameplay UI redesign | [../references/game-viewport-contract.md](../references/game-viewport-contract.md) |
| Game token/theme migration, palette values, HTML/Phaser theme boundary | [../references/game-theme-tokens.md](../references/game-theme-tokens.md) |
| Game CSS shell | [../references/game-css-shell.md](../references/game-css-shell.md) |
| Game screen or action panel | [../references/game-interface-foundations.md](../references/game-interface-foundations.md) |
| Responsive layout and previews | [../references/responsive-preview.md](../references/responsive-preview.md) |
| Public site | [../references/site-design.md](../references/site-design.md) |
| Admin or studio cabinet UI | [../references/cabinet-design.md](../references/cabinet-design.md) |
| Detailed layout and CSS references | [../references/frontend-layout.md](../references/frontend-layout.md) |

Read the referenced details for the task at hand. Verify implementation claims against current code and tests.
