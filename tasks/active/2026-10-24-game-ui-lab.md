# Отдельная лаборатория игрового интерфейса

Дата: 2026-10-24. Продолжение работы над оболочкой интерфейса; сохраняется выбранный пользователем режим с независимым ревизором. Статус reviewed-awaiting-acceptance; текущая гексовая композиция ожидает визуального принятия владельцем.

Запрос: «так как мы сейчас разрабатываем другие страницы от рифта можно это выделить в отдельную пока папку и мы подумаем как нарисовать условно внутри Phaser наш бой».

## Требования

R1. Создать отдельную папку game_ui_lab для будущих центральных игровых экранов. Rift Lab и runtime не менять. done/pass (ui_lab_review).
R2. Перенести копию визуальной основы Rift Lab: большая постоянная HTML-панель персонажа слева, справа Phaser-поле над HTML-чатом, Adventure из общих токенов. Не переносить генератор/сцену рифта и lab debug tools. done/pass (ui_lab_review).
R3. Предоставить локально открываемую пустую сцену Phaser для дальнейшего обсуждения боя, без реализации серверной боевой механики. Персонаж/чат — явные mock fixtures, без БД/Redis/API/авторизации. done/pass (ui_lab_review).
R4. Сохранить происхождение скопированных исходников (пути/SHA/характер изменений), отдельную инструкцию запуска и записать ещё не утверждённые варианты рядов/журнала боя как предложения. done/pass (ui_lab_review).
R5. Проверить изолированность импортов и HTTP paths, реальный Phaser canvas, desktop 2560×1440/1920×1080/1366×768, чат и browser errors; независимая проверка. done/pass (ui_lab_review).

## План

1. Создать минимальный независимый HTTP/Jinja adapter, локальные templates/static/fixture, использовать общие runtime assets (шрифты, Phaser, изображения и theme.css) по явным путям.
2. Скопировать только необходимые части оболочки с provenance. В центре — заготовка сцены, а не готовый бой. Кнопка рюкзака обозначена как будущая, никаких игровых команд не отправляет.
3. Проверить unit/static/HTTP и браузерные desktop состояния; показать отдельный URL. Режим independent review. Не коммитить и не деплоить.

## Будущее обсуждение боя

Предложение владельца: дальний ряд — ещё не действовавшие противники; средний — действовавшие против игрока, ожидающие размена; ближний — текущий противник. Для союзников обдумать два/три ряда. Анимации показывают авторитетное состояние, а не создают новые правила. Журнал боя может быть отдельной вкладкой в нижней области рядом с чатом. Эти решения пока не реализуются и не считаются утверждённой серверной механикой.


## Выполнение и проверки

Создана отдельная game_ui_lab с app.py/templates/static/data/README/COMBAT_NOTES/PROVENANCE. Shared assets: runtime theme.css, fonts, Phaser и изображения. Python imports ограничены stdlib и Jinja2; игровой app/настройки/генератор не импортируются. Во время этой задачи rift_lab и runtime-файлы не менялись. Четыре копии оболочки/fixture записаны с SHA исходников и адаптированных копий; хеши сверены ведущим. Варианты боя записаны предложениями, сцена пока без юнитов/боевой логики.

Локальный запуск `.venv/Scripts/python.exe -m game_ui_lab.app --port 8879`, привязка127.0.0.1, сервер оставлен для просмотра. 10focused tests pass0.26s (isolation/path traversal и Node resize adapter), Ruff pass. Первичная browser-проверка обнаружила2дефекта: scale.refresh не менял размер Phaser при изменении контейнера; hidden divider сдвигал чат в нулевой gridrow. Исправлено: Scale.NONE+явныйresize из ResizeObserver с защитой повторного размера, явные gridrows1/2/3. Resize test RED на старой реализации → GREEN на исправленной.

Повторная проверка Edge:3840×2160,2560×1440,1920×1080,1366×768,1366×650. Активная настоящая Phaser.Scene/canvas; JS errors0, failedassets0, brokenimages0, horizontaloverflow0. Проверены collapse/reopen, увеличение canvas, keyboardEnd/Home divider, локальный вводстроки с HTML-тегами как textContent и отсутствие /game/ либо /api запросов. Свёрнутый чат ровно40px во всех5случаях. Артефакты tmp/game_ui_lab/browser-report.json и PNG; script tmp/game_ui_lab_check.cjs. Ведущий визуально посмотрел1920×1080.

Независимая проверка ui_lab_review: pass; исходники, provenance,10тестов и browser-артефакты проверены, оба browser-дефекта закрыты. Существенных замечаний нет; принятие пользователем отдельно. Это локальная лаборатория, не перенос в runtime и не проверка production. Игровые данные/деплой/коммиты не менялись.


## Прототип боя — поручение 2026-10-24

Пользователь: «сделаем такой прототип в game_ui_lab: два ряда сверху и снизу, большая цель в центре, меч справа внизу. Без журнала, с быстрой сменой цели и анимацией урона и эффектов на карточке вернувшегося противника ... кнопочку в хедере ... генерировать сессию боя».

Уточнения из обсуждения: поле с текстурой лесной земли, без тактического перемещения; карточки с аватаром на подсвеченных гексах, сверху HP/EN/CONC. Центральный гекс/карточка вдвое по ширине/высоте относительно обычного. Верхние2ряда противников и нижние2союзников показывают очередь/намерения, не новые правила дальности. Внутри Phaser нижняя самостоятельная зона управления: меч справа,3фиксированных места финтов и постоянные виды боевых токенов со счётчиками, способности левее/по центру. Журнал НЕ делать ни на поле, ни отдельной вкладкой чата. Допускается до10видимых противников +счётчик остальных. Позиция меча справа для первого варианта.

