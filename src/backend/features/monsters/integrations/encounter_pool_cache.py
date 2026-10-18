"""Monster-facing integration for shared, lazily prepared roster artifacts."""

import anyio

from src.backend.features.monsters.encounters.services.variant_pool import MonsterEncounterVariantPoolDTO


class MonsterEncounterPoolCache:
    def __init__(self, manager):
        self.manager = manager
        self.limiter = anyio.CapacityLimiter(2)

    async def resolve(self, identity, build):
        parsed = {}

        def decode(raw):
            try:
                pool = MonsterEncounterVariantPoolDTO.model_validate_json(raw)
                if pool.key_identity != identity:
                    return False
                parsed[raw] = pool
                return True
            except (ValueError, TypeError):
                return False

        async def valid(raw):
            return await anyio.to_thread.run_sync(decode, raw, limiter=self.limiter)

        async def serialize():
            return (await build()).model_dump_json()

        raw, status = await self.manager.get_or_build(identity, serialize, valid)
        return parsed[raw], status
