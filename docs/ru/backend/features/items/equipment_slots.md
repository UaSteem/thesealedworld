# Слоты экипировки и безопасный перенос сохранённых персонажей

## Активный контракт

В инвентаре 14 визуальных позиций: шлем, нагрудник, наручи, поножи, обувь; перчатки, пояс, плащ, амулет, серьги, два кольца; основная и вторая рука. `two_hand` остаётся механическим слотом двуручного оружия. Обычное двуручное оружие занимает обе визуальные руки, как раньше; при луке вторая позиция доступна для колчана.

Удалены equipment slot IDs `chest_garment`, `legs_garment`, `quiver` из обоих enum. Технические ID `gloves_garment` и `outer_garment` сохранены. Перчатки и плащ показываются слоем `accessory`, их type/материалы/аффиксы/числовая механика не меняются. Броня перчаткам не добавляется; наручи остаются `arms_armor`.

Луки `shortbow`, `longbow`, `composite_bow` сохраняют `two_hand`. Шесть баз колчана сохраняют base IDs, `type=ammo`, power, charge/effect payload и занимают `off_hand`. Колчан можно экипировать только при луке в `two_hand`. Исключение не действует для щитов, другого оружия или другого двуручного оружия. Экипировка щита/одноручного оружия снимает двуручное оружие по прежнему контракту; колчан при утрате лука переносится в рюкзак. При замене лука на другой лук уже надетый колчан остаётся. Снятие и намеренное выбрасывание лука также возвращают колчан в рюкзак.

Боевой снапшот считает колчан боезапасом основной руки: он не создаёт off-hand атаку, tactical dual-wield или off-hand damage/spread из собственного power. `ammo_effects`, `ammo_charges`, `ammo_charge_caps` по-прежнему относятся к `main_hand` лука.

`apron`, `shirt`, `tunic`, `pants` исключены из активного каталога и стартовых наборов. Броневые базы, включая `medium_leg_armor`, сохранены независимо от старого имени «штаны». Retired экземпляры сохраняют публичные названия и описания через read-only `retired_presentations.py`, включая historical aliases; этот ресурс не входит в active generation catalog и не раскрывает private unidentified lore. Retired экземпляры могут храниться в рюкзаке; повторная экипировка запрещена даже при ошибочно записанном valid slot. Новая генерация и выдача retired bases отклоняется действующим отсутствием базы в каталоге.

## Карта архива и сохранённого исходного материала

| Материал | Расположение | Активная загрузка |
| --- | --- | --- |
| 4 ordinary garment definitions | `archive/equipment_slots_2026_10_25/retired_bases.json` | Нет; JSON export с SHA256 в README |
| Оригинальные исторические family literals | `src/backend/features/monsters/catalog/families/{goblins,bandits,rats}.py` и другие frozen sources | Сохраняются как история, canonical starter catalogs их не импортируют |
| Исторические scenario rewards | `src/backend/features/scenario/resources/json/awakening_rift/archive/` | Архив сценария; в этой задаче не переписывается |
| Черновики будущих семейств | `tools/reserve/monsters/` | Резерв, не активные каталоги |
| Legacy IDs на границе переноса | `services/equipment_migration.py` в Inventory | Только explicit offline transform, не alias активной генерации/equip |

Monster active authored loadouts, shared equipment library и достижимые prepared payload slots согласованы с `off_hand`. Директории `.../quiver_training_quiver/` в shared library сохраняют историческое файловое имя; ключи index и slot внутри payload уже новые. Семейные подготовленные item IDs не перегенерируются, численные значения и seeds не перебрасываются. Frozen numeric digest tests используют явное обратное отображение только изменения формы слотов, без обновления исторических hash-констант.

## Offline dry-run

Инструмент принимает один экспортированный **полный InventoryRuntimeSession JSON** с `char_id`, `layout`, `by_id`. Он не читает БД/Redis, не принимает DSN и не реализует live SQL/Redis adapter. Active-character projection с неполным `by_id` не заменяет экспорт полного инвентаря.

```powershell
.\.venv\Scripts\python.exe -m tools.inventory.migrate_equipment_slots D:\exports\inventory-7.json
.\.venv\Scripts\python.exe -m tools.inventory.migrate_equipment_slots D:\exports\inventory-7.json --write-output D:\exports\inventory-7-migrated.json
```

