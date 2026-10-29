"""Exercise parent-size changes through the actual lab boot script."""

import shutil
import subprocess
from pathlib import Path


def test_chat_size_changes_resize_the_phaser_surface():
    node = shutil.which("node")
    assert node, "Node.js is required for the scene resize adapter check"
    source = Path("game_ui_lab/experiments/history/static/scene.js").resolve()
    script = r"""
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const host={clientWidth:1000,clientHeight:500},calls=[];
let callback,config;
const window={},document={getElementById:()=>host,documentElement:{}};
const Phaser={Scene:class{},AUTO:0,Scale:{NONE:0,RESIZE:1,CENTER_BOTH:2},Game:class{
 constructor(options){config=options;this.scale={width:options.width,height:options.height,
 refresh:()=>{},resize:(width,height)=>{calls.push([width,height]);this.scale.width=width;this.scale.height=height;}};}
}};
class ResizeObserver{constructor(cb){callback=cb;}observe(target){assert.equal(target,host);}}
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),{
 window,document,Phaser,ResizeObserver,getComputedStyle:()=>({getPropertyValue:()=>'#24323e'})
});
assert.equal(config.scale.mode,Phaser.Scale.NONE);
assert.equal(config.width,1000);assert.equal(config.height,500);
host.clientHeight=740;callback();
assert.deepEqual(calls,[[1000,740]]);
callback();assert.equal(calls.length,1,'Unchanged parent must not resize again');
host.clientWidth=820;host.clientHeight=410;callback();
assert.deepEqual(calls[1],[820,410]);
"""
    result = subprocess.run([node, "-e", script, str(source)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
