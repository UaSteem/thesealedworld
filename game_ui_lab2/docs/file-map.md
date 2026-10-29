# Карта файлов Lab2

| Задача | Владелец |
| --- | --- |
| Vite/dev8880/build/preview8881, зависимости | package.json, pnpm-lock.yaml, vite.config.js, index.html, start.ps1 |
| Сборка Vue/общие CSS | src/main.js, src/styles/obsidian-bronze.css, shell.css, workspace.css, client.css |
| Оболочка и композиция | src/app/App.vue |
| Переходы, исходный экран, запреты боя, возврат | src/app/navigation.js |
| Загрузка моделей/ошибки через gateway | src/app/gameClient.js, src/integrations/mockGameGateway.js |
| HUD ресурсов/аватар | src/app/PlayerHud.vue |
| Персонаж,4×4.5, сетка/фильтры/осмотр, навыки/галочка/билды | src/features/character/CharacterPage.vue, character.css |
| Квесты | src/features/character/QuestPage.vue |
| Группы модификаторов и значение | src/features/character/ModifierGroups.vue, src/integrations/modifierSheet.js |
| Mock персонажа/инвентаря, явный состав пользовательских модификаторов | src/mocks/character.json, inventory.json, player-modifier-layout.json; правила проекции см. current-decisions.md |
| Сообщения/нижние вкладки | src/features/messages/MessagePanel.vue |
| Источник чата / отдельно источник журнала | src/integrations/mockChatGateway.js, mockCombatLogGateway.js, mockMessageGateways.js |
| Арена/кварталы/окна/готовые состояния | src/features/places/PlacePage.vue, placeData.js, constructionFixtures.js |
| Текстовые концепции остальных страниц | src/app/BriefPage.vue, src/mocks/page-briefs.json |
| Vue → один Phaser/resize/destroy | src/app/GameField.vue, src/engine/createField.js |
| Рифт/зум/crop/геометрия | src/engine/renderers/rift-scene.js, rift-renderer/; public/ui-data/rift-preview.json |
| Боевое поле/анимации/управление/инспектор | src/engine/renderers/combat-scene.js, combat-controls.js, target-inspector.js, hex-layout.js |
| Предзаданный ответ боевого mock | src/integrations/mockFieldGateway.js |
| Каталог визуальных ресурсов Phaser | src/engine/assets.js, public/ui-static/game/assets/catalog.json |
| Активные картинки/шрифты | public/ (включается в dist) |
| Сценарные/gateway тесты | src/app/gameClient.test.js, src/integrations/*.test.js |
| Поставка/хеши текстур | tools/distribution.test.js |

HTML/CSS-окно меняется в Vue-компоненте, не рисуется заново внутри Phaser. Поле/камера не реализуются вторым canvas. App.vue только компонует; форматы данных и источники не прятать в шаблоне.

Пути выше относятся к game_ui_lab2. Старые app.py/templates/Jinja/boot.js другой Lab в этот клиент не подключаются. public — локальная поставка, без обращений к соседним папкам при работе браузера.
