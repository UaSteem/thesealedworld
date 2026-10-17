"""Pure read-only presentation of runtime items, shared by all consumers."""

from decimal import Decimal, InvalidOperation

from src.backend.features.game_catalog.combat.resources.triggers.definitions.catalog import ALL_TRIGGER_CATALOG_ENTRIES
from src.backend.features.game_catalog.skills.services.catalog_service import SkillCatalogService
from src.backend.features.items.dto.instance import RuntimeItemProjectionDTO
from src.backend.features.items.dto.presentation import ItemCardDTO, ItemPropertyRowDTO
from src.backend.features.items.resources.item_grade import GRADE_BY_RARITY_TIER
from src.backend.features.items.resources.modifier_contracts.catalog import MODIFIER_CONTRACTS
from src.backend.features.items.resources.presentation_texts import IMPLICIT_PERCENT_KEYS, TEXTS
from src.backend.features.items.services.catalog_service import ItemCatalogService


def _number(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.0001")), "f").rstrip("0").rstrip(".").replace(".", ",") or "0"


class ItemPresentationService:
    def __init__(self, catalog: ItemCatalogService | None = None):
        self.catalog = catalog if catalog is not None else ItemCatalogService.load_default()
        self.skills = SkillCatalogService()
        self.triggers = {entry.technical.trigger_id: entry for entry in ALL_TRIGGER_CATALOG_ENTRIES}
        self.units = {contract.target_field: contract.value_kind for contract in MODIFIER_CONTRACTS.values()}

    def _row(self, key: str, raw: float | str, *, implicit: bool = False) -> ItemPropertyRowDTO:
        label = TEXTS["ru"]["stats"].get(key, "Неизвестное свойство")
        command = str(raw)
        operation = command[0] if command and command[0] in "+-*= " else ""
        operation = operation.strip()
        operand = command[1:] if operation else command
        try:
            value = Decimal(operand)
        except InvalidOperation:
            return ItemPropertyRowDTO(label=label, value="Значение требует проверки")
        percent = key in IMPLICIT_PERCENT_KEYS if implicit else self.units.get(key) == "percent"
        # Multiplication is a factor even when the target field is a probability.
        suffix = "%" if percent and operation != "*" else ""
        if suffix:
            value *= 100
        prefix = {"*": "×", "=": "=", "+": "+", "-": "−"}.get(operation, "")
        return ItemPropertyRowDTO(label=label, value=f"{prefix}{_number(value)}{suffix}")

    def present(self, item: RuntimeItemProjectionDTO, *, locale: str = "ru") -> ItemCardDTO:
        # Only RU resources currently exist; expose the actual language used.
        base = self.catalog.get_base_item(item.base_id)
        material = self.catalog.get_material(item.generation.material_id) if item.generation.material_id else None
        rarity_tier = next(
            (tier for tier, grade in GRADE_BY_RARITY_TIER.items() if grade == item.generation.item_grade), None
        )
        rarity = self.catalog.get_rarity(rarity_tier) if rarity_tier is not None else None
        effects = []
        for trigger_id in item.combat.triggers:
            entry = self.triggers.get(trigger_id.split(".", 1)[-1])
            if entry is None:
                effects.append("Неизвестный эффект — проверьте технические данные.")
            else:
                text = entry.descriptive.variants[entry.descriptive.default_taxonomy]
                effects.append(f"{text.display_name}. {text.short_description}")
        skill = self.skills.get(item.combat.related_skill) if item.combat.related_skill else None
        power_label = {"weapon": "Сила оружия", "armor": "Защита доспеха"}.get(item.item_type, "Сила предмета")
        properties = [self._row(key, value, implicit=True) for key, value in item.combat.implicit_bonuses.items()]
        if item.combat.damage_spread:
            properties.insert(
                0,
                ItemPropertyRowDTO(
                    label="Разброс урона", value=f"±{_number(Decimal(str(item.combat.damage_spread)) * 100)}%"
                ),
            )
        return ItemCardDTO(
            title=base.name_ru if base else "Неизвестный предмет",
            description=(base.narrative_description or "") if base else "Описание отсутствует.",
            material_label=material.name_ru if material else "Материал не указан",
            rarity_label=rarity.name_ru if rarity else "Редкость не определена",
            rarity_color=rarity.color_hex if rarity else "#888899",
            slot_label=TEXTS["ru"]["slots"].get(item.slot, "Неизвестный слот"),
            power_label=power_label,
            power_value=_number(Decimal(str(item.combat.power))),
            properties=properties,
            bonuses=[self._row(key, value) for key, value in item.combat.bonuses.items()],
            effects=effects,
            skill_label=skill.name_ru if skill else ("Неизвестный навык" if item.combat.related_skill else None),
            technical=item.model_dump(mode="json"),
        )