R6. Реализовать эту визуальную композицию в Phaser в game_ui_lab, сохранив HTML-персонажа/чат. Карточка выбранной цели не дублируется в верхних рядах. done/pass (battle_proto_review).
R7. Быстрый выбор/смена цели, атака немедленно переключает следующую; отложенный demo результат по actorId+sessionId+exchange/eventId обновляет/анимирует именно прежнего противника. Повторы события не проигрывать; старый результат после новой сессии игнорировать. done/pass (battle_proto_review).
R8. В header кнопка генерации локальной mock-сессии; никакого настоящего backend боя/сохранения/награды. Демо-источник явно обозначен. Реальный HTTP/API/боевые формулы не изменяются. done/pass (battle_proto_review).
R9. Fixed token kinds сверить с текущим исходником, не угадывать7/8. Найден COMBAT_TOKEN_CATALOG: tempo,hit,crit,dodge,parry,block,pressure,blood,gift (8обычных+gift). Использовать их значки как static assets, без импорта backend/frontend application. Анимации урона/блока/лечения/эффектов иллюстративные. done/pass (battle_proto_review).
R10. Unit-проверки demo state событий, регенерации и dedup; browser реальные карточки/целевой HUD/быстрая атака с запоздалым событием, desktop1366×768/1920×1080/2560×1440+ и resize/collapse, assets/errors, независимая ревизия. done/pass (battle_proto_review).

План: отдельная чистая JS demo-модель +данные → Phaser board/HUD → header generation и документация → unit/браузер и визуальная доводка → independent review. Запрос генерации сессии трактуется как локальная демонстрационная сессия в изолированной лаборатории; production создание боя не поручено. На узкой доступной высоте адаптировать размеры и раскладку, не перекрывать controls/карточки. Runtime/RiftLab, game CSS/themes, боевые базы и данные остаются вне scope.


## Реализация прототипа боя R6–R10

Выполнение done; independent review battle_proto_review PASS, существенных открытых замечаний нет. Сцена больше не пустая. Созданы изолированные demo-model.js и battle-layout.js; scene.js рисует всё поле/HUD в Phaser. HTMLheader содержит генератор 10/20/30 противников. Grass texture скопирована с исходным SHA в provenance. Никакие runtime/RiftLab/backend-файлы этой задачей не изменялись.

- Два верхних и два нижних ряда, портретные карточки (голова/верх тела, а не фигурки), три полосы сверху, выбранная цель2× и не дублируется. Лесная земля статична, тактического перемещения нет. Нижний HUD: меч справа,3финта,9постоянных валют,4демо-способности. Журнала нет ни на поле, ни в чате.
- Атака синхронно выбирает следующего противника; fake-response задержан480–660ms. Событие содержит session/event/exchange/actor IDs; модель применяет канонический pending результат один раз. Новый sessionId сбрасывает pending, старые ответы игнорируются. До128pending; сцена отменяет таймеры/FX при регенерации. Результаты привязаны к карточке, ресурсам и эффектам прежнего участника. Намерения союзников в snapshot вычислены относительно выбранного врага через mock actedAgainstIds.
- Отрисовка ограничена10противниками включая цель; остальные показаны счётчиком. Возвращённый/получивший результат actor повышается в приоритете видимости. Невидимые исходы временно агрегируются по actorId, последняя подпись эффекта сохраняется; нет UI-журнала. Мёртвая карточка задерживается кратко для последнего урона. Приоритет очереди и величины иллюстративные, не утверждённая серверная модель.
- Левые HTML HP/EN/CONC синхронизируются с героем демо-сессии; остальные стартовые характеристики/аватар остаются fixture. Это не реальный аккаунт.

### Проверки исполнителя

13focused tests PASS0.66s (`pytest tests/game_ui_lab --no-cov --basetemp=tmp/pytest-battle-final`), Ruff и source diff-check pass. Demo-model тест проверяет мгновенную смену, actor/session matching, повторы, reset, out-of-order, bounds,128pendingcap, расходы способностей и target-dependent allyrows. Layout tests проверяют2×, границы/центральный проход и regression20returnevents под полной pin-очередью. Существующий resize adapter test сохранён.

Browser Edge на реальном локальном8879:3840×2160,2560×1440,1920×1080,1366×768,1366×650. На каждом: реальный clickAttack → immediateTargetSwap без ожидания результата → lateFX на прежнем actor; вторая быстрая атака; regeneration до старого ответа → новая сессия/HP не изменились;30противников →10видимых;20мгновенных атак →20уникальных FX-records, cleanup transient0; collapseChat →canvasрастёт, сессия сохраняется. JS errors0, failedassets0, game/API requests0, overflow0. Отчёты `tmp/battle_proto/interaction-report.json`, компактный summary.json, скрипт tmp/battle_proto_interactions.cjs. PNG final/outcome-*; ведущий посмотрел1920×1080 и1366×768.

После финального bridge отдельно проверены HTML-ресурсы/трата8EN/позднее лечение: `hero-report.json`, `hero-healing-1920x1080.png`; errors0. Все оригинальные/копированные SHA в PROVENANCE проверены, включая лесную текстуру.

В процессе browser/peer проверки исправлены: SVG чёрные квадраты (load.svg explicit128), разрывы альфа-текстуры пола (cached centralcrop), fullbody силуэты вместо avatarcrop, числовые полосы, сортировка возвратных акторов по recency (первоначально10-й быстрый результат мог попасть на скрытого), преждевременный snap анимаций при lateFX, очистка transient/timers и расходящиеся ресурсы слева. Поздние анимации остаются прототипными, короткая высота650 даёт компактные подписи. Это не production/integration/full-project gate. Коммитов/деплоя/изменения игровых данных нет.


