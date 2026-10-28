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

## Current desktop priority

Owner decision 2026-10-24: focus on desktop from 2560×1440 and larger down to 1366×768, including 1920×1080. Check 3840×2160 and shorter browser content height too. Mobile/tablet development and acceptance are deferred. Earlier guidance is preserved in archive/game_mobile_legacy/2026-10-24/related-originals/.

Keep the field readable, preserve useful control sizes and use internal scrolling when content is long. Wider screens should add useful space rather than stretch every button. Shared desktop/touch components can retain mobile-prefixed names. Future phone design targets landscape, collapsible chat and less vertical world visibility; it is separate work.

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
- Whether the action panel leaves enough room for the main field at 1366×768 and reduced browser content height.
