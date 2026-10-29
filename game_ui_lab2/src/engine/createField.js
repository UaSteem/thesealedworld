import Phaser from 'phaser';
import {createCombatScene} from './renderers/combat-scene.js';
import {createRiftScene} from './renderers/rift-scene.js';

// Boundary for the inherited visual renderers. Vue owns windows/navigation;
// Phaser owns the single field, camera and visual mock encounter.
export async function createField(host,gateway){
  const dpr=Math.min(2,window.devicePixelRatio||1);
  const scenes=[createRiftScene(),createCombatScene(host,()=>gateway.exchange())];
  const game=new Phaser.Game({type:Phaser.AUTO,parent:host,transparent:true,
    width:Math.max(1,host.clientWidth*dpr),height:Math.max(1,host.clientHeight*dpr),
    scale:{zoom:1/dpr,mode:Phaser.Scale.NONE},scene:scenes,render:{antialias:true}});
  let current='rift';
  const keys={rift:'RiftPreview',combat:'HexCombatWorkspace'};
  let frame;
  const resize=()=>{cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>{
    if(host.clientWidth&&host.clientHeight)game.scale.resize(host.clientWidth*dpr,host.clientHeight*dpr);
  });};
  const observer=new ResizeObserver(resize);observer.observe(host);
  return {
    show(id){
      if(!keys[id])return;
      if(id!==current){game.scene.stop(keys[current]);game.scene.start(keys[id]);current=id;}
      resize();
    },
    setVisible(visible){
      const key=keys[current];
      if(visible&&game.scene.isSleeping(key))game.scene.wake(key);
      else if(!visible&&game.scene.isActive(key))game.scene.sleep(key);
      if(visible)resize();
    },
    destroy(){observer.disconnect();cancelAnimationFrame(frame);game.destroy(true);},
  };
}
