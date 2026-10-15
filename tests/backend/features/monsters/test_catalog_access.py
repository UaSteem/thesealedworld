import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.backend.config.settings import settings
from src.backend.core.database import get_db
from src.backend.features.monsters.api.router import router


@pytest.mark.parametrize("method,path", [
    ("GET", "/generated"), ("GET", "/generated/summary"),
    ("POST", "/generated/rebuild/plan"), ("POST", "/generated/rebuild/apply"),
])
@pytest.mark.parametrize("key", [None, "wrong-key"])
def test_catalog_denies_before_database(monkeypatch, method, path, key):
    monkeypatch.setattr(settings, "frontend_internal_service_key", "test-read-secret")
    app = FastAPI()
    app.include_router(router)

    def forbidden_database():
        raise AssertionError("Rejected request must not reach database")

    app.dependency_overrides[get_db] = forbidden_database
    headers = {"X-Internal-Service-Key": key} if key else {}
    response = TestClient(app).request(method, "/api/admin/monsters" + path, headers=headers, json={})
    assert response.status_code == 403


@pytest.mark.parametrize("configured,presented", [
    ("test-write-secret", None),
    ("test-write-secret", "wrong-key"),
    ("", "anything"),
    ("change-me-write-key", "change-me-write-key"),
    ("test-read-secret", "test-read-secret"),
])
def test_read_identity_cannot_apply_without_separate_write_permission(monkeypatch, configured, presented):
    monkeypatch.setattr(settings, "frontend_internal_service_key", "test-read-secret")
    monkeypatch.setattr(settings, "monster_catalog_write_key", configured)
    app = FastAPI()
    app.include_router(router)

    def forbidden_database():
        raise AssertionError("Write rejection must happen before database")

    app.dependency_overrides[get_db] = forbidden_database
    headers = {"X-Internal-Service-Key": "test-read-secret"}
    if presented:
        headers["X-Monster-Catalog-Write-Key"] = presented
    response = TestClient(app).post("/api/admin/monsters/generated/rebuild/apply", headers=headers, json={})
    assert response.status_code == 403


@pytest.mark.parametrize("configured", ["", "change-me-service-key", "dev-site-to-game-service-key"])
def test_catalog_rejects_unconfigured_or_public_default_service_keys(monkeypatch, configured):
    monkeypatch.setattr(settings, "frontend_internal_service_key", configured)
    monkeypatch.setattr(settings, "site_to_game_service_key", configured)
    app = FastAPI()
    app.include_router(router)

    def forbidden_database():
        raise AssertionError("Default credentials must not reach database")

    app.dependency_overrides[get_db] = forbidden_database
    response = TestClient(app).get("/api/admin/monsters/generated/summary", headers={"X-Internal-Service-Key": configured})
    assert response.status_code == 403


async def test_studio_client_can_inspect_with_read_credentials_only(monkeypatch):
    import httpx

    from src.backend.features.monsters.api.router import get_generated_monster_view_service
    from src.studio.integrations.backend_api.admin_monsters import AdminMonstersApi

    monkeypatch.setattr(settings, "frontend_internal_service_key", "test-read-secret")

    class FakeView:
        async def summary(self, *, family_id=None):
            return {"clans": 4, "members": 48, "missing_images": 2}

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_generated_monster_view_service] = lambda: FakeView()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app)) as client:
        api = AdminMonstersApi(client=client, base_url="http://local.test", internal_service_key="test-read-secret")
        summary = await api.get_generated_summary()
    assert summary.clans == 4
    assert summary.members == 48
    assert summary.missing_images == 2


def test_catalog_scoped_read_key_cannot_apply_or_be_reused_for_write(monkeypatch):
    monkeypatch.setattr(settings, "frontend_internal_service_key", "dev-site-to-game-service-key")
    monkeypatch.setattr(settings, "monster_catalog_read_key", "test-catalog-read-secret")
    monkeypatch.setattr(settings, "monster_catalog_write_key", "test-catalog-read-secret")
    app = FastAPI()
    app.include_router(router)

    def forbidden_database():
        raise AssertionError("Read-only identity must not reach write DB")

    app.dependency_overrides[get_db] = forbidden_database
    client = TestClient(app, headers={"X-Internal-Service-Key": "test-catalog-read-secret"})
    assert client.get("/api/admin/monsters/catalog/summary").status_code == 200
    assert client.post("/api/admin/monsters/generated/rebuild/apply", json={}, headers={
        "X-Monster-Catalog-Write-Key": "test-catalog-read-secret",
    }).status_code == 403
