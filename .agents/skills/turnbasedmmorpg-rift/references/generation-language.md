# TurnBasedMMORPG Rift Design Gate

## Purpose

Use this skill as the first guardrail for all rift work.

The rift system is under active design. Do not treat existing planning notes as
an implementation contract. The current goal is to build the shared language and
approved stages first, then expand this skill as real tasks and working code
stabilize.

## Read First

- `.agents/skills/turnbasedmmorpg-project/references/repository-operations.md`
- `.agents/skills/turnbasedmmorpg-project/references/agent-skill-maintenance.md` when editing this skill
- `docs/planning/tasks/rift/README.md`
- `docs/planning/tasks/rift/00_core_current_state.md`

For backend/API/service work, also read:

- `.agents/skills/turnbasedmmorpg-backend/references/feature-architecture.md`

For frontend/game UI work, also read:

- `.agents/skills/turnbasedmmorpg-frontend/references/feature-architecture.md`
- `.agents/skills/turnbasedmmorpg-frontend/references/game-interface-foundations.md`

## Source Priority

Use sources in this order:

1. Direct project-owner decisions in the current conversation.
2. `docs/planning/tasks/rift/README.md` and established codebase anchors (`src/backend/features/rift/`).
3. Other `docs/planning/tasks/rift/*` files only as idea drafts, not contracts.

If these sources conflict, pause and ask the project owner. Do not resolve the
conflict by inventing a permanent rule.

## Current Working Model

Rift work currently focuses on a pre-instance generation layer.

The important distinction:

- Master metadata and node metadata describe material used to generate a rift instance.
- They are not player runtime state, run progress, combat result state, or final persistence contracts.

Do not introduce runtime/run/progress concepts unless the owner explicitly asks
to design that layer.

## Master Metadata

Master metadata describes the broader generated zone language and generation
context. It may include:

- biome or semantic tags;
- the zone's general descriptive style;
- the opening/leading part of location descriptions;
- metadata for blocked passages, collapses, walls, unavailable directions, and similar obstacles;
- language resources used by generation and rendering;
- rules or metadata that allow the zone to expand.

This is generation metadata for future rift instances, not a live rift run.

## Node Metadata

Node metadata describes generated location-node material used by future rift
instances. It may include:

- node title;
- node-specific description details;
- data inserted into movement button templates;
- destination-driven transition wording data;
- template variables needed by the movement/transition renderer;
- node-specific suffixes or details for unavailable or blocked states.

The movement engine may own button templates, but the node owns the data used to
fill those templates.

## Transition Principle

Use destination-driven transitions as the working direction:

- Button text is assembled from the destination node's data.
- The engine owns reusable button templates.
- Nodes store the lexical/template data needed to make those buttons read correctly.
- Blocked or unavailable paths use master metadata plus node-specific data.

Do not reduce rift movement to exploration navigation. Rift movement is expected
to be its own layer because transitions can be symbolic, vertical, blocked,
destination-driven, or non-coordinate-like.
