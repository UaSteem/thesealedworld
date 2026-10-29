import {readInventory} from './data.js';
import {readTheme} from './theme.js';
import {inventoryScene} from './scene.js';

// Adapt the existing inventory to the shared game and persistent HTML shell.
export function createInventoryClientScene({host,renderScale=1}) {
  if(!host)throw new Error('Inventory client requires the shared canvas host');
  const data=readInventory(),theme=readTheme();
  data.mainHandOccupied=Boolean(document.querySelector('.cp-slot[data-slot="main_hand"].is-equipped'));
  return {
    Scene:inventoryScene(data,theme,{viewport:()=>({width:host.clientWidth,height:host.clientHeight}),renderScale}),
    data,
  };
}
