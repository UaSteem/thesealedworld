# Combat trigger contracts

Читай этот файл перед любой работой с combat triggers: добавлением нового триггера, weapon trigger, изменением log_builder, event_texts, или merge правил.

---

## Что такое trigger в этом проекте

Trigger — пассивное правило боя, которое срабатывает в определённый момент размена (ON_CRIT, ON_DODGE, ON_PARRY, и т.д.). В отличие от финтов (активный выбор игрока), триггеры активируются автоматически, если установлен соответствующий флаг в `TriggerRulesFlagsDTO`.

Крит в игре — это **не всегда x2 урон**. Крит может быть триггером, который накладывает bleed, stun, pierce, или даёт тройной урон. Это определяется набором активных trigger flags в `CritTriggersDTO`.

---

## Структура данных (паттерн — как feints)

### TriggerTechnicalDTO
Чистая логика. Читается только resolver-ом и log_builder-ом.

```python
class TriggerTechnicalDTO(BaseModel):
    trigger_id: str                               # e.g. "bleed_on_crit"
    event: str                                    # "ON_CRIT", "ON_MISS", "ON_DODGE", etc.
    chance: float = 1.0                           # вероятность срабатывания [0.0–1.0]
    mutations: dict[str, Any]                     # мутации контекста/результата
    applied_effect_ids: list[str]                 # явный список эффектов (для log_builder)
    token_grants_attacker: list[str]              # токены атакующему при срабатывании
    token_grants_defender: list[str]              # токены защищающемуся при срабатывании
```

`applied_effect_ids` заполняется **вручную** при определении триггера — не выводится из `mutations`. Позволяет log_builder-у разрешить имя эффекта без парсинга мутаций.

### TriggerCatalogEntryDTO
Полная каталожная запись (аналог FeintCatalogEntryDTO).

```python
class TriggerCatalogEntryDTO(CombatCatalogEntryDTO):
    key: str                      # "combat.trigger.crit.bleed_on_crit"
    technical: TriggerTechnicalDTO
    descriptive: CombatDescriptionDTO
```

### CombatDescriptionDTO
Стандартный класс из `common/descriptions.py`. Разбит по taxonomy (humanoid / beast). Пока реализуется только humanoid; beast_event_texts передаётся через `default_trigger_proc_event_texts()`.

---

## Catalog key convention

```
combat.trigger.{group}.{trigger_id}
```

| Group | Resolver stage / смысл | Примеры |
|---|---|---|
| `crit` | ON_CRIT | `combat.trigger.crit.bleed_on_crit` |
| `miss` | ON_MISS | `combat.trigger.miss.rage_on_miss` |
| `accuracy` | ON_ACCURACY_CHECK | `combat.trigger.accuracy.true_strike` |
| `dodge` | ON_DODGE | `combat.trigger.dodge.counter_on_dodge` |
| `parry` | ON_PARRY | `combat.trigger.parry.counter_on_parry` |
| `block` | ON_BLOCK | `combat.trigger.block.bash_on_block` |
| `control` | ON_CHECK_CONTROL | `combat.trigger.control.stun_on_hit` |
| `damage` | ON_DAMAGE | `combat.trigger.damage.execute_low_hp` |
| `style` | Любое событие (стиль боя) | `combat.trigger.style.offhand_attack` |
| `weapon` | Оружейный триггер | `combat.trigger.weapon.katana_bleed` |

**Важно:** `trigger_id` в `TriggerTechnicalDTO` — это имя флага в `TriggerRulesFlagsDTO` (например, `style_dual_extra`). Catalog key использует семантическое имя (например, `style.offhand_attack`). Они могут отличаться.

---
