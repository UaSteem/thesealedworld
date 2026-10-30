import { reactive, ref, computed } from 'vue';

const STORAGE_KEY = 'sealed_world_ui_layout_v1';

export function getStageDimensions() {
  if (typeof window === 'undefined') return { width: 1920, height: 1080 };
  const stage = document.querySelector('.stage-shell') || document.querySelector('.game-viewport');
  const w = stage?.clientWidth || window.innerWidth || 1920;
  const h = stage?.clientHeight || window.innerHeight || 1080;
  return { width: Math.max(640, w), height: Math.max(480, h) };
}

export function createDefaultLayout() {
  const { width: sw, height: sh } = getStageDimensions();
  return {
    hud: {
      id: 'hud',
      name: 'HUD игрока',
      x: 14,
      y: 14,
      width: 320,
      height: 104,
      minWidth: 240,
      minHeight: 82,
      zIndex: 10,
      visible: true,
    },
    menu: {
      id: 'menu',
      name: 'Игровое меню',
      x: Math.max(14, sw - 290 - 14),
      y: 14,
      width: 290,
      height: 44,
      minWidth: 180,
      minHeight: 38,
      zIndex: 10,
      visible: true,
      anchor: 'right',
      rightMargin: 14,
    },
    chat: {
      id: 'chat',
      name: 'Чат / Лог боя',
      x: 14,
      y: Math.max(14, sh - 300 - 14),
      width: 580,
      height: 300,
      minWidth: 280,
      minHeight: 140,
      zIndex: 10,
      visible: true,
      anchor: 'bottom-left',
      bottomMargin: 14,
    },
    riftDebug: {
      id: 'riftDebug',
      name: 'Отладка зума',
      x: Math.max(14, sw - 270 - 14),
      y: 68,
      width: 270,
      height: 180,
      minWidth: 180,
      minHeight: 40,
      zIndex: 10,
      visible: true,
      anchor: 'right',
      rightMargin: 14,
    },
    inspector: {
      id: 'inspector',
      name: 'Инспектор цели',
      x: 14,
      y: 130,
      width: 196,
      height: 260,
      minWidth: 160,
      minHeight: 150,
      zIndex: 10,
      visible: true,
    },
  };
}

