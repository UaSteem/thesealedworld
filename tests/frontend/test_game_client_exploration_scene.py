"""Exploration never grants movement from a visual cell or invents encounter options."""
import shutil
import subprocess
from pathlib import Path


def test_exploration_authority_and_layout():
    source = Path('src/frontend/static/js/game/client/exploration-scene.js').resolve()
    script = r"""
const fs=require('fs'),assert=require('node:assert/strict');
(async()=>{
const m=await import('data:text/javascript;base64,'+fs.readFileSync(process.argv[1]).toString('base64'));
const model={loc_id:'here',local_map:{rows:[[{loc_id:'here',is_current:true},{loc_id:'near',is_known:true},{loc_id:'far'}]]},actions:[{id:'opaque-move',kind:'move',params:{target_id:'near'},enabled:true},{id:'service',kind:'service',enabled:true},{id:'blocked',kind:'move',params:{target_id:'far'},enabled:false}]};
const before=JSON.stringify(model);
const joined=m.explorationCells({city_map:{rows:[[{loc_id:'a',tile_url:'/tile',is_current:true}]]},local_map:{rows:[[{loc_id:'a',title:'Cell',corpse_count:0,edges:{n:{state:'locked'}}}]]}})[0];
assert.equal(joined.tile_url,'/tile');assert.equal(joined.title,'Cell');assert.equal(joined.corpse_count,0);assert.equal(joined.edges.n.state,'locked');
assert.ok(m.encounterInformation({bypass_chance_percent:0}).join(' ').includes('0%'));

assert.deepEqual(m.actionsForCell(model,'near').map(a=>a.id),['opaque-move']);
assert.deepEqual(m.actionsForCell(model,'far').map(a=>a.id),['blocked']);
assert.deepEqual(m.actionsForCell(model,'here').map(a=>a.id),['service']);
assert.deepEqual(m.inspectionLines({...model,objects:['Настоящие останки']},{loc_id:'here',corpse_count:0,threat_tier:0,edges:{north:{label:'Север',state:'locked'}}}),['Опасность: 0','Останки: 0','Север · заперт','Настоящие останки']);
assert.ok(m.enemyInformation({intel:{danger_band:'low',vitals:{energy:{label:'Пусто',percent:0},concentration:{label:'Нет',percent:0}}}}).includes('Энергия · Пусто · 0%'));
assert.ok(m.enemyInformation({name:'Реальное имя',description:'Описание',role:'Страж',intel:{vitals:{hp:{label:'Ранен',points:0}}}}).join(' ').includes('Здоровье · Ранен · 0'));
assert.equal(m.explorationCells(model)[0].is_current,true);assert.equal(JSON.stringify(model),before);
assert.deepEqual(m.encounterActions({...model,encounter:{options:[]}}),[]);
assert.deepEqual(m.encounterActions({...model,encounter:{options:[{id:'choice',label:'Wait',action_id:'service'}]}}).map(a=>a.id),['service']);
for(const [w,h] of [[1060,500],[1300,700],[1600,900]]){
 const r=m.contextPlacement({x:w-20,y:h-20,width:20,height:20},w,h,350,400);
 assert.ok(r.x>=8&&r.y>=8&&r.x+r.width<=w-8&&r.y+r.height<=h-8);
}
assert.equal(m.sameOriginAsset('https://evil.invalid/x','https://game.test'),null);
assert.equal(m.sameOriginAsset('/tiles/x.webp','https://game.test'),'https://game.test/tiles/x.webp');
const Scene=m.createExplorationScene({Scene:class{}});const scene=new Scene();scene.present(model,{busy:true});assert.equal(scene.model,model);assert.equal(scene.callbacks.busy,true);
})().catch(e=>{console.error(e);process.exit(1)});
"""
    node = shutil.which('node')
    assert node
    result = subprocess.run([node, '-e', script, str(source)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
