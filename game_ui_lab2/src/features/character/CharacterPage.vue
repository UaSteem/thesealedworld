<script setup>
import ModifierGroups from './ModifierGroups.vue'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  character: { type: Object, required: true },
  inventory: { type: Object, required: true },
  tab: { type: String, default: 'inventory' },
  act: { type: Function, required: true },
})
const emit = defineEmits(['tab-change', 'close'])

const tabs = [
  { id: 'inventory', label: 'Снаряжение' },
  { id: 'attributes', label: 'Характеристики' },
  { id: 'builds', label: 'Билды' },
]
const filters = [
  { id: 'all', label: 'Все', icon: '/static/images/ui/inventory-icons/items.svg' },
  { id: 'weapons', label: 'Оружие', icon: '/static/images/ui/inventory-gear/weapon_sword.svg', types: ['weapon'] },
  { id: 'armor', label: 'Броня', icon: '/static/images/ui/inventory-gear/torso.svg', types: ['armor', 'garment'] },
  { id: 'accessories', label: 'Аксессуары', icon: '/static/images/ui/inventory-gear/ring.svg', types: ['accessory'] },
  { id: 'consumables', label: 'Расходники', icon: '/static/images/ui/inventory-gear/consumable.svg', types: ['consumable'] },
  { id: 'resources', label: 'Ресурсы', icon: '/static/images/ui/inventory-gear/resource.svg', types: ['resource', 'material'] },
  { id: 'quest', label: 'Квестовые', icon: '/static/images/ui/inventory-gear/quest.svg', types: ['quest'] },
]
const attributeGroups = [
  { title: 'Тело', entries: [['strength', 'Сила'], ['agility', 'Ловкость'], ['endurance', 'Выносливость']] },
  { title: 'Разум', entries: [['intellect', 'Интеллект'], ['memory', 'Память'], ['mental', 'Ментальность']] },
  { title: 'Чувства', entries: [['perception', 'Восприятие'], ['projection', 'Проекция'], ['prediction', 'Предвидение']] },
]
const skillNames = {
  weapon_mastery: 'Владение оружием', tactical: 'Боевые стили', armor: 'Броня',
  combat_support: 'Боевая поддержка', crafting: 'Ремёсла', gathering: 'Сбор ресурсов',
  trade: 'Торговля', leadership: 'Лидерство', survival: 'Выживание',
}
const leftSlots = ['head_armor', 'main_hand', 'chest_armor', 'belt_accessory', 'legs_armor']
const rightSlots = ['outer_garment', 'arms_armor', 'gloves_garment', 'off_hand', 'feetwear']
const topSlots = ['amulet', 'earring']
const bottomSlots = ['ring_1', 'ring_2']

const filter = ref('all')
const selectedId = ref(null)
const pinned = ref(false)
const notice = ref('')
const openedGroups = ref(['weapon_mastery', 'armor'])
const hideUnavailableSkills = ref(false)
const bagScroller = ref(null)
const columns = ref(8)
const cellSize = ref(48)
const bagHeight = ref(0)
let bagObserver

function measureBag() {
  const element = bagScroller.value
  if (!element?.clientWidth || !element.clientHeight) return
  const available = Math.max(0, element.clientWidth - 24)
  columns.value = Math.max(8, Math.floor((available + 5) / 57))
  cellSize.value = Math.max(48, Math.min(64, Math.floor((available - (columns.value - 1) * 5) / columns.value)))
  bagHeight.value = Math.max(0, (bagScroller.value?.clientHeight || 0) - 24)
}
onMounted(() => {
  measureBag()
  bagObserver = new ResizeObserver(measureBag)
  if (bagScroller.value) bagObserver.observe(bagScroller.value)
})
onUnmounted(() => bagObserver?.disconnect())
watch(bagScroller, (element, previous) => {
  if (previous) bagObserver?.unobserve(previous)
  if (element) { bagObserver?.observe(element); requestAnimationFrame(measureBag) }
}, { flush: 'post' })

const items = computed(() => props.inventory?.items || [])
const visibleItems = computed(() => {
  const current = filters.find(entry => entry.id === filter.value)
  return current?.types ? items.value.filter(item => current.types.includes(item.item_type)) : items.value
})
const selected = computed(() => items.value.find(item => item.item_id === selectedId.value) || null)
const equipped = computed(() => Object.fromEntries((props.character?.equipment || []).map(slot => [slot.slot_id, slot])))
const skillGroups = computed(() => Object.entries(skillNames).map(([id, name]) => ({
  id, name, items: (props.character?.skill_catalog || []).filter(skill => skill.group === id),
})).map(group => ({ ...group, total: group.items.length, items: hideUnavailableSkills.value ? group.items.filter(skill => skill.unlocked) : group.items })).filter(group => group.items.length))
const openedCount = computed(() => (props.character?.skill_catalog || []).filter(skill => skill.unlocked).length)
const weight = computed(() => props.inventory?.weight || { value: 0, worn: 0, limit: 1 })
const usedWeight = computed(() => Math.min(100, 100 * weight.value.value / (weight.value.limit || 1)))

