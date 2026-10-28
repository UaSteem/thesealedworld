# Responsive Game Shell Reference

Before sizing or redesigning any gameplay interface, read the owner's
[game-viewport-contract.md](game-viewport-contract.md). Its 2026-10-25 target
supersedes experimental prototype framing and historical mobile-first plans.
Do not infer accepted dimensions from the current Lab implementation.

## CSS Source Layers

Use these layers in order:

1. `src/frontend/static/css/theme_bundle.css`: shared game/core/scales.css plus the active game/themes/adventure.css, compiled to theme.css and loaded first. game/core/tokens.css is a standalone Lab compatibility entry, not runtime input.
2. `src/frontend/static/css/game/components/*.css`: shared game components.
3. `src/frontend/static/css/game/shell/layout/index.css`: base shell imports.
4. `src/frontend/static/css/game/domains/*/index.css`: domain/content imports.
5. `src/frontend/static/css/game/shell/responsive/index.css`: shared desktop responsive imports.
6. `src/frontend/static/css/game_bundle.css`: source entry that imports game modules.
7. `src/frontend/static/css/game.css`: compiled output, never direct-edit.

Trace imports and selectors against current templates before choosing an owning file. Read [game-theme-tokens.md](game-theme-tokens.md) for the approved future theme/shell direction. The future shell is not yet migrated runtime behavior.

## Base Shell Files

Templates:

- `src/frontend/templates/game/base_game.html`
- `src/frontend/templates/game/session_content.html`
- `src/frontend/templates/game/session_content_inner.html`
- `src/frontend/templates/game/includes/header.html`
- `src/frontend/templates/game/includes/footer.html`
- `src/frontend/templates/game/domains/game_menu/header_nav.html`

CSS:

- `src/frontend/static/css/game/shell/layout/index.css` and its imports
- `src/frontend/static/css/game/shell/responsive/index.css` and its imports

JS:

- `src/frontend/static/js/core/game_shell.js`

## Shell Tokens

Use these tokens instead of hard-coding shell dimensions in feature CSS:

- `--side-panel-width`
- `--side-panel-width-compact`
- `--game-drawer-width`
- `--center-content-max`
- `--game-header-height`
- `--game-footer-height`
- `--game-ui-scale`
- `--game-panel-z`
- `--game-overlay-z`

Feature CSS may introduce feature-local tokens, such as `--scenario-avatar-width`, but should derive them from viewport or shell context rather than redefining shell columns.

## Breakpoint Contract

Owner scope on 2026-10-24: desktop from 2560×1440 and larger down to 1366×768. Check 3840×2160, 2560×1440, 1920×1080 and 1366×768, including reduced browser content height. Preserve the 1280–1439 laptop tier: it applies at 1366.

Mobile/tablet development and checks are deferred. Removed mobile-only rules and earlier guidance are preserved with original paths, ranges and hashes in `archive/game_mobile_legacy/2026-10-24/`. Shared desktop/touch components may retain mobile-prefixed names; do not remove them by name. Future landscape-phone design is separate work.

For shared threshold changes trace the active shell imports. For one screen's overflow fix its internals.

## Domain CSS Responsibilities

Domain CSS may own:

- inner content grids;
- cards, action lists, text blocks, story panels;
- local avatar/image sizing;
- local scroll containers;
- feature-specific empty states;
- feature-specific breakpoints for content only.

Domain CSS must not own:

- shell column behavior;
- drawer mechanics;
- header/footer structure;
- game menu base layout;
- `leftOpen/rightOpen` grid behavior;
- global chat/HUD z-index layering.

## Common Workflow

1. Read the current dated task plan and game-theme-tokens.md; older layout plans are historical context.
2. Identify whether the issue is shell behavior or feature content behavior.
3. For shell behavior, trace layout/index.css or responsive/index.css to the owning source.
4. For feature content, edit only that feature CSS/template.
5. Avoid editing `game.css`; compile it later from `game_bundle.css`.
6. Verify with `git diff --check` and viewport checks.

## Search Commands

Find shell selector duplication:

```powershell
rg "\.game-header|\.game-footer|\.center-nav|\.cnav-btn|\.game-menu-icon|\.game-top-row|\.col-left|\.col-center|\.col-right" src\frontend\static\css\game
```

Find breakpoints:

```powershell
rg "@media" src\frontend\static\css\game
```

Find compiled/source entry references:

```powershell
rg "game_bundle|game.css|layout_responsive" src\frontend\static\css src\frontend\templates docs tests
```
