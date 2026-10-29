/* Asset groups share one Phaser Texture Manager across the game client's scenes. */
(() => {
  'use strict';
  let catalog=null;
  async function initialize(url){
    const response=await fetch(url);
    if(!response.ok)throw new Error(`Asset catalog: HTTP ${response.status}`);
    const value=await response.json();
    if(value.schema_version!==1||!Array.isArray(value.assets))throw new Error('Unsupported asset catalog');
    const keys=new Set();
    for(const entry of value.assets){
      if(entry.type!=='image'||!entry.key||!entry.group||!entry.url||keys.has(entry.key))throw new Error('Invalid asset entry');
      keys.add(entry.key);
    }
    catalog=value;
    return catalog;
  }
  function preload(scene,group){
    if(!catalog)throw new Error('Asset catalog must be initialized before starting scenes');
    const entries=catalog.assets.filter(entry=>entry.group===group);
    if(!entries.length)throw new Error(`Unknown asset group: ${group}`);
    for(const entry of entries)if(!scene.textures.exists(entry.key))scene.load.image(entry.key,entry.url);
  }
  window.GameClientAssets={initialize,preload,inspect:()=>catalog};
})();
