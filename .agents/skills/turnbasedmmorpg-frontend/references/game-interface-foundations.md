# TurnBasedMMORPG Game Interface Design

## Read by task

Inspect the current template and CSS for the game screen being changed. Read .agents/skills/turnbasedmmorpg-frontend/references/design-system.md when changing shared classes or components, .agents/skills/turnbasedmmorpg-frontend/references/game-css-shell.md for shared shell or responsive layout, and .agents/skills/turnbasedmmorpg-frontend/references/feature-architecture.md for route, view-model, or API-client changes. Combat UI contract changes also use .agents/skills/turnbasedmmorpg-combat/references/snapshots.md.
## Core Rule

Separate interface behavior from domain content.

Common behavior belongs in shared game components or shell/layout CSS. Domain CSS only decides what a specific screen puts inside those components.

Do not create a new domain-local panel, drawer, button language, footer, header, action bar, or shell container when the same behavior exists or should exist across gameplay screens.

## Layer Ownership

Use this order:

1. tokens: colors, fonts, spacing, borders, shadows, textures
2. shell: header, main, footer/chat, viewport, side-panel slots
3. layouts: mobile portrait, mobile landscape, tablet, desktop composition
4. components: action panel, buttons, drawers, cards, widgets, meters, tabs, lists
5. domain screen layer: exploration, combat, scenario, loot, status, inventory
6. prototype-only overrides

If a rule affects more than one gameplay domain, it is not domain CSS.

## CSS Naming Rule

Prefer a base class plus a domain modifier:

```css
.game-action-panel {}
.game-action-panel--bottom {}
.game-action-button {}
.game-action-drawer {}

.combat-action-panel {}
.exploration-action-panel {}
```

Avoid creating unrelated domain-only base systems for shared behavior:

```css
.combat-command-deck {}
.mobile-action-grid {}
.scenario-choice-panel {}
```

Those may exist only as domain wrappers or temporary prototype debt, not as the final reusable behavior layer.

## Action Panel Contract

Every gameplay screen that has player commands uses the shared action panel contract.

- The action panel position is common behavior.
- Current owner scope is desktop 2560×1440 and larger down to 1366×768. Mobile layout rules are deferred; earlier guidance is archived in archive/game_mobile_legacy/2026-10-24/related-originals/.
- The central screen/field takes remaining space above the action panel.
- Keep the main field and action controls usable at the minimum desktop content height.
- Drawers inside the action panel open as overlays and must not move the button that opened them.
- Clicking the same place should be able to close a drawer.
- Belt, abilities, local services, navigation, scenario choices, combat feints, loot actions, and encounter decisions are domain content inside the common action panel.
- Button surface, hover, disabled, active, icon mask, and metal/wood texture behavior are shared component concerns.

## Prototype Rules

For `design_prototype/`:

- Do not put all states into one giant HTML file.
- Create purpose pages such as `exploration.html`, `combat.html`, `status.html`, `inventory.html`, `scenario.html`, and `loot.html`.
- Current purpose-page previews cover the desktop matrix in game-theme-tokens.md; mobile/tablet previews are deferred.
- Keep shared prototype imports in entry CSS and reusable components.
- Keep domain-specific layout in `design_prototype/css/screens/<domain>.css`.
- When a pattern appears in two domains, stop and move the base behavior into `design_prototype/css/components/` before extending it further.
- Prototype CSS should mirror the future production split: tokens, shell, layouts, components, screen layer.