Без `--write-output` выводится только отчёт с входным SHA256. С флагом создаётся новый файл эксклюзивно; исходный и существующие outputs не перезаписываются. Вложенные неизвестные поля сохраняются. Список item IDs и quantity проверяется на равенство; повторное преобразование результата не меняет документ. Переполнение визуальной вместимости не является основанием удалять предметы.

Правила переноса:

1. Все предметы из удалённых garment slots и known retired bases уходят в backpack. Исторические IDs `linen_shirt`, `wool_tunic`, `fur_pants` учитываются как retired. Экземпляры сохраняют item ID, количество, имя и механику; valid_slots retired экземпляров очищаются.
2. Сохранённый `quiver_training` явно становится `quiver_standard` на этой границе; quantity/charge/effect payload не меняются. Quiver mechanics.slot/valid_slots и runtime valid_slots становятся `off_hand`.
3. Legacy quiver из layout переносится в off_hand только при луке и свободной второй руке. При конфликте уже занятый off_hand не перезаписывается; колчан уходит в backpack. Далее несовместимые с two_hand предметы рук также уходят в backpack.
4. Старый лук, записанный в main_hand, переносится в two_hand, если слот свободен; иначе сам лук уходит в backpack. Это исправление сохранённого контракта, а не разрешение main_hand для новых луков.
5. Невложенные в layout carried экземпляры возвращаются в backpack. Dangling references, duplicate references, неизвестные equipment slots, несовпадение by_id key/item_id или не-carried storage вызывают отказ; исходный документ не изменяется.

Новые runtime actions и flush отклоняют legacy layout/mechanics с HTTP 409 до явного переноса. Это предохранитель от записи старых слотов обратно, а не автоматическая миграция рабочих данных.

## Безопасное применение к SQL и runtime

Порядок ниже — инструкция для отдельно порученного применения, в этой задаче он не выполнялся.

1. Включить обслуживание: остановить inventory actions, выдачи/перемещения предметов и фоновые inventory flush. Сохранить полный SQL и Redis inventory snapshot; dirty runtime сначала согласовать с SQL по прежнему контракту либо экспортировать и разобрать явно. Не удалять dirty Redis до сохранения его состояния.
2. Подготовить полные JSON snapshots всех carried items, включая expedition-held unsecured предметы и risk_run_id. Сравнить SQL placements и последний authoritative runtime layout; расхождения разобрать до трансформации. Не подставлять неполную AC projection вместо полного inventory.
3. Выполнить dry-run, проверить conservation IDs/quantity, retired backpack, bow/off_hand conflicts, отсутствие потерянных belt/backpack references. Сохранить исходный SHA256 и отчёты. Независимо проверить результат на копии данных.
4. Отдельно реализовать/проверить транзакционный SQL apply adapter с ownership и expected-state/версионной проверкой. Он должен обновить **и placements, и mechanics.slot/valid_slots/base_id** колчанов/старых луков, а также valid_slots retired экземпляров. `InventoryItemRepository.save_placements` пишет только placements и для этого недостаточен. Generated templates и сохранённые tier snapshots требуют отдельной инвентаризации; этот CLI их не мигрирует.
5. После успешного SQL commit при всё ещё остановленных writers заменить/инвалидировать согласованные runtime inventory caches и пересобрать AC items projection из мигрированных данных. Не давать старому Redis flush перезаписать SQL. Пересобрать GS, боевые/витальные проекции; активные старые боевые snapshots не переписывать в ходе боя — дождаться безопасной границы.
6. Проверить representative персонажей: bow+quiver, bow→bow, bow→shield/двуручное/одноручное, unequip/drop, retired одежда в рюкзаке, сохранность всех ID/quantity, стартеры и relog. Только затем возобновить writers и actions.

Предыдущая задача naming IDs имела собственную replacement-only границу. Этот CLI явно покрывает только retired garment aliases и quiver_training; остальные старые base IDs (например старые armor IDs) требуют отдельной согласованной миграции naming задачи до применения нового контракта.

## Ограничения проверки

Изменения не применялись к рабочим/production данным. Live SQL migration, Redis rollout, browser/runtime visual acceptance и полный `tools/dev/check.py` не выполнялись. Изменения game_ui_lab, его архива, CSS, canvas, размеров, чата и сцены исключены.
