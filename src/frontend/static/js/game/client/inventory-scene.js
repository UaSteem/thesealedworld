/* Authoritative inventory presentation: no equipment, quantity or action simulation. */
export function packInventoryRows(rows, columns) {
    if (!Number.isInteger(columns) || columns < 1) throw new RangeError('Invalid inventory columns');
    const occupied = new Set(), placements = [];
    let maxRow = 0;
    for (const item of rows) {
        const width = Math.max(1, Math.min(columns, Math.floor(Number(item.grid_w) || 1)));
        const height = Math.max(1, Math.min(8, Math.floor(Number(item.grid_h) || 1)));
        let row = 0, col = 0, found = false;
        while (!found) {
            for (col = 0; col <= columns - width; col++) {
                let free = true;
                for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) if (occupied.has(`${row+y}:${col+x}`)) free = false;
                if (free) {found = true; break;}
            }
            if (!found) row++;
        }
        for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) occupied.add(`${row+y}:${col+x}`);
        placements.push({item,row,col,width,height});maxRow = Math.max(maxRow,row+height);
    }
    return {placements,rows:maxRow};
}

export function inventoryItemActions(item, canAct) {
    return (item?.details?.actions || []).map(action => ({action:action.action,label:action.label,
        enabled:Boolean(canAct && action.enabled),reason:action.reason || null,
        item_id:item.item_id,slot_id:action.slot_id || null}));
}

export function inventoryDetailLines(details) {
    if (!details) return [];
    const result = [];
    const add = (text,tone='neutral') => {if(text)result.push({text:String(text),tone});};
    add(details.description);add(details.flavor);
    if (details.item_type_label) add(details.item_type_label);
    if (details.rarity_label) add(details.rarity_label);
    for (const group of ['details','affixes','comparison']) for (const line of details[group] || []) add(`${line.label}: ${line.value}`,line.tone);
    for (const group of ['effects','tags']) for (const line of details[group] || []) add(line.label,line.tone);
    for (const line of details.requirements || []) add(`${line.label}: ${line.value}${line.current != null ? ` · сейчас ${line.current}` : ''}`,line.met?'positive':'negative');
    for (const line of details.meta || []) add(`${line.label}: ${line.value}`);
    return result;
}

/** A redraw owns focus only when its outgoing native control owned it. */
export function captureInventoryFocus(host) {
    const active = host.ownerDocument.activeElement;
    return {owned:Boolean(host.contains(active) && active?.dataset?.inventoryControl),key:active?.dataset?.inventoryControl || null};
}
export function restoreInventoryFocus(host, state) {
    if (!state?.owned) return false;
    const current = host.ownerDocument.activeElement;
    if (current && current !== host.ownerDocument.body && !host.contains(current)) return false;
    const controls = [...host.querySelectorAll('[data-inventory-control]')].filter(element => !element.disabled && !element.hidden);
    const target = controls.find(element => element.dataset.inventoryControl === state.key)
        || controls.find(element => element.dataset.inventoryControl === 'inventory-close');
    target?.focus({preventScroll:true});return Boolean(target);
}

