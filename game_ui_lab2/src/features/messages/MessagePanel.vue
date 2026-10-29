<script setup>
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import { CHAT_CHANNELS } from '../../integrations/mockChatGateway.js';
import { createMockMessageGateways } from '../../integrations/mockMessageGateways.js';

const props = defineProps({
  screen: { type: String, required: true },
  gateways: { type: Object, default: null },
});

const adapters = props.gateways ?? createMockMessageGateways();
const selected = ref('world');
const collapsed = ref(false);
const draft = ref('');
const chatRows = ref([]);
const combatRows = ref([]);
const logElement = ref(null);
const visible = ['rift', 'combat', 'arena', 'districts'];
let stopChat = null;
let stopCombat = null;

function refreshChat() {
  if (selected.value === 'combat') return;
  chatRows.value = adapters.chat.getMessages(selected.value);
  scrollToEnd();
}

function scrollToEnd() {
  nextTick(() => {
    if (logElement.value) logElement.value.scrollTop = logElement.value.scrollHeight;
  });
}

function choose(channel) {
  if (channel === 'combat' && props.screen !== 'combat') return;
  selected.value = channel;
  refreshChat();
  scrollToEnd();
}

function send() {
  if (selected.value === 'combat' || props.screen === 'combat' && selected.value === 'combat') return;
  const content = draft.value.trim();
  if (!content) return;
  adapters.chat.send(selected.value, content);
  draft.value = '';
}

function syncCombat(screen) {
  stopCombat?.();
  stopCombat = null;
  combatRows.value = [];
  if (screen === 'combat') {
    stopCombat = adapters.combat.subscribe((event) => {
      combatRows.value = [...combatRows.value, event];
      if (selected.value === 'combat') scrollToEnd();
    });
  } else if (selected.value === 'combat') {
    choose('world');
  }
}

onMounted(() => {
  refreshChat();
  stopChat = adapters.chat.subscribe(({ channel, message }) => {
    if (channel === selected.value) {
      chatRows.value = [...chatRows.value, message];
      scrollToEnd();
    }
  });
  syncCombat(props.screen);
});

watch(() => props.screen, syncCombat);
onUnmounted(() => {
  stopChat?.();
  stopCombat?.();
});
</script>

<template>
  <section v-if="visible.includes(screen)" id="chat" class="chat" :class="{ 'is-collapsed': collapsed }" aria-label="Сообщения и журнал боя">
    <header class="chat-heading">
      <div class="chat-tabs" role="group" aria-label="Вкладки сообщений">
        <button v-for="channel in CHAT_CHANNELS" :key="channel.id" type="button" :class="{ 'is-active': selected === channel.id }" :aria-pressed="selected === channel.id" @click="choose(channel.id)">{{ channel.label }}</button>
        <button v-if="screen === 'combat'" type="button" :class="{ 'is-active': selected === 'combat' }" :aria-pressed="selected === 'combat'" @click="choose('combat')">Бой</button>
      </div>
      <button id="chat-toggle" type="button" :aria-expanded="!collapsed" :aria-label="collapsed ? 'Развернуть чат' : 'Свернуть чат'" :title="collapsed ? 'Развернуть чат' : 'Свернуть чат'" @click="collapsed = !collapsed">{{ collapsed ? '⌃' : '⌄' }}</button>
    </header>
    <div v-if="!collapsed" class="chat-content">
      <div ref="logElement" class="chat-messages" :class="{ 'combat-log': selected === 'combat' }" role="log" :aria-label="selected === 'combat' ? 'Моковый журнал текущего боя' : 'Сообщения чата'" aria-live="polite">
        <template v-if="selected === 'combat'">
          <p v-for="event in combatRows" :key="event.id"><b>{{ event.round }}</b><span>{{ event.text }}</span></p>
        </template>
        <template v-else>
          <p v-for="message in chatRows" :key="message.id"><time>{{ message.time }}</time><b>{{ message.author }}</b><span>{{ message.text }}</span></p>
        </template>
      </div>
      <form v-if="selected !== 'combat'" @submit.prevent="send">
        <label class="sr-only" for="chat-input">Тестовое сообщение, только в этой вкладке</label>
        <input id="chat-input" v-model="draft" autocomplete="off" maxlength="300" placeholder="Локальное сообщение…">
        <button type="submit" aria-label="Добавить тестовое сообщение">↵</button>
      </form>
    </div>
  </section>
