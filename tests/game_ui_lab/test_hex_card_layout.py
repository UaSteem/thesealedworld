"""Flat-top character-card edges and safe full-image rectangle geometry."""
import shutil
import subprocess
from pathlib import Path


def test_hex_resource_edges_and_contained_original_rectangle():
    script = r"""
const assert=require('node:assert/strict'),L=require(process.argv[1]);
for(const r of [29,38,76,94]){
 const v=L.vertices(0,0,r);
 assert(Math.abs(v[4].y-v[5].y)<1e-8);assert(v[4].x<0&&v[5].x>0);
 assert(v[3].x<v[4].x&&v[3].y>v[4].y);assert(v[5].x<v[0].x&&v[5].y<v[0].y);
 for(const [from,to] of [[4,5],[3,4],[5,0]]){
  const b=L.edge(0,0,r,from,to,.35);
  assert(Math.abs(Math.hypot(b.fillEnd.x-b.start.x,b.fillEnd.y-b.start.y)/Math.hypot(b.end.x-b.start.x,b.end.y-b.start.y)-.35)<1e-8);
 }
 const inner=r-9,x=(r-13)*.6,y=(r-13)*.65+3;
 assert(y<=Math.sqrt(3)*(inner-x));
}
for(const [w,h] of [[995,435],[1449,626],[2089,878]]){
 const s=L.slots(w,h);assert(s.hero.radius>s.enemies[0].radius);assert(s.target.x>s.hero.x);assert(s.target.y<s.hero.y);
 const a=L.bounds(s.hero.x,s.hero.y,s.hero.radius),b=L.bounds(s.target.x,s.target.y,s.target.radius);assert(!L.overlaps(a,b));
}
"""
    result = subprocess.run([shutil.which("node"), "-e", script, str(Path("game_ui_lab/static/game/shared/hex-layout.js").resolve())], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
