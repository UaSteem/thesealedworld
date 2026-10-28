from __future__ import annotations

import asyncio
import json
import math
from dataclasses import dataclass
from secrets import choice
from typing import Any, ClassVar
from urllib.parse import urlencode

import httpx
from fastapi import Request
from starlette.responses import RedirectResponse, Response

from fastapi_cabinet import CabinetAdmin, ListWidget, MetricWidget, SidebarItem, cabinet_site
from fastapi_cabinet.contracts.widgets import ListWidgetMap, MetricWidgetMap, TableColumnMap, TableWidgetMap
from fastapi_cabinet.rendering.layout_mapper import build_layout_map
from fastapi_cabinet.runtime import resolve_active_admin
from src.studio.integrations.backend_api.catalog_monsters import CatalogClan, CatalogMember, CatalogMonstersApi
from src.studio.settings import settings as studio_settings

_BASE = "/admin/content-ops"
_PREPARED_FAMILIES = frozenset({"goblin_tribe", "wolf_pack", "rat_swarm", "bandit_gang", "golem_foundry"})

_ATTRIBUTE_LABELS = {
    "strength": "Сила",
    "agility": "Ловкость",
    "endurance": "Выносливость",
    "intellect": "Интеллект",
    "memory": "Память",
    "mental": "Ментальность",
    "perception": "Восприятие",
    "projection": "Проекция",
    "prediction": "Предвидение",
}
_ROLE_LABELS = {"minion": "Миньон", "veteran": "Ветеран", "elite": "Элита", "boss": "Босс"}
_SLOT_LABELS = {
    "main_hand": "Правая рука",
    "off_hand": "Вторая рука",
    "two_hand": "Две руки",
    "chest_armor": "Броня",
    "amulet": "Амулет",
}


@dataclass(frozen=True)
class MonsterBrowserContext:
    clans: list[CatalogClan]
    family_options: list[str]
    tier_options: list[int]
    role_options: list[str]
    filters: dict[str, str]
    total_families: int
    total_clans: int
    total_members: int
    missing_images: int
    error: str = ""


def _api(request: Request) -> CatalogMonstersApi:
    source = request.state.source
    local_key = studio_settings.monster_catalog_read_key if source.kind == "local" else None
    return CatalogMonstersApi(
        client=request.app.state.backend_http_client,
        base_url=source.api_base,
        internal_service_key=local_key or None,
    )


async def _overview_provider(request: Request) -> ListWidgetMap:
    return ListWidgetMap(
        key="content_ops_overview",
        title="Инспекция контента",
        items=[
            "Готовый Python-каталог: семьи, кланы, типы бойцов и изображения.",
            "Просмотр определений; каталог и выбранный источник не изменяются.",
        ],
    )


async def _monster_count_provider(request: Request) -> MetricWidgetMap:
    try:
        summary = await _api(request).get_summary()
    except (AttributeError, httpx.HTTPStatusError, httpx.RequestError):
        return MetricWidgetMap(
            key="content_ops_monsters", title="Каталог монстров", value="—", subtitle="backend недоступен"
        )
    return MetricWidgetMap(
        key="content_ops_monsters",
        title="Каталог монстров",
        value=str(summary.clans),
        subtitle=f"семей {summary.families} / бойцов {summary.members} / без изображения {summary.missing_images}",
    )


def _filter_monster_clans(clans: list[CatalogClan], filters: dict[str, str]) -> list[CatalogClan]:
    result = []
    for clan in clans:
        if filters.get("family_id") and clan.family_id != filters["family_id"]:
            continue
        members = clan.members
        if filters.get("role"):
            members = [member for member in members if member.role == filters["role"]]
        tier = filters.get("tier", "")
        if tier:
            try:
                value = int(tier)
            except ValueError:
                continue
            members = [member for member in members if member.min_tier <= value <= member.max_tier]
        if filters.get("missing_image"):
            members = [member for member in members if not member.image or not member.image.image_url]
        if not members and any(filters.get(key) for key in ("role", "tier", "missing_image")):
            continue
        result.append(
            clan.model_copy(
                update={
                    "members": members,
                    "member_count": len(members),
                    "missing_images": sum(not member.image or not member.image.image_url for member in members),
                }
            )
        )
    return result


