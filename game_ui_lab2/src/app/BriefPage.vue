<script setup>
import briefs from '../mocks/page-briefs.json';
const props=defineProps({id:String});
</script>
<template><section class="brief-page"><h1>{{briefs[id]?.title}}</h1><p class="brief-purpose">{{briefs[id]?.purpose}}</p><div class="brief-columns"><article v-for="[title,text] in briefs[id]?.sections" :key="title"><h2>{{title}}</h2><p>{{text}}</p></article></div></section></template>
