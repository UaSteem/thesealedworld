import layout from '../mocks/player-modifier-layout.json' with {type:'json'};
const number=new Intl.NumberFormat('ru-RU',{maximumFractionDigits:4});
// Deliberate presentation allowlist, not DTO enumeration. All attack totals are
// prepared by the mock/server source: no hit/crit/damage formulas in the client.
export function createModifierSheet(values,{actorId='lab-guard',name='Ada Guard',context={attacks:[],has_shield:false}}={}){
 function item(field){
  const value=values[field.key];
  if(!Number.isFinite(value))throw new TypeError(`Missing numeric modifier: ${field.key}`);
  const value_text=field.unit==='percent'?`${number.format(value*100)}%`:number.format(value);
  return {key:field.key,label:field.label,value,value_text};
 }
 const sections=layout.map(group=>({...group,items:group.items.map(item)}));
 const attack=sections.find(group=>group.key==='attack');
 attack.profiles=context.attacks.map(profile=>{
  if(!['main_hand','off_hand'].includes(profile.slot))throw new TypeError('Unknown attack slot');
  return {key:profile.slot,label:profile.slot==='main_hand'?'Основная рука':'Вторая рука',weapon:profile.weapon,items:structuredClone(profile.items)};
 });
 if(context.has_shield)sections.find(group=>group.key==='defense').items.push(
  item({key:'block',label:'Блокирование щитом',unit:'percent'}),
  item({key:'shield_guard_power',label:'Защита щитом',unit:'raw'}),
 );
 return {actor_id:actorId,name,sections,total_count:sections.reduce((count,group)=>count+group.items.length+(group.profiles||[]).reduce((n,profile)=>n+profile.items.length,0),0)};
}
