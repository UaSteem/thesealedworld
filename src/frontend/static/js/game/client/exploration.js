export function actionEnabled(action, cooling = false) {
    return Boolean(action?.enabled) && !(action.kind === 'move' && cooling);
}
export function explorationBridgeModel(payload, snapshot, cooling = false) {
    return {node_key:snapshot,buttons:(payload?.actions || []).filter(action=>actionEnabled(action,cooling)).map(action=>({action_id:action.id})),payload};
}

export async function installExploration(shell, version = '') {
    const [{createExplorationScene}, {createChoiceBridge}] = await Promise.all([
        import('./exploration-scene.js'+version),import('./scenario.js'+version),
    ]);
    let currentRoot, currentScene, sourceText, pendingRequest, requestRoot, lastRender, lastState, timer;
    const events = new AbortController();
    const cooling = () => Boolean(window.ExplorationMoveCooldown?.isActive());
    function source(root = currentRoot) {return root?.querySelector('[data-game-client-exploration]');}
    function read(root = currentRoot) {
        try {
            const value=JSON.parse(source(root)?.textContent || 'null');
            return value && typeof value.loc_id==='string' && Array.isArray(value.actions)
                && String(value.char_id)===root.dataset.characterId ? value : null;
        }catch{return null;}
    }
    function publish(state) {
        lastState=state;
        if (cooling() && !timer && currentRoot?.dataset.gameState === 'exploration') {
            timer=setInterval(()=>{
                if(lastState)publish(lastState);
                if(!cooling()){clearInterval(timer);timer=null;}
            },100);
        }
        if(!state.model?.payload || !currentScene?.sys.isActive() || !currentRoot?.isConnected)return;
        const activeCooldown=cooling(), rendered=JSON.stringify({state,activeCooldown});
        if(rendered===lastRender)return;lastRender=rendered;
        const model=state.model.payload;
        currentScene.present({...model,actions:model.actions.map(action=>({...action,enabled:actionEnabled(action,activeCooldown)}))},
            {busy:state.busy,error:state.error,onAction:id=>bridge.choose(id),onRefresh:()=>window.location.assign('/game/session')});
    }
    const bridge=createChoiceBridge({
        read:()=>explorationBridgeModel(read(),source()?.textContent,cooling()),
        activate(id) {
            const action=read()?.actions.find(action=>action.id===id);
            if(!actionEnabled(action,cooling()) || !currentRoot?.isConnected || currentRoot.dataset.gameState!=='exploration')return false;
            const button=[...currentRoot.querySelectorAll('[data-game-client-exploration-action]')].find(button=>button.dataset.gameClientExplorationAction===id && !button.disabled);
            if(!button)return false;
            pendingRequest=null;button.click();
            if(pendingRequest && action.kind==='move' && action.move_duration>0) {
                window.ExplorationMoveCooldown?.start(action.move_duration);
                clearInterval(timer);timer=setInterval(()=>{if(lastState)publish(lastState);if(!cooling()){clearInterval(timer);timer=null;}},100);
            }
            return Boolean(pendingRequest);
        }, render:publish,
    });
    shell.register('exploration',{key:'GameClientExploration',Scene:createExplorationScene(Phaser),stopOnExit:true,initialData:root=>({model:read(root)}),canRender:root=>Boolean(read(root)),
        update(scene,root) {
            if(currentRoot!==root){bridge.reset();pendingRequest=null;sourceText=undefined;lastRender=null;}
            currentRoot=root;currentScene=scene;
            const text=source()?.textContent;
            if(text!==sourceText){sourceText=text;lastRender=null;bridge.update(explorationBridgeModel(read(),text));}
            else if(!scene.model)bridge.update(explorationBridgeModel(read(),text));
            else if(lastState)publish(lastState);
        },
    });
    document.body.addEventListener('htmx:beforeRequest',event=>{
        const element=event.detail.elt;
        if(!element?.matches?.('[data-game-client-exploration-action]') || !currentRoot?.contains(element))return;
        pendingRequest=event.detail.xhr;requestRoot=currentRoot;
        const origin=currentRoot,characterId=origin.dataset.characterId;
        const guard=incoming=>{
            if(!element.isConnected || origin!==document.getElementById('game-session-root') || origin.dataset.gameState!=='exploration' || origin.dataset.characterId!==characterId)incoming.preventDefault();
        };
        element.addEventListener('htmx:beforeOnLoad',guard);
        element.addEventListener('htmx:afterRequest',()=>element.removeEventListener('htmx:beforeOnLoad',guard),{once:true});bridge.begin();
    },{signal:events.signal});
    document.body.addEventListener('htmx:afterRequest',event=>{
        if(pendingRequest!==event.detail.xhr)return;pendingRequest=null;
        if(requestRoot===currentRoot && currentRoot?.isConnected && currentRoot.dataset.gameState==='exploration'){bridge.finish(Boolean(event.detail.successful));shell.refresh();}
    },{signal:events.signal});
    return {
        syncRoot(root) {
            if(pendingRequest && (requestRoot!==root || !root?.isConnected || root.dataset.gameState!=='exploration')){const pending=pendingRequest;pendingRequest=null;pending.abort();bridge.reset();}
            if(!root || root.dataset.gameState!=='exploration'){clearInterval(timer);timer=null;}
        },
        dispose(){events.abort();clearInterval(timer);pendingRequest?.abort();bridge.reset();currentRoot=null;currentScene=null;},
    };
}
