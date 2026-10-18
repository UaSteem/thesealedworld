import asyncio
from types import SimpleNamespace

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from src.backend.infrastructure.monsters.managers.encounter_pool import (
    EncounterPoolCacheManager,
    EncounterPoolCacheUnavailable,
)


class MemoryRedis:
    def __init__(self):
        self.values = {}
        self.expiries = {}

    async def get(self, key):
        return self.values.get(key)

    async def set(self, key, value, nx=False, px=None):
        if nx and key in self.values:
            return False
        self.values[key] = value
        return True

    async def eval(self, script, count, *args):
        keys, values = args[:count], args[count:]
        if self.values.get(keys[0]) != values[0]:
            return 0
        if script == EncounterPoolCacheManager._PUBLISH:
            self.values[keys[1]] = values[1]
            self.expiries[keys[1]] = int(values[2])
            del self.values[keys[0]]
        elif script == EncounterPoolCacheManager._RENEW:
            return 1
        else:
            del self.values[keys[0]]
        return 1


def manager(client=None, **kwargs):
    client = client or MemoryRedis()
    return EncounterPoolCacheManager(SimpleNamespace(string=SimpleNamespace(client=client)), **kwargs)


@pytest.mark.asyncio
async def test_hundred_concurrent_orders_build_once_and_keep_fixed_daily_ttl():
    cache = manager()
    builds = 0

    async def build():
        nonlocal builds
        builds += 1
        await asyncio.sleep(0.05)
        return "valid"

    results = await asyncio.gather(
        *(cache.get_or_build("same-budget", build, lambda raw: raw == "valid") for _ in range(100))
    )
    assert builds == 1
    assert {raw for raw, _ in results} == {"valid"}
    assert [status for _, status in results].count("miss") == 1
    assert set(cache.client.expiries.values()) == {86400}
    assert (await cache.get_or_build("same-budget", build, lambda raw: raw == "valid"))[1] == "hit"
    assert builds == 1


@pytest.mark.asyncio
async def test_corrupt_owned_entry_is_rebuilt_without_deleting_other_keys():
    cache = manager()
    value_key, _ = cache.keys("budget")
    cache.client.values.update({value_key: "bad", "unrelated": "preserved"})

    async def build():
        return "good"

    assert await cache.get_or_build("budget", build, lambda raw: raw == "good") == ("good", "miss")
    assert cache.client.values["unrelated"] == "preserved"


@pytest.mark.asyncio
async def test_failure_and_cancellation_release_only_owned_lease():
    cache = manager()

    async def fail():
        raise ValueError("failure")

    with pytest.raises(ValueError):
        await cache.get_or_build("budget", fail, lambda _: True)
    assert cache.keys("budget")[1] not in cache.client.values
    started = asyncio.Event()

    async def slow():
        started.set()
        await asyncio.sleep(10)

    task = asyncio.create_task(cache.get_or_build("budget", slow, lambda _: True))
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert cache.keys("budget")[1] not in cache.client.values


@pytest.mark.asyncio
async def test_expired_owner_cannot_publish_over_successor():
    cache = manager(wait_seconds=0.2)
    value_key, lock_key = cache.keys("budget")

    async def build():
        cache.client.values[lock_key] = "new-owner"
        cache.client.values[value_key] = "winner"
        return "stale"

    result = await cache.get_or_build("budget", build, lambda _: True)
    assert result == ("winner", "wait")
    assert cache.client.values[lock_key] == "new-owner"


@pytest.mark.asyncio
async def test_redis_outage_fails_closed_without_cpu_build():
    class Broken(MemoryRedis):
        async def get(self, key):
            raise RedisConnectionError("offline")

    async def forbidden():
        pytest.fail("Redis outage must not trigger uncached CPU work")

    with pytest.raises(EncounterPoolCacheUnavailable):
        await manager(Broken()).get_or_build("budget", forbidden, lambda _: True)


@pytest.mark.asyncio
async def test_waiter_has_bounded_timeout():
    cache = manager(wait_seconds=0.01)
    cache.client.values[cache.keys("budget")[1]] = "other"

    async def forbidden():
        pytest.fail("Waiter must not build without owning lease")

    with pytest.raises(EncounterPoolCacheUnavailable, match="timed out"):
        await cache.get_or_build("budget", forbidden, lambda _: True)


@pytest.mark.asyncio
async def test_lease_is_renewed_during_a_slow_build():
    class Observed(MemoryRedis):
        renewals = 0

        async def eval(self, script, count, *args):
            if script == EncounterPoolCacheManager._RENEW:
                self.renewals += 1
            return await super().eval(script, count, *args)

    client = Observed()
    cache = manager(client, lease_ms=30)

    async def build():
        await asyncio.sleep(0.08)
        return "good"

    assert await cache.get_or_build("budget", build, lambda _: True) == ("good", "miss")
    assert client.renewals >= 2


def test_http_cache_outage_is_explicit_503(monkeypatch):
    import json

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from src.backend.config.settings import settings
    from src.backend.features.monsters.api.dependencies import get_cached_monster_selection_service
    from src.backend.features.monsters.api.router import router

    class BrokenService:
        async def select(self, order):
            raise EncounterPoolCacheUnavailable("offline")

    monkeypatch.setattr(settings, "frontend_internal_service_key", "test")
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_cached_monster_selection_service] = lambda: BrokenService()
    with TestClient(app) as client:
        response = client.get(
            "/api/admin/monsters/encounters/select",
            headers={"X-Internal-Service-Key": "test"},
            params={
                "order": json.dumps(
                    {
                        "encounter_type": "ordinary",
                        "location_tier": 0,
                        "seed": 1,
                        "family_ids": ["goblin_tribe"],
                        "player_gear_score": 35,
                    }
                )
            },
        )
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "monster_pool_cache_unavailable"


@pytest.mark.asyncio
async def test_facade_reuses_budgets_but_rebinds_current_order_and_seed():
    from src.backend.features.monsters.encounters.dto.selection import MonsterEncounterOrderDTO
    from src.backend.features.monsters.encounters.services.cached_selection_service import (
        CachedMonsterEncounterSelectionService,
    )
    from src.backend.features.monsters.encounters.services.squad_selection_service import (
        MonsterEncounterSelectionService,
    )
    from src.backend.features.monsters.integrations.encounter_pool_cache import MonsterEncounterPoolCache

    class CountingDomain(MonsterEncounterSelectionService):
        builds = 0

        def build_pool(self, order):
            self.builds += 1
            return super().build_pool(order)

    domain = CountingDomain()
    service = CachedMonsterEncounterSelectionService(MonsterEncounterPoolCache(manager()), domain=domain)
    first = MonsterEncounterOrderDTO(
        encounter_type="ordinary",
        difficulty="easy",
        location_tier=0,
        family_ids=("goblin_tribe",),
        player_gear_score=36.326,
        seed=1,
    )
    second = first.model_copy(update={"seed": 99, "player_gear_score": 36.327})
    a, status_a = await service.select(first)
    b, status_b = await service.select(second)
    assert (status_a, status_b) == ("miss", "hit")
    assert domain.builds == 1
    assert a.preparation.order == first
    assert b.preparation.order == second
    assert b == domain.select(second)
