const { test } = require('node:test');
const assert = require('node:assert/strict');
require('../../../../src/frontend/static/js/game/combat/battle_feed.js');
const feed = () => {
    const model = GameBattleFeed.create();
    model.chatTab = 'global';
    model.$refs = { battleScroll: { scrollTop: 23, scrollHeight: 500, clientHeight: 200 } };
    model.$nextTick = fn => fn();
    Object.assign(model.battle, { id: 'A', charId: '5', visible: true, active: true });
    return model;
};
const response = (id = 'A', entries = [{ id: '1', text: 'fact', format: 'factual-v1' }], page = 1) => ({ ok: true, json: async () => ({ session_id: id, turns: [{ title: 'Размен 1', entries }], page, page_size: 8, total_turns: 20 }) });
test('authoritative repeated snapshots replace a bounded page; preserve scroll and unread', async () => {
    const model = feed();
    global.fetch = async () => response();
    await model._battleRefresh();
    await model._battleRefresh();
    assert.equal(model.battle.turns[0].entries.length, 1);
    assert.equal(model.$refs.battleScroll.scrollTop, 23);
    assert.equal(model.battle.pages, 3);
    assert.equal(model.battle.unread, true);
    assert.equal(model.chatTab, 'global');
});
test('late old battle and out-of-order page responses cannot replace current report', async () => {
    const model = feed();
    let resolve;
    global.fetch = () => new Promise(done => { resolve = done; });
    const old = model._battleRefresh();
    model.battle.id = 'B';
    global.fetch = async () => response('B', [{ id: 'new' }], 2);
    await model._battleRefresh(2);
    resolve(response('A'));
    await old;
    assert.equal(model.battle.page, 2);
    assert.equal(model.battle.turns[0].entries[0].id, 'new');
    assert.equal(model.battle.loading, false);
});
test('server session mismatch is rejected even when request generation is current', async () => {
    const model = feed();
    global.fetch = async () => response('wrong');
    await model._battleRefresh();
    assert.deepEqual(model.battle.turns, []);
});
test('lifecycle retains final report, resets on new battle and clears on character change', () => {
    const model = feed();
    model._battleRefresh = () => {};
    model.battle.turns = [{ entries: [{ id: 'retained' }] }];
    model._battleSync({ dataset: { characterId: '5', battleId: '', battleActive: 'false' } });
    assert.equal(model.battle.visible, true);
    assert.equal(model.battle.active, false);
    assert.equal(model.battle.turns.length, 1);
    model._battleSync({ dataset: { characterId: '5', battleId: 'B', battleActive: 'true' } });
    assert.equal(model.battle.id, 'B');
    assert.equal(model.battle.turns.length, 0);
    model.chatTab = 'battle';
    model._battleSync({ dataset: { characterId: '6', battleId: '', battleActive: 'false' } });
    assert.equal(model.battle.visible, false);
    assert.equal(model.chatTab, 'global');
});
test('legacy narrative is excluded; facts preserve actor direction and numbers', () => {
    const text = GameBattleFeed.describe({ text: 'клыки впились', source: { id: '1', name: '<b>Союзник</b>' }, target: { id: '2', name: 'Враг' }, outcome: 'blocked', numbers: { damage: 5, absorbed: 3 } });
    assert.match(text, /<b>Союзник<\/b> → Враг:/);
    assert.match(text, /поглощено 3/);
    assert.doesNotMatch(text, /клыки/);
});
test('factual format still displays structured absorbed damage and tactical provenance', () => {
    const text = GameBattleFeed.describe({ format: 'factual-v1', text: 'short summary', source: { id: '1', name: 'Союзник' }, target: { id: '2', name: 'Враг' }, action: { id: 'feint-1', label: 'Финт' }, numbers: { damage: 5, absorbed: 3 }, tactical_transitions: [{ actor_id: '1', style: 'shield', before: 'normal', after: 'advantage', reason: 'initiative', source_feint_id: 'feint-1' }] });
    assert.match(text, /поглощено 3/);
    assert.match(text, /Союзник: щит обычное → выгодное \(инициатива\) \/ финт: Финт/);
    assert.doesNotMatch(text, /short summary/);
});
test('transition labels and effect duration render without implementation keys', () => {
    const text = GameBattleFeed.describe({ source: { id: '1', name: 'Ратник' }, target: { id: '2', name: 'Волк' }, action: { label: 'Атака' }, effects: [{ actor_id: '2', tooltip: 'Кровотечение', action: 'apply', duration: 3 }], tactical_transitions: [{ actor_id: '1', style: 'skill_two_handed', before: 'normal', after: 'advantage', reason: 'feint_assisted_entry', source_feint_id: 'catalog.key', source_feint_label: 'Силовой нажим' }] });
    assert.match(text, /^Ратник → Волк: Атака/);
    assert.match(text, /Кровотечение наложен \(3 разменов\)/);
    assert.match(text, /двуручное оружие обычное → выгодное \(инициатива с помощью финта\).*Силовой нажим/);
    assert.doesNotMatch(text, /skill_two_handed|feint_assisted_entry|catalog.key/);
});
test('AoE preserves each recipient outcome and numbers without repeating aggregate damage', () => {
    const text = GameBattleFeed.describe({ source: { id: '1', name: 'Маг' }, action: { label: 'Волна' }, numbers: { damage: 99 }, target_results: [{ target: { id: '2', name: 'Волк' }, outcome: 'hit', numbers: { damage: 7 }, flags: { crit: true } }, { target: { id: '3', name: 'Лиса' }, outcome: 'miss', numbers: { damage: 0 } }] });
    assert.match(text, /Маг → Волк: Волна · попадание · урон 7 · критический удар/);
    assert.match(text, /Маг → Лиса: Волна · промах/);
    assert.doesNotMatch(text, /99/);
});
