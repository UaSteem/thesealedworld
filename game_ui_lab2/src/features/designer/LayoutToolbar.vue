<script setup>
import { ref } from 'vue';
import { globalLayoutStore } from './layoutStore.js';

const store = globalLayoutStore;
const showExportModal = ref(false);
const showImportModal = ref(false);
const exportText = ref('');
const importText = ref('');
const importError = ref('');
const copiedNotice = ref(false);

function openExport() {
  exportText.value = store.exportLayoutJson();
  showExportModal.value = true;
  copiedNotice.value = false;
}

function copyExport() {
  navigator.clipboard?.writeText(exportText.value);
  copiedNotice.value = true;
  setTimeout(() => { copiedNotice.value = false; }, 2000);
}

function openImport() {
  importText.value = '';
  importError.value = '';
  showImportModal.value = true;
}

function applyImport() {
  const res = store.importLayoutJson(importText.value);
  if (res.ok) {
    showImportModal.value = false;
  } else {
    importError.value = res.error || 'Ошибка импорта';
  }
}

function toggleGridSize() {
  if (!store.snapToGrid.value) {
    store.snapToGrid.value = true;
    store.gridSize.value = 8;
  } else if (store.gridSize.value === 8) {
    store.gridSize.value = 16;
  } else {
    store.snapToGrid.value = false;
  }
}

function onReset(e) {
  e.preventDefault();
  e.stopPropagation();
  store.resetLayout();
}
</script>

<template>
  <div @pointerdown.stop @mousedown.stop @click.stop>
    <!-- Background Grid Overlay when editing and enabled -->
    <div
      v-if="store.isEditMode.value && store.snapToGrid.value"
      class="designer-grid-overlay"
      :style="{ backgroundSize: `${store.gridSize.value * 2}px ${store.gridSize.value * 2}px` }"
    />

    <!-- Floating Designer Toolbar (Centered at the bottom, isolated from canvas clicks) -->
    <aside
      class="designer-toolbar"
      aria-label="Панель конструктора интерфейса"
      @pointerdown.stop
      @mousedown.stop
      @mouseup.stop
      @click.stop
    >
      <button
        type="button"
        :class="{ 'is-active': store.isEditMode.value }"
        title="Включить / выключить интерактивное редактирование UI (Alt+E)"
        @click.stop="store.toggleEditMode"
      >
        <span>🛠</span>
        <span>Конструктор UI: <b>{{ store.isEditMode.value ? 'ВКЛ' : 'ВЫКЛ' }}</b></span>
      </button>

      <template v-if="store.isEditMode.value">
        <div class="toolbar-divider" />

        <button
          type="button"
          :title="`Привязка к сетке: ${store.snapToGrid.value ? store.gridSize.value + 'px' : 'Выкл'}`"
          @click.stop="toggleGridSize"
        >
          <span>⊞</span>
          <span>{{ store.snapToGrid.value ? `Сетка: ${store.gridSize.value}px` : 'Без сетки' }}</span>
        </button>

        <!-- Selected Element Inspector -->
        <template v-if="store.selectedBlock.value">
          <div class="toolbar-divider" />
          <div class="inspector-inputs" @pointerdown.stop @mousedown.stop @click.stop>
            <strong :title="store.selectedBlock.value.name">
              {{ store.selectedBlock.value.name }}:
            </strong>
            <label>X:<input
              type="number"
              :value="store.selectedBlock.value.x"
              @change="store.updateBlock(store.selectedBlock.value.id, { x: Number($event.target.value) })"
            /></label>
            <label>Y:<input
              type="number"
              :value="store.selectedBlock.value.y"
              @change="store.updateBlock(store.selectedBlock.value.id, { y: Number($event.target.value) })"
            /></label>
            <label>W:<input
              type="number"
              :value="store.selectedBlock.value.width"
              @change="store.updateBlock(store.selectedBlock.value.id, { width: Number($event.target.value) })"
            /></label>
            <label>H:<input
              type="number"
              :value="store.selectedBlock.value.height"
              @change="store.updateBlock(store.selectedBlock.value.id, { height: Number($event.target.value) })"
            /></label>
          </div>
        </template>

        <div class="toolbar-divider" />

        <button type="button" title="Сбросить все панели к исходным позициям" @click="onReset">
          <span>⟲</span>
          <span>Сброс</span>
        </button>

        <button type="button" title="Экспортировать JSON раскладки" @click.stop="openExport">
          <span>💾</span>
          <span>Экспорт</span>
        </button>

        <button type="button" title="Импортировать JSON раскладки" @click.stop="openImport">
          <span>📥</span>
          <span>Импорт</span>
        </button>
      </template>
    </aside>

    <!-- Export Modal -->
    <div
      v-if="showExportModal"
      class="designer-modal-backdrop"
      @pointerdown.stop
      @mousedown.stop
      @click.stop="showExportModal = false"
    >
      <div class="designer-modal" role="dialog" aria-labelledby="export-title" @click.stop>
        <h3 id="export-title">Экспорт макета UI (JSON)</h3>
        <p style="font-size:12px;color:var(--col-text-dim);margin:0 0 10px;">
          Скопируйте конфигурацию для фиксации в коде или сохранения:
        </p>
        <textarea readonly :value="exportText" @focus="$event.target.select()"></textarea>
        <div class="designer-modal-actions">
          <button type="button" @click.stop="copyExport">
            {{ copiedNotice ? '✓ Скопировано!' : '📋 Скопировать' }}
          </button>
          <button type="button" @click.stop="showExportModal = false">Закрыть</button>
        </div>
      </div>
    </div>

    <!-- Import Modal -->
    <div
      v-if="showImportModal"
      class="designer-modal-backdrop"
      @pointerdown.stop
      @mousedown.stop
      @click.stop="showImportModal = false"
    >
      <div class="designer-modal" role="dialog" aria-labelledby="import-title" @click.stop>
        <h3 id="import-title">Импорт макета UI</h3>
        <p style="font-size:12px;color:var(--col-text-dim);margin:0 0 10px;">
          Вставьте ранее экспортированный JSON:
        </p>
        <textarea v-model="importText" placeholder="{ ... }"></textarea>
        <p v-if="importError" style="color:#ff8b7b;font-size:12px;margin:6px 0 0;">{{ importError }}</p>
        <div class="designer-modal-actions">
          <button type="button" class="is-active" @click.stop="applyImport">Применить</button>
          <button type="button" @click.stop="showImportModal = false">Отмена</button>
        </div>
      </div>
    </div>
  </div>
</template>
