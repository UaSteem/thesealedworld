<script setup>
defineProps({sheet:{type:Object,required:true}})
</script>
<template>
<div class="modifier-groups">
  <template v-for="(group,index) in sheet.sections" :key="group.key">
    <h4 v-if="index===0 || sheet.sections[index-1].category!==group.category" class="modifier-category">{{group.category==='world'?'Мирные':'Боевые'}}</h4>
    <details class="modifier-group" :open="index===0">
      <summary>{{group.label}}</summary>
      <div v-for="profile in group.profiles || []" :key="profile.key" class="attack-profile">
        <h5>{{profile.label}} <span>{{profile.weapon}}</span></h5>
        <dl><div v-for="item in profile.items" :key="item.key"><dt>{{item.label}}</dt><dd>{{item.value_text}}</dd></div></dl>
      </div>
      <h5 v-if="group.profiles?.length" class="common-bonuses">Общие бонусы атаки</h5>
      <dl><div v-for="item in group.items" :key="item.key"><dt>{{item.label}}</dt><dd>{{item.value_text}}</dd></div></dl>
    </details>
  </template>
</div>
</template>
<style scoped>
.modifier-category {margin:18px 0 8px;color:var(--col-text-world);font:19px var(--font-world);}
.modifier-group {margin:8px 0;border:1px solid var(--col-border);background:var(--col-bg-darker);}
.modifier-group summary {display:flex;align-items:center;gap:10px;padding:10px;cursor:pointer;color:var(--col-accent);font-size:14px;}
.modifier-group summary::before {content:'▸';}.modifier-group[open] summary::before {content:'▾';}
.modifier-group h5 {margin:8px 10px;padding-top:5px;color:var(--col-text-world);font-size:13px;font-weight:500;}
.attack-profile h5 span{display:block;margin-top:4px;color:var(--col-text-dim);font-size:12px;}
.modifier-group dl {display:grid;grid-template-columns:1fr;gap:0;margin:0;padding:0 10px 8px;}
.modifier-group dl>div {display:flex;align-items:baseline;justify-content:space-between;gap:14px;border-top:1px solid var(--col-border);padding:8px 0;}
.modifier-group dt {font-size:12px;line-height:1.4;color:var(--col-text-dim);overflow-wrap:anywhere;}
.modifier-group dd {margin:0;font-size:15px;white-space:nowrap;color:var(--col-text-world);font-variant-numeric:tabular-nums;}
</style>
