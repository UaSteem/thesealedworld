/* Interior presentation only. Hotspots inspect places; server action tokens remain opaque. */
export const placeValue = value => value == null ? '' : typeof value === 'boolean' ? (value ? 'Да' : 'Нет') : String(value);
const textValue = placeValue;
const ARENA_SPOTS = [
    {id:'registrar',label:'Распорядитель',point:[.19,.70],poly:[[.01,.58],[.13,.50],[.32,.61],[.32,.87],[.01,.97]]},
    {id:'duel',label:'Зал поединков',point:[.255,.43],poly:[[.14,.54],[.15,.30],[.22,.20],[.31,.20],[.355,.30],[.355,.59]]},
    {id:'main',label:'Главная арена',point:[.51,.42],poly:[[.435,.61],[.435,.23],[.47,.14],[.53,.14],[.573,.24],[.573,.60]]},
    {id:'board',label:'Турнирная доска',point:[.765,.51],poly:[[.66,.39],[.835,.36],[.843,.73],[.659,.69]]},
    {id:'exit',label:'Выход',point:[.945,.56],poly:[[.87,.32],[.99,.27],[1,.77],[.87,.72]]},
];
const SERVICE_POINTS = {
    administrative:[[.44,.43],[.69,.51],[.91,.70]],
    trading:[[.16,.60],[.55,.49],[.84,.58]],
    crafting:[[.16,.61],[.54,.49],[.74,.53],[.92,.55]],
    tavern:[[.25,.57],[.65,.42],[.78,.69]],
    portal:[[.50,.48],[.25,.65],[.78,.65]],
};
export function mainPlaceScreen(model) {
    return model?.kind === 'arena' ? model.screen === 'main_menu' : model?.screen === 'main';
}
function visibleActions(model) {return (model?.actions || []).filter(action => !action.hidden_poll);}
function arenaSpot(action) {
    if(action.action === 'menu_mode')return {one_vs_one:'duel',group:'main',tournament:'board'}[action.mode];
    if(action.action === 'start_shadow')return 'registrar';
    if(action.action === 'leave')return 'exit';
    return null;
}
function actionSpot(model, action) {
    if(model.kind === 'arena')return arenaSpot(action);
    if(model.npc?.action_id === action.id)return 'npc';
    if(action.section_id != null)return String(action.section_id);
    if(action.action === 'leave')return 'exit';
    return null;
}
export function actionsForPlace(model, spotId) {
    const validIds = new Set((model.sections || []).map(section => String(section.id)));
    return visibleActions(model).filter(action => {
        const spot = actionSpot(model, action);
        const supported = model.kind === 'arena' ? Boolean(spot) : spot === 'npc' || spot === 'exit' || validIds.has(spot);
        return spotId === 'other' ? !supported : spot === spotId;
    });
}
export function placeHotspots(model) {
    if(!mainPlaceScreen(model))return [];
    const spots = model.kind === 'arena' ? ARENA_SPOTS.map(spot => ({...spot})) : (model.sections || []).map((section,index) => {
        const points = SERVICE_POINTS[model.place] || [[.3,.55],[.65,.48],[.8,.72]];
        // Extra server sections remain visible without inventing additional buildings.
        const point = points[index] || [.2 + (index % 4) * .2,.82];
        return {id:String(section.id),label:section.title || String(section.id),description:section.description,point};
    });
    if(model.kind !== 'arena' && model.npc)spots.push({id:'npc',label:model.npc.name || model.npc.role || 'Собеседник',point:[.12,.65]});
    if(model.kind !== 'arena' && actionsForPlace(model,'exit').length)spots.push({id:'exit',label:'Выход',point:[.93,.72]});
    if(actionsForPlace(model,'other').length)spots.push({id:'other',label:'Другие действия',point:[.50,.89]});
    return spots;
}
export function fitPlaceBackground(width,height,sourceWidth,sourceHeight) {
    const top = Math.min(76,height*.2),bottom = Math.min(36,height*.1);
    const scale = Math.min(width/sourceWidth,Math.max(1,height-top-bottom)/sourceHeight);
    return {x:(width-sourceWidth*scale)/2,y:top+(height-top-bottom-sourceHeight*scale)/2,width:sourceWidth*scale,height:sourceHeight*scale};
}
export function placeAssetUrl(path,origin) {
    if(typeof path !== 'string' || !path.trim())return null;
    try {const url=new URL(path,origin);return url.origin===new URL(origin).origin && ['http:','https:'].includes(url.protocol)?url.href:null;}catch{return null;}
}
function palette(host) {
    const probe=host.ownerDocument.createElement('span');host.append(probe);const result={};
    for(const [name,token] of Object.entries({bg:'--col-bg-base',panel:'--col-bg-surface',line:'--col-border',accent:'--col-accent',text:'--col-text-primary',dim:'--col-text-dim'})) {
        probe.style.color=`var(${token})`;const css=getComputedStyle(probe).color,ch=css.match(/[\d.]+/g)?.slice(0,3).map(Number)||[20,24,30];
        result[name]={css,number:(ch[0]<<16)+(ch[1]<<8)+ch[2]};
    }
    probe.remove();return result;
}
let instanceSequence=0;
export function createPlacesScene(P) {
    return class PlacesScene extends P.Scene {
        constructor(){super({key:'GameClientPlaces'});this.controls=[];this.serial=++instanceSequence;this.imageSequence=0;this.selected=null;this.scroll=0;}
        create(options={}) {
            this.services=options.services||this.services;this.model=options.model||this.model||{};this.callbacks={...this.callbacks};
            for(const key of ['busy','error','onAction','onRefresh'])if(options[key]!==undefined)this.callbacks[key]=options[key];
            this.host=document.getElementById('game-client-canvas-host');this.dead=false;
            this.resize=()=>{if(this.sys.isActive())this.draw();};
            this.imageComplete=key=>{
                if(this.background?.key===key){this.background.state='ready';if(this.sys.isActive())this.draw();}
                else if(key.startsWith(`places-${this.serial}-`)&&this.textures.exists(key))this.textures.remove(key);
            };
            this.imageError=file=>{if(this.background?.key===file.key){this.background.state='failed';if(this.sys.isActive())this.draw();}};
            this.load.on('filecomplete',this.imageComplete);this.load.on('loaderror',this.imageError);
            this.scale.on('resize',this.resize);this.events.on('wake',this.resize);
            this.events.once('shutdown',()=>{
                this.dead=true;this.scale.off('resize',this.resize);this.events.off('wake',this.resize);
                this.load.off('filecomplete',this.imageComplete);this.load.off('loaderror',this.imageError);this.load.reset();
                this.clearView();this.releaseBackground();
            });
            this.draw();
        }
        present(model,callbacks={}) {
            if(this.model?.kind!==model?.kind || this.model?.place!==model?.place || this.model?.screen!==model?.screen){this.selected=null;this.scroll=0;this.pendingFocus=null;}
            this.model=model||{};this.callbacks={...this.callbacks,...callbacks};
            if(this.host&&this.services&&this.sys.isActive())this.draw();
        }
        releaseBackground(){if(this.background?.key&&this.textures.exists(this.background.key))this.textures.remove(this.background.key);this.background=null;}
        clearView(){for(const control of this.controls)control.destroy();this.controls=[];this.context?.remove();this.context=null;this.children.removeAll(true);}
        image(path) {
            const url=placeAssetUrl(path,location.origin);
            if(this.background?.url!==url){this.releaseBackground();if(url){this.background={url,key:`places-${this.serial}-${++this.imageSequence}`,state:'loading'};this.load.image(this.background.key,url);if(!this.load.isLoading())this.load.start();}}
            return this.background?.state==='ready'?this.background.key:null;
        }
        text(x,y,label,size=16,color=this.colors.text.css,width) {
            return this.services.components.createText(this,x,y,textValue(label),{fontSize:size,color,renderScale:this.ratio,themeHost:this.host,...(width?{wordWrap:{width,useAdvancedWrap:true}}:{})});
        }
        native(key,rect,label,onActivate,disabled=false) {
            const control=this.services.components.attachSemanticButton(this.host,{scene:this,label,rect,onActivate,disabled});
            control.element.dataset.placesControl=key;this.controls.push(control);return control;
        }
        draw() {
            const active=document.activeElement;
            const outside=active&&active!==document.body&&active!==document.documentElement&&!this.host.contains(active);
            if(outside)this.pendingFocus=null;
            const focused=this.host.contains(active)?active.dataset.placesControl:null;
            if(focused&&!this.pendingFocus)this.pendingFocus=focused;
            this.scroll=this.context?.scrollTop||this.scroll||0;this.clearView();this.colors=palette(this.host);
            const {width:w,height:h}=this.host.getBoundingClientRect();if(w<2||h<2)return;
            this.ratio=Math.max(1,this.scale.width/w);this.cameras.main.setViewport(0,0,this.scale.width,this.scale.height).setZoom(this.ratio).centerOn(w/2,h/2);
            this.add.rectangle(0,0,w,h,this.colors.bg.number).setOrigin(0);
            const key=this.image(this.model.background_url);
            let bounds=fitPlaceBackground(w,h,1920,1080);
            if(key){const source=this.textures.get(key).getSourceImage();bounds=fitPlaceBackground(w,h,source.width,source.height);const cover=Math.max(w/source.width,h/source.height);
                this.add.image(w/2,h/2,key).setScale(cover).setAlpha(.24);
                this.add.image(bounds.x,bounds.y,key).setOrigin(0).setDisplaySize(bounds.width,bounds.height);
            }else this.text(18,Math.max(92,h/2),this.background?.state==='loading'?'Загрузка помещения…':'Изображение помещения недоступно',16,this.colors.dim.css,w-36);
            const spots=placeHotspots(this.model);
            for(const spot of spots)this.hotspot(spot,bounds,Boolean(this.selected));
            this.add.rectangle(0,0,w,70,this.colors.bg.number,.92).setOrigin(0);
            this.text(18,12,this.model.title||'Помещение',22,this.colors.text.css,w-150);
            const summary=this.callbacks.error||this.model.notice||this.model.description||'';
            this.text(18,43,summary.length>155?summary.slice(0,152)+'…':summary,14,this.colors.dim.css,w-36);
            this.text(w-103,19,'Обновить',14);
            this.native('refresh',{x:w-116,y:8,width:106,height:36},'Обновить',()=>this.callbacks.onRefresh?.(),Boolean(this.callbacks.busy));
            this.text(18,h-27,this.model.unavailable||'Выберите объект помещения',14,this.colors.dim.css,w-36);
            if(!mainPlaceScreen(this.model))this.panel(null,w,h);
            else if(this.selected)this.panel(spots.find(spot=>spot.id===this.selected)||{id:'other',label:'Действия'},w,h);
            if(this.pendingFocus){const target=[...this.host.querySelectorAll('[data-places-control]')].find(node=>node.dataset.placesControl===this.pendingFocus);if(target&&!target.disabled){target.focus({preventScroll:true});this.pendingFocus=null;}else {this.context?.focus({preventScroll:true});this.pendingFocus=null;}}
        }
        hotspot(spot,bounds,disabled) {
            const center={x:bounds.x+spot.point[0]*bounds.width,y:bounds.y+spot.point[1]*bounds.height};
            const points=(spot.poly || [[spot.point[0]-.07,spot.point[1]-.06],[spot.point[0]+.07,spot.point[1]-.06],[spot.point[0]+.07,spot.point[1]+.06],[spot.point[0]-.07,spot.point[1]+.06]]).map(([x,y])=>({x:bounds.x+x*bounds.width,y:bounds.y+y*bounds.height}));
            const x=Math.min(...points.map(p=>p.x)),y=Math.min(...points.map(p=>p.y)),width=Math.max(...points.map(p=>p.x))-x,height=Math.max(...points.map(p=>p.y))-y;
            const glow=this.add.graphics();
            const paint=on=>{glow.clear();if(on)glow.fillStyle(this.colors.accent.number,.10).fillPoints(points,true).lineStyle(3,this.colors.accent.number,.8).strokePoints(points,true).lineStyle(10,this.colors.accent.number,.08).strokePoints(points,true);};
            this.add.rectangle(center.x,center.y,Math.min(190,Math.max(85,spot.label.length*8)),32,this.colors.bg.number,.86);
            this.text(center.x,center.y,spot.label,16,this.colors.text.css).setOrigin(.5);
            const button=this.native('spot-'+spot.id,{x,y,width,height},spot.label,()=>{this.selected=spot.id;this.scroll=0;this.pendingFocus='panel';this.draw();},disabled);
            button.element.style.clipPath='polygon('+points.map(p=>`${(p.x-x)/width*100}% ${(p.y-y)/height*100}%`).join(',')+')';
            button.element.addEventListener('pointerenter',()=>paint(true));button.element.addEventListener('pointerleave',()=>paint(false));button.element.addEventListener('focus',()=>paint(true));button.element.addEventListener('blur',()=>paint(false));
        }
        panel(spot,w,h) {
            const modal=this.host.ownerDocument.createElement('section');this.context=modal;modal.tabIndex=-1;modal.dataset.placesControl='panel';modal.setAttribute('role','dialog');modal.setAttribute('aria-modal','true');modal.setAttribute('aria-label',spot?.label||this.model.title||'Действия');modal.setAttribute('aria-busy',String(Boolean(this.callbacks.busy)));
            const width=Math.min(600,w-32),height=Math.max(50,h-108);
            Object.assign(modal.style,{position:'absolute',left:(w-width)/2+'px',top:'82px',width:width+'px',maxHeight:height+'px',boxSizing:'border-box',overflowY:'auto',padding:'20px',background:'var(--col-bg-surface)',border:'1px solid var(--col-accent)',color:'var(--col-text-primary)',font:'16px var(--font-ui)',lineHeight:'1.45',scrollbarWidth:'thin'});
            const append=(tag,text)=>{const node=modal.ownerDocument.createElement(tag);node.textContent=textValue(text);node.style.margin='0 0 12px';modal.append(node);return node;};
            append('h2',spot?.label||this.model.title);
            const description=spot?.description||(!spot?this.model.description:'');if(description)append('p',description);
            if(this.model.notice)append('p',this.model.notice);
            if(this.callbacks.error){const alert=append('p',this.callbacks.error);alert.setAttribute('role','alert');}
            if(this.model.unavailable)append('p',this.model.unavailable);
            if(spot?.id==='npc'&&this.model.npc){const npc=this.model.npc;append('p',[npc.name,npc.role].filter(Boolean).join(' · '));const url=placeAssetUrl(npc.portrait_url,location.origin);if(url){const image=modal.ownerDocument.createElement('img');image.src=url;image.alt=npc.name||'';image.loading='lazy';Object.assign(image.style,{width:'96px',height:'96px',objectFit:'contain'});modal.append(image);}}
            for(const detail of this.model.details||[])append('p',[detail.label,detail.value].filter(v=>v!=null&&v!=='').map(placeValue).join(': '));
            const actions=spot?actionsForPlace(this.model,spot.id):visibleActions(this.model);
            if(!actions.length||actions.every(action=>action.enabled===false))append('p','Сейчас недоступно');
            for(const action of actions){const button=append('button',action.label);button.type='button';button.dataset.placesControl='action-'+action.id;button.disabled=action.enabled===false||Boolean(this.callbacks.busy)||Boolean(this.callbacks.error);Object.assign(button.style,{display:'block',width:'100%',margin:'10px 0 0',padding:'12px',textAlign:'left',color:'var(--col-text-primary)',background:'var(--col-bg-darker)',border:'1px solid var(--col-border)',font:'inherit'});button.addEventListener('click',()=>this.callbacks.onAction?.(action.id));}
            const close=()=>{this.selected=null;this.pendingFocus='spot-'+spot?.id;this.scroll=0;this.draw();};
            if(spot){const button=append('button','Закрыть');button.type='button';button.style.marginTop='16px';button.addEventListener('click',close);}
            modal.addEventListener('keydown',event=>{if(event.key==='Escape'&&spot){event.preventDefault();close();}if(event.key==='Tab'){const items=[...modal.querySelectorAll('button:not(:disabled)')];if(!items.length){event.preventDefault();modal.focus();return;}const first=items[0],last=items.at(-1);if(event.shiftKey&&(document.activeElement===first||document.activeElement===modal)){event.preventDefault();last.focus();}else if(!event.shiftKey&&(document.activeElement===last||document.activeElement===modal)){event.preventDefault();first.focus();}}});
            this.host.append(modal);modal.scrollTop=this.scroll;
            const sleep=()=>{modal.hidden=true;},wake=()=>{modal.hidden=false;};this.events.on('sleep',sleep);this.events.on('wake',wake);const remove=modal.remove.bind(modal);modal.remove=()=>{this.events.off('sleep',sleep);this.events.off('wake',wake);remove();};
        }
    };
}
