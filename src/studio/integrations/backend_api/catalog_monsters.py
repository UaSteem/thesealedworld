"""Read-only client for authored monster definitions (not persisted instances)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from src.frontend.core.api import BaseApiClient


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
    description: str = ""
    role: str
    tags: list[str] = Field(default_factory=list)
    min_tier: int
    max_tier: int
    base_stats: dict[str, int] = Field(default_factory=dict)
    skills: list[str] = Field(default_factory=list)
    ability_ids: list[str] = Field(default_factory=list)
    base_id: str | None = None
    fixed_loadout: dict[str, str | None] = Field(default_factory=dict)
    member_model: dict[str, Any] | None = None
    image: CatalogImage | None = None


class CatalogClan(BaseModel):
    clan_id: str
    family_id: str
    family_name: str
    name: str
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


class CatalogMonstersApi(BaseApiClient):
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
