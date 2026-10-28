"""Scenario choice bridge never invents actions or replays uncertain POSTs."""
import shutil
import subprocess
from pathlib import Path


def test_scenario_choice_bridge_lock_and_current_actions():
    script = r"""
const fs=require('fs'),assert=require('node:assert/strict');
(async()=>{
const {createChoiceBridge,resolveScenarioCatalog}=await import('data:text/javascript;base64,'+fs.readFileSync(process.argv[1]).toString('base64'));
let payload={node_key:'n1',buttons:[{action_id:'exact-action'}]},calls=0,state;
const bridge=createChoiceBridge({read:()=>payload,activate:id=>{assert.equal(id,'exact-action');calls++;return true},render:s=>state=s});
bridge.update(payload);assert.equal(bridge.choose('fake'),false);assert.equal(calls,0);
assert.equal(bridge.choose('exact-action'),true);assert.equal(calls,1);assert.equal(state.busy,true);
assert.equal(bridge.choose('exact-action'),false);assert.equal(calls,1);
bridge.finish(false);assert.ok(state.error);assert.equal(bridge.choose('exact-action'),false);
payload={node_key:'n2',buttons:[{action_id:'exact-action'}]};bridge.update(payload);assert.equal(state.error,null);
payload={node_key:'n3',buttons:[]};assert.equal(bridge.choose('exact-action'),false);assert.equal(calls,1);
bridge.reset();assert.equal(bridge.choose('exact-action'),false);
const raw={extra_data:{right_panel:{widgets:[{items:[{label:'skill_raw',catalog:'skills',catalog_key:'skill_raw',value:0,percent:17}]}]}}};
const resolved=resolveScenarioCatalog(raw,()=>({title:'Настоящее название'}));
assert.equal(resolved.extra_data.right_panel.widgets[0].items[0].label,'Настоящее название');
assert.equal(resolved.extra_data.right_panel.widgets[0].items[0].percent,17);assert.equal(raw.extra_data.right_panel.widgets[0].items[0].label,'skill_raw');

})().catch(e=>{console.error(e);process.exit(1)});
"""
    result = subprocess.run([shutil.which('node'), '-e', script,
                             str(Path('src/frontend/static/js/game/client/scenario.js').resolve())], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
