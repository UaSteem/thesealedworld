<script setup>
import { computed } from 'vue';

const props = defineProps({
  character: {
    type: Object,
    default: () => ({})
  },
  disabled: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['character']);

const vitalBars = computed(() => {
  const c = props.character || {};
  const hp = c.hp ?? 117;
  const maxHp = c.max_hp ?? 117;
  const en = c.energy ?? 31;
  const maxEn = c.max_energy ?? 31;
  const cn = c.stamina ?? 54;
  const maxCn = c.max_stamina ?? 54;

  return [
    {
      key: 'HP',
      label: 'Здоровье',
      val: hp,
      max: maxHp,
      pct: Math.min(100, Math.max(0, maxHp ? Math.round((hp / maxHp) * 100) : 0)),
      color: '#cc4c3d' // Red
    },
    {
      key: 'EN',
      label: 'Энергия',
      val: en,
      max: maxEn,
      pct: Math.min(100, Math.max(0, maxEn ? Math.round((en / maxEn) * 100) : 0)),
      color: '#3d86cc' // Blue
    },
    {
      key: 'CN',
      label: 'Концентрация',
      val: cn,
      max: maxCn,
      pct: Math.min(100, Math.max(0, maxCn ? Math.round((cn / maxCn) * 100) : 0)),
      color: '#3ea65a' // Green
    }
  ];
});

const defaultEffects = [
  { id: 'eff_shield', name: 'Каменная стойка', type: 'buff', icon: '🛡️', duration: '3х', desc: '+10 броня' },
  { id: 'eff_focus', name: 'Концентрация', type: 'buff', icon: '✨', duration: '5х', desc: '+15% шанс крита' },
  { id: 'eff_swift', name: 'Ускорение', type: 'buff', icon: '⚡', duration: '2х', desc: '+1 действие' },
  { id: 'eff_bleed', name: 'Кровотечение', type: 'debuff', icon: '🩸', duration: '2х', desc: '-6 HP / ход' }
];

const activeEffects = computed(() => {
  if (Array.isArray(props.character?.effects) && props.character.effects.length > 0) {
    return props.character.effects;
  }
  return defaultEffects;
});

function onClick() {
  if (!props.disabled) {
    emit('character');
  }
}
</script>

<template>
  <div
    class="player-hud"
    :class="{ 'is-disabled': disabled }"
    role="button"
    :tabindex="disabled ? -1 : 0"
    :aria-disabled="disabled"
    aria-label="Открыть окно персонажа"
    @click="onClick"
    @keydown.enter="onClick"
    @keydown.space.prevent="onClick"
  >
    <!-- 1. LEFT BLUE ZONE: Аватар (верхние 25% по центру портрета) -->
    <div class="player-hud-avatar-frame" title="Нажмите, чтобы открыть окно персонажа">
      <img
        class="player-hud-avatar"
        :src="character?.avatar_url || '/static/images/avatars/rook7.webp'"
        :alt="character?.name || 'Персонаж'"
      />
      <div class="avatar-glass-overlay"></div>
    </div>

    <!-- 2. RIGHT BODY: 3 горизонтальных слоя -->
    <div class="player-hud-body">
      <!-- Слой 1 (00ff00): Зона имени игрока (выровнена по центру) -->
      <div class="player-hud-name-zone">
        <strong class="player-hud-name">{{ character?.name || 'Ada Guard' }}</strong>
      </div>

      <!-- Слой 2 (000000): Зона vital статусов (без лишней рамки, цвет фона совпадает с HUD) -->
      <div class="player-hud-vitals-zone">
        <div
          v-for="bar in vitalBars"
          :key="bar.key"
          class="vital-row"
          :class="`vital-${bar.key.toLowerCase()}`"
          :title="`${bar.label}: ${bar.val} / ${bar.max}`"
        >
          <span class="vital-key">{{ bar.key }}</span>
          <div class="vital-track">
            <span
              class="vital-fill"
              :style="{ width: bar.pct + '%', backgroundColor: bar.color }"
            >
              <i class="vital-shine"></i>
            </span>
          </div>
          <span class="vital-val">{{ bar.val }}<small>/{{ bar.max }}</small></span>
        </div>
      </div>

      <!-- Слой 3 (ffff00): Зона статусбара (только иконки эффектов со свечением) -->
      <div class="player-hud-status-zone" aria-label="Статусбар: эффекты, бонусы и дебафы">
        <div
          v-for="eff in activeEffects"
          :key="eff.id"
          class="status-chip"
          :class="`is-${eff.type}`"
          :title="`${eff.name}${eff.duration ? ' (' + eff.duration + ')' : ''}${eff.desc ? '\n' + eff.desc : ''}`"
          @click.stop
        >
          <span class="status-chip-icon">{{ eff.icon }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 5b5959 — общий блок HUD Игрока */
.player-hud {
  display: flex;
  align-items: stretch;
  gap: 10px;
  width: 100%;
  height: 100%;
  padding: 8px 10px;
  box-sizing: border-box;
  background: var(--col-bg-surface, #1a2028);
  border: 1px solid var(--col-border, #81704f);
  border-radius: 6px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45);
  cursor: pointer;
  user-select: none;
  overflow: hidden;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  text-align: left;
}

.player-hud:hover:not(.is-disabled) {
  border-color: var(--col-border-strong, #ab8c59);
  box-shadow: 0 4px 22px rgba(210, 178, 115, 0.18);
}

.player-hud.is-disabled {
  cursor: default;
  opacity: 1;
}

/* СИНИЙ — Аватар (верхние 25% по центру портрета) */
.player-hud-avatar-frame {
  position: relative;
  flex: 0 0 84px;
  height: 100%;
  min-height: 80px;
  overflow: hidden;
  border-radius: 4px;
  border: 1px solid var(--col-border, #81704f);
  background: #090c10;
  box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.7);
}

.player-hud-avatar {
  position: absolute;
  width: 220%;
  height: 220%;
  top: 0;
  left: 50%;
  transform: translate(-50%, -6%);
  object-fit: cover;
  pointer-events: none;
  transition: transform 0.25s ease;
}

.player-hud:hover:not(.is-disabled) .player-hud-avatar {
  transform: translate(-50%, -6%) scale(1.04);
}

.avatar-glass-overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: 3px;
  box-shadow: inset 0 0 8px rgba(0, 0, 0, 0.5);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.04) 0%, rgba(0, 0, 0, 0.15) 100%);
}

/* Правая часть: 3 горизонтальных слоя */
.player-hud-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 4px;
}

