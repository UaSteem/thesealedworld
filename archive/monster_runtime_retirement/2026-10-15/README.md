# Retired persisted monster runtime

Byte-identical pre-retirement source snapshots, mapped by repository path plus `.snapshot`.
The active source retains algorithms behind permanent retirement guards. World/rift population startup and rebuild writes are disabled; Python catalog and anchor projections remain active.

- `src/backend/features/monsters/events/__init__.py`
- `src/backend/features/monsters/encounters/services/monster_group_service.py`
- `src/backend/core/containers/game.py`
- `src/backend/features/monsters/catalog/materialization/clan_factory.py`
- `src/backend/features/monsters/catalog/materialization/generation_builder.py`
- `src/backend/features/monsters/catalog/services/generated_rebuild_service.py`
- `src/backend/features/monsters/api/router.py`
- `src/backend/features/monsters/encounters/services/habitat_clan_pool_materialization_service.py`

Additional bootstrap/CLI snapshots:
- `deploy/docker-compose.yml`
- `deploy/compose.game.yml`
- `src/backend/features/monsters/scripts/rebuild_generated.py`

Superseded positive runtime tests are preserved under their original paths with `.snapshot`. Pure helper/assembler tests stay active; mixed test files retain helper and read/API checks. Replacement rejection coverage: `tests/backend/features/monsters/test_runtime_retirement.py`.