Независимый ревизор battle_proto_review: PASS R6–R10; модель/asset paths/layout/renderer,13tests и browser артефакты проверены. Закрыт его дефект потери анимации под полной очередью pinned-карточек; подтверждены20FX из20событий и финальная согласованность HTML-ресурсов. Существенные утверждения итогового ответа сверены; ограничение мелких подписей650px остаётся явно прототипным. Статус reviewed-awaiting-acceptance, пользовательское принятие отдельно.


## Уточнение и исправление гексового прототипа (2026-10-24)

Пользователь отверг синий тон поля, квадраты/мелкие контуры вместо текстурированных гексов, сплошной прямоугольный фон из grass и размытое увеличение. Его последняя схема: сохранить наклонную сетку Rift Lab; попробовать слева направо — игрок в центре левой ромашки, союзники вокруг, текущая цель впереди справа, дальше ожидающие размена и ещё дальше не выбравшие действие. Большая цель/площадка должна рисоваться из исходного материала под конечный размер, а не растягиваться из малого растра. Предыдущие R6 верх/низ заменены этой новой композицией; это изменение владельца, не выбор исполнителя. Журнал по-прежнему запрещён.

R11. Перестроить поле слева направо на настоящих Rift Lab hex coordinates/perspectiveY=.65 и grass material с исходными рисунком/цветами. Игрок/союзники на левой ромашке, выбранная цель впереди справа, затем acted/waiting-группы; связанные пустые гексы образуют площадки. done; проверено исполнителем и ревизором.
R12. Убрать сплошную TileSprite-заливку/синюю shade и квадратные подставки поля. Границы натуральных гексов должны читаться. Тёмное пустое пространство вне площадок допустимо как у Rift Lab. done; проверено исполнителем и ревизором.
R13. Исправить резкость: terrain/crop портретов формируется непосредственно из оригиналов под фактический размер и DPR; текст рисуется в конечном экранном размере и повышенной resolution, координаты округлены, без постоянно дробно масштабируемых карточек. Увеличенная цель не получается растягиванием маленькой текстуры. done; проверено исполнителем и ревизором.
R14. Сохранить работающие демо-события, быстрые цели, регенерацию/дедуп/FX, HUD справа/снизу и локальный чат; настоящий backend/Rift Lab/runtime не менять. done; проверено исполнителем и ревизором.
R15. Unit geometry/native-size guards, browser screenshot просмотр до отчёта, DPR1/2 и desktop1366/1920/2560+, повтор async/overflow/reset; independent reviewer. done; проверено исполнителем и ревизором.

План: сохранить отвергнутый эскиз отдельно → использовать копию чистого RiftTerrain helper (с provenance), не генератор → новый layout/hex material/cards с явными группами → desktop/DPR visual+interaction checks → независимая проверка. Направление первой пробы: игрок слева, противники справа; конкретная геометрия ромашки/мест проверяется визуально. Размеры гексов задаются геометрией и физическим разрешением текстуры, а не upscaling готового128px tile.


### Результат исправления R11–R15

Реализована проба слева направо. Исходный grass2048² и точная копия RiftTerrain helper формируют наклонные гексы с perspectiveY=.65; отдельная2Rплощадка цели генерируется напрямую в нужном физическом размере. Нет TileSprite/синего покрытия, контейнеры карточек scale1. DPR1/2: backing canvas/CSS соответствует DPR, клики проверены. Портреты и текст генерируются под конечный размер. Три полосы над аватаром. Нормальная карточка и её hitarea55px при минимальном шаге58.54px; подписи цели разнесены. Все занятые места имеют ground. Строгие acted/waiting-группы имеют собственную вместимость: при переполнении видимых может быть меньше10, остальные в счётчике. Приоритет позднего результата сохраняет возвратного участника в своей группе. Это компоновочный прототип, не утверждённая серверная очередь.

15focused tests PASS0.94s, pytest tests/game_ui_lab --no-cov --basetemp=tmp/pytest-hex-final. Browser Edge:2560×1440,1920×1080,1366×768DPR1 и1366×768DPR2. Реальный clickAttack→мгновенная смена→lateFX; reset30 до старого ответа не меняет новую сессию;20burst→20уникальныхFX; transientcleanup0; resize чата сохраняет сессию; JSerrors0, failedassets0, APIrequests0. Отчёт tmp/battle_proto/hex-interaction-report.json, скрипт tmp/battle_hex_interactions.cjs. Ведущий просмотрел финальный1920×1080 и DPR2; предыдущая отклонённая проба сохранена в archive/game_ui_lab_trials/2026-10-24-before-rift-hex-revision.

Независимый hex_revision_review нашёл и потребовал исправить пересечение CONC/имени, увеличенные области клика и смешивание групп при overflow. Исправления внесены и повторно проверены. Изменения изолированы в game_ui_lab/tests/docs/archive; runtime, backend и RiftLab текущей правкой не менялись. Данные/события остаются mock. Коммит/деплой не выполнялись.


## R16 — только карта, новая проба

Предыдущий вариант отвергнут владельцем. Сделать вертикальную (вершиной вверх) сплошную гексовую сетку минимум15×15, одноцветную вместо текстуры. Фиксированная карта не зависит от участников. Без целей, карточек, HUD и боевых controls. Без внутренних вырезов и чёрных участков в игровом окне. Оболочку персонажа/чат сохранить. План: отдельная простая map-only сцена, отключить demo scripts/controls, browser screenshot и resize, независимая ревизия. pending/pending.