export function createLayoutStore(storage = typeof localStorage !== 'undefined' ? localStorage : null) {
  const isEditMode = ref(false);
  const snapToGrid = ref(true);
  const gridSize = ref(8);
  const showGuides = ref(true);
  const selectedId = ref(null);

  const blocks = reactive(loadPersisted() || createDefaultLayout());

  function loadPersisted() {
    if (!storage) return null;
    try {
      const data = storage.getItem(STORAGE_KEY);
      if (!data) return null;
      const parsed = JSON.parse(data);
      const defaults = createDefaultLayout();
      const { width: sw, height: sh } = getStageDimensions();

      for (const [key, val] of Object.entries(parsed)) {
        if (defaults[key]) {
          const defaultAnchor = defaults[key].anchor;
          Object.assign(defaults[key], val);
          if (!val.anchor) {
            defaults[key].anchor = defaultAnchor;
          }
          if (defaults[key].id === 'menu' || defaults[key].id === 'riftDebug' || defaults[key].anchor === 'right') {
            if (defaults[key].anchor !== 'custom') {
              defaults[key].x = Math.max(14, sw - defaults[key].width - (defaults[key].rightMargin ?? 14));
            }
          } else if (defaults[key].x + defaults[key].width > sw) {
            defaults[key].x = Math.max(14, sw - defaults[key].width - 14);
          }
          if (defaults[key].id === 'chat' || defaults[key].anchor === 'bottom-left' || defaults[key].anchor === 'bottom') {
            if (defaults[key].anchor !== 'custom') {
              defaults[key].y = Math.max(14, sh - defaults[key].height - (defaults[key].bottomMargin ?? 14));
            }
          } else if (defaults[key].y + defaults[key].height > sh) {
            defaults[key].y = Math.max(14, sh - defaults[key].height - 14);
          }
        } else {
          defaults[key] = val;
        }
      }
      return defaults;
    } catch {
      return null;
    }
  }

  function persist() {
    if (!storage) return;
    try {
      storage.setItem(STORAGE_KEY, JSON.stringify(blocks));
    } catch (e) {
      console.warn('Failed to persist layout:', e);
    }
  }

  function snap(val) {
    if (!snapToGrid.value || gridSize.value <= 1) return Math.round(val);
    return Math.round(val / gridSize.value) * gridSize.value;
  }

  function toggleEditMode() {
    isEditMode.value = !isEditMode.value;
    if (!isEditMode.value) selectedId.value = null;
  }

  function selectBlock(id) {
    selectedId.value = id;
  }

  function updateBlock(id, patch) {
    if (!blocks[id]) {
      blocks[id] = { id, name: id, x: 0, y: 0, width: 200, height: 100, minWidth: 100, minHeight: 40, zIndex: 10, visible: true };
    }
    const b = blocks[id];
    const { width: sw, height: sh } = getStageDimensions();

    if (patch.x !== undefined) {
      const rawX = snap(patch.x);
      b.x = Math.max(0, Math.min(rawX, sw - 40));
      if (patch.anchor !== undefined) {
        b.anchor = patch.anchor;
      } else if (rawX >= sw - (b.width || 200) - 50) {
        b.anchor = 'right';
        b.rightMargin = Math.max(0, sw - (b.x + b.width));
      } else {
        b.anchor = 'custom';
      }
    }
    if (patch.y !== undefined) {
      const rawY = snap(patch.y);
      b.y = Math.max(0, Math.min(rawY, sh - 30));
      if (patch.anchor !== undefined) {
        b.anchor = patch.anchor;
      } else if (rawY >= sh - (b.height || 100) - 50) {
        b.anchor = 'bottom-left';
        b.bottomMargin = Math.max(0, sh - (b.y + b.height));
      } else if (b.anchor === 'bottom-left' || b.anchor === 'bottom') {
        b.anchor = 'custom';
      }
    }
    if (patch.width !== undefined) {
      const rawW = snap(patch.width);
      b.width = Math.max(b.minWidth || 50, Math.min(rawW, sw));
    }
    if (patch.height !== undefined) {
      const rawH = snap(patch.height);
      b.height = Math.max(b.minHeight || 30, Math.min(rawH, sh));
    }
    if (patch.visible !== undefined) b.visible = patch.visible;
    if (patch.zIndex !== undefined) b.zIndex = patch.zIndex;
    persist();
  }

  function resetLayout() {
    const defaults = createDefaultLayout();
    for (const key of Object.keys(blocks)) {
      if (!defaults[key]) delete blocks[key];
    }
    for (const [key, val] of Object.entries(defaults)) {
      blocks[key] = val;
    }
    if (storage) {
      try { storage.removeItem(STORAGE_KEY); } catch {}
    }
    selectedId.value = null;
  }

  function exportLayoutJson() {
    return JSON.stringify(blocks, null, 2);
  }

  function importLayoutJson(jsonStr) {
    try {
      const parsed = JSON.parse(jsonStr);
      if (typeof parsed !== 'object' || parsed === null) throw new Error('Invalid format');
      const defaults = createDefaultLayout();
      for (const [k, v] of Object.entries(parsed)) {
        if (v && typeof v === 'object' && typeof v.x === 'number' && typeof v.y === 'number') {
          blocks[k] = Object.assign(defaults[k] || {}, v);
        }
      }
      persist();
      return { ok: true };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  }

  function adaptToViewport(viewportWidth, viewportHeight) {
    if (!viewportWidth || !viewportHeight) return;
    for (const b of Object.values(blocks)) {
      if (b.id === 'menu' || b.id === 'riftDebug' || b.anchor === 'right') {
        if (b.anchor !== 'custom') {
          const margin = b.rightMargin ?? 14;
          b.x = Math.max(14, viewportWidth - b.width - margin);
        }
      } else if (b.x + b.width > viewportWidth) {
        b.x = Math.max(0, viewportWidth - b.width - 14);
      }

      if (b.id === 'chat' || b.anchor === 'bottom-left' || b.anchor === 'bottom') {
        if (b.anchor !== 'custom') {
          const margin = b.bottomMargin ?? 14;
          b.y = Math.max(14, viewportHeight - b.height - margin);
          b.x = 14;
        }
      } else if (b.y + b.height > viewportHeight) {
        b.y = Math.max(0, viewportHeight - b.height - 14);
      }
    }
  }

  const selectedBlock = computed(() => {
    return selectedId.value ? blocks[selectedId.value] : null;
  });

  return {
    isEditMode,
    snapToGrid,
    gridSize,
    showGuides,
    selectedId,
    selectedBlock,
    blocks,
    toggleEditMode,
    selectBlock,
    updateBlock,
    resetLayout,
    exportLayoutJson,
    importLayoutJson,
    adaptToViewport,
    snap,
  };
}

export const globalLayoutStore = createLayoutStore();
