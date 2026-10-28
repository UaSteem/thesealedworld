"""Controlled affix lore meanings; mechanics and contextual tags stay separate."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

NARRATIVE_TAGS: dict[str, str] = {
    "precision": "Точность, выверенное движение и надёжный прицел.",
    "ferocity": "Сокрушительная сила и беспощадное поражение уязвимого места.",
    "agility": "Лёгкость, проворство и быстрый ответ на опасность.",
    "blood_drain": "Вампирическая тяга, отнимающая жизненную силу.",
    "protection": "Укреплённая преграда, стойкая защита и выдерживание ударов.",
    "retaliation": "Опасная поверхность, отвечающая на прикосновение болью.",
    "control": "Подавление чужой воли или движений.",
    "resolve": "Несгибаемая воля и сопротивление принуждению.",
    "arcane": "Резонанс древней аномальной энергии и чар.",
    "flame": "Плазменный жар южного Якоря.",
    "vitality": "Запас жизни, выносливость и телесная стойкость.",
    "renewal": "Восстановление жизни и затягивание повреждений.",
    "focus": "Собранность, концентрация и устойчивый запас сил.",
    "knowledge": "Накопленное знание, память и понимание скрытого.",
    "foresight": "Предчувствие и предвидение возможного исхода.",
    "craft": "Мастерство ремесла и бережная точная работа.",
    "fortune": "Благоприятный случай и удачная находка.",
    "trade": "Расчётливость торговца и чутьё на ценность.",
    "wayfinding": "Путь, ориентирование и уверенное странствие.",
    "awareness": "Наблюдательность и распознавание скрытых следов.",
    "cold_ward": "Защита от холода и северного оцепенения.",
    "purity": "Очищение и сопротивление заражению биомассой.",
    "heat_ward": "Защита от палящего жара.",
}


def validate_narrative_tags(tags: Iterable[str]) -> tuple[str, ...]:
    normalized = tuple(sorted(set(tags)))
    unknown = set(normalized) - NARRATIVE_TAGS.keys()
    if unknown:
        raise ValueError(f"Unknown affix narrative tags: {', '.join(sorted(unknown))}")
    return normalized


def normalize_lore_tags(affixes: Iterable[object]) -> tuple[str, ...]:
    # Read only identities that were actually rolled, never caller-supplied tags/roll values.
    from .catalog import AFFIX_CATALOG

    tags: set[str] = set()
    for raw in affixes:
        if not isinstance(raw, dict) or not raw.get("affix_id"):
            raise ValueError("Rolled affix must reference an authored affix_id")
        affix_id = str(raw["affix_id"])
        entry = AFFIX_CATALOG.get(affix_id)
        if entry is None:
            raise ValueError(f"Unknown rolled affix: {affix_id}")
        tags.update(entry.descriptive.narrative_tags)
    return validate_narrative_tags(tags)
