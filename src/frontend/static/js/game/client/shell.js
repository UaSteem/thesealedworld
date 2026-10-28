/* Game-only persistent renderer boundary. Unmigrated domains retain real HTML. */
(() => {
    'use strict';
    if (window.GameClientShell) return;
    const handlers = new Map();
    const moduleVersion = new URL(document.currentScript.src).search;
    let servicesPromise, assetManager, inventoryClientPromise, inventoryClient, overlay, scenarioPromise, scenarioClient, explorationPromise, explorationClient, placesPromise, placesClient;
    let overlaySequence = 0;
    let shell, host, anchor, chatAnchor, game, activeKey, activeRoot;
    let frame = 0, loading, generation = 0, observedAnchor, mainObserver, chatObserver;
    let disposed = false;
    let dragging = false;
    const resizeObserver = new ResizeObserver(schedule);
    const controller = new AbortController();
    const options = {signal: controller.signal};

    function schedule() {
        if (!disposed && !frame) frame = requestAnimationFrame(sync);
    }
    function setProperty(element, name, value) {
        if (element.style.getPropertyValue(name) !== value) element.style.setProperty(name, value);
    }
    function phaserReady() {
        if (window.Phaser) return Promise.resolve();
        if (loading) return loading;
        loading = new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = '/static/js/vendor/phaser.min.js';
            script.dataset.gameClientVendor = 'phaser';
            script.onload = resolve;
            script.onerror = () => {script.remove(); loading = null; reject(new Error('Не удалось загрузить игровую область.'));};
            document.head.append(script);
        });
        return loading;
    }
    function errorView(message) {
        if (!host) return;
        let panel = host.querySelector('[data-client-error]');
        if (!panel) {
            panel = document.createElement('div'); panel.dataset.clientError = 'true';
            panel.className = 'game-client-shell-error'; panel.setAttribute('role', 'status');
            const copy = document.createElement('p'), retry = document.createElement('button');
            retry.type = 'button'; retry.textContent = 'Повторить';
            retry.addEventListener('click', () => {panel.remove(); host.dataset.clientFailed = 'false'; schedule();}, options);
            panel.append(copy, retry); host.append(panel);
        }
        panel.querySelector('p').textContent = message;
        host.dataset.clientFailed = 'true';
    }
    async function ensureGame() {
        if (game) return game;
        await phaserReady();
        if (disposed || !anchor?.isConnected) return null;
        if (!game) {
            game = new Phaser.Game({type: Phaser.AUTO, parent: host, transparent: true,
                width: 1, height: 1, scale: {mode: Phaser.Scale.NONE}, scene: [],
                render: {antialias: true}});
            game.events.once('ready', schedule);
        }
        return game;
    }
    function ensureServices(instance) {
        if (!instance) return Promise.reject(new Error('Game viewport unavailable'));
        if (!servicesPromise) servicesPromise = Promise.all([
            import('./assets.js' + moduleVersion), import('./components.js' + moduleVersion),
        ]).then(([assets, components]) => {
            if (disposed || game !== instance) throw new Error('Game client disposed');
            assetManager = assets.createAssetManager({textures: instance.textures,
                catalogURL: '/static/images/game-client/catalog.json' + moduleVersion});
            return {assets: assetManager, components};
        }).catch(error => {servicesPromise = null; throw error;});
        return servicesPromise;
    }
    function closeOverlay() {
        overlaySequence++;
        if (overlay) {
            const key = overlay.key; overlay = null;
            game?.scene.stop(key); game?.scene.remove(key);
        }
        if (shell) delete shell.dataset.clientOverlay;
        const legacy = document.getElementById('game-center');
        const handler = handlers.get(activeRoot?.dataset.gameState);
        if (legacy) legacy.hidden = Boolean(handler);
        if (host) {host.dataset.clientRenderer = handler ? 'canvas' : 'legacy'; host.setAttribute('aria-hidden', String(!handler));}
        schedule();
    }
    async function openOverlay(key, Scene, data) {
        if (overlay?.key === key) return game.scene.getScene(key);
        closeOverlay();
        const epoch = ++overlaySequence, root = document.getElementById('game-session-root');
        const instance = await ensureGame();
        if (!instance) return null;
        if (!instance.isBooted) await new Promise(resolve => instance.events.once('ready', resolve));
        const services = await ensureServices(instance);
        if (disposed || epoch !== overlaySequence || root !== document.getElementById('game-session-root')) return null;
        if (activeKey) instance.scene.sleep(activeKey);
        if (instance.scene.keys[key]) instance.scene.remove(key);
        const scene = instance.scene.add(key, Scene, false);
        overlay = {key, root, domain: root.dataset.gameState, charId: root.dataset.characterId}; shell.dataset.clientOverlay = 'true';
        host.dataset.clientRenderer = 'canvas'; host.setAttribute('aria-hidden','false');
        const legacy = document.getElementById('game-center'); if (legacy) legacy.hidden = true;
        const ready = new Promise(resolve => {
            scene.events.once('create', () => resolve(scene));
            scene.events.once('destroy', () => resolve(null));
        });
        instance.scene.start(key, {...data, services});
        return ready;
    }
    function ensureInventoryClient() {
        if (!inventoryClientPromise) inventoryClientPromise = import('./inventory.js' + moduleVersion)
            .then(async module => {
                const instance = await ensureGame();
                if (!instance || disposed) throw new Error('Game viewport unavailable');
                return module.createInventoryClient(window.GameClientShell, moduleVersion);
            })
            .then(client => {
                if (disposed) {client.dispose(); throw new Error('Game client disposed');}
                inventoryClient = client;return client;
            }).catch(error => {inventoryClientPromise = null;throw error;});
        return inventoryClientPromise;
    }
    function geometry() {
        const scale = Math.min(1, window.innerWidth / 1920);
        const styles = getComputedStyle(shell);
        const header = Number.parseFloat(styles.getPropertyValue('--game-header-height')) || 40;
        const footer = Number.parseFloat(styles.getPropertyValue('--game-footer-height')) || 24;
        setProperty(shell, '--client-scale', String(scale));
        setProperty(shell, '--client-height', `${Math.max(1, (innerHeight - header - footer) / scale)}px`);
        const state = window.Alpine?.$data(shell);
        shell.dataset.clientChatCollapsed = String(Boolean(state?.chatClosed));
        const rect = anchor.getBoundingClientRect(), chatRect = chatAnchor?.getBoundingClientRect();
        Object.assign(host.style, {left: `${rect.left}px`, top: `${rect.top}px`, width: `${rect.width}px`, height: `${rect.height}px`});
        if (chatRect) for (const [key, value] of Object.entries({left: chatRect.left, top: chatRect.top, width: chatRect.width, height: chatRect.height})) {
            setProperty(shell, '--client-chat-' + key, `${value}px`);
        }
        if (game?.isBooted) {
            const dpr = Math.min(2, devicePixelRatio || 1), w = Math.max(1, Math.round(anchor.clientWidth * dpr)), h = Math.max(1, Math.round(anchor.clientHeight * dpr));
            if (game.scale.width !== w || game.scale.height !== h) game.scale.resize(w, h);
            Object.assign(game.canvas.style, {width: `${rect.width}px`, height: `${rect.height}px`});
            game.scale.updateBounds();
        }
    }
    async function route(root, epoch) {
        const domain = root.dataset.gameState || '', candidate = handlers.get(domain);
        const handler = candidate && (!candidate.canRender || candidate.canRender(root)) ? candidate : null;
        shell.dataset.clientScene = handler?.key || '';
        const legacy = document.getElementById('game-center');
        if (activeKey && (!handler || handler.key !== activeKey)) {
            if ([...handlers.values()].some(value => value.key === activeKey && value.stopOnExit)) game?.scene.stop(activeKey);
            else game?.scene.sleep(activeKey); activeKey = null;
        }
        // The HTML is authoritative until that domain is explicitly migrated.
        host.dataset.clientRenderer = handler ? 'canvas' : 'legacy';
        host.setAttribute('aria-hidden', String(!handler));
        if (legacy) legacy.hidden = Boolean(handler);
        if (!handler) return;
        const instance = await ensureGame();
        if (!instance || epoch !== generation || !root.isConnected) return;
        if (!instance.isBooted) {instance.events.once('ready', schedule); return;}
        const services = await ensureServices(instance);
        if (disposed || epoch !== generation || !root.isConnected) return;
        if (!instance.scene.keys[handler.key]) instance.scene.add(handler.key, handler.Scene, false);
        const scene = instance.scene.getScene(handler.key);
        if (instance.scene.isSleeping(handler.key)) instance.scene.wake(handler.key);
        else if (!instance.scene.isActive(handler.key)) {scene.events.once('create',schedule);instance.scene.start(handler.key, {services, ...handler.initialData?.(root)});}
        activeKey = handler.key;
        if (scene.sys.settings.status === Phaser.Scenes.RUNNING) handler.update?.(scene, root, services);
    }
    function sync() {
        frame = 0;
        shell = document.querySelector('[data-game-client-shell]');
        host = document.getElementById('game-client-canvas-host');
        anchor = document.getElementById('game-client-scene-anchor');
        chatAnchor = document.getElementById('game-client-chat-anchor');
        const root = document.getElementById('game-session-root');
        scenarioClient?.syncRoot(root);
        explorationClient?.syncRoot(root);
        placesClient?.syncRoot(root);
        if (!shell || !host || !anchor || !root) {
            if (activeRoot || overlay) {inventoryClient?.close(); closeOverlay();}
            if (host) host.dataset.clientRenderer = 'legacy';
            if (activeKey) {
                if ([...handlers.values()].some(value => value.key === activeKey && value.stopOnExit)) game?.scene.stop(activeKey);
                else game?.scene.sleep(activeKey);
            }
            activeKey = null; activeRoot = null;
            return;
        }
        if (observedAnchor !== anchor) {
            resizeObserver.disconnect(); resizeObserver.observe(anchor);
            if (chatAnchor) resizeObserver.observe(chatAnchor);
            observedAnchor = anchor;
        }
        geometry();
        if ((activeRoot && activeRoot !== root) || (overlay && (overlay.domain !== root.dataset.gameState || overlay.charId !== root.dataset.characterId))) {inventoryClient?.close(); closeOverlay();}
        if (activeRoot !== root) generation++;
        activeRoot = root;
        const epoch = generation;
        if (document.querySelector('[data-game-client-belt]')) ensureInventoryClient().then(client => client.refreshBelt()).catch(error => console.error(error));
        if (root.dataset.gameState === 'scenario' && !scenarioPromise) {
            scenarioPromise = ensureGame().then(instance => {
                if(!instance || disposed)throw new Error('Game viewport unavailable');
                return import('./scenario.js' + moduleVersion);
            }).then(module => module.installScenario(window.GameClientShell,moduleVersion)).then(client => {
                if(disposed){client.dispose();throw new Error('Game client disposed');}
                scenarioClient=client;schedule();return client;
            }).catch(error => {scenarioPromise=null;console.error(error);errorView('Не удалось открыть диалог. Повторите загрузку.');});
        }
        if (root.dataset.gameState === 'exploration' && !explorationPromise) {
            explorationPromise = ensureGame().then(instance => {
                if (!instance || disposed) throw new Error('Game viewport unavailable');
                return import('./exploration.js' + moduleVersion);
            }).then(module => module.installExploration(window.GameClientShell, moduleVersion)).then(client => {
                if (disposed) {client.dispose(); throw new Error('Game client disposed');}
                explorationClient = client; schedule(); return client;
            }).catch(error => {explorationPromise = null; console.error(error); errorView('Не удалось открыть карту. Повторите загрузку.');});
        }
        if (['arena','city_services'].includes(root.dataset.gameState) && !placesPromise) {
            placesPromise = ensureGame().then(instance => {
                if(!instance || disposed)throw new Error('Game viewport unavailable');
                return import('./places.js' + moduleVersion);
            }).then(module => module.installPlaces(window.GameClientShell,moduleVersion)).then(client => {
                if(disposed){client.dispose();throw new Error('Game client disposed');}
                placesClient=client;schedule();return client;
            }).catch(error => {placesPromise=null;console.error(error);errorView('Не удалось открыть помещение. Повторите загрузку.');});
        }
        if (overlay) return;
        // Create a single persistent Game even while the HTML domain is retained.
        ensureGame().then(() => {if (epoch === generation) {geometry(); return route(root, epoch);}})
            .catch(error => {console.error(error); errorView(error.message);});
    }
    function boot() {
        const main = document.getElementById('main-content');
        if (!document.querySelector('[data-game-client-shell]') || !main) return;
        mainObserver = new MutationObserver(schedule); mainObserver.observe(main, {childList: true, subtree: true});
        const chat = document.getElementById('game-chat-container');
        if (chat) {chatObserver = new MutationObserver(schedule); chatObserver.observe(chat, {attributes: true, attributeFilter: ['style', 'class']});}
        schedule();
    }
    function chatShare(percent) {
        if (!shell) return;
        const value = Math.max(15, Math.min(20, percent));
        setProperty(shell, '--client-chat-share', value + '%');
        const state = window.Alpine?.$data(shell);
        if (state) state.chatClosed = false;
        schedule();
    }
    function dispose() {
        disposed = true; generation++; inventoryClient?.dispose(); scenarioClient?.dispose(); explorationClient?.dispose(); placesClient?.dispose(); closeOverlay();
        cancelAnimationFrame(frame); controller.abort(); resizeObserver.disconnect();
        mainObserver?.disconnect(); chatObserver?.disconnect(); assetManager?.dispose(); game?.destroy(true); game = null;
    }
    window.GameClientShell = {
        register(domain, handler) {
            if (!domain || !handler?.key || !handler.Scene) throw new Error('Invalid scene registration');
            handlers.set(domain, handler); schedule();
        },
        inspect: () => ({game, activeKey, overlay: overlay?.key, domain: activeRoot?.dataset.gameState, renderer: host?.dataset.clientRenderer}),
        services: () => ensureGame().then(ensureServices),
        openOverlay, closeOverlay,
        openInventory: () => ensureInventoryClient().then(client => client.open('inventory')),
        refresh: schedule, dispose,
    };
    document.addEventListener('click', event => {
        const button = event.target.closest?.('[data-game-client-open]');
        if (!button || !document.querySelector('[data-game-client-shell]')) return;
        event.preventDefault();event.stopImmediatePropagation();
        ensureInventoryClient().then(client => client.open(button.dataset.gameClientOpen)).catch(error => errorView(error.message));
    }, {...options, capture: true});
    document.addEventListener('keydown', event => {
        if(event.key !== 'Escape' || !overlay)return;
        event.preventDefault();event.stopPropagation();
        const scene=game?.scene.getScene(overlay.key);
        if(overlay.key==='InventoryClientScene' && scene?.selected){
            if(scene.dismissDetail)scene.dismissDetail();else{scene.selected=null;scene.draw();}
        }else{inventoryClient?.close();closeOverlay();}
    }, options);
    document.addEventListener('htmx:afterSwap', schedule, options);
    document.addEventListener('htmx:oobAfterSwap', schedule, options);
    document.addEventListener('pointerdown', event => {
        const divider = event.target.closest?.('#game-client-chat-divider');
        if (!divider) return;
        dragging = true; divider.setPointerCapture?.(event.pointerId); event.preventDefault();
    }, options);
    document.addEventListener('pointermove', event => {
        if (!dragging) return;
        const viewport = document.getElementById('game-viewport')?.getBoundingClientRect();
        if (viewport?.height) chatShare((viewport.bottom - event.clientY) / viewport.height * 100);
    }, options);
    document.addEventListener('pointerup', () => {dragging = false;}, options);
    document.addEventListener('pointercancel', () => {dragging = false;}, options);
    document.addEventListener('keydown', event => {
        if (event.target.id !== 'game-client-chat-divider') return;
        const value = Number.parseFloat(shell.style.getPropertyValue('--client-chat-share')) || 17.5;
        const next = {ArrowUp: value + .5, ArrowDown: value - .5, Home: 15, End: 20}[event.key];
        if (next !== undefined) {event.preventDefault(); chatShare(next);}
    }, options);
    window.addEventListener('resize', schedule, options);
    window.addEventListener('pagehide', event => {if (!event.persisted) dispose();}, options);
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, {...options, once: true});
    else boot();
})();
