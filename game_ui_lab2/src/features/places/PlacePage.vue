<script setup>
import {computed, onBeforeUnmount, onActivated, onDeactivated, ref, watch} from 'vue';
import {arena, arenaDetails, districts, titles, descriptions, actions} from './placeData.js';
import {constructionSnapshots} from './constructionFixtures.js';

const props = defineProps({id: {type: String, required: true}});
const emit = defineEmits(['navigate']);
const districtId = ref('administrative');
const path = ref([]);
const showPlaces = ref(true);
const hint = ref('Наведите на объект, чтобы узнать действие');
const notice = ref('');
const constructionStep = ref(0);
const lotOwned = ref(false);
const houseBuilt = ref(false);

const isArena = computed(() => props.id === 'arena');
const place = computed(() => isArena.value ? arena : districts[districtId.value]);
const spots = computed(() => isArena.value ? arena.spots : place.value.spots.map(([id, name, x, y, box]) => ({id, name, x, y, box})));
const selected = computed(() => path.value.at(-1));
const selectedName = computed(() => isArena.value ? arena.spots.find(spot => spot.id === selected.value)?.name : titles[selected.value]);
const snapshot = computed(() => constructionSnapshots[constructionStep.value]);
const productRows = computed(() => selected.value === 'shop1' ? ['Железный меч','Щит','Наконечники'] : selected.value === 'shop2' ? ['Лечебные травы','Настой','Сухой сбор'] : ['Походный паёк','Верёвка','Фляга']);
const serviceDescription = computed(() => {
  if (selected.value === 'house' && houseBuilt.value) return 'Ваш дом готов в демонстрационном состоянии.';
  if (selected.value === 'lot' && lotOwned.value) return 'Участок закреплён за вами в демо. Можно показать следующий шаг строительства.';
  return descriptions[selected.value] || 'Ассортимент выбранной лавки игрока.';
});
const serviceActions = computed(() => {
  if (selected.value === 'lot' && lotOwned.value) return [['Построить дом (демо)', 'build-house']];
  if (selected.value === 'house' && houseBuilt.value) return [['Войти в свой дом', 'home']];
  return actions[selected.value] || [];
});

function resetPath() { path.value = []; notice.value = ''; }
function select(id) { path.value = [id]; notice.value = ''; }
function go(id) { path.value = [...path.value, id]; notice.value = ''; }
function back() { path.value = path.value.slice(0, -1); notice.value = ''; }
function changeDistrict(id) { districtId.value = id; resetPath(); }
function arenaAction(label, target) {
  if (target === 'city' || target === 'combat') { resetPath(); emit('navigate', target); }
  else if (target === 'close') resetPath();
  else notice.value = `${label}: демонстрация. Серверное действие не отправлено.`;
}
function serviceAction(target) {
  if (target === 'buy-lot') { lotOwned.value = true; notice.value = 'Участок приобретён только в демо.'; }
  else if (target === 'build-house') { houseBuilt.value = true; notice.value = 'Дом построен только в демо.'; }
  else if (target === 'demo') notice.value = 'Пробный экран услуги. Серверное действие не отправляется.';
  else go(target);
}
function constructionAction() {
  constructionStep.value = 1;
  notice.value = 'Готовый ответ локальной демонстрации. Серверное действие не отправлено.';
}
function onKeydown(event) { if (event.key === 'Escape' && path.value.length) { back(); event.preventDefault(); event.stopPropagation(); } }
onActivated(() => window.addEventListener('keydown', onKeydown));
onDeactivated(() => window.removeEventListener('keydown', onKeydown));
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown));
watch(() => props.id, () => { resetPath(); hint.value = 'Наведите на объект, чтобы узнать действие'; });
</script>

