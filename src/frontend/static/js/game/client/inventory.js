/* Server snapshots remain authoritative; this controller never equips locally. */
export function createInventoryController({load, send, show, close, valid, onBusy = () => {}, onError = () => {}, onRefresh = () => {}}) {
    let generation = 0, current = null, active = false, busy = false, abort;
    async function run(operation, tab, mutation = false) {
        if (busy && mutation) return;
        const epoch = ++generation;
        abort?.abort(); abort = new AbortController(); busy = true; onBusy(true);
        try {
            const response = await operation(abort.signal);
            if (epoch !== generation || !active || !valid()) return;
            const model = response?.inventory;
            if (!model || !Array.isArray(model.visible_rows) || !Array.isArray(model.quick_slots)) throw new Error('Сервер не вернул данные инвентаря.');
            current = model;
            await show(model, {notice: response.notice, tab});
            if (mutation && epoch === generation && active && valid()) onRefresh();
        } catch (error) {
            if (error.name !== 'AbortError' && epoch === generation && active && valid()) onError(error);
        } finally {
            if (epoch === generation) {busy = false; onBusy(false);}
        }
    }
    function allDetails() {
        const slots = [...(current?.weapon_slots || []), ...(current?.accessory_rows || []).flatMap(row => row.slots || []),
            ...(current?.body_zones || []).flatMap(zone => [zone.primary_slot, zone.secondary_slot].filter(Boolean)), ...(current?.quick_slots || [])];
        return [...(current?.visible_rows || []).map(row => [row.item_id, row.details]), ...slots.map(slot => [slot.item?.item_id, slot.details])];
    }
    return {
        open(tab = 'items') {if (busy) return Promise.resolve(); active = true; return run(signal => load(tab, signal), tab);},
        action(params) {
            if (!active || busy || !current?.can_act || !valid()) return Promise.resolve();
            const detail = allDetails().find(([id]) => id === params.item_id)?.[1];
            const allowed = detail?.actions?.some(action => action.enabled && action.action === params.action && (action.slot_id || null) === (params.slot_id || null));
            if (!allowed) return Promise.resolve();
            const tab = current.tabs?.find(tab => tab.is_active)?.tab_id || 'items';
            return run(signal => send({...params, tab_id: tab}, signal), tab, true);
        },
        close() {generation++; active = false; current = null; busy = false; abort?.abort(); onBusy(false); close();},
        inspect: () => ({active, busy}),
    };
}

