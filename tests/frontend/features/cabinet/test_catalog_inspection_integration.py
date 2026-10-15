from pathlib import Path
from types import SimpleNamespace

import httpx
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from fastapi_cabinet import include_cabinet
from src.backend.config.settings import settings as backend_settings
from src.backend.core.database import get_db
from src.backend.features.monsters.api.router import router
from src.studio.settings import settings as studio_settings


async def test_studio_reads_real_catalog_api_and_local_images_without_database(monkeypatch):
    monkeypatch.setattr(backend_settings, "monster_catalog_read_key", "test-catalog-only-secret")
    monkeypatch.setattr(studio_settings, "monster_catalog_read_key", "test-catalog-only-secret")
    backend = FastAPI()
    backend.include_router(router)

    def forbidden_database():
        raise AssertionError("Studio catalogue must never read generated monster rows")

    backend.dependency_overrides[get_db] = forbidden_database
    requests = []

    async def record(request):
        requests.append((request.method, request.url.path))

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=backend), event_hooks={"request": [record]}) as upstream:
        studio = FastAPI()
        studio.state.backend_http_client = upstream

        @studio.middleware("http")
        async def source(request, call_next):
            request.state.source = SimpleNamespace(kind="local", api_base="http://catalog.test")
            return await call_next(request)

        include_cabinet(studio, modules=("src.studio.features.cabinet.modules.content_ops.cabinet",), mount_path="/admin")
        studio.mount("/static", StaticFiles(directory="src/frontend/static"))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=studio), base_url="http://studio.test") as browser:
            overview = await browser.get("/admin/content-ops")
            listing = await browser.get("/admin/content-ops/monster-browser")
            clan = await browser.get("/admin/content-ops/monster-detail?id=goblin_tribe.base")
            member = await browser.get(
                "/admin/content-ops/monster-member-detail?clan_id=goblin_tribe.base&member_id=goblin_tribe.base.goblin_sneak"
            )
            assert all(response.status_code == 200 for response in (overview, listing, clan, member))
            assert "Гоблины" in listing.text and "Базовые характеристики" in member.text
            assert "goblin_tribe.base" in clan.text
            wolf = await browser.get(
                "/admin/content-ops/monster-member-detail?clan_id=wolf_pack.base&member_id=wolf_pack.base.pack_huntmaster"
            )
            assert wolf.status_code == 200
            assert "Общая основа" in wolf.text
            assert "Способности варианта" in wolf.text
            assert "Отдельные способности в каталоге пока не заданы." in wolf.text
            image = await browser.get("/static/images/monsters/catalog/goblin_tribe.goblin_sneak.png")
            assert image.status_code == 200
            assert image.content == Path(
                "assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_sneak-face-v1.png"
            ).read_bytes()
    assert requests
    assert all(method == "GET" and path in {
        "/api/admin/monsters/catalog", "/api/admin/monsters/catalog/summary",
    } for method, path in requests)
