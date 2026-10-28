# TurnBasedMMORPG Game CSS Shell

## First Reads

First read [game-viewport-contract.md](game-viewport-contract.md) for the owner's
2026-10-25 shell agreement. It overrides experimental Lab dimensions: the full
status/canvas/chat container is capped at 1920px, independently of the page-wide
header and available height. Current implementation is not proof of acceptance.

Read:

- `.agents/skills/turnbasedmmorpg-frontend/references/responsive-shell.md`
- The current shell task and [game-viewport-contract.md](game-viewport-contract.md).

Also use:

- .agents/skills/turnbasedmmorpg-frontend/references/feature-architecture.md for routing/template/API boundaries.
- .agents/skills/turnbasedmmorpg-frontend/references/design-system.md for visual/component reuse.
- .agents/skills/turnbasedmmorpg-frontend/references/game-interface-foundations.md for HUD and action-panel design.

## Core Rules

- Treat `src/frontend/static/css/game.css` as compiled output. Do not edit it directly.
- Treat `src/frontend/static/css/game_bundle.css` as the game CSS source entry.
- Load compiled `theme.css` before `game.css`; tokens come from theme_bundle.css, not imports from the game layout bundle. Standalone Lab's game/core/tokens.css compatibility entry must not be restored to the runtime game bundle.
- Trace base shell styles from `src/frontend/static/css/game/shell/layout/index.css` and responsive/drawer styles from `src/frontend/static/css/game/shell/responsive/index.css` to their imported sources. Verify selectors against current templates before choosing the file to edit.
- For game token/theme changes and the approved future shell direction, read [game-theme-tokens.md](game-theme-tokens.md). Its target contract does not mean runtime migration is complete.
- Keep shell behavior in shell CSS. Domain CSS should style content inside shell containers.
- If side panel behavior or breakpoint behavior is wrong across screens, fix the owning shared shell source found through those imports, not every domain CSS file.
- If one feature's content overflows, fix that feature's internal CSS using shell tokens.
- Before editing shared shell selectors, inspect all current definitions with `rg`.
- Gameplay action panel placement, chat slot behavior, side panel slots, and viewport sizing are shell/component contracts. Do not reimplement them independently in exploration, combat, scenario, loot, or inventory CSS.

## Compiled CSS Discipline

Never hand-edit compiled CSS after running the compiler.

After compilation, do nothing manually to `src/frontend/static/css/game.css`.

The compiler removes comments and may leave whitespace or line-ending diffs.
That output is still the compiler output. Do not clean it, narrow it, restore
comments, fix line endings, or copy selected hunks by hand.

If compiled output should not be part of the current task, revert `game.css` as
a whole. Otherwise accept the compiler output exactly as produced.

## Template Preview Discipline

For game shell, responsive layout, action panel, or domain template/CSS changes, use the local preview renderer before trying to inspect live game routes:

```powershell
.\.venv\Scripts\python.exe tools\game_preview\render.py --fixture combat/active_10_abilities --out tmp\game_preview\combat_10.html
.\.venv\Scripts\python.exe tools\game_preview\render.py --fixture combat/active_10_abilities --serve
```

- The preview renderer links `src/frontend/static/css/game.css`, matching the real game shell. Compile static assets before visual CSS checks when source CSS changed.
- Use `--serve` when assets under `/static/...` must load in a browser screenshot.
- Add focused fixtures under `tools/game_preview/fixtures/` for new gameplay states instead of depending on live user sessions.
- Only inspect a live combat/session route when the user provides a valid session URL, `char_id`, or explicit dev/spectator route.

## Shell-Owned Selectors

Do not redefine these in domain CSS unless the task is explicitly shell refactor work:

- `.game-header`
- `.game-footer`
- `.center-nav`
- `.cnav-btn`
- `.game-menu-icon`
- `.game-top-row`
- `.col-left`
- `.col-center`
- `.col-center-inner`
- `.col-right`
- `.shell-constrained`
- `#game-chat-shell`
- `.hud-window`

## Verification

For shell/responsive work:

- Run `git diff --check`.
- Render affected template states with `tools/game_preview/render.py`; for responsive checks, use fixtures that stress the changed state.
- Do not hand-edit compiled `game.css`.
- Compile static output before browser validation when source CSS changed.
- Required owner checkpoints: `2560×1440`, `1920×1080`, `1600×900`, `1366×768`, plus reduced browser content height. Larger screens are additional checks; mobile/tablet work is deferred. Follow [game-viewport-contract.md](game-viewport-contract.md).
- Search for accidental shell selector duplication in domain CSS.
