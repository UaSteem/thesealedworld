"""Joint consumer→real ASGI router contract; only Redis storage is an in-memory double.

No application lifespan, real credentials, Redis connection or game catalog changes.
"""

from __future__ import annotations

from importlib import import_module
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI

from src.backend.infrastructure.game_config.base import BaseGameConfig, ConfigEntryMeta
from src.backend.infrastructure.game_config.manager import GameConfigManager
from src.frontend.integrations.backend_api.game_config import GameConfigApi

config_routes = import_module("src.backend.features.game_config.api.router")

pytestmark = pytest.mark.integration
BASE_URL = "http://backend.contract.test"
READ = "contract-reader"  # pragma: allowlist secret
WRITE = "contract-writer"  # pragma: allowlist secret
SERVICE = "contract-service"  # pragma: allowlist secret


class ContractConfig(BaseGameConfig):
    namespace = "contract_http"
    RATE = 1.5
    LIMIT = 3
    ENABLED = True
    TITLE = "Тест"
    config_metadata = {
        "RATE": ConfigEntryMeta(
            label="Тестовый коэффициент",
            description="Только синтетический контракт",
            group="Контракт",
            unit="ratio",
            min_value=0,
            max_value=10,
            step=0.5,
            risk="medium",
            live_scope="new_exchange",
            tags=("contract", "http"),
        ),
        "LIMIT": ConfigEntryMeta(min_value=0, max_value=10),
    }


class OtherConfig(BaseGameConfig):
    namespace = "contract_other"
    TITLE = "Другая настройка"


class MemoryRedis:
    """Only the manager's get/set/NX surface, not Redis wire semantics."""

    def __init__(self):
        self.data = {}
        self.calls = []

    async def get(self, key):
        self.calls.append(("get", key))
        return self.data.get(key)

    async def set(self, key, value, *, nx=False):
        self.calls.append(("set", key))
        if nx and key in self.data:
            return False
        self.data[key] = str(value)
        return True


@pytest.fixture
async def contract(monkeypatch):
    from src.backend.config import settings as backend_config

    monkeypatch.setattr(
        backend_config,
        "settings",
        SimpleNamespace(
            operator_read_key=READ,
            operator_write_key=WRITE,
            frontend_internal_service_key=SERVICE,
            site_to_game_service_key=SERVICE,
        ),
    )
    storage = MemoryRedis()
    manager = GameConfigManager(storage)
    manager.register(ContractConfig)
    manager.register(OtherConfig)
    await manager.bootstrap()
    app = FastAPI()
    app.include_router(config_routes.router)
    app.state.game_config = manager
    requests = []

    async def observe(request):
        requests.append((request.method, request.url.path, request.headers.get("X-Operator-Key")))

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url=BASE_URL, event_hooks={"request": [observe]}
    ) as http:

        def api(**overrides):
            options = {"operator_read_key": READ, "operator_write_key": WRITE}
            options.update(overrides)
            return GameConfigApi(http, BASE_URL, **options)

        yield SimpleNamespace(api=api, http=http, manager=manager, storage=storage, requests=requests)


async def entries(api, namespace="contract_http"):
    return {entry.key: entry for entry in await api.list_namespace(namespace)}


async def test_real_serialization_metadata_and_default_types(contract):
    result = await entries(contract.api())
    assert set(result) == {"RATE", "LIMIT", "ENABLED", "TITLE"}
    rate = result["RATE"]
    assert (rate.namespace, rate.current, rate.default, rate.value_type, rate.is_modified) == (
        "contract_http",
        "1.5",
        "1.5",
        "float",
        False,
    )
    assert (rate.label, rate.description, rate.group, rate.unit) == (
        "Тестовый коэффициент",
        "Только синтетический контракт",
        "Контракт",
        "ratio",
    )
    assert (rate.min_value, rate.max_value, rate.step, rate.risk, rate.live_scope, rate.tags) == (
        0,
        10,
        0.5,
        "medium",
        "new_exchange",
        ["contract", "http"],
    )
    assert (result["LIMIT"].current, result["LIMIT"].value_type) == ("3", "int")
    assert (result["ENABLED"].current, result["ENABLED"].value_type) == ("True", "bool")
    assert (result["TITLE"].current, result["TITLE"].value_type) == ("Тест", "str")
    assert contract.requests == [("GET", "/api/internal/config/contract_http", READ)]


@pytest.mark.parametrize(
    "key,value", [("RATE", "4.5"), ("LIMIT", "7"), ("ENABLED", "false"), ("TITLE", "Текст через HTTP")]
)
async def test_set_roundtrip_is_consumed_by_real_frontend(contract, key, value):
    api = contract.api()
    before = (await entries(api))[key]
    await api.set_value("contract_http", key, value)
    after = (await entries(api))[key]
    assert after.current == value
    assert after.default == before.default
    assert after.value_type == before.value_type
    assert after.is_modified
    assert contract.requests[-2] == ("PATCH", f"/api/internal/config/contract_http/{key}", WRITE)