R16 реализация: done. Только map-scene.js: фиксированные32×32=1024ячейки pointy-top, одинаковая сплошная заливка, без текстур/actors/cards/HUD/controls. Внешняя граница карты за viewport, камера показывает центральный участок; resize меняет визуальный масштаб, не состав карты. Старые боевые исходники сохранены отключёнными. Browser1366×768DPR1 и2560×1440DPR2 errors0, screenshotsmap-only-*.png просмотрены ведущим; chatcollapse без ошибок. App/legacyresize10testsPASS0.32s; новыйresize проверен браузером. Independentreview pending.
R16 независимый map_only_review: pass, исходники и оба screenshot проверены, node syntax pass, открытых замечаний нет. Browser assertions выполнены ведущим, ревизор их не перезапускал. Статус reviewed-awaiting-acceptance; визуальное принятие владельцем отдельно.

R17 уточнение владельца:32×32 было лишним решением исполнителя. Уменьшить фиксированную сетку до15×15, увеличить ячейки; показывать центральный участок, не пытаться вместить всю карту. План: изменить side и подпись, browser screenshot, независимая проверка. done/check pending.
R17 проверка ведущего: browser1366×768DPR1 и2560×1440DPR2,225cells,errors0; радиус52.22/109.64px вместо20.52/43.07px (увеличение2.55×). Screenshot1366 просмотрен: видна центральная часть, ячейки крупнее, чёрных участков нет.
R17 independent map_only_review pass: код/подпись/README/screenshot/syntax, замечаний нет. reviewed-awaiting-acceptance.

## R18 — карточки в подставках на конечном поле

Запрос владельца: нарисовать обсуждённое в game_ui_lab, пять гексов в ширину, фон рифта, карточки в настольных подставках, HP без цифр. Демо без WebSocket, с независимым ревизором. Требования: pointy-top наклонённая конечная площадка целиком, одинаковый размер ячеек при изменении количества; boundedrows/overflow+N, приоритетactedagainstviewer затемnearestdeadline; игрок/цель соседние вцентре, врагивверху/союзникивнизу; контрастная подставка/вертикальный неприплюснутый портрет, толькоHPяркий+сераяпотеря; панельподробностей бездублированияпортрета (hoverpreview/clickpin); компактныйheader. Будущийтранспорт отдельный, никакихWS/backend/runtime/Riftchanges. Рельефтерриториибудущий, текущийполодноцветныйнафонеRift. План: scene/layout исполнитель, parent shell/detail/docs; browserdesktopDPR/hover/pin/HP/overflow; независимаяревизия. pending/pending.

R18 реализация done: standee-layout/map-scene/actor-details + компактныйheader32px, точныйriftvoidbg_v3.webp. Пятьстолбцов, pointy-top perspective.65, радиус43..60 поframeширине, неизмененотчислаучастников. Перваяпробаимеет5рядов/3компактных; расширение7/9рядовпока не реализовано. Наобычномframe6врагов4союзника, приcompact2врага+цель/герой+2союзника; фиксированныйдемоtotal840/160, +Nсоответствуетвидимым. Этоиллюстрация1000участниковс10fixtureакторами, НЕпроверканагрузки1000. ПриоритетactedAgainstViewer затемdeadline. ПортретыкадрируютсяквадратноизоригиналовподDPR, подставкисбортиком/тенью, толькоHPбарбезцифр; состояниеотметкой сбоку. ПодробностиотдельнойDOMпанелью безпортрета;hoverpreview/clickpinвключаясоюзников. Деморазменциклdamage/dodge/miss, потерянныйHPсветлеетпереходитвсерый, безтранспорта/backend.

16focusedtestsPASS0.89s pytest tests/game_ui_lab --no-cov --basetemp=tmp/pytest-standee-final; большаячастьстарыхтестов покрываетсохранённыйотключённыйdemo, новыйstandee_layoutпроверяетpriority/radius/rowfit. BrowserEdge tmp/standee_check.cjs:1366×768,1920×1080,2560×1440DPR2,1920×768. Реальныйhover/clickenemy/allypin, HP-12, chatcollapse/resizeradiusconstant; errors0,assetsfailed0,APIrequests0. Report tmp/battle_proto/standee-report.json. ДополнительноdividerEnd1366:3rows,R60,6cards,height373,границыкарточекпомещаются. Screenshotstandee-compact.png иstandee-1366-768-dpr1.png просмотреныведущим. Stageминимум300черезchatbounds. Independentreviewpending.
R18 standee_review: блокирующих замечаний реализации нет; проверены source/base+compact screenshots и browser report/script, сам browser не перезапускал. Исправлены allypin и compactheight; README полностью актуализирован, COMBAT_NOTES явно помечает старую историю. reviewed-awaiting-acceptance. Коммит/деплой не выполнялись.

R19 уточнение: игрок и цель наискосок на соседних гексах соседних рядов, не в одном ряду. Исправить только позиции текущей пары, browser screenshot и независимый просмотр. done/checkpending.
R19: цельrowmiddle-1col2, игрокrowmiddlecol2: вертикальнососедниеряды со смещением0.5горизонтальногошага, тоестьсоседниегексы. Чтобыверхниекарточкинезакрывалитекущуюцель, topoccupiedslots0/1/4, остальныев+N. Browser4caseshover/pin/HP/resize/DPR PASS errors0; screenshot1366просмотрен.

