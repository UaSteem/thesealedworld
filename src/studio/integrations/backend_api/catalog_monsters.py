"""Read-only client for authored monster definitions (not persisted instances)."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.frontend.core.api import BaseApiClient
from src.frontend.integrations.backend_api.item_presentation import (
    ItemCard,  # noqa: TC001 - Pydantic resolves field models
)


class CatalogImage(BaseModel):
    asset_id: str
    image_url: str | None = None
    source_path: str | None = None
    review_status: str = ""
    display_mirror: bool = False


class CatalogMember(BaseModel):
    member_id: str
    clan_id: str
    family_id: str
    variant_id: str
    name: str
    text_locale: str = "ru"
    text_fallback: bool = False
    description: str = ""
    role: str
    tags: list[str] = Field(default_factory=list)
    min_tier: int
    max_tier: int
    base_stats: dict[str, int] = Field(default_factory=dict)
    skills: list[str] = Field(default_factory=list)
    ability_ids: list[str] = Field(default_factory=list)
    base_id: str | None = None
    image_source: str | None = None
    equipment_set_id: str | None = None
    equipment_source: str | None = None
    fixed_loadout: dict[str, str | None] = Field(default_factory=dict)
    member_model: dict[str, Any] | None = None
    image: CatalogImage | None = None


class CatalogClan(BaseModel):
    clan_id: str
    family_id: str
    family_name: str
    name: str
    text_locale: str = "ru"
    text_fallback: bool = False
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    normal_spawn: bool
    members: list[CatalogMember] = Field(default_factory=list)
    member_count: int
    missing_images: int


class CatalogSummary(BaseModel):
    families: int = 0
    clans: int = 0
    members: int = 0
    missing_images: int = 0


class CatalogPagination(BaseModel):
    limit: int
    offset: int
    total: int
    has_more: bool


class CatalogPage(BaseModel):
    items: list[CatalogClan]
    pagination: CatalogPagination


class EquipmentCombat(BaseModel):
    model_config = ConfigDict(extra="allow")
    power: float
    damage_spread: float = 0
    bonuses: dict[str, str] = Field(default_factory=dict)
    implicit_bonuses: dict[str, float] = Field(default_factory=dict)
    triggers: list[str] = Field(default_factory=list)
    related_skill: str | None = None


class EquipmentGeneration(BaseModel):
    model_config = ConfigDict(extra="allow")
    material_id: str | None = None
    item_grade: str
    affixes: list[dict[str, Any]] = Field(default_factory=list)


class EquipmentItem(BaseModel):
    model_config = ConfigDict(extra="allow")
    item_id: str
    base_id: str
    slot: str
    combat: EquipmentCombat
    generation: EquipmentGeneration


class MonsterStatRow(BaseModel):
    key: str
    label: str
    base_value: str
    equipped_value: str
    delta_value: str
    catalog_value: str | None = None


class MonsterStatGroup(BaseModel):
    key: str
    label: str
    rows: list[MonsterStatRow]


class MonsterStatsPreview(BaseModel):
    groups: list[MonsterStatGroup]
    notes: list[str]
    technical: dict[str, Any]
    tier_multiplier: float = 1


class PlayerComparisonRow(BaseModel):
    key: str
    label: str
    player_value: str
    monster_value: str


class PlayerComparisonGroup(BaseModel):
    key: str
    label: str
    rows: list[PlayerComparisonRow]


class PlayerComparison(BaseModel):
    label: str
    notes: list[str]
    input_attributes: dict[str, int]
    mastery: float
    groups: list[PlayerComparisonGroup]
    item_cards: list[ItemCard]
    technical: dict[str, Any]


class CatalogEquipment(BaseModel):
    member_id: str
    variant_id: str
    tier: int
    available_tiers: list[int]
    base_stats: dict[str, int]
    equipment_set_id: str
    items: list[EquipmentItem]
    item_cards: list[ItemCard] = Field(default_factory=list)
    stats_preview: MonsterStatsPreview | None = None
    player_comparison: PlayerComparison | None = None


class CatalogMonstersApi(BaseApiClient):
    async def get_equipment(
        self,
        member_id: str,
        tier: int,
        *,
        player_attributes: dict[str, int] | None = None,
    ) -> CatalogEquipment:
        params: dict[str, Any] = {"member_id": member_id, "tier": tier}
        if player_attributes is not None:
            params["player_attributes"] = json.dumps(player_attributes)
        return await self._request(
            "GET",
            "/api/admin/monsters/catalog/equipment",
            CatalogEquipment,
            params=params,
        )

    async def get_summary(self) -> CatalogSummary:
        return await self._request("GET", "/api/admin/monsters/catalog/summary", CatalogSummary)

    async def list_catalog(self, *, clan_id: str | None = None, limit: int = 100, offset: int = 0) -> CatalogPage:
        params: dict[str, Any] = {"limit": limit, "offset": offset, "include_members": True}
        if clan_id:
            params["clan_id"] = clan_id
        return await self._request("GET", "/api/admin/monsters/catalog", CatalogPage, params=params)

    async def list_all(self) -> list[CatalogClan]:
        clans: list[CatalogClan] = []
        offset = 0
        while True:
            page = await self.list_catalog(offset=offset)
            clans.extend(page.items)
            if not page.pagination.has_more:
                return clans
            if not page.items:
                raise ValueError("Catalogue pagination returned an empty intermediate page")
            offset += len(page.items)

    async def get_clan(self, clan_id: str) -> CatalogClan | None:
        page = await self.list_catalog(clan_id=clan_id, limit=1)
        return page.items[0] if page.items else None
