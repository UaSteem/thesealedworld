import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const source=await readFile(new URL('./static/game/shared/resize.js',import.meta.url),'utf8');
const {createResizeCoordinator}=await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
let size={width:900,height:400},current={...size},dragging=true,sequence=0;
const callbacks=new Map(),calls=[];
const coordinator=createResizeCoordinator({readSize:()=>size,readCurrent:()=>current,isDragging:()=>dragging,resize:(width,height)=>{current={width,height};calls.push(current);},requestFrame:callback=>{callbacks.set(++sequence,callback);return sequence;},cancelFrame:id=>callbacks.delete(id)});
const flush=()=>{const pending=[...callbacks.values()];callbacks.clear();pending.forEach(callback=>callback());};
for(let height=401;height<430;height++){size={width:900,height};coordinator.schedule();flush();}
assert.equal(calls.length,0,'drag must preserve backing canvas');
dragging=false;coordinator.schedule();coordinator.schedule();flush();
assert.deepEqual(calls,[{width:900,height:429}],'release applies latest dimensions once');
size={width:950,height:450};coordinator.schedule();size={width:1000,height:480};coordinator.schedule();
assert.equal(callbacks.size,1,'window resize burst coalesces');flush();
assert.deepEqual(calls.at(-1),size);
coordinator.schedule();flush();assert.equal(calls.length,2,'unchanged size avoids backing reset');
size={width:0,height:0};coordinator.schedule();flush();assert.equal(calls.length,2,'hidden zero host ignored');
size={width:1100,height:500};coordinator.schedule();assert.equal(callbacks.size,1);coordinator.dispose();assert.equal(callbacks.size,0);coordinator.schedule();flush();assert.equal(calls.length,2,'cleanup prevents late callbacks');
console.log('Inventory resize coordinator: drag/release/coalescing/unchanged/hidden/cleanup pass');