async def _load_monster_browser_context(request: Request) -> MonsterBrowserContext:
    params = request.query_params
    filters = {key: (params.get(key) or "").strip() for key in ("family_id", "tier", "role")}
    filters["missing_image"] = "1" if params.get("missing_image") == "1" else ""
    try:
        source = await _api(request).list_all()
    except (AttributeError, ValueError, httpx.HTTPStatusError, httpx.RequestError) as exc:
        return MonsterBrowserContext(
            [], [], [], [], filters, 0, 0, 0, 0, f"backend недоступен: {exc.__class__.__name__}"
        )
    clans = _filter_monster_clans(source, filters)
    return MonsterBrowserContext(
        clans=clans,
        family_options=sorted({clan.family_id for clan in source}),
        tier_options=sorted(
            {tier for clan in source for member in clan.members for tier in range(member.min_tier, member.max_tier + 1)}
        ),
        role_options=sorted({member.role for clan in source for member in clan.members}),
        filters=filters,
        total_families=len({clan.family_id for clan in clans}),
        total_clans=len(clans),
        total_members=sum(len(clan.members) for clan in clans),
        missing_images=sum(clan.missing_images for clan in clans),
    )


async def _monster_table_provider(request: Request) -> TableWidgetMap:
    browser = await _load_monster_browser_context(request)
    return TableWidgetMap(
        key="content_ops_monster_families",
        title="Кланы готового каталога",
        columns=[
            TableColumnMap(key="name", label="Клан"),
            TableColumnMap(key="family", label="Семья"),
            TableColumnMap(key="members", label="Типы бойцов"),
            TableColumnMap(key="missing", label="Без изображения"),
        ],
        rows=[
            {
                "name": clan.name,
                "family": clan.family_name,
                "members": clan.member_count,
                "missing": clan.missing_images,
                "href": f"{_BASE}/monster-detail?id={clan.clan_id}",
            }
            for clan in browser.clans
        ],
        row_href_key="href",
    )


async def _encounter_profile_matrix(
    api: CatalogMonstersApi, *, family_id: str, location_tier: int, seed: int, reference_gs: float
) -> list[dict[str, Any]]:
    """Compare built-in profiles through the read-only consumer API only."""
    if not math.isfinite(reference_gs) or reference_gs <= 0:
        raise ValueError("Backend did not provide a valid tier reference GS")
    semaphore = asyncio.Semaphore(4)

    async def row(encounter_type: str, difficulty: str) -> dict[str, Any]:
        async with semaphore:
            item: dict[str, Any] = {"encounter_type": encounter_type, "difficulty": difficulty}
            order = {
                "encounter_type": encounter_type,
                "difficulty": difficulty,
                "party_mode": "solo",
                "family_ids": [family_id],
                "location_tier": location_tier,
                "seed": seed,
                "player_gear_score": reference_gs,
            }
            try:
                base = await api.select_encounter(order)
                item["base"] = base
                configs = base.preparation.configurations
                profile = base.preparation.profile or {}
                config = configs[0] if configs else None
                pools = {}
                cap_scores = []
                for pool_name in ("minions", "seniors"):
                    pool = getattr(config, pool_name) if config is not None else profile[pool_name]

                    def value(key: str, pool: Any = pool) -> Any:
                        return getattr(pool, key) if config is not None else pool[key]

                    mode = getattr(pool, "mode", "fixed") if config is not None else pool.get("mode", "fixed")
                    threshold = value("gs_threshold")
                    step_size = value("gs_step_size")
                    points = value("gs_points_per_step")
                    bonus_max = value("gs_bonus_max")
                    reference = value("reference_gs") if mode == "relative_gs" else None
                    if mode == "relative_gs":
                        cap_gs = math.nextafter(
                            reference * (value("base_points") + bonus_max) / value("base_points"), math.inf
                        )
                    else:
                        cap_gs = threshold + step_size * math.ceil(bonus_max / points) if points else threshold
                    pools[pool_name] = dict(
                        mode=mode,
                        reference_gs=reference,
                        threshold=threshold,
                        step_size=step_size,
                        points=points,
                        bonus_max=bonus_max,
                        cap_gs=cap_gs,
                    )
                    cap_scores.append(cap_gs)
                cap_gs = max(cap_scores)
                item.update(pools=pools, cap_gs=cap_gs)
                item["cap"] = await api.select_encounter({**order, "player_gear_score": cap_gs})
            except (httpx.HTTPError, ValueError, AttributeError, KeyError, ZeroDivisionError):
                item["error"] = "Сравнение недоступно: профиль или выбранный backend не предоставил данные."
            return item

    return list(
        await asyncio.gather(
            *(
                row(kind, difficulty)
                for kind in ("ordinary", "patrol", "guard", "leader")
                for difficulty in ("easy", "normal", "hard")
            )
        )
    )


