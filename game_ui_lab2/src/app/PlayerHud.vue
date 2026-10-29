<script setup>
import {computed} from 'vue';
const props=defineProps({character:Object,disabled:Boolean});
const emit=defineEmits(['character']);
const bars=computed(()=>[['HP',props.character.hp,props.character.max_hp],['EN',props.character.energy,props.character.max_energy],['STA',props.character.stamina,props.character.max_stamina]]);
</script>
<template>
<button class="player-hud" :disabled="disabled" aria-label="Открыть персонажа" @click="emit('character')">
<img class="player-hud-avatar" :src="character.avatar_url" alt="">
<span class="player-hud-info"><strong>{{character.name}}</strong>
<span v-for="[key,value,max] in bars" :key="key" class="player-hud-resource"><b>{{key}}</b><span class="player-hud-track"><i :style="{width:(value/max*100)+'%'}"/></span><small>{{value}}/{{max}}</small></span>
</span></button>
</template>
