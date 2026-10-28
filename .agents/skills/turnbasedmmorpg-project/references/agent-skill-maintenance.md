# Agent-skill maintenance

Use the global project-skills-maintainer workflow for ownership, evidence, backup, and validation. Project-owned agent skills live in .agents/skills/turnbasedmmorpg-<domain>/SKILL.md. Keep each entrypoint short and route task details to focused references. Add a top-level domain only when an independent trigger warrants it.

Do not confuse agent guidance with the in-game character skill catalog under src/backend/features/game_catalog/skills. For catalog work, read .agents/skills/turnbasedmmorpg-game-content/references/skill-contracts-and-migration.md. An agent-skill-only edit needs structural and link checks; runtime tests apply when behavior changes.

## Main rule for domain skills

Every domain skill has a short `SKILL.md` with two explicit routes:

- **Use the domain:** `references/contract.md` describes or locates supported entry points, inputs/outputs, constraints, errors and examples for callers.
- **Change the domain:** `references/properties.md` explains ownership, structure, invariants and routes to thematic references. Keep existing detailed references when they remain independently useful.

Keep essential ownership and safety constraints in the entrypoint so choosing the consumer route cannot bypass them. Load only the route and references needed for the task. Mark missing or unverified contract details explicitly; a structural split does not prove current runtime behavior.

The existing domain skills are backend, frontend, combat, game-content, monsters, rift and studio. Project, quality, release, audit-remediation and content-archive are process/operational skills; retain task-based routing without inventing domain APIs. Content-archive governs local archive/export/cleanup procedures, not a runtime content service.

For this structural migration, retain existing material in properties and thematic references; contract maps may identify gaps pending the next substantive refresh. Future contract updates need implementation evidence and must keep caller guidance separate from internal design.
