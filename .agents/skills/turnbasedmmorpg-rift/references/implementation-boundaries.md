## Current Approved Stage

The first approved development stage is the local dev harness described in:

- `docs/planning/tasks/rift/approved_stages/phase_01_local_dev_harness.md`

For now, this means:

- use JSON on disk as a design/source fixture;
- do not create DB models or migrations;
- do not freeze final API contracts;
- keep local unauthenticated test surfaces explicitly dev-only;
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
