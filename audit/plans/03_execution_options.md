# Technical Hardening — варианты исполнения и решения владельца

Дата плана:10.10.2026; источники09.10, чтение09–10.10.2026. **Документирование → STOP.** Ни один вариант не выбран автоматически; реализация каждого согласованного пакета требует отдельного задания. Источники: [scope](00_technical_hardening_scope.md), [matrix](01_technical_findings_matrix.md), [37 packages](02_technical_work_packages.md), [K/W/E backlog](04_skill_enforcement_backlog.md).

## 1. Объём и выбор

116 canonical findings /120 original IDs распределены по одной primary class; severity каждого original сохранена. Связанные пакеты — варианты будущих slices, а не новые findings.

| Class | Число | Правило исполнения |
| --- | ---: | --- |
| TECH-HARDENING | 68 | Можно выбрать отдельный пакет после contract/caller/current evidence/ownership admission |
| GAME-DESIGN | 3 | Решение механики вне этапа; A03-13/A04-19/A04-21 |
| MIXED | 9 | Отдельный decision gate; техническую часть нельзя использовать для молчаливого выбора reward/death/late-loot/browser-history rules |
| EXPERIMENTAL-LEGACY | 17 | Только explicit support/stage decision; Legacy Rift/Hex не включаются автоматически |
| VERIFY-FIRST | 14 | Сначала выбранная изолированная проверка/version/config/contract; correction допускается лишь по результату |
| NO-ACTION | 5 | Accepted observations/policy decisions, не утверждение «исправлено» |
| **Всего** | **116** | Полный mapping и доказательность — матрица |

**37 пакетов** включают verification/decision варианты. Их нельзя оценивать как37 обязательных coding tasks. Узкие связанные изменения можно исполнить последовательно внутри одного owner boundary; Medium-карточка сначала разбивается на disjoint leaf tasks с явными acceptance criteria. Для reward-once после contract gate нужны отдельные оценки durability, safe-resource claim и finalizer effects; общий контракт не означает общего мегарефакторинга.

## 2. Общие gates для всех вариантов

- **G0 — Exposure facts.** До дальнейшей публикации получить владельческие данные о текущем ingress, flags, consumers, effective environment и deployed sources. В этом задании VPS/ключи/ingress не исследуются. Static repository chain config/admin/internal+generic proxy опасна; фактическая доступность неизвестна. Если owner подтверждает доступ, containment имеет срочность независимо от pre-alpha, через отдельно разрешённый change.
- **G1 — Permission contract.** Кто player/account/service/operator, какие read/write capabilities, какой источник admin authority. Current frontend service header не равен superuser; current backend get_current_user роль admin не выдаёт.
- **G2 — Reproducible tests/artifact.** Чистый dependency source и version manifest; isolated storage fixtures только для требуемых contracts. Проверки должны быть исполнимы на выбранном target environment.
- **G3 — Operation acceptance/replay.** Где authoritative факт, identity эффекта, marker/status, какая ошибка и как recovery. **Не включать Streams reclaim/reconciliation для effect handler до доказанной защиты повторного применения.** Это dependency gate, не обещание broker exactly-once.
- **G4 — Stage/mechanics decision.** Legacy support, Hex/dev scope, reward identity/effect set, death/late-loot/browser history semantics. Unanswered question сохраняет corresponding часть вне implementation.
- **G5 — Integration/release.** Один owner shared files, valid frontend+backend contracts, agreed migration/credential compatibility/rollback. NONE / DATA-MIGRATION / WIPE определяется по реальным изменениям; WIPE требует отдельного решения.

## 3. Вариант A — Security-first

Пригоден, если текущая публикация реальна или планируется скоро и privilege exposure — основной риск.

| Волна | Выбираемые пакеты | Dependency / результат |
| --- | --- | --- |
| A0 | G0/G1; WP-secret-validation, WP-surface-isolation | Установлены среды/callers; explicit failclosed validation/mounts. Potential containment не ждёт gameplay-пакетов, но current task изменений не разрешает |
| A1 | WP-auth-config, WP-auth-admin, WP-auth-internal; WP-session-lifecycle contract | Раздельные service/admin read/write scopes; before-storage/enqueue negative tests; сохранить current service consumers |
| A2 | WP-auth-game, WP-chat-access, WP-studio-readonly; WP-metrics-redaction, WP-log-redaction | Подтверждённые player ownership/private membership/selected-source gates; public diagnostic leakage закрыта в выбранном deployment policy |
| A3 | WP-dependency-source, WP-quality-provenance, WP-supply-chain, выбранные WP-runtime-isolation / WP-transport-policy checks | Воспроизводимый artifact и допустимая публикация; внешние protections/rotation отдельно |
| A4 | WP-storage-harness; выбранные commit/sync/archive/AI/stream packages после G3 | Надёжность admitted effect paths, без gameplay решения по умолчанию |

Плюсы: быстрее защищает опасные entrypoints. Цена: security tests/build acceptance всё равно зависят от доступного dependency source; нельзя объявить безопасность production по unit tests. Auth shared leaves потребуют последовательной интеграции; parallel drafting не означает simultaneous edits auth.py.

