## Game Screen Structure

Gameplay screens should be assembled from stable slots:

- header/menu slot
- main viewport/field slot
- left side panel slot
- right side panel slot
- bottom action panel slot
- footer chat drawer slot

Domain screens decide content:

- exploration: scene text/art, local services, navigation grid, encounter interrupt
- combat: actor state, exchange text, belt, abilities, feints, attack/refresh
- scenario: narrative, choices, requirements, result state
- loot: corpse/item list, inspect, claim, split, discard
- status: avatar, resources, attributes, skills, build actions
- inventory: containers, equipped gear, belt/pockets, item details

The slots themselves are shared.

## Mobile Priority

Mobile portrait is the hardest layout and must be designed first.

- Keep the main game field readable.
- Avoid turning actor/resource/status areas into scroll zones unless the screen is explicitly a panel or inventory.
- Chat expands upward and may cover lower UI by design.
- Drawers must not reflow critical controls.
- Text controls that require reading get height priority over icon-only controls.
- Icon-only ability/belt/tool rows must stay compact.

## Desktop And Tablet

Tablet and desktop reuse the same component contracts with different layout placement.

- Side panels may become persistent on desktop but drawer-based on mobile/tablet.
- Wider screens should add useful spacing or side panels, not stretch every button into oversized strips.
- Desktop game menu can be full navigation; mobile can use burger/menu behavior.
- Do not solve desktop by copying mobile widths blindly, and do not solve mobile by shrinking desktop.

## Data Honesty

Do not invent gameplay data just to fill a design.

- Use real catalog/view-model fields when available.
- Use explicit empty, unknown, locked, or `NO_DATA` states when data is not available.
- Do not show database keys as player coordinates or labels.
- Convert internal ids into player-facing names, coordinates, or unknown states.

## Preview Validation

For gameplay template or CSS changes, validate layout through the project preview renderer before relying on real game sessions:

```powershell
.\.venv\Scripts\python.exe tools\game_preview\render.py --fixture combat/active_8_abilities --out tmp\game_preview\combat_8.html
.\.venv\Scripts\python.exe tools\game_preview\render.py --fixture combat/active_10_abilities --out tmp\game_preview\combat_10.html
```

- Use `tools/game_preview/render.py` for combat, scenario, exploration, loot, rift, status, and inventory UI previews when fixture data exists.
- Add or extend a fixture under `tools/game_preview/fixtures/` when the affected state cannot be rendered with an existing fixture.
- Use preview fixtures for Codex-owned layout validation; real-data validation can be done by the user or through a provided live session URL.
- Do not open a real combat/session route unless the user provides a valid `char_id`, session URL, or dev/spectator route.
- Prefer preview states that stress the changed layout, for example 8 abilities and 10+ abilities for ability-strip work.

## Required Self-Check

Before finishing gameplay UI work, report:

- Which shared component/shell class owns the behavior.
- Which domain class only customizes content.
- Whether any page-local CSS should be promoted to a component.
- Whether the mobile action panel leaves enough room for the main game field.
