# Game UI Lab 2

Новый игровой клиент: Vue 3 + JavaScript, Vite, Phaser 3. Python и TypeScript не используются. Старую game_ui_lab не удаляли: она остаётся образцом. В src ничего не переносили.

## Запуск

Нужны Node.js 22.12+ (проверено на24.19) и pnpm11.

```powershell
cd game_ui_lab2
pnpm install --frozen-lockfile
pnpm dev
```

Открыть http://127.0.0.1:8880/ . Старый образец — http://127.0.0.1:8879/.

```powershell
pnpm test
pnpm build
pnpm preview
```

Preview открывает собранный dist на8881. dist можно обслуживать статическим HTTP-сервером: Python/backend и соседние папки не нужны. Node нужен только для разработки/сборки/preview. Открытие index.html через file:// не поддерживается.

## Карта кода

- src/app/App.vue — композиция, не доменные расчёты; navigation.js — переходы и ограничения боя, gameClient.js — сценарий загрузки через gateway.
- src/features/character/ — Vue персонаж/инвентарь, навыки, билды и отдельные квесты; PR4 компоновка4×4.5.
- src/features/messages/ — Vue оболочка нижних вкладок. Источники чата и combat log независимы.
- src/features/places/ — арена, кварталы, окна услуг; готовые демонстрационные состояния строительства.
- src/app/BriefPage.vue — текущие текстовые намерения для диалогов/города/добычи/итога боя.
- src/integrations/ — подменяемые mock adapters. Источник ответов меняется здесь, компоненты не импортируют backend.
- src/mocks/ — локальные презентационные данные; формат пока не объявляется действительным production API.
- src/engine/createField.js — один Phaser Game, resize/scene lifecycle; renderers/ — визуальная геометрия/отрисовка, явно импортированные ES-модули.
- src/styles/ — текущая палитра и оболочка; менять по поручению, сохранять при несвязанных правках.
- public/ — выбранные локальные ассеты; все пути внутри сборки, нет runtime-доступа к старой Lab/src/rift_lab.

Ограничения и проверки: [migration-status.md](docs/migration-status.md). Вход для агентов: AGENTS.md / GEMINI.md и локальный SKILL.md.

Инструкции для работы: [текущие решения](docs/current-decisions.md), [точная карта файлов](docs/file-map.md). Позднее явное поручение владельца/художника обновляет решение в своей области; отражать его в current-decisions. Не откатывать существующие изменения оформления по старым миграционным заметкам. Проверять фактический runtime отдельно; выполненная правка не равна приёмке человеком.
