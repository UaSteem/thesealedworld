/* Choices use the existing HTMX transport and its authoritative state transitions. */
export function createChoiceBridge({read, activate, render}) {
    let model = null, busy = false, error = null, revision;
    const publish = () => render({model, busy, error});
    return {
        update(value) {
            const next = JSON.stringify(value);
            if (next !== revision) {revision = next;model = value;error = null;}
            publish();
        },
        choose(actionId) {
            const current = read();
            if (!model || busy || error || current?.node_key !== model.node_key
                || !model.buttons?.some(button => button.action_id === actionId)
                || !current.buttons?.some(button => button.action_id === actionId)) return false;
            busy = true;error = null;publish();
            if (activate(actionId) === false) {busy = false;error = 'Не удалось отправить ответ. Обновите состояние.';publish();return false;}
            return true;
        },
        begin() {busy = true;publish();},
        finish(successful) {busy = false;if(!successful)error = 'Не удалось подтвердить ответ. Обновите состояние перед продолжением.';publish();},
        reset() {model = null;revision = undefined;busy = false;error = null;},
    };
}

export function resolveScenarioCatalog(model, lookup) {
    const panel = model?.extra_data?.right_panel;
    if (!panel || !lookup) return model;
    return {...model, extra_data:{...model.extra_data, right_panel:{...panel, widgets:(panel.widgets || []).map(widget => ({
        ...widget, items:(widget.items || []).map(item => {
            if(!item.catalog || !item.catalog_key)return item;
            const entry=lookup(item.catalog,item.catalog_key), title=entry?.title || entry?.name;
            return title ? {...item,label:String(title)} : item;
        }),
    }))}}};
}

export async function installScenario(shell, version = '') {
    const {createScenarioScene} = await import('./scenario-scene.js' + version);
    let currentRoot, currentScene, sourceText, pendingRequest, requestRoot, lastRender;
    const events = new AbortController();
    function read(root = currentRoot) {
        const script = root?.querySelector('[data-game-client-scenario]');
        if (!script) return null;
        try {
            const value = JSON.parse(script.textContent);
            return value && Array.isArray(value.buttons) && typeof value.text === 'string'
                && String(value.char_id) === root.dataset.characterId ? value : null;
        } catch {return null;}
    }
    const bridge = createChoiceBridge({read,
        activate(actionId) {
            if (!currentRoot?.isConnected || currentRoot.dataset.gameState !== 'scenario') return false;
            const button = [...currentRoot.querySelectorAll('[data-game-client-scenario-action]')]
                .find(button => button.dataset.gameClientScenarioAction === actionId && !button.disabled);
            if (!button) return false;
            pendingRequest = null;button.click();return Boolean(pendingRequest);
        },
        render({model,busy,error}) {
            if (!model || !currentScene?.sys.isActive() || !currentRoot?.isConnected) return;
            const rendered = JSON.stringify({model,busy,error});
            if(rendered === lastRender)return;lastRender = rendered;
            const presentation=resolveScenarioCatalog(model,(catalog,key)=>window.GameCatalogCache?.get(catalog,key));
            currentScene.present(presentation, {busy,error,onChoose:action => bridge.choose(action),
                onRefresh:() => window.location.assign('/game/session')});
        },
    });
    shell.register('scenario', {key:'GameClientScenario',Scene:createScenarioScene(Phaser),
        canRender:root => Boolean(read(root)),
        update(scene,root,services) {
            const script = root.querySelector('[data-game-client-scenario]');
            if (currentRoot !== root) {bridge.reset();pendingRequest = null;sourceText = undefined;lastRender = null;}
            currentRoot = root;currentScene = scene;
            const text = script?.textContent;
            if (sourceText !== text) {sourceText = text;lastRender = null;bridge.update(read(root));}
            else if(!scene.model)bridge.update(read(root));
        },
    });
    document.body.addEventListener('htmx:beforeRequest', event => {
        const element = event.detail.elt;
        if (!element?.matches?.('[data-game-client-scenario-action]') || !currentRoot?.contains(element)) return;
        pendingRequest = event.detail.xhr;requestRoot = currentRoot;
        const origin = currentRoot, characterId = origin.dataset.characterId;
        // beforeOnLoad runs before HX-Redirect and all OOB swaps, even on a detached source element.
        const guard = incoming => {
            if(!element.isConnected || origin !== document.getElementById('game-session-root')
                || origin.dataset.gameState !== 'scenario' || origin.dataset.characterId !== characterId) incoming.preventDefault();
        };
        element.addEventListener('htmx:beforeOnLoad',guard);
        element.addEventListener('htmx:afterRequest',()=>element.removeEventListener('htmx:beforeOnLoad',guard),{once:true});
        bridge.begin();
    }, {signal:events.signal});
    document.body.addEventListener('htmx:afterRequest', event => {
        if (pendingRequest !== event.detail.xhr) return;
        pendingRequest = null;
        if (requestRoot === currentRoot && currentRoot?.isConnected && currentRoot.dataset.gameState === 'scenario') {
            bridge.finish(Boolean(event.detail.successful));shell.refresh();
        }
    }, {signal:events.signal});
    window.GameCatalogCache?.init().then(()=>{
        if(currentRoot?.isConnected){lastRender=null;bridge.update(read());}
    }).catch(()=>{});
    return {
        syncRoot(root) {
            if(pendingRequest && (requestRoot !== root || !root?.isConnected || root.dataset.gameState !== 'scenario')) {
                const pending=pendingRequest;pendingRequest=null;pending.abort();bridge.reset();
            }
        },
        dispose(){events.abort();pendingRequest?.abort();bridge.reset();pendingRequest=null;currentScene=null;currentRoot=null;},
    };
}
