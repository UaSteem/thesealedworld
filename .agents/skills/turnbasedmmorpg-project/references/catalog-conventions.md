# Catalog, bootstrap and visual-reference conventions

Read this when creating or restructuring a server resource catalog, its indexes, a catalog bootstrap, or an image-reference registry.
Do not apply it to merely collecting or drawing SVG assets.

## Start from the existing project path

Before proposing a new directory, loader, registry or bootstrap, inspect the nearest working project example.
Trace authored resource -> validation -> ID indexes -> owning facade -> DTO/API -> actual consumer.
Identify the authoritative domain and the current behavior separately from planned work.
Reuse the relevant project shape; preserve domain-specific rules rather than copying an entire neighboring domain.
Record a concrete reason when an existing pattern cannot meet the task. Do not silently introduce a parallel organization.

The owner's server-side default is Python-authored dictionaries/resources, Pydantic models where validation or serialization is needed, and dictionaries keyed by stable IDs for direct lookup.
JSON is appropriate for transport, caches, exports and temporary asset workbenches. A collected JSON manifest is not automatically a production runtime catalog.
Do not introduce filesystem JSON loading as the new server source of truth without a concrete task requirement or an explicit owner decision.

## Data and contracts

- Keep authored definitions in the owning feature's existing resource/catalog tree.
- Use Pydantic for validated fields, references and boundary DTOs; use `model_validate` and `model_dump` at the owning assembly/boundary.
- Existing Monsters composition/read definitions also use frozen dataclasses and read-only mappings. Preserve these supported contracts; do not rewrite them merely to make every type a Pydantic model.
- Build lookup dictionaries and needed secondary indexes from the same definitions. Reuse the existing catalog service/facade and its caching lifecycle.
- For new registries, validate duplicate IDs and cross-references before dictionary construction can hide duplicate entries. Monsters demonstrates this explicitly; do not assume every existing loader already does so.
- Separate a reusable mechanical basis from variants that reference it. Do not duplicate authored statistics for presentation variants.
- Keep definitions, generated instances and persisted records distinct. Loading an authored catalog must not create gameplay instances or trigger providers/database writes.
- Pydantic validation does not implement selection policy or prove filesystem availability. Keep domain selection explicit and test references at the appropriate boundary.

## Current examples to inspect

| Concern | Current source |
| --- | --- |
| Monster typed fields and immutable composition | `src/backend/features/monsters/catalog/contracts.py`, `nested_contracts.py` |
| Monster bases and clan variants | `src/backend/features/monsters/catalog/families/goblin_catalog/bases/`, `clans/base/members/` |
| Validation, ID maps and tag index | `src/backend/features/monsters/catalog/registry.py`, `validation.py`, `indexes.py` |
| Item Python resources and Pydantic loading | `src/backend/features/items/resources/bases.py`, `resources/base_item/`, `services/catalog_service.py` |
| Skill Python definitions and derived indexes | `src/backend/features/game_catalog/skills/resources/__init__.py`, `services/catalog_service.py` |

Paths after the first entry in a cell are relative to that entry's owning feature/catalog when abbreviated. Confirm the current files before reuse.

## Bootstrap: distinguish the two existing contracts

- `src/backend/features/monsters/catalog/bootstrap.py` builds a deterministic, localized catalog projection. `bootstrap_contracts.py` has typed `families`, `clans`, `members` dictionaries and a section manifest. The service-only API route in `monsters/api/router.py` supports ETag/304.
- `src/backend/features/game_catalog/services/catalog_service.py` builds the broader game text bootstrap from Items, Skills, Combat and family presentation. `game_catalog/dto/bootstrap.py` has the older, more permissive `catalogs` dictionary contract.
- `src/frontend/game_features/game_catalog/routes/bootstrap.py` proxies the existing backend bootstrap. `src/frontend/static/js/core/catalog.js` caches it in IndexedDB and performs dictionary lookups using manifest hashes.

These contracts have different audiences and payloads. Reuse the appropriate integration; do not add another bootstrap or copy the older `Any` payload shape as a blanket design rule.
For new sections, prefer explicit typed domain models while preserving the agreed consuming API contract. A schema/API migration is a separate implementation decision.
Serialize public catalog data from authoritative domain definitions. Keep private mechanics and local source paths out of the public client bootstrap; internal inspection DTOs have their own audience.

## Image references and asset publishing

Monsters already has `ImageAssetReference(asset_id, source_path, review_status, display_mirror)` in `catalog/contracts.py`.
A basis can supply `default_image`; a clan variant can supply an `image` override. `nested_contracts.py` resolves the chosen reference and records its provenance.
The image identity, source file, published frontend file and URL are different concerns.
`tools/monsters/publish_catalog_images.py` explicitly publishes linked local files to frontend static storage. Inspection must not invoke publishing merely to check references.
`catalog/bootstrap.py` and `inspection/services/catalog_view_service.py` project URLs into Pydantic response DTOs for their respective audiences.

Use this as an architectural example for other domains. Do not import a Monsters-owned contract into another domain or move it to shared solely for convenience.
Do not invent another asset registry, naming-derived selection rule, storage service or publishing path before inspecting the relevant owner's existing contracts.
An existing catalog image field does not prove the live instance/Combat path carries it. Inspect that consumer separately; do not bypass retired materialization guards.

For Items, the image-set/variant decision is recorded in `docs/adr/0001-item-visual-selection.md`.
The files under `assets/item_art/`, including JSON manifests, remain an asset workbench.
Items owns Python/Pydantic definitions in `resources/visuals/` and `services/visual_service.py`.
`generation_service.py` selects appearance after mechanics and persists it on the instance.
Two content-addressed WebP renditions are published explicitly through the existing S3 adapter, not copied into frontend static.
The existing GameCatalog bootstrap exposes public `item_visuals`; inventory projection chooses thumbnails or larger images.
Empty slots keep the local interface SVGs. Prepared AI lore is private until instance identification.
See `docs/ru/backend/features/items/visual_catalog.md` for the implemented sword slice and migration boundary.

## Proportionate verification

For a catalog change, check ID uniqueness, reference integrity, representative facade lookups and the actual projection/consumer affected by the task.
For a bootstrap change, check typed output, stable content hashes and intended field exposure; check HTTP caching only when that adapter changes.
For image references, distinguish reference validity, source-file existence, published-file existence and actual rendering. Report only what was checked.
Useful current examples: `tests/backend/features/monsters/catalog/test_authored_catalog.py`, `test_catalog_localization.py`, `test_catalog_bootstrap.py`, and `tests/backend/features/game_catalog/test_bootstrap_service.py`.
For a guidance-only edit, validate skill metadata, routing and links. Do not require a database, publishing or a live game merely to edit this reference.
