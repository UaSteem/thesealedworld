# Items: меч T0–T5, S3, лорные признаки и раскрытие

R41: убрать технические подписи «Игровой экран/Прототип/Phaser», оставить простое «Инвентарь»; поправить нижнее оформление по скриншоту; убрать золотую обводку canvas при фокусе. План: локальный inventory template/CSS и нижняя геометрия сцены, не shared shell. Независимый режим сохраняется. Implementation pending / verification pending.

R40: счётчик «Все» показывает только общее количество, без6/6; в категории — отфильтрованное из общего. План: изменить только строку подписи в Inventory Lab scene.js. Независимый режим сохраняется; syntax/browser/reviewer. Implementation pending / verification pending.

R39 — оформить фильтры стильными вкладками: активная визуально сливается с общей рамкой инвентаря; подобрать существующие SVG-иконки. Только Inventory Lab. План: переиспользовать frontend inventory-icons/items.svg и inventory-gear weapon_sword/torso/ring/consumable/resource/quest.svg без копирования; preload SVG в Phaser, tint semantic tokens; общая рамка области, открытый снизу контур активной вкладки, названия/counts и текущая фильтрация сохранены. Проверка node syntax, браузер desktop/1366 и независимый ревизор. Implementation pending / verification pending.

R35: владелец сообщил, что hover-карточка блокирует определение предмета под ней. Требование: незакреплённая карточка пропускает наведение/щелчок/колесо к сетке; после выбора закреплённая карточка принимает ввод. План: проверять popup bounds только в pinned-состоянии для pointermove/down/wheel. Только scene.js, независимая проверка сохраняется. Implementation done / verification pass.

R33 — уточнение владельца: пустая сетка сразу заполняет всю доступную высоту рюкзака; дополнительные строки под предметы продолжаются вниз с прокруткой. План: вычислить минимум строк по высоте viewport и шагу ячейки, сохранить рост по footprints. Только Inventory Lab scene.js. Режим независимой проверки сохраняется. Реализация done; node syntax и placement checks pass; CUA reload + screenshot var/inventory-lab/full-height-grid.png; independent static review pass.

Продолжение R32: по скриншоту владельца сделать GS тонкой полосой под экипировкой, над GS разместить пояс8 ячеек в HTML-панели персонажа. Убрать дубликат пояса из Phaser. Только Inventory Lab, shared combat/character исходники не менять. План: локальный boot добавляет пояс перед cp-power, scoped CSS уплотняет GS, сцена освобождает верх рюкзака. Независимый режим сохраняется; проверка браузером и ревизором. Реализация done, проверка: CUA pass (8 ячеек над GS, GS30px), independent static + screenshot review pass.

Статус: reviewed-awaiting-acceptance; R1–R31 прошли независимую ревизию. Владелец выбрал независимого ревизора 2026-10-24.

## Исходный запрос и согласованный контекст

«Создавай задачу со всем что обсудили: меч Т0–Т5, два размера картинок в S3, генератор, лорные теги и раскрытие предмета. Выполняй с независимым ревизором».

Принятые уточнения из обсуждения:
- База → материал → тир материала → масштабирование и аффиксы → выбор изображения → сохранение экземпляра. Числовые значения аффиксов — механика, не идентичность лорного текста.
- Существующие Python-ресурсы и Pydantic, словари по устойчивым ID; не вводить runtime-источник из рабочего JSON.
- Малый контролируемый словарь лорных смыслов объединяет механически разные аффиксы; использовать существующее descriptive.narrative_tags. Нормализовать только признаки фактически выпавших аффиксов, не смешивать с тегами базы/материала/происхождения.
- Существующая item_generated_templates и хеш комбинации/версии промпта переиспользуются; новая таблица для описаний не нужна.
- Выбранный visual_variant_id и is_identified относятся к экземпляру. Подготовка текста ИИ и раскрытие независимы; ИИ заказывается заранее, скрытый текст не передаётся клиенту до раскрытия.
- Базовое название и описание находятся в каталоге (публичный bootstrap/IndexedDB); не дублировать их в каждом экземпляре. Материал и base_id, характеристики, роллы и износ сохраняются у экземпляра.
- Готовые изображения — S3 с устойчивыми ключами; SVG-исходники остаются в assets/item_art. Два размера одного рисунка: миниатюра экипировки и более крупный инвентарный/карточный.
- Старые frontend SVG остаются иконками пустых слотов и резервом для непокрытых предметов. У занятого слота новая предметная картинка, подпись слота скрыта; название доступно в карточке/подсказке.
- Начать с существующих шести мечей T0–T5, вертикальный меч в ячейке 1×3. Тематические рисунки под аффиксы пока не заказывать; нынешние варианты универсальны для своих материалов.
- Предметы на телах монстров не рисовать. Навык оценки отложен; состояние раскрытия и доступное действие нужны сейчас.

## Требования и приёмка

| ID | Требование | Реализация | Независимая проверка |
| --- | --- | --- | --- |
| R1 | Сохранить и реализовать материал как источник тира; согласовать DTO/вызовы/хеш, не менять утверждённые числовые правила без необходимости. | done | pass, независимый ревизор |
| R2 | Единый контролируемый словарь лорных признаков и нормализация аффиксов; валидировать неизвестные ID. | done | pass, независимый ревизор |
| R3 | Довести Python/Pydantic-каталог меча T0–T5, базовые названия/описания и ссылки; JSON оставить workbench. | done | pass, независимый ревизор |
| R4 | Подбор картинки после механики по базе, материалу/тиру, лорным признакам; отдельная случайность не меняет механические роллы; резерв для непокрытых предметов. | done | pass, независимый ревизор |
| R5 | Сохранять выбранный visual_variant_id в экземпляре; повторный read и UI не перевыбирают изображение. | done | pass, независимый ревизор |
| R6 | Подготовить 12 прозрачных растров из шести SVG: миниатюра и крупный вид, без искажения пропорций; сохранить SVG-мастера. | done | pass, независимый ревизор |
| R7 | Использовать существующую S3-интеграцию, устойчивые ключи с версией содержимого и публичные URL; публикацию и доступность проверять отдельно от локального build. | done | pass, независимый ревизор |
| R8 | Публичные базовые тексты и два вида изображений проходят существующий bootstrap, manifest/version и IndexedDB. | done | pass, независимый ревизор |
| R9 | Инвентарь/экипировка/карточка показывают выбранную картинку нужного размера; пустые слоты сохраняют старые локальные SVG и подписи. | done | pass, независимый ревизор |
| R10 | Существующий текстовый кеш учитывает нормализованный лорный набор и значимую внешность; числа/ID экземпляров/порядок аффиксов не создают новые шаблоны; новая версия промпта. | done | pass, независимый ревизор |
| R11 | is_identified у экземпляра, базовое представление до раскрытия; ИИ-текст хранится заранее и раскрывается независимо от готовности/задержки; не передавать скрытые тексты в публичные DTO/DOM. | done | pass, независимый ревизор |
| R12 | Сохранить полные экземпляры/владение/износ; убрать дубли базовых текстов в новых экземплярах, согласовать схему и чтение существующих записей. | done | pass, независимый ревизор |
| R13 | Риск-соразмерные тесты и браузерная проверка, наглядное сравнение T0–T5 в двух размерах, независимая ревизия и точные ограничения результатов. | done | pass, независимый ревизор |
| R14 | Не заказывать внешнюю AI-графику, не добавлять навык оценки или новые наборы оружия; не менять чужие параллельные изменения, не коммитить/деплоить/мигрировать рабочие БД без поручения. | done | pass, независимый ревизор |
| R15 | Показать отдельный визуальный пример будущего инвентаря без блока персонажа и слотов экипировки из последнего скриншота. | done | pass, независимый ревизор |
| R16 | В примере пояс расположен одной линией до восьми ячеек; это вариант обсуждения, не новая утверждённая механика ёмкости. | done | pass, независимый ревизор |
| R17 | Показать переработанную карточку: компактное название, изображение рядом с параметрами, аффиксы и описание ниже; использовать существующие мечи и их данные. | done | pass, независимый ревизор |
| R18 | Пример отдельный, допускает смену выбранного меча, не меняет текущий интерфейс/БД; решение Phaser или HTML в игровой области остаётся открытым. | done | pass, независимый ревизор |
| R19 | Добавить настоящий Phaser-инвентарь ниже существующего HTML-примера, сохранив оба для сравнения. Использовать существующий локальный runtime. | done | pass, независимый ревизор |
| R20 | Передать в Phaser тот же DTO-набор шести мечей, параметров и публичных S3-ссылок. Сетка, изображения, пояс и карточка рисуются игровыми объектами, не HTML внутри canvas-рамки. | done | pass, независимый ревизор |
| R21 | В Phaser можно просматривать/выбирать мечи; нет постоянной пустой карточки до выбора, пояс до восьми ячеек одной строкой, без блока персонажа. | done | pass, независимый ревизор |
| R22 | Только отдельный интерактивный preview. Не подключать рабочие действия экипировки/БД, не менять production UI, S3 policies или итоговое решение о рендерере. Проверить реальный canvas и размеры в браузере. | done | pass, независимый ревизор |

