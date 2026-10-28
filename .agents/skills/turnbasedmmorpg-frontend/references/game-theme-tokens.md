# Game tokens and themes

## Status and ownership

Owner direction recorded on 2026-10-24: use stable game tokens and separate theme values from component/responsive rules. The staged plan and verification evidence are in `tasks/active/2026-10-24-game-css-tokens-themes.md`; read its requirements before continuing that task. Theme migration does not imply the later Lab-shell or Phaser-screen redesign is implemented.

Current implementation: `theme_bundle.css` imports `game/core/scales.css` and `game/themes/adventure.css`, producing `theme.css`. `game_bundle.css` imports components/shell/domains/responsive sources and produces `game.css`. Runtime `game/base_game.html` and the preview renderer select Adventure before first paint and load theme before game. Both version stamps include theme output. `game/core/tokens.css` is a standalone Lab compatibility entry loading scales and Classic; it must not enter the runtime game graph. Classic source remains disabled in game runtime. Verify current imports/templates; historical `pages/game/layout*.css` are not active owners.

## Target token contract

- Keep token names stable across themes; theme sets change values. Reuse existing meaningful names before introducing replacements. Maintain a migration map for necessary renames.
- Cover color roles, typography, sizes/spacing, borders/radii, shadows and motion where reusable. Keep density/responsive dimensions independent of palette choice. Keep structural rules and media-query conditions in layout CSS; ordinary CSS variables cannot generally replace media-query conditions.
- Use base scales, semantic roles and limited component aliases. Do not tokenize every literal or turn a domain's local geometry into a global role. Document legitimate art/geometry exceptions.
- Keep separate compiled `theme.css` (tokens/theme values) and `game.css` (components/layout rules referring to tokens). Compile with the existing compiler during development/release, never for each player's theme selection. Do not manually edit compiled outputs. Update runtime and preview loaders/cache invalidation together when changing asset boundaries.
- Adventure (Rift Lab's “Тёплое приключение”) is the default and only enabled theme for the first migration. Preserve the current runtime palette as a complete second source set, including relevant inline/JS/component overrides, but exclude it from active imports, templates and settings until separately requested. Do not enable Lab's other palettes.
- Audit global/game source imports and cascade order, dynamic styles, tooltip portals and JS consumers. Scope game theme values to avoid changing site/cabinet surfaces; themed overlays outside that root need an explicit theme host.
- Read `docs/ru/frontend/interface_design/game_theme_token_contract.md` and the migration map for palette/scales, texture/filter ownership and geometry/content-art exceptions. Numbered tone identifiers preserve the historic shades for Classic; never renumber them or regenerate the one-shot migration. Prefer existing semantic roles for new components; append a shade only when a distinct value is required in both themes.
- Interface chrome uses col/game roles, not world-accent overrides. World data may style explicit content art. Risk-frame JS writes color-mix expressions referencing game-risk roles rather than a separate RGB palette. Raster item/scenario/world art stays content; decorative chrome textures and icon-tint filters belong to the theme.

## Shell and Phaser boundary

For sizing and all future central-area work, the owner's 2026-10-25
[game-viewport-contract.md](game-viewport-contract.md) is mandatory. It supersedes
earlier experimental Lab sizes and fixes four desktop checkpoints including
1600x900. It is a target contract, not a claim of completed runtime migration.

Target desktop shell: persistent HTML character panel at left; central gameplay field above persistent HTML chat at right. These components remain available between states including combat. Current owner scope is desktop: 2560×1440 and larger down to 1366×768, including 1920×1080. Check available browser content height. Mobile/tablet development is deferred; old mobile-only game code is archived with provenance in archive/game_mobile_legacy/2026-10-24/. Preserve shared desktop/touch consumers even when names contain mobile. Future phone work targets landscape, collapsible chat and less vertical world visibility at a readable object scale; it is not current acceptance scope.

Port only the approved Lab shell/visual direction with real runtime data contracts. Do not copy the experimental rift generator/scene, debug controls or mock character/chat into runtime. Choose HTML, Phaser or a combination per central screen; combat in Phaser is exploratory, not an instruction to migrate it now.

CSS variables do not automatically style canvas objects. A future game-owned JS adapter must read a defined token set, normalize colors/units, handle fonts and notify scenes without a second palette source. Preserve one Phaser Game's graphic caches across central screen changes; refresh authoritative data on return and reject stale responses. Keep input lifecycle explicit for hidden scenes.

A logical 600×600 scene with FIT preserves composition but also shrinks text and touch controls; it can leave letterboxing. RESIZE changes available canvas area and requires layout handling. Verify mobile readability, touch targets, input coordinates, orientation and DPR instead of promising automatic adaptive UI. See official [Scale Manager](https://docs.phaser.io/phaser/concepts/scale-manager) and [Scenes](https://docs.phaser.io/phaser/concepts/scenes) references when implementing.

## Verification proportional to the change

For migration: verify build/load graph, mandatory token keys in both sets, unresolved/cyclic variables, literal exceptions, theme isolation and first paint. Render affected real game fixtures with `tools/game_preview/render.py`; browser-check 3840×2160, 2560×1440, 1920×1080 and 1366×768, plus reduced browser content height. Mobile/tablet checks are deferred. Include hover/focus/disabled, long content, overlays, chat and combat. Record static, browser and runtime evidence separately. A guidance-only edit needs frontmatter/link and diff checks; it does not prove CSS/runtime migration.