// Row-major presentation packing from the accepted inventory mock; no capacity or game rule.
const packedItems = computed(() => {
  const occupied = new Set()
  return visibleItems.value.map(item => {
    const width = Math.max(1, Math.min(columns.value, Math.floor(Number(item.grid_w) || 1)))
    const height = Math.max(1, Math.floor(Number(item.grid_h) || 1))
    for (let row = 0; ; row++) for (let col = 0; col <= columns.value - width; col++) {
      let free = true
      for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) {
        if (occupied.has(`${row + y}:${col + x}`)) free = false
      }
      if (!free) continue
      for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) occupied.add(`${row + y}:${col + x}`)
      return { item, col, row, width, height }
    }
  })
})
const gridRows = computed(() => Math.max(
  5,
  Math.floor((bagHeight.value + 5) / (cellSize.value + 5)),
  ...packedItems.value.map(entry => entry.row + entry.height),
))
const emptyCells = computed(() => Array.from({ length: gridRows.value * columns.value }, (_, index) => ({
  row: Math.floor(index / columns.value) + 1,
  col: index % columns.value + 1,
})))

watch(filter, () => { selectedId.value = null; pinned.value = false })
watch(() => props.tab, () => { selectedId.value = null; pinned.value = false; notice.value = '' })
watch(items, () => {
  if (!items.value.some(item => item.item_id === selectedId.value)) { selectedId.value = null; pinned.value = false }
})

function chooseItem(item) { selectedId.value = item.item_id; pinned.value = true }
function previewItem(item) { if (!pinned.value) selectedId.value = item.item_id }
function endPreview() { if (!pinned.value) selectedId.value = null }
function closeDetails() { selectedId.value = null; pinned.value = false }
function toggleGroup(id) {
  openedGroups.value = openedGroups.value.includes(id)
    ? openedGroups.value.filter(group => group !== id)
    : [...openedGroups.value, id]
}
async function showAction(type) {
  try {
    const response = await props.act({ type, itemId: type === 'equip' ? selected.value?.item_id : undefined })
    notice.value = response?.notice || 'Ответ действия не содержит сообщения.'
  } catch {
    notice.value = 'Не удалось получить ответ на действие.'
  }
}
function onKeydown(event) {
  if (event.key !== 'Escape') return
  if (notice.value) notice.value = ''
  else if (selected.value) closeDetails()
  else emit('close')
  event.stopPropagation()
}
</script>