</template>

<style scoped>
.chat { position:absolute;left:14px;bottom:14px;width:580px;max-width:calc(100% - 28px);height:300px;max-height:45%;z-index:5;display:flex;flex-direction:column;min-height:0;overflow:hidden;color:var(--col-text-world);background:transparent;border:1px solid transparent;border-radius:5px;transition:background .15s,border-color .15s; }
.chat:hover,.chat:focus-within { background:color-mix(in srgb,var(--col-bg-surface) 88%,transparent);border-color:var(--col-border); }
.chat-heading { order:2;display:flex;align-items:flex-start;gap:8px;height:30px;min-height:30px;padding:0 10px;opacity:.45;transition:opacity .15s; }
.chat:hover .chat-heading,.chat:focus-within .chat-heading { opacity:1; }
.chat-tabs { display:flex;align-items:flex-start;gap:3px;min-width:0;max-width:calc(100% - 36px);overflow-x:auto;scrollbar-width:thin; }
.chat-heading button { position:relative;flex:none;color:inherit;font-size:11px;white-space:nowrap;cursor:pointer; }
.chat-tabs button { min-width:0;height:26px;margin-top:3px;padding:0 10px;border:1px solid var(--col-border);border-top:0;border-radius:0 0 6px 6px;background:color-mix(in srgb,var(--col-bg-darker) 75%,transparent); }
.chat-tabs button.is-active { height:30px;margin-top:-1px;padding-top:1px;color:var(--col-accent);border-color:var(--col-accent);background:var(--col-bg-darker);z-index:1; }
.chat-tabs button.is-active::after { content:'';position:absolute;left:9px;right:9px;bottom:1px;height:2px;background:var(--col-accent); }
#chat-toggle { margin-left:auto;width:28px;height:26px;border:1px solid var(--col-border);border-top:0;border-radius:0 0 5px 5px;background:color-mix(in srgb,var(--col-bg-darker) 75%,transparent);font-size:16px; }
.chat-content { display:flex;flex:1;flex-direction:column;min-height:0;padding:4px 10px 0; }
.chat-messages { flex:1;min-height:0;overflow:auto;font-size:15px;line-height:20px;text-shadow:0 1px 3px #000;mask-image:linear-gradient(to bottom,transparent,black 95%); }
.chat:hover .chat-messages,.chat:focus-within .chat-messages { mask-image:none; }
.chat-messages p { display:flex;gap:12px;margin:2px 0;overflow-wrap:anywhere; }
.chat-messages time { flex:none;padding-top:4px;color:var(--col-text-dim);font-size:10px; }
.chat-messages b { flex:none;color:var(--col-accent);font-weight:500; }
.combat-log b { min-width:65px; }
form { display:flex;gap:5px;margin-top:5px; }
input { flex:1;min-width:0;padding:6px 8px;color:inherit;background:color-mix(in srgb,var(--col-bg-darker) 65%,transparent);border:1px solid var(--col-border);border-radius:4px 4px 0 0; }
form button { padding:0 12px;color:rgb(var(--theme-action-rgb));background:var(--col-bg-darker);border:1px solid var(--col-border);border-radius:4px;cursor:pointer; }
button:focus-visible,input:focus-visible { outline:2px solid var(--col-accent);outline-offset:2px; }
.sr-only { position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0; }
.is-collapsed { height:32px; }
@media (max-width:1400px) { .chat { width:440px;height:240px; } }
@media (max-width:700px) { .chat { left:6px;right:6px;bottom:6px;width:auto;max-width:none;height:190px;max-height:35%; } .chat-messages { font-size:13px;line-height:18px; } form { margin-top:4px;gap:4px; } input { padding:5px 6px;font-size:12px; } }
</style>