R20 исправление по владельцу: увеличить гексы, чтобы карточка с подставкой полностью помещалась внутри своего гекса; изображения персонажей отображать целиком без sourcecrop, с сохранением пропорций. Сохранить диагональную пару соседнихрядов. План: пересчитатьрадиус/наклон/anchorиrowcapacity, fullimagecontain, polygoncontainmentcheck + screenshotdesktop + независимыйревизор. pending/pending.

R20 done/pass: радиус76..92 (77при995frame), perspective.95; fitучитываетширинуивысотуфрейма, нечислоучастников. Полноеизображениерисуется5argdrawImageuniformcontainв64pxcanvasбезsourcecrop. Карточкаперемещенавнутрьhex: anchorцентр+37; polygoncontainmentпроверенoutlinecornersи24точкамиbaseellipse (castshadowисключён). Диагональсохранена. Chatminstage410, фактически410приmaxchatиfield365.75на1366×768. 16focusedtestsPASS1.13s. Browserfourcases1366×768,1920×1080,2560×1440DPR2,1920×768: polygonpoints/hover/pin/HP/resizePASSerrors0. Screenshot1366просмотрен. Независимыйstandee_review R20PASSисходники+1366/2560screenshots; browserreportизучен,самнеперезапускал. reviewed-awaiting-acceptance.

R21 новаягеометрияпообсуждению: основапрямоугольник3ряда×5гексов, продолжениесправасверхуивлевуснизу, противоположныесвободныеуглыподвыбранногоучастника/управление. Запрос: «сделай такуюсетку». Менятьгеометрию, неbackend/WS. Новоеизображениересэмплинготдельно; текущиеполныеисходникисохранить. План: конечныйcellsetиfit, сохранитьдемоеслинепрепятствуетгеометрии, screenshot1366/2560, независимыйreview. pending/pending.

R21 implementationchoice: новаяформа5рядовприR76/.95несовместимасwholefield435pxиcontainкарточки. Таккаквладелецпопросилсделатьсетку, временноскрытьдемокарточки/подробности, сохранитькод. Показатьтолькоконечнуюсетку19ячеекнаклон.60 дляоценкиформы; вернутьучастниковпослеподборакомпозиции. Пользователюсообщено.

R21 done/check:19cells вfinitecellset (core15,верхсправа2,низслева2); противоположныеуглыvoid, фонрифта. gridForFrame fitвесьframe, radius83при995×435,perspective.6. Карточки/счётчики/панель временнонеактивны,кодсохранён. Unitgeometry PASS0.18s. Browser1366×768DPR1/2560×1440DPR2errors0; PNGmap-only-* обновлены,1366просмотренведущим. Reviewpending.
R21 independent standee_review PASS: code+2screenshots,19связанныхячеек,противоположныеуглысвободны,полецеликом;browserсамнеперезапускал. reviewed-awaiting-acceptance.

R22: владелецисправилоснову5рядов×3столбцаипроситнараститьдоцельногоромба,неотдельныхвыступов. Показатьсимметричныйромбширинами1/2/3/4/5/4/3/2/1,25связанныхгексов,средние5рядоввмещаюттрёхстолбцовуюоснову. Толькосетка. Проверитьscreenshot+независимыйreview.

R22 исполнение:25связанныхячеек,симметричныеряды1..5..1,полецеликом,безотдельныхвыступов. Browser1366DPR1/2560DPR2errors0, screenshot1366просмотрен, unitgeometryPASS0.20s. Reviewpending.
R22 standee_reviewPASScode+2screenshots,25гексовцельныйромббезразрывов;reviewed-awaiting-acceptance.

R23: по прямому запросу владельца показать сплошную площадку7×7=49гексов,безвырезов. Владелецсамзакраситчтоубрать. Толькосетка, не угадыватьконтур. РеализациязаменяетR22ромб.

R23 done/pass:49ячеекбезпропусков, browser1366/2560DPR1/2errors0, PNGпросмотрен, unitPASS0.17s. standee_reviewPASSsource+screenshot. Ожидаетсяразметкавладельца;никакихдальнейшихпредположенийоконтуре.

R24 прямойзапрос:6рядовпо7гексов,верхнийсдвинутвправонаполшага,нижнийвлево.42ячейкибезвырезов,дляпоследующейразметки. Изменитьтолькосоставичередование,проверитьскриншот/geometry/ревизор.

R24 browser1366DPR1/2560DPR2errors0,42cells,source+PNG1366просмотрены;unitcount/shift/fitPASS0.20s. Reviewpending.
R24 independent standee_reviewPASScode+screenshot:6×7,topright/bottomleft,wholefield. reviewed-awaiting-acceptance.

R25: убратьзакрашенныевладельцемячейкиизclipboard-c9e0bdfc-3d59-41cd-b78e-1a4451e9ad26.png. Нулеваяиндексация(row,col):0:[0,1],1:[0,1],2:[0,6],3:[0,6],4:[5,6],5:[5,6]. Всего12удалений,30остаются. Остальнойшаг/смещение/фонсохранить. Screenshot+reviewразметки.

R25 browser1366/2560DPR1/2errors0,30cells; screenshot1366просмотрен. UnitPASS0.18s counts5eachrow/fit. Независимаясверкасрисункомpending.
R25 standee_reviewPASS: исходнаяразметка/координаты/новыйPNGсверены,12удаленийсоответствуют. reviewed-awaiting-acceptance.

R26 прямойзапрос:показатьтекущийконтурсобычнымипропорциямигексовбезвертикальногосплющивания. gridForFrame perspectiveY1вместо.6;состав30ячеек,удалённыекоординаты,чередованиесохранить. Fitвесьframeбезкамернойперспективыпока. Screenshotиgeometryreview.
R26 проверка:geometryunitPASS0.17s,browsererrors0. Владелецуточнил:скриншотынеделать/неприсылать,смотритпрямовинтерфейсе;дальшепроверкибезснимков. Обычныепропорциивключены.

