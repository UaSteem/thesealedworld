"""Place hotspots retain real server actions and authored background proportions."""
import shutil
import subprocess
from pathlib import Path


def test_places_authority_and_layout():
    source = Path('src/frontend/static/js/game/client/places-scene.js').resolve()
    script = r"""
const fs=require('fs'),assert=require('node:assert/strict');(async()=>{
const m=await import('data:text/javascript;base64,'+fs.readFileSync(process.argv[1]).toString('base64'));
const model={kind:'arena',screen:'main_menu',actions:[{id:'duel-token',action:'menu_mode',mode:'one_vs_one',enabled:true},{id:'shadow-token',action:'start_shadow',enabled:true},{id:'group-token',action:'menu_mode',mode:'group',enabled:false},{id:'exit-token',action:'leave',enabled:true},{id:'unexpected',action:'real_extra',enabled:true},{id:'poll',hidden_poll:true}]};
assert.equal(m.placeValue(true),'Да');assert.equal(m.placeValue(false),'Нет');assert.equal(m.placeValue(0),'0');
const before=JSON.stringify(model);assert.deepEqual(m.actionsForPlace(model,'duel').map(a=>a.id),['duel-token']);assert.deepEqual(m.actionsForPlace(model,'registrar').map(a=>a.id),['shadow-token']);assert.equal(m.actionsForPlace(model,'main')[0].enabled,false);assert.deepEqual(m.actionsForPlace(model,'other').map(a=>a.id),['unexpected']);assert.equal(JSON.stringify(model),before);
const service={kind:'service',screen:'main',place:'tavern',sections:[{id:'bar',title:'Бар'},{id:'room',title:'Комната'}],npc:{name:'Хозяин',action_id:'talk'},actions:[{id:'open-bar',action:'open_section',section_id:'bar',enabled:true},{id:'talk',action:'talk_npc',enabled:true}]};
assert.deepEqual(m.actionsForPlace(service,'bar').map(a=>a.id),['open-bar']);assert.deepEqual(m.actionsForPlace(service,'npc').map(a=>a.id),['talk']);assert.equal(m.placeHotspots(service).filter(s=>s.id==='bar')[0].label,'Бар');assert.equal(m.placeHotspots(service).some(s=>s.id==='construction'),false);
for(const [w,h]of [[1060,480],[1300,680],[1600,900]]){const r=m.fitPlaceBackground(w,h,1920,1080);assert.ok(r.x>=0&&r.y>=0&&r.x+r.width<=w&&r.y+r.height<=h);assert.ok(Math.abs(r.width/r.height-1920/1080)<1e-8);}
assert.equal(m.placeAssetUrl('https://evil.invalid/image','https://game.test'),null);assert.equal(m.placeAssetUrl(null,'https://game.test'),null);
const Scene=m.createPlacesScene({Scene:class{}}),scene=new Scene();scene.present(model,{busy:true});assert.equal(scene.model,model);assert.equal(scene.callbacks.busy,true);
})().catch(e=>{console.error(e);process.exit(1)});
"""
    node = shutil.which('node')
    assert node
    result = subprocess.run([node, '-e', script, str(source)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
