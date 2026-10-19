## Current Stage Demarcation & Codebase Anchors

Rift development is demarcated across distinct codebase anchors:

- **Legacy Node-based Rift**: `src/backend/features/rift/api/router.py`, `src/backend/features/rift/integrations/runtime.py`, `docs/planning/tasks/rift/00_core_current_state.md`. Do not refactor or alter player contracts without an explicit owner decision.
- **Experimental Hex Prototype**: `tests/backend/features/rift/test_hex_rift.py`, `/api/dev/rift` in `src/backend/features/rift/api/router.py`. Must remain strictly dev-only behind `enable_dev_rift_routes` with bounded instance limits and edge blocking.
- **Active Pre-alpha Targets**: `src/backend/features/world/`, `src/backend/features/expedition/`.

For rift work:

- use JSON on disk or design fixtures for exploratory work;
- do not create new rift DB models or migrations without explicit owner decision;
- do not freeze final API contracts;
- keep local unauthenticated test surfaces explicitly dev-only;
- use isolated `random.Random(seed)` instances rather than mutating global `random.seed()`;
- use Redis/runtime projection only if that stage decision is being worked on and the owner confirms the exact task.

## Hard Stops

Confirm an explicit owner decision in the current request or approved stage before:

- creating rift DB models;
- creating Alembic migrations;
- creating shared DTOs or final API contracts;
- creating `src/backend/features/rift/` implementation files;
- choosing Redis key shapes;
- choosing how combat returns to rift;
- deciding contract-board behavior;
- deciding dirty loot behavior;
- treating planning notes as approved implementation steps;
- mixing generation metadata with live runtime/progress state.

## Editing Rule

Do not edit code for rifts unless the user explicitly asks with words such as:

- "пиши"
- "реализуй"
- "создай файл"
- "внеси правки"
- "сделай"
- "implement"
- "edit"

Discussion, design exploration, or statements like "надо делать" are not
permission to write code.

## Working Process

For rift design tasks:

1. Restate what layer is being discussed.
2. Separate owner-approved decisions from hypotheses.
3. Identify which metadata belongs to master and which belongs to node.
4. Identify what must remain out of scope for the current stage.
5. Update approved-stage task docs only when the owner asks to record a decision.
6. Update this skill only when a repeated rule has become stable enough to guide future agents.

## Current Status

This skill is an early base. It is intentionally not a final rift architecture
specification. Expand it as tasks are collected, decisions are confirmed, and
working code proves the shape of the system.