R27 запроспримерперспективы:наэтойжесеткепереключательСверху/Перспектива;настоящаяpinholeпроекцияплоскостиповорот50градусов/делениенаглубину,неравномерныймасштабдальнееближнее. Контур30ячеекнеизменен. Defaultperspective. Безскриншотов. Проверитьгеометрию/клики/resizeипередатьнезависимомуревизору.

R27 browserбезснимков:реальныйtoggleflat/perspective,resize1366→2560,errors0,cells30. perspectivefarwidth63.34/near106.90;flatwidthодинакова. Независимыйreviewpending. Скриншотынесоздавались.
R27 standee_reviewPASSsource:общаяпроекциястыки/30cells/toggle/fit;не3Dкамера,скриншотовнет. reviewed-awaiting-acceptance.

R28 implementation requestedexplicitly: staticproportionsNOW, NOTanimation. Acceptedperspectiveand30hexcontour. Ownerimagef8117721: heroBIGleftforeground,targetBIGrightback;theseareprimarynativecardssize,waiting/allies~halfsizefithex. Primarypairmaycovermultiplehexes. Fullsourceoriginaltexturesrenderdirectly,NO64pxintermediate. Panelupperleftfreecornernotcoverfield;fieldcanraise. Noanimation/WS/backend, noscreenshots(ownerdirectconstraint). Planexecutor scene/layout+parentshell/details, browserDOMgeometryhover/clickresizematrixwithoutcaptures,independentreview.

R28 реализацияdone: accepted30cells/50degreeprojection kept, projectionfitfillsframe (removed artificial max1cap); originalGPUtexturesdirect uniformcontain nointermediateraster/crop. Primaryhero~(.43,.60),target~(.73,.48)nearestprojectedcells, size107at1366/120larger. Queue21..44dependingdepth projectedhex containment andprimaryreservation/nooverlap;primaryneednotfithex. All10fixtureactorsvisiblein3testedinitialframes. Compactupperleftpanel height~210, noactionbutton; NOtweens/animations.

Browser tmp/static_proportions_check.cjs withoutscreenshots:1366×768DPR1,1920×1080DPR1,2560×1440DPR2. Actualhover/clickqueuedenemy,flat/perspectivetoggle,chatcollapse,10cards,30cells;allcardsinframe,queuedcardboundsinsidehexpolygon,cardpairsoverlap0,uniformrenderaspectoriginaltexturesource>render,activeTweens0,API/errors/failedassets0. Reporttmp/battle_proto/static-proportions-report.json. SATrectanglepanel-vsallprojectedtilepolygons0atall3initialframes (tmp/proportions_panel_check.py). 16focusedtestsPASS0.95s includesmostlyretainedlegacy;browserassertionsverifycurrentrenderer. No screenshotscreated/viewed. Runtime/backend/RiftLabunchanged, demo-only. Reviewpending.
R28 independent standee_review PASS source+browserdata; SATpanel-vsfield/cards independentlyrecomputed all9states overlap0. Flat1366 shows7cards vs10perspective (capacityfit), noanimation/sourceoriginalconfirmed. No screenshots. reviewed-awaiting-acceptance.

R29 прямоеуточнение:HPдолженбытьяркокрасным,контрастнымнавсехкарточках,небледнорозовый/бирюзовый. ИзменёнтолькоцветактивногоHPна#ff2020;потерянныйсерыйсохранён. Снимкизапрещены. Проверкасинтаксиса/исходникаинезависимыйdelta-review.
R29 done/pass syntax+source,standee_reviewPASS:activeHP#ff2020allactors,lossgrayunchanged. reviewed-awaiting-acceptance.

R30 latestowneradjustments: perspective allies shouldnotlooksameassmallfar-monsters; heromoveEXACToneadjacenthexLEFT, herosizeokay. Mirrorenemiesfacinghero. Selectedtargetslightlysmaller toretain2queuerows; allieslarger andbottomedge likemonstersupperedge. Fieldtextures5–6variantsareundecidedleaveunchanged. Statusreadinessicons/pulsationforunansweredaction andWebSocketpotentiallythisiterationarediscussion/future, NOTimplementnowwithoutcontracttask. Staticcompositionremain, NOscreenshots. Planexecutor scene, parentbrowsergeometry/hover/resize/flipsizepositionverificationandindependentreview.

R30 done: heroexactleftsame-rowcol-1frompreviousnearestcell, herosize107/120unchanged; target87%93/104; enemyoriginalimagesflipXtrueonly (HP/UIunmirrored); allyqueuefitlimit76instead44actual57–76, bottomrow5preferred. Enemyrow0/row1interleavedplusrow1col2candidateforcompactwithoutprimaryoverlap. All10fixturecardsvisible3initialframes. Panelwidthclamp160..196 preventsherooverlapat1366. Icons/readinesstimerpulses/WebSocketnotimplemented, recordedfuture.

Browserwithoutcaptures tmp/static_proportions_check.cjs:1366×768DPR1/1920×1080DPR1/2560×1440DPR2; actualhover/click,projectiontoggle/chatresize. Assertsherooffsetexact,targetratio,allflips,allyrow5size>44,bothenemyrows0/1,fullsourceaspect,queueactualframe/baseinsideprojectedpolygon,allcardpairsnooverlap,viewportfit,tweens0,API/errors/assets0. PanelSATall9savedstates(initial/flat/expanded)versusfield+cards0. 16focusedtestsPASS0.89s (mostlylegacy;currentbrowserassertionsprimaryproof). Reportstatic-proportions-report.json. Independentreviewpending. No screenshots.
R30 standee_reviewPASSsource+numericbrowserdata;panelSAT9statesindependently0;sourceart/brightredHP/noanimationconfirmed. reviewed-awaiting-acceptance.

