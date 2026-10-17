"""Presentation of already assembled catalog monster statistics."""

from src.backend.features.monsters.catalog.contracts import FamilyDefinition, MemberDefinition
from src.backend.features.monsters.catalog.prepared_equipment import PreparedEquipmentSetDTO
from src.backend.features.monsters.inspection.dto.catalog_view import MonsterStatsPreviewDTO
from src.backend.features.monsters.instances.dto.instance_build import MonsterInstanceBuildDTO
from src.backend.features.monsters.instances.services.instance_builder import MonsterInstanceBuilder

_GROUPS = (
    (
        "resources",
        "Ресурсы",
        (
            ("hp", "Здоровье"),
            ("en", "Энергия"),
            ("hp_regen", "Восстановление здоровья"),
            ("en_regen", "Восстановление энергии"),
        ),
    ),
    (
        "attributes",
        "Характеристики",
        (
            ("strength", "Сила"),
            ("agility", "Ловкость"),
            ("endurance", "Выносливость"),
            ("intellect", "Интеллект"),
            ("memory", "Память"),
            ("mental", "Воля"),
            ("perception", "Восприятие"),
            ("projection", "Проекция"),
            ("prediction", "Предвидение"),
        ),
    ),
    (
        "attack",
        "Атака",
        (
            ("main_hand_damage_base", "База удара основной руки"),
            ("off_hand_damage_base", "База удара второй руки"),
            ("main_hand_damage_spread", "Разброс основной руки"),
            ("off_hand_damage_spread", "Разброс второй руки"),
            ("physical_damage_bonus", "Бонус физического урона"),
            ("magical_damage", "Магическая сила"),
        ),
    ),
    (
        "defense",
        "Защита",
        (
            ("armor", "Броня"),
            ("magic_armor", "Магическая броня"),
            ("physical_resistance", "Физическое сопротивление"),
            ("magic_resist", "Магическое сопротивление"),
            ("shield_guard_power", "Сила защиты щитом"),
        ),
    ),
    (
        "accuracy",
        "Точность — модификаторы",
        (
            ("main_hand_accuracy", "Точность основной руки"),
            ("off_hand_accuracy", "Точность второй руки"),
            ("accuracy", "Общий бонус точности"),
            ("main_hand_accuracy_penalty", "Штраф точности основной руки"),
            ("off_hand_accuracy_penalty", "Штраф точности второй руки"),
        ),
    ),
    (
        "critical",
        "Критический удар — исходные бонусы",
        (
            ("main_hand_crit_chance", "Крит основной руки"),
            ("off_hand_crit_chance", "Крит второй руки"),
            ("crit_chance", "Общий бонус крита"),
        ),
    ),
    (
        "avoidance",
        "Уклонение и парирование — до проверок",
        (
            ("evasion", "Уклонение до капа и противодействия"),
            ("anti_dodge_chance", "Противодействие уклонению"),
            ("parry", "Парирование до навыка и капа"),
        ),
    ),
    (
        "penetration",
        "Пробивание и подавление",
        (
            ("main_hand_armor_penetration_pct", "Пробивание основной руки"),
            ("off_hand_armor_penetration_pct", "Пробивание второй руки"),
            ("armor_penetration_pct", "Общий бонус пробивания"),
            ("armor_penetration_flat", "Плоское пробивание брони"),
            ("armor_ignore_chance", "Бонус игнорирования брони"),
            ("physical_suppression", "Подавление физического сопротивления"),
        ),
    ),
    (
        "caps",
        "Заданные ограничения",
        (
            ("dodge_cap", "Кап уклонения"),
            ("parry_cap", "Кап парирования"),
            ("main_hand_crit_cap", "Кап крита основной руки"),
            ("off_hand_crit_cap", "Кап крита второй руки"),
            ("shield_block_cap", "Кап блока щитом"),
            ("resistance_cap", "Кап сопротивления (сейчас не применяется)"),
        ),
    ),
)
_PERCENT_KEYS = frozenset(
    {
        "main_hand_damage_spread",
        "off_hand_damage_spread",
        "physical_resistance",
        "main_hand_accuracy",
        "off_hand_accuracy",
        "accuracy",
        "main_hand_accuracy_penalty",
        "off_hand_accuracy_penalty",
        "main_hand_crit_chance",
        "off_hand_crit_chance",
        "crit_chance",
        "evasion",
        "anti_dodge_chance",
        "parry",
        "main_hand_armor_penetration_pct",
        "off_hand_armor_penetration_pct",
        "armor_penetration_pct",
        "armor_ignore_chance",
        "physical_suppression",
        "dodge_cap",
        "parry_cap",
        "main_hand_crit_cap",
        "off_hand_crit_cap",
        "shield_block_cap",
        "resistance_cap",
    }
)


