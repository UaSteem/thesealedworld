"""Presentation-only catalogue snapshot for client caches."""

from pydantic import BaseModel


class CatalogTextDTO(BaseModel):
    id: str
    name: str
    description: str
    tags: list[str]


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
    ability_ids: list[str]
    image: CatalogArtDTO | None


class CatalogManifestDTO(BaseModel):
    version: str
    sections: dict[str, str]


class MonsterCatalogBootstrapDTO(BaseModel):
    schema_version: int = 1
    version: str
    families: dict[str, FamilyTextDTO]
    clans: dict[str, ClanTextDTO]
    members: dict[str, MemberTextDTO]
    manifest: CatalogManifestDTO
