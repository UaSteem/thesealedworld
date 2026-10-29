import catalog from '../../public/ui-static/game/assets/catalog.json';
export const assets={preload(scene,group){for(const asset of catalog.assets.filter(a=>a.group===group))if(!scene.textures.exists(asset.key))scene.load.image(asset.key,asset.url);}};