## 4. Вариант B — Infrastructure/reproducibility-first

Пригоден, если внешняя публикация фактически закрыта и сначала нужна исполнимая доказательная среда.

| Волна | Выбираемые пакеты | Dependency / результат |
| --- | --- | --- |
| B0 | G0; WP-dependency-source, WP-site-migrations verification/history decision | Clean checkout/artifact sources и schema baseline доступны; no assumption deployed history |
| B1 | WP-supply-chain, WP-quality-provenance, WP-test-controls, WP-storage-harness | Actual app audit, behavioral/ref/digest gates, meaningful isolated contracts |
| B2 | WP-secret-validation, WP-surface-isolation, WP-runtime-isolation verification, WP-log-redaction, WP-metrics-redaction | Runtime/config safety и observability canaries; no speculative least-privilege breakage |
| B3 | G1; WP-session-lifecycle, WP-auth-*, WP-chat-access, WP-studio-readonly | Security claims проверяются real consumer→adapter chain |
| B4 | WP-combat-commit, WP-inventory-sync, WP-ac-sync, WP-chat-archive, WP-ai-durability; G3 then WP-stream-recovery | Crash/retry safeguards в исполнимой среде; delayed optimizations only after correctness |

Плюсы: меньше недоказанных fixes и clean install failures. Цена: дольше до route authorization. **Непригоден для откладывания containment подтверждённо публичных privileged APIs:** в таком случае отдельный security slice выполняется до продолжения варианта.

## 5. Вариант C — Dependency-aware balanced

Пригоден для ограниченного состава исполнителей: короткий security stream и test/source foundation идут параллельно с disjoint leaf ownership.

| Волна | Stream1 security | Stream2 foundation/reliability | Общий gate |
| --- | --- | --- | --- |
| C0 | G0/G1; secret-validation + surface-isolation contracts | dependency-source + schema/deployed revision inventory | Owner выбирает scope/callers; нет shared-file concurrent edits |
| C1 | config/admin/internal scoped adapter slices; metrics/log redaction отдельными leaves | storage-harness + test-controls; site-migrations после history gate | Shared auth и CI/Docker/Nginx integrator; actual consumers positive tests |
| C2 | session-lifecycle → auth-game/chat-access; Studio independent leaf | combat-commit; inventory-sync/ac-sync version contracts; archive reader | Stable session identity / accepted runtime revision / UoW ownership |
| C3 | quality-provenance/supply-chain accepted artifact chain | chat-archive cursor/append → drain; ai-durability → resource budget; loot-transfer exact source | G3 for each handler; reward-once still gated by G4 |
| C4 | Optional actual exposure/recovery evidence accepted separately | stream-recovery only admitted replay-safe consumers; combat/archive IO optimizations; chat-fanout after overflow policy | Targeted+required checks, release compatibility, documented unknowns |

Плюсы: ранние privilege guards и reliability proof без ожидания всего этапа. Цена: больше coordination; не больше доступных agent slots. Helpers получают leaves и не делегируют дальше без отдельного поручения. Astra/ведущий принимает source/policy/contract и integration; стандартная реализация — Sol, простые независимые slices — Luna при доступности. Модель сама по себе не заменяет appropriate tests.

## 6. Независимость и междоменные зависимости

«Независим» означает отсутствие implementation prerequisite другого WP **после общего owner admission**; контракт окружения/consumer всё равно нужен.

| Независимые candidate leaves | Условия / общий файл |
| --- | --- |
| WP-secret-validation | settings single owner; env identity provision decision |
| WP-metrics-redaction | shared metrics single owner; scrape publication policy |
| WP-log-redaction | logging source owner; Nginx integration один owner |
| WP-studio-readonly | Studio source client/capability owner; auth access decision |
| WP-combat-readback | known existing archive store; authorized viewer fixture; если storage source меняется — WP-combat-archive dependency |
| WP-site-migrations | applied history/empty target gate; site SQL fixtures |
| WP-recovery-readiness, WP-transport-policy, WP-browser-render | verification-only first, no assumed fixes/production actions |
| WP-surface-isolation | mounts/environment decision; Nginx shared leaf координируется с logs/transport/runtime |

Основные dependency chains:

