"""Localized presentation labels; mechanics and units remain catalog-owned."""

TEXTS = {
    "ru": {
        "stats": {
            "main_hand_accuracy": "Точность основной руки",
            "off_hand_accuracy": "Точность второй руки",
            "main_hand_accuracy_penalty": "Штраф точности основной руки",
            "off_hand_accuracy_penalty": "Штраф точности второй руки",
            "physical_crit_chance": "Шанс критического удара",
            "crit_chance": "Шанс критического удара",
            "parry_chance": "Парирование",
            "parry_penalty": "Парирование",
            "evasion_penalty": "Уклонение",
            "debuff_avoidance": "Избежание негативных эффектов",
            "armor_penetration_pct": "Пробивание брони",
            "control_chance_bonus": "Шанс контроля",
            "control_resistance": "Сопротивление контролю",
            "physical_resistance": "Физическое сопротивление",
            "environment_heat_resistance": "Сопротивление жаре",
            "evasion": "Уклонение",
            "hp_regen": "Восстановление здоровья",
            "agility": "Ловкость",
            "strength": "Сила",
            "endurance": "Выносливость",
            "intellect": "Интеллект",
            "memory": "Память",
            "mental": "Ментальность",
            "projection": "Проекция",
            "prediction": "Предвидение",
            "luck": "Удача",
            "perception": "Восприятие",
            "armor": "Броня",
            "hp": "Здоровье",
            "en": "Энергия",
            "shield_guard_power": "Защита щитом",
            "thorns_damage_flat": "Ответный урон шипами",
        },
        "slots": {
            "main_hand": "Основная рука",
            "off_hand": "Вторая рука",
            "two_hand": "Двуручное оружие",
            "chest_armor": "Броня корпуса",
            "head_armor": "Броня головы",
            "arms_armor": "Наручи",
            "legs_armor": "Броня ног",
            "gloves_garment": "Перчатки",
            "outer_garment": "Плащ",
            "feetwear": "Обувь",
            "belt_accessory": "Пояс",
            "amulet": "Амулет",
            "ring_1": "Первое кольцо",
            "ring_2": "Второе кольцо",
            "earring": "Серьга",
        },
    }
}

# Base implicit properties have no modifier contract. Declare units explicitly.
IMPLICIT_PERCENT_KEYS = frozenset(
    {
        "main_hand_accuracy_penalty",
        "off_hand_accuracy_penalty",
        "physical_crit_chance",
        "parry_chance",
        "parry_penalty",
        "evasion_penalty",
        "debuff_avoidance",
    }
)
