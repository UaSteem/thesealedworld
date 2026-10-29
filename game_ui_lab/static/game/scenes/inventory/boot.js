import {createResizeCoordinator} from '../../shared/resize.js';
import {readTheme} from './theme.js';
import {readInventory} from './data.js';
import {inventoryScene} from './scene.js';
const currentBag=document.querySelector('.cp-bag button');
const power=document.querySelector('.cp-power');
if(power){
  const belt=document.createElement('section');
  belt.className='inventory-character-belt';
  belt.setAttribute('aria-label','Пояс: быстрый доступ');
  const label=document.createElement('span');label.className='inventory-belt-label';label.textContent='Пояс';belt.append(label);
  const slots=document.createElement('div');slots.className='inventory-belt-slots';
  for(let index=1;index<=8;index++){
    const slot=document.createElement('button');slot.type='button';slot.disabled=true;
    slot.setAttribute('aria-label',`Пояс, ячейка ${index}: пусто`);
    slot.title='Макет быстрого доступа';slot.textContent=String(index);slots.append(slot);
  }
  belt.append(slots);power.before(belt);
}
if(currentBag){currentBag.textContent='Инвентарь · открыт';currentBag.title='Текущий экран: локальный макет инвентаря';currentBag.setAttribute('aria-current','page');}
await document.fonts.ready;
const host=document.getElementById('inventory-stage');
const resizeOverlay=document.createElement('div');resizeOverlay.className='inventory-resize-overlay';
resizeOverlay.setAttribute('role','status');resizeOverlay.setAttribute('aria-live','polite');
const resizeIcon=document.createElement('img');resizeIcon.src='/static/images/ui/inventory-icons/items.svg';resizeIcon.alt='';resizeIcon.width=64;resizeIcon.height=64;
const resizeLabel=document.createElement('strong');resizeLabel.textContent='Подстраиваем размер…';
const resizeHint=document.createElement('span');resizeHint.textContent='Отпустите границу, чтобы продолжить';
resizeOverlay.append(resizeIcon,resizeLabel,resizeHint);host.append(resizeOverlay);
host.dataset.inventoryOpen='true';
const theme=readTheme(),data=readInventory();
data.mainHandOccupied=Boolean(document.querySelector('.cp-slot[data-slot="main_hand"].is-equipped'));
const game=new Phaser.Game({type:Phaser.AUTO,parent:host,width:host.clientWidth,height:host.clientHeight,backgroundColor:theme.bg.css,scale:{mode:Phaser.Scale.NONE},scene:[inventoryScene(data,theme)],render:{antialias:true,roundPixels:true}});
const resizeCoordinator=createResizeCoordinator({
  readSize:()=>({width:host.clientWidth,height:host.clientHeight}),
  readCurrent:()=>({width:game.scale.width,height:game.scale.height}),
  resize:(width,height)=>game.scale.resize(width,height),
  isDragging:()=>document.body.classList.contains('is-chat-resizing'),
  requestFrame:callback=>requestAnimationFrame(callback),cancelFrame:id=>cancelAnimationFrame(id),
});
const observer=new ResizeObserver(resizeCoordinator.schedule);observer.observe(host);
const dragObserver=new MutationObserver(resizeCoordinator.schedule);
dragObserver.observe(document.body,{attributes:true,attributeFilter:['class']});
window.addEventListener('resize',resizeCoordinator.schedule);
window.inventoryLab={game,data,sceneName:'InventoryWorkspace'};
const closeButton=document.getElementById('inventory-close');
const closedNote=document.createElement('p');closedNote.className='inventory-closed-note';
closedNote.textContent='Инвентарь закрыт. Откройте его кнопкой в панели персонажа.';closedNote.hidden=true;host.append(closedNote);
function setInventoryOpen(open){
  host.dataset.inventoryOpen=String(open);
  game.canvas.hidden=!open;closedNote.hidden=open;closeButton.hidden=!open;
  currentBag.textContent=open?'Инвентарь · открыт':'Открыть инвентарь';
  currentBag.setAttribute('aria-expanded',String(open));
  currentBag.title=open?'Текущий экран: инвентарь':'Открыть инвентарь';
  if(open){currentBag.setAttribute('aria-current','page');game.scene.resume('InventoryWorkspace');resizeCoordinator.schedule();}
  else{currentBag.removeAttribute('aria-current');game.scene.pause('InventoryWorkspace');currentBag.focus();}
}
currentBag.disabled=false;currentBag.setAttribute('aria-expanded','true');currentBag.setAttribute('aria-controls','inventory-stage');
currentBag.addEventListener('click',()=>setInventoryOpen(true));
closeButton.addEventListener('click',()=>setInventoryOpen(false));
window.addEventListener('pagehide',()=>{observer.disconnect();dragObserver.disconnect();window.removeEventListener('resize',resizeCoordinator.schedule);resizeCoordinator.dispose();game.destroy(true);},{once:true});
