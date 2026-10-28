from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.backend.features.items.dto.instance import GeneratedItemDTO
from src.backend.features.items.dto.visuals import ItemAppearanceDTO
from src.backend.features.items.resources.affixes.narrative import normalize_lore_tags
from src.backend.features.items.services.catalog_service import ItemCatalogService

if TYPE_CHECKING:
    from src.backend.features.items.dto.instance import ItemOriginRefDTO, ItemPlacementRefDTO
    from src.backend.features.items.repositories import ItemInstanceRepository


class ItemPersistenceIntegration:
    """Items facade over item instance persistence."""

    def __init__(self, repo: ItemInstanceRepository, catalog: ItemCatalogService | None = None) -> None:
        self.repo = repo
        self.catalog = catalog or ItemCatalogService.load_default()

    async def create_mechanical_item(
        self,
        item: GeneratedItemDTO,
        placement_ref: ItemPlacementRefDTO,
        *,
        text_status: str,
        origin_ref: ItemOriginRefDTO | None = None,
        generated_template_id: str | None = None,
    ) -> str:
        instance = await self.repo.create_mechanical(
            item,
            placement_ref,
            text_status=text_status,
            origin_ref=origin_ref,
            generated_template_id=generated_template_id,
        )
        return str(instance.id)

    async def get_text_visual_template_by_hash(self, text_visual_hash: str) -> Any | None:
        return await self.repo.get_text_visual_template_by_hash(text_visual_hash)

    async def create_text_visual_template(
        self,
        item: GeneratedItemDTO,
        *,
        text_visual_hash: str,
        text_payload: dict[str, Any],
        prompt_version: str,
        text_status: str,
    ) -> Any:
        return await self.repo.create_text_visual_template(
            item,
            text_visual_hash=text_visual_hash,
            text_payload=text_payload,
            prompt_version=prompt_version,
            text_status=text_status,
        )

    async def request_template_text(self, template_id: str) -> bool:
        return await self.repo.request_template_text(template_id)

    async def get_generated_item(self, item_id: str) -> GeneratedItemDTO | None:
        instance = await self.repo.get(item_id)
        if instance is None:
            return None
        template_id = getattr(instance, "generated_template_id", None)
        template = await self.repo.get_generated_template(template_id) if template_id else None
        return self._dto_from_instance(instance, template=template)

    async def save_generated_text(self, item_id: str, item: GeneratedItemDTO) -> None:
        await self.repo.update_text(
            item_id,
            name=item.name,
            description=item.description,
            text_status="generated",
        )
        await self.repo.update_template_text_for_item(
            item_id,
            name=item.name,
            description=item.description,
            text_status="generated",
            metadata={
                "ai_text_status": item.metadata.get("ai_text_status"),
                "ai_prompt": item.metadata.get("ai_prompt"),
            },
        )

    async def mark_text_failed(self, item_id: str, reason: str | None = None) -> None:
        await self.repo.mark_text_failed(item_id, reason)

    async def transfer_deleted_character_items_to_system(self, character_id: int) -> int:
        return await self.repo.transfer_character_items_to_system(character_id)

    def _dto_from_instance(self, instance: Any, *, template: Any | None = None) -> GeneratedItemDTO:
        mechanics_raw = dict(instance.mechanics or {})
        bonuses = dict(mechanics_raw.get("bonuses") or {})

        # Lazy heal: compile bonuses from affixes for legacy items stored with bonuses={}
        if not bonuses and mechanics_raw.get("affixes"):
            from src.backend.features.items.runtime.item_factory import ItemFactory

            bonuses = ItemFactory._compile_affix_bonuses(mechanics_raw["affixes"])

        from src.backend.features.items.services.visual_service import ItemVisualService

        generation = dict(instance.generation or {})
        appearance_raw = dict(instance.appearance or {})
        visual_variant_id = appearance_raw.get("visual_variant_id")
        baseline_name, baseline_description = ItemVisualService(self.catalog).base_presentation(
            instance.base_id, generation.get("material_id"), visual_variant_id
        )
        # Internal DTO may carry prepared lore. Public inventory independently gates identification.
        generated_text = template is not None and template.text_status == "generated"
        name = (template.name or baseline_name) if generated_text else (instance.name or baseline_name)
        description = (
            (template.description or baseline_description)
            if generated_text
            else (instance.description or baseline_description)
        )
        material = self.catalog.get_material(generation.get("material_id"))
        item_tier = int(material.tier) if material is not None else int(generation.get("item_tier") or 0)
        return GeneratedItemDTO(
            instance_id=instance.id,
            template_id=str(mechanics_raw.get("template_id") or instance.base_id),
            item_type=instance.item_type,
            rarity=instance.rarity,
            rarity_tier=instance.rarity_tier,
            name=name,
            description=description,
            item_tier=item_tier,
            appearance=ItemAppearanceDTO.model_validate(
                {key: value for key, value in appearance_raw.items() if key in ItemAppearanceDTO.model_fields}
            )
            if appearance_raw
            else None,
            is_identified=bool(getattr(instance, "is_identified", False)),
            lore_tags=list(normalize_lore_tags(mechanics_raw.get("affixes", []))),
            base_id=instance.base_id,
            material_id=instance.generation.get("material_id"),
            affix_bundle_ids=list(instance.generation.get("affix_bundle_ids") or []),
            power=float(mechanics_raw.get("power") or 0),
            durability_max=float(mechanics_raw.get("durability_max") or 0),
            damage_spread=float(mechanics_raw.get("damage_spread") or 0.1),
            slot=str(mechanics_raw.get("slot") or ""),
            valid_slots=list(mechanics_raw.get("valid_slots") or []),
            implicit_bonuses=dict(mechanics_raw.get("implicit_bonuses") or {}),
            bonuses=bonuses,
            triggers=list(mechanics_raw.get("triggers") or []),
            narrative_tags=list(instance.generation.get("narrative_tags") or []),
            mechanics=mechanics_raw,
            metadata={
                **dict(instance.metadata_ or {}),
                "generated_template_id": getattr(instance, "generated_template_id", None),
            },
        )
