# Tactical states and factual report

- `runtime/engine/tactical_state.py` coordinates actor-global state after all exchange waves. Current state applies throughout the exchange; next state starts at the next own exchange. Offhand/counter do not add transition checks. Both owners use frozen decision inputs before applying results.
- Archer retains `ranged_position` far/mid/close and specialized defense. Other three styles use `tactical_state` normal/advantage; do not route them through archer dodge events.
- Starting coefficients live in `game_catalog/combat/resources/common/tactical_states.py`; they are tunable defaults, not accepted balance. Style mastery scales parry/anti-dodge/crit; weapon mastery never multiplies added tactical crit.
- Feints use whitelisted tactical mutations. Guaranteed dislodge wins over protected hold/forced entry. Preserve activation conditions and forced-close provenance; generated strikes must not activate the selected feint again.
- Position RNG is isolated and stable per battle/exchange/actor. This does not migrate all existing MathCore module-global randomness.
- `TacticalTransitionFactDTO` carries actor/style/before/after/reason/action/feint. Public counterpart is in `src/shared/schemas/combat.py`; status params expose current state. Only actual transitions create report rows.
- `runtime/support/factual_report.py` + `log_builder.py` report facts without narrative variants. Keep damage/heal/absorbed/reflect, effects, resources and causality. Defensive triggers belong to the defender. Text library remains reserved: see [retention and log rules](trigger-log-rendering.md).
- Battle tab is read-only UI in persistent chat area: `src/frontend/static/js/game/combat/battle_feed.js`, `/game/combat/report`, typed BackendCombatApi.logs. Never use chat.message/system/storage as combat report transport; never remount persistent chat on navigation.
- Backend GET logs checks auth, game-character scope and actual ownership. Pages replace snapshots; session/generation guards reject stale responses. Hex highlights/floating window are deferred.

Verify `test_tactical_states`, `test_effect_timing_contract`, `test_exchange_execution_contract`, `test_factual_combat_log`, log ownership tests and frontend `battle_feed.test.cjs`. Cover forced defender, AoE, second hand/counter, feint conflicts, negative initiative, archer regression and reconnect. Narrow tests do not prove accepted balance or full-suite success.
