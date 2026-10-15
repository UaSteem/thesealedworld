## Weapon triggers

Weapon trigger — обычный `TriggerCatalogEntryDTO` с group `weapon`. Оружие ссылается на него через `BaseItemDTO.triggers: list[str]` (список `trigger_id`).

### Файл определений
`src/backend/features/game_catalog/combat/resources/triggers/definitions/rules/weapon_triggers.py`
Экспортирует `WEAPON_TRIGGER_CATALOG: list[TriggerCatalogEntryDTO]`.
Добавляется в `ALL_TRIGGER_CATALOG_ENTRIES` в `definitions/catalog.py`.

### Пример weapon trigger
```python
TriggerCatalogEntryDTO(
    key="combat.trigger.weapon.katana_bleed",
    technical=TriggerTechnicalDTO(
        trigger_id="katana_bleed",
        event="ON_CRIT",
        chance=0.75,
        mutations={"add_effect": {"id": "dot_bleed"}},
        applied_effect_ids=["dot_bleed"],
    ),
    descriptive=build_combat_description(
        resource_type="trigger",
        resource_id="katana_bleed",
        display_name="Кровь катаны",
        short_description="Критический удар катаной открывает кровотечение.",
        humanoid_event_texts=CombatEventTextSetDTO(
            crit_proc=["{source} рассекает {target} катаной; лезвие вскрывает вену."],
            apply_effect=["{source} накладывает {effect} на {target}."],
        ),
        beast_event_texts=default_trigger_proc_event_texts("Кровь катаны"),
    ),
)
```

### Привязка к оружию
В файле определения оружия (например, `swords/katana.py`):
```python
BaseItemDTO(
    ...
    triggers=["katana_bleed"],  # trigger_id из TriggerTechnicalDTO
)
```

---

## Как добавить новый триггер

1. **Определить group** — по resolver stage (`crit`, `parry`, `dodge`, etc.) или `weapon`/`style`
2. **Создать запись** в нужном `definitions/rules/on_*.py` или `weapon_triggers.py`:
   - `TriggerTechnicalDTO` с `trigger_id`, `event`, `chance`, `mutations`, `applied_effect_ids`
   - `build_combat_description(...)` с `humanoid_event_texts` по нужному `{event}_proc` или `proc`
   - Обернуть в `TriggerCatalogEntryDTO(key="combat.trigger.{group}.{trigger_id}", ...)`
3. **Добавить в `*_CATALOG`** соответствующего файла правил
4. **Добавить bool флаг** в нужный `*TriggersDTO` в `trigger_rules.py`:
   ```python
   class CritTriggersDTO(BaseModel):
       bleed_on_crit: bool = False
       my_new_trigger: bool = False   # добавить сюда
   ```
5. **Если weapon trigger** — добавить `trigger_id` в `triggers: list[str]` оружия в `BaseItemDTO`
6. **Если counter / extra_strike** — добавить `trigger_id` в `_SEPARATE_LINE_TRIGGERS` в `log_builder.py`

---

## Ключевые файлы

| Файл | Назначение |
|---|---|
| `src/backend/features/game_catalog/combat/resources/triggers/schemas.py` | TriggerTechnicalDTO, TriggerCatalogEntryDTO |
| `src/backend/features/game_catalog/combat/resources/common/descriptions.py` | CombatEventTextSetDTO (включая proc-поля), default_trigger_proc_event_texts |
| `src/backend/features/game_catalog/combat/resources/triggers/__init__.py` | Реестр: TRIGGER_REGISTRY, TRIGGER_CATALOG_BY_KEY, public API |
| `src/backend/features/game_catalog/combat/resources/triggers/definitions/catalog.py` | ALL_TRIGGER_CATALOG_ENTRIES (агрегатор) |
| `src/backend/features/game_catalog/combat/resources/triggers/definitions/rules/` | Определения по событиям: on_crit.py, on_parry.py, styles.py, weapon_triggers.py, ... |
| `src/backend/features/combat/dto/trigger_rules.py` | TriggerRulesFlagsDTO (bool флаги по stages) |
| `src/backend/features/combat/runtime/engine/resolver.py` | _resolve_triggers() — пишет в res.fired_triggers |
| `src/backend/features/combat/dto/pipeline.py` | InteractionResultDTO.fired_triggers |
| `src/backend/features/combat/integrations/catalog_integrator.py` | CombatCatalogIntegrator — get_trigger_catalog_entry, get_trigger_catalog_entry_by_key |
| `src/backend/features/combat/runtime/services/log_builder.py` | _build_trigger_proc_entry, _trigger_suffix_text, _should_merge_trigger |

---

## Не делать

- Не создавать отдельную папку `descriptions/` — descriptive данные живут рядом с triggers
- Не дублировать damage строку если trigger merge=True
- Не использовать старый `TriggerDTO` — он заменён `TriggerTechnicalDTO`
- Не выводить `applied_effect_ids` из `mutations` — заполнять явно при определении
- Не добавлять `trigger_id` в catalog_key (только в `TriggerTechnicalDTO.trigger_id`)
