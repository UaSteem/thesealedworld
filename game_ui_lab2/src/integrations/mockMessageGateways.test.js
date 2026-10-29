import test from 'node:test';
import assert from 'node:assert/strict';
import { createMockChatGateway } from './mockChatGateway.js';
import { createMockCombatLogGateway } from './mockCombatLogGateway.js';

test('chat stores local messages only in their channel and unsubscribes cleanly', () => {
  const chat = createMockChatGateway();
  const events = [];
  const stop = chat.subscribe((event) => events.push(event));
  const beforeWorld = chat.getMessages('world').length;
  const beforeLocal = chat.getMessages('local').length;
  chat.send('world', '  Привет  ');
  assert.equal(chat.getMessages('world').length, beforeWorld + 1);
  assert.equal(chat.getMessages('local').length, beforeLocal);
  assert.equal(events[0].message.text, 'Привет');
  stop();
  chat.send('world', 'Ещё');
  assert.equal(events.length, 1);
});

test('combat events stream independently, stop on unsubscribe and restart fresh', () => {
  let tick;
  let cancelled = 0;
  const combat = createMockCombatLogGateway({
    setTimer(callback) { tick = callback; return 1; },
    clearTimer() { cancelled += 1; },
  });
  const chat = createMockChatGateway();
  const initialChatCount = chat.getMessages('world').length;
  const firstVisit = [];
  const stop = combat.subscribe((event) => firstVisit.push(event));
  assert.equal(firstVisit.length, 1);
  tick();
  assert.equal(firstVisit.length, 2);
  stop();
  tick();
  assert.equal(firstVisit.length, 2);
  assert.equal(cancelled, 1);
  const secondVisit = [];
  combat.subscribe((event) => secondVisit.push(event))();
  assert.deepEqual(secondVisit[0], firstVisit[0]);
  assert.equal(chat.getMessages('world').length, initialChatCount);
});
