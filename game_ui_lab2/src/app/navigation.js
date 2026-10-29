import {ref} from 'vue';
export const screens=[['rift','Карта рифта'],['combat','Бой'],['character','Персонаж'],['quests','Квесты'],['settings','Настройки'],['dialogues','Диалоги'],['arena','Арена'],['districts','Кварталы'],['city','Город'],['loot','Добыча'],['death','Смерть']];
export function createNavigation(){
 const screen=ref('rift'),characterTab=ref('attributes');let origin='rift';
 const management=new Set(['character','quests','settings']);
 function go(id){
  if(screen.value==='combat'&&management.has(id))return false;
  if(management.has(id)&&!management.has(screen.value))origin=screen.value;
  screen.value=id;return true;
 }
 function close(){if(screen.value==='combat')return false;screen.value=management.has(screen.value)?origin:'rift';}
 function tab(id){characterTab.value=id;}
 return {screen,characterTab,go,close,tab};
}
