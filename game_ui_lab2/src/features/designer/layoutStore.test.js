import assert from 'node:assert/strict';
import test from 'node:test';
import { createLayoutStore, createDefaultLayout } from './layoutStore.js';

test('layoutStore initializes with defaults and toggles edit mode', () => {
  const store = createLayoutStore();
  assert.equal(store.isEditMode.value, false);
  store.toggleEditMode();
  assert.equal(store.isEditMode.value, true);
  store.toggleEditMode();
  assert.equal(store.isEditMode.value, false);
  assert.ok(store.blocks.hud.width >= 200);
});

test('layoutStore updates position, respects snap-to-grid and min dimensions', () => {
  const store = createLayoutStore();
  store.snapToGrid.value = true;
  store.gridSize.value = 10;

  store.updateBlock('hud', { x: 23, y: 47, width: 304, height: 122 });
  assert.equal(store.blocks.hud.x, 20); // snapped to 20
  assert.equal(store.blocks.hud.y, 50); // snapped to 50
  assert.equal(store.blocks.hud.width, 300); // snapped to 300
  assert.equal(store.blocks.hud.height, 120); // snapped to 120

  // Respects min dimensions
  store.updateBlock('hud', { width: 50, height: 20 });
  assert.equal(store.blocks.hud.width, store.blocks.hud.minWidth);
  assert.equal(store.blocks.hud.height, store.blocks.hud.minHeight);
});

test('layoutStore persists to storage and restores on reset', () => {
  const mockStorage = {
    data: {},
    getItem(k) { return this.data[k] || null; },
    setItem(k, v) { this.data[k] = v; },
    removeItem(k) { delete this.data[k]; },
  };

  const store = createLayoutStore(mockStorage);
  store.updateBlock('chat', { x: 104, y: 200 });
  assert.ok(mockStorage.data.sealed_world_ui_layout_v1);

  // New instance from same storage
  const restored = createLayoutStore(mockStorage);
  assert.equal(restored.blocks.chat.x, 104);
  assert.equal(restored.blocks.chat.y, 200);

  // Reset restores defaults
  restored.resetLayout();
  const defaults = createDefaultLayout();
  assert.equal(restored.blocks.chat.x, defaults.chat.x);
  assert.equal(restored.blocks.chat.y, defaults.chat.y);
  assert.equal(mockStorage.getItem('sealed_world_ui_layout_v1'), null);
});

test('layoutStore exports and imports valid JSON layouts', () => {
  const store = createLayoutStore();
  store.updateBlock('hud', { x: 152, y: 152 });
  const exported = store.exportLayoutJson();
  assert.ok(exported.includes('"hud"'));

  const second = createLayoutStore();
  const res = second.importLayoutJson(exported);
  assert.equal(res.ok, true);
  assert.equal(second.blocks.hud.x, 152);

  const badRes = second.importLayoutJson('not-json');
  assert.equal(badRes.ok, false);
});