def _format(value: float, *, percent: bool = False, signed: bool = False) -> str:
    value = round(value * (100 if percent else 1), 2)
    number = f"{abs(value):.2f}".rstrip("0").rstrip(".").replace(".", ",")
    sign = "−" if value < 0 else ("+" if signed and value > 0 else "")
    return f"{sign}{number}{'%' if percent else ''}"


class MonsterEquipmentStatsService:
    """Use existing pre-combat math; never generate, persist, or resolve a hit."""

    def preview(
        self, *, member: MemberDefinition, family: FamilyDefinition, prepared: PreparedEquipmentSetDTO
    ) -> MonsterStatsPreviewDTO:
        return self.present(MonsterInstanceBuilder().build(member=member, family=family, prepared=prepared))

    @staticmethod
    def present(build: MonsterInstanceBuildDTO) -> MonsterStatsPreviewDTO:
        """Format an existing instance build without recalculating its mechanics."""
        baseline, equipped = build.baseline.values, build.equipped.values
        tier_multiplier = build.tier_multiplier
        groups = []
        for group_key, label, fields in _GROUPS:
            rows = []
            for key, field_label in fields:
                if key.startswith("off_hand_damage") and not equipped.get("off_hand_damage_base"):
                    continue
                before, after = baseline.get(key, 0.0), equipped.get(key, 0.0)
                if group_key not in {"attributes", "resources"} and not before and not after:
                    continue
                percent = key in _PERCENT_KEYS
                rows.append(
                    {
                        "key": key,
                        "label": field_label,
                        "base_value": _format(before, percent=percent),
                        "equipped_value": _format(after, percent=percent),
                        "delta_value": _format(after - before, percent=percent, signed=True),
                        "catalog_value": _format(build.catalog_attributes[key]) if group_key == "attributes" else None,
                    }
                )
            if rows:
                groups.append({"key": group_key, "label": label, "rows": rows})
        return MonsterStatsPreviewDTO(
            tier_multiplier=tier_multiplier,
            groups=groups,
            notes=[
                "Сравнение с тем же монстром без снаряжения на выбранном тире. Базовые характеристики каталога не изменены.",
                f"Характеристики на тире: основа × {tier_multiplier:g}, с округлением до целого. Использована существующая таблица развития тиров.",
                "Владение навыками рассчитано по существующему правилу: тир / 7.",
                "База удара — до проверки попадания, критического удара, брони цели и случайного разброса. Эффекты предметов во время боя здесь не активируются.",
            ],
            technical={
                "combat_math_version": build.combat_math_version,
                "tier": build.tier,
                "catalog_attributes": build.catalog_attributes,
                "tier_attributes": build.tier_attributes,
                "skills": build.skills,
                "base": baseline,
                "equipped": equipped,
                "base_trace": {
                    "raw": build.baseline.raw,
                    "formulas": build.baseline.formulas,
                    "loadout": build.baseline.loadout,
                },
                "equipped_trace": {
                    "raw": build.equipped.raw,
                    "formulas": build.equipped.formulas,
                    "loadout": build.equipped.loadout,
                },
            },
        )
