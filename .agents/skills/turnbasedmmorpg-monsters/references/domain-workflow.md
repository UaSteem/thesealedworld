# Domain map and workflow

Source owner: `src/backend/features/monsters/`.

| Responsibility | Location |
| --- | --- |
| Authored Python definitions, localized text, art defaults, shared equipment references | `catalog/` |
| Catalog filtering without selection | `catalog/search.py` |
| Build readiness and single instance assembly path | `instances/services/` |
| External order, internal admission/composition, preparation and concrete squad selection | `encounters/dto/`, `encounters/policies/`, `encounters/services/` |
| Common point-profile contracts, registry and provisional solo resources | `encounters/profiles/` |
| Presentation of domain results | `inspection/` |
| Protected HTTP adapter | `api/` |
| Cross-domain import boundary | `public.py` |

Follow backend and game-content skills for affected implementation details. Studio consumes selected-source HTTP APIs; it must not duplicate domain rules or write game data. Battle execution and log ownership remain in Combat.

The owner-approved development workflow is to work on an isolated domain through its contract, expose a Studio check for that contract, and keep reusable verification in domain tests or Studio. Before a requested commit, remove temporary diagnostic scripts outside the domain and Studio after retaining useful checks. Identify only scripts created for the current task; do not delete historical artifacts, reports or somebody else's tools as blanket cleanup.

Before a commit, verify branch and staged ownership. Preserve unrelated Combat changes. Record executed tests and Studio checks; distinguish preparation from actual squad selection. Never change DB records, balance or formulas merely to make a preview succeed.

Verification sources: `tests/backend/features/monsters/encounters/` for order, preparation and candidate search; readiness/assembly tests and API/Studio tests at their owning test folders. Verify actual paths before constructing commands.

Reusable offline battle probes use `python -m tools.monsters.balance_probe`; see `tools/monsters/balance_probe/README.md`. Keep native starter skills by default, label saved snapshots explicitly, and retain the manifest and per-seed results. This verification tool does not change domain balance or persistence.
