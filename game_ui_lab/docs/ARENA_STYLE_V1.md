> Исторический вариант стиля. 26.10.2026 владелец заменил фон на рисованный
> `static/game/assets/places/painted/arena-hall.jpg`. Этот текст и его промпт относятся
> к прежней генерации; PNG и исходная копия документа сохранены в
> `archive/game_ui_migration/2026-10-26/retired-place-art/`.
> Актуальный набор: `static/game/assets/places/painted/README.md`.

# Арена: фон вестибюля V1

Статус: пробный образец композиции и стиля; не утверждённый стиль всех городов.
Ассет: `static/game/assets/places/arena-hall-v1.png`.
Генерация: встроенный imagegen, 2026-10-26. Изображение сохранено без изменения.

## Правила, согласованные с владельцем

- Новые города строят фракции. Это не обязательные руины и не ремонт древних зданий.
- Средневековые оружие и быт; архитектура может выражать освоенные древние знания через геометрию и конструкции.
- Уточнение владельца: уровень города открывает типы и количество кварталов; внешние городские тайлы получают дизайн по уровню развития. Внутренний интерьер пока один на тип сцены. См. docs/adr/0002-faction-city-district-progression.md.
- Золото относится к интерфейсу. Не делать архитектуру золотой ради совпадения с UI.
- Арена — городское здание для боёв и турниров, включая будущие межфракционные встречи.
- Персонаж внутри сцены не перемещается. Объекты помещения становятся областями наведения и действий.

## Визуальный рецепт этого варианта

Сдержанная тёмная фэнтезийная архитектура: серый камень, тёмный дуб, чёрное кованое железо, светлые и бордовые ткани. Тёплый свет фонарей и прохладный дневной свет. Обжитое действующее общественное здание. Живописный реализм, ясные силуэты интерактивных объектов, спокойный передний план. Ракурс из одной неподвижной точки посетителя, не вид сверху.

Бордовые ткани, конкретные гербы, статуи и масштаб здания — результат этой генерации, а не утверждённые обязательные признаки мира.

## Точный отправленный промпт

```text
Create one wide landscape 16:9 high quality dark fantasy RPG environment background, a readable interactive adventure game scene, no UI, no text, no labels, no grids. View from a stationary visitor at eye height into a newly built medieval city arena's grand entrance hall. Not abandoned, not ruins, not futuristic. Civilization using ancient geometric architectural knowledge but medieval weapons and everyday materials. Restrained slate gray stone arches, dark oak beams and counters, black wrought iron, cream banners and a few deep burgundy textiles. NO gold architecture, NO shiny gold ornament, NO technology screens, NO neon. Warm lantern light contrasted with soft cool daylight, painterly realistic game concept art, carefully controlled crisp detail, moody but legible shadows. Composition explicitly: lower left foreground small oak registrar counter with a seated medieval clerk and ledger, centered around normalized x .22 y .67; left middle background large open arched doorway to a duel practice hall x .29 y .38 with distant silhouettes, middle large monumental arch doorway x .51 y .35 leading to main arena with daylight and hint of arena sand, right middle a clearly recognizable wooden tournament notice board with pinned parchment (no readable writing) x .78 y .48; far right foreground curved stairs or arch to exit at x .91 y .75. Upper hall soaring stone vault and cloth pennants. Keep the foreground floor broad, relatively quiet, and accessible. Strong object silhouettes so they can become hover hotspots. Unified physical perspective, no collaged panels. This is a functional civic building for organized duels and inter-faction tournaments, not a dungeon. Full bleed composition, single finished environment plate.
```

## Как повторять направление

Прикладывать `arena-hall-v1.png` как визуальный референс вместе с правилами выше.
Для другого помещения заменять композиционную часть (объекты и назначение), сохраняя материалы, характер изображения и освещения. Один текстовый промпт не гарантирует идентичный стиль или геометрию; результат сравнивать с референсом в игровом размере.
