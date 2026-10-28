"""Stale inventory responses and action allowlists are presentation boundaries."""
import shutil
import subprocess
from pathlib import Path


def test_inventory_controller_authoritative_actions_and_stale_close():
    source = Path('src/frontend/static/js/game/client/inventory.js').resolve()
    script = r"""
const fs=require('fs'),assert=require('assert/strict');
(async()=>{
const {createInventoryController}=await import('data:text/javascript;base64,'+fs.readFileSync(process.argv[1]).toString('base64'));
let finish,shown=0,posted=0,closed=0;
const model={char_id:7,can_act:true,visible_rows:[{item_id:'real-1',details:{actions:[{action:'equip',enabled:true,slot_id:'main_hand'}]}}],body_zones:[],weapon_slots:[],accessory_rows:[],quick_slots:[]};
const controller=createInventoryController({load:()=>new Promise(r=>finish=r),send:async(params)=>{posted++;assert.equal(params.item_id,'real-1');assert.equal(params.slot_id,'main_hand');return{inventory:model}},show:()=>shown++,close:()=>closed++,valid:()=>true});
const pending=controller.open();controller.close();finish({inventory:model});await pending;assert.equal(shown,0);assert.equal(closed,1);
const again=controller.open();finish({inventory:model});await again;assert.equal(shown,1);
await controller.action({item_id:'real-1',action:'use'});assert.equal(posted,0);
await controller.action({item_id:'real-1',action:'equip',slot_id:'off_hand'});assert.equal(posted,0);
await controller.action({item_id:'real-1',action:'equip',slot_id:'main_hand'});assert.equal(posted,1);
controller.close();await controller.action({item_id:'real-1',action:'equip',slot_id:'main_hand'});assert.equal(posted,1);
})().catch(e=>{console.error(e);process.exit(1)});
"""
    result = subprocess.run([shutil.which('node'), '-e', script, str(source)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
