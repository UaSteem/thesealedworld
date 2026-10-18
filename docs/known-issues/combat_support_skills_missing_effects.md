# BUG: заявленные эффекты skill_tactics и skill_anatomy не подключены

Статус: исправление реализовано локально 18.10.2026; первоначальная диагностика сохранена ниже как история дефекта.

## Исправление после диагностики

По уточнению владельца навыки усиливают вклад атрибутов, а не прямые предметные бонусы. Для нормализованного `s ∈ [0, 1]`:

| Эффект | Реализованная формула |
| --- | --- |
| Тактика: уворот | природная часть × `(1+s)`; максимум ×2 |
| Тактика: антиуворот | природная часть × `(1+3s)`; максимум ×4 |
| Тактика: контратака | природная часть × `(1+4s)`; максимум ×5; старые капы и окна сохранены |
| Анатомия: HP/Energy вне боя | природный реген × `(1+3s)`; максимум ×4 |
| Анатомия: HP/Energy в бою | природный реген × `(1+s)`; максимум ×2 |
| Анатомия: входящее HP-лечение | `received_healing_bonus += s`, затем multiplier `max(0, 1+bonus)` один раз у получателя |

Прямые предметные прибавки к тактике и регену не масштабируются. Предметные прибавки к самим атрибутам участвуют в обычном расчёте атрибута. Дополнительный бонус анатомии к player max-HP recovery baseline исходит из attribute-derived HP; предметный HP не умножается навыком. Stamina не изменена; HP-реген монстров остаётся выключен. Атрибутный EN-реген игрока по существующему правилу не работает в бою; анатомия не создаёт его из нуля.

`rules/support_skills.py` формирует правила, общий waterfall применяет их к нужному слою. Существующий GS получает уже собранные поля, отдельного score за уровень навыка не добавлено. Внебоевые vitals теперь получают те же persisted/pending skills при bootstrap, refresh и restore. Все producers входящего лечения используют один helper; commit не усиливает сумму повторно. Direct heal и restore_hp направляют явную resource application получателю, устраняя прежнюю ошибку source-only применения.

Регрессионные тесты сохранены как обычные tests, probe-инструменты не возвращались:

```powershell
python -m pytest tests/backend/features/character/runtime/test_combat_support_skills.py tests/backend/features/character/runtime/test_anatomy_vitals.py tests/backend/features/combat/test_received_healing_bonus.py tests/backend/features/combat/test_combat_support_execution.py --import-mode=importlib --no-cov -p no:cacheprovider
```

Изолированные проверки охватывают ступени 0/.25/.5/1, предметные и атрибутные слои, повторный rebuild, монстров, оба режима регена и GS. Исполнение через `AC → lifecycle snapshot → Executor/Pipeline → commit` подтверждает лечение 50/62/75/100 HP при фиксированных остальных входах и реальные изменения dodge/anti-dodge/counter. Сохранённые монстры пересобирают только слой support rules из своих навыков при чтении, без изменения БД/экипировки/клановых вкладов. Старые замороженные player raw-входы и уже начатые боевые снимки нужно пересобрать для новой версии `combat-math:2026-10-18.support-skills`; в ходе задачи БД и сохранённые профили не переписывались.

Проверка исправления: **169 passed** в новой и смежной направленной выборке; Ruff проходит. Расширенная выборка Combat/Character/Monster-runtime: **1096 passed, 6 failed**. Все шесть падений отдельно воспроизведены на исходной `codex/monster-alpha` без этого исправления: четыре проверки подавления/брони, старая фиксированная строка версии в victory-finalizer и старое ожидание HP-регена без max-HP baseline. Их исправление не включено в эту задачу. Логи и отдельный task-only patch сохранены в `var/` worktree. Полный project gate не заявляется.

## Историческая диагностика (до исправления)

## Проверенный срез и границы

Проверены текущие файлы рабочего checkout `codex/monster-alpha` поверх `eca85cf1`, включая незакоммиченные изменения расчётов регена, монстров и экспериментального GS. Отдельная ветка диагностики: `codex/support-skills-diagnosis`. Чистый HEAD `eca85cf1` не содержит весь проверенный срез, в частности экспериментальный GS. Это существенно для воспроизведения: результаты относятся к сохранённому срезу, а не к одному SHA.

