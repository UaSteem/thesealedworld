<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({ character: { type: Object, required: true } })
const emit = defineEmits(['close'])
const quests = computed(() => props.character?.quests || [])
const selectedIndex = ref(0)
const selected = computed(() => quests.value[Math.min(selectedIndex.value, quests.value.length - 1)] || null)
watch(quests, () => { if (selectedIndex.value >= quests.value.length) selectedIndex.value = 0 })
</script>

<template>
  <section class="quest-page" aria-labelledby="quest-title">
    <header class="quest-heading"><h2 id="quest-title">Квесты</h2><button type="button" aria-label="Вернуться в игру" @click="emit('close')">×</button></header>
    <div class="quest-layout">
      <nav class="quest-list" aria-label="Список квестов">
        <button v-for="(quest, index) in quests" :key="`${quest.title}-${index}`" type="button" :aria-current="selectedIndex === index ? 'true' : undefined" @click="selectedIndex = index">
          <strong>{{ quest.title }}</strong><span>В работе · {{ quest.progress }}</span>
        </button>
        <p v-if="!quests.length" class="no-quests">В этом слепке квестов нет.</p>
      </nav>
      <article class="quest-detail" aria-live="polite">
        <template v-if="selected">
          <h3>{{ selected.title }}</h3><p class="quest-status">В работе · {{ selected.progress }}</p>
          <hr><h4>Описание</h4><p>{{ selected.description }}</p>
          <h4>Диалоги</h4><p class="quest-muted">В этом учебном слепке диалоги квеста не записаны.</p>
        </template>
      </article>
    </div>
  </section>
</template>

<style scoped>
.quest-page { display:flex;flex-direction:column;width:100%;height:100%;min-height:0;min-width:0;overflow:hidden;background:var(--col-bg-base);color:var(--col-text-world);font-family:var(--font-ui); }
.quest-page * { box-sizing:border-box; }
.quest-page button { font:inherit;cursor:pointer;color:var(--col-text-world);background:var(--col-bg-darker);border:1px solid var(--col-border);border-radius:4px; }
.quest-page button:hover,.quest-page button:focus-visible { color:var(--col-accent);border-color:var(--col-accent); }.quest-page button:focus-visible { outline:2px solid var(--col-accent);outline-offset:2px; }
.quest-heading { display:flex;align-items:center;justify-content:space-between;flex:none;height:46px;padding:0 16px;border-bottom:1px solid var(--col-border);background:var(--col-bg-surface); }.quest-heading h2 { margin:0;font:23px var(--font-world); }.quest-heading button { padding:2px 10px;font-size:24px;line-height:1; }
.quest-layout { display:grid;grid-template-columns:min(360px,27%) minmax(0,1fr);gap:20px;flex:1;min-width:0;min-height:0;padding:24px 32px; }.quest-list,.quest-detail { min-width:0;min-height:0;overflow:auto;border:1px solid var(--col-border);background:var(--col-bg-surface); }.quest-list { display:flex;flex-direction:column;gap:10px;padding:20px 12px; }.quest-list button { display:flex;flex-direction:column;align-items:flex-start;justify-content:center;gap:10px;flex:none;min-height:85px;padding:12px 14px;text-align:left;font-size:16px; }.quest-list button[aria-current=true] { color:var(--col-accent);border-color:var(--col-accent);background:var(--col-bg-surface-light); }.quest-list strong { font-weight:400; }.quest-list span,.quest-status,.quest-muted { font-size:13px;color:var(--col-text-dim); }.quest-detail { padding:28px; }.quest-detail h3 { margin:0;font:26px var(--font-world);color:var(--col-accent); }.quest-status { margin:16px 0 24px; }.quest-detail hr { border:0;border-top:1px solid var(--col-border); }.quest-detail h4 { margin:26px 0 18px;font:21px var(--font-world);color:var(--col-accent); }.quest-detail p { line-height:1.6; }.no-quests { color:var(--col-text-dim);font-size:14px; }
@media (max-width:650px) { .quest-heading { height:38px;padding:0 10px; }.quest-heading h2 { font-size:17px; }.quest-layout { grid-template-columns:1fr;grid-template-rows:minmax(140px,35%) minmax(0,1fr);gap:10px;padding:10px; }.quest-list { padding:8px; }.quest-list button { min-height:55px; }.quest-detail { padding:16px; } }
</style>
