from __future__ import annotations

import asyncio
from copy import deepcopy
from unittest.mock import AsyncMock

import pytest

from tests.backend.features.inventory.test_inventory_service import (
    FakeInventoryRepository,
    _active_character,
    _item,
    _service,
)


class DurableRepository(FakeInventoryRepository):
    def __init__(self, items):
        super().__init__(items)
        self.events = {}
        self.fail_commit = False

    async def apply_durability_damage(self, *, char_id, idempotency_key, payload, item_ids, expedition_run_id=None):
        async with self._durability_locks[char_id]:
            return await self._apply_damage(
                char_id=char_id, idempotency_key=idempotency_key, payload=payload, item_ids=item_ids
            )

    async def _apply_damage(self, *, char_id, idempotency_key, payload, item_ids):
        key = (char_id, idempotency_key)
        if key in self.events:
            if self.events[key][0] != payload:
                raise ValueError("Idempotency key payload conflict")
            return {"duplicate": True, "changed": []}
        if self.fail_commit:
            raise RuntimeError("commit failed")
        changed = []
        for item in self.items:
            if item.item_id not in item_ids:
                continue
            current = item.mechanics.get("durability_current", item.mechanics.get("durability_max"))
            if current is None:
                continue
            after = max(0.0, round(float(current) - payload["amount"], 4))
            if after == item.mechanics.get("durability_current"):
                continue
            item.mechanics = {**item.mechanics, "durability_current": after}
            changed.append({"item_id": item.item_id, "before": float(current), "after": after})
        self.events[key] = (deepcopy(payload), deepcopy(changed))
        self.committed = True
        return {"duplicate": False, "changed": changed}


def setup_service(redis_service, redis_client):
    _active_character(redis_client, state="combat_result")
    repository = DurableRepository(
        [
            _item(
                "sword-1",
                "weapon",
                slot="main_hand",
                placement="equipped",
                mechanics={"durability_current": 10, "durability_max": 12, "valid_slots": ["main_hand"]},
            )
        ]
    )
    return _service(redis_service, [], repository=repository), repository


async def damage(service, **overrides):
    return await service.apply_durability_damage(
        **{"char_id": 7, "amount": 0.1, "combat_id": "combat-1", "idempotency_key": "event-1", **overrides}
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["inventory", "character", "marker", "gear_score"])
async def test_retry_after_projection_failure_never_applies_twice(
    fake_redis_service, fake_redis_client, monkeypatch, failure
):
    service, repository = setup_service(fake_redis_service, fake_redis_client)
    await service.get_or_create_session(7)
    targets = {
        "inventory": (service.inventory_sessions, "set"),
        "character": (service.character_sessions, "set_items_projection"),
        "marker": (service, "_mark_durability_event_processed"),
        "gear_score": (service.stream_client, "request_gear_score_recalculation"),
    }
    target, method = targets[failure]
    original = getattr(target, method)
    monkeypatch.setattr(target, method, AsyncMock(side_effect=RuntimeError("projection failed")))
    with pytest.raises(RuntimeError, match="projection failed"):
        await damage(service)
    assert repository.items[0].mechanics["durability_current"] == 9.9
    monkeypatch.setattr(target, method, original)
    result = await damage(service)
    assert result["reason"] == "duplicate_event"
    assert repository.items[0].mechanics["durability_current"] == 9.9
    assert fake_redis_client.store["game:inventory:7"]["by_id"]["sword-1"]["mechanics"]["durability_current"] == 9.9
    assert fake_redis_client.store["game:ac:7"]["items"]["by_id"]["sword-1"]["mechanics"]["durability_current"] == 9.9


@pytest.mark.asyncio
async def test_sql_failure_keeps_cached_durability_unchanged(fake_redis_service, fake_redis_client):
    service, repository = setup_service(fake_redis_service, fake_redis_client)
    await service.get_or_create_session(7)
    repository.fail_commit = True
    with pytest.raises(RuntimeError, match="commit failed"):
        await damage(service)
    assert fake_redis_client.store["game:inventory:7"]["by_id"]["sword-1"]["mechanics"]["durability_current"] == 10
    assert repository.events == {}


@pytest.mark.asyncio
async def test_lost_marker_and_stale_cache_repaired_from_sql(fake_redis_service, fake_redis_client):
    service, repository = setup_service(fake_redis_service, fake_redis_client)
    await damage(service)
    fake_redis_client.store["game:ac:7"]["processed_events"] = {}
    fake_redis_client.store["game:inventory:7"]["by_id"]["sword-1"]["mechanics"]["durability_current"] = 1
    await damage(service)
    assert repository.items[0].mechanics["durability_current"] == 9.9
    assert fake_redis_client.store["game:inventory:7"]["by_id"]["sword-1"]["mechanics"]["durability_current"] == 9.9


