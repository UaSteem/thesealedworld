"""Native HUD anchors use the same transform as their hit regions."""
import shutil
import subprocess
from pathlib import Path


def test_generated_hud_anchor_transform_and_regions():
    script = r"""
const assert=require('node:assert/strict');
const L=require(process.argv[1]);
assert.equal(L.SIZE.width,1942);assert.equal(L.SIZE.height,809);
assert.equal(L.tokens.length,9);assert.equal(L.feints.length,3);assert.equal(L.abilities.length,8);
for(const [w,h] of [[995,435],[1449,626],[2089,878]]){
 const layout=L.compute(w,h);
 assert(layout.x>=0&&layout.y>=0&&layout.x+layout.width<=w&&layout.y+layout.height<=h);
 for(const region of [...L.tokens,...L.abilities,L.attack,...L.feints.map(f=>({...f,width:480,height:100}))]){
  const p=L.world(region,layout);
  assert.equal(p.x,layout.x+region.x*layout.scale);
  assert.equal(p.y,layout.y+region.y*layout.scale);
  assert(p.x-p.width/2>=0&&p.x+p.width/2<=w);
  assert(p.y-p.height/2>=0&&p.y+p.height/2<=h);
 }
}
assert.deepEqual(L.feints.map(f=>f.cost),[{hit:3},{hit:3,parry:2},{hit:3,dodge:2}]);
"""
    result = subprocess.run([shutil.which("node"), "-e", script, str(Path("game_ui_lab/experiments/history/static/hud-layout.js").resolve())], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
