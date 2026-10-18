# Боевые навыки: оставшиеся пробелы после исправления поддержки

Дата: 18.10.2026. Проверенный код: `codex/monster-alpha`, `d620c420`.

Перед анализом выполнен fast-forward merge: `27562385` — checkpoint исходной работы, `d620c420` — отдельное исправление тактики/анатомии (23 файла). Checkpoint сохраняет исходный срез без formatter hooks; обычные hooks исправления прошли. Safety stash оставлен. Локальные `outputs/` и вложенный worktree не коммитились.

Проверены **16 combat-навыков**: шесть оружейных, четыре тактических, три брони и три поддержки. Небоевые, включая `skill_first_aid` и `skill_adaptation`, исключены. В ходе аналитики механика, коэффициенты, каталог и база не менялись.

**Вывод:** полностью пустых активных боевых навыков не найдено. Есть конкретные неполные цепочки у heavy armor, ranged combat, unarmed и anatomy XP; отдельно — отключённый resistance-эксперимент и устаревшие обещания. Отсутствие роста из-за cap или закрытого conditional gate не считается багом.

## Покрытие каждого навыка

«Работает» означает основные подтверждённые эффекты текущего каталога, а не все исторические дизайн-планы.

| Навык | Работающие потребители | Остаток / оценка |
| --- | --- | --- |
| `skill_swords` | Сборка урона, точность/компенсация штрафа, разброс, crit/item triggers | Основные эффекты работают; полный unlock триггеров по mastery — backlog |
| `skill_fencing` | Те же потребители с весами fencing и предметными крит-триггерами | Основные эффекты работают |
| `skill_polearms` | Сборка, точность, разброс, crit, оружейные финты/контроль | Основные эффекты работают |
| `skill_macing` | Сборка, точность, разброс, crit-триггеры тяжёлого удара/контроля | Основные эффекты работают |
| `skill_archery` | Сборка/точность/crit, критические боеприпасы, запас ammunition | Основные эффекты работают; позиционный дефект относится к ranged combat |
| `skill_unarmed` | Точность, эффективность силы `.5→3`, разброс `.5→.1` | Частично: изменённая сила не обновляет damage base; mastery anti-evasion приёмов нет |
| `skill_ranged_combat` | Начальная far-позиция, positioning/avoidance, skill-scaled смена дистанции, ограничение heavy armor | Частично: protective backstep marker теряется при закреплении следующей позиции |
| `skill_two_handed` | Стилевое подавление parry/block; компенсация accuracy penalty вместе с weapon mastery | Основные обещания работают; pressure proc имеет фиксированную вероятность `.25` |
| `skill_shield_mastery` | Блок, guard armor, shield counter/opening, запрет dodge со щитом | Новое ядро работает; каталог описывает старую reflection-модель; item shield-bash отсоединён |
| `skill_dual_wield` | Гарантированный offhand, качество оружия/штрафы, cross-cut, запрет рекурсивного offhand | Ядро работает; каталог ошибочно обещает `25→50%` после accuracy success |
| `skill_light_armor` | Dodge cap, armor mastery, окно counter после dodge и бонус вероятности | Основные обещания работают при доступных условиях |
| `skill_medium_armor` | Возврат dodge cap, armor mastery, условное окно counter после parry | Основные обещания работают |
| `skill_heavy_armor` | Armor mastery и hard dodge cap | Частично: resistance отключён экспериментом; subsequent-hit защита не получает индекс |
| `skill_parrying` | Parry base × `(1+4s)`, cap, defense XP, ranged line control | Основные обещания работают; без parry-базы навык её не создаёт |
| `skill_tactics` | После фикса: атрибутные evasion/anti-dodge/counter, обычные caps/окна и XP | Три исправленных эффекта работают; tactical-overwhelm остаётся backlog |
| `skill_anatomy` | После фикса: природный HP/EN-реген двух режимов, incoming heal один раз | Боевые эффекты работают; обещанный XP от принятого урона не начисляется |

