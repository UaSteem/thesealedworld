from pathlib import PurePosixPath
from urllib.parse import quote

from src.backend.features.monsters.catalog.contracts import MemberDefinition, MonsterRole, thaw_catalog_value
from src.backend.features.monsters.catalog.indexes import MonsterCatalog
from src.backend.features.monsters.catalog.registry import get_catalog
from src.backend.features.monsters.inspection.dto.catalog_view import (
    CatalogMonstersResponseDTO,
    CatalogMonstersSummaryDTO,
)


class CatalogMonsterViewService:
    """Project authored definitions for inspection; never load generated DB rows."""

    def __init__(self, catalog: MonsterCatalog | None = None):
        self.catalog = catalog if catalog is not None else get_catalog()

    def list_catalog(
        self,
        *,
        family_id: str | None = None,
        clan_id: str | None = None,
        role: MonsterRole | None = None,
        include_members: bool = True,
        limit: int = 25,
        offset: int = 0,
    ) -> CatalogMonstersResponseDTO:
        clans = [
            c
            for c in self.catalog.clans.values()
            if (family_id is None or c.family_id == family_id) and (clan_id is None or c.id == clan_id)
        ]
        items = []
        for clan in clans[offset : offset + limit]:
            members = [
                self.catalog.members[mid]
                for mid in clan.member_ids
                if role is None or self.catalog.members[mid].role == role
            ]
            items.append(
                {
                    "clan_id": clan.id,
                    "family_id": clan.family_id,
                    "family_name": self.catalog.families[clan.family_id].name,
                    "name": clan.name,
                    "description": clan.description,
                    "tags": sorted(clan.tags),
                    "features": list(clan.features),
                    "normal_spawn": clan.normal_spawn,
                    "members": [self._member(member) for member in members] if include_members else [],
                    "member_count": len(members),
                    "missing_images": sum(member.image is None for member in members),
                }
            )
        return CatalogMonstersResponseDTO(
            items=items,
            pagination={"limit": limit, "offset": offset, "total": len(clans), "has_more": offset + limit < len(clans)},
        )

    def summary(self, *, family_id: str | None = None) -> CatalogMonstersSummaryDTO:
        families = [f for f in self.catalog.families.values() if family_id is None or f.id == family_id]
        clans = [c for c in self.catalog.clans.values() if family_id is None or c.family_id == family_id]
        members = [m for m in self.catalog.members.values() if family_id is None or m.family_id == family_id]
        return CatalogMonstersSummaryDTO(
            families=len(families),
            clans=len(clans),
            members=len(members),
            missing_images=sum(m.image is None for m in members),
        )

    def _member(self, member: MemberDefinition) -> dict:
        model = member.mechanics.get("member_model")
        if model is None:
            model = next(
                (
                    m
                    for m in self.catalog.families[member.family_id].mechanics.get("member_models", ())
                    if m["variant_key"] == member.variant_id
                ),
                None,
            )
        image = member.image
        return {
            "member_id": member.id,
            "clan_id": member.clan_id,
            "family_id": member.family_id,
            "variant_id": member.variant_id,
            "name": member.name,
            "description": member.description,
            "role": member.role,
            "tags": sorted(member.tags),
            "min_tier": member.min_tier,
            "max_tier": member.max_tier,
            "base_stats": dict(member.base_stats),
            "skills": list(member.skills),
            "ability_ids": list(member.ability_ids),
            "base_id": member.base_id,
            "fixed_loadout": dict(member.fixed_loadout),
            "member_model": thaw_catalog_value(model) if model is not None else None,
            "image": {
                "asset_id": image.asset_id,
                "image_url": f"/static/images/monsters/catalog/{quote(image.asset_id, safe='')}{PurePosixPath(image.source_path).suffix}",
                "source_path": image.source_path,
                "review_status": image.review_status,
                "display_mirror": image.display_mirror,
            }
            if image is not None
            else None,
        }
