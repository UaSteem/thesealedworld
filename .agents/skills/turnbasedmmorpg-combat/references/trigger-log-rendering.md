## event_texts для триггеров

`CombatEventTextSetDTO` имеет специальные поля для триггеров (в дополнение к стандартным `use`, `hit`, `crit`, etc.):

| Поле | Когда используется |
|---|---|
| `proc` | Generic fallback — любое срабатывание |
| `hit_proc` | Trigger сработал при попадании (ON_HIT / ON_CHECK_CONTROL) |
| `crit_proc` | Trigger сработал на крите (ON_CRIT) |
| `miss_proc` | Trigger сработал при промахе (ON_MISS) |
| `dodge_proc` | Trigger сработал при уклонении (ON_DODGE) |
| `parry_proc` | Trigger сработал при парировании (ON_PARRY) |
| `block_proc` | Trigger сработал при блоке (ON_BLOCK) |
| `apply_effect` | Стандартное поле — наложение эффекта |
| `token_gain` | Получение токена от триггера |
| `counter` | Контратака активирована |
| `extra_strike` | Дополнительный удар |

**Порядок разрешения в log_builder:** `{event}_proc` → `proc` → `{event}` (fallback на стандартное поле).

Переменные шаблонов: `{source}`, `{target}`, `{trigger}` (display_name), `{effect}`, `{damage}`, `{token}`.

Используй `default_trigger_proc_event_texts(name)` из `common/descriptions.py` для beast_event_texts или как заглушку.

---

## Merge rules (когда триггер отдельная строка)

| Тип триггера | Примеры | Отдельная строка лога? |
|---|---|---|
| Effect applicator | `bleed_on_crit`, `stun_on_crit`, `stun_on_hit`, `bleed_on_hit` | **Нет** — вплетается в summary |
| Tactical pipeline flag | `true_crit`, `piercing_crit`, `unblockable_crit`, `heavy_strike_on_crit` | **Нет** |
| Token grant | `rage_on_miss` | **Нет** — видно через badge |
| Accuracy / evasion override | `true_strike`, `style_ranged_perfect_backstep`, `style_2h_ignore` | **Нет** |
| Counter-attack | `counter_on_parry`, `counter_on_dodge` | **Да** — генерирует собственный обмен |
| Extra strike | `style_dual_extra`, `bash_on_block` | **Да** — собственный обмен и damage |

Новые триггеры типа counter / extra_strike добавлять в `_SEPARATE_LINE_TRIGGERS` в `log_builder.py`.

---
