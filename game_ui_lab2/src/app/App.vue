<script setup>
import {computed,onMounted,onBeforeUnmount,ref,watch} from 'vue';
import {createNavigation,screens} from './navigation.js';
import {createGameClient} from './gameClient.js';
import {createMockGameGateway} from '../integrations/mockGameGateway.js';
import {createMockMessageGateways} from '../integrations/mockMessageGateways.js';
import {createMockFieldGateway} from '../integrations/mockFieldGateway.js';
import PlayerHud from './PlayerHud.vue';
import GameField from './GameField.vue';
import BriefPage from './BriefPage.vue';
import CharacterPage from '../features/character/CharacterPage.vue';
import QuestPage from '../features/character/QuestPage.vue';
import MessagePanel from '../features/messages/MessagePanel.vue';
import PlacePage from '../features/places/PlacePage.vue';
import DesignableBlock from '../features/designer/DesignableBlock.vue';
import LayoutToolbar from '../features/designer/LayoutToolbar.vue';
import { globalLayoutStore } from '../features/designer/layoutStore.js';
import '../features/designer/designer.css';

const fieldGateway=createMockFieldGateway();
const nav=createNavigation(),{screen,characterTab}=nav;
const model=ref(null),error=ref('');
const client=createGameClient(createMockGameGateway()),messageGateways=createMockMessageGateways();
const fieldScreen=ref('rift');
const layoutStore=globalLayoutStore;
const title=computed(()=>screens.find(([id])=>id===screen.value)?.[1]||'Интерфейс');

watch(screen,id=>{document.body.dataset.gameScreen=id;if(['rift','combat'].includes(id))fieldScreen.value=id;},{immediate:true});
const go=id=>nav.go(id);

function onKeyDown(event){
  if(event.altKey && (event.key==='e' || event.key==='E' || event.key==='у' || event.key==='У')){
    event.preventDefault();
    layoutStore.toggleEditMode();
    return;
  }
  if(!event.defaultPrevented&&event.key==='Escape'&&!event.target.closest('input,textarea,select')){
    if(layoutStore.isEditMode.value && layoutStore.selectedId.value){
      layoutStore.selectedId.value = null;
      return;
    }
    nav.close();
  }
}

function onWindowResize(){
  layoutStore.adaptToViewport(window.innerWidth, window.innerHeight);
}

onMounted(async()=>{
  window.addEventListener('keydown',onKeyDown);
  window.addEventListener('resize',onWindowResize);
  try{model.value=await client.load();}catch(e){error.value=e.message;}
});
onBeforeUnmount(()=>{
  window.removeEventListener('keydown',onKeyDown);
  window.removeEventListener('resize',onWindowResize);
  document.body.removeAttribute('data-game-screen');
});
</script>
<template>
<div class="game-viewport" id="game-viewport"><main class="workspace"><section class="game-frame"><div class="play-column">
<header class="lab-debug-header">
  <div id="lab-debug">
    <strong>Debug</strong>
    <nav aria-label="Страницы лаборатории">
      <button v-for="[id,label] in screens" :key="id" :aria-pressed="screen===id" :disabled="screen==='combat'&&['character','quests','settings'].includes(id)" @click="go(id)">{{label}}</button>
    </nav>
    <button type="button" :aria-pressed="layoutStore.isEditMode.value" title="Переключить визуальный конструктор UI (Alt+E)" @click="layoutStore.toggleEditMode">
      🛠 Конструктор: {{ layoutStore.isEditMode.value ? 'ВКЛ' : 'ВЫКЛ' }}
    </button>
    <div id="combat-view-options" class="projection-switch" v-show="screen==='combat'">
      <label><input id="show-hex-grid" type="checkbox">Сетка</label>
      <label><input id="show-hex-numbers" type="checkbox">Номера гексов</label>
    </div>
  </div>
  <span>{{title}}</span>
  <button v-if="!['rift','combat'].includes(screen)" @click="nav.close">Назад</button>
</header>
<div class="scene-split"><section class="stage-shell" aria-label="Игровая область">
<GameField v-if="model" :screen="fieldScreen" :gateway="fieldGateway" :visible="['rift','combat'].includes(screen)" @error="error=$event"/>

<DesignableBlock id="riftDebug" title="Отладка зума" :autoHeight="true" v-show="screen==='rift'">
  <details class="rift-debug-window" open><summary>Debug · зум</summary><div><label for="rift-min-zoom">Предел отдаления · минимальный масштаб</label><input id="rift-min-zoom" type="range" min="0.01" max="2" step="0.01" value="1"><output id="rift-min-zoom-value">1.00×</output><label class="rift-zoom-unlock"><input id="rift-unlock-zoom-out" type="checkbox">Убрать ограничение отдаления</label><span>Текущий масштаб</span><output id="rift-current-zoom">—</output><small>Масштаб по умолчанию — 1.00×.</small></div></details>
</DesignableBlock>

<template v-if="model">
  <DesignableBlock id="hud" title="HUD игрока" v-show="['rift','combat','arena','districts'].includes(screen)">
    <PlayerHud :character="model.character" :disabled="screen==='combat'" @character="go('character')"/>
  </DesignableBlock>

  <DesignableBlock id="menu" title="Игровое меню" v-show="['rift','arena','districts'].includes(screen)">
    <nav class="player-menu" aria-label="Игровое меню">
      <button @click="go('character')">Персонаж</button>
      <button @click="go('quests')">Квесты</button>
      <button @click="go('settings')">Настройки</button>
    </nav>
  </DesignableBlock>

  <KeepAlive><CharacterPage v-if="screen==='character'" class="client-page" :character="model.character" :inventory="model.inventory" :act="client.action" :tab="characterTab" @tab-change="nav.tab" @close="nav.close"/></KeepAlive>
  <KeepAlive><QuestPage v-if="screen==='quests'" class="client-page" :character="model.character" @close="nav.close"/></KeepAlive>
  <section v-if="screen==='settings'" class="client-page brief-page"><button class="page-close" aria-label="Вернуться в игру" @click="nav.close">×</button><h1>Настройки</h1><p>Состав настроек пока не определён.</p></section>
  <BriefPage v-if="['dialogues','city','loot','death'].includes(screen)" class="client-page" :id="screen"/>
  <KeepAlive><PlacePage v-if="['arena','districts'].includes(screen)" class="client-place" :id="screen" :key="screen" @navigate="go"/></KeepAlive>

  <DesignableBlock id="chat" title="Чат / Лог боя" v-show="['rift','combat','arena','districts'].includes(screen)">
    <MessagePanel :screen="screen" :gateways="messageGateways"/>
  </DesignableBlock>

  <!-- Visual Constructor Floating Toolbar -->
  <LayoutToolbar />
</template>
<p v-if="error" role="alert" class="client-error">{{error}}</p>
<p v-if="!model&&!error" role="status">Загрузка интерфейса…</p>
</section></div></div></section></main></div>
</template>
