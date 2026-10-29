import assert from 'node:assert/strict';
import test from 'node:test';
import {createMockGameGateway} from './mockGameGateway.js';
import {createModifierSheet} from './modifierSheet.js';
test('sword and shield shows one weapon attack, shield defense, and no technical DTO groups',async()=>{
 const c=await createMockGameGateway().loadCharacter();const sheet=c.modifier_sheet;
 assert.deepEqual(sheet.sections.find(s=>s.key==='attack').profiles.map(p=>p.key),['main_hand']);
 const keys=sheet.sections.flatMap(s=>s.items.map(i=>i.key));
 assert.ok(keys.includes('shield_guard_power'));assert.ok(keys.includes('trade_bonus'));
 assert.ok(keys.every(k=>!k.startsWith('item_')&&!k.includes('_cap')&&!k.includes('_raw')&&!k.includes('_mastery')));
 assert.ok(!sheet.sections.some(s=>['item','main_hand','off_hand','caps'].includes(s.key)));
 const attack=sheet.sections.find(s=>s.key==='attack');assert.deepEqual(attack.profiles[0].items.map(i=>i.label),['Урон','Точность','Критический удар']);
 assert.ok(attack.items.some(i=>i.key==='crit_chance'&&i.value===0));
});
test('second weapon appears only when its attack profile is supplied; unequipped shield stats disappear',async()=>{
 const c=await createMockGameGateway().loadCharacter();
 const context={attacks:[...c.modifier_context.attacks,{slot:'off_hand',weapon:'Кинжал',items:[{key:'off_hand_damage',label:'Урон',value:3,value_text:'2–3'}]}],has_shield:false};
 const sheet=createModifierSheet(c.modifier_values,{context});
 assert.deepEqual(sheet.sections.find(s=>s.key==='attack').profiles.map(p=>p.key),['main_hand','off_hand']);
 assert.ok(!sheet.sections.find(s=>s.key==='defense').items.some(i=>['block','shield_guard_power'].includes(i.key)));
 const noWeapon=createModifierSheet(c.modifier_values,{context:{attacks:[],has_shield:false}});
 assert.equal(noWeapon.sections.find(s=>s.key==='attack').profiles.length,0);
});
test('flat damage bonus is formatted as a number, unrelated DTO fields are not required',async()=>{
 const c=await createMockGameGateway().loadCharacter();const values={...c.modifier_values,physical_damage_bonus:5};
 const sheet=createModifierSheet(values,{context:c.modifier_context});
 assert.equal(sheet.sections.find(s=>s.key==='attack').items.find(i=>i.key==='physical_damage_bonus').value_text,'5');
 assert.throws(()=>createModifierSheet({}),/Missing numeric modifier/);
});