async def test_reset_key_preserves_other_override(contract):
    api = contract.api()
    await api.set_value("contract_http", "RATE", "4.5")
    await api.set_value("contract_http", "LIMIT", "7")
    await api.reset_key("contract_http", "RATE")
    result = await entries(api)
    assert (result["RATE"].current, result["RATE"].is_modified) == ("1.5", False)
    assert (result["LIMIT"].current, result["LIMIT"].is_modified) == ("7", True)


async def test_reset_namespace_does_not_reset_another_namespace(contract):
    api = contract.api()
    await api.set_value("contract_other", "TITLE", "Сохранить")
    await api.set_value("contract_http", "RATE", "4.5")
    await api.set_value("contract_http", "ENABLED", "false")
    await api.reset_namespace("contract_http")
    assert all(not item.is_modified and item.current == item.default for item in (await entries(api)).values())
    assert (await entries(api, "contract_other"))["TITLE"].current == "Сохранить"


@pytest.mark.parametrize(
    "credentials",
    [
        {"operator_read_key": "", "operator_write_key": ""},
        {"operator_read_key": SERVICE, "operator_write_key": SERVICE},
        {"operator_read_key": "incorrect", "operator_write_key": "incorrect"},
    ],
)
@pytest.mark.parametrize("operation", ["read", "set", "reset_key", "reset_namespace"])
async def test_actual_auth_denies_before_storage(contract, credentials, operation):
    api = contract.api(**credentials)
    before = dict(contract.storage.data)
    calls = len(contract.storage.calls)
    with pytest.raises(httpx.HTTPStatusError) as error:
        await invoke(api, operation)
    assert error.value.response.status_code == 403
    assert len(contract.storage.calls) == calls
    assert contract.storage.data == before


async def invoke(api, operation):
    if operation == "read":
        return await api.list_namespace("contract_http")
    if operation == "set":
        return await api.set_value("contract_http", "RATE", "4.5")
    if operation == "reset_key":
        return await api.reset_key("contract_http", "RATE")
    return await api.reset_namespace("contract_http")


@pytest.mark.parametrize("write_key", ["", READ])
@pytest.mark.parametrize("operation", ["set", "reset_key", "reset_namespace"])
async def test_read_capability_reads_but_cannot_mutate_over_http(contract, write_key, operation):
    api = contract.api(operator_write_key=write_key)
    assert await entries(api)
    before = dict(contract.storage.data)
    calls = len(contract.storage.calls)
    with pytest.raises(httpx.HTTPStatusError) as error:
        await invoke(api, operation)
    assert error.value.response.status_code == 403
    assert len(contract.storage.calls) == calls
    assert contract.storage.data == before


async def test_write_only_capability_can_read_and_write(contract):
    api = contract.api(operator_read_key="")
    await api.set_value("contract_http", "RATE", "4.5")
    assert (await entries(api))["RATE"].current == "4.5"
    assert contract.requests[-1][2] == WRITE


@pytest.mark.parametrize("value", ["invalid", "-1", "11", {"incompatible": "object"}])
async def test_validation_failure_is_not_swallowed_or_written(contract, value):
    before = dict(contract.storage.data)
    with pytest.raises(httpx.HTTPStatusError) as error:
        await contract.api().set_value("contract_http", "LIMIT", value)
    assert error.value.response.status_code == 422
    assert contract.storage.data == before
    assert (await entries(contract.api()))["LIMIT"].current == "3"


@pytest.mark.parametrize("operation", ["read", "set", "reset_key", "reset_namespace"])
async def test_missing_namespace_returns_404_through_client(contract, operation):
    api = contract.api()
    with pytest.raises(httpx.HTTPStatusError) as error:
        if operation == "read":
            await api.list_namespace("missing")
        elif operation == "set":
            await api.set_value("missing", "RATE", "4.5")
        elif operation == "reset_key":
            await api.reset_key("missing", "RATE")
        else:
            await api.reset_namespace("missing")
    assert error.value.response.status_code == 404


@pytest.mark.parametrize("field", ["key", "namespace", "current", "default"])
async def test_incompatible_producer_required_field_is_detected(contract, monkeypatch, field):
    original = config_routes._entry_dict

    def incompatible(entry):
        payload = original(entry)
        payload[f"renamed_{field}"] = payload.pop(field)
        return payload

    monkeypatch.setattr(config_routes, "_entry_dict", incompatible)
    with pytest.raises(KeyError, match=field):
        await contract.api().list_namespace("contract_http")


@pytest.mark.parametrize("operation", ["set", "reset_key"])
async def test_unknown_key_does_not_change_storage(contract, operation):
    before = dict(contract.storage.data)
    with pytest.raises(httpx.HTTPStatusError) as error:
        if operation == "set":
            await contract.api().set_value("contract_http", "MISSING", "4.5")
        else:
            await contract.api().reset_key("contract_http", "MISSING")
    assert error.value.response.status_code == 404
    assert contract.storage.data == before


async def test_read_only_source_refuses_write_before_http_even_with_writer_capability(contract):
    api = contract.api(read_only=True)
    assert await entries(api)
    calls = len(contract.requests)
    before = dict(contract.storage.data)
    with pytest.raises(httpx.HTTPStatusError) as error:
        await api.set_value("contract_http", "RATE", "4.5")
    assert error.value.response.status_code == 403
    assert len(contract.requests) == calls
    assert contract.storage.data == before
