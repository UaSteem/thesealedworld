# Compatibility and workaround decisions

Use the global code-compatibility-decision skill to determine whether external clients, saved state, or rolling deployments require old behavior. If the user authorized a clean refactor, complete it without asking again. If a workaround is necessary and its choice has not been explicitly settled, explain the source cause, concrete alternatives and material costs, and ask before implementing the bypass. This includes temporary fixes, assets, rendering, UI, prototypes and labs; it is not limited to production or legacy clients. Use the global skill's references/workaround-decisions.md for the decision procedure and boundary examples.

Project constraints:

- Feature code uses feature integrations for infrastructure access. Do not bypass that boundary to keep an old call site.
- Do not create a second source of truth, duplicate DTO/schema/enum, or copy business logic into another layer solely to avoid migrating callers.
- Do not hide invalid catalog, configuration, or runtime data with a broad fallback or silent default.
- If an external compatibility contract requires a temporary adapter, keep it at the boundary, test the old contract, and record a removal condition.
- Keep shared contracts stable for both sides; do not reshape them for one local caller without checking all consumers.

For backend ownership, read .agents/skills/turnbasedmmorpg-backend/references/feature-architecture.md. For cross-side DTOs, read .agents/skills/turnbasedmmorpg-project/references/project-rules.md.

## Asset and Lab boundary

A fixed defect in an image belongs to its source asset unless runtime composition is an intended requirement. For example, hiding a forest cutout with an independently loaded tree is a workaround candidate: compare source compositing with runtime insertion and disclose additional texture/object/maintenance costs before choosing the latter. Procedural variation, depth/occlusion and animation can justify separate objects; do not prohibit them solely because they are separate.

During migration, check relevant inherited bypasses and runtime dependencies against the intended delivery. An ignored local Lab folder is not available to another Git checkout. Reuse a complete supported module/asset package or prepare a scoped source fix; do not disguise a partial copy or placeholder as a complete migration. Full catalog/count requirements must be represented explicitly in mocks, not replaced with a small sample presented as complete.

Existing authorization persists for the same disclosed decision. Do not create a new approval gate for ordinary source repair or launch a full audit solely because a workaround is discovered. Report the specific finding in the touched scope; do not assign authorship to the current chat without evidence.
