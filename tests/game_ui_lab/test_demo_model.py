"""Exercise the isolated demo model in Node, without a Phaser renderer."""

import shutil
import subprocess
from pathlib import Path


def test_demo_events_are_actor_and_session_scoped():
    node = shutil.which("node")
    assert node, "Node.js is required for the demo state checks"
    source = Path("game_ui_lab/experiments/history/static/demo-model.js").resolve()
    script = r"""
const assert=require('node:assert/strict');
const {Model,TOKEN_TYPES,FEINTS,ABILITIES}=require(process.argv[1]);
const model=new Model({seed:7,enemyCount:20,allyCount:4});
const initial=model.snapshot();
assert.equal(TOKEN_TYPES.length,9);assert.equal(Object.keys(initial.tokens).length,9);
assert.equal(new Set(initial.actors.map(a=>a.id)).size,24);
const firstFront=initial.actors.filter(a=>a.side==='ally'&&a.intent==='acted').map(a=>a.id);
assert(firstFront.length>0);
assert(model.selectTarget('enemy-2'));
const secondFront=model.snapshot().actors.filter(a=>a.side==='ally'&&a.intent==='acted').map(a=>a.id);
assert(secondFront.length>0);
assert.notDeepEqual(secondFront,firstFront,'Ally front row must describe the selected opponent');
assert(model.selectTarget(initial.selectedId));
const action=model.attack(),next=model.snapshot().selectedId;
assert.notEqual(action.previousTargetId,next,'Attack must immediately select a new enemy');
const previousHp=initial.actors.find(a=>a.id===action.event.actorId).hp;
assert.equal(model.applyEvent({...action.event,actorId:next}),false);
assert.equal(model.applyEvent(action.event),true);
let state=model.snapshot();
assert.equal(state.selectedId,next,'Delayed result must not steal the new target');
assert.equal(state.actors.find(a=>a.id===action.event.actorId).hp,
 Math.min(previousHp,Math.max(0,previousHp-action.event.damage+action.event.healing)));
assert.equal(model.applyEvent(action.event),false,'Duplicate must not apply twice');
const pending=model.attack();const oldSession=state.sessionId;
model.reset({seed:7,enemyCount:20});
assert.notEqual(model.snapshot().sessionId,oldSession);
assert.equal(model.applyEvent(pending.event),false,'Old-session result must be ignored');
assert.equal(model.selectTarget('missing'),false);
assert.equal(model.selectTarget(model.snapshot().actors.find(a=>a.side==='ally').id),false);
const clone=model.snapshot();clone.actors[0].hp=-999;clone.tokens.hit=-999;
assert(model.snapshot().actors[0].hp>0);assert(model.snapshot().tokens.hit>=0);
const events=[];for(let i=0;i<40;i++){const a=model.attack();assert(a);events.push(a.event);}
for(const event of events.reverse())assert(model.applyEvent(event));
assert.equal(model.applyEvent(events[0]),false);
for(const actor of model.snapshot().actors){
 assert(actor.hp>=0&&actor.hp<=actor.maxHp);
 assert(actor.en>=0&&actor.en<=actor.maxEn);
 assert(actor.conc>=0&&actor.conc<=actor.maxConc);
}
assert.equal(FEINTS.length,3);assert.equal(ABILITIES.length,4);
model.reset({seed:7});
const before=model.snapshot();
const ability=model.useAbility('energy-strike');assert(ability);
assert(model.snapshot().actors.find(a=>a.side==='ally').en<before.actors.find(a=>a.side==='ally').en);
assert(model.applyEvent(ability.event));
assert.equal(model.useAbility('missing'),null);
const bounded=new Model();let count=0;while(bounded.attack())count++;
assert(count>0&&count<=128,'Pending outcomes must be bounded');
bounded.reset();assert(bounded.attack(),'New session must clear pending capacity');
"""
    result = subprocess.run([node, "-e", script, str(source)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
