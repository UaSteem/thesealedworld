# CSS font-size token migration — packet index

Each packet below is a **self-contained prompt** for a low-context model. Open one, paste it + let the model edit that single file. Order: small files first to build confidence, or by domain.

Total files with hardcoded font-size px: **57**

| packet | target file | total px | exact-swap values |
|---|---|---|---|
| `components__modal.md` | `components/modal.css` | 1 | 0 |
| `components__panels.md` | `components/panels.css` | 1 | 0 |
| `components__status_widgets.md` | `components/status_widgets.css` | 1 | 0 |
| `domains__chat__responsive_states.md` | `domains/chat/responsive_states.css` | 1 | 1 |
| `domains__field__inventory.md` | `domains/field/inventory.css` | 1 | 1 |
| `domains__loot__responsive.md` | `domains/loot/responsive.css` | 1 | 0 |
| `domains__rift__screen.md` | `domains/rift/screen.css` | 1 | 0 |
| `domains__scenario__panels.md` | `domains/scenario/panels.css` | 1 | 1 |
| `shell__layout__center_nav.md` | `shell/layout/center_nav.css` | 1 | 1 |
| `shell__responsive__mobile_header.md` | `shell/responsive/mobile_header.css` | 1 | 0 |
| `shell__responsive__narrow_phone.md` | `shell/responsive/narrow_phone.css` | 1 | 0 |
| `components__cards.md` | `components/cards.css` | 2 | 1 |
| `domains__combat__screen.md` | `domains/combat/screen.css` | 2 | 2 |
| `domains__exploration__responsive.md` | `domains/exploration/responsive.css` | 2 | 1 |
| `domains__field__exploration_services.md` | `domains/field/exploration_services.css` | 2 | 1 |
| `domains__loot__loot.md` | `domains/loot/loot.css` | 2 | 1 |
| `domains__scenario__scene.md` | `domains/scenario/scene.css` | 2 | 2 |
| `domains__status__metrics.md` | `domains/status/metrics.css` | 2 | 1 |
| `domains__status__shell.md` | `domains/status/shell.css` | 2 | 1 |
| `domains__arena__repair.md` | `domains/arena/repair.css` | 3 | 1 |
| `domains__chat__input.md` | `domains/chat/input.css` | 3 | 3 |
| `domains__selection__screen.md` | `domains/selection/screen.css` | 3 | 1 |
| `shell__layout__footer.md` | `shell/layout/footer.css` | 3 | 2 |
| `components__action_panel.md` | `components/action_panel.css` | 4 | 2 |
| `domains__arena__group_browser.md` | `domains/arena/group_browser.css` | 4 | 2 |
| `domains__arena__groups.md` | `domains/arena/groups.css` | 4 | 1 |
| `domains__arena__live_battles.md` | `domains/arena/live_battles.css` | 4 | 2 |
| `domains__chat__tabs.md` | `domains/chat/tabs.css` | 4 | 3 |
| `domains__status__tags.md` | `domains/status/tags.css` | 4 | 2 |
| `domains__arena__responsive.md` | `domains/arena/responsive.css` | 5 | 1 |
| `domains__exploration__right_sidebar.md` | `domains/exploration/right_sidebar.css` | 5 | 2 |
| `domains__status__avatar.md` | `domains/status/avatar.css` | 5 | 2 |
| `domains__arena__lobby.md` | `domains/arena/lobby.css` | 6 | 3 |
| `domains__exploration__movement.md` | `domains/exploration/movement.css` | 6 | 1 |
| `domains__status__attributes.md` | `domains/status/attributes.css` | 6 | 2 |
| `domains__arena__modals.md` | `domains/arena/modals.css` | 7 | 2 |
| `domains__chat__messages.md` | `domains/chat/messages.css` | 7 | 3 |
| `domains__combat__teams.md` | `domains/combat/teams.css` | 7 | 3 |
| `domains__exploration__services.md` | `domains/exploration/services.css` | 7 | 2 |
| `domains__rift__responsive.md` | `domains/rift/responsive.css` | 7 | 2 |
| `components__inventory.md` | `components/inventory.css` | 8 | 1 |
| `components__tooltips.md` | `components/tooltips.css` | 8 | 3 |
| `domains__arena__matchmaking.md` | `domains/arena/matchmaking.css` | 8 | 2 |
| `domains__arena__modes.md` | `domains/arena/modes.css` | 8 | 3 |
| `domains__arena__right_sidebar.md` | `domains/arena/right_sidebar.css` | 8 | 2 |
| `domains__combat__prototype.md` | `domains/combat/prototype.css` | 9 | 2 |
| `domains__exploration__scene.md` | `domains/exploration/scene.css` | 9 | 2 |
| `domains__city_services__index.md` | `domains/city_services/index.css` | 10 | 3 |
| `domains__field__exploration_encounters.md` | `domains/field/exploration_encounters.css` | 11 | 3 |
| `domains__scenario__result.md` | `domains/scenario/result.css` | 11 | 4 |
| `shell__layout__header.md` | `shell/layout/header.css` | 11 | 2 |
| `domains__status__skills.md` | `domains/status/skills.css` | 12 | 3 |
| `domains__combat__responsive.md` | `domains/combat/responsive.css` | 13 | 3 |
| `domains__combat__sidebars.md` | `domains/combat/sidebars.css` | 13 | 3 |
| `domains__combat__result.md` | `domains/combat/result.css` | 21 | 5 |
| `domains__combat__actions.md` | `domains/combat/actions.css` | 29 | 4 |
| `domains__exploration__encounters.md` | `domains/exploration/encounters.css` | 30 | 6 |

## Suggested batching
- Tiny files (≤3 px) can be combined into one chat.
- Big files (`combat/actions.css`, `combat/result.css`, `exploration/encounters.css`) get their own chat.
