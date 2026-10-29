import Phaser from 'phaser';
import RiftTerrain from './rift-renderer/terrain-pointy.js';
import RiftFlowerTerrain from './rift-renderer/flower-terrain.js';
/* Fixed map from Rift Lab. Reuses its terrain renderer; no gameplay or generation. */
export function createRiftScene(){
  class RiftPreview extends Phaser.Scene {
    constructor(){super('RiftPreview');}
    preload(){
      this.load.json('rift-preview-layout','/ui-data/rift-preview.json');
      RiftFlowerTerrain.preload(this);
    }
    create(){
      this.layout=this.cache.json.get('rift-preview-layout');
      this.point=(q,r)=>RiftTerrain.point(q,r);
      this.terrain=new RiftFlowerTerrain.Terrain(this);
      this.cameras.main.setBackgroundColor('#10141a');
      const zoomInput=document.getElementById('rift-min-zoom'),zoomValue=document.getElementById('rift-min-zoom-value');
      const unlock=document.getElementById('rift-unlock-zoom-out');
      const limit=()=>unlock.checked?.0001:Number(zoomInput.value);
      const apply=value=>this.cameras.main.setZoom(Phaser.Math.Clamp(value,limit(),2));
      this.fit=()=>{
        const c=this.cameras.main;
        c.setViewport(0,0,this.scale.width,this.scale.height);
        if(!this.initialView){
          const b=this.terrain.bounds;c.centerOn((b.left+b.right)/2,(b.top+b.bottom)/2);
          apply(Number(zoomInput.value));this.initialView=true;
        }
      };
      this.scale.on('resize',this.fit);this.events.on('wake',this.fit);
      const updateLimit=()=>{zoomValue.textContent=Number(zoomInput.value).toFixed(2)+'×';apply(Number(zoomInput.value));};
      const updateUnlock=()=>{if(!unlock.checked)apply(this.cameras.main.zoom);};
      zoomInput.addEventListener('input',updateLimit);unlock.addEventListener('change',updateUnlock);
      const status=()=>{
        if(this.cameras.main.zoom<limit())apply(this.cameras.main.zoom);
        const current=document.getElementById('rift-current-zoom'),value=this.cameras.main.zoom.toFixed(3)+'×';
        if(current.textContent!==value)current.textContent=value;
      };
      this.events.on('preupdate',status);
      this.events.once('shutdown',()=>{
        this.scale.off('resize',this.fit);this.events.off('wake',this.fit);this.events.off('preupdate',status);
        zoomInput.removeEventListener('input',updateLimit);unlock.removeEventListener('change',updateUnlock);this.terrain.destroy();this.initialView=false;
      });
      this.fit();updateLimit();
      this.input.on('wheel',(_p,_o,_dx,dy)=>apply(this.cameras.main.zoom*(dy>0?.9:1.1)));
      this.input.on('pointermove',p=>{if(p.isDown){const c=this.cameras.main;c.scrollX-=(p.x-p.prevPosition.x)/c.zoom;c.scrollY-=(p.y-p.prevPosition.y)/c.zoom;}});
      this.game.canvas.setAttribute('aria-label','Карта рифта: примерка интерфейса');
    }
  }
  return RiftPreview;
}