В исходном checkout ничего не изменено. База, Redis, баланс, каталог и runtime не изменялись. В итоговый merge входит только этот документ. По просьбе владельца диагностические probe-скрипты удалены из versioned tools; их копии сохранены в локальном срезе для воспроизведения. Локальный воспроизводимый срез исходников, тестов, скриптов и двух входных профилей сохранён в игнорируемом `var/diagnosed-source/` отдельного worktree; JSON результатов и SHA256-манифест находятся в его родительском `var/`. Этот срез не входит в Git. Ссылки и номера строк ниже относятся к нему; после merge соседних изменений номера могут сместиться.

## Навык → эффект → потребитель

| Навык | Обещанный эффект | Фактический потребитель | Результат |
| --- | --- | --- | --- |
| `skill_tactics` | Уворот | `EvasionStep`: `def_.mods.evasion`, `dodge_cap`, `target_evasion_mult` | Поля работают; навык не изменяет их и не читается шагом. Эффект навыка не работает. |
| `skill_tactics` | Антиуворот | `EvasionStep`: `atk.mods.anti_dodge_chance` вычитается из уворота | Поле работает; связь с навыком отсутствует. |
| `skill_tactics` | Контратака | `CounterCheckStep`: `counter_attack_chance/cap`, затем условные бонусы брони/финтов | Потребитель работает при открытом окне; вклад навыка отсутствует. |
| `skill_anatomy` | Естественное восстановление в бою | Waterfall → `combat_*_regen` → `AbilityService` → `MechanicsService` | Существующий реген работает, изменения навыка его не меняют. |
| `skill_anatomy` | Естественное восстановление вне боя | Waterfall → `outside_*_regen` → `CharacterVitalsCalculator` | Существующий реген работает, изменения навыка его не меняют. |
| `skill_anatomy` | Входящее лечение | `HealingStep`, prepared heal, HOT, lifesteal → применение HP | Вклад навыка отсутствует; `received_healing_bonus` также не потребляется этими путями. |

