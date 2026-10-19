---
name: turnbasedmmorpg-project
description: Repository boundaries, agent-skill maintenance, compatibility, and creative decisions for TurnBasedMMORPG. Use for structural work, cross-domain choices, or project guidance changes.
---

# TurnBasedMMORPG Project

src/ is the target application tree. Frontend and backend communicate through HTTP/API contracts; src/shared holds cross-service enums, DTO contracts, and shared infrastructure helpers (`logging_config`, `log_middleware`, `metrics_middleware`), but must not contain domain business logic, ORM models, or service state.
Frontend directly owns the site database (`tbmmorpg_site`: accounts, auth, news, surveys, site Alembic migrations) and is strictly forbidden from directly accessing the game database (`tbmmorpg_game`), Redis game state, or Mongo game collections.
Distinguish stages: Legacy (old node-based Rift), Experimental / Dev-only (Hex Rift), and Pre-alpha active target (World, Expedition, Exploration). Procedural generation and simulations must use isolated `random.Random(seed)` rather than mutating global `random.seed()`.
Treat planning notes as proposals unless a current owner decision approves them. Existing user authorization carries forward; ask only for unresolved consequential choices.
For agent-skill edits, follow the global project-skills-maintainer workflow. Character skills are a game catalog owned by game-content.

## Read the relevant reference

| Task | Reference |
| --- | --- |
| Repository boundaries, donor code, handoff | [references/repository-operations.md](references/repository-operations.md) |
| Agent-skill edits | [references/agent-skill-maintenance.md](references/agent-skill-maintenance.md) |
| Compatibility or workaround choice | [references/compatibility-decisions.md](references/compatibility-decisions.md) |
| Lore, balance, visual, or public-copy choice | [references/creative-decisions.md](references/creative-decisions.md) |
| Parallel design prompts | [references/parallel-design-prompts.md](references/parallel-design-prompts.md) |
| Detailed ownership rules | [references/project-rules.md](references/project-rules.md) |
| Isolated Monsters contracts and Studio verification workflow | [Monsters domain workflow](../turnbasedmmorpg-monsters/references/domain-workflow.md) |

Read the referenced details for the task at hand. Verify implementation claims against current code and tests.