/* СЛОЙ 1 (00ff00) — Зона имени игрока (выровнена по центру) */
.player-hud-name-zone {
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  min-width: 0;
  flex: 0 0 auto;
}

.player-hud-name {
  font: 16px/1.2 var(--font-world, 'EB Garamond', serif);
  color: var(--col-text-world, #eee5d4);
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: 0.4px;
  text-align: center;
}

/* СЛОЙ 2 (000000) — Зона vital статусов (без полоски, одинаковый фон с интерфейсом HUD) */
.player-hud-vitals-zone {
  background: var(--col-bg-surface, #1a2028);
  border: none;
  padding: 4px 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
  flex: 1;
  min-height: 0;
}

.vital-row {
  display: grid;
  grid-template-columns: 20px minmax(0, 1fr) 52px;
  gap: 6px;
  align-items: center;
  line-height: 1;
}

.vital-key {
  font: 9px/1 var(--font-mono, 'JetBrains Mono', monospace);
  font-weight: 700;
  color: #9aa5b1;
  text-align: left;
  letter-spacing: 0.5px;
}

.vital-track {
  height: 6px;
  background: rgba(0, 0, 0, 0.45);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 2px;
  overflow: hidden;
  position: relative;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.6);
}

.vital-fill {
  display: block;
  height: 100%;
  border-radius: 2px;
  position: relative;
  transition: width 0.25s ease;
}

.vital-shine {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 50%;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.38) 0%, rgba(255, 255, 255, 0) 100%);
  border-radius: 2px 2px 0 0;
}

/* Одинаковый компактный размер цифр значений HP, EN, CN */
.vital-val {
  font: 9px/1 var(--font-mono, 'JetBrains Mono', monospace);
  font-variant-numeric: tabular-nums;
  color: var(--col-text-primary, #e3e8ed);
  text-align: right;
  white-space: nowrap;
}

.vital-val small {
  font-size: 9px;
  color: var(--col-text-dim, #a7b2be);
}

/* СЛОЙ 3 (ffff00) — Зона статусбара (иконки эффектов со свечением) */
.player-hud-status-zone {
  display: flex;
  align-items: center;
  gap: 5px;
  overflow-x: auto;
  scrollbar-width: none;
  flex: 0 0 auto;
  padding-top: 1px;
}

.player-hud-status-zone::-webkit-scrollbar {
  display: none;
}

.status-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  box-sizing: border-box;
  background: rgba(16, 20, 26, 0.7);
  border-radius: 4px;
  cursor: help;
  transition: background 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease, transform 0.1s ease;
  flex-shrink: 0;
}

.status-chip:hover {
  background: rgba(26, 32, 40, 0.95);
  transform: scale(1.1);
}

/* Позитивные эффекты: золотая обводка + легкое зеленое свечение */
.status-chip.is-buff {
  border: 1px solid var(--col-accent, #d2b273);
  box-shadow: 0 0 6px rgba(78, 196, 102, 0.45);
}

.status-chip.is-buff:hover {
  border-color: #f3d492;
  box-shadow: 0 0 9px rgba(78, 196, 102, 0.75);
}

/* Негативные эффекты: красная обводка + легкое красное свечение */
.status-chip.is-debuff {
  border: 1px solid #d64537;
  box-shadow: 0 0 6px rgba(214, 69, 55, 0.55);
}

.status-chip.is-debuff:hover {
  border-color: #ff6b5e;
  box-shadow: 0 0 9px rgba(214, 69, 55, 0.85);
}

.status-chip-icon {
  font-size: 13px;
  line-height: 1;
  display: block;
}
</style>