Обещания взяты из актуального [каталога, anatomy L22 и tactics L38](../../src/backend/features/game_catalog/skills/resources/definitions/combat_support.py#L22). Он обещает восстановление/входящее лечение и anti-evasion/уклонение/контратаку, но не задаёт коэффициенты, охват HP/EN/stamina, правила капов и охват источников лечения. `stat_weights` там относятся к росту навыков, а не к формуле боевого бонуса. [Runtime reference L97–98](../game-design/rules/skills/combat_runtime_reference.md#L97) прямо относит полную модель анатомии и тактики к незавершённому design direction. Описание не использовано как доказательство реализации.

## Прослеженный путь данных

**Персонаж.** Каталог → [SkillProgress L16–31](../../src/backend/features/character/models/skill.py#L16) (`skill_key`, `total_xp`, unlock/state) → [CharacterStateIntegrator L293–305](../../src/backend/features/character/integrations/character_state_integrator.py#L293), который переносит unlocked записи в session как `{xp, unlocked, state}` → session `skills: dict` ([session L148](../../src/backend/features/character/schemas/session.py#L148)) → [flat skills и pending progress L20–33, L442–473](../../src/backend/features/character/runtime/combat_actor_input.py#L20). Оба значения передаются в `CharacterCombatMathModelBuilder.build_raw` и отдельно в `skills` снимка. [Raw builder L94–119 и L231–236](../../src/backend/features/character/runtime/combat_math_model.py#L94) обрабатывает экипировку, оружейные/броневые навыки, но не производит бонусы этих двух навыков. [Waterfall L88–140](../../src/backend/core/calculators/stats_waterfall_calculator.py#L88) считает атрибуты, source/temp и профили регена; прямого входа skills у него нет. [StatsEngine L85–103](../../src/backend/features/combat/runtime/engine/stats_engine.py#L85) вызывает waterfall, `BasePowerAssembler`, затем создаёт `ActorStats.mods` и `CombatSkillsDTO`. Навыки сохранены в [DTO L66–67](../../src/shared/schemas/modifier_dto.py#L66), но сам факт доставки значения не даёт эффекта.

**Монстр.** [Goblin chief L7](../../src/backend/features/monsters/catalog/families/goblin_catalog/clans/base/members/goblin_chief.py#L7) содержит оба навыка. [Generation fields L78–88, L210–227](../../src/backend/features/monsters/catalog/materialization/generation_fields.py#L78) выдаёт нормализованные значения; для T2 оба равны `0.2857`. [Skill contract L7–24](../../src/backend/features/monsters/catalog/skill_contract.py#L7) их не исключает. [Generation builder L402–423, L466–515](../../src/backend/features/monsters/catalog/materialization/generation_builder.py#L402) передаёт их в raw и combat input. [Monster math builder L61–85](../../src/backend/features/monsters/instances/runtime/combat_math_model.py#L61) использует общий character builder. [Monster actor input L16–46](../../src/backend/features/monsters/instances/runtime/combat_actor_input.py#L16) сохраняет prebuilt input в снимок. Далее применяется тот же StatsEngine; оба навыка доходят до `ActorStats.skills`.

**Боевые потребители.** [Evasion L55–65](../../src/backend/features/combat/runtime/engine/resolver/steps/evasion.py#L55), [counter L31–64](../../src/backend/features/combat/runtime/engine/resolver/steps/counter_check.py#L31), [порядок шагов L43–69](../../src/backend/features/combat/runtime/engine/resolver/orchestrator.py#L43). Контратака условна: окно открывается после соответствующей защиты; light armor, medium armor, shield и финты имеют свои правила. Эти навыки нельзя заменять `skill_tactics`. Диагностика принудительно открывает окно отдельным контролем, а не делает вывод из отсутствия контратаки в обычном бою.

## Прямые и косвенные применения

- [Experience finalizer L210–211](../../src/backend/features/combat/runtime/services/experience_finalizer.py#L210) начисляет опыт обоим навыкам. Это рабочий consumer прогрессии, не заявленных боевых эффектов.
- Проверены динамический [trigger_chance L45–56](../../src/backend/features/combat/runtime/engine/resolver/support/trigger_activator.py#L45), триггеры, условия, правила и ресурсы каталога. Механизм `chance_skill_key` допускает чтение навыка через `getattr`, но актуальные определения не привязывают его к anatomy/tactics; используемый style key относится к `skill_ranged_combat`. Waterfall source-выражения не получают отдельную среду со skills.
- [Feint availability L243–329](../../src/backend/features/game_catalog/combat/resources/feints/availability.py#L243) не открывает финты через эти два навыка: текущий `build_known_feints` выбирает их по loadout/weapon/style. Утверждение reference L80–81 о skill_tactics/anatomy устарело; в ходе этой задачи справка не переписывалась.
- Отдельно найдены UI, starting imprints, admin generation, Chaos actor preset и Rift tunables. Это определения/передача/другой домен, не применение трёх бонусов тактики или восстановления анатомии.
- AI-тактика, оружейные tactical skills (`skill_two_handed`, `skill_shield_mastery`, `skill_dual_wield`, `skill_ranged_combat`) и `cost.tactics` финтов не являются `skill_tactics`.

## Воспроизведение и наблюдения

Диагностические скрипты фиксируют наблюдаемое поведение; это не новые regression tests, закрепляющие отсутствие эффектов навсегда. Все прогоны работают в памяти.

1. `probe_combat_support_skills`: два набора × шесть персонажей × два навыка × четыре уровня = **96 строк**, **0 изменений** полного raw, waterfall, итогового `ActorStats.mods`, loadout, полного GS breakdown и контролируемых resolver-результатов относительно уровня 0. Другой навык, атрибуты, предметы и symbiote фиксированы. Проверено сохранение нового значения в `ActorStats.skills`; flat, nested `{xp}` и эквивалентный pending delta дают одинаковый полный actor input. На каждую точку: восемь одинаковых seed в роли атакующего и защищающегося; дополнительно прямые проверки evasion/counter с открытыми условиями и лечение `100 → 100`.
2. `probe_support_skills_monsters_gs`: skills актуального chief T2, фиксированные атрибуты по 10, синтетическая неизменная экипировка/loadout; по одному навыку 0/.25/.5/1. Все **8 строк** сохраняют новое значение в snapshot/ActorStats, но дают одинаковые raw/mods/resolver/GS. GS **27.494** во всех точках. Это проверка catalog skill projection → builder → snapshot, а не создание DB-инстанса/нового encounter.
3. `probe_support_skills_recovery`: **24 точки** (два навыка × player/humanoid/beast × четыре уровня) и **4 контроля** `received_healing_bonus`. Одинаковы: self-heal **20**, prepared heal **18**, HOT **7**, принудительно успешный lifesteal **10**. До капа HP далеко; фактическая прибавка совпадает с заявленной. Для player raw `hp=100, hp_regen=2` даёт `2.5` в обоих режимах; боевое применение округляет до **+2**, четыре внебоевых тика дают **+10**. У monster HP regen остаётся 0. Изменение `received_healing_bonus` от 0 до 1 не меняет ни один проверенный результат.
4. Положительные контроли resolver: `evasion=.4`, антиуворот `0→.2` дают шанс `.4→.2`; `counter_attack_chance=.1→.3` передаётся в фактическую проверку как `.1→.3`. Отсутствие реакции навыка не объясняется неработающим стендом.

Входы (SHA256):

- `reference-six-full-t2-goblins-t2/inputs.json`: `12b158aab01cec1bb81d0b3dbbb51775ddf2b37f4d3cd0bf914079ea94c65ddd`.
- `reference-six-t2-developed-skills/inputs.json`: `f0952115a90857fe318a1ff8174cebced0e036b0e411522e43bde848df94715a`.

### Лечение, реген и двойное применение

[HealingStep L36–54](../../src/backend/features/combat/runtime/engine/resolver/steps/healing.py#L36) берёт magical damage/override, множитель crit и округление; не читает target received bonus. Дополнительные реальные пути — [prepared heal L877](../../src/backend/features/combat/runtime/engine/ability_service.py#L877), [combat regen L1324](../../src/backend/features/combat/runtime/engine/ability_service.py#L1324), [lifesteal L1338](../../src/backend/features/combat/runtime/engine/ability_service.py#L1338), [periodic tick L45](../../src/backend/features/combat/runtime/engine/mechanics_service.py#L45), [HP commit L225](../../src/backend/features/combat/runtime/engine/mechanics_service.py#L225). Вне боя [vitals L140–180](../../src/backend/features/character/runtime/vitals.py#L140) использует outside regen и число тиков.

Текущий бонус навыка не применяется ни один раз; доказательств двойного применения нет. Дополнительная база player `maxHP * .005` вычисляется один раз на режим ([waterfall L111–140](../../src/backend/core/calculators/stats_waterfall_calculator.py#L111)); generic/outside alias не складываются между собой. Prepared heal/lifesteal не удваиваются от присутствия `healing_final`: фактическая HP-дельта совпадает с resource application. Это ограниченный прогон, не доказательство для всех комбинаций эффектов.

У монстров HP-реген принудительно обнулён в waterfall L128–129. Исправление анатомии не должно автоматически включать его. Охват входящего лечения (включая HOT, lifesteal, предметы и лечение другим актором) нужно утвердить отдельно. Проверки commit здесь используют self-heal и явные recipient applications; маршрутизация произвольного target-heal не объявляется проверенной. Наблюдаемое применение generic `resource_changes` к source — отдельный вопрос, не причина отсутствия bonus и не часть предлагаемого исправления.

### Экспериментальный GS

[GS L115](../../src/backend/features/character/runtime/experimental_gear_score.py#L115) учитывает evasion с reference anti-dodge и запретом dodge для shield; [L204–249](../../src/backend/features/character/runtime/experimental_gear_score.py#L204) — условные counters и anti-dodge proxy; [L259–283](../../src/backend/features/character/runtime/experimental_gear_score.py#L259) — сумму боевого регена и итог компонентов. Отдельной надбавки за skill_tactics/anatomy нет.

Контроли при light armor mastery=1 и ненулевом dodge: evasion `.2→.3` даёт **+0.594 GS**, anti-dodge `0→.2` — **+0.627**, counter `.2→.4` — **+0.188**. Combat HP/EN/stamina regen `+2/+3/+4` дают ровно **+2/+3/+4 GS** в support, без повторного добавления в EHP. Generic/outside HP regen=99 и received bonus=.5 дают нулевую дельту — они вне текущей модели GS. GS является оценкой относительно эталона, а не доказательством успешного боевого срабатывания. Будущее исправление должно менять собираемые поля один раз; отдельно начислять GS за уровень навыка не требуется.

### Команды

Локально точный проверенный срез сохранён независимо от чистоты merge-ветки:

```powershell
Set-Location D:/Workspace/personal/pets/TurnBasedMMORPG/.worktrees/support-skills-diagnosis/var/diagnosed-source
$probePython = 'D:/Workspace/personal/pets/TurnBasedMMORPG/.venv/Scripts/python.exe'
& $probePython -m tools.diagnostics.probe_combat_support_skills var/reference-six-full-t2-goblins-t2/inputs.json var/reference-six-t2-developed-skills/inputs.json
& $probePython -m tools.diagnostics.probe_support_skills_monsters_gs
& $probePython -m tools.diagnostics.probe_support_skills_recovery
& $probePython -m pytest tests/backend/features/monsters/instances/runtime/test_combat_actor_input.py tests/backend/features/monsters/catalog/materialization/test_generation_fields.py tests/backend/features/monsters/catalog/resources/test_family_combat_skills.py tests/backend/features/character/runtime/test_experimental_gear_score.py --no-cov -q -p no:cacheprovider
& $probePython -m ruff check --no-cache tools/diagnostics
```

После фиксации соседних runtime-изменений эти же модули можно запускать из корня актуального checkout, предоставив сохранённые inputs. На голом базовом `eca85cf1` они не воспроизводят этот срез: экспериментальный GS/новые режимы регена требуют соответствующих исходников.

Проверка четырёх указанных pytest-файлов: **56 passed**. Ruff трёх диагностических модулей: **passed**. Дополнительные recovery/regen pytest-проверки напечатали PASSED для 24 assertions, но процесс завис после последнего теста и был прерван; успешным gate это не считается. Узкий повтор с 19 regen-проверками показал то же поведение. Скрипт восстановления завершился нормально с exit 0. Полный project gate не запускался: runtime в этой задаче не меняется; вывод относится к направленной диагностике.

## План исправления и тестов (не реализован)

1. Утвердить формулы тактики и анатомии, капы, охват ресурсов/лечения и правила монстров. Не выводить коэффициенты из `stat_weights` и не переносить legacy шкалу 0..100 в значения 0..1.
2. До runtime-правок добавить падающие тесты: один навык 0/.25/.5/1 при фиксированных входах; положительная ожидаемая дельта только согласованных полей, проверка caps и несвязанных показателей. Общая сборка character/monster, flat/nested/pending skills.
3. Формировать постоянные бонусы в общем слое raw/skill rules с явной source-меткой; не добавлять их отдельно в encounter builder, resolver и GS. Проверить повторный rebuild, dirty_stats, снятие temp effects: бонус не накапливается.
4. Проверить `builder → waterfall → ActorSnapshot → resolver → commit`: уворот с отключённым shield, антиуворот с ненулевым уклонением цели, counters с открытым и закрытым окном; затем реальный `executor → pipeline → commit`. Сохранить существующие XP и правила оружейных tactical skills.
5. Для лечения утвердить один уровень применения incoming bonus и его получателя; добавить self/other target, direct heal, prepared heal, HOT, lifesteal, item, crit, overheal/cap, no-heal и dead-recipient cases. Подтвердить фактическую HP-дельту и отсутствие повторного множителя в producer/commit.
6. Проверить оба режима регена и aliases, tick/round rounding, отсутствие начисления outside regen в бою, сохранение запрета monster HP regen. Добавить GS-тесты на уже собранные поля, отсутствие отдельного skill score и двойного учёта support/EHP.
7. Повторить ограниченные сравнения двух T2-профилей и монстров, затем релевантные combat/character/monsters suites. Баланс и формулы остаются отдельной утверждаемой задачей.

## Состав объединяемого изменения

Итоговый diff диагностической ветки содержит только этот документ. Probe-скрипты удалены из tools; воспроизводимый локальный срез и JSON остаются в игнорируемом `var/` worktree. Исходный dirty checkout и его изменения runtime не включаются в коммиты этой задачи. Перед объединением прежняя untracked-версия bug-документа сохраняется отдельно; изменения механики, коэффициенты и база остаются вне этой диагностики. Сам баг всё ещё открыт и критичен для интерпретации текущих боевых прогонов.