R31 прямойзапроссобратьнастольныйвидсверхуипоказатьскриншот. Безревизора(уточнениевладельца:прототипсамопроверка). Flat:карточкилежатвцентрахгексовбезподставок,обычныесоюзники/врагиодинаковогоhex-relativeразмера,центральнаяпара~1.5×,originalfulltextures/redHP,общиецель/данныеипереключатель. Perspectiveсохранить. Screenshotsсноваразрешеныипрямозапрошены. Планмалыйrendererbranch/browser/screenshot.

R31 done/самопроверкаPASS:FlatотдельныйtableCardrendererбезstand,одинаковыйhex-relativeобычныйразмер,центральные~1.5×. При1920обычные79px/главные118px. Originaltexturesfullcontain/redHP/hoverpinсохранены,перспективныйrendererнеизменён. Browser1920/1366errors0;2big,10cards1920,standfalse,обычныесамеразмер,переключениеназадperspectivePASS. PNGtabletop-1920.pngпросмотренведущим. Теперьdefaultflatдляобзора,переключательперспективысохранён. Безревизорапоинструкциивладельца. checked-awaiting-acceptance.

R32:сблизитьцентральнуюпару(текущийвидсверху);ожидающихпротивниковсовторогорядавернутьвпервый. Flatheroanchor.48/.60,target.62/.48вместопрежнегоразнесения;waitingonlyrow0. Prototypeбезревизора. Проверитьклики/расстановкуиснимок.

R32 done/самопроверка:Flatцентральнаяпаранаточнососеднихдиагональныхгексах,вертикальныйотступвнутриячеек±12pxсохраняетразделениекарточек. Waitingтолькопервыйряд0,все5демоожидающихвмещаются. Browser1920/1366errors0,10cards,standfalse,toggleperspectivePASS. Безревизора. checked-awaiting-acceptance.

R33 исправление:сблизитьнеозначаетналожить. Проверкафактическихграницнашламинимальныйзазор3.7pxпри1920иoverlap4.9pxпри2560. Вместофиксированного±12offsetвычислятьoffsetизвысотыкарточки+16pxзазоримежрядногошага. Тежеячейки/размерысохранить. Безревизора.
R34 диагностикаразмеровпоowner:4viewporttabletop2560/1920/1600/1366. All10cards,overlap0,overflow0,JSerrors0,pairgap16. Main139×166/99×118/79×94/64×76;queue92×111/65×79/52×63/42×51. Пустыебока451/304/256/226каждый. Ограничениевысотаполя,автоматическийuniformfitуменьшаеткарточкивместесгексами. PNGresponsive-tabletop-*.png,reportJSON. 1366просмотренведущим,очередьмелкая;необъявлятьreadabilityaccepted.

R35 ownerexactsystem:WHOLEzone(status+field+chat+header)max1920wide;2560side320,1920nooutergap;below1920uniformscaleallzone. Logicaldesign1920×1080,shortheightlimitslogicalheightwithoutadditionallyscalingwidth. Centerzoneouterviewport. Replaceindependentpanelvwheightdvhwithfixedbaselinewidth420/status andworkspaceparentheight. Prototypeownchecknoreviewer. Request3FULLscreenshots2560/1920/1366. Planviewportwrapper+uniformCSSzoom, browserdimensions/pointer/errors+screenshotvisualcheck.
R35 selfcheckPASS:2560zone1920×1080x320y180;1920zone1920×1080x0y0;samehost1449×654,main99×118logical.1366zone1366×768scale.711458,status298.8vs420,hostlogical1448×653/main99×118logical. All30cells,scaledpointerclickPASS,overflow0,errors/failedassets0. ThreeFULLviewportPNGwhole-zone-{2560,1920,1366}.png,reportJSON. Noindependentreviewerperowner. checked-awaiting-acceptance.

R36 owner:применитьсгенерированныйHUDиспросилкакрассчитатькоординатыскиллов. Asset1942×809RGBAfromgenerated_imagesexec-c98295dd-8e1d-44b8-9409-16ba06af48d9.png copiedworkspaceassets/combat-controls-v1.png. ScopeprototypeHUDinsamePhaser,bottomrightskincircle+9resources+3feints+8abilityslots. Dynamicicons/text/hitregionssharesourcemanifestcoordinatesandonecontainertransform, no bakedtext. Actualcatalogshortlabels/costexamples, demonstrationonly. Readynewtargetimmediatelykeepssword;clockonlyreadyfalse. NoWS/backend/production. Owncheck noindependentreviewerperowner. Planmodule+manifest,sceneintegration,geometry/pointer/resize+DPRcheckandscreenshot.

R36 done/owncheckPASS: generatedRGBA1942×809copiedunchanged+SHAprovenance. hud-layout.js nativecoordinateanchors, onePhasercontainerx/y/scale forbackground+icons+text+21interactiveareas. 9tokenicons+counts/3shortfeintswithrealcatalogcosts/8abilityicons; Russianhoverlabels. Center readyattackimmediateselectsnextdemotarget, waitingonlyexplicitdemoReadyfalse (noattackauto-wait). Selectioncallbacksdemoonly,nobackend/resourcestransactions.

