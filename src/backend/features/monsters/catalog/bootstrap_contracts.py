"""Presentation-only catalogue snapshot for client caches."""

from typing import Annotated

from pydantic import BaseModel, Field, StrictInt


class CatalogTextDTO(BaseModel):
    id: str
    name: str
    description: str
    tags: list[str]
    text_locale: str = "ru"
    text_fallback: bool = False


class FamilyTextDTO(CatalogTextDTO):
    clan_ids: list[str]


class ClanTextDTO(CatalogTextDTO):
    family_id: str
    member_ids: list[str]


class CatalogArtDTO(BaseModel):
    asset_id: str
    image_url: str
    display_mirror: bool


class MemberTextDTO(CatalogTextDTO):
    family_id: str
    clan_id: str
    variant_id: str
    role: str
    assembly_cost: Annotated[StrictInt, Field(gt=0)]
    base_id: str | None = None
    image_source: str | None = None
    ability_ids: list[str]
    image: CatalogArtDTO | None


class CatalogManifestDTO(BaseModel):
    version: str
    sections: dict[str, str]


class MonsterCatalogBootstrapDTO(BaseModel):
    schema_version: int = 2
    locale: str = "ru"
    fallback_locale: str = "ru"
    available_locales: list[str]
    version: str
    families: dict[str, FamilyTextDTO]
    clans: dict[str, ClanTextDTO]
    members: dict[str, MemberTextDTO]
    manifest: CatalogManifestDTO