@pytest.mark.asyncio
async def test_no_items_is_recorded_and_new_equipment_is_not_damaged_on_retry(fake_redis_service, fake_redis_client):
    service, repository = setup_service(fake_redis_service, fake_redis_client)
    repository.items = []
    assert (await damage(service))["reason"] == "no_durable_items"
    repository.items = [
        _item("new", "weapon", slot="main_hand", placement="equipped", mechanics={"durability_current": 10})
    ]
    await service.inventory_sessions.delete(7)
    assert (await damage(service))["reason"] == "duplicate_event"
    assert repository.items[0].mechanics["durability_current"] == 10


@pytest.mark.asyncio
async def test_missing_combat_key_and_conflicting_payload_rejected(fake_redis_service, fake_redis_client):
    service, _ = setup_service(fake_redis_service, fake_redis_client)
    with pytest.raises(ValueError, match="idempotency"):
        await damage(service, idempotency_key=None)
    await damage(service)
    for amount in (0.2, 0):
        with pytest.raises(ValueError, match="conflict"):
            await damage(service, amount=amount)


@pytest.mark.asyncio
async def test_sql_mechanics_refresh_preserves_dirty_runtime_placement(fake_redis_service, fake_redis_client):
    service, repository = setup_service(fake_redis_service, fake_redis_client)
    session = await service.get_or_create_session(7)
    service._unequip(session, "sword-1")
    session.is_dirty = True
    await service.inventory_sessions.set(session)
    await damage(service, scope="all_carried")
    cached = await service.inventory_sessions.get(7)
    assert cached.is_dirty
    assert cached.layout.backpack == ["sword-1"]
    assert cached.by_id["sword-1"].placement == "backpack"
    assert repository.items[0].mechanics["durability_current"] == 9.9


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("scope", "expected"),
    [
        ("equipped", {"equipped"}),
        ("belt", {"belt"}),
        ("all_active", {"equipped", "belt"}),
        ("all_carried", {"equipped", "belt", "backpack"}),
    ],
)
async def test_scope_preserved(fake_redis_service, fake_redis_client, scope, expected):
    service, repository = setup_service(fake_redis_service, fake_redis_client)
    repository.items = [
        _item("equipped", "weapon", slot="main_hand", placement="equipped", mechanics={"durability_current": 10}),
        _item("belt", "consumable", slot="belt_slot_1", placement="belt", mechanics={"durability_current": 10}),
        _item("backpack", "weapon", slot=None, placement="backpack", mechanics={"durability_current": 10}),
    ]
    result = await damage(service, scope=scope)
    assert {change["item_id"] for change in result["changed"]} == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("amount", [float("nan"), float("inf"), -float("inf")])
async def test_nonfinite_amount_rejected(fake_redis_service, fake_redis_client, amount):
    service, repository = setup_service(fake_redis_service, fake_redis_client)
    with pytest.raises(ValueError, match="finite"):
        await damage(service, amount=amount)
    assert repository.events == {}


@pytest.mark.asyncio
@pytest.mark.parametrize("duplicate", [False, True])
async def test_delayed_publication_cannot_overwrite_newer_durability(
    fake_redis_service, fake_redis_client, monkeypatch, duplicate
):
    service, repository = setup_service(fake_redis_service, fake_redis_client)
    await service.get_or_create_session(7)
    if duplicate:
        await damage(service)
    paused = asyncio.Event()
    release = asyncio.Event()
    writer_started = asyncio.Event()
    original_set = service.inventory_sessions.set
    original_apply = repository.apply_durability_damage

    async def delayed_set(session):
        if asyncio.current_task().get_name() == "slow-publication":
            paused.set()
            await release.wait()
        await original_set(session)

    async def tracked_apply(**kwargs):
        if kwargs["idempotency_key"] == "event-2":
            writer_started.set()
        return await original_apply(**kwargs)

    monkeypatch.setattr(service.inventory_sessions, "set", delayed_set)
    monkeypatch.setattr(repository, "apply_durability_damage", tracked_apply)
    slow = asyncio.create_task(damage(service), name="slow-publication")
    await asyncio.wait_for(paused.wait(), timeout=5)
    newer = asyncio.create_task(damage(service, idempotency_key="event-2"))
    await asyncio.wait_for(writer_started.wait(), timeout=5)
    release.set()
    await asyncio.wait_for(asyncio.gather(slow, newer), timeout=5)
    assert repository.items[0].mechanics["durability_current"] == 9.8
    for key in ("game:inventory:7", "game:ac:7"):
        document = fake_redis_client.store[key]
        items = document if key == "game:inventory:7" else document["items"]
        assert items["by_id"]["sword-1"]["mechanics"]["durability_current"] == 9.8