Browserapplied_hud_check.cjs1920/1366/2560:actualclickfeint/ability/attack,selectedtargetchangesimmediatelyreadytrue;readyfalsehourglass+attackgated;12repeatedattacksstablechildren(noaccumulatingHUD);errors0/failedassets0. PNGapplied-hud-1920.pngviewed:skin+overlaysaligned,lower-rightfieldcorner;reportapplied-hud-report.json. Newlayoutunitanchors/transformsPASS0.19s. Noindependentreviewerperowner. checked-awaiting-acceptance.

R37 прямойзапрос:убратьстоимостьфинтовсплашек,показыватьвкарточкеприhover. Удаленыпостоянныеиконки/цифрыcost,названиецентрировано;hoverкарточкатекстназвание/описание/стоимость. Сохранитькликивыбора. Самопроверкабезревизора.
R37 done/ownbrowserPASS:costhiddeninitial,hoverdescription+costshown,selectcallbackworks,pointerleavehides. Addedpointerleavehandlerwithrootdestroycleanupsohovercarddoesnotstickoutsidecanvas. Syntaxpass. checked-awaiting-acceptance.

R38 owner:HUDслишкомбольшойзаходитнаполе,уменьшить;вместовременныхSVGхочетзаказныерастровыеиконки. displayWidth760→570(−25%),compact680→510. Сначалаприменитьмасштаб/проверить. Заказатьмечичасикивстилерамкиотдельнымasset,остальныеиконкиследующийнабор. Prototypeowncheck.

R38 done/ownbrowserPASS3sizes pointer/attack/clock/feint/ability/cleanup. HUD−25%=570logicalpx baseline; centralSVG/vectorreplacedgeneratedRGBAattack/waitoriginals copiedunchangedwithprovenanceSHA. Token/abilitySVGremainexplicittemporarynextassetset. Screenshotapplied-hud-1920.pngviewed. Noindependentreview. checked-awaiting-acceptance.

R39 попробоватьразныеэтапынаразныхожидающихпротивниках. Demoстатусыthinking/decided/imminent;надHPтёмныйbadge:триточки/меч/меч+янтарнаядугатаймера. Hoverописаниевпанели,статичнобезпульсации/WS. Неопределятьготовностьпоряду. Проверитьразныеэтапы/bounds/screenshotsownбезревизора.
R39 ownbrowserPASS1920/1366flat+perspective:3stagesvisible,badgesaboveHP,inframe,JSerrors0. Perspective40pxheadroomreservedtopreventbadgesclipping. StaticnoWS. PNGenemy-intentions-1920.pngviewed. checked-awaiting-acceptance.

R40 ownerapprovedcompacttargetpanel+accordionsections,damageimmediatelyvisible. Role/power/resources/effects/intent +damageprimaryrange,3collapsedsectionsАтака/Защита/Прочее. Displaystat_sheet.sections/value_textcontract;demo fixturesexplicitnoserverformulas. Preserveopenstateacrosshover;panelheightbounded340scroll. Ownbrowserchecknoindependentreviewerprototype.
R40 done/ownbrowserPASS:damageimmediately18–26then14–22ontargetswitch,3closedaccordions,open/closeclicks,preservedsectionstateonactorchange,1366resize,errors0. Screenshot1920viewed. Valuesarelocaldemofixturesnotrealbackenddata. checked-awaiting-acceptance.

R41 ownerapproved:точностьосновнойпоказательопасностирядомсуроном,непутатьсуклонением. Вывестиготовыйvalue_textизstat_sheetдля*_accuracy/accuracyвсводкебезраскрытия. Самопроверкаsource/syntax,prototypeбезревизора.

R42 owner:скрытьнативныйWindows scrollbarвпанелицели,сохранитьwheelпрокрутку. CSSscrollbar-widthnone/webkitscrollbardisplaynone,overflowautoсохранён;paneltabindex0дляклавиатурнойпрокрутки. Prototypeowncheck.

R43 regressionperspectiveafterflatwork. Foundsharedwaitingrow0(R32)appliedbothmodesandnearestscreenplacementafterheadroomcouldselectsame-rowhero/target. Separate:flatunchangedoneneighborpair+onequeue;perspectiveheroexplicitfrontrow4,targetrow3,queues0/1. Keepcamera50/sourceart/standees. Owncross-modechecksnoindependentreviewer.
R43 done/ownbrowserPASS1920/1366 sequenceflat→perspective→flat:perspectivehero4target3(herolower),queue0/1;flatpair3/2queue0;30cells,sameart/renderermodes,pairsoverlap0,errors0. PNGperspective-restored.pngviewed. Noindependentreviewer. checked-awaiting-acceptance.

R44 ownerrejectsR43самовольныеперестановки:вернутьзаднийряднаместа,требовалосьлишьсблизитьпаруоднимгексом;проситсогласовыватьизменения. R43revertedonly:waitingrow0unchangedpreR43,forcedhero4/target3removed;flat/perspectivepriorplacementrestored. Furtherpairmovementpendingexplicitcoordinatesdiscussion,NOotherchanges.

## R45 — обязательный общий контракт оболочки

Решение владельца2026-10-25 зафиксировано отдельно: [game-shell-contract](2026-10-25-game-shell-contract.md). ПравилаR35(фиксированные1920×1080/вертикальноецентрирование) НЕсчитаютсяпринятойоболочкой и замененыэтимрешением. Весьцентрmax1920 независимоотхедера~40/optionalfooterдо40;реальнаядоступнаявысота;HTMLстатусслева,PhaserнадHTMLчатомсправа. Обязательны4контрольныхviewport2560/1920/1600/1366. Сначаласогласованнаяоболочка,затемscene-onlyработа. Сейчасизмененытолькодокументы/projectguidance;стенднеисправленэтойзадачей.