## Первоначальный план

1. Проверить текущие Items/runtime/persistence, inventory projection, frontend/IndexedDB и S3 adapter; согласовать узкие интерфейсы между исполнителями.
2. Исправить генерацию/лор/шаблоны/сохранение/раскрытие с целевыми тестами.
3. Подготовить каталог/два размера/публикацию в S3 и общедоступную проекцию.
4. Подключить каталог и UI через существующие границы; проверить fallback, размеры и отсутствие утечки текста.
5. Выполнить тесты/браузерную проверку, сохранить доказательства; провести независимую ревизию по исходным требованиям и отдельно проверить финальные утверждения.

## Границы и ещё проверяемые детали

Формат и размеры растров выбираются на мече после визуального сравнения. Проверить реальные настройки S3 без вывода секретов; при недоступности внешнего сервиса не объявлять публикацию завершённой. Подготовка миграции разрешена, применение к рабочим данным не поручено. Старые записи не менять массово. Не обходить заморозку AI image tasks; текстовый провайдер при тестах не вызывать.

## Журнал реализации и доказательства

До правок обнаружен сильно изменённый общий checkout. Новый scope не разрешает откат иных работ. Режим независимого ревизора выбран непосредственно в исходном запросе.


## Реализованный результат

- Items: материал определяет item_tier; явный material_tier отделён от существующей grade/rarity-подсказки. Механические числовые определения не перебалансированы.
- Контролируемый Python-словарь из 23 лорных смыслов; авторские narrative_tags ссылаются на него. Набор собирается по ID фактически выпавших аффиксов.
- Текстовый хеш v2 использует версию, клан, базу, материал/его тир, нормализованные смыслы и visual ID. Промпт получает смыслы и описание внешности.
- Выбор внешности после механики использует отдельный Random. Выбранные ID/размеры сохраняются в appearance и восстанавливаются без повторного выбора.
- Новые instance и template не дублируют базовые тексты: до ответа ИИ name/description=NULL. Базовое представление приходит из каталога.
- is_identified отделён от text_status. Owner-scoped действие identify проверяет доступность и состояние; повтор безопасен. Готовность ИИ не раскрывает предмет.
- Публичная проекция скрывает подготовленный текст до определения; обновляет видимое представление при последующих чтениях кешированного инвентаря.
- Предварительная генерация ответа, переиспользование готового шаблона и перевод ранее не запрошенного шаблона в pending согласованы. Новый нераскрытый экземпляр не получает приватное имя даже при reuse.
- Шесть SVG сохранены. Подготовлены 12 прозрачных lossless WebP (96×288 и 256×768), content-addressed S3-ключи в Python, отдельный build/publish CLI.
- Реальная публикация: uploaded=12. Публичные HTTP GET:12/12, image/webp и SHA256 совпали. Повторная публикация: uploaded=0, skipped=12.
- Existing S3 reader/redirect доставляет файлы по прежнему /static/generated-assets URL. Файлы игры не добавлены в frontend static.
- GameCatalog bootstrap/manifest и IndexedDB включают item_visuals с базовыми текстами и двумя URL. Старые SVG пустых слотов остаются локальными.
- Экипировка использует thumbnail без подписи занятого слота; рюкзак/карточка используют крупный рисунок. Меч1×3, object-fit:contain.
- Штатным codex_core static compiler пересобраны только game.css/game.js. Ручная правка скомпилированных файлов не выполнялась.
- Подготовлена миграция0003_item_identification для bool и nullable-текстов обеих таблиц. Старые строки не переписываются; рабочая миграция не запускалась.

## Фактические проверки ведущего

2026-10-24:

1. Объединённый pytest:308 passed,14 skipped,2 deselected,1 deprecation warning (6.91s). Полный результат в var/item-visuals-integrated-tests.log. Покрыты Items, inventory, bootstrap и frontend generated-assets adapter.
2. Дополнительные frontend inventory contracts:9 passed,31 deselected (0.70s), файл tests/frontend/game_features/exploration/test_template_contract.py, фильтр -k inventory.
3. После узкого исправления typed kwargs в sword.py:35 visual tests повторно passed (0.78s). Явный model_validate не изменил данные.
4. Ruff изменённых Items/inventory/bootstrap/shared/frontend source и root tooling:pass. Node --check собранного game.js:pass. Mypy четырёх новых визуальных файлов:pass; лог var/item-visuals-root-mypy.log. Исполнитель UI дополнительно проверил шесть своих файлов mypy.
5. Source-scoped git diff --check:без ошибок содержимого; Git предупреждает о CRLF→LF в существующих файлах. Compiler output сохранён как создан, без косметической очистки.
6. Quick_validate routed project и game-content skills:valid; относительные ссылки документации разрешаются.
7. Сравнение двух размеров: assets/item_art/variants/sword/delivery-preview.png. Публичные S3 SHA доказательства:var/item-visuals-s3-verification.json. Идемпотентная публикация:var/item-visuals-publish-repeat.log.
8. CUA browser local preview127.0.0.1:8873:семь предметных img реально загрузились, имеют contain и правильные natural dimensions. Preview использует production frontend S3 reader/redirect, но не deployed frontend.
9. Preview1024×900 и390×844 через same-origin iframes; desktop исходно1280×720. Снимки и сценарий в var/item-visuals-inventory-preview/.
10. Сценарий responsive.html после init открывает настоящий IndexedDB readonly transaction, читает item_visuals и __manifest__, сверяет обе ссылки шести записей и хеш с bootstrap. Видимый результат:«IndexedDB: чтение6/6 вариантов; хеш совпал»; наблюдение сохранено в browser-observations.json.

Async pytest/публикация выполнялись вне Windows sandbox: в sandbox asyncio застревал при socketpair. Зависшие собственные dry-run процессы идентифицированы и остановлены; dry-run CLI теперь синхронный и не делает сетевых запросов.

## Независимая ревизия

Ревизор:/root/review_item_visuals_lore, отдельный fresh-context агент, без редактирования результата.

Первоначальная ревизия:существенных дефектов реализации не найдено. Независимый pytest277 passed/2 failed; оба metrics-теста воспроизведены с pre-task baseline InventoryService. Они не вызваны этой работой. Независимо проверены12 публичных объектов S3 (HTTP200, MIME, SHA).

Первоначально R8/R13 имели partial по уровню browser proof. Ревизор обоснованно указал, что счётчик из GameCatalogCache.memory не доказывает прямое чтение IndexedDB. QA-сценарий дополнен readonly transaction и сравнением с manifest; реализация кеша не менялась.

Повторная сверка точных финальных утверждений:все подтверждены, R8 и R13 обновлены до pass в границах local source/tests/preview/S3. Ревизор самостоятельно повторил35 visual tests и quick_validate двух skills, просмотрел новые артефакты и mypy log. Новых существенных замечаний нет.

## Ограничения и состояние данных

