<script setup>
import {onMounted,onBeforeUnmount,ref,watch} from 'vue';
const props=defineProps({screen:String,gateway:Object,visible:Boolean});const emit=defineEmits(['error']);const host=ref();let runtime,disposed=false;
onMounted(async()=>{try{const {createField}=await import('../engine/createField.js');runtime=await createField(host.value,props.gateway);if(disposed)runtime.destroy();else {runtime.show(props.screen);runtime.setVisible(props.visible);}}catch(error){emit('error',error.message);}});
watch(()=>props.screen,id=>runtime?.show(id));
watch(()=>props.visible,value=>runtime?.setVisible(value));
onBeforeUnmount(()=>{disposed=true;runtime?.destroy();});
</script>
<template><div id="combat-stage" ref="host" aria-label="Игровое поле"/></template>
