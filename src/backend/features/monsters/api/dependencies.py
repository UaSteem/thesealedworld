from fastapi import HTTPException, Request

from src.backend.features.monsters.encounters.services.cached_selection_service import (
    CachedMonsterEncounterSelectionService,
)
from src.backend.features.monsters.integrations.encounter_pool_cache import MonsterEncounterPoolCache


async def get_cached_monster_selection_service(request: Request) -> CachedMonsterEncounterSelectionService:
    service = getattr(request.app.state, "monster_encounter_selection", None)
    if service is None:
        managers = getattr(request.app.state, "redis_managers", None)
        if managers is None:
            raise HTTPException(status_code=503, detail={"code": "monster_pool_cache_unavailable"})
        service = CachedMonsterEncounterSelectionService(MonsterEncounterPoolCache(managers.monster_encounter_pools))
        request.app.state.monster_encounter_selection = service
    return service
