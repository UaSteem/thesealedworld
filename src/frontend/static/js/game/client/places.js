/* Existing arena/service commands remain the authoritative HTMX transport. */
export function placesBridgeModel(payload, snapshot) {
    return {node_key:snapshot,buttons:(payload?.actions || []).filter(action=>action.enabled).map(action=>({action_id:action.id})),payload};
}

export async function installPlaces(shell, version = '') {
    const [{createPlacesScene}, {createChoiceBridge}] = await Promise.all([
        import('./places-scene.js'+version), import('./scenario.js'+version),
    ]);
    const domains=new Set(['arena','city_services']);
    const events=new AbortController();
    let currentRoot,currentScene,sourceText,pendingRequest,requestRoot,lastRender,lastState,pollTimer;
    function read(root=currentRoot) {
        try {
            const payload=JSON.parse(root?.querySelector('[data-game-client-places]')?.textContent || 'null');
            return payload && ['arena','service'].includes(payload.kind) && Array.isArray(payload.actions)
                && String(payload.char_id)===root.dataset.characterId ? payload : null;
        } catch {return null;}
    }
    function stopPolling(){clearTimeout(pollTimer);pollTimer=null;}
    function schedulePoll() {
        const poll=lastState?.model?.payload?.poll;
        if(!poll || lastState.busy || lastState.error || !currentRoot?.isConnected || !domains.has(currentRoot.dataset.gameState)){stopPolling();return;}
        if(pollTimer)return;
        pollTimer=setTimeout(()=>{
            pollTimer=null;
            if(currentScene?.sys.isActive() && !shell.inspect().overlay && currentRoot===document.getElementById('game-session-root'))bridge.choose(poll.id);
            else schedulePoll();
        },poll.interval_ms);
    }
    function publish(state) {
        lastState=state;
        if(state.model?.payload && currentScene?.sys.isActive() && currentRoot?.isConnected) {
            const rendered=JSON.stringify(state);
            if(rendered!==lastRender){lastRender=rendered;currentScene.present(state.model.payload,
                {busy:state.busy,error:state.error,onAction:id=>bridge.choose(id),onRefresh:()=>window.location.assign('/game/session')});}
        }
        schedulePoll();
    }
    const bridge=createChoiceBridge({
        read:()=>placesBridgeModel(read(),currentRoot?.querySelector('[data-game-client-places]')?.textContent),
        activate(id){
            if(!currentRoot?.isConnected || !domains.has(currentRoot.dataset.gameState) || shell.inspect().overlay)return false;
            const button=[...currentRoot.querySelectorAll('[data-game-client-places-action]')].find(el=>el.dataset.gameClientPlacesAction===id && !el.disabled);
            if(!button)return false;
            pendingRequest=null;button.click();return Boolean(pendingRequest);
        },render:publish,
    });
    const handler={key:'GameClientPlaces',Scene:createPlacesScene(Phaser),stopOnExit:true,
        initialData:root=>({model:read(root)}),canRender:root=>Boolean(read(root)),
        update(scene,root){
            if(root!==currentRoot){bridge.reset();pendingRequest=null;sourceText=undefined;lastRender=null;stopPolling();}
            currentRoot=root;currentScene=scene;
            const text=root.querySelector('[data-game-client-places]')?.textContent;
            if(text!==sourceText){stopPolling();sourceText=text;lastRender=null;bridge.update(placesBridgeModel(read(),text));}
            else if(lastState)publish(lastState);
        },
    };
    for(const domain of domains)shell.register(domain,handler);
    document.body.addEventListener('htmx:beforeRequest',event=>{
        const element=event.detail.elt;
        if(!element?.matches?.('[data-game-client-places-action]') || !currentRoot?.contains(element))return;
        pendingRequest=event.detail.xhr;requestRoot=currentRoot;
        const origin=currentRoot,domain=origin.dataset.gameState,charId=origin.dataset.characterId;
        const guard=incoming=>{
            if(!element.isConnected || origin!==document.getElementById('game-session-root') || origin.dataset.gameState!==domain || origin.dataset.characterId!==charId)incoming.preventDefault();
        };
        element.addEventListener('htmx:beforeOnLoad',guard);
        element.addEventListener('htmx:afterRequest',()=>element.removeEventListener('htmx:beforeOnLoad',guard),{once:true});bridge.begin();
    },{signal:events.signal});
    document.body.addEventListener('htmx:afterRequest',event=>{
        if(pendingRequest!==event.detail.xhr)return;
        pendingRequest=null;
        if(requestRoot===currentRoot && currentRoot?.isConnected && domains.has(currentRoot.dataset.gameState)){bridge.finish(Boolean(event.detail.successful));shell.refresh();}
    },{signal:events.signal});
    return {
        syncRoot(root){
            if(pendingRequest && (requestRoot!==root || !root?.isConnected || !domains.has(root.dataset.gameState))){const pending=pendingRequest;pendingRequest=null;pending.abort();bridge.reset();}
            if(!root || !domains.has(root.dataset.gameState))stopPolling();
        },
        dispose(){events.abort();stopPolling();pendingRequest?.abort();bridge.reset();currentRoot=null;currentScene=null;},
    };
}