Источники обещаний: [weapon mastery](../../src/backend/features/game_catalog/skills/resources/definitions/weapon_mastery.py), [tactical](../../src/backend/features/game_catalog/skills/resources/definitions/tactical.py), [armor](../../src/backend/features/game_catalog/skills/resources/definitions/armor.py), [support](../../src/backend/features/game_catalog/skills/resources/definitions/combat_support.py). Общие оружейные потребители: [assembler L55–87](../../src/backend/features/character/runtime/rules/base_power_assembler.py#L55), [accuracy L90–129](../../src/backend/features/combat/runtime/engine/resolver/support/offensive_lookup.py#L90), [crit L58–66](../../src/backend/features/combat/runtime/engine/resolver/steps/crit.py#L58).

## Подтверждённые проблемы исполнения

### R1. Heavy armor: защита повторных ударов не получает индекс

[Consumer L56–59](../../src/backend/features/combat/runtime/engine/resolver/steps/damage/elemental.py#L56) уменьшает damage только при `hit_index > 0`. `rg -n "hit_index" src` показывает лишь [default 0](../../src/backend/features/combat/dto/pipeline.py#L110), [декларацию разрешённой mutation](../../src/backend/features/game_catalog/combat/resources/common/pipeline_mutations.py#L113) и consumer. Runtime/catalog writer не найден. [Executor L318](../../src/backend/features/combat/runtime/processors/executor.py#L318) создаёт offhand без такого индекса.

В обычной цепочке main/offhand/counter эта защита не включается. Кроме того, dormant branch не проверяет надетую heavy armor: при ручном `hit_index=1`, флаге **light armor** и heavy skill `0/.25/.5/1` raw damage `100` становится **100/87.5/75/50**. Исправлять индекс следует вместе с equipment gate и явным определением серии ударов, иначе изученный heavy skill защитит light/naked актора. Актуальная справка ошибочно утверждает, что subsequent-hit protection уже работает.

### R2. Ranged combat: «Идеальный отскок» теряет владельца результата

[Каталог L16–18](../../src/backend/features/game_catalog/skills/resources/definitions/tactical.py#L16) обещает far на следующий размен. [Защитный trigger L62–69](../../src/backend/features/game_catalog/combat/resources/triggers/definitions/rules/styles.py#L62) пишет `next_ranged_position_override="far"` в результат **входящей атаки врага**.

Но [update_after_exchange L181–193](../../src/backend/features/combat/runtime/engine/ranged_position.py#L181) выбирает для лучника только его **исходящий source-result** и читает marker из него. Реальная цепочка `catalog trigger → defensive step → updater` дала: fired `style_ranged_perfect_backstep`, incoming override `far`, сохранённая next position **close**. Внутри текущего defensive step отскок работает; обещанная следующая позиция теряется.

Тест около [L5908](../../tests/backend/features/combat/test_runtime_processors.py#L5908) вручную кладёт marker в исходящий результат и не ловит реальную ownership-ошибку. Нужны recipient-based positional facts и тесты обоих порядков пары результатов, unidirectional и защиты без собственного удара.

### R3. Unarmed: изменённая сила не доходит до damage base

[_apply_unarmed_base L356](../../src/backend/features/character/runtime/combat_math_model.py#L356) копирует исходную Strength в `main_hand_damage_base`; [assembler L60–61](../../src/backend/features/character/runtime/rules/base_power_assembler.py#L60) пропускает unarmed. [Raw roll L38–48](../../src/backend/features/combat/runtime/engine/resolver/steps/damage/raw_roll.py#L38) умножает эту сохранённую базу на эффективность навыка.

При Strength `11`, skill `1` и temp `strength +11` итоговый `physical_strength_power` меняется **11→44**, но hand base остаётся **11**, а реальный диапазон damage — **29.7…33**. Предметные прибавки к самому атрибуту проходят ту же проблему. Рост навыка работает; изменённая сила не используется. Нужна единая каноническая strength-база с item/temp gains, debuffs, removal и dirty rebuild, без двойного добавления силы.

### R4. Anatomy: нет обещанного XP от принятого урона

[Каталог L33–34](../../src/backend/features/game_catalog/skills/resources/definitions/combat_support.py#L33) обещает XP от нанесённого и принятого урона. [Finalizer L204–211](../../src/backend/features/combat/runtime/services/experience_finalizer.py#L204) берёт anatomy power только из `_successful_offensive_action_power` — собственных успешных offensive counters.

`_add_combat_support_power({}, {"defense_armor":10})` не добавляет ничего; `{"main_hand_hit":1}` даёт anatomy/tactics по `.5` action power. Это дефект progression/обещания, а не повторная потеря регена/лечения. Нужен receive-only тест с фактической потерей HP, отдельно успешная defense без потери HP, DOT, shield absorb и защита от двойного начисления. Величину action power за полученный урон нужно утвердить, сохранив прочий accounting.

### R5. Unarmed: обещанные mastery anti-evasion приёмы отсутствуют

[Определение L96–97](../../src/backend/features/game_catalog/skills/resources/definitions/weapon_mastery.py#L96) обещает спецприёмы на высоком mastery. Но fallback [не назначает unarmed trigger L142–152](../../src/backend/features/character/runtime/combat_actor_input.py#L142), unarmed отсутствует в [WEAPON_MASTERY_FEINTS L208–214](../../src/backend/features/game_catalog/combat/resources/feints/availability.py#L208), а [weapon_techniques_for_skill L252–253](../../src/backend/features/game_catalog/combat/resources/feints/availability.py#L252) возвращает `[]`.

Sweep `0/.25/.5/1` сохраняет одинаковые **12 базовых финтов**; динамический consumer обещанного mastery-control не найден. Это недостающий контент/контракт: нужны согласованные приёмы или корректировка текущего обещания, а не выдуманный порог/коэффициент в диагностике.

### R6. Shield: предметный shield-bash trigger не имеет полной цепочки

[Щиты L22/42/62/82](../../src/backend/features/items/resources/base_item/weapons/offhand.py#L22) назначают `block.weapon_shield_bash_on_block`. [ContextBuilder L157–164](../../src/backend/features/combat/runtime/engine/context_builder.py#L157) активирует weapon-trigger атакующей руки, а [_analyze_defense L206–237](../../src/backend/features/combat/runtime/engine/context_builder.py#L206) не активирует defensive off_hand_trigger.

[Technical rule L317–326](../../src/backend/features/game_catalog/combat/resources/triggers/definitions/rules/weapon_triggers.py#L317) выставляет `chain.trigger_extra_strike`. [Executor L311–324](../../src/backend/features/combat/runtime/processors/executor.py#L311) обрабатывает counter/offhand, но не этот extra-strike. DTO/analytics/log consumers флага не исполняют удар. При forced block item flag false, fired только style-trigger, extra-strike false.

Это отсоединённая legacy item/catalog цепочка. Новый shield counter работает отдельно: подключать старый bash без решения о замене/сосуществовании опасно двойным ответным ударом.

## Намеренное отключение и расхождения описаний

**Heavy natural resistance.** Бонус собирается в [builder L320–331](../../src/backend/features/character/runtime/combat_math_model.py#L320), но [physical damage L34–37](../../src/backend/features/combat/runtime/engine/resolver/steps/damage/physical.py#L34) после расчёта принудительно задаёт mitigation `0`. Это явно помеченный временный resistance/suppression эксперимент. Natural resistance `.2/.225/.25/.3` при heavy skill `0/.25/.5/1`, incoming raw `100`, armor `0` оставляет **100 damage** во всех точках. До решения судьбы эксперимента этот бонус навыка бесполезен; включать его попутно нельзя.

**Heavy anti-crit.** В каталоге есть обещание снизить эффективность критических попаданий. Выделенного defensive heavy consumer в crit/calculate_crit_multiplier нет; общая броня уменьшает и критический урон. Требуется уточнить, обещан ли отдельный anti-crit эффект. Подтверждённая сломанная формула здесь не заявляется.

**Shield description.** [Каталог L51–54](../../src/backend/features/game_catalog/skills/resources/definitions/tactical.py#L51) всё ещё обещает Kinetic Reflection при провале блока и `50% absorption / 50% reflection`. [Runtime reference L40–58](../game-design/rules/skills/combat_runtime_reference.md#L40) и тест `test_counter_shield_block_no_longer_reflects_guard_power` фиксируют замену новой guard/block/counter моделью. Это дрейф описания; возвращать reflection по старому тексту неправильно.

**Dual description.** [Каталог L69–72](../../src/backend/features/game_catalog/skills/resources/definitions/tactical.py#L69) обещает `25→50%` после successful accuracy. [ContextBuilder L167–172](../../src/backend/features/combat/runtime/engine/context_builder.py#L167) ставит offhand без roll и до accuracy, [Executor L318–324](../../src/backend/features/combat/runtime/processors/executor.py#L318) его выполняет. На всех skill-точках forced miss сохраняет offhand flag. Текущее направление — гарантированный offhand с меняемым качеством/штрафами; [GS L155](../../src/backend/features/character/runtime/experimental_gear_score.py#L155) также считает гарантированный followup. Нужна синхронизация контракта, а не автоматическая отмена механики.

Полный item-trigger unlock по weapon mastery и tactical-overwhelm явно оставлены в [design backlog L113 и далее](../game-design/rules/skills/combat_runtime_reference.md#L113). Нельзя объявлять все пять вооружённых навыков сломанными из-за доступности trigger при skill0: навык уже увеличивает вероятность соответствующего crit-события.

## Численные контроли и GS

Для пяти вооружённых классов фиксированы Strength/Agility `11`, weapon power `10`, spread `.4`, accuracy penalty `.2`, crit `.1`. Равные атрибуты нейтрализуют различие весов классов:

| Skill | Hand base | Spread | Accuracy | Crit |
| --- | --- | --- | --- | --- |
| 0 | 12.75 | .4 | .4 | .1 |
| .25 | 14.8125 | .35 | .5447 | .125 |
| .5 | 16.875 | .3 | .6838 | .15 |
| 1 | 21 | .2 | .9 | .2 |

Parry при base `.05` даёт `.05/.10/.15/.25`. Эффективное поглощение armor `10`, skill `0/.25/.5/1`: light `4.67/6.69/8.63/12.28%`, medium `5.93/8.45/10.83/15.25%`, heavy `8.63/12.16/15.42/21.26%`. Поэтому heavy skill не полностью пустой.

Экспериментальный GS учитывает weapon damage/accuracy/crit, armor/parry/dodge, shield guard/counter и dual followup. Исправленную тактику получает из итоговых полей, анатомию — из combat regen; отдельного score за skill нет. Он явно не моделирует unarmed efficiency, ranged positioning, two-handed anti-parry/block, произвольный контроль и incoming healing. Равный GS не доказывает отсутствие этих боевых эффектов. См. [GS exclusions L300–306](../../src/backend/features/character/runtime/experimental_gear_score.py#L300).

## Проверки и воспроизводимость

Использовались ступени `0/.25/.5/1` при неизменных остальных входах, фиксированные RNG — только для достижения conditional ветки. Изменение raw/trigger отдельно не считалось выполнением эффекта: проверялись фактические consumers, а для позиции — обновление состояния. БД/Redis/сеть не использовались. Scratch-пробы и выводы сохранены в игнорируемом `var/combat-skill-coverage/`, versioned probe-инструменты не добавлены.

После merge выполнены **133 passed**:

```powershell
.venv/Scripts/python.exe -m pytest tests/backend/features/character/runtime/test_combat_math_model.py tests/backend/features/combat/test_damage_resistance_experiment.py tests/backend/features/character/runtime/test_combat_support_skills.py tests/backend/features/combat/test_received_healing_bonus.py tests/backend/features/monsters/instances/runtime/test_support_skill_snapshot_rules.py tests/backend/features/combat/test_combat_support_execution.py --import-mode=importlib --no-cov -q -p no:cacheprovider
```

Оружейная выборка — **13 passed / 259 deselected**:

```powershell
.venv/Scripts/python.exe -m pytest tests/backend/features/combat/test_base_power_assembler.py tests/backend/features/combat/test_runtime_processors.py -k 'base_power or crit_roll_uses_normalized_weapon_skill or accuracy_roll or unarmed_damage or archery_crit_queues_active_ammo or archery_crit_without_ammo' --import-mode=importlib --no-cov -p no:cacheprovider -q
```

Тактическая выборка — **16 passed / 251 deselected**:

```powershell
.venv/Scripts/python.exe -m pytest tests/backend/features/combat/test_runtime_processors.py -k 'dual_wield_style or dual_wield_cross_cut or ranged_combat_style or ranged_position_service_commits_next_position or shield_block or no_longer_reflects' --import-mode=importlib --no-cov -p no:cacheprovider -q
rg -n 'hit_index' src
rg -n 'trigger_extra_strike|weapon_shield_bash_on_block' src/backend/features/combat/runtime src/backend/features/items/resources
```

Выборки пересекаются, их нельзя складывать как число уникальных тестов. Они подтверждают работающие пути и не заменяют новые падающие regression tests для R1–R6. Шесть прежних падений широкого прогона отдельно воспроизведены на pre-fix main и не зарегистрированы здесь как новые skill bugs. Полный project gate для аналитики не запускался. Windows asyncio-тесты запускались вне sandbox из-за зависания локального `socketpair`; это не обращение к внешнему сервису.

### Репродукция R2: код для запуска из корня репозитория

```python
import runpy
h = runpy.run_path("tests/backend/features/combat/test_runtime_processors.py")
a, b = h["actor"](1,"a"), h["actor"](2,"b")
a.loadout.layout.update(main_hand="skill_archery", tactical_style="skill_ranged_combat",
                        tactical_style_trigger="dodge.style_ranged_perfect_backstep")
a.stats = h["stats"](skills={"skill_ranged_combat": .5})
b.stats = h["stats"]()
a.statuses.effects.append(h["ActiveEffectDTO"](uid="p",effect_id="ranged_position",
    source_id=1,expire_at_exchange=1,params={"position":"mid"}))
move=h["CombatMoveDTO"](move_id="m",char_id=2,strategy="exchange",
                       payload=h["ExchangePayload"](target_id=1))
c=h["ContextBuilder"].build_context(b,a,move)
h["MathCore"].roll_chance=staticmethod(lambda chance:(0,True))
h["ranged_position_defense_step"].run(b.stats,a.stats,c,c.result)
h["RangedPositionService"].roll_next_position=staticmethod(lambda **kw:"close")
h["RangedPositionService"].update_after_exchange([
    (b,a,c.result),(a,b,h["InteractionResultDTO"](source_id=1,target_id=2))])
print(c.result.fired_triggers, c.result.action_facts["next_ranged_position_override"],
      a.statuses.effects[-1].params["position"])
```

Получено: `['style_ranged_perfect_backstep'] far close`. Нужен far; случайный fallback намеренно зафиксирован в close, чтобы различить ветви.

### Репродукция R3: код для запуска из корня репозитория

```python
from copy import deepcopy
from src.backend.features.character.runtime.combat_math_model import CharacterCombatMathModelBuilder
from src.backend.features.combat.runtime.engine.stats_engine import StatsEngine
from src.backend.features.combat.dto.pipeline import PipelineContextDTO, InteractionResultDTO
from src.backend.features.combat.runtime.engine.resolver.steps.damage._state import DamageState
from src.backend.features.combat.runtime.engine.resolver.steps.damage import raw_roll
skills={"skill_unarmed":1.0}
raw=CharacterCombatMathModelBuilder().build_raw(attributes={"strength":11},skills=skills)
for bonus in (0,11):
    changed=deepcopy(raw)
    changed["attributes"]["strength"]["temp"]={"buff":f"+{bonus}"}
    stats,_=StatsEngine.build_stats(raw=changed,skills=skills,loadout={"layout":{"main_hand":"skill_unarmed"}})
    ctx=PipelineContextDTO()
    ctx.flags.meta.source_type="main_hand"
    ctx.flags.meta.weapon_class="unarmed"
    ctx.flags.damage.physical=True
    state=DamageState()
    raw_roll.apply(state,stats,stats,ctx,InteractionResultDTO())
    print(bonus,stats.mods.physical_strength_power,stats.mods.main_hand_damage_base,state.min_d,state.max_d)
```

Получено: `0 11 11 29.7 33` и `11 44 11 29.7 33`.

## Предлагаемый порядок следующих работ

1. Heavy subsequent-hit: определить scope серии, источник hit_index и heavy equipment gate. Тестировать executor → pipeline → commit на main/offhand/extra/counter и light/naked отрицательных контролях.
2. Ranged backstep: закреплять positional marker по получателю; проверить порядок пары, отсутствие ответного удара и single application.
3. Unarmed: исправить final Strength-базу и dirty rebuild, сохранив согласованный масштаб/эффективность силы.
4. Anatomy progression: согласовать XP за принятый урон и добавить его без повторного учёта/изменения остальных наград.
5. Контентным решением закрыть unarmed mastery-control, shield item legacy trigger и устаревшие shield/dual описания.
6. Отдельно решить судьбу resistance-эксперимента и heavy anti-crit обещания. Аналитика не включает их незаметное включение или новые коэффициенты.