<template>
  <section class="place-page client-page" :aria-label="isArena ? 'Городская арена' : 'Кварталы города'">
    <div class="place-art-stage">
      <div class="place-backdrop" :style="{backgroundImage: `url(${place.image})`}" aria-hidden="true"></div>
      <div class="place-art" :style="{backgroundImage: `url(${place.image})`}">
        <button v-for="spot in spots" :key="spot.id" class="place-hotspot" :class="{'is-labelled': showPlaces}"
          :style="{left: spot.box[0] + '%', top: spot.box[1] + '%', width: spot.box[2] - spot.box[0] + '%', height: spot.box[3] - spot.box[1] + '%'}"
          :aria-label="spot.name" :title="spot.hint || `${spot.name} · нажмите, чтобы войти`"
          @mouseenter="hint = spot.hint || `${spot.name} · нажмите, чтобы войти`" @mouseleave="hint = isArena ? 'Наведите на объект, чтобы узнать действие' : 'Наведите на объект квартала · все действия — локальная демонстрация'"
          @focus="hint = spot.hint || `${spot.name} · нажмите, чтобы войти`" @click="select(spot.id)">
          <span class="place-hotspot-label" :style="{left: ((spot.x - spot.box[0]) / (spot.box[2] - spot.box[0]) * 100) + '%', top: ((spot.y - spot.box[1]) / (spot.box[3] - spot.box[1]) * 100) + '%'}">{{ spot.name }}</span>
        </button>
      </div>
    </div>
    <header class="place-header">
      <div><h1>{{ isArena ? arena.title : `${place.name} квартал` }}</h1><p>{{ place.subtitle }}</p><p class="place-context-hint" role="status">{{ hint }}</p></div>
      <div class="place-header-actions">
        <button v-if="isArena" class="place-button" @click="showPlaces = !showPlaces">{{ showPlaces ? 'Скрыть подписи' : 'Показать объекты' }}</button>
        <button v-else class="place-button" @click="emit('navigate', 'city')">В город</button>
      </div>
    </header>
    <nav v-if="!isArena" class="place-district-nav" aria-label="Кварталы">
      <button v-for="(district, key) in districts" :key="key" class="place-button" :aria-current="districtId === key ? 'page' : undefined" @click="changeDistrict(key)">{{ district.name }}</button>
      <button class="place-button place-label-toggle" @click="showPlaces = !showPlaces">{{ showPlaces ? 'Скрыть подписи' : 'Показать объекты' }}</button>
    </nav>

    <div v-if="selected" class="place-modal-backdrop" @click.self="resetPath">
      <section class="place-modal" :class="{'place-modal--construction': selected === 'construction'}" role="dialog" aria-modal="true" :aria-label="selectedName">
        <div class="place-modal-heading"><div><h2>{{ selectedName }}</h2><p v-if="!isArena">{{ place.name }} квартал{{ path.length > 1 ? ` / ${titles[path[0]]}` : '' }} · вложение {{ path.length }}</p></div><div class="place-modal-controls"><button v-if="!isArena" class="place-button" @click="back">Назад</button><button class="place-button place-close" aria-label="Закрыть" @click="resetPath">×</button></div></div>

        <template v-if="isArena"><p class="place-intro">{{ arenaDetails[selected]?.text }}</p><div class="place-action-list"><button v-for="([label, target], index) in arenaDetails[selected]?.actions" :key="index" class="place-button" @click="arenaAction(label, target)">{{ label }}</button></div><p class="place-notice">{{ notice || 'Пробная сцена · действия пока демонстрационные' }}</p></template>

        <template v-else-if="selected === 'construction'">
          <p class="place-intro">Куда сдаём ресурсы — то строим. Завершение одного проекта обнуляет ВСЕ три вклада.</p>
          <p class="place-muted">Цикл {{ snapshot.cycle }} · при себе: {{ snapshot.inventory }}</p>
          <div class="construction-options"><article v-for="(option, index) in snapshot.options" :key="index" class="construction-option"><h3>{{ option.name }}</h3><div v-for="([resource, amount, percent], row) in option.rows" :key="row" class="construction-resource"><div><span>{{ resource }}</span><strong>{{ amount }}</strong></div><div class="construction-track"><i :style="{width: percent + '%'}"></i></div><div class="construction-buttons"><button class="place-button" @click="constructionAction">Сдать 10</button><button class="place-button" @click="constructionAction">Доложить</button></div></div></article></div>
          <div class="construction-bottom"><p>Построено в демо: {{ snapshot.built }}</p><button class="place-button" @click="constructionStep = 0; notice = ''">Сбросить демо</button></div>
          <p class="place-notice">{{ notice || snapshot.notice }} · локальная демонстрация</p>
        </template>

        <template v-else><p class="place-intro">{{ serviceDescription }}</p>
          <div v-if="selected === 'shops'" class="place-shop-list"><article v-for="(name, index) in ['Походные припасы','Стальной клинок','Травник']" :key="name"><div><h3>{{ name }}</h3><p>{{ ['Владелец: Следопыт · 12 товаров','Владелец: Кузнец · 8 товаров','Владелец: Лиственница · 15 товаров'][index] }}</p></div><button class="place-button" @click="go('shop' + index)">Войти</button></article></div>
          <div v-else-if="['merchant','shop0','shop1','shop2'].includes(selected)" class="place-products"><div v-for="(name, index) in productRows" :key="name"><span>{{ name }}</span><span>{{ [12,25,8][index] }} монет</span><button class="place-button" @click="notice = 'Покупка — демонстрация. Товар и деньги не меняются.'">Купить</button></div></div>
          <div v-else class="place-action-list"><button v-for="([label, target], index) in serviceActions" :key="index" class="place-button" @click="serviceAction(target)">{{ label }}</button><p v-if="selected === 'hall'">Совет пока недоступен · будущая функция</p><p v-if="selected === 'home'">Личное пространство · следующий уровень вложенной сцены</p></div>
          <p class="place-notice">{{ notice || 'Демо-данные · реальные предметы, деньги и участки не изменяются' }}</p>
        </template>
      </section>
    </div>
  </section>
