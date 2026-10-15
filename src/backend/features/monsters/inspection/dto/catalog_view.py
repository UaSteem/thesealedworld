from typing import Any

from pydantic import BaseModel, Field

from src.backend.features.monsters.catalog.contracts import MonsterRole
from src.backend.features.monsters.inspection.dto.generated_view import PaginationDTO


class CatalogImageViewDTO(BaseModel):
    asset_id: str
    image_url: str
    source_path: str
    review_status: str
    display_mirror: bool = False


class CatalogMemberViewDTO(BaseModel):
    member_id: str
    clan_id: str
    family_id: str
    variant_id: str
    name: str
    description: str
    role: MonsterRole
    tags: list[str]
    min_tier: int
    max_tier: int
    base_stats: dict[str, int]
    skills: list[str]
    ability_ids: list[str] = Field(default_factory=list)
    base_id: str | None = None
    fixed_loadout: dict[str, str | None]
    member_model: dict[str, Any] | None = None
    image: CatalogImageViewDTO | None = None


class CatalogClanViewDTO(BaseModel):
    clan_id: str
    family_id: str
    family_name: str
    name: str
    description: str
    tags: list[str]
    features: list[str]
    normal_spawn: bool
    members: list[CatalogMemberViewDTO] = Field(default_factory=list)
    member_count: int
    missing_images: int


class CatalogMonstersResponseDTO(BaseModel):
    items: list[CatalogClanViewDTO]
    pagination: PaginationDTO


class CatalogMonstersSummaryDTO(BaseModel):
    families: int
    clans: int
    members: int
    missing_images: int
