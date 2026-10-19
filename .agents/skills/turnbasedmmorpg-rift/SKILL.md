---
name: turnbasedmmorpg-rift
description: Rift generation language and approved implementation boundaries in TurnBasedMMORPG. Use for rift design, metadata, routes, or runtime work.
---

# TurnBasedMMORPG Rift

Approved stages outrank exploratory notes. Distinguish generation metadata from live run and player progress state.
Use current owner decisions and existing codebase anchors before freezing persistence, APIs, Redis keys, or combat-return behavior.

## Stage Demarcation (SG10-K1)

- **Legacy**: Old node-based Rift (`src/backend/features/rift/`). Do not refactor or alter player contracts without an explicit owner decision.
- **Experimental / Dev-only**: Hex Rift (`tests/backend/features/rift/test_hex_rift.py`, `/api/dev/rift`). Must stay strictly gated behind `enable_dev_rift_routes` and bounded instance limits; blocked at edge.
- **Pre-alpha**: Active target progression and world systems (World, Expedition, Exploration).

## Generation Determinism (SG10-W4)

Procedural generation and simulations must use isolated `random.Random(seed)` instances. Never call global `random.seed()` or mutate global RNG state. Stabilize unordered candidates before RNG selection to prevent `PYTHONHASHSEED` nondeterminism across processes; preserve authored sequence order.

## Read the relevant reference

| Task | Reference |
| --- | --- |
| Master/node metadata and movement language | [references/generation-language.md](references/generation-language.md) |
| Approved stage, code, storage, or API boundary | [references/implementation-boundaries.md](references/implementation-boundaries.md) |

Read the referenced details for the task at hand. Verify implementation claims against current code and tests.
