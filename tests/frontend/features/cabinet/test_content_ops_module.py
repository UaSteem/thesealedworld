from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.studio.features.cabinet.modules.content_ops.cabinet as content_ops
from fastapi_cabinet import include_cabinet
from src.studio.integrations.backend_api.catalog_monsters import CatalogClan, CatalogMonstersApi

MODULES = ("src.studio.features.cabinet.modules.content_ops.cabinet",)


def clan_payload(index=0):
    return {
        "clan_id": f"base-{index}",
        "family_id": "goblins",
        "family_name": "Гоблины",
        "name": "Обычные гоблины",
        "description": "Готовый клан",
        "tags": ["forest"],
        "features": [],
        "normal_spawn": True,
        "member_count": 2,
        "missing_images": 1,
        "members": [
            {
                "member_id": f"scout-{index}",
                "clan_id": f"base-{index}",
                "family_id": "goblins",
                "variant_id": "scout",
                "name": "Разведчик",
                "description": "Хитрый разведчик",
                "role": "minion",
                "tags": [],
                "min_tier": 0,
                "max_tier": 7,
                "base_stats": {"strength": 10},
                "skills": ["skill_swords"],
                "fixed_loadout": {"main_hand": "hatchet"},
                "member_model": None,
                "image": {
                    "asset_id": "scout",
                    "image_url": "/static/images/monsters/catalog/scout.png",
                    "review_status": "accepted",
                    "display_mirror": True,
                },
            },
            {
                "member_id": f"boss-{index}",
                "clan_id": f"base-{index}",
                "family_id": "goblins",
                "variant_id": "boss",
                "name": "Главарь",
                "role": "boss",
                "min_tier": 4,
                "max_tier": 7,
            },
        ],
    }


class FakeApi:
    async def list_all(self):
        return [CatalogClan.model_validate(clan_payload())]

    async def get_clan(self, clan_id):
        return CatalogClan.model_validate(clan_payload()) if clan_id == "base-0" else None

    async def get_summary(self):
        return SimpleNamespace(families=5, clans=5, members=52, missing_images=6)


def test_member_filters_use_tier_window_and_count_missing_members():
    clan = CatalogClan.model_validate(clan_payload())
    filtered = content_ops._filter_monster_clans([clan], {"tier": "3", "role": "minion"})
    assert filtered[0].member_count == 1
    assert filtered[0].missing_images == 0
    missing = content_ops._filter_monster_clans([clan], {"missing_image": "1"})
    assert [member.member_id for member in missing[0].members] == ["boss-0"]
    assert clan.member_count == 2  # Filtering must not mutate shared definitions.


@pytest.mark.asyncio
async def test_summary_and_browser_use_authored_contract(monkeypatch):
    monkeypatch.setattr(content_ops, "_api", lambda request: FakeApi())
    browser = await content_ops._load_monster_browser_context(SimpleNamespace(query_params={}))
    assert (browser.total_families, browser.total_clans, browser.total_members, browser.missing_images) == (1, 1, 2, 1)
    assert browser.tier_options == list(range(8))
    metric = await content_ops._monster_count_provider(SimpleNamespace())
    assert metric.value == "5"
    assert "бойцов 52" in metric.subtitle


@pytest.mark.parametrize("source", ["local", "prod"])
def test_pages_render_catalog_and_never_call_writes_or_generation(monkeypatch, source):
    monkeypatch.setattr(content_ops, "_api", lambda request: FakeApi())
    app = FastAPI()
    include_cabinet(app, modules=MODULES, mount_path="/admin")
    with TestClient(app) as client:
        client.cookies.set("studio_source", source)
        browser = client.get("/admin/content-ops/monster-browser")
        assert "Каталог монстров" in browser.text
        assert "Гоблины" in browser.text
        detail = client.get("/admin/content-ops/monster-detail?id=base-0&ai_task_ids=obsolete&ai_kind=member_image")
        assert "Готовый клан" in detail.text
        assert "/static/images/monsters/catalog/scout.png" in detail.text
        assert "нет изображения" in detail.text
        assert "AI-задача" not in detail.text
        member = client.get("/admin/content-ops/monster-member-detail?clan_id=base-0&member_id=scout-0")
        assert "Базовые характеристики" in member.text
        assert "Сила" in member.text
        assert "scaleX(-1)" in member.text
        assert "accepted" in member.text
        assert "Фиксированное снаряжение" in member.text
        assert "hatchet" in member.text
        assert "Gear score" not in member.text
        for action in ["monster-rebuild-plan", "monster-rebuild-apply", "regenerate-member-image"]:
            assert client.post(f"/admin/content-ops/{action}").status_code in (404, 405)
        assert client.get("/admin/content-ops/monster-detail?id=missing").status_code == 200
    assert all(method == "GET" for method, _ in content_ops.ContentOpsAdmin.action_routes.values())


@pytest.mark.asyncio
async def test_catalog_client_paginates_using_selected_backend_and_service_headers():
    calls = []

    def handler(request):
        calls.append(request)
        assert request.method == "GET"
        assert request.url.host == "selected-backend"
        assert request.headers["X-Service-Key"] == "inspection-secret"
        assert request.url.path == "/api/admin/monsters/catalog"
        offset = int(request.url.params["offset"])
        total = 103
        items = [clan_payload(index) for index in range(offset, min(offset + 100, total))]
        return httpx.Response(
            200,
            json={
                "items": items,
                "pagination": {"limit": 100, "offset": offset, "total": total, "has_more": offset + len(items) < total},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        api = CatalogMonstersApi(
            client,
            "http://selected-backend",
            internal_service_key="inspection-secret",
            internal_service_header="X-Service-Key",
        )
        clans = await api.list_all()
    assert len(clans) == 103
    assert [request.url.params["offset"] for request in calls] == ["0", "100"]


@pytest.mark.asyncio
async def test_browser_backend_unavailable_returns_inspection_error(monkeypatch):
    class Unavailable:
        async def list_all(self):
            raise httpx.ConnectError("unavailable")

    monkeypatch.setattr(content_ops, "_api", lambda request: Unavailable())
    browser = await content_ops._load_monster_browser_context(SimpleNamespace(query_params={}))
    assert browser.error.startswith("backend недоступен")
    assert browser.total_members == 0
