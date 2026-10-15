---
name: turnbasedmmorpg-project
description: Repository boundaries, agent-skill maintenance, compatibility, and creative decisions for TurnBasedMMORPG. Use for structural work, cross-domain choices, or project guidance changes.
---

# TurnBasedMMORPG Project

src/ is the target application tree. Frontend and backend communicate through HTTP/API contracts; src/shared holds only stable cross-side contracts.
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

Read the referenced details for the task at hand. Verify implementation claims against current code and tests.