-14 PostgreSQL durability tests требуют отдельной disposable среды; в этом прогоне skipped. Полный project checker не запускался.
-Два ранее существовавших metrics assertion tests исключены из итогового объединённого прогона; независимый ревизор отдельно подтвердил baseline reproduction. Не заявляется зелёный полный проект.
-Рабочая БД не мигрировалась; deployment/production UI и реальный AI provider не проверялись. Нужна отдельно разрешённая операция миграции/развёртывания.
-Реально изменены внешние данные только в порученном S3:созданы12 новых content-addressed объектов. Existing objects не перезаписывались; повторная публикация их пропустила.
-Новые PNG/WebP для иных предметов, новый навык оценки, генерация AI-картинок, коммиты и push не выполнялись.
-Параллельные старые изменения checkout сохранены. Снимки затронутых файлов:var/item-visuals-lore-baseline, var/item-visuals-ui-baseline, var/item-visuals-compiled-baseline; прежние skill references:var/item-visuals-guidance-stage/*.before.

## Документация

Обновлены docs/ru/backend/features/items/visual_catalog.md, ADR-0001, asset README и routed references generation-determinism.md/catalog-conventions.md. Исторические старые task MD не переписаны под новый результат. Результат ожидает принятия владельцем.

## Визуальное уточнение после основной реализации

Пользователь: «нет я хотел чтобы ты сделал пример как ты сейчас с инвентарём показал ... вот той части не будет в инвентаре будущего; пояс ... одной линией до8 ячеек ... на распутье: Phaser или HTML открывающийся в зоне Phaser».
Перед этим пользователь указал, что карточка с высокой картинкой выглядит странно. Предложено вынести изображение из шапки к основным параметрам.
План продолжения: отдельный preview fixture/template, реальные ресурсы/механические данные мечей без игровой БД, локальное переключение карточки, проверка desktop/mobile и независимая проверка узкого примера. Производственные шаблоны и алгоритмы не менять.


### Результат визуального уточнения R15–R18

Добавлен изолированный `inventory/future` fixture и шаблон `game/previews/inventory_future.html`. Это локальный пример компоновки, не production-маршрут и не решение о Phaser/HTML.
Команда: `.venv/Scripts/python.exe -m tools.game_preview.render --fixture inventory/future --out var/item-visuals-inventory-preview/future.html`.

Результат: рюкзак без персонажа/экипировки, одна линия из8 ячеек пояса, компактный заголовок карточки, рисунок144px рядом с реальными параметрами. Аффиксы и базовое описание расположены ниже. Данные: текущие ItemFactory → InventoryRuntimeItemDTO → InventoryViewService; детерминированный seed, без БД и ИИ. Выбор меча меняет только локальную видимую карточку; игровые действия отключены.

Проверки ведущего: Ruff check/format pass; source-scoped diff check pass; старый swords fixture и новый future успешно отрендерены. CUA переключил все6 мечей, после каждого видима ровно одна правильная карточка. Desktop:8 belt cells/1 row, no horizontal overflow,7 visible images loaded+contain, paperdoll отсутствует. Mobile390px просмотрен в same-origin iframe: пояс остаётся одной линией, карточка переносится под рюкзак без горизонтального обрезания.

Артефакты: `var/item-visuals-inventory-preview/future-desktop.png`, `future-mobile.png`, `future-observations.json`. Live local preview: `http://127.0.0.1:8873/future.html`. Для вывода в чат сохранена обрезка исходного браузерного скриншота `future-example.png`.

Независимый ревизор `/root/review_inventory_layout_example`:R15–R18 pass; independently rendered HTML equals future.html, old swords fixture renders; source and both screenshots/observations inspected. Существенных замечаний нет; точные финальные утверждения подтверждены. Production UI/БД в этом визуальном продолжении не менялись. Ожидается принятие владельцем.


## Phaser-пример R19–R22

Исходный запрос продолжения:«ты можешь взять ... фрейм Phaser и нарисовать нам инвентарь и передать туда данные как в примере ... тоже ниже этого примера».
Согласованная граница: рюкзак Phaser, персонаж/надетые предметы остаются HTML; сейчас нужен сравнимый локальный стенд, не рабочие действия экипировки.

Использован уже существующий frontend vendor Phaser3.60.0 без замены/загрузки зависимостей. Новый isolated module:src/frontend/static/js/game/previews/inventory_phaser.js. В inventory/future исходный HTML сохранён сверху, новый canvas расположен ниже. Один и тот же window.visible_rows экспортируется в безопасный JSONscript:6мечей, параметры, аффиксы, описания и ссылки совпадают. Реальная сетка, пояс, изображения, карточка и подписи нарисованы Phaser Graphics/Text/Image. В host только CANVAS, DOM-карточка внутрь не подставляется.

Управление: hover на desktop показывает просмотр; click/tap закрепляет, пустое место/×/Escape закрывает; стрелки при фокусе canvas выбирают предметы. Начальное selected_id=null. Пояс8в1строку; персонаж/экипировка отсутствуют. Размер logical canvas зависит от host (desktop918×640, mobile364×640), на узком экране карточка overlay. Сетка8×5 здесь демонстрационная; это не решение о будущем ограничении ёмкости/весе.

Доставка: публичный S3 GET существующего рисунка вернул200,image/webp, без ACAO для localhost. Настройки бакета не менялись. Только developer PreviewServer получил каталог-ограниченный /preview/item-textures/<visual_variant_id>/image|thumbnail:existing reader → trustedS3 bytes → same-origin response. Никаких URL из пользовательского ввода или произвольного upstream; версия содержимого присутствует в query texture_url. Проверена SHA переданных WebP-байтов. Это временная доставка стенда, не production CORS fix.

Проверки ведущего: Ruff fixture/server pass, node --check JS pass, source diff check pass. Оба fixture future/swords рендерятся. CUA подтвердил настоящий Phaser3.60.0 WebGL,6/6 текстур, один CANVAS, начальное отсутствие выбранного предмета, последовательный выборT0–T5 клавишами, pinT4 и закрытие мобильной карточки касанием×. DesktopPhaser и mobile390 просмотрены, карточка и кнопки помещаются в canvas. Hover/empty-close дополнительно прослежены по исходникам; не заявляется отдельная browser-проверка всех hover-траекторий.

Артефакты:var/item-visuals-inventory-preview/phaser-desktop.png,phaser-mobile.png,phaser-observations.json,phaser-final.png,phaser-final-metrics.json,phaser-example.png. Пользовательская страница: http://127.0.0.1:8873/future.html#future-phaser-title.

Независимый ревизор:/root/review_phaser_inventory_preview. R19–R22 pass. Independently:bothfixtures rendered;6JSONitems equalHTML rows/params; invalid relay IDs/URL-shaped references/extra segments returned404; screenshots+observations inspected. Существенных замечаний нет. Точные итоговые утверждения сверены вторым этапом и подтверждены.

Игровые действия, БД, S3 policy, AI, production UI и общий loader игры в этом продолжении не менялись. Ни предметы не надеваются, ни навык оценки не исполняется. Ожидается принятие владельцем.

## Отдельный экран Inventory Lab: R23–R28

Исходное уточнение: отдельное окно инвентаря в общей Adventure-оболочке Game UI Lab; HTML-персонаж слева, Phaser-инвентарь справа над HTML-чатом. Внешний размер окна не зависит от выбранного предмета, адаптируется лишь карточка/рисунок. Пока изолированный макет для будущей интеграции. Режим с независимым ревизором сохраняется.

| ID | Требование | Реализация | Проверка |
| --- | --- | --- | --- |
| R23 | Самостоятельный локальный экран в общей оболочке; существующий combat lab не менять | done | pass — independent reviewer |
| R24 | Adventure semantic tokens для HTML и Phaser, улучшенная композиция | done | pass — independent reviewer |
| R25 | Стабильное внешнее окно при выборе; desktop 1366×768–2560×1440 и изменение чата | done | pass — independent reviewer |
| R26 | Phaser-сетка и пояс 8 ячеек; нет начального выбора; hover временный, click закрепляет, Escape закрывает | done | pass — independent reviewer |
| R27 | Замороженные реальные данные 6 мечей; stdlib/Jinja runtime без backend/settings; локальная строгая карта WebP | done | pass — independent reviewer |
| R28 | Только mock, без игровых mutations/API, изменения экипировки, веса, drag, S3 policy или production integration | done | pass — independent reviewer |

План: экспортировать existing inventory/future payload в JSON; добавить отдельный stdlib/Jinja server и шаблон с неизменёнными shared HTML character/chat; реализовать модульные data/theme/scene и локальную CSS-композицию. Phaser Scale.NONE + ResizeObserver, карточка прокручивается внутри собственного пространства при малой высоте. Проверить syntax/server/allowlist и передать браузерную проверку/независимую ревизию ведущему. Затрагиваются только новые inventory-specific файлы и эта запись.

### Наблюдения исполнителя Inventory Lab (2026-10-24)

R23–R28: implementation done; independent verification pending (ведущий выполняет browser proof и ревизию). Новые файлы: inventory_app.py, templates/inventory.html, data/inventory.json, static/inventory/{inventory.css,theme.js,data.js,scene.js,boot.js}, INVENTORY_README.md, test_inventory_app.py. Shared combat shell/character/chat и production frontend не изменялись.

Проверки исполнителя: Ruff check/format Python pass; node --check четырёх модулей pass; Jinja render pass; unittest 3/3 pass (структура frozen payload/оболочки, все12 art responses побайтово равны existing WebP, unknown/traversal URLs404). Это offline Handler-проверка, не сетевой HTTP proof. Sandbox urllib встретил WinError10013. Сервер запущен foreground exec session56339 на localhost8880; готовность вывода сервера наблюдалась. Live browser/desktop resize проверяет ведущий отдельно.

Inventory review follow-up: Escape now dismisses temporary hover cards without requiring canvas focus; editable input/textarea/select/contenteditable contexts retain keyboard ownership. Arrow controls remain canvas-focus-only. Cell-height geometry reserves an additional26px for the footer so belt cells do not overlap its instruction text at300px canvas height. node --check scene.js pass; browser recheck pending leading reviewer.

## Приёмка Inventory Lab R23–R28

Ведущий проверил реальный Phaser в CUA: 1366×768, 1920×1080, 2560×1440. При 1366×768 все шесть выборов сохраняют canvas995×407; максимум чата даёт995×349, свёрнутый чат995×550. Текстуры6/6, без горизонтального overflow. Стрелка вниз прокручивает карточку, не страницу. Изображения и состояния: `var/inventory-lab/{1366-selected.png,1366-maxchat.png,1920.png,2560.png,states.json,example.png}`. Точные размеры проверены внутри same-origin iframe через отдельную QA-страницу; масштаб показа iframe не меняет его внутренний viewport. Полный набор hover-траекторий отдельно браузерно не заявляется.

Ревизор `/root/review_inventory_lab` независимо проверил R23–R28 и выявил Escape до фокуса canvas и недостаточный отступ под поясом. Оба исправлены и повторно приняты; новых блокирующих замечаний нет. Точные финальные утверждения сопоставлены с доказательствами. Независимые и повторные проверки ведущего: unittest3/3 OK, Ruff pass. Принятие владельцем ещё ожидается.

Текущий просмотр: http://127.0.0.1:8881/ (сервер session99872). Порт8880 был недоступен из браузера; использован альтернативный локальный порт без изменения сетевой политики. Исходный боевой стенд остаётся на8879. Это отдельный локальный mock в общей оболочке; игровое надевание/оценка, сеть и перенос в основную игру не реализованы этим продолжением.
## Продолжение Inventory Lab R29–R31

Уточнение пользователя: пояс наверху; рюкзак увеличивает число строк с количеством предметов и прокручивается вниз отдельно; правую карточку сохранить примерно текущей высоты. Пользователь сообщает о размытых шрифтах.

| ID | Требование | Реализация | Проверка |
| --- | --- | --- | --- |
| R29 | Фиксированный верхний пояс и отдельный прокручиваемый рюкзак, растущие по footprints строки без лимита40 | done | pass — independent reviewer |
| R30 | Сохранить6 настоящих мечей по умолчанию; explicit lab ?copies=N повторяет mock items с уникальными ID, не меняет каталог | done | pass — independent reviewer |
| R31 | Повысить чёткость текста, проверить Phaser resolution/координаты, не объявлять непроверенную причину размытия | done | pass — independent reviewer |

План: выделить masked bag viewport, размещать реальные grid_w/h по occupancy; размер ячейки зависит от ширины48–64px, высота не уменьшает текст/предметы. Колесо в рюкзаке меняет только bag scroll; карточка имеет отдельный scroll и неизменную внешнюю высоту. Прочитать Phaser Text resolution API, oversampling Text texture минимум2× и integer pixel positions; measured root browser DPR1/backing=CSS, поэтому CSS stretch/DPR не установлен как причина. Реализовать локальный query fixture expander, обновить клавиши на фактическую длину списка, targeted checks и browser proof ведущего. Режим независимого ревизора сохраняется.

### Наблюдения исполнителя R29–R31

Implementation done; browser и независимая приёмка pending. Scene: неподвижный пояс сверху, masked independent bag viewport, row-major occupancy учитывает grid_w/h; min5rows не является лимитом. Размер cell48–64 по ширине. Query copies1–100 расширяет только клиентский mock, default6 неизменен. Карточка остаётся прежнего внешнего размера. Text.setResolution минимум2×, integer text coordinates, roundPixels; renderer global resolution не изменялся, причина blur не утверждается.

node --check scene/data/boot pass; существующие offline server unittest3/3 pass. Новый node game_ui_lab/test_inventory_data.mjs pass: исходные6 не мутированы, 72 повторённых и72 смешанных footprints все размещены без пересечений/выхода за8 колонок, строки растут>5, недопустимые footprints/copies отклоняются. Диагностика window.inventoryLabState дополнена bagScroll/maxBagScroll/bagRows/itemCount/cellSize/bagBounds/textResolution. Копии fixture не меняют server catalog. Порт server default не менялся; текущий8881 проверяет ведущий.

### Проверка продолжения R29–R31

Ведущий: CUA, viewport1366×768 через QA iframe, 72 явно помеченных mock-предмета →27строк, cell62, canvas995×407. Реальное колесо в рюкзаке: bagScroll0→1591, pinned T4 и cardScroll0 сохранены. Колесо над карточкой: cardScroll111, bagScroll1591 сохранён. Клик по верхнему пустому поясу не выбирает скрытый под ним предмет. Default URL снова показывает исходные6 предметов. Артефакты: var/inventory-lab/scroll-proof.json, bag-scroll.png, top-belt.png. Упаковка fixture/72повтора/72разных footprints: node game_ui_lab/test_inventory_data.mjs pass; unittest3/3 OK. Первоначальный вызов JS-теста по неверному пути static/inventory исправлен на фактический game_ui_lab/test_inventory_data.mjs.

Чёткость: Text.setResolution(max(2,devicePixelRatio)), округление координат и camera.roundPixels. В текущем браузере DPR1, backing canvas=CSS; CSS stretch причиной не установлен. Не заявляется устранение субъективного размытия на мониторе пользователя или browser-проверка DPR>1. Renderer resolution не меняли.

Независимый ревизор /root/review_inventory_scrolling: R29–R31 pass с указанным пределом визуального вывода; самостоятельно изучил исходники, vendor API, артефакты и запустил placement test. Существенных замечаний нет. Точные финальные утверждения подтверждены. Это локальный mock, игровая ёмкость/вес/API не изменены. Ожидается принятие владельцем.

R32 browser proof: var/inventory-lab/character-belt.png и character-belt-detail.png;8слотов,beltBottom720.95,powerTop728.95,powerHeight30. Изменены только inventory boot/CSS/scene; shared character/combat файлы не менялись.

## Inventory Lab R34 — плавающая карточка

Уточнение пользователя: убрать постоянно выделенную правую панель карточки, отдать её место сетке инвентаря. Карточка появляется около наведённого предмета/указателя, закрепляется нажатием, закрывается Escape, вне карточки или × и остаётся внутри Phaser canvas. Предыдущие R32 (пояс HTML слева) и R33 (сетка заполняет высоту) сохраняются. Независимая ревизия продолжается.

R34 implementation pending / verification pending. План: использовать всю ширину рюкзака с адаптивным количеством колонок при читаемой ячейке; размещать floating card только при выборе, якорь фиксировать около предмета/указателя и clamp по границам canvas. Приоритет hover/click/wheel у popup над сеткой; отдельная прокрутка деталей и закреплённая карточка сохраняются. Проверить JS syntax и existing footprint tests; браузер/ревизия ведущего отдельно. Scope scene.js и эта запись, без shared/production правок.

R34 executor implementation done / verification pending: permanent card area and empty placeholder removed. Grid uses full available width with responsive column count and actualfootprint packing; visible cells still fill viewport height. Selected card anchors near pointer/item, prefers right then left, clamps to canvas12px inset, height min620/canvas-24. Popup receives pointer/wheel before underlying bag; hover stays open while pointer is inside it; click pins, ×/Escape/empty-space closes. HTML-left belt remains untouched. Diagnostics include columns and popupBounds (null initially). node --check scene.js pass; node game_ui_lab/test_inventory_data.mjs pass. Browser proof and independent review pending.

R34 принятие: CUA подтвердил отсутствие постоянной панели, hover T4, click-pin и Escape-close. Артефакты var/inventory-lab/no-side-panel.png, floating-hover.png, floating-pinned.png, floating-closed.png. Ревизор /root/review_inventory_scrolling: static + visual PASS, точные финальные утверждения подтверждены. Крестик/внешний клик подтверждены кодом, отдельный browser proof не заявлен. README обновлён по текущему размещению HTML-пояса. Implementation done / verification pass; owner acceptance pending.

R35: node syntax + placement tests pass. CUA screenshots hover-before.png (T1), hover-through.png (T3 под popup), click-through-pinned.png (закреплён T4) в var/inventory-lab/. Независимый reviewer /root/review_inventory_scrolling подтвердил static + visual PASS и точное итоговое утверждение. Owner acceptance pending.

## Inventory Lab R36–R38 — фильтры, вес и действия макета

Пользователь поручил в текущем стенде вкладки категорий, нижнюю полосу веса с «Разборка»/«Крафт», а закреплённой карточке — «Надеть»/«Заменить». Всё остаётся локальным макетом без изменения игрового состояния. Режим независимой ревизии сохраняется.

R36: вкладки с counts, фильтрация и пустые состояния; смена вкладки закрывает карточку и сбрасывает bag scroll. R37: фиксированная нижняя полоса веса/шкалы и кнопок; при отсутствии реального веса явно MOCK. R38: действие только в pinned footer карточки, отдельном от scroll; нажатие даёт закрываемое локальное уведомление, предметы/экипировка не меняются. Все implementation/verification pending.

Проверенные основания: ItemType в src/shared/enums/item_enums.py содержит weapon/armor/garment/accessory/consumable/resource/material/quest; существующий fixture генерирует sword с item_type=weapon. Special не тип каталога: вкладка обозначается будущей и остаётся пустой, не определяется редкостью. В frozen payload веса нет, поиск item resource schema не дал поля weight: числа стенда будут явно mock, не механика. План: локальная fixture metadata/category mapping + pure filter/weight functions, canvas tabs и fixed footer, modal notice, pinned action с учётом занятости HTML main_hand. Сохранить R35 hover pass-through, fullwidth grid, scrolling, fonts. Targeted node tests и browser/review ведущего.

R36–38 executor implementation done / independent verification pending. Реализованы7 вкладок на существующих ItemType (Special исключена как несуществующий тип), counts/empty states/reset selection и scroll; нижняя полоса MOCK16/30кг (2кг/меч +4кг worn) с независимостью от фильтра; закрываемые локальные уведомления «Разборка»/«Крафт»/«Заменить» и fixed pinned-action footer. Runtime DTO имеет aggregateweight, однако frozen fixture не передаёт его и реальных per-itemweights нет: числа намеренно помечены MOCK. Экипировка/рюкзак не мутируются. Порядок pointerdown: notice > pinned action/X/body > tabs/footer > bag, unpinned hover сохраняет R35 pass-through.

Проверки исполнителя: node --check scene/data/boot pass; node test_inventory_data.mjs pass (packing+filtergroups/emptycategories/no rarityspecial/mockweight/frozen nonmutation);3serverunittests pass. Browser proof и ревизия ведущего pending. Изменены только inventoryscene/data/boot, existing pureJS test, README и taskMD. Shared HTML equipment/chat/combat не менялись.

### Приёмка R36–R38

CUA: все7 вкладок проверены на1366×768; All/Weapons6, остальные0, общий MOCK вес16кг неизменен при фильтрации. Скриншоты и JSON: var/inventory-lab/controls-all.png,filter-empty.png,filter-proof.json,controls-1366.png. Кнопки Разборка/Крафт открывают закрываемые local notices (disassembly-notice.png,craft-notice.png). Pinned T4 показывает Заменить, нажатие открывает уведомление (controls-pinned.png,equip-notice.png); Esc закрывает. Надеть для свободной main_hand подтверждено по коду, browser-ветка свободной руки отдельно не проверялась. Никакие предметы/экипировка не меняются.

Ревизор /root/review_inventory_controls самостоятельно запустил node placement/filter/weight и unittest3/3; нашёл и повторно проверил исправление popup priority над tab/footer. ИтогR36–R38 PASS, точные финальные утверждения подтверждены. Ведущий повторил targetedtests:pass. Вес/лимит16/30кг и4кг надетого явно MOCK, не игровые значения. Runtime/backend/production не менялись. Implementation done / verification pass, owner acceptance pending.

R39 проверка: CUA desktop +1366×768, все7 SVG видны, подписи/counts не перекрываются; все вкладки переключены, counts6/6/0/0/0/0/0. var/inventory-lab/styled-tabs.png,styled-tabs-1366.png,styled-tabs-proof.json,styled-tabs-detail.png. Node syntax/data tests pass. Независимый /root/review_inventory_controls: static/tests/visual PASS, точный финальный текст подтверждён. Implementation done / verification pass; owner acceptance pending. Изменены только scene.js, Inventory README и MD; исходные SVG/атрибуция без изменений.

R40 implementation done / verification pass: node syntax, CUA All/Weapons переключение (var/inventory-lab/count-all.png,count-filter.png), независимый reviewer /root/review_inventory_controls static PASS и точный финальный текст подтверждён.

R41 done/pass: node syntax pass; CUA focusedcanvas computed outline none, headertext только Инвентарь. Screenshot var/inventory-lab/clean-header-footer.png + footer-fixed-detail.png. Независимый /root/review_inventory_controls static/visual PASS, финальные утверждения подтверждены. Sharedshell не менялся.

R42: по скриншоту переименовать кнопку Рюкзак · открыт в Инвентарь · открыт в Inventory Lab, без shared/production изменений. План: одна строка boot.js, syntax/browser/independent review. pending.

R42 done/pass: syntax + CUA button label confirmed, independent static review PASS. Screenshot var/inventory-lab/inventory-button.png.

R43: пользователь указал на отсутствующий крестик закрытия окна. Добавить X справа в header Inventory Lab; закрывает центральный инвентарь, левая кнопка открывает снова; чат/персонаж сохраняются. План template/CSS/boot local toggle, scene pause/resume. Независимый режим сохраняется, syntax/browser/reviewer. pending.

R43 implementation done: node syntax pass, CUA close/reopen confirmed in AX and var/inventory-lab/inventory-closed.png/inventory-reopened.png. Leftbutton locator timeout после успешного изменения label; fresh AX confirmed reopened. Independent static pass, visual pending.
R43 visual proof обновлён после отдельного repaint: canvas hidden=true/display=none, notice visible. Независимый reviewer итог static+visual PASS, точный финальный текст подтверждён.

## Inventory Lab R44 — чёрная Phaser-область после изменения высоты чата

Сообщение пользователя: изменение высоты чата делает Phaser чёрным. Диагностика ведущего: одиночный keyboard End (40%) пока воспроизводит нормальный экран; continuous drag и close/reopen ещё проверяются. Требование R44: исправить подтверждённую причину только в inventory lab, сохранив shared chat/combat и все существующие локальные состояния. Implementation pending / verification pending; независимая ревизия сохраняется.

План: сначала получить browser errors/context/render state при воспроизведении, сопоставить Scale.NONE resize и paused lifecycle с Phaser3.60 vendor. Текущий факт кода: ResizeObserver синхронно scale.resize; resize listener синхронно уничтожает/создаёт маски и Text-объекты; closed scene pause не отменяет scale events. Причина пока не установлена. После подтверждения — минимальное исправление, проверяемый lifecycle regression перед изменением при необходимости, browser drag/close/reopen/review ведущего. Не менять sharedchat/layout/combat и не подменять WebGL другим renderer без доказательств.

R44 диагностика: ведущий сообщил live1500×1245/Phaser3.60 WebGL, End40%, drag40→18→40 и close→Home11→reopen отрисовываются корректно; browser errors/warnings пусты. Исполнитель проверил порядок vendor Scale.resize/renderer viewport/scissor events и текущий paused lifecycle, но причинная ошибка не подтверждена. Код renderer/lifecycle не изменён; R44 implementation pending / verification unverified (не воспроизведено). Уточнение transient/persistent и точных шагов пользователя ожидается ведущим. Это не утверждение, что пользовательская ошибка исправлена.

R44 уточнение пользователя: чёрное изображение возникает временно только во время непрерывного перетаскивания границы чата и восстанавливается после отпускания. Разрешено ограниченное исправление resize performance, без утверждения persistent WebGL/context fault. План до правки: inventory-only ResizeCoordinator с requestAnimationFrame coalescing; во время body.is-chat-resizing не менять backing canvas, CSS временно растягивает последнюю отрисовку; после removal class — один resize на актуальные размеры. ResizeObserver/window resize и open используют общий scheduler; pagehide отменяет callbacks/disconnect. Проверка pure coordinator drag0calls/release1latest/coalescing/cleanup; browser непрерывного drag и ревизия ведущего.

R44 bounded implementation done / browser verification pending. Added inventory-only resize.js coordinator, boot ResizeObserver + bodyclass MutationObserver + window resize route through rAF; is-chat-resizing blocks backing resize. Scoped CSS temporarily fits existing canvas to host while dragging; native dimensions update on release. Open schedules reconciliation; pagehide disconnects observers/listeners and cancels pending frames. Existing [hidden] display:none remains effective. Shared chat/combat/renderer selection unchanged.

Regression evidence: new node test_inventory_resize.mjs initially failed dragbacking assertion29calls≠0 on unguarded coordinator (before fix); after drag guard passed. Covers zero drag calls, one latest-size release, burst coalescing, unchanged/zero-size guards and cleanup. node --check boot/resize pass; existing placement/filter/weight tests pass;3serverunittests pass. This addresses repeated resize during reported transient, not a claimed persistent GPU/context fault; browser continuous-drag proof and independent review pending.

R44 дополнительное указание пользователя до правки: во время перетаскивания показывать красивую картинку/надпись вместо чёрной области. План: inventory-only HTML overlay внутри host с существующим items.svg, semantic-token gradient/halo и текстом «Подстраиваем размер…» / «Отпустите границу, чтобы продолжить». Показывать только при body.is-chat-resizing и открытом inventory; закрытый экран/чат/персонаж не закрывать. Resize coordinator сохраняется; новых raster assets/анимаций/фильтров нет.

R44 resize-placeholder implementation: HTML overlay внутри inventoryhost, existing items.svg64px с token-based halo/градиентом и двумя согласованными надписями. CSS включает его только при drag и data-inventory-open=true; закрытие сохраняет отсутствие overlay, sharedчат/character не перекрываются. Временное CSSрастягивание canvas удалено, последнее изображение скрыто непрозрачным тематическим overlay. Coordinator tests и node --check boot pass; визуальная проверка ведущего pending.
R44 итог: user уточнил transientblack только пока держит границу, предложил красивую картинку/надпись. Реализованы themed existingbagSVG overlay и coalesced finalresize без backingresize во время drag. Rootдобавил pointer-events:none и QA-only resize-preview query для stillshot. CUA actualdrag -110px: release dragging=false,overlay=none,canvasHeight=hostHeight=648; screenshotresize-released.png. Заставка просмотрена через явный QA still-mode1366×768 (resize-placeholder.png/resize-placeholder-detail.png), это не выдаётся за screenshot midstrealdrag. Координатор meaningfulregressiontest initially29dragresizes→expected0, послеfix0drag/1finalpass; node syntax/data/servercheckspass. Independent /root/review_inventory_controls static/tests/visual PASS, finalclaimsconfirmed. Исходный blackframe у пользователя отдельно не воспроизведён и его GPUпричина не установлена. Implementation done / verification pass, owner acceptance pending.

## R45 — базовые свойства вспомогательной экипировки

Авторизованное продолжение item-task; независимая проверка сохраняется. Четыре концептуальные группы: оружие/вторая рука, броня, бонусная экипировка, магические украшения. Эта итерация меняет только базовые свойства, без миграции enum/types/slots/IDs/materials. Пояс: HP + quick slots; обувь: stamina + stamina regen; перчатки: anti-dodge + шанс критического триггера; плащ: HP regen + положительная защита среды. Бонусная экипировка не даёт armor power и штрафов. Броня и все affixes сохраняются. У кольца убрать базовый HP regen, у серьги stamina regen; прочие свойства украшений сохранить. Малые бонусы классов брони только обсуждаются.

План до кода: failing factory-to-actor и saved projection тесты; минимальные правки каталога/проекции; targeted items + character checks. Балансные стартовые допущения (не утверждённые отдельно пользователем): boots stamina10/regen1.5, gloves anti-dodge0.005/crit chance0.01, cloak HPregen0.5/cold6, belt HP10/quickslot1. Существующие положительные gravity1/bio2 сохраняются; heat-2 убирается. Материальное масштабирование остаётся текущим. Новых combat/world механик не вводить; текущую границу world-only параметров и регенерации проверить отдельно. Без DB/migrations/provider/commit/push/deploy и shared combat/UI изменений.

R45 уточнение после проверки фактического потребителя: пояс base_power=2 используется inventory.belt_inventory_cell_bonus для прежней ёмкости рюкзака, а не armor. Сохраняем 2 и существующее tier-масштабирование ёмкости; удалён только вводящий в заблуждение defense_type=physical. Предыдущий план power0 отменён до завершения реализации. Actor test явно подтверждает отсутствие armor и неизменный crit_power, inventory test — прежнюю ёмкость2 и quickslot1.

R45 реализация готова / независимая приёмка ведущего ожидается. Базы boots/gloves/cloak получили указанные положительные параметры; hp/stamina regen убраны только из баз ring/earring. Центральная intrinsic projection обновляет только явно перечисленные изменённые ключи; удаляет retired regen/heat penalty, сохраняет authored прочие значения/affixes, не мутирует исходный предмет и идемпотентна. Все IDs/types/slots/materials, armor resources и affix pools оставлены без изменения. Character/combat mapper/formulas не менялись. Regeneration проверена через реальные vitals и waterfall combat/outside; environment через actor raw, без заявления проверки мировых hazards.

Доказательства: до production edits новый test_bonus_equipment.py дал6 ожидаемых failures (belt power2, missing stamina/anti-dodge, cloak penalty, jewelry regen). После реализации — .venv/Scripts/python.exe -m pytest tests/backend/features/items/test_bonus_equipment.py tests/backend/features/items/test_jewelry_support.py tests/backend/features/items/test_item_factory.py tests/backend/features/items/test_affix_material_independence.py tests/backend/features/items/test_modifier_contracts.py tests/backend/features/character/runtime --no-cov -m unit -q --tb=short:91 passed,127 deselected. Отдельно bonus_equipment + jewelry_support + character/runtime/test_regeneration_modes.py без marker:22 passed (включая3 saved base projection проверки). Ruff на7 затронутых Python-файлах pass; scoped git diff --check pass (только CRLF normalization warnings).

Полный запуск items + character runtime прерван: зависание на первом async admin grant service; расширенный character без marker прерван на test_session_vitals_include_persisted_and_pending_anatomy. Это не считается провалом/успехом непрошедшей части. Полный project gate, DB, production и UI не проверялись. Первый pytest.exe/uv launcher выдавал uv trampoline failed to canonicalize script path; точный venv python.exe -m pytest работает. Отдельных log-файлов нет, результаты в tool output. Armor penalty regression tests прошли в выбранных91; исходные armor файлы исполнитель не менял, baseline hash до работы не снимался.
R45 независимая приёмка: /root/review_bonus_equipment PASS по всем требованиям. Самостоятельно61 тест:16bonus/jewelry+45factory/combatmodelregressions, всеpass; точные финальные утверждения проверены и подтверждены. Полный project gate не заявлен; broad async-suite исполнителя прерваны на stalled fixtures. После минимального усиления теста (явно передан belt mechanics.power=2) ведущий повторил16target —pass; production после независимой проверки не менялся. Свойства обновлены в исходниках/чистой runtime projection, без записей рабочейБД, миграций, переролла аффиксов, деплоя. Материальное масштабирование сохранено; численные основы стартовые. Типы/слоты/GARMENTenum не мигрировали. Новые armorclass bonuses не реализовывались. ИтогR45 implementation done / verification pass, reviewed-awaiting-acceptance.

R46 — оценить бонусы предметов по тирам после квадратичного роста атрибутов. Исходный запрос: «пересмотри предметы и их бонусы от тира, возможно после квадратичности их надо усилить». План: read-only численный анализ текущих основ/аффиксов T0–T7 и runtime формулы, сравнение атрибутов20→21 и нескольких уровней; отдельное рассмотрение физической защиты/оружия, свойств без атрибутного аналога и caps. Выдать проверяемый отчёт/таблицу и предложения. Не подменять «возможно усилить» массовым изменением баланса без установленной цели. Independent review продолжается; никакой БД/деплоя. pending.
R46 уточнение: пользователь задаёт ориентир основы одного Т7 предмета ≈ квадратичный вклад22–23статов безаффиксов. Ожидается обязательное уточнение: полный вклад22–23 либо delta20→22–23. До ответа зависимые изменения баланса не выполнять; параллельно считаются оба варианта.
R46 ответ владельца: ориентир — DELTA20→22–23 соответствующего атрибута для основы Т7 без аффиксов, не полный22–23. Численный расчёт runtime delta20→22.5: anti0.2898, mentalres0.1932,initiative4.8296,HP28.9773,stamina33.8068,staminaregen2.8977,hpregen1.1107. Текущие Т7 бонусы ресурсов уже выше ориентира; без nerf/массового множителя. План изменения: glovesanti0.005→0.04 (T7leather.272/cloth.26 в диапазоне20→22..23), ringmental.005→.03 (T7.21), earringinitiative.5→.7 (T7 4.9); прочие основы/крит/аффиксы/оружие/броня без изменений. Числа выбраны внутри указанного диапазона; сравнение только соответствующего свойства, не полного пакета атрибута. Обновить owning saved projection для mental/initiative как изменяемых базовых ключей, сохранить аффиксы/непринадлежащие значения/неизменяемость входа. Test-first/generationT0–T7/runtime/projection/independent review. pending.

R46 реализация исполнителя готова; независимая проверка ведущего ожидается. После явного уточнения пользователя целевой ориентир — прирост одного соответствующего параметра при attribute20→22–23, не полный вклад22. Изменены только три слабых базы: gloves anti_dodge_chance0.005→0.04; ring mental_resistance0.005→0.03; earring initiative0.5→0.7. T7 фактические прямые прибавки: leather gloves0.272 / cloth gloves0.26 внутри calculator-интервала0.2291..0.3518; ring0.21 внутри0.1527..0.2345; earring4.9 внутри3.8182..5.8636. Это сравнение отдельных свойств, не эквивалент всего набора характеристик. Crit trigger, другие свойства/ресурсы, weapon/armor/affixes и коэффициенты материалов не менялись.

Центральная intrinsic projection также владеет текущими mental_resistance кольца и initiative серьги: сохранённые старые значения заменяются масштабированными текущими без суммирования; retired HP/stamina regen по-прежнему удаляются только из implicit. Не принадлежащие изменению свойства и affixes сохранены, source dict не мутируется; идемпотентность проверена. Тесты сохранения authored mental resistance в старых тестах заменены на сохранение unowned control_resistance, новый mental проверяется отдельно.

Test-first: новый actual factory→actor→StatsWaterfallCalculator с attributes20/skills0 дал4 ожидаемых failures до source edits: gloves0.034/0.0325<0.2291, ring0.035<0.1527, earring3.5<3.8182. После правок все4 проходят. Дополнительный T0–T7 generation test проверяет положительное монотонное material scaling обеих категорий gloves и ingot jewelry. Expanded selected unit command прежнего R45:99 passed/129 deselected; bonus_equipment+jewelry_support+test_regeneration_modes без marker:32 passed. Ruff на6 изменённых Python files pass; scoped diff --check pass, только CRLF warnings. Последнее изменение после проверок — упрощение test assert >=previous, без изменения проверяемого условия. Балансный audit analysis.md/json не перезаписывался. Никаких DB/deploy/production действий.
R46 приёмка: /root/review_bonus_equipment независимые32теста PASS, actual delta во всех player profiles проверен, итоговые утверждения подтверждены. Исполнитель99unit selected/129deselected +32targetpass,Ruff6pass; ведущий26targetpass и regenerated afterreport. Числа Т7: glovesanti.26/.272,ringmental.21,earringinitiative4.9; в диапазонах delta20→22–23. Доизменения сохранены before.json/before.md, текущие analysis.json/analysis.md, русская сводка comparison.md. Неблокирующая неоднозначная фраза source unchanged исправлена на read-only генерацию отчёта. Оружие/броня/ресурсы/crit/аффиксы/materialmultipliers не менялись этой итерацией; полный project gate/живые данные не заявлены. Бонусы сравниваются по одному свойству до caps, не по полному пакету атрибута. Implementation done / verification pass; reviewed-awaiting-acceptance. БД/деплой не выполнялись.

R47 — владелец окончательно выбрал полный вклад0→20 атрибута как основу Т7 и экспоненциальный рост отТ0; последнее поручение: проверить даёт ли атрибут крит, сообщить если нет и продолжать работу. Источник ATTRIBUTE_MODIFIER_RULES/playerprofiles прямого crit_chance не содержит; текущий crit bonus оставляем без новой кривой. Это заменяет прежнюю цель R46 delta20→22–23; исторический отчёт не переписывать под новое решение.
План: для согласованных core implicit (beltHP, bootsstamina+regen, glovesanti, cloakHPregen, ringmentalres, amuletENregen,earringinitiative) чистая экспонента между текущей силойТ0 и runtimeвкладом20атрибута наТ7. НачалоТ0 сохраняется как техническое допущение реализации, не отдельное численное поручение пользователя. Цели без навыков/экипировки: HP109.0909,stamina127.2727,staminaregen10.9091 (без универсальной1),anti1.0909,HPregen4.1819 (включая естественныйHPвклад),mentalres.7273,ENregen9.0909 (внебой),initiative18.1818. Отдельные криты, среда, слоты/вместимость, аффиксы и оружие/броня не меняются. Сравнение по одному показателю до caps. Это разрешённое исключение из прежнего линейного material tier_mult для выбранных implicit; tier по-прежнему задаётся материалом. Единая формула и каталог, одинаковы для новой генерации и saved projection; preserve unowned/affixes/idempotence/nonmutation. Test-first endpoints/T0–Т7 геометрическая прогрессия/actualactorstats и независимая ревизия. Без DB/deploy. pending.
R47 documentation: narrowproject-owned items.md scalingguidance correction records authorized8implicitcurve exception; snapshot var/item-balance-review/items-guidance-before-r47.md, noentrypointrestructure/global/vendor edits. Rootreviewincludescontract consistency.

R47 implementation готова / независимая приёмка ведущего ожидается. Реализован один resources/support_progression.py: явные8T0/T7 опорных пар + чистая geometric функция. Factory и saved intrinsic projection используют её для выбранных core implicit. T0 сохранены по фактическим R46 items: HP8/stamina8/stamina_regen1.2/anti0.032/hp_regen0.4/mental0.024/en_regen0.8/initiative0.56. T7 равны полному вкладу соответствующей характеристики0→20; одинаковы для всех allowed material families. Остальные implicit, crit chance, slotcapacity, belt power, affixes, durability, materials, weapon/armor и combat formulas не изменялись.

Saved tier contract: embedded mechanics.material.tier → material ID lookup → mechanics.tier/metadata.tier/item.item_tier/generation.item_tier/mechanics.item_tier → T0 без сведений. Никакого угадывания по tier_mult/rarity. Fractional/nonfinite/invalid tier ValueError; integer clamp0..7. Исходные implicit_bonuses_base остаются авторским шаблоном;8опорных точек задаются в отдельном явном каталоге. Исключение из materialmult правила описано в docs/ru/backend/features/items/support_progression.md. Agent skills исполнитель не менял; их общее правило material multiplier теперь требует уточнения про R47 exception при разрешённом skill maintenance.

Test-first evidence уточнено: первый newtest прогон12failed;5из них были harness KeyError из-за отсутствующего нулевого значения в output calculator, исправлены get(key,0). До production edits meaningful failures:3regen curve +4saved tier. После harness correction старый linear producer воспроизведён только in-process monkeypatch(helper→None), все8corecurve tests ожидаемо failed наT1; production source не откатывался. С действующим helper все проходят. Не утверждается12meaningfultestfirst failures.

Проверки: expandedunit .venv/Scripts/python.exe -m pytest tests/backend/features/items/test_support_progression.py tests/backend/features/items/test_bonus_equipment.py tests/backend/features/items/test_jewelry_support.py tests/backend/features/items/test_item_factory.py tests/backend/features/items/test_affix_material_independence.py tests/backend/features/items/test_modifier_contracts.py tests/backend/features/character/runtime --no-cov -m unit -q --tb=short →122passed/129deselected. Отдельно support_progression+bonus_equipment+jewelry_support+character/runtime/test_regeneration_modes.py без marker →55passed. Проверены все8corebonuses на всех8tiers всехallowedmaterials, endpoints actualactor+waterfall, положительность/ускорение, unrelatedimplicit oldscale, saved6provenance routes/missing/invalid/bounds/idempotence/nonmutation. Ruff7Pythonfiles pass; scoped diff check pass (CRLFwarnings only). Полного project gate/liveDB/UI/deploy нет. R46 audit report не перезаписывался.
R47 финальная приёмка: independent /root/review_bonus_equipment55tests PASS + source/docs/guidanceconsistency, точные финальные утверждения отдельно сверены и подтверждены. Root49targettestsPASS. Исполнитель122selectedunit/129deselected+55targetPASS,Ruff7/scopeddiffPASS. Проектное items.md правило обновлено узким исключением8implicit, snapshotдоизменения сохранён. Документация support_progression.md актуальна; старые analysis.md/comparison.md отмечены историческимR46. Полныйprojectgate/liveDB/deploy не заявляются. Т0 сохранён,Т7полныйвклад0→20 в один сыройпоказательдоcaps; стаминарегенисключаетуниверсальную1,энергорегенэталонoutside. Прямого critchance bridge отатрибутовнет, критперчатоквне8кривых. Implementation done / verification pass; reviewed-awaiting-acceptance.

R48: владелец задаёт основу критперчаток наТ7≈20%. Реализация: отдельныйнеатрибутныйendpoint.20, T0.008сохранён, тажеэкспонента/sharedfactory+savedhelper. Значение до weaponmastery; полныйskillможетдать.40дообщегоcap. Остальные8кривых/аффиксы/оружие/броня не меняются. Test-first T0..T7/materials/saved, independentreview. pending.
R48 correction from owner: bonus glovesT7 +20p.p. is ADDITIVE, weaponmastery acts ONLYonweaponbase crit. Rootstatementbeforeabort thatbonusdoubleswasincorrect and rejected. CurrentCritStep multiplies total(mainhand+global) by1+skill; fix authorizedscope weapon-sourcecomponentonly; globalgloves/affixcrit isaddedafter. Preservecaps/force/restriction/triggers, magical/item sourcesnotweaponmastery. Addtestfirstchance weapon.05/global.20 skills0/.5/1→.25/.275/.30; offhandandsources/caps integration. Previouscritcurvetestname 'before_weapon_mastery' shouldrename independentbonus; no assertionbonusdoubling. InitialR48testwrittenandfailed/unfinishedduringinterrupt beforecatalogchange; inspectactualstate. NewR48corecurve20%stillrequested, expT0.008→T7.20. pending.
R48 rootguidanceplan: clarify8attribute curves+explicitcrit20% exception initems.md, andCritStepweaponpart-onlymasterynote inresolver-math.md. Snapshotsvar/item-balance-review/*guidance-before-r48.md. Nootherguidancechanges.

R48 implementation готова / независимая проверка ведущего ожидается. Исправлена подтверждённая ошибка CritStep: раньше агрегировались hand_crit+global_crit и вся сумма умножалась на mastery. Теперь physical main/off: hand_crit*(1+weapon_skill)+global_crit, затем прежний source cap. Глобальные бонусы (перчатки/affixes/etc.) не умножаются оружейным skill. Magic/item/elemental ветки не используют оружейный multiplier; прежний elemental выбор magicalchance, caps, ON_CRIT/ON_CRIT_FAIL и forced/cannot/suppress hooks сохранены. Offensive_lookup и accuracy не менялись; trace дополнен weapon_base/global_bonus для явной диагностики компонентов.

Gloves physical_crit_chance добавлен девятой кривой к тем же helper/projection: T0=.008 сохранён, T7=.20 независимо от cloth/leather, между ними geometric. Это отдельный явный бонус20%, без attribute bridge, без crit_damage или forcedcrit. Предыдущие8кривых сохранены. Docs support_progression.md теперь различает8атрибутных эталонов+1явныйcrit. Project skills обновляет ведущий, исполнитель их не менял.

Test-first: до production edits16selected:10expectedfailed/6passed. Доказанные различия: mainhand.05+global.20 skill.5 old.375 vs expected.275; skill1 old.50 vs expected.30; globalonly20% old40%; magic/item old24/30% vs expected12/15%; savedglovescurve oldT0.01 vs expected.008. После source changes39focused passed. Финальные проверки: engine folder +support_progression/bonus_equipment/jewelry_support/item_factory --no-cov -m unit →92passed/16deselected; direct crit_independence +resolver_trigger_contract +support_progression+bonus_equipment без marker →68passed. Actual integration T7factory обеихmaterialcategories→CharacterBuilder→StatsEngine→CritStep: skills0/.5/1 дают total25/27.5/30% при weaponbase5%, неизменный глобальный бонус20%; globalonly20% независим отskill. Savedprojection idempotent/nonmutating; всеT0–T7обеихкатегорий.

Existing runtime_processors exact tests test_crit_roll_uses_normalized_weapon_skill_and_default_cap +test_dual_wield_cross_cut_fixed_chance_scales_crit_power_with_skill →2passed. Более широкий -k crit собрал28, первые4passed, затем завис на async contact fixture; прерван, оставшиеся не считаются проверенными. Ruff5touchedPythonfiles pass; scopedgitdiffcheckpass. Без DB/production/deploy. Полныйproject gate не запускался.
R48 финальная независимая приёмка /root/review_bonus_equipment PASS:80targettests, generatedgloves→actor→CritStep bothmaterials skills0/.5/1global20%invariant;hand5%results25/27.5/30%;offhand/magic/item/caps/hooks/force/restriction покрыты. Root48targetpass. Исполнитель92selectedunit+68target+2existingprocessorpass; broad-kcritпрерваннасталлившемasyncfixture, полныйsuiteнеуспехнезаявлен. Истиннаяошибкаrootstatement 'перчатки20могут40' исправлена по прямому уточнению владельца: мастерство толькоhandweaponcrit,globalbonus additive. ЭкспонентаcritТ0.008→Т7.20, восемьатрибутныхкривыхбезизменений. Проектные items/resolverguidance синхронизированы, staleformula-bugrowисправлен, screenshotsнеприменимы backendchange. Exactfinalclaimsapproved; implementationdone/verificationpass/reviewed-awaiting-acceptance. БезБД/деплоя.

## R49 — удалить старые дополнительные бонусы и округлить базовые
Запрос пользователя: «да уберай и округляй». Удалить из innate баз обуви environment_gravity_resistance, перчаток environment_bio_resistance, плаща environment_cold_resistance, амулета debuff_avoidance; удалять их также при существующей runtime-проекции сохранённых предметов, не трогая аффиксы. Округлять механические результаты текущих экспоненциальных кривых: HP/stamina до целого, regen/initiative до десятых, вероятности до 0.1 процентного пункта (0.001 внутренней доли). Quick slots целые, прежняя схема 1–8. Формулу/материалы/конечные ориентиры и независимость крита от mastery не менять; равенство атрибутному эталону теперь с учётом округления. Не изменять БД/данные, UI, оружие, броню и аффиксы. Режим продолжающейся задачи: независимый ревизор. План: каталог и общий helper, saved projection, регрессии и документация; независимая проверка. implementation pending / verification pending.


R49 implementation готова / независимая проверка ведущего ожидается. Удалены четыре согласованных innate из garment/jewelry catalog; existing intrinsic projection владеет их retired keys и удаляет только из implicit соответствующей базы, сохраняя affixes/unowned/source dictionary. Общий support_bonus_at_tier округляет фактический результат геометрической формулы: HP/stamina precision0; regen/initiative1; chance fractions3. Опорные пары, material tier provenance/clamp, отсутствие повторного tier_mult и T7crit.20 не изменены. Initiative T0 после округления.6; HP/staminaT7 109/127. Slots1–8 проверяются прежними тестами. UI/БД/combat/affix definitions не менялись.

Test-first: перед production edits test_support_progression.py27tests дал20expected failures/7passed: округление всех8corecurves, savedtier values, critT1.0127→.013 и4retiredcatalogkeys. После реализации expanded selected unit (support_progression, bonus_equipment, jewelry_support, item_factory, catalog_service, crit_bonus_independence)127passed/6deselected. Дополнительный прогон без marker выявил5stale saved-value expectations плюс retiredgloves assertion; исправлены по R49. Итог support_progression+bonus_equipment+jewelry_support+character/runtime/test_regeneration_modes.py без marker59passed. Ruff9изменённыхPythonfilesPASS; import order catalog test приведён в порядок. Docs support_progression.md актуализирован. Всеtiers/materialcategories проверены через factory, retiredsaved через project_runtime_item и resolver, nonmutation/idempotence/unowned/affixes сохранены. Независимая ревизия и scoped diff check выполняются ведущим; полный project gate/liveDB/UI/deploy не заявляются.
R49 независимая приёмка /root/review_support_rounding PASS, замечаний нет: 107 целевых тестов, исходники/docs/guidance сверены. Root77focused PASS. Четыре старых innate удалены из каталога и saved projection, affixes/прочие implicit сохранены; девять кривых округляют реальные механические значения по принятой точности, crit20pp независим от mastery. Проекция идемпотентна/nonmutating. implementation done / verification pass / reviewed-awaiting-acceptance. БД/деплой не выполнялись; полный suite не заявлен.
