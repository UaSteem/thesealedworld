"""Pure inventory layout and server-owned presentation contract checks."""
import shutil
import subprocess
from pathlib import Path


def test_inventory_scene_presentation_helpers():
    script = r"""
const fs=require('fs'),assert=require('node:assert/strict');
(async()=>{
const m=await import('data:text/javascript;base64,'+fs.readFileSync(process.argv[1]).toString('base64'));
const rows=[{item_id:'a',grid_w:2,grid_h:2},{item_id:'b',grid_w:2,grid_h:1},{item_id:'c',grid_w:1,grid_h:2}];
const original=JSON.stringify(rows),packed=m.packInventoryRows(rows,4);
assert.equal(JSON.stringify(rows),original);assert.equal(packed.placements.length,3);
const cells=new Set();for(const p of packed.placements){assert(p.col+p.width<=4);for(let y=0;y<p.height;y++)for(let x=0;x<p.width;x++){const k=(p.row+y)+':'+(p.col+x);assert(!cells.has(k));cells.add(k)}}
assert.equal(m.packInventoryRows([],4).rows,0);assert.throws(()=>m.packInventoryRows(rows,0));
const row={item_id:'real-17',details:{actions:[{action:'equip',label:'Надеть',enabled:true,slot_id:'off_hand'},{action:'drop',label:'Выбросить',enabled:false,reason:'Нет доступа'}]}};
assert.deepEqual(m.inventoryItemActions(row,true),[{action:'equip',label:'Надеть',enabled:true,reason:null,item_id:'real-17',slot_id:'off_hand'},{action:'drop',label:'Выбросить',enabled:false,reason:'Нет доступа',item_id:'real-17',slot_id:null}]);
assert(m.inventoryItemActions(row,false).every(a=>!a.enabled));assert.deepEqual(m.inventoryItemActions({item_id:'x'},true),[]);
const lines=m.inventoryDetailLines({description:'Text',details:[{label:'Урон',value:'8',tone:'positive'}],affixes:[{label:'Сила',value:'+2'}],comparison:[{label:'Броня',value:'-1'}],effects:[{label:'Огонь'}],tags:[{label:'Меч'}],requirements:[{label:'Сила',value:'12',met:false,current:'9'}],meta:[{label:'Вес',value:'2'}]});
for(const text of ['Урон: 8','Сила: +2','Броня: -1','Огонь','Меч','Сила: 12 · сейчас 9','Вес: 2'])assert(lines.some(l=>l.text===text),text);
assert.equal(typeof m.createInventoryScene,'function');
let focused='';const make=(key,disabled=false)=>({dataset:{inventoryControl:key},disabled,hidden:false,focus:()=>{focused=key}});
const itemButton=make('item:real-17'),close=make('inventory-close'),outside={};
const doc={activeElement:itemButton,body:{}};
const host={ownerDocument:doc,contains:e=>[itemButton,close].includes(e),querySelectorAll:()=>[itemButton,close]};
const saved=m.captureInventoryFocus(host);assert.equal(saved.key,'item:real-17');assert.equal(m.restoreInventoryFocus(host,saved),true);assert.equal(focused,'item:real-17');
doc.activeElement=outside;focused='';assert.equal(m.captureInventoryFocus(host).owned,false);assert.equal(m.restoreInventoryFocus(host,{...saved,owned:false}),false);assert.equal(focused,'');
itemButton.disabled=true;doc.activeElement=itemButton;assert.equal(m.restoreInventoryFocus(host,saved),true);assert.equal(focused,'inventory-close');

})().catch(e=>{console.error(e);process.exit(1)});
"""
    result = subprocess.run([shutil.which('node'), '-e', script, str(Path('src/frontend/static/js/game/client/inventory-scene.js').resolve())], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
