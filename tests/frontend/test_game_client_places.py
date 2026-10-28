"""Real bridge lifecycle with a minimal transport and timer harness."""
import shutil
import subprocess
from pathlib import Path


def test_places_polling_pauses_exits_and_never_replays_an_uncertain_command():
    script = r"""
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
(async()=>{
const file=process.argv[1],url=s=>'data:text/javascript;base64,'+Buffer.from(s).toString('base64');
const bridgeUrl=url(fs.readFileSync(path.join(path.dirname(file),'scenario.js'),'utf8'));
const source=fs.readFileSync(file,'utf8').replace("import('./places-scene.js'+version)","Promise.resolve({createPlacesScene:()=>class{}})").replace("import('./scenario.js'+version)",`import('${bridgeUrl}')`);
let handler,currentRoot,active=true,overlay=null,next=0,posts=0;
const timers=new Map(),body=new EventTarget();
global.document={body,getElementById:()=>currentRoot};global.Phaser={};global.window={location:{assign:()=>{}}};
global.setTimeout=callback=>{const id=++next;timers.set(id,callback);return id;};global.clearTimeout=id=>timers.delete(id);
const tick=()=>{for(const [id,callback]of [...timers]){timers.delete(id);callback();}};
const event=(name,detail)=>{const value=new Event(name,{cancelable:true});value.detail=detail;return value;};
const payload={char_id:7,kind:'arena',actions:[{id:'poll',enabled:true},{id:'confirm',enabled:true}],poll:{id:'poll',interval_ms:1000}};
const sourceScript={textContent:JSON.stringify(payload)};
const button=new EventTarget();Object.assign(button,{dataset:{gameClientPlacesAction:'poll'},isConnected:true,matches:()=>true,
 click(){posts++;body.dispatchEvent(event('htmx:beforeRequest',{elt:button,xhr:{abort(){}}}));}});
currentRoot={dataset:{gameState:'arena',characterId:'7'},isConnected:true,querySelector:()=>sourceScript,querySelectorAll:()=>[button],contains:()=>true};
const {installPlaces}=await import(url(source));
const client=await installPlaces({register:(domain,value)=>handler=value,refresh(){},inspect:()=>({overlay})});
const scene={sys:{isActive:()=>active},present(model,callbacks){this.model=model;this.callbacks=callbacks;}};
handler.update(scene,currentRoot);assert.equal(timers.size,1);
const originalTimer=[...timers.keys()][0];handler.update(scene,currentRoot);assert.equal([...timers.keys()][0],originalTimer,'redraw must not postpone polling');
overlay='Inventory';active=false;tick();assert.equal(posts,0);assert.equal(timers.size,1);
overlay=null;active=true;tick();assert.equal(posts,1);assert.equal(timers.size,0,'only one pending request');
body.dispatchEvent(event('htmx:afterRequest',{successful:false,xhr:undefined}));
// A matching failed request stops polling and leaves explicit refresh recovery.
let xhr;body.addEventListener('htmx:beforeRequest',e=>xhr=e.detail.xhr);
// The actual first pending XHR is intentionally completed using captured request evidence.
// Restart with a fresh root to test the failure path independently.
client.syncRoot({dataset:{gameState:'scenario'},isConnected:true});
currentRoot={...currentRoot};handler.update(scene,currentRoot);tick();assert.equal(posts,2);
body.dispatchEvent(event('htmx:afterRequest',{successful:false,xhr}));
assert.ok(scene.callbacks.error);assert.equal(timers.size,0);
handler.update(scene,currentRoot);assert.equal(timers.size,0);assert.equal(posts,2);
const incoming=event('htmx:beforeOnLoad',{});button.isConnected=false;button.dispatchEvent(incoming);assert.equal(incoming.defaultPrevented,true);
client.dispose();assert.equal(timers.size,0);assert.equal(payload.actions[1].id,'confirm');
})().catch(error=>{console.error(error);process.exit(1)});
"""
    result = subprocess.run([shutil.which('node'), '-e', script,
                             str(Path('src/frontend/static/js/game/client/places.js').resolve())],
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
