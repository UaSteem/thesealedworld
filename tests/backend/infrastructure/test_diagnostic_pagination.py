from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.backend.infrastructure.combat.managers.session import CombatSessionManager
from src.backend.infrastructure.exploration.managers.encounter_runtime import ExplorationEncounterRuntimeManager
from src.backend.infrastructure.scenario.managers.session_manager import ScenarioSessionManager


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "manager_type,prefix",
    [
        (CombatSessionManager, "combat:rbc:"),
        (ScenarioSessionManager, "game:ac:"),
        (ExplorationEncounterRuntimeManager, "game:encounter:"),
    ],
)
async def test_oversized_scan_batch_preserves_all_keys_with_bounded_hydration(manager_type, prefix):
    keys = [
        f"{prefix}{i}"
        + (
            ":meta"
            if manager_type is CombatSessionManager
            else ":scenario"
            if manager_type is ScenarioSessionManager
            else ""
        )
        for i in range(5)
    ]
    client = SimpleNamespace(scan=AsyncMock(return_value=(0, keys)), hgetall=AsyncMock(return_value={"active": "1"}))
    json_module = SimpleNamespace(get=AsyncMock(return_value=[{"encounter_id": "e"}]))
    manager = manager_type(SimpleNamespace(redis_client=client, json_module=json_module))
    cursor = "0:0"
    sizes = []
    for expected_cursor in ("0:2", "0:4", None):
        page, cursor = await manager.list_session_page(cursor=cursor, limit=2)
        sizes.append(len(page))
        assert cursor == expected_cursor
    assert sizes == [2, 2, 1]
    assert client.scan.await_count == 3
    assert client.hgetall.await_count + json_module.get.await_count == 5
    hydration_calls = (
        client.hgetall.await_args_list if manager_type is CombatSessionManager else json_module.get.await_args_list
    )
    assert [call.args[0] for call in hydration_calls] == keys


@pytest.mark.asyncio
async def test_empty_scan_batch_retains_nonzero_continuation():
    client = SimpleNamespace(
        scan=AsyncMock(side_effect=[(47, []), (0, [b"combat:rbc:last:meta"])]),
        hgetall=AsyncMock(return_value={b"active": b"1"}),
    )
    manager = CombatSessionManager(SimpleNamespace(redis_client=client))
    assert await manager.list_session_page(limit=1) == ([], "47:0")
    assert await manager.list_session_page(cursor="47:0", limit=1) == ([("last", {"active": "1"})], None)
    assert [call.args[0] for call in client.scan.await_args_list] == [0, 47]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "cursor",
    ["-1:0", "0:-1", "1", "x:0", "0:1:2", "18446744073709551616:0", "0:9223372036854775808", "0:" + "1" * 5000],
)
async def test_invalid_cursor_rejected_before_redis(cursor):
    client = SimpleNamespace(scan=AsyncMock())
    with pytest.raises(ValueError):
        await CombatSessionManager(SimpleNamespace(redis_client=client)).list_session_page(cursor=cursor)
    client.scan.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("limit", [0, -1, 501, True, 1.5])
async def test_invalid_limit_rejected_before_redis(limit):
    client = SimpleNamespace(scan=AsyncMock())
    with pytest.raises(ValueError):
        await CombatSessionManager(SimpleNamespace(redis_client=client)).list_session_page(limit=limit)
    client.scan.assert_not_awaited()


@pytest.mark.asyncio
async def test_filtering_does_not_extend_hydration_budget_and_legacy_method_is_bounded():
    client = SimpleNamespace(
        scan=AsyncMock(return_value=(31, [f"combat:rbc:{i}:meta" for i in range(200)])),
        hgetall=AsyncMock(return_value={"active": "0"}),
    )
    manager = CombatSessionManager(SimpleNamespace(redis_client=client))
    assert await manager.scan_active_sessions() == []
    assert client.scan.await_count == 1
    assert client.hgetall.await_count == 100


@pytest.mark.asyncio
@pytest.mark.parametrize("manager_type", [ScenarioSessionManager, ExplorationEncounterRuntimeManager])
async def test_summary_errors_do_not_extend_budget_and_legacy_method_is_bounded(manager_type):
    client = SimpleNamespace(scan=AsyncMock(return_value=(71, [f"game:ac:{i}:scenario" for i in range(5)])))
    json_module = SimpleNamespace(get=AsyncMock(side_effect=[RuntimeError("expired"), None]))
    manager = manager_type(SimpleNamespace(redis_client=client, json_module=json_module))
    assert await manager.list_session_summaries(limit=2) == []
    assert client.scan.await_count == 1
    assert json_module.get.await_count == 2
