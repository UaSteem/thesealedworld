from typing import Any

from pydantic import BaseModel, Field

from src.backend.features.items.dto.instance import RuntimeItemProjectionDTO
from src.backend.features.items.dto.presentation import ItemCardDTO
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
    text_locale: str = "ru"
    text_fallback: bool = False
    description: str
    role: MonsterRole
    tags: list[str]
    min_tier: int
    max_tier: int
    base_stats: dict[str, int]
    skills: list[str]
    ability_ids: list[str] = Field(default_factory=list)
    base_id: str | None = None
    image_source: str | None = None
    equipment_set_id: str | None = None
    equipment_source: str | None = None
    fixed_loadout: dict[str, str | None]
    member_model: dict[str, Any] | None = None
    image: CatalogImageViewDTO | None = None


class CatalogClanViewDTO(BaseModel):
    clan_id: str
    family_id: str
    family_name: str
    name: str
    text_locale: str = "ru"
    text_fallback: bool = False
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


class MonsterStatRowDTO(BaseModel):
    key: str
    label: str
    base_value: str
    equipped_value: str
    delta_value: str
    catalog_value: str | None = None


class MonsterStatGroupDTO(BaseModel):
    key: str
    label: str
    rows: list[MonsterStatRowDTO]


class MonsterStatsPreviewDTO(BaseModel):
    tier_multiplier: float
    groups: list[MonsterStatGroupDTO]
    notes: list[str]
    technical: dict[str, Any]


class PlayerComparisonRowDTO(BaseModel):
    key: str
    label: str
    player_value: str
    monster_value: str


class PlayerComparisonGroupDTO(BaseModel):
    key: str
    label: str
    rows: list[PlayerComparisonRowDTO]


class PlayerComparisonDTO(BaseModel):
    label: str
    notes: list[str]
    input_attributes: dict[str, int]
    mastery: float
    groups: list[PlayerComparisonGroupDTO]
    item_cards: list[ItemCardDTO]
    technical: dict[str, Any]


class CatalogEquipmentViewDTO(BaseModel):
    member_id: str
    variant_id: str
    tier: int
    available_tiers: list[int]
    base_stats: dict[str, int]
    stats_scaled: bool = False
    equipment_set_id: str
    items: list[RuntimeItemProjectionDTO]
    item_cards: list[ItemCardDTO] = Field(default_factory=list)
    stats_preview: MonsterStatsPreviewDTO | None = None
    player_comparison: PlayerComparisonDTO | None = None
