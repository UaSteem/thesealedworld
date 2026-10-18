"""Read-only reference player, using player item rolls and character combat math."""

from copy import deepcopy
from functools import lru_cache
from typing import Any

from src.backend.core.calculators.stats_waterfall_calculator import StatsWaterfallCalculator
from src.backend.features.character.resources.starting_imprints import ATTRIBUTE_KEYS, STARTING_IMPRINTS
from src.backend.features.character.runtime.combat_actor_input import CharacterCombatActorInputBuilder
from src.backend.features.character.runtime.combat_math_model import CharacterCombatMathModelBuilder
from src.backend.features.character.runtime.rules.base_power_assembler import BasePowerAssembler
from src.backend.features.items.dto.instance import GeneratedItemDTO, ItemGenerationRequestDTO, ItemOriginRefDTO
from src.backend.features.items.runtime.item_factory import ItemFactory
from src.backend.features.items.services.presentation_service import ItemPresentationService
from src.backend.features.monsters.inspection.dto.catalog_view import MonsterStatsPreviewDTO, PlayerComparisonDTO
from src.backend.features.monsters.inspection.services.equipment_stats_service import _GROUPS, _PERCENT_KEYS, _format

_LOADOUT = (
    ("main_hand", "stiletto"),
    ("off_hand", "main_gauche"),
    ("head_armor", "hood"),
    ("chest_armor", "leather_armor"),
    ("arms_armor", "soft_bracers"),
    ("legs_armor", "scout_leggings"),
    ("chest_garment", "linen_shirt"),
    ("legs_garment", "fur_pants"),
    ("feetwear", "travel_boots"),
    ("gloves_garment", "work_gloves"),
    ("outer_garment", "winter_cloak"),
    ("belt_accessory", "belt"),
    ("ring_1", "ring"),
    ("ring_2", "ring"),
    ("amulet", "amulet"),
    ("earring", "earring"),
)

_JEWELRY_SLOTS = frozenset({"ring_1", "ring_2", "amulet", "earring"})
_DUAL_BLADES_ATTRIBUTES = {
    "ring_1": "attribute_agility",
    "ring_2": "attribute_perception",
    "amulet": "attribute_endurance",
    "earring": "attribute_strength",
}


def validate_player_attributes(attributes: dict[str, int]) -> dict[str, int]:
    if not isinstance(attributes, dict) or set(attributes) != set(ATTRIBUTE_KEYS):
        raise ValueError("Player attributes must contain exactly all nine attribute keys")
    if any(type(value) is not int or not 1 <= value <= 500 for value in attributes.values()):
        raise ValueError("Player attributes must be integers from 1 to 500 (inspection input limit)")
    return dict(attributes)


class _StablePreviewItemFactory(ItemFactory):
    @staticmethod
    def _pool_for_item(*args, **kwargs):
        # Preserve legal candidates, remove hash-order dependence from this preview.
        return sorted(ItemFactory._pool_for_item(*args, **kwargs))


@lru_cache(maxsize=8)
def _gear(tier: int) -> tuple[dict[str, Any], ...]:
    factory = _StablePreviewItemFactory()
    result = []
    for slot, base_id in _LOADOUT:
        jewelry = slot in _JEWELRY_SLOTS
        seed_version = "studio-player-dual-blades-v3" if jewelry else "studio-player-dual-blades-v1"
        seed = f"{seed_version}:{tier}:{slot}"
        item = factory.generate_player_item(
            ItemGenerationRequestDTO(
                base_id=base_id,
                target_slot=slot,
                rarity_tier=tier,
                origin_ref=ItemOriginRefDTO(seed=seed),
                request_ai_text=False,
                forced_affix_ids=[_DUAL_BLADES_ATTRIBUTES[slot]] if jewelry else [],
            )
        )
        item.instance_id = seed
        result.append(item.model_dump(mode="json"))
    return tuple(result)