<template>
  <section class="character-page" aria-labelledby="character-title" tabindex="-1" @keydown="onKeydown">
    <header class="page-heading">
      <h2 id="character-title">Персонаж</h2>
      <button type="button" class="close-button" aria-label="Вернуться в игру" @click="emit('close')">×</button>
    </header>
    <nav class="page-tabs" aria-label="Разделы персонажа">
      <button v-for="entry in tabs" :key="entry.id" type="button" :aria-pressed="tab === entry.id" @click="emit('tab-change', entry.id)">{{ entry.label }}</button>
    </nav>

    <div v-if="tab === 'inventory'" class="inventory-layout">
      <aside class="character-rail" aria-label="Персонаж">
        <div class="identity"><h3>{{ character.name }}</h3><span>Макет</span></div>
        <p class="build-name">{{ character.title }}</p>
        <div class="vitals" aria-label="Ресурсы стартового персонажа">
          <div v-for="vital in [{ key: 'hp', label: 'HP' }, { key: 'energy', label: 'EN' }, { key: 'stamina', label: 'CONC' }]" :key="vital.key" class="vital" :class="`vital-${vital.key}`">
            <span>{{ vital.label }}</span><meter min="0" :max="character[`max_${vital.key}`] || 1" :value="character[vital.key] || 0" :aria-label="vital.label" /><b>{{ character[vital.key] }} / {{ character[`max_${vital.key}`] }}</b>
          </div>
        </div>
        <div class="loadout" aria-label="Надетые предметы">
          <div class="slot-column slot-left">
            <button v-for="id in leftSlots" :key="id" type="button" class="gear-slot" :class="{ equipped: equipped[id]?.items?.length }" :title="`${equipped[id]?.label || id}: ${equipped[id]?.items?.join(' / ') || 'Пусто'}`" :aria-label="`${equipped[id]?.label || id}: ${equipped[id]?.items?.join(' / ') || 'Пусто'}`">
              <img v-if="equipped[id]?.icon" :src="`/static/images/ui/inventory-gear/${equipped[id].icon}.svg`" alt=""><span>{{ equipped[id]?.label }}</span>
            </button>
          </div>
          <div class="slot-center">
            <div class="slot-pair"><button v-for="id in topSlots" :key="id" type="button" class="gear-slot" :class="{ equipped: equipped[id]?.items?.length }" :title="`${equipped[id]?.label || id}: ${equipped[id]?.items?.join(' / ') || 'Пусто'}`" :aria-label="`${equipped[id]?.label || id}: ${equipped[id]?.items?.join(' / ') || 'Пусто'}`"><img v-if="equipped[id]?.icon" :src="`/static/images/ui/inventory-gear/${equipped[id].icon}.svg`" alt=""><span>{{ equipped[id]?.label }}</span></button></div>
            <figure class="avatar"><img :src="character.avatar_url" :alt="`Демонстрационный образ персонажа ${character.name}`"></figure>
            <div class="slot-pair"><button v-for="id in bottomSlots" :key="id" type="button" class="gear-slot" :class="{ equipped: equipped[id]?.items?.length }" :title="`${equipped[id]?.label || id}: ${equipped[id]?.items?.join(' / ') || 'Пусто'}`" :aria-label="`${equipped[id]?.label || id}: ${equipped[id]?.items?.join(' / ') || 'Пусто'}`"><img v-if="equipped[id]?.icon" :src="`/static/images/ui/inventory-gear/${equipped[id].icon}.svg`" alt=""><span>{{ equipped[id]?.label }}</span></button></div>
          </div>
          <div class="slot-column slot-right">
            <button v-for="id in rightSlots" :key="id" type="button" class="gear-slot" :class="{ equipped: equipped[id]?.items?.length }" :title="`${equipped[id]?.label || id}: ${equipped[id]?.items?.join(' / ') || 'Пусто'}`" :aria-label="`${equipped[id]?.label || id}: ${equipped[id]?.items?.join(' / ') || 'Пусто'}`">
              <img v-if="equipped[id]?.icon" :src="`/static/images/ui/inventory-gear/${equipped[id].icon}.svg`" alt=""><span>{{ equipped[id]?.label }}</span>
            </button>
          </div>
        </div>
        <div class="power"><span>Сила персонажа</span><strong>{{ Number(character.gear_score || 0).toFixed(1) }} <small>GS</small></strong></div>
        <details class="rail-details"><summary>Атрибуты</summary><div v-for="group in attributeGroups" :key="group.title"><b>{{group.title}}</b><dl><div v-for="[id,label] in group.entries" :key="id"><dt>{{label}}</dt><dd>{{character.attributes[id]}}</dd></div></dl></div></details>
        <details class="rail-details"><summary>Навыки</summary><dl><div v-for="skill in character.skill_catalog.filter(s=>s.unlocked)" :key="skill.key"><dt>{{skill.label || skill.name}}</dt><dd>{{skill.progress}}%</dd></div></dl></details>
        <details class="rail-details"><summary>Модификаторы</summary><ModifierGroups :sheet="character.modifier_sheet"/></details>
      </aside>

      <section class="backpack" aria-label="Рюкзак" @mouseleave="endPreview">
        <header class="backpack-heading"><h3>Рюкзак</h3><span>{{ filter === 'all' ? `Всего: ${items.length} предметов` : `Показано: ${visibleItems.length} из ${items.length}` }}</span></header>
        <div class="filters" role="group" aria-label="Фильтры предметов">
          <button v-for="entry in filters" :key="entry.id" type="button" :aria-pressed="filter === entry.id" @click="filter = entry.id"><img :src="entry.icon" alt=""><span>{{ entry.label }}</span><small>{{ entry.types ? items.filter(item => entry.types.includes(item.item_type)).length : items.length }}</small></button>
        </div>
        <div class="bag-frame">
          <div ref="bagScroller" class="bag-scroller">
            <div class="bag-grid" :style="{ '--grid-rows': gridRows, '--columns': columns, '--cell': `${cellSize}px` }">
              <span v-for="cell in emptyCells" :key="`${cell.row}:${cell.col}`" class="empty-cell" :style="{ gridRow: cell.row, gridColumn: cell.col }" aria-hidden="true"></span>
              <button v-for="entry in packedItems" :key="entry.item.item_id" type="button" class="item" :class="[{ selected: selectedId === entry.item.item_id }, `tier-${entry.item.tier}`]" :style="{ gridColumn: `${entry.col + 1} / span ${entry.width}`, gridRow: `${entry.row + 1} / span ${entry.height}` }" :aria-label="`${entry.item.name}, ${entry.item.rarity_label}`" @mouseenter="previewItem(entry.item)" @focus="previewItem(entry.item)" @click="chooseItem(entry.item)">
                <img :src="entry.item.texture_url || entry.item.thumbnail_url || entry.item.image_url" alt=""><span>T{{ entry.item.tier }}</span>
              </button>
              <p v-if="!visibleItems.length" class="empty-bag">В этой категории пока нет предметов<br><small>В слепке стенда доступны только шесть мечей</small></p>
            </div>
          </div>
        </div>
        <footer class="bag-footer">
          <div class="weight"><span>Вес · MOCK {{ Number(weight.value).toFixed(1) }} / {{ weight.limit }} кг</span><small>Включая надетое: {{ weight.worn }} кг (макет)</small><span class="weight-track"><span :style="{ width: `${usedWeight}%` }"></span></span></div>
          <button type="button" @click="showAction('disassembly')">Разборка</button><button type="button" @click="showAction('craft')">Крафт</button>
        </footer>
        <div v-if="selected" class="details" :class="{ pinned }" role="dialog" aria-label="Осмотр предмета" @mouseleave="endPreview">
          <header><small>{{ pinned ? 'ПРОСМОТР ЗАКРЕПЛЁН' : 'ПРОСМОТР ПРЕДМЕТА' }}</small><button type="button" aria-label="Закрыть осмотр" @click="closeDetails">×</button></header>
          <h3>{{ selected.name }}</h3><p class="rarity" :class="`tier-${selected.tier}`">{{ selected.rarity_label }} · T{{ selected.tier }} · Одноручный меч</p>
          <div class="details-scroll"><div class="details-top"><img :src="selected.texture_url || selected.thumbnail_url || selected.image_url" alt=""><dl><div v-for="(line, index) in selected.details || []" :key="index"><dt>{{ line.label }}</dt><dd>{{ line.value }}</dd></div></dl></div>
            <div v-if="selected.affixes?.length" class="affixes"><h4>ОСОБЫЕ СВОЙСТВА</h4><p v-for="(line, index) in selected.affixes" :key="index">{{ line.label }} {{ line.value }}</p></div>
            <h4>ОПИСАНИЕ</h4><p class="description">{{ selected.description }}</p>
          </div>
          <button v-if="pinned" type="button" class="item-action" @click="showAction('equip')">{{ equipped.main_hand?.items?.length ? 'Заменить' : 'Надеть' }}</button>
        </div>
      </section>
    </div>

    <div v-else-if="tab === 'attributes'" class="attributes-layout">
      <div class="attribute-side">
        <section class="attribute-panel"><h3>Атрибуты</h3><div class="attribute-groups"><div v-for="group in attributeGroups" :key="group.title"><h4>{{ group.title }}</h4><dl><div v-for="[key, label] in group.entries" :key="key"><dt>{{ label }}</dt><dd>{{ character.attributes?.[key] ?? '—' }}</dd></div></dl></div></div></section>
        <section class="modifier-panel"><h3>Модификаторы</h3><p class="fixture-note">Для текущей экипировки · демонстрационные значения.</p><ModifierGroups :sheet="character.modifier_sheet"/></section>
      </div>
      <section class="skills-panel"><header><h3>Навыки</h3><div class="skills-options"><span>Открыто {{ openedCount }} / {{ character.skill_catalog?.length || 0 }} · прокрутка</span><label><input v-model="hideUnavailableSkills" type="checkbox"> Скрыть недоступные</label></div></header><div class="skills-scroller"><div v-for="group in skillGroups" :key="group.id" class="skill-group"><button type="button" :aria-expanded="openedGroups.includes(group.id)" @click="toggleGroup(group.id)">{{ openedGroups.includes(group.id) ? '−' : '+' }} {{ group.name }} · {{ group.items.filter(skill => skill.unlocked).length }} / {{ group.total }}</button><div v-if="openedGroups.includes(group.id)" class="skill-list"><div v-for="skill in group.items" :key="skill.key" class="skill" :class="{ locked: !skill.unlocked }"><span class="skill-name"><span v-if="!skill.unlocked" aria-hidden="true">🔒</span>{{ skill.name }}</span><span>{{ skill.unlocked ? `${skill.progress}%` : 'Закрыт' }}</span><progress :max="100" :value="skill.unlocked ? skill.progress : 0" :aria-label="`Прогресс: ${skill.name}`" /></div></div></div></div></section>
    </div>

    <section v-else class="builds-panel"><h3>Билды не реализованы</h3><p>Концепция под вопросом. Настройка и переключение сборок пока отсутствуют.</p></section>
    <div v-if="notice" class="notice-backdrop" role="presentation"><div class="notice" role="alertdialog" aria-labelledby="notice-title" aria-describedby="notice-text"><h3 id="notice-title">Локальный макет</h3><p id="notice-text">{{ notice }}</p><button type="button" @click="notice = ''">Закрыть</button></div></div>
  </section>
</template>

<style scoped src="./character.css"></style>
