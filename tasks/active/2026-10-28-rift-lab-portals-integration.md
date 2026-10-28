# Интеграция порталов Vortex и Shattered в rift_lab взамен старого спрайтшита

Дата: 2026-10-28.
Задача: Подключить два новых варианта порталов (Vortex и Shattered Reality) в лабораторию Рифта (`rift_lab`) взамен старого `portals_spritesheet.png`. Настроить конфигурацию и рендерер так, чтобы любой другой агент/ИИ чётко понимал, как активировать портал, а всю остальную матрицу артефактов оставить на хранении в резерве.

## Контекст и исходное состояние
- В `rift_lab` сейчас входной портал (`kind: "portal"`) рендерится через `static/population/encounters.json` (`animations.portal`), который ссылается на старый растровый спрайтшит `/static/images/rift/portals_spritesheet.png` (кадры 128×128, 8 кадров).
- Новые чистые RGBA-спрайты высокого разрешения уже подготовлены и лежат в `rift_lab/static/population/portals/`:
  - `portal_vortex_512_rgba.png` (Вихревой разлом)
  - `portal_shattered_512_rgba.png` (Кристаллический разлом)
- Врата игроков (`portal_player_gate_*`) остаются на хранении в `tools/assets/player_portals/`.
- Требуется использовать **только Vortex и Shattered**, без остальных вариантов.

## Требования задачи
1. **R1. Конфигурация в `rift_lab`**:
   - Обновить `encounters.json` (или специализированный конфиг порталов в `rift_lab/static/population/`), зарегистрировав оба варианта: `portal_vortex` и `portal_shattered`.
   - Задать точные параметры посадки на гекс (anchor x=0.5, y=0.75..0.8, display_size под регулярный гекс $222 \times 256$ px, тинты сложности).
2. **R2. Поддержка в `population-renderer.js` и `population-gallery.js`**:
   - Научить рендерер отображать новые варианты порталов (как статические RGBA-спрайты с эффектом вращения/пульсации Phaser или прямым рендером) при наличии `portal_variant` в layout/настройках.
   - Обеспечить обратную совместимость или дефолтный выбор (например, `portal_vortex` по умолчанию с возможностью переключения на `portal_shattered`).
   - Добавить отображение обоих вариантов в галерею населения (`population-gallery.js` / витрина объектов).
3. **R3. Документация для других агентов / ИИ**:
   - Оформить внятный интерфейс активации в `rift_lab/static/population/portals/README.md` (или `rift_lab/README.md`): как вызвать, какие поля в JSON передавать (`object.variant: "vortex" | "shattered"`), какие слои и параметры глубины используются.
4. **R4. Сохранение резерва**:
   - Не трогать резерв `tools/assets/player_portals/` и архив.

## План работ
1. Проверить текущую обработку `object.kind === 'portal'` в `rift_lab/population.py` и `population_planning.py`.
2. Добавить регистрацию вариантов порталов в `rift_lab/static/population/encounters.json`.
3. Модифицировать `population-renderer.js`, чтобы для `kind: 'portal'` поддерживались варианты `vortex` и `shattered` из `portals/`.
4. Обновить витрину `population-gallery.js`, чтобы оба варианта были видны в галерее.
5. Написать краткое руководство по активации для агентов в `rift_lab/static/population/portals/README.md`.
6. Проверить в браузере / тестами.