class PlayerComparisonService:
    def preview(
        self, *, tier: int, monster: MonsterStatsPreviewDTO, attributes: dict[str, int] | None = None
    ) -> PlayerComparisonDTO:
        if type(tier) is not int or not 0 <= tier <= 7:
            raise ValueError("Unsupported equipment tier")
        imprint = STARTING_IMPRINTS["starter_dual_blades_01"]
        inputs = validate_player_attributes(attributes if attributes is not None else dict(imprint.attribute_values))
        mastery = tier / 7
        skills = {key: mastery for key in ("skill_fencing", "skill_dual_wield", "skill_light_armor")}
        items = {"layout": {"equipment": {}}, "by_id": {}}
        cards = []
        presentation = ItemPresentationService()
        for payload in _gear(tier):
            # A fresh DTO/dump prevents callers mutating the cached reference roll.
            item = GeneratedItemDTO.model_validate(payload)
            data = item.model_dump(mode="json")
            data["item_id"] = item.instance_id
            base = presentation.catalog.get_base_item(item.base_id)
            data["mechanics"] = {
                **item.mechanics,
                "power": item.power,
                "bonuses": dict(item.bonuses),
                "damage_spread": item.damage_spread,
                "triggers": list(item.triggers),
                "related_skill": item.metadata.get("related_skill"),
                "armor_class": base.armor_class if base else None,
            }
            items["layout"]["equipment"][item.slot] = item.instance_id
            items["by_id"][item.instance_id] = data
            cards.append(presentation.present(ItemFactory.project_runtime_item(item)))
        raw = CharacterCombatMathModelBuilder().build_raw(
            attributes=inputs, items=items, skills=skills, symbiote={"gift_rank": max(1, tier + 1)}
        )
        values, formulas = StatsWaterfallCalculator.calculate_waterfall(raw)
        loadout = CharacterCombatActorInputBuilder._loadout(items, skills, include_basic_gift_abilities=False)
        BasePowerAssembler.apply_to_values(values, loadout_layout=loadout["layout"], skills=skills)
        groups = []
        monster_values = monster.technical["equipped"]
        for group_key, label, fields in _GROUPS:
            rows = []
            for key, field_label in fields:
                player_value, monster_value = values.get(key, 0), monster_values.get(key, 0)
                if group_key in {"attack", "defense"} and not player_value and not monster_value:
                    continue
                rows.append(
                    {
                        "key": key,
                        "label": field_label,
                        "player_value": _format(player_value, percent=key in _PERCENT_KEYS),
                        "monster_value": _format(monster_value, percent=key in _PERCENT_KEYS),
                    }
                )
            if rows:
                groups.append({"key": group_key, "label": label, "rows": rows})
        return PlayerComparisonDTO(
            label="Игрок: стилет и дага, лёгкая броня",
            input_attributes=inputs,
            mastery=mastery,
            groups=groups,
            item_cards=cards,
            notes=[
                "Четыре украшения подобраны под два клинка: ловкость, восприятие, выносливость и сила. Число аффиксов определяется обычными правилами редкости; усиление игрока — 5 шагов.",
                "Точность, крит, уклонение и парирование показаны как исходные боевые модификаторы. Это не итоговые шансы против выбранного противника: resolver учитывает навыки, противодействие, стиль боя и капы; щит может отключать проверку уклонения.",
                "Это настраиваемый пример игрока, а не готовый баланс персонажа данного тира.",
                "По умолчанию взяты стартовые характеристики существующего слепка стилета и даги (общий пул 135). Автоматический рост характеристик игрока от тира не задан; их можно изменить вручную.",
                f"Запрошен тир экипировки и редкости {tier}: 16 предметов, обычные правила игрока, 5 шагов аффикса, фиксированный seed. Фактический материал виден в карточке каждого предмета.",
                f"Допущения примера: владение фехтованием, парным оружием и лёгкой бронёй — {mastery:.1%}; ранг симбионта {max(1, tier + 1)}, без перегрузки экипировки.",
                "Бой не симулировался: попадание, критические удары, активные способности и тактика могут изменить исход.",
                *(
                    [
                        "Сырое сопротивление может превышать 100%: в бою из него вычитается подавление противника. Сравнивать эти показатели нужно в паре."
                    ]
                    if monster_values.get("physical_resistance", 0) > 1
                    else []
                ),
                *(
                    ["Показаны заданные вручную характеристики игрока; правила их получения здесь не проверяются."]
                    if attributes is not None
                    else []
                ),
            ],
            technical={
                "input_attributes": inputs,
                "skills": skills,
                "equipped": values,
                "raw": raw,
                "formulas": formulas,
                "loadout": loadout,
                "equipment": deepcopy(list(_gear(tier))),
                "seed_version": "studio-player-dual-blades-v3-jewelry",
            },
        )
