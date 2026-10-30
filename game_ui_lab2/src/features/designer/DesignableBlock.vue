<script setup>
import { computed, ref } from 'vue';
import { globalLayoutStore } from './layoutStore.js';

const props = defineProps({
  id: { type: String, required: true },
  title: { type: String, default: '' },
  resizable: { type: Boolean, default: true },
  draggable: { type: Boolean, default: true },
  autoHeight: { type: Boolean, default: false },
});

const store = globalLayoutStore;
const isDragging = ref(false);
const isResizing = ref(false);

const block = computed(() => {
  return store.blocks[props.id] || null;
});

const isSelected = computed(() => {
  return store.isEditMode.value && store.selectedId.value === props.id;
});

const blockStyle = computed(() => {
  if (!block.value) return {};
  const s = {
    left: `${block.value.x}px`,
    top: `${block.value.y}px`,
    width: `${block.value.width}px`,
    zIndex: isSelected.value ? 200 : (block.value.zIndex || 10),
  };
  if (props.autoHeight) {
    s.minHeight = `${block.value.minHeight || 40}px`;
  } else {
    s.height = `${block.value.height}px`;
  }
  return s;
});

function onClick(e) {
  if (store.isEditMode.value) {
    store.selectBlock(props.id);
  }
}

// DRAG & DROP
function startDrag(e) {
  if (!store.isEditMode.value || !props.draggable) return;
  e.preventDefault();
  e.stopPropagation();
  store.selectBlock(props.id);
  isDragging.value = true;

  const startX = e.clientX;
  const startY = e.clientY;
  const initialX = block.value.x;
  const initialY = block.value.y;

  function onMouseMove(moveEvent) {
    const dx = moveEvent.clientX - startX;
    const dy = moveEvent.clientY - startY;
    store.updateBlock(props.id, {
      x: initialX + dx,
      y: initialY + dy,
    });
  }

  function onMouseUp() {
    isDragging.value = false;
    window.removeEventListener('mousemove', onMouseMove);
    window.removeEventListener('mouseup', onMouseUp);
  }

  window.addEventListener('mousemove', onMouseMove);
  window.addEventListener('mouseup', onMouseUp);
}

// 8-DIRECTIONAL RESIZING
function startResize(e, dir) {
  if (!store.isEditMode.value || !props.resizable) return;
  e.preventDefault();
  e.stopPropagation();
  store.selectBlock(props.id);
  isResizing.value = true;

  const startX = e.clientX;
  const startY = e.clientY;
  const initX = block.value.x;
  const initY = block.value.y;
  const initW = block.value.width;
  const initH = block.value.height;
  const minW = block.value.minWidth || 60;
  const minH = block.value.minHeight || 40;

  function onMouseMove(ev) {
    const dx = ev.clientX - startX;
    const dy = ev.clientY - startY;
    const patch = {};

    // Horizontal
    if (dir.includes('e')) {
      patch.width = Math.max(minW, initW + dx);
    } else if (dir.includes('w')) {
      const newW = Math.max(minW, initW - dx);
      patch.width = newW;
      patch.x = initX + (initW - newW);
    }

    // Vertical
    if (dir.includes('s')) {
      patch.height = Math.max(minH, initH + dy);
    } else if (dir.includes('n')) {
      const newH = Math.max(minH, initH - dy);
      patch.height = newH;
      patch.y = initY + (initH - newH);
    }

    store.updateBlock(props.id, patch);
  }

  function onMouseUp() {
    isResizing.value = false;
    window.removeEventListener('mousemove', onMouseMove);
    window.removeEventListener('mouseup', onMouseUp);
  }

  window.addEventListener('mousemove', onMouseMove);
  window.addEventListener('mouseup', onMouseUp);
}
</script>

<template>
  <div
    class="designable-block"
    :class="{
      'is-edit-mode': store.isEditMode.value,
      'is-selected': isSelected,
      'is-dragging': isDragging,
      'is-resizing': isResizing,
    }"
    :style="blockStyle"
    @click="onClick"
  >
    <!-- Drag Handle Badge -->
    <div
      v-if="store.isEditMode.value && draggable"
      class="designable-header-badge"
      title="Зажмите и потяните для перемещения"
      @mousedown="startDrag"
    >
      <span class="drag-icon">✥</span>
      <span>{{ title || block?.name || id }}</span>
      <span class="block-coords" v-if="block">
        {{ block.x }},{{ block.y }} · {{ block.width }}×{{ block.height }}
      </span>
    </div>

    <!-- Inner Component Slot -->
    <slot />

    <!-- 8 Interactive Resize Handles (visible in Edit Mode) -->
    <template v-if="store.isEditMode.value && resizable">
      <!-- 4 Corners with visible grip squares -->
      <div class="resize-handle corner-handle handle-se" title="Тяните для изменения размера (SE)" @mousedown="startResize($event, 'se')">
        <span class="handle-grip"></span>
      </div>
      <div class="resize-handle corner-handle handle-sw" title="Тяните для изменения размера (SW)" @mousedown="startResize($event, 'sw')">
        <span class="handle-grip"></span>
      </div>
      <div class="resize-handle corner-handle handle-ne" title="Тяните для изменения размера (NE)" @mousedown="startResize($event, 'ne')">
        <span class="handle-grip"></span>
      </div>
      <div class="resize-handle corner-handle handle-nw" title="Тяните для изменения размера (NW)" @mousedown="startResize($event, 'nw')">
        <span class="handle-grip"></span>
      </div>

      <!-- 4 Edges -->
      <div class="resize-handle edge-handle handle-e" title="Изменить ширину" @mousedown="startResize($event, 'e')"></div>
      <div class="resize-handle edge-handle handle-w" title="Изменить ширину" @mousedown="startResize($event, 'w')"></div>
      <div class="resize-handle edge-handle handle-s" title="Изменить высоту" @mousedown="startResize($event, 's')"></div>
      <div class="resize-handle edge-handle handle-n" title="Изменить высоту" @mousedown="startResize($event, 'n')"></div>
    </template>
  </div>
</template>
