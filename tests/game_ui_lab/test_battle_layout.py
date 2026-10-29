"""Bounded pure layout checks for the battle stage and its reserved controls."""

import shutil
import subprocess
from pathlib import Path


def test_battle_layout_uses_inclined_axial_terrain_and_native_cards():
    node = shutil.which("node")
    source = Path("game_ui_lab/experiments/history/static/battle-layout.js").resolve()
    script = r"""
const assert=require('node:assert/strict');
const {compute}=require(process.argv[1]);
for(const [w,h] of [[995,325],[995,407],[1449,626],[2089,878]]){
 const b=compute(w,h);
 assert.equal(b.boardHeight+b.hudHeight,h);
 assert.equal(b.center.radius,b.radius*2);
 assert.equal(b.center.scale,1);
 assert(b.center.x>b.hero.x);
 const p=b.point(1,0),o=b.point(0,0);
 assert(Math.abs(p.x-o.x-1.5*b.radius)<.001);
 assert(Math.abs(p.y-o.y-Math.sqrt(3)*b.radius*.65/2)<.001);
 assert(b.cells.length>15);
 assert(b.cardWidth>=56);
 assert(b.visibleLimit>=6 && b.visibleLimit<=10);
 assert(b.center.x-2*b.radius>b.hero.x+2.5*b.radius);
 assert(b.center.y-126>=0);
 for(const p of b.allies){assert(p.y+Math.sqrt(3)*b.radius*.65/2<=b.boardHeight);}
 for(const p of [...b.allies,...b.enemySlots])assert(b.cells.some(c=>c.q===p.q&&c.r===p.r),'Occupied slot lacks terrain');
 const occupied=[...b.allies.slice(0,4),...b.enemySlots];
 for(let i=0;i<occupied.length;i++)for(let j=i+1;j<occupied.length;j++){
  const a=occupied[i],c=occupied[j];assert(Math.abs(a.x-c.x)>=60 || Math.abs(a.y-c.y)>=55,'Native card overlap');
 }
 for(const p of b.cells){
  const dx=Math.abs(p.x-b.center.x),dy=Math.abs(p.y-b.center.y)/.65;
  assert(dx>=3*b.radius-1 || Math.hypot(dx,dy)>=2.9*b.radius);
 }
}
"""
    result = subprocess.run([node, "-e", script, str(source)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


def test_scene_renders_original_material_at_independent_native_sizes():
    source = Path("game_ui_lab/experiments/history/static/scene.js").read_text()
    assert "RiftTerrain.drawGround" in source
    assert "tileSprite" not in source
    assert "ctx.scale" in source
    assert "setScale(p.scale)" not in source
    assert "setResolution" in source
    assert "portrait-" in source


def test_newly_returned_enemy_is_visible_under_a_full_pin_window():
    node = shutil.which("node")
    assert node
    source = Path("game_ui_lab/experiments/history/static/battle-layout.js").resolve()
    script = r"""
const assert=require('node:assert/strict');
const {selectVisible}=require(process.argv[1]);
const actors=Array.from({length:30},(_,i)=>({id:'enemy-'+(i+1),hp:100}));
const pins=new Map();let order=0;
for(let i=0;i<20;i++)pins.set(actors[i].id,++order);
for(let i=0;i<20;i++){
 const returning=actors[i].id;pins.set(returning,++order);
 const selected=actors[25].id;
 const visible=selectVisible(actors,selected,pins);
 assert(visible.shown.some(actor=>actor.id===returning),'New result lost under pin pressure: '+returning);
 assert(!visible.shown.some(actor=>actor.id===selected),'Target duplicated in row');
 assert.equal(visible.shown.length,9);
 assert.equal(visible.hidden,20);
}
"""
    result = subprocess.run([node, "-e", script, str(source)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


def test_enemy_bands_keep_intentions_and_latest_return_visible():
    node = shutil.which("node")
    source = Path("game_ui_lab/experiments/history/static/battle-layout.js").resolve()
    script = r"""
const assert=require('node:assert/strict');
const {selectBands}=require(process.argv[1]);
const actors=Array.from({length:30},(_,i)=>({id:'e'+i,hp:100,intent:i<15?'acted':'waiting'}));
const pins=new Map();let order=0;
for(let i=0;i<20;i++)pins.set(actors[i].id,++order);
for(let i=0;i<20;i++){
 pins.set(actors[i].id,++order);
 const v=selectBands(actors,'e29',pins,5,5,10);
 assert(v.shown.some(a=>a.id===actors[i].id));
 assert(v.shown.filter(a=>a.intent==='acted').length<=5);
 assert(v.shown.filter(a=>a.intent==='waiting').length<=5);
 assert.equal(v.hidden,30-v.shown.length-1);
}
const allWaiting=actors.map(a=>({...a,intent:'waiting'}));
const v=selectBands(allWaiting,'e29',pins,5,5,10);
assert.equal(v.shown.length,5);assert.equal(v.hidden,24);
"""
    result = subprocess.run([node, "-e", script, str(source)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