export async function createInventoryClient(shell, version = '') {
    const [{createInventoryScene}, {createCharacterScene}] = await Promise.all([
        import('./inventory-scene.js' + version), import('./character-scene.js' + version),
    ]);
    let context, controller, characterRequest, characterEpoch = 0, banner, beltGeneration = 0, lastModel, lastCallbacks;
    const beltCache = new Map(), beltPending = new Map();
    const root = () => document.getElementById('game-session-root');
    const allowed = () => context && context.root === root() && context.charId === root()?.dataset.characterId && !['combats', 'death', 'loot'].includes(root()?.dataset.gameState);
    function message(copy, retry) {
        banner?.remove();
        if (!copy) return;
        banner = document.createElement('div');banner.className = 'game-client-shell-error';banner.setAttribute('role','status');
        const text = document.createElement('p');text.textContent = copy;banner.append(text);
        if (retry) {const button = document.createElement('button');button.textContent = 'Повторить';button.onclick = retry;banner.append(button);}
        const close = document.createElement('button');close.textContent = 'Закрыть';close.onclick = closeAll;banner.append(close);
        document.getElementById('game-client-canvas-host').append(banner);
    }
    async function json(url, init = {}) {
        const response = await fetch(url, {credentials: 'same-origin', redirect: 'error', ...init, headers: {'Accept':'application/json', ...init.headers}});
        if (!response.ok) throw new Error(`Не удалось получить данные (${response.status}).`);
        if (!response.headers.get('Content-Type')?.includes('application/json')) throw new Error('Сессия недоступна. Обновите страницу.');
        return response.json();
    }
    function closeAll() {characterEpoch++; characterRequest?.abort(); controller?.close(); shell.closeOverlay(); message(null);}
    async function open(kind = 'inventory') {
        if (controller?.inspect().busy) return;
        if (['combats','death','loot'].includes(root()?.dataset.gameState)) return;
        closeAll();
        context = {root:root(),charId:root()?.dataset.characterId};
        if (!/^\d+$/.test(context.charId || '')) {message('Не удалось определить персонажа.');return;}
        if (kind === 'character') {
            const epoch = ++characterEpoch;characterRequest = new AbortController();message('Загружаем персонажа…');
            try {
                const response = await json(`/game/character-status/panel?char_id=${context.charId}&presentation=client`, {signal:characterRequest.signal});
                if (epoch !== characterEpoch || !allowed()) return;
                if (String(response.character?.char_id) !== context.charId) throw new Error('Получен другой персонаж.');
                message(null);
                await shell.openOverlay('GameClientCharacter', createCharacterScene(Phaser), {model:response.character,onClose:closeAll});
            } catch(error) {if(error.name !== 'AbortError' && epoch === characterEpoch && allowed()) message(error.message,()=>open(kind));}
            return;
        }
        controller = createInventoryController({
            valid:allowed,
            load:(tab,signal)=>json(`/game/inventory/window?char_id=${context.charId}&tab=${encodeURIComponent(tab)}&presentation=client`,{signal}),
            send:(params,signal)=>{
                const form = new FormData();for(const [key,value] of Object.entries({...params,char_id:context.charId,presentation:'client'})) if(value !== null && value !== undefined) form.set(key,String(value));
                return json('/game/inventory/action',{method:'POST',body:form,signal});
            },
            async show(model,{notice}) {
                if (String(model.char_id) !== context.charId) throw new Error('Получен инвентарь другого персонажа.');
                message(null);lastModel = model;
                const callbacks={onAction:params=>controller.action(params),onTab:tab=>controller.open(tab),onClose:closeAll,notice};
                lastCallbacks = callbacks;
                const scene=await shell.openOverlay('InventoryClientScene',createInventoryScene(Phaser),{model,...callbacks});
                scene?.present(model,callbacks);
            },
            close:()=>shell.closeOverlay(),
            onBusy(value) {const game=shell.inspect().game;const scene=game?.scene.keys.InventoryClientScene;if(scene?.sys.isActive() && lastModel)scene.present(lastModel,{...lastCallbacks,busy:value});if(value)message('Обновляем инвентарь…');else if(banner?.querySelector('p')?.textContent==='Обновляем инвентарь…')message(null);},
            onError:error=>message(error.message,()=>open()),
            onRefresh() {
                invalidateBelt();
                if (allowed() && document.getElementById('status-container') && window.htmx) {
                    window.htmx.ajax('GET',`/game/character-status/panel?char_id=${context.charId}`,{target:'#status-container',swap:'outerHTML'});
                }
            },
        });
        return controller.open();
    }
    function refreshBelt() {
        const host=document.querySelector('[data-game-client-belt]');if(!host || host.dataset.requested)return;
        const id=root()?.dataset.characterId, domain=root()?.dataset.gameState;
        if(!/^\d+$/.test(id || ''))return;
        host.dataset.requested='true';const key=id+':'+domain, epoch=beltGeneration;
        if(!beltPending.has(key) && !beltCache.has(key)) beltPending.set(key,fetch(`/game/inventory/belt?char_id=${id}`,{credentials:'same-origin',redirect:'error'}).then(response=>{
            if(!response.ok || !response.headers.get('Content-Type')?.includes('text/html'))throw Error('Пояс временно недоступен');return response.text();
        }).then(html=>{if(epoch===beltGeneration)beltCache.set(key,html);return html;}).finally(()=>{if(epoch===beltGeneration)beltPending.delete(key);}));
        Promise.resolve(beltCache.get(key) || beltPending.get(key)).then(html=>{
            if(epoch===beltGeneration && host.isConnected && root()?.dataset.characterId===id && root()?.dataset.gameState===domain)host.innerHTML=html;
        }).catch(()=>{if(epoch===beltGeneration && host.isConnected){host.textContent='Не удалось загрузить пояс.';const retry=document.createElement('button');retry.textContent='Повторить';retry.onclick=()=>{delete host.dataset.requested;refreshBelt();};host.append(retry);}});
    }
    function invalidateBelt() {
        beltGeneration++;beltCache.clear();beltPending.clear();
        const host=document.querySelector('[data-game-client-belt]');if(host)delete host.dataset.requested;
        refreshBelt();
    }
    document.body.addEventListener('character-status-refresh',invalidateBelt);
    return {open, close:closeAll, refreshBelt, invalidateBelt, dispose(){closeAll();beltGeneration++;beltCache.clear();beltPending.clear();document.body.removeEventListener('character-status-refresh',invalidateBelt);}};
}