</template>

<style scoped>
.place-page{overflow:hidden;isolation:isolate;color:var(--col-text-primary);font-family:var(--font-ui)}
.place-art-stage{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;container-type:size;background:var(--col-bg-base)}
.place-backdrop{position:absolute;inset:0;background-size:cover;background-position:center;filter:brightness(.22) saturate(.5)}
.place-art{position:relative;flex:none;width:min(100%,179.27cqh);aspect-ratio:1920/1071;max-height:100%;background-size:100% 100%;background-position:center;filter:brightness(.78)}
.place-hotspot{position:absolute;z-index:1;border:2px solid transparent;background:transparent;padding:0;cursor:pointer;filter:brightness(1.28)}
.place-hotspot:hover,.place-hotspot:focus-visible{border-color:var(--col-accent);background:rgb(var(--theme-accent-rgb) / .12);box-shadow:0 0 18px rgb(var(--theme-accent-rgb) / .3);outline:none}
.place-hotspot-label{position:absolute;transform:translate(-50%,-50%);white-space:nowrap;color:#f6e9cf;background:#10141ae8;padding:6px 11px;font-size:clamp(10px,1.2vw,18px);font-weight:600;text-shadow:0 1px 2px #000;pointer-events:none;opacity:0}
.place-hotspot.is-labelled .place-hotspot-label,.place-hotspot:hover .place-hotspot-label,.place-hotspot:focus-visible .place-hotspot-label{opacity:1}
.place-header,.place-district-nav{position:absolute;z-index:2;left:0;right:0;background:rgb(16 20 26 / .9)}
.place-header{top:0;min-height:84px;padding:11px 25px;display:flex;align-items:center;justify-content:space-between;gap:16px}
.place-header h1{font:clamp(22px,2.2vw,29px)/1.2 var(--font-world);color:#f1e6d2;margin:0}
.place-header p{font-size:14px;color:var(--col-text-dim);margin:4px 0 0}
.place-header-actions{display:flex;gap:8px;flex:none}
.place-button{background:var(--col-bg-surface);color:var(--col-text-world);border:1px solid var(--col-border);border-radius:3px;padding:8px 14px;min-height:36px;cursor:pointer}
.place-button:hover,.place-button:focus-visible{border-color:var(--col-accent);color:var(--col-accent);background:var(--col-bg-surface-light)}
.place-district-nav{top:84px;display:flex;gap:7px;padding:7px 25px;overflow-x:auto;background:rgb(16 20 26 / .83)}
.place-district-nav .place-button{white-space:nowrap;font-size:12px;min-height:30px;padding:4px 10px}
.place-district-nav [aria-current="page"]{border-color:var(--col-accent);color:var(--col-accent)}
.place-label-toggle{margin-left:auto}
.place-header .place-context-hint{font-size:12px;line-height:1.35;color:var(--col-text-dim);margin-top:6px}
.place-modal-backdrop{position:absolute;z-index:5;inset:0;background:rgb(8 11 16 / .74);display:flex;align-items:center;justify-content:center;padding:28px}
.place-modal{width:min(900px,100%);max-height:100%;min-height:360px;overflow:auto;background:var(--col-bg-surface);border:1px solid var(--col-border-strong);box-shadow:0 15px 45px #000b;padding:20px 25px;display:flex;flex-direction:column;scrollbar-width:thin}
.place-modal--construction{width:min(1190px,100%)}
.place-modal-heading{display:flex;justify-content:space-between;gap:15px;border-bottom:1px solid var(--col-border);padding-bottom:12px}
.place-modal-heading h2{font:clamp(21px,2vw,28px)/1.2 var(--font-world);color:var(--col-accent);margin:0}
.place-modal-heading p,.place-muted{color:var(--col-text-dim);font-size:14px;margin:5px 0 0}
.place-modal-controls{display:flex;gap:8px;align-items:flex-start}.place-close{font-size:24px;line-height:20px;padding:4px 10px}
.place-intro{font-size:18px;line-height:1.5;max-width:75ch;margin:20px 0 22px;white-space:pre-line}
.place-action-list{display:flex;flex-direction:column;gap:10px}.place-action-list .place-button{text-align:left;min-height:46px;font-size:16px}
.place-action-list p{color:var(--col-text-dim);font-size:18px}.place-notice{margin:auto 0 0;padding-top:22px;color:var(--col-text-dim);font-size:14px}
.construction-options{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:20px}
.construction-option{min-width:0;padding:14px;background:var(--col-bg-darker);border:1px solid var(--col-border)}
.construction-option h3,.place-shop-list h3{font:21px var(--font-world);color:var(--col-accent);margin:0 0 13px}
.construction-resource{margin:13px 0}.construction-resource>div:first-child{display:flex;justify-content:space-between;gap:8px;font-size:14px;color:var(--col-text-dim)}
.construction-resource strong{font-weight:500;color:var(--col-text-primary)}.construction-track{height:5px;margin:8px 0;background:var(--col-bg-surface-light)}.construction-track i{display:block;height:100%;background:var(--col-accent)}
.construction-buttons{display:flex;gap:6px}.construction-buttons .place-button{flex:1;padding:4px;font-size:12px;min-height:30px}
.construction-bottom{display:flex;justify-content:space-between;align-items:center;gap:12px;color:var(--col-text-dim);font-size:14px;margin-top:14px}
.place-shop-list{display:grid;gap:12px}.place-shop-list article{display:flex;justify-content:space-between;align-items:center;gap:15px;padding:12px 16px;border:1px solid var(--col-border);background:var(--col-bg-darker)}.place-shop-list h3{margin:0}.place-shop-list p{margin:3px 0 0;color:var(--col-text-dim)}
.place-products>div{display:grid;grid-template-columns:1fr auto auto;align-items:center;gap:16px;border-top:1px solid var(--col-border);padding:12px 8px;font-size:17px}.place-products>div>span:nth-child(2){color:var(--col-accent);font-size:15px}
@media(max-width:800px){.place-header{padding:9px 13px}.place-header p{font-size:11px}.place-district-nav{padding:6px 10px}.place-modal-backdrop{padding:12px}.place-modal{padding:15px;min-height:0}.construction-options{grid-template-columns:1fr}.place-hotspot-label{font-size:10px;padding:3px 5px}.place-products>div{gap:7px;font-size:13px}}
</style>
