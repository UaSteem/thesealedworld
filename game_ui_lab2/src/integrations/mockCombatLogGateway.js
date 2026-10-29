const presetEvents = [
  ['Раунд 1', 'Бой начался: Ada Guard против Хранителя.'],
  ['Раунд 1', 'Ada Guard атакует. Хранитель теряет 18 HP.'],
  ['Раунд 1', 'Хранитель отвечает. Ada Guard блокирует часть удара: −6 HP.'],
  ['Раунд 2', 'Хранитель готовит тяжёлый удар.'],
  ['Раунд 2', 'Ada Guard использует защитную стойку.'],
  ['Раунд 2', 'Тяжёлый удар заблокирован. Ada Guard теряет 4 HP.'],
  ['Раунд 3', 'Ada Guard наносит критический удар: −27 HP.'],
  ['Раунд 3', 'Ожидание следующего действия…'],
];

// One subscription represents one visit to the combat screen. Unsubscribe stops
// delivery; a later subscription replays a fresh fixture. No chat API is used.
export function createMockCombatLogGateway({ intervalMs = 1800, setTimer = setInterval, clearTimer = clearInterval } = {}) {
  function subscribe(listener) {
    let cursor = 0;
    let timer = null;
    let active = true;
    const append = () => {
      if (!active || cursor >= presetEvents.length) return;
      const [round, text] = presetEvents[cursor];
      listener({ id: `combat-${cursor++}`, round, text });
      if (cursor >= presetEvents.length && timer !== null) {
        clearTimer(timer);
        timer = null;
      }
    };
    append();
    if (cursor < presetEvents.length && active) timer = setTimer(append, intervalMs);
    return () => {
      active = false;
      if (timer !== null) clearTimer(timer);
      timer = null;
    };
  }

  return { subscribe };
}
