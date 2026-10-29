# TurnBasedMMORPG agent guidance

Project-owned skills live in `.agents/skills/`. Load the domain skill for the affected task, then only its relevant references. Verify implementation claims against current code, tests, and configuration.

For the new Vue/Vite game-client prototype in `game_ui_lab2`, first read [its entrypoint](game_ui_lab2/AGENTS.md) and local skill. For the previous UI reference in `game_ui_lab`, read [its entrypoint](game_ui_lab/AGENTS.md). Do not confuse either prototype with the current frontend in src or import backend code into a client.

| Task | Skill |
| --- | --- |
| Repository structure, cross-domain decisions, agent-skill upkeep | [project](.agents/skills/turnbasedmmorpg-project/SKILL.md) |
| Backend features, persistence, Redis Streams | [backend](.agents/skills/turnbasedmmorpg-backend/SKILL.md) |
| Frontend routes, templates, CSS, site, cabinet | [frontend](.agents/skills/turnbasedmmorpg-frontend/SKILL.md) |
| Combat resolver, snapshots, triggers, logs | [combat](.agents/skills/turnbasedmmorpg-combat/SKILL.md) |
| Items, monsters, character skills, generation, lore | [game-content](.agents/skills/turnbasedmmorpg-game-content/SKILL.md) |
| Monster encounter orders, candidate readiness, instances, domain consumer contracts | [monsters](.agents/skills/turnbasedmmorpg-monsters/SKILL.md) |
| Rift design or implementation | [rift](.agents/skills/turnbasedmmorpg-rift/SKILL.md) |
| Local retired game data, JSONL exports, archive discovery | [content-archive](.agents/skills/turnbasedmmorpg-content-archive/SKILL.md) |
| Local analytical studio | [studio](.agents/skills/turnbasedmmorpg-studio/SKILL.md) |
| Tests, validation, logging, log diagnosis | [quality](.agents/skills/turnbasedmmorpg-quality/SKILL.md) |
| Audit findings, cross-audit comparison, remediation or domain stabilization plans | [audit-remediation](.agents/skills/turnbasedmmorpg-audit-remediation/SKILL.md) |
| Versions, wipe, changelog, deployment, news | [release](.agents/skills/turnbasedmmorpg-release/SKILL.md) |

## Main rule for domain skills

Every domain skill has a short `SKILL.md` with two explicit routes:

- **Use the domain:** `references/contract.md` describes or locates supported entry points, inputs/outputs, constraints, errors and examples for callers.
- **Change the domain:** `references/properties.md` explains ownership, structure, invariants and routes to thematic references. Keep existing detailed references when they remain independently useful.

Keep essential ownership and safety constraints in the entrypoint so choosing the consumer route cannot bypass them. Load only the route and references needed for the task. Mark missing or unverified contract details explicitly; a structural split does not prove current runtime behavior.

The existing domain skills are backend, frontend, combat, game-content, monsters, rift and studio. Project, quality, release, audit-remediation and content-archive are process/operational skills; retain task-based routing without inventing domain APIs. Content-archive governs local archive/export/cleanup procedures, not a runtime content service.

Agent-skill maintenance follows the global `project-skills-maintainer` workflow and the project's [maintenance reference](.agents/skills/turnbasedmmorpg-project/references/agent-skill-maintenance.md). In-game character skills are owned by the game catalog under `src/backend/features/game_catalog/skills`.

`graphify-out/` is generated context and may be stale after source or skill changes. Verify claims against current files and regenerate only when the task requires a current graph.
