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
            assert "Набор снаряжения" in member.text
            assert "Набор основы" in member.text
            assert "Комплект по тиру" in member.text
            assert member.text.count('<article class="item-card">') > 4
            assert 'aria-label="Сравнение игрока и монстра"' in member.text
            assert "Настроить характеристики тестового игрока" in member.text
            assert "Точность основной руки" in member.text
            assert '<details class="item-card__technical">' in member.text
            assert 'aria-label="Итоговые характеристики монстра"' in member.text
            assert "Характеристики бойца" in member.text
            assert "Без вещей" in member.text and "Итог" in member.text
            assert "knife" in member.text
            tier_five = await browser.get(
                "/admin/content-ops/monster-member-detail?clan_id=goblin_tribe.base"
                "&member_id=goblin_tribe.base.goblin_sneak&tier=5"
            )
            assert tier_five.status_code == 200
            assert 'value="5" selected' in tier_five.text
            assert "thorium" in tier_five.text
            attributes = {
                "strength": 30, "agility": 40, "endurance": 35, "intellect": 12,
                "memory": 13, "mental": 14, "perception": 25, "projection": 15, "prediction": 16,
            }
            custom = await browser.get(
                "/admin/content-ops/monster-member-detail",
                params={"clan_id": "goblin_tribe.base", "member_id": "goblin_tribe.base.goblin_sneak",
                        "tier": 5, **{f"player_{key}": value for key, value in attributes.items()}},
            )
            assert custom.status_code == 200
            assert 'name="player_strength" value="30"' in custom.text
            random_member = await browser.get("/admin/content-ops/monster-random")
            assert random_member.status_code == 303
            assert any(f"member_id={family}.base." in random_member.headers["location"]
                       for family in ("goblin_tribe", "wolf_pack", "rat_swarm", "bandit_gang"))
            assert "tier=" in random_member.headers["location"]
            wolf = await browser.get(
                "/admin/content-ops/monster-member-detail?clan_id=wolf_pack.base&member_id=wolf_pack.base.pack_huntmaster"
            )
            assert wolf.status_code == 200
            assert "Общая основа" in wolf.text
            assert "Комплект недоступен" not in wolf.text
            assert 'aria-label="Итоговые характеристики монстра"' in wolf.text
            assert '<article class="item-card">' in wolf.text
            assert "Сравнение с тем же монстром без снаряжения" in wolf.text
            assert "Случайный гоблин и тир" not in wolf.text
            wolf_five = await browser.get(
                "/admin/content-ops/monster-member-detail?clan_id=wolf_pack.base"
                "&member_id=wolf_pack.base.cub&tier=5"
            )
            assert wolf_five.status_code == 200
            assert 'value="5" selected' in wolf_five.text
            assert "Молодые волчьи клыки" in wolf_five.text
            assert "Короткие острые клыки" in wolf_five.text
            assert "Способности варианта" in wolf.text
            assert "Отдельные способности в каталоге пока не заданы." in wolf.text
            for clan_id, member_id, expected in (
                ("rat_swarm.base", "screecher", "Ядовитый плевок крысы"),
                ("bandit_gang.base", "bandit_cutthroat", "Комплект по тиру"),
            ):
                remaining = await browser.get(
                    "/admin/content-ops/monster-member-detail",
                    params={"clan_id": clan_id, "member_id": f"{clan_id}.{member_id}", "tier": 5},
                )
                assert remaining.status_code == 200
                assert expected in remaining.text
                assert "Комплект недоступен" not in remaining.text
                assert 'value="5" selected' in remaining.text
                assert 'aria-label="Итоговые характеристики монстра"' in remaining.text
                assert '<article class="item-card">' in remaining.text
                assert "Случайный боец и тир" in remaining.text
                random_family = await browser.get("/admin/content-ops/monster-random", params={"clan_id": clan_id})
                assert random_family.status_code == 303
                assert f"member_id={clan_id}." in random_family.headers["location"]
                assert f'value="{clan_id}.{member_id}" selected' in remaining.text
            image = await browser.get("/static/images/monsters/catalog/goblin_tribe.goblin_sneak.png")
            assert image.status_code == 200
            assert image.content == Path(
                "assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_sneak-face-v1.png"
            ).read_bytes()
    assert requests
    assert all(method == "GET" and path in {
        "/api/admin/monsters/catalog", "/api/admin/monsters/catalog/summary",
        "/api/admin/monsters/catalog/equipment",
    } for method, path in requests)
