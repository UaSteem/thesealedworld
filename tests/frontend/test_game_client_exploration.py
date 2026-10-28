"""Action bridge for Exploration reuses only current server-advertised commands."""
import shutil
import subprocess
from pathlib import Path


def test_exploration_action_availability_and_cooldown():
    script = r"""
const fs=require('fs'),assert=require('node:assert/strict');
(async()=>{
const {explorationBridgeModel,actionEnabled}=await import('data:text/javascript;base64,'+fs.readFileSync(process.argv[1]).toString('base64'));
const payload={char_id:7,loc_id:'52_52',actions:[{id:'m',kind:'move',enabled:true},{id:'s',kind:'service',enabled:true},{id:'x',kind:'interact',enabled:false}]};
assert.equal(actionEnabled(payload.actions[0],true),false);assert.equal(actionEnabled(payload.actions[1],true),true);assert.equal(actionEnabled(payload.actions[2],false),false);
assert.deepEqual(explorationBridgeModel(payload,'snapshot',true).buttons,[{action_id:'s'}]);
assert.equal(explorationBridgeModel(payload,'snapshot',false).node_key,'snapshot');
assert.equal(payload.actions[0].enabled,true);
})().catch(e=>{console.error(e);process.exit(1)});
"""
    result = subprocess.run([shutil.which('node'), '-e', script,
                             str(Path('src/frontend/static/js/game/client/exploration.js').resolve())], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_installed_exploration_bridge_resumes_cooldown_after_overlay_and_reentry():
    script = r"""
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
(async()=>{
const file=process.argv[1];
const moduleUrl=source=>'data:text/javascript;base64,'+Buffer.from(source).toString('base64');
const bridgeUrl=moduleUrl(fs.readFileSync(path.join(path.dirname(file),'scenario.js'),'utf8'));
// Keep installExploration and createChoiceBridge intact; only replace the Phaser
// scene factory and resolve its sibling bridge import for this Node harness.
const original=fs.readFileSync(file,'utf8');
assert.ok(original.includes("import('./exploration-scene.js'+version)"));
assert.ok(original.includes("import('./scenario.js'+version)"));
const source=original
 .replace("import('./exploration-scene.js'+version)","Promise.resolve({createExplorationScene:()=>class{}})")
 .replace("import('./scenario.js'+version)",`import('${bridgeUrl}')`);
let cooling=true,active=true,handler,nextTimer=0;
const timers=new Map(),presentations=[];
global.window={ExplorationMoveCooldown:{isActive:()=>cooling}};
global.Phaser={};
global.document={body:new EventTarget()};
global.setInterval=callback=>{const id=++nextTimer;timers.set(id,callback);return id;};
global.clearInterval=id=>timers.delete(id);
const tick=()=>{for(const callback of [...timers.values()])callback();};
const {installExploration}=await import(moduleUrl(source));
const client=await installExploration({register:(domain,value)=>{
 assert.equal(domain,'exploration');handler=value;
}});
const payload={char_id:7,loc_id:'52_52',actions:[
 {id:'move',kind:'move',enabled:true},{id:'service',kind:'service',enabled:true},
]};
const script={textContent:JSON.stringify(payload)};
const makeRoot=()=>({dataset:{gameState:'exploration',characterId:'7'},isConnected:true,
 querySelector:()=>script});
const root=makeRoot();
const scene={sys:{isActive:()=>active},present(model){
 this.model=model;presentations.push(model.actions.map(action=>action.enabled));
}};
handler.update(scene,root);
assert.deepEqual(scene.model.actions.map(a=>a.enabled),[false,true]);
assert.equal(timers.size,1);
// The cooldown expires while the underlying scene sleeps behind Inventory.
active=false;cooling=false;tick();
assert.equal(timers.size,0);
assert.equal(presentations.length,1,'sleep must not render the underlying scene');
active=true;handler.update(scene,root);
assert.deepEqual(scene.model.actions.map(a=>a.enabled),[true,true]);
// A domain exit cancels its timer; returning during a cooldown must resume it.
cooling=true;handler.update(scene,root);
assert.equal(timers.size,1);
client.syncRoot({dataset:{gameState:'scenario'},isConnected:true});
assert.equal(timers.size,0);
handler.update(scene,makeRoot());
assert.equal(timers.size,1,'reentry must restart cooldown observation');
assert.equal(scene.model.actions[0].enabled,false);
cooling=false;tick();
assert.equal(scene.model.actions[0].enabled,true);
assert.equal(timers.size,0);
assert.equal(payload.actions[0].enabled,true,'server payload must remain unchanged');
client.dispose();
assert.equal(timers.size,0);
})().catch(error=>{console.error(error);process.exit(1)});
"""
    node = shutil.which('node')
    assert node
    result = subprocess.run(
        [node, '-e', script, str(Path('src/frontend/static/js/game/client/exploration.js').resolve())],
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, result.stderr
