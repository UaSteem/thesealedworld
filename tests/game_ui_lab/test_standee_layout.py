"""Checks for the local standee selection and frame-sized hexes."""
import shutil
import subprocess
from pathlib import Path


def test_standee_priority_and_fixed_frame_radius():
    script = r"""
const assert=require('node:assert/strict');
const {prioritize,radiusForFrame,rowsForFrame,containsPoint,gridForFrame}=require(process.argv[1]);
const actors=[{id:'later',actedAgainstViewer:false,deadlineMs:9000},{id:'soon',actedAgainstViewer:false,deadlineMs:1000},{id:'acted',actedAgainstViewer:true,deadlineMs:20000}];
assert.deepEqual(prioritize(actors).map(a=>a.id),['acted','soon','later']);
assert.deepEqual(actors.map(a=>a.id),['later','soon','acted']);
assert.equal(rowsForFrame(435,77),3);assert.equal(rowsForFrame(800,92),5);
assert.equal(radiusForFrame(1449,435),83);
assert.equal(radiusForFrame(2089,410),77);
for(const [width,height] of [[995,435],[1449,435],[2089,878]]){
 const grid=gridForFrame(width,height);
 assert.equal(grid.coreColumns,7);assert.equal(grid.coreRows,6);assert.equal(grid.cells.length,30);
 assert.deepEqual(Array.from({length:6},(_,row)=>grid.cells.filter(c=>c.row===row).length),[5,5,5,5,5,5]);
 assert(grid.cells.find(c=>c.row===0&&c.col===2).x>grid.cells.find(c=>c.row===5&&c.col===2).x);
 assert(grid.bounds.x>=0&&grid.bounds.y>=0);
 assert(grid.bounds.x+grid.bounds.width<=width);
 assert(grid.bounds.y+grid.bounds.height+6<=height);
}
for(const width of [995,1449,2089]){
 const r=radiusForFrame(width);assert(r>=76&&r<=92);
 assert(Math.sqrt(3)*r*5.5<=width-248);
 // Original 64px portrait card and stand remain inside their own projected hex.
 for(const [x,y] of [[-36,-52],[36,-52],[-36,36],[36,36]])assert(containsPoint(r,x,y));
 for(let i=0;i<24;i++){
  const a=i*Math.PI/12;assert(containsPoint(r,45*Math.cos(a),43+12.5*Math.sin(a)));
 }
}
"""
    result = subprocess.run([shutil.which("node"), "-e", script, str(Path("game_ui_lab/experiments/history/static/standee-layout.js").resolve())], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
