from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.backend.config.settings import settings
from src.backend.core.database import get_db
from src.backend.features.monsters.api.router import router


def test_bootstrap_content_cache_and_no_database(monkeypatch):
    monkeypatch.setattr(settings, "monster_catalog_read_key", "test-bootstrap-secret")
    app = FastAPI()
    app.include_router(router)

    def no_database():
        raise AssertionError("Bootstrap must not access database")

    app.dependency_overrides[get_db] = no_database
    with TestClient(app) as client:
        assert client.get("/api/admin/monsters/catalog/bootstrap").status_code == 403
        headers = {"X-Internal-Service-Key": "test-bootstrap-secret"}
        response = client.get("/api/admin/monsters/catalog/bootstrap", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["families"]) == 4
        assert len(data["members"]) == 47
        assert data["members"]["wolf_pack.base.alpha_prime"]["name"] == "Фенрир"
        assert "description" in data["members"]["wolf_pack.base.alpha_prime"]
        assert "source_path" not in response.text
        assert "base_stats" not in response.text
        assert data["version"] == data["manifest"]["version"]
        assert response.headers["etag"]
        cached = client.get("/api/admin/monsters/catalog/bootstrap", headers={**headers, "If-None-Match": response.headers["etag"]})
        assert cached.status_code == 304 and not cached.content
        assert client.get("/api/admin/monsters/catalog/bootstrap?include_system=true", headers=headers).json()["members"].keys() > data["members"].keys()


def test_bootstrap_version_tracks_content_and_is_stable():
    from dataclasses import replace

    from src.backend.features.monsters.catalog.bootstrap import MonsterCatalogBootstrapService
    from src.backend.features.monsters.catalog.indexes import MonsterCatalog
    from src.backend.features.monsters.catalog.registry import get_catalog

    catalog = get_catalog()
    initial = MonsterCatalogBootstrapService(catalog).build()
    assert initial == MonsterCatalogBootstrapService(catalog).build()
    target = catalog.members["wolf_pack.base.alpha_prime"]
    changed = replace(target, text_id=None, description="Updated client description")
    other = MonsterCatalog(catalog.families, catalog.clans, {**catalog.members, target.id: changed})
    updated = MonsterCatalogBootstrapService(other).build()
    assert updated.version != initial.version
    assert updated.manifest.sections["members"] != initial.manifest.sections["members"]
    assert updated.manifest.sections["families"] == initial.manifest.sections["families"]
    initial.members.clear()
    assert MonsterCatalogBootstrapService(catalog).build().members
