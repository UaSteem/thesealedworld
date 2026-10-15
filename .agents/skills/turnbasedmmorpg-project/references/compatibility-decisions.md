# Compatibility and workaround decisions

Use the global code-compatibility-decision skill to determine whether external clients, saved state, or rolling deployments require old behavior. If the user authorized a clean refactor, complete it without asking again. If a lasting workaround is necessary and the current request does not settle the choice, prepare concrete options and ask once.

Project constraints:

- Feature code uses feature integrations for infrastructure access. Do not bypass that boundary to keep an old call site.
- Do not create a second source of truth, duplicate DTO/schema/enum, or copy business logic into another layer solely to avoid migrating callers.
- Do not hide invalid catalog, configuration, or runtime data with a broad fallback or silent default.
- If an external compatibility contract requires a temporary adapter, keep it at the boundary, test the old contract, and record a removal condition.
- Keep shared contracts stable for both sides; do not reshape them for one local caller without checking all consumers.

For backend ownership, read .agents/skills/turnbasedmmorpg-backend/references/feature-architecture.md. For cross-side DTOs, read .agents/skills/turnbasedmmorpg-project/references/project-rules.md.