class ContentOpsAdmin(CabinetAdmin):
    key = "content_ops"
    label = "Монстры"
    group = "content_ops"
    group_label = "Контент"
    path = _BASE
    order = 10
    sidebar: ClassVar = (
        SidebarItem(key="overview", label="Обзор", path=_BASE, order=10),
        SidebarItem(key="monsters", label="Каталог монстров", path=f"{_BASE}/monster-browser", order=20),
        SidebarItem(key="encounter", label="Проверка заказа", path=f"{_BASE}/monster-encounter", order=30),
    )
    dashboard_widgets: ClassVar = (
        MetricWidget(key="content_ops_monsters", title="Каталог монстров", provider="content_ops.monster_count"),
        ListWidget(key="content_ops_overview", title="Инспекция контента", provider="content_ops.overview", order=20),
    )
    sub_pages: ClassVar[dict[str, Any]] = {}
    action_routes: ClassVar = {
        "monster-browser": ("GET", "handle_monster_browser"),
        "monster-encounter": ("GET", "handle_monster_encounter"),
        "monster-detail": ("GET", "handle_monster_detail"),
        "monster-member-detail": ("GET", "handle_monster_member_detail"),
        "monster-random": ("GET", "handle_monster_random"),
    }
    providers: ClassVar = {
        "content_ops.overview": _overview_provider,
        "content_ops.monster_count": _monster_count_provider,
        "content_ops.monster_table": _monster_table_provider,
    }

    async def get_dashboard_context(self, request: Request) -> dict[str, Any]:
        browser = await _load_monster_browser_context(request)
        return {
            "sections": [
                {
                    "label": "Каталог монстров",
                    "href": f"{_BASE}/monster-browser",
                    "status": "готово" if not browser.error else "недоступно",
                    "detail": f"{browser.total_families} семей / {browser.total_clans} кланов / {browser.total_members} типов бойцов",
                }
            ]
        }

    async def handle_monster_encounter(self, request: Request) -> Response:
        params = request.query_params
        fields = {
            "encounter_type": params.get("encounter_type", "ordinary"),
            "difficulty": params.get("difficulty", "normal"),
            "party_mode": params.get("party_mode", "solo"),
            "player_gear_score": params.get("player_gear_score", ""),
            "location_tier": params.get("location_tier", "0"),
            "seed": params.get("seed", "1"),
            "profile_source": params.get("profile_source", "builtin"),
            "profile_override": params.get("profile_override", ""),
        }
        families = params.getlist("family_ids")
        contract, preview, result, order_json, error = None, None, None, "", ""
        profile_matrix = []
        try:
            api = _api(request)
            contract = await api.get_encounter_contract()
            if not params.get("run") and not families and contract.families:
                families = [contract.families[0].id]
            if not fields["profile_override"]:
                fields["profile_override"] = json.dumps(contract.profile_override_example, ensure_ascii=False, indent=2)
            if params.get("compare_profiles") == "1":
                if len(families) != 1:
                    raise ValueError("Choose exactly one family")
                profile_matrix = await _encounter_profile_matrix(
                    api,
                    family_id=families[0],
                    location_tier=int(fields["location_tier"]),
                    seed=int(fields["seed"]),
                    reference_gs=float(contract.reference_player_gs_by_tier.get(int(fields["location_tier"]), "nan")),
                )
            if params.get("run"):
                if len(families) != 1:
                    raise ValueError("Choose exactly one family")
                order = {
                    "encounter_type": fields["encounter_type"],
                    "difficulty": fields["difficulty"],
                    "party_mode": fields["party_mode"],
                    "location_tier": int(fields["location_tier"]),
                    "family_ids": families,
                    "seed": int(fields["seed"]),
                }
                if fields["player_gear_score"].strip():
                    gear_score = float(fields["player_gear_score"])
                    if not math.isfinite(gear_score) or gear_score < 0:
                        raise ValueError("invalid gear score")
                    order["player_gear_score"] = gear_score
                if fields["profile_source"] == "external":
                    override = json.loads(fields["profile_override"])
                    if not isinstance(override, dict):
                        raise ValueError("Profile must be a JSON object")
                    order["profile_override"] = override
                elif fields["profile_source"] != "builtin":
                    raise ValueError("Unknown profile source")
                order_json = json.dumps(order, ensure_ascii=False, indent=2)
                result = await api.select_encounter(order)
                preview = result.preparation
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 422:
                error = "Заказ отклонён проверкой контракта. Проверьте тир, сложность, режим, GS и внешний профиль."
            else:
                error = "Проверка недоступна. Проверьте доступ к выбранному backend."
        except httpx.RequestError:
            error = "Backend выбранного источника недоступен."
        except (ValueError, AttributeError):
            error = "Не удалось прочитать контракт или запрос: выберите ровно одну семью; тир и seed — целые числа, GS — конечное неотрицательное число, внешний профиль — JSON-объект."
        return _render_custom(
            self,
            request,
            "cabinet/content_ops_monster_encounter.html",
            {
                "profile_matrix": profile_matrix,
                "contract": contract,
                "preview": preview,
                "result": result,
                "fields": fields,
                "selected_families": families,
                "order_json": order_json,
                "error": error,
                "base_url": _BASE,
            },
        )

    async def handle_monster_browser(self, request: Request) -> Response:
        return _render_custom(
            self,
            request,
            "cabinet/content_ops_monsters.html",
            {"browser": await _load_monster_browser_context(request), "base_url": _BASE},
        )

    async def handle_monster_detail(self, request: Request) -> Response:
        clan, error = await _load_clan(request, request.query_params.get("id", ""))
        return _render_custom(self, request, "cabinet/content_ops_monster_detail.html", {"clan": clan, "error": error})

    async def handle_monster_member_detail(self, request: Request) -> Response:
        clan, error = await _load_clan(request, request.query_params.get("clan_id", ""))
        member = _find_member(clan, request.query_params.get("member_id", ""))
        equipment, equipment_error = None, ""
        tier = member.min_tier if member else 0
        if member:
            try:
                tier = int(request.query_params.get("tier", str(tier)))
                if not member.min_tier <= tier <= member.max_tier:
                    raise ValueError
            except ValueError:
                tier = member.min_tier
                equipment_error = "Недоступный тир. Показан минимальный доступный тир."
            if member.family_id in _PREPARED_FAMILIES:
                try:
                    player_attributes = None
                    if any(f"player_{key}" in request.query_params for key in _ATTRIBUTE_LABELS):
                        player_attributes = {
                            key: int(request.query_params[f"player_{key}"]) for key in _ATTRIBUTE_LABELS
                        }
                        if any(not 1 <= value <= 500 for value in player_attributes.values()):
                            raise ValueError("Invalid test attributes")
                    equipment = await _api(request).get_equipment(
                        member.member_id,
                        tier,
                        player_attributes=player_attributes,
                    )
                except (ValueError, KeyError):
                    equipment_error = "Для тестового игрока нужны все девять характеристик: целые числа от 1 до 500."
                except (httpx.HTTPStatusError, httpx.RequestError):
                    equipment_error = "Комплект недоступен. Проверьте выбранный источник и доступность backend."
        return _render_custom(
            self,
            request,
            "cabinet/content_ops_monster_member_detail.html",
            {
                "clan": clan,
                "member": member,
                "error": error,
                "attribute_labels": _ATTRIBUTE_LABELS,
                "slot_labels": _SLOT_LABELS,
                "equipment": equipment,
                "equipment_error": equipment_error,
                "selected_tier": tier,
            },
        )

    async def handle_monster_random(self, request: Request) -> Response:
        browser = await _load_monster_browser_context(request)
        clan_id = request.query_params.get("clan_id")
        members = [
            member
            for clan in browser.clans
            for member in clan.members
            if member.family_id in _PREPARED_FAMILIES and (not clan_id or member.clan_id == clan_id)
        ]
        if not members:
            return _render_custom(
                self,
                request,
                "cabinet/content_ops_monster_detail.html",
                {
                    "clan": None,
                    "error": browser.error or "Нет монстров с готовыми комплектами для просмотра.",
                },
            )
        member = choice(members)
        tier = choice(list(range(member.min_tier, member.max_tier + 1)))
        return RedirectResponse(
            f"{_BASE}/monster-member-detail?"
            + urlencode(
                {
                    "clan_id": member.clan_id,
                    "member_id": member.member_id,
                    "tier": tier,
                }
            ),
            status_code=303,
        )


async def _load_clan(request: Request, clan_id: str) -> tuple[CatalogClan | None, str]:
    if not clan_id:
        return None, ""
    try:
        return await _api(request).get_clan(clan_id), ""
    except (AttributeError, httpx.HTTPStatusError, httpx.RequestError) as exc:
        return None, f"backend недоступен: {exc.__class__.__name__}"


def _find_member(clan: CatalogClan | None, member_id: str) -> CatalogMember | None:
    return next((member for member in clan.members if member.member_id == member_id), None) if clan else None


def _render_custom(admin: Any, request: Request, template: str, context: dict[str, Any]) -> Response:
    active_path = str(request.url.path)
    layout = build_layout_map(
        cabinet_site.registry,
        mount_path="/admin",
        active_admin=resolve_active_admin(active_path, cabinet_site.registry, "/admin"),
        static_mount_path=cabinet_site.static_mount_path,
        active_path=active_path,
        title=admin.label,
    )
    return cabinet_site.templates.TemplateResponse(
        request,
        template,
        {
            "layout": layout,
            "module": admin,
            "module_context": {},
            "widgets": [],
            "role_labels": _ROLE_LABELS,
            **context,
        },
    )


cabinet_site.register(ContentOpsAdmin)