let sceneSequence = 0;
export function createInventoryScene(P) {
    return class InventoryClientScene extends P.Scene {
        constructor() {super({key:'InventoryClientScene'});this._prefix=`inventory-client-${++sceneSequence}-`;}
        create(options = {}) {
            this.services = options.services;this.model = options.model;this.callbacks = options;
            this.host = options.host || document.getElementById('game-client-canvas-host');
            this.controls=[];this.masks=[];this.imageKeys=new Map();this.failedImages=new Set();
            this.scroll=0;this.detailScroll=0;this.selected=null;this.view='bag';this.dead=false;
            this._onResize=()=>this.draw();
            this._onImage=()=>this.scheduleDraw();
            this._onImageError=file=>{this.failedImages.add(file.key);this.scheduleDraw();};
            this._onWheel=event=>{if(!this.scene.isActive())return;event.preventDefault();this.scrollBy(event.deltaY);};
            this._onKey=event=>{
                if(!this.scene.isActive())return;
                if(event.key==='Escape') {if(!this.dismissDetail())this.callbacks.onClose?.();}
                else if(['PageDown','PageUp'].includes(event.key)){event.preventDefault();this.scrollBy(event.key==='PageDown'?180:-180);}
            };
            this.scale.on('resize',this._onResize);
            this.load.on('filecomplete',this._onImage);this.load.on('loaderror',this._onImageError);
            this.host.addEventListener('wheel',this._onWheel,{passive:false});this.input.keyboard?.on('keydown',this._onKey);
            this.events.once('shutdown',()=>this.cleanup());
            this.draw();
        }
        present(model, callbacks = {}) {
            this.model=model;this.callbacks={...this.callbacks,...callbacks};
            if(this.selected) this.selected=this.findItem(this.selected.item_id);
            this.draw();
        }
        findItem(id) {
            return [...(this.model?.visible_rows||[]),...this.equipment().filter(slot=>slot.item).map(slot=>this.slotItem(slot))].find(item=>item.item_id===id)||null;
        }
        equipment() {
            const model=this.model||{},slots=[];
            for(const zone of model.body_zones||[]) {if(zone.primary_slot)slots.push(zone.primary_slot);if(zone.secondary_slot)slots.push(zone.secondary_slot);}
            slots.push(...(model.weapon_slots||[]));
            for(const row of model.accessory_rows||[])slots.push(...(row.slots||[]));
            slots.push(...(model.quick_slots||[]));
            return slots;
        }
        slotItem(slot) {return {...slot.item,item_id:slot.item.item_id,details:slot.details,name:slot.item.name};}
        safeImage(url) {
            if(!url)return null;
            try {const value=new URL(url,location.href);return value.origin===location.origin&&['http:','https:'].includes(value.protocol)?value.href:null;}catch{return null;}
        }
        prepareImages(items) {
            if(this.dead)return;
            let queued=false;
            for(const item of items) {
                const url=this.safeImage(item.thumbnail_url||item.details?.thumbnail_url||item.image_url||item.details?.image_url);
                if(!url||this.imageKeys.has(url))continue;
                const key=this._prefix+this.imageKeys.size;this.imageKeys.set(url,key);this.load.image(key,url);queued=true;
            }
            if(queued&&!this.load.isLoading())this.load.start();
        }
        scheduleDraw() {if(this.dead||this._frame)return;this._frame=requestAnimationFrame(()=>{this._frame=0;if(!this.dead)this.draw();});}
        cleanup() {
            this.dead=true;cancelAnimationFrame(this._frame);
            this.scale.off('resize',this._onResize);this.host.removeEventListener('wheel',this._onWheel);this.input.keyboard?.off('keydown',this._onKey);
            this.load.off('filecomplete',this._onImage);this.load.off('loaderror',this._onImageError);this.load.reset();
            this.clearView();
            for(const key of this.imageKeys.values())if(this.textures.exists(key))this.textures.remove(key);
        }
        clearView() {
            for(const control of this.controls||[])control.destroy();this.controls=[];
            for(const mask of this.masks||[])mask.destroy();this.masks=[];
            this.children.removeAll(true);
        }
        theme() {
            const style=getComputedStyle(this.host),probe=document.createElement('span');this.host.append(probe);
            const read=(token,fallback)=>{
                probe.style.color=`var(${token}, ${fallback})`;
                const css=getComputedStyle(probe).color,channels=css.match(/[\d.]+/g)?.slice(0,3).map(Number)||[32,43,54];
                return {css,number:(channels[0]<<16)+(channels[1]<<8)+channels[2]};
            };
            const result={};for(const [name,token,fallback]of [['bg','--col-bg-base','#202b36'],['panel','--col-bg-surface','#303e4b'],['cell','--col-bg-darker','#24323e'],['line','--col-border','#617382'],['accent','--col-accent','#dfb980'],['text','--col-text-primary','#f1e9db'],['dim','--col-text-dim','#bcc8d0'],['positive','--col-success','#76b995'],['negative','--col-danger','#d87568']])result[name]=read(token,fallback);
            result.tiers=Array.from({length:8},(_,index)=>read(`--r${index}`,'#dfb980'));
            probe.remove();return result;
        }
        text(x,y,value,size=14,color=this.t.text.css,width) {
            return this.services.components.createText(this,x,y,value,{fontSize:size,color,renderScale:this.ratio,themeHost:this.host,wordWrap:width?{width,useAdvancedWrap:true}:undefined});
        }
        box(x,y,w,h,fill=this.t.panel.number,line=this.t.line.number) {
            return this.add.graphics().fillStyle(fill).fillRoundedRect(x,y,w,h,5).lineStyle(1,line,.85).strokeRoundedRect(x+.5,y+.5,w-1,h-1,5);
        }
        button(x,y,w,h,label,callback,disabled=false,active=false,accessibleLabel=label,focusKey=`button:${accessibleLabel}`) {
            this.box(x,y,w,h,active?this.t.cell.number:this.t.panel.number,active?this.t.accent.number:this.t.line.number);
            const caption=this.text(x+w/2,y+h/2,label,13,disabled?this.t.dim.css:this.t.text.css,Math.max(20,w-18));caption.setOrigin(.5);
            const control=this.services.components.attachSemanticButton(this.host,{scene:this,label:accessibleLabel,rect:{x,y,width:w,height:h},onActivate:callback,disabled});
            control.element.dataset.inventoryControl=focusKey;
            this.controls.push(control);return control;
        }
        scrollBy(delta) {
            if(this.selected)this.detailScroll=Math.max(0,Math.min(this.detailMax||0,this.detailScroll+delta));
            else this.scroll=Math.max(0,Math.min(this.maxScroll||0,this.scroll+delta));
            this.draw();
        }
        select(item) {
            const focus=captureInventoryFocus(this.host);this._returnFocusKey=focus.key||`item:${item.item_id}`;
            this.selected=item;this.detailScroll=0;this._requestedFocus={owned:focus.owned,key:'detail-close'};this.draw();
        }
        dismissDetail() {
            if(!this.selected)return false;
            const focus=captureInventoryFocus(this.host);this.selected=null;
            this._requestedFocus={owned:focus.owned,key:this._returnFocusKey||'inventory-close'};this.draw();return true;
        }
        draw() {
            if(this.dead||!this.services||!this.host)return;
            const focus=this._requestedFocus||captureInventoryFocus(this.host);this._requestedFocus=null;
            this.clearView();this.t=this.theme();
            const rect=this.host.getBoundingClientRect();this.w=Math.max(1,rect.width);this.h=Math.max(1,rect.height);this.ratio=this.scale.width/this.w;
            this.cameras.main.setViewport(0,0,this.scale.width,this.scale.height).setZoom(this.ratio).centerOn(this.w/2,this.h/2).setBackgroundColor(this.t.bg.number);
            const pad=20,w=this.w,h=this.h,disabled=Boolean(this.selected||this.callbacks.busy);
            this.text(pad,18,this.model?.title||'Инвентарь',25,this.t.accent.css);
            this.button(w-118,16,98,32,'Закрыть',()=>this.callbacks.onClose?.(),Boolean(this.callbacks.busy),false,'Закрыть','inventory-close');
            if(!this.model) {this.text(pad,75,'Данные инвентаря недоступны',17);restoreInventoryFocus(this.host,focus);return;}
            const tabs=this.model.tabs||[],tabY=62,tabW=Math.min(180,(w-170-pad*2)/Math.max(1,tabs.length));
            tabs.forEach((tab,index)=>this.button(pad+index*(tabW+4),tabY,tabW-4,34,tab.label,()=>{this.scroll=0;this.callbacks.onTab?.(tab.tab_id);},disabled,tab.is_active&&this.view==='bag'));
            this.button(w-156,tabY,136,34,'Экипировка',()=>{this.view=this.view==='gear'?'bag':'gear';this.scroll=0;this.draw();},disabled,this.view==='gear');
            this.noticeY=106;
            if(this.model.can_act===false||this.callbacks.notice) this.text(pad,this.noticeY,this.callbacks.notice||this.model.forbidden_reason||'Действия сейчас недоступны',13,this.t.negative.css,w-40);
            this.gridY=137;const viewportH=Math.max(40,h-this.gridY-55);
            if(this.view==='gear')this.drawEquipment(pad,this.gridY,w-pad*2,viewportH,disabled);
            else this.drawBag(pad,this.gridY,w-pad*2,viewportH,disabled);
            const stats=this.model.stats||{},parts=[];
            if(stats.current_weight!=null&&stats.max_weight!=null)parts.push(`Вес: ${stats.current_weight} / ${stats.max_weight}`);
            if(stats.slots_used!=null&&stats.slots_total!=null)parts.push(`Места: ${stats.slots_used} / ${stats.slots_total}`);
            this.text(pad,h-34,parts.join('     '),13,this.t.dim.css,w-40);
            if(this.callbacks.busy)this.text(w-170,h-34,'Обновление…',13,this.t.accent.css);
            if(this.selected)this.drawDetails(this.selected);
            restoreInventoryFocus(this.host,focus);
        }
        drawBag(x,y,width,height,disabled) {
            const columns=Math.max(2,Math.floor((width+5)/62)),cell=(width-(columns-1)*5)/columns,step=cell+5;
            const packed=packInventoryRows(this.model.visible_rows||[],columns);
            this.maxScroll=Math.max(0,packed.rows*step-5-height);this.scroll=Math.max(0,Math.min(this.scroll,this.maxScroll));
            const clip=this.make.graphics({x:0,y:0,add:false}).fillRect(x,y,width,height),mask=clip.createGeometryMask();this.masks.push(mask,clip);
            const content=this.add.container(0,0).setMask(mask);
            const visibleRows=Math.ceil(height/step)+1,start=Math.floor(this.scroll/step);
            for(let row=start;row<start+visibleRows;row++)for(let col=0;col<columns;col++)content.add(this.box(x+col*step,y+row*step-this.scroll,cell,cell,this.t.cell.number));
            const visibleItems=[];
            for(const place of packed.placements){
                const px=x+place.col*step,py=y+place.row*step-this.scroll,pw=place.width*step-5,ph=place.height*step-5,item=place.item;
                if(py+ph<y||py>y+height)continue;
                visibleItems.push(item);
                const rarity=Number.isInteger(item.rarity_tier)?this.t.tiers[Math.max(0,Math.min(7,item.rarity_tier))]:this.t.accent;
                content.add(this.box(px,py,pw,ph,this.t.panel.number,rarity.number));
                const url=this.safeImage(item.thumbnail_url||item.details?.thumbnail_url||item.image_url||item.details?.image_url),key=this.imageKeys.get(url);
                if(key&&this.textures.exists(key)){
                    const image=this.add.image(px+pw/2,py+ph/2,key);const fit=this.services.components.fitAspect(image.width,image.height,Math.max(1,pw-10),Math.max(1,ph-28));image.setDisplaySize(fit.width,fit.height);content.add(image);
                }else content.add(this.text(px+8,py+9,item.name,12,this.t.text.css,Math.max(20,pw-16)));
                if(Number.isInteger(item.rarity_tier))content.add(this.text(px+7,py+ph-18,`T${item.rarity_tier}`,10,rarity.css));
                if(item.quantity>1)content.add(this.text(px+pw-8,py+ph-18,`×${item.quantity}`,11,this.t.accent.css).setOrigin(1,0));
                if(item.is_unsecured)content.add(this.text(px+7,py+7,'Не закреплён',10,this.t.negative.css,Math.max(20,pw-14)));
                const top=Math.max(y,py),bottom=Math.min(y+height,py+ph);
                const control=this.services.components.attachSemanticButton(this.host,{scene:this,label:item.name||item.item_id,rect:{x:px,y:top,width:pw,height:Math.max(1,bottom-top)},disabled,onActivate:()=>this.select(item)});control.element.dataset.inventoryControl=`item:${item.item_id}`;this.controls.push(control);
            }
            this.prepareImages(visibleItems);
            if(!packed.placements.length)this.text(x+20,y+24,'В этой категории нет предметов',17,this.t.dim.css,width-40);
            if(this.maxScroll)this.drawScroll(x+width-3,y,height,height/(packed.rows*step),this.scroll/this.maxScroll);
        }
        drawScroll(x,y,height,fraction,position) {
            const thumb=Math.max(18,height*fraction);this.add.graphics().fillStyle(this.t.line.number,.3).fillRoundedRect(x,y,3,height,1).fillStyle(this.t.accent.number,.8).fillRoundedRect(x,y+(height-thumb)*position,3,thumb,1);
        }
        drawEquipment(x,y,width,height,disabled) {
            const slots=this.equipment(),cols=Math.max(1,Math.floor(width/240)),gap=8,rowH=66,slotW=(width-(cols-1)*gap)/cols;
            this.maxScroll=Math.max(0,Math.ceil(slots.length/cols)*(rowH+gap)-height);this.scroll=Math.max(0,Math.min(this.scroll,this.maxScroll));
            for(const [index,slot]of slots.entries()){
                const sx=x+(index%cols)*(slotW+gap),sy=y+Math.floor(index/cols)*(rowH+gap)-this.scroll;
                if(sy<y||sy+rowH>y+height)continue;
                this.box(sx,sy,slotW,rowH);this.text(sx+10,sy+8,slot.label||slot.slot_id,12,this.t.accent.css,slotW-20);
                this.text(sx+10,sy+30,slot.item?.name||'Пусто',13,this.t.text.css,slotW-20);
                const control=this.services.components.attachSemanticButton(this.host,{scene:this,label:`${slot.label||slot.slot_id}: ${slot.item?.name||'Пусто'}`,rect:{x:sx,y:sy,width:slotW,height:rowH},disabled:disabled||!slot.item,onActivate:()=>this.select(this.slotItem(slot))});control.element.dataset.inventoryControl=`slot:${slot.slot_id}`;this.controls.push(control);
            }
            if(!slots.length)this.text(x+20,y+24,'Данные экипировки недоступны',17,this.t.dim.css,width-40);
        }
        drawDetails(item) {
            const w=Math.min(420,this.w-40),h=Math.max(220,this.h-32),x=this.w-w-16,y=16,pad=18;
            this.add.graphics().fillStyle(this.t.bg.number,.75).fillRect(0,0,this.w,this.h);
            this.box(x,y,w,h,this.t.cell.number,this.t.accent.number);
            this.text(x+pad,y+pad,item.name||item.item_id,20,this.t.accent.css,w-72);
            this.button(x+w-48,y+10,34,30,'×',()=>this.dismissDetail(),false,false,'Закрыть описание','detail-close');
            const actions=inventoryItemActions(item,this.model.can_act&&!this.callbacks.busy),actionH=34,gap=6,actionsH=actions.length*(actionH+gap),bodyY=y+72,bodyH=Math.max(45,h-92-actionsH);
            const clip=this.make.graphics({x:0,y:0,add:false}).fillRect(x+pad,bodyY,w-pad*2,bodyH),mask=clip.createGeometryMask();this.masks.push(mask,clip);
            const body=this.add.container(0,0).setMask(mask);let cursor=bodyY-this.detailScroll;
            const lines=inventoryDetailLines(item.details);
            if(!item.details)lines.push({text:'Подробные данные предмета недоступны',tone:'neutral'});
            if(item.is_unsecured)lines.unshift({text:'Предмет ещё не закреплён',tone:'negative'});
            for(const line of lines){const label=this.text(x+pad,cursor,line.text,13,this.t[line.tone]?.css||this.t.text.css,w-pad*2);body.add(label);cursor+=label.height+8;}
            this.detailMax=Math.max(0,cursor+this.detailScroll-bodyY-bodyH);this.detailScroll=Math.max(0,Math.min(this.detailScroll,this.detailMax));
            if(this.detailMax)this.drawScroll(x+w-8,bodyY,bodyH,bodyH/(bodyH+this.detailMax),this.detailScroll/this.detailMax);
            actions.forEach((action,index)=>this.button(x+pad,y+h-actionsH-12+index*(actionH+gap),w-pad*2,actionH,action.reason?`${action.label} · ${action.reason}`:action.label,()=>this.callbacks.onAction?.({action:action.action,item_id:action.item_id,slot_id:action.slot_id}),!action.enabled,false,action.reason?`${action.label} · ${action.reason}`:action.label,`action:${action.item_id}:${action.action}:${action.slot_id||''}`));
        }
    };
}
