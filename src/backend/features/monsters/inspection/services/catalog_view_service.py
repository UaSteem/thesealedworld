from pathlib import PurePosixPath
from urllib.parse import quote

from src.backend.features.items.services.presentation_service import ItemPresentationService
from src.backend.features.monsters.catalog.contracts import MemberDefinition, MonsterRole, thaw_catalog_value
from src.backend.features.monsters.catalog.indexes import MonsterCatalog
from src.backend.features.monsters.catalog.prepared_equipment import (
    get_prepared_equipment,
    list_prepared_equipment,
)
from src.backend.features.monsters.catalog.registry import get_catalog
from src.backend.features.monsters.catalog.resources.equipment_mapping import get_natural_equipment_mapping
from src.backend.features.monsters.catalog.texts import localized_definition
from src.backend.features.monsters.inspection.dto.catalog_view import (
    CatalogEquipmentViewDTO,
    CatalogMonstersResponseDTO,
    CatalogMonstersSummaryDTO,
)
from src.backend.features.monsters.inspection.services.equipment_stats_service import MonsterEquipmentStatsService
from src.backend.features.monsters.inspection.services.player_comparison_service import PlayerComparisonService


class CatalogMonsterViewService:
    """Project authored definitions for inspection; never load generated DB rows."""

    def __init__(self, catalog: MonsterCatalog | None = None):
        self.catalog = catalog if catalog is not None else get_catalog()

    def list_catalog(
        self,
        *,
        family_id: str | None = None,
        locale: str = "ru",
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
                    "family_name": localized_definition(self.catalog.families[clan.family_id], locale)["name"],
                    **localized_definition(clan, locale),
                    "tags": sorted(clan.tags),
                    "features": list(clan.features),
                    "normal_spawn": clan.normal_spawn,
                    "members": [self._member(member, locale) for member in members] if include_members else [],
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

    def equipment(
        self, *, member_id: str, tier: int, player_attributes: dict[str, int] | None = None
    ) -> CatalogEquipmentViewDTO:
        member = self.catalog.members.get(member_id)
        if member is None:
            raise LookupError("Unknown catalog member")
        if type(tier) is not int or not member.min_tier <= tier <= member.max_tier:
            raise ValueError("Tier is outside this member's catalog availability")
        if member.family_id not in {"goblin_tribe", "wolf_pack", "rat_swarm", "bandit_gang"}:
            raise LookupError("Prepared equipment is not available for this family")
        available_tiers = sorted(
            available_tier
            for variant_id, available_tier in list_prepared_equipment(family_id=member.family_id)
            if variant_id == member.variant_id and member.min_tier <= available_tier <= member.max_tier
        )
        prepared = get_prepared_equipment(family_id=member.family_id, variant_id=member.variant_id, tier=tier)
        expected_set_id = member.equipment_set_id or f"{member.family_id}.{member.base_id}"
        if prepared.clan_id != member.clan_id or prepared.equipment_set_id != expected_set_id:
            raise LookupError("Prepared equipment does not match this catalog clan and set")
        presentation = ItemPresentationService()
        cards = []
        for item in prepared.items:
            card = presentation.present(item)
            natural = (
                get_natural_equipment_mapping(item.generation.natural_key) if item.generation.natural_key else None
            )
            if natural is not None:
                card = card.model_copy(
                    update={
                        "title": natural.name_ru or card.title,
                        "description": natural.description_ru or card.description,
                        "material_label": "Природное снаряжение",
                    }
                )
            context = item.generation.source_context
            presentation_overrides = {
                field: context[key]
                for field, key in (("title", "presentation_name_ru"), ("description", "presentation_description_ru"))
                if isinstance(context.get(key), str) and context[key]
            }
            if presentation_overrides:
                card = card.model_copy(update=presentation_overrides)
            cards.append(card)
        stats = MonsterEquipmentStatsService().preview(
            member=member, family=self.catalog.families[member.family_id], prepared=prepared
        )
        return CatalogEquipmentViewDTO(
            member_id=member.id,
            variant_id=member.variant_id,
            tier=tier,
            available_tiers=available_tiers,
            base_stats=dict(member.base_stats),
            equipment_set_id=prepared.equipment_set_id,
            items=list(prepared.items),
            item_cards=cards,
            stats_preview=stats,
            player_comparison=PlayerComparisonService().preview(tier=tier, monster=stats, attributes=player_attributes),
        )

    def _member(self, member: MemberDefinition, locale: str = "ru") -> dict:
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
            **localized_definition(member, locale),
            "role": member.role,
            "tags": sorted(member.tags),
            "min_tier": member.min_tier,
            "max_tier": member.max_tier,
            "base_stats": dict(member.base_stats),
            "skills": list(member.skills),
            "ability_ids": list(member.ability_ids),
            "base_id": member.base_id,
            "image_source": member.image_source,
            "equipment_set_id": member.equipment_set_id,
            "equipment_source": member.equipment_source,
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
