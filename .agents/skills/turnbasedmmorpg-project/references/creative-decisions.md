# TurnBasedMMORPG Creative Approval Gate

## Purpose

Reading, diagnosis, code navigation, and non-mutating analysis are allowed by default.

Routine implementation work may proceed when the user explicitly asks for code changes and the work does not alter creative intent, game design, lore, visual direction, balance, or player-facing content.

Before changing creative material, check whether the user already authorized the specific creative direction or content change. If so, proceed within that scope. Ask only when a consequential creative choice remains unresolved.

## Creative Material

Treat these as creative or product-content changes:

- lore, worldbuilding, scenario text, quest text, dialogue, news copy, and public-facing marketing copy
- game-design rules, progression formulas, rewards, economy values, combat tuning, monster behavior, item stats, skill definitions, and balance numbers
- visual direction, UI mood, illustration prompts, generated images, icons, palettes, typography direction, and gameplay presentation
- catalog resources under backend feature content folders when the edit changes player-visible meaning or balance
- generated assets or prompts that define product style, fiction, creatures, locations, or factions

## Allowed Without Extra Creative Approval

Proceed normally when the user has already explicitly requested the specific creative change. Also proceed with implementation limited to:

- tests, type fixes, lint fixes, imports, or formatting
- bug fixes that preserve existing creative meaning and balance
- infrastructure, deployment, logging, diagnostics, or CI changes
- backend/frontend wiring that exposes existing approved content without changing it
- documentation that describes current behavior without inventing new lore, rules, or balance

## Required Approval Shape

When a requested implementation leaves the creative decision unresolved, prepare the concrete proposed change and then report:

```text
This touches creative/game-design material:
- <files or surfaces>
- <what would change>
- <why it matters>

Please choose the creative direction before I apply that unresolved change.
```

Do not bury creative changes inside a broader code patch.

## Relationship To Codex Config

Global Codex `config.toml` controls technical permissions such as sandbox mode, shell approvals, and trusted project paths.

This skill controls semantic approval: when the agent should pause before changing project creative intent even if filesystem permissions allow the edit.
