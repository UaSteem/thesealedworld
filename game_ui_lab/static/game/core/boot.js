/* One game instance; individual gameplay scenes do not own the browser shell. */
(() => {
  'use strict';
  const host=document.getElementById('combat-stage');
  if(!host)return;
  async function boot(){
    await window.GameClientAssets.initialize('/ui-static/game/assets/catalog.json');
    const {createResizeCoordinator}=await import('/ui-static/game/shared/resize.js');
    const sceneId=host.dataset.gameScene||'combat';
    const Scene=window.GameClientScenes?.[sceneId];
    if(!Scene)throw new Error(`Unknown gameplay scene: ${sceneId}`);
    const dpr=Math.min(2,window.devicePixelRatio||1);
    const game=new Phaser.Game({type:Phaser.AUTO,parent:host,transparent:true,
      width:host.clientWidth*dpr,height:host.clientHeight*dpr,
      scale:{zoom:1/dpr,mode:Phaser.Scale.NONE},scene:[Scene],render:{antialias:true}});
    let active=sceneId,switching=false,inventory=null;
    let managementOrigin=null,managementTab='inventory',returnFocus=null;
    const stage=host.parentElement,characterWindow=document.getElementById('character-window');
    const characterContent=document.getElementById('character-window-content');
    const bag=document.querySelector('.cp-bag button'),close=document.getElementById('inventory-close');
    const title=document.getElementById('game-screen-title'),views=document.getElementById('combat-view-options');
    const battleTitle='Бой';
    const loading=document.createElement('div');loading.className='game-client-loading';
    loading.setAttribute('role','status');loading.textContent='Открываем инвентарь…';loading.hidden=true;host.append(loading);
    const resizeOverlay=document.createElement('div');resizeOverlay.className='inventory-resize-overlay';
    resizeOverlay.setAttribute('role','status');
    const resizeLabel=document.createElement('strong');resizeLabel.textContent='Подстраиваем размер…';
    const resizeHint=document.createElement('span');resizeHint.textContent='Отпустите границу, чтобы продолжить';
    resizeOverlay.append(resizeLabel,resizeHint);host.append(resizeOverlay);
    const resize=createResizeCoordinator({
      readSize:()=>({width:host.clientWidth*dpr,height:host.clientHeight*dpr}),
      readCurrent:()=>({width:game.scale.width,height:game.scale.height}),
      resize:(width,height)=>game.scale.resize(width,height),
      isDragging:()=>active==='inventory'&&document.body.classList.contains('is-chat-resizing'),
      requestFrame:callback=>requestAnimationFrame(callback),cancelFrame:id=>cancelAnimationFrame(id),
    });
    const observer=new ResizeObserver(resize.schedule);observer.observe(host);
    const dragObserver=new MutationObserver(resize.schedule);dragObserver.observe(document.body,{attributes:true,attributeFilter:['class']});
    const draftKeys={rift:'RiftPreview',character:'CharacterDraft',scenario:'ScenarioDraft',arena:'ArenaDraft',districts:'DistrictDraft',city:'CityDraft',loot:'LootDraft',death:'DeathDraft'};
    const screenTitles={rift:'Карта рифта',combat:'Бой',character:'Персонаж · черновик',scenario:'Диалоги · концепция',arena:'Арена · черновик',districts:'Кварталы · черновик',city:'Город · концепция',loot:'Добыча · черновик',death:'Смерть · черновик'};
    const sceneKey=id=>id==='inventory'?'InventoryWorkspace':draftKeys[id]||'HexCombatWorkspace';
    function showScreen(id){
      const managing=id==='inventory'||id==='character';
      characterWindow.dataset.section=id==='inventory'?'inventory':managementTab;
      document.getElementById('character-window-title').textContent=['Квесты','Настройки'].includes(managementTab)&&id==='character'?managementTab:'Персонаж';
      characterWindow.hidden=!managing;
      (managing?characterContent:stage).append(host);
      document.querySelectorAll('[data-character-tab]').forEach(button=>{
        const selected=managing&&button.dataset.characterTab===managementTab;
        button.setAttribute(button.classList.contains('player-hud')?'aria-expanded':'aria-pressed',String(selected));
      });
      active=id;document.body.dataset.gameScreen=id;
      document.querySelectorAll('.player-menu [data-character-tab]').forEach(button=>button.disabled=id==='combat');
      const hud=document.querySelector('.player-hud');if(hud)hud.disabled=id==='combat';
      document.querySelectorAll('[data-lab-screen="character"]').forEach(button=>{button.disabled=id==='combat';button.title=id==='combat'?'В бою недоступно':'';});host.dataset.inventoryOpen=String(id==='inventory');
      const pageTitle=id==='character'&&['Квесты','Настройки'].includes(managementTab)?managementTab:screenTitles[id]||(id==='inventory'?'Инвентарь':battleTitle);
      title.textContent=pageTitle;views.hidden=id!=='combat';close.hidden=id==='combat'||id==='rift';
      document.querySelectorAll('[data-lab-screen]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.labScreen===id&&!(id==='character'&&['Квесты','Настройки'].includes(managementTab)))));
      bag.textContent=id==='inventory'?'Закрыть инвентарь':'Инвентарь ↗';
      bag.setAttribute('aria-expanded',String(id==='inventory'));bag.setAttribute('aria-controls','combat-stage');
      bag.title=id==='inventory'?'Вернуться к бою':'Открыть инвентарь';
      game.canvas.setAttribute('aria-label',pageTitle);
    }
    async function openInventory(){
      if(switching||active==='inventory'||active==='combat')return;
      if(active==='inventory')return;
      switching=true;bag.disabled=true;loading.hidden=false;
      const previous=active;
      if(!managementOrigin){managementOrigin=active;returnFocus=document.activeElement;}
      managementTab='inventory';
      showScreen('inventory');resize.schedule();
      try{
        if(!inventory){
          await document.fonts.ready;
          const {createInventoryClientScene}=await import('/ui-static/game/scenes/inventory/client.js');
          const prepared=createInventoryClientScene({host,renderScale:dpr});
          inventory=game.scene.add('InventoryWorkspace',prepared.Scene,false);
          window.inventoryLab={game,data:prepared.data,sceneName:'InventoryWorkspace'};
          const ready=new Promise(resolve=>inventory.events.once('create',resolve));
          game.scene.sleep(sceneKey(previous));game.scene.start('InventoryWorkspace');
          await ready;
        }else{
          game.scene.sleep(sceneKey(previous));game.scene.wake('InventoryWorkspace');
        }
        showScreen('inventory');resize.schedule();game.canvas.focus({preventScroll:true});
      }catch(error){
        console.error(error);restoreManagement();
        loading.textContent='Не удалось открыть инвентарь. Попробуйте ещё раз.';
        return;
      }finally{
        switching=false;bag.disabled=false;
        if(active==='inventory')loading.hidden=true;
      }
    }
    function closeInventory(){
      if(switching||active!=='inventory')return;
      game.scene.sleep('InventoryWorkspace');restoreManagement();
    }
    bag.addEventListener('click',()=>active==='inventory'?closeInventory():openInventory());
    function suspendScreen(id){
      const key=sceneKey(id);
      if(['arena','districts','city'].includes(id))game.scene.stop(key);else game.scene.sleep(key);
    }
    function closeDraft(){
      if(!draftKeys[active]||active==='rift')return;
      if(active==='character'&&managementOrigin){suspendScreen(active);restoreManagement();return;}
      suspendScreen(active);game.scene.wake('RiftPreview');showScreen('rift');resize.schedule();
    }
    async function openDraft(id,parameters={}){
      if(switching||(active==='combat'&&id==='character'))return;
      if(managementOrigin&&id!=='character'){if(active==='inventory')closeInventory();else closeDraft();}
      if(id===active && !(id==='districts'&&parameters.district&&game.scene.getScene('DistrictDraft').state.district!==parameters.district))return;
      if(id==='combat'){if(managementOrigin){if(active==='inventory')closeInventory();else closeDraft();}suspendScreen(active);if(!game.scene.keys.HexCombatWorkspace)game.scene.add('HexCombatWorkspace',window.GameClientScenes.combat,false);game.scene.start('HexCombatWorkspace');showScreen('combat');resize.schedule();return;}
      if(!draftKeys[id])return;
      switching=true;
      const previous=active;
      if(id==='character'){if(!managementOrigin){managementOrigin=active;returnFocus=document.activeElement;}showScreen(id);resize.schedule();}
      try{
        if(!game.scene.keys[draftKeys[id]]){
          const {createDraftScenes}=await import('/ui-static/game/scenes/drafts/pages.js');
          for(const Draft of createDraftScenes({host,renderScale:dpr}))game.scene.add(new Draft().sys.settings.key,Draft,false);
        }
        if(id==='character')game.scene.sleep(sceneKey(previous));else suspendScreen(previous);
        const key=draftKeys[id];
        if(id==='character')game.scene.getScene(key).state.tab=managementTab;
        if(game.scene.isSleeping(key))game.scene.wake(key);else game.scene.start(key,parameters);
        showScreen(id);resize.schedule();
      }catch(error){console.error(error);if(managementOrigin)restoreManagement();else game.scene.wake(sceneKey(active));}
      finally{switching=false;}
    }
    function restoreManagement(){
      const origin=managementOrigin||'combat';managementOrigin=null;
      showScreen(origin);
      const key=sceneKey(origin);
      if(game.scene.isSleeping(key))game.scene.wake(key);else if(!game.scene.isActive(key))game.scene.start(key);
      resize.schedule();returnFocus?.focus?.({preventScroll:true});
    }
    async function openCharacterTab(tab){
      if(switching||active==='combat')return;
      if(tab==='inventory'){await openInventory();return;}
      managementTab=tab;
      if(active==='character'){game.scene.getScene('CharacterDraft').state.tab=tab;game.scene.getScene('CharacterDraft').draw();showScreen(active);return;}
      await openDraft('character');
    }
    document.querySelectorAll('[data-character-tab]').forEach(button=>button.addEventListener('click',()=>openCharacterTab(button.dataset.characterTab)));
    document.getElementById('character-window-close').addEventListener('click',()=>active==='inventory'?closeInventory():closeDraft());
    characterWindow.addEventListener('keydown',event=>{
      if(event.key!=='Tab')return;
      const controls=[...characterWindow.querySelectorAll('button:not(:disabled),summary,[tabindex="0"]')].filter(node=>node.getClientRects().length);
      const first=controls[0],last=controls.at(-1);
      if(event.shiftKey&&document.activeElement===first){event.preventDefault();last?.focus();}
      else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first?.focus();}
    });
    document.querySelectorAll('[data-lab-screen]').forEach(button=>button.addEventListener('click',()=>button.dataset.labScreen==='character'?openCharacterTab('Характеристики'):openDraft(button.dataset.labScreen)));
    close.addEventListener('click',()=>active==='inventory'?closeInventory():closeDraft());
    const escape=event=>{
      const editing=event.target instanceof Element&&(event.target.closest('input,textarea,select')||event.target.isContentEditable);
      if(event.key==='Escape'&&!editing&&active==='inventory'&&!inventory?.current&&!inventory?.notice){event.preventDefault();closeInventory();}
      else if(event.key==='Escape'&&!editing&&draftKeys[active]){event.preventDefault();if(!game.scene.getScene(sceneKey(active)).handleEscape?.())closeDraft();}
    };
    window.addEventListener('keydown',escape);
    const ready=()=>{
      if(!game.scene.isActive(sceneKey(sceneId)))return;
      game.events.off('step',ready);bag.disabled=false;showScreen(sceneId);
    };
    game.events.on('step',ready);
    game.events.once('destroy',()=>{observer.disconnect();dragObserver.disconnect();resize.dispose();window.removeEventListener('keydown',escape);});
    window.GameClientRuntime={game,get sceneId(){return active;},openInventory,closeInventory,openDraft,openCharacterTab};
    // Lab diagnostics, not a backend API or production integration.
    window.gameUiLab={game,sceneName:sceneKey(sceneId)};
  }
  boot().catch(error=>{
    console.error(error);
    const message=document.createElement('div');
    message.className='game-client-error';message.setAttribute('role','alert');
    message.textContent='Не удалось загрузить игровой интерфейс. Обновите страницу.';
    host.append(message);
  });
})();