1. **Identity/permissions:** session-lifecycle contract → auth-game + chat-access. Config/admin/internal use agreed scoped service/operator authority; shared policy module один owner, feature adapters дальше disjoint. Studio selected-source gate может идти отдельно.
2. **Source/artifact:** dependency-source → actual clean runner/build → quality-provenance; supply-chain checks app manifest этого source. CI/deploy/Docker shared files edits serialized. Migration history → site-migrations → refresh real-PG proof.
3. **Runtime state:** accepted create/commit revision + real-store capabilities → combat-archive/IO; inventory-sync + agreed durability identity → conditional reward effect slice; AC dirty generation → fair scanner/dedup write optimization.
4. **Ownership:** boundary-state/dto contracts ↔ loot-transfer/inventory-sync/ac-sync consumers. Сначала выбрать owner API, затем owner implementation и caller leaves. Это contract dependency, не циклический порядок executable tasks; совместная SQL UoW сохраняется.
5. **Delivery:** agreed effect identity/dedup proof → stream-recovery for that handler. Chat cursor+Mongo append proof → drain-budget optimization. AI durable input/status/queue obligation → restart reconciliation → resource budget.
6. **Cross feature finalization:** combat accepted exchange → approved finalization/effect identity → effect idempotency → recovery/archive support scheduling. Gameplay/reward decision нельзя обойти transport fix.
7. **Chat transport:** UUID/selected-character/membership resolver → chat-access; separate slow-consumer policy → fanout buffer. Multi-process audience distribution requires VERIFY-FIRST, не «добавить replicas».
8. **Browser:** render sink verification независима от gameplay UI; history buffer remains MIXED until owner UX/history contract, не первоочередная technical coding work.

**Leaf ownership до запуска:** перечислить разрешённые files каждого исполнителя и запрещённые shared files; auth.py/game_auth.py, Combat/Inventory/AC session managers, shared DTOs, fixtures, CI/Docker/Nginx и library canonical source получают одного владельца. Другие исполнители предлагают contract/caller changes без одновременного редактирования общего leaf. Существующие пользовательские dirty changes не перезаписываются.

## 7. Вопросы владельцу и неизвестные условия

| Решение | Что оно разблокирует | До решения |
| --- | --- | --- |
| Выбранный вариант A/B/C и первая ограниченная wave? | Состав отдельно утверждённого задания, бюджет/приёмка | Ни один пакет не исполняется |
| Какие routers опубликованы сейчас, где public/internal/dev boundary, actual ingress/env/deployed ref? | G0, surface/auth/transport urgency | Production unknown; severity сохранена |
| Кто имеет config.write/reset, content.generate, simulation.launch/delete/train, analytics.raw/backfill; откуда server role/scope? | config/admin/internal | Не доверять UI role или generic service key |
| Нужны ли player analytics и account-only inventory view? | auth-game/internal read projection | Не расширять current read authority молча |
| Logout current/all sessions, deactivation/WS revocation latency, refresh lost-response policy? | session lifecycle и game/Chat consumers | Указаны негативные tests, outcome не выбран |
| Account UUID↔selected char связь, authoritative DM/group/zone membership, system publisher? | chat-access | UUID→int migration исключена |
| Что Studio может вычислять изолированно и где outputs вне source? Какая operator auth? | studio-readonly | Readonly source включая local; pure outside compute сохраняется |
| Поддерживается ли Legacy player Rift? Нужен ли Hex dev API и в каких средах? | Optional Legacy auth/runtime; Hex exposure | Нет обязательного развития Legacy/Hex |
| Once-only effect set/identity, late-loot cutoff, death publication/outcome contract? | MIXED reward-once child slices | Не менять суммы/eligibility/death; не включать replay |
| Same combat_id conflicting fingerprint, source holder transitions, accepted exchange fields? | combat-commit/loot-transfer | Сначала failure/conflict contract |
| Deployed migration revisions, supported store versions, source/lock/library release policy? | site-migrations/dependency-source/storage harness | No history rewrite/wipe/source substitution |
| Dirty flush fairness/latency; backlog retention/drain budget; WS overflow/multi-process delivery? | AC/archive/fanout technical performance | No production capacity claim/new UX by guess |
| Metrics/log access+retention/PII, service credentials/network/writable directories? | observability/runtime-isolation | Synthetic tests only; no actual credentials/log disclosure |
| Existing backups/monitor owner, allowed sanitized restore target/objectives? | recovery-readiness | Нет operations production и readiness claim |
| Browser visible/history/retrieval contract и trusted rich HTML sources? | browser-retention/browser-render | History MIXED, sink VERIFY-FIRST |

Не все вопросы требуют ответа для любого выбранного small package: владелец отвечает только на relevant gates. Technical scope не превращается в согласование полного будущего геймдизайна.

## 8. Какие project skills могут потребовать расширения

[Backlog04](04_skill_enforcement_backlog.md) содержит19 K/W/E предложений, связанных с RC-01–17. Потенциальные владельцы: backend (authority/UoW/state/replay/queue), quality (real boundaries/control fixtures/CI provenance), release (source/environment/publication/migration/restore proof), project (semantic ownership/DTO/compatibility), studio (selected-source capabilities/local compute distinction), frontend (actual typed client/bootstrap/site auth/safe rendering), combat (accepted exchange/finalization/archive parity), game-content (accepted generation input/result/provider resources). Rift — только stage/deferred-scope knowledge при выбранной optional работе. Skill changes не сделаны и не считаются реализацией gate.

Критерий завершения будущей wave: admitted packages проходят relevant positive+negative/fault/retry/consumer/required checks; source/artifact и release compatibility доказаны; legitimate gameplay outputs неизменны; unresolved conditions явно сохранены. Завершение **этого задания** — согласованный пятифайловый план, статическая проверка completeness/ссылок и STOP.
