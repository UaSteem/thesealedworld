"""Async orchestration; expensive preparation never runs on the event loop."""

import anyio
from loguru import logger

from src.backend.features.monsters.encounters.services.squad_selection_service import MonsterEncounterSelectionService


class CachedMonsterEncounterSelectionService:
    def __init__(self, cache, *, domain=None):
        self.cache = cache
        self.domain = domain or MonsterEncounterSelectionService()
        self.limiter = anyio.CapacityLimiter(2)

    async def select(self, order):
        logger.bind(order=order.model_dump(mode="json")).info("MonsterEncounterCachedSelectionRequested")
        identity = await anyio.to_thread.run_sync(self.domain.cache_identity, order, limiter=self.limiter)

        async def build():
            return await anyio.to_thread.run_sync(self.domain.build_pool, order, limiter=self.limiter)

        pool, status = await self.cache.resolve(identity, build)
        result = await anyio.to_thread.run_sync(self.domain.select_from_pool, order, pool, limiter=self.limiter)
        logger.bind(
            cache_status=status,
            seed=order.seed,
            status=result.status,
            members=[{"member_id": m.member_id, "tier": m.tier} for m in result.selection.members]
            if result.selection
            else [],
        ).info("MonsterEncounterCachedSelectionCompleted")
        return result, status
