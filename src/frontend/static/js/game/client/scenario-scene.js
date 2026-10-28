/* Scenario presentation only. Choices and context come from the server snapshot. */
const scalar = value => typeof value === 'string' || typeof value === 'boolean' || (typeof value === 'number' && Number.isFinite(value));
const stringValue = value => scalar(value) ? String(value) : '';

/** Keep all choices in paired rows; an odd last choice never spans both columns. */
export function layoutScenarioChoices(choices, width, {gap = 10, minHeight = 56, measure = () => 24} = {}) {
    if (!Number.isFinite(width) || width <= gap) throw new RangeError('Choice area is too narrow');
    const cellWidth = (width - gap) / 2, cells = [];
    let y = 0;
    for (let index = 0; index < choices.length; index += 2) {
        const pair = choices.slice(index, index + 2);
        const height = Math.max(minHeight, ...pair.map(choice => Math.max(0, measure(String(choice.label ?? ''), cellWidth - 32)) + 28));
        pair.forEach((choice, column) => cells.push({...choice, x: column * (cellWidth + gap), y, width: cellWidth, height}));
        y += height + gap;
    }
    return {cells, height: Math.max(0, y - gap), cellWidth};
}

/** Scalar zero/false are real values. No relationship, timer or quest value is fabricated. */
export function scenarioContextLines(model) {
    const lines = [];
    const add = (text, heading = false, percent) => {if (scalar(text) && String(text).trim()) lines.push({text:String(text), heading, ...(Number.isFinite(percent) ? {percent} : {})});};
    const group = (title, values) => {const accepted = (values || []).filter(scalar);if(accepted.length){add(title,true);accepted.forEach(value=>add(value));}};
    group('Состояние', model?.status_bar);group('Сообщения', model?.system_messages);
    const extra = model?.extra_data || {}, reputation = extra.reputation;
    if (reputation && (scalar(reputation.npc) || scalar(reputation.faction))) {
        add('Отношение',true);
        if(scalar(reputation.npc))add(`NPC: ${reputation.npc}`);
        if(scalar(reputation.faction))add(`Фракция: ${reputation.faction}`);
    }
    if(scalar(extra.npc_reputation))add(`Репутация NPC: ${extra.npc_reputation}`);
    if(scalar(extra.npc_affinity))add(`Отношение NPC: ${extra.npc_affinity}`);
    for(const widget of extra.right_panel?.widgets || []) {
        if(widget.visible === false || String(widget.title || '').toLowerCase()==='scenario')continue;
        const content=[];
        if(['key_value','list','meter_list'].includes(widget.type)) {
            for(const item of widget.items || []) {
                if(['quest','node','step','phase','quest_key','node_key'].includes(String(item?.key ?? item?.label ?? '').toLowerCase()))continue;
                if(scalar(item)){content.push({text:String(item)});continue;}
                const label=stringValue(item?.label ?? item?.key),value=stringValue(item?.display_value ?? item?.value);
                if(label || value)content.push({text:label && value ? `${label}: ${value}` : label || value, percent:widget.type==='meter_list' ? item?.percent : undefined});
            }
        }else if(widget.type==='text') {
            const value=widget.data?.text ?? widget.text;
            if(scalar(value))content.push({text:String(value)});
        }
        if(content.length){if(widget.title)add(widget.title,true);for(const line of content)add(line.text,false,line.percent);}
    }
    if(Array.isArray(extra.rewards)) {
        const rewards=extra.rewards.map(reward=>scalar(reward)?String(reward):[stringValue(reward?.label ?? reward?.name),stringValue(reward?.value ?? reward?.quantity ?? reward?.amount)].filter(Boolean).join(' · ')).filter(Boolean);
        group('Награды',rewards);
    }
    return lines;
}

function themeColors(host) {
    const probe=host.ownerDocument.createElement('span');host.append(probe);
    const colors={};
    for(const [name,token] of Object.entries({bg:'--col-bg-base',panel:'--col-bg-surface',cell:'--col-bg-darker',line:'--col-border',accent:'--col-accent',text:'--col-text-primary',dim:'--col-text-dim'})) {
        probe.style.color=`var(${token})`;
        const css=getComputedStyle(probe).color,channels=css.match(/[\d.]+/g)?.slice(0,3).map(Number) || [20,24,30];
        colors[name]={css,number:(channels[0]<<16)+(channels[1]<<8)+channels[2]};
    }
    probe.remove();return colors;
}

export function createScenarioScene(P) {
    return class ScenarioClientScene extends P.Scene {
        constructor(){super({key:'GameClientScenario'});this.storyScroll=0;this.choiceScroll=0;this.contextScroll=0;this.controls=[];this.masks=[];this.regions=[];}
        create(options = {}) {
            this.services=options.services || this.services;this.model=options.model || this.model || {};
            this.callbacks={...this.callbacks};
            for(const key of ['onChoose','busy','error','onRefresh'])if(options[key]!==undefined)this.callbacks[key]=options[key];
            this.host=document.getElementById('game-client-canvas-host');this.dead=false;
            this.resizeHandler=()=>{if(this.sys.isActive())this.draw();};
            this.wheelHandler=event=>{
                if(!this.sys.isActive())return;
                const rect=this.host.getBoundingClientRect(),x=event.clientX-rect.left,y=event.clientY-rect.top;
                const area=Object.entries(this.areas || {}).find(([,r])=>x>=r.x&&x<=r.x+r.width&&y>=r.y&&y<=r.y+r.height)?.[0];
                if(area && this.scrollLimits?.[area]>0){event.preventDefault();this.moveScroll(area,event.deltaY);}
            };
            this.keyHandler=event=>{
                if(!this.sys.isActive())return;
                const area=event.target.closest?.('[data-scenario-area]')?.dataset.scenarioArea || 'story';
                const viewport=this.areas?.[area];
                const movement={ArrowDown:42,ArrowUp:-42,PageDown:viewport?.height,PageUp:-(viewport?.height || 0),Home:-Infinity,End:Infinity}[event.key];
                if(movement!==undefined){event.preventDefault();this.moveScroll(area,movement);}
            };
            this.scale.on('resize',this.resizeHandler);this.events.on('wake',this.resizeHandler);
            this.host.addEventListener('wheel',this.wheelHandler,{passive:false});this.host.addEventListener('keydown',this.keyHandler);
            this.events.once('shutdown',()=>{
                this.dead=true;cancelAnimationFrame(this.frame);
                this.scale.off('resize',this.resizeHandler);this.events.off('wake',this.resizeHandler);
                this.host.removeEventListener('wheel',this.wheelHandler);this.host.removeEventListener('keydown',this.keyHandler);
                this.clearView();
            });
            this.draw();
        }
        present(model, callbacks={}) {
            const changed=this.model?.node_key!==model?.node_key || this.model?.char_id!==model?.char_id;
            if(changed){this.storyScroll=0;this.choiceScroll=0;this.contextScroll=0;}
            this.model=model || {};this.callbacks={...this.callbacks,...callbacks};
            if(this.host && this.services && this.sys.isActive())this.draw();
        }
        clearView() {
            for(const control of this.controls || [])control.destroy();this.controls=[];
            for(const region of this.regions || [])region.remove();this.regions=[];
            for(const {mask,graphics} of this.masks || []){mask.destroy();graphics.destroy();}this.masks=[];
            this.children.removeAll(true);
        }
        mask(rect) {
            const graphics=this.make.graphics({add:false});graphics.fillStyle(0xffffff).fillRect(rect.x,rect.y,rect.width,rect.height);
            const mask=graphics.createGeometryMask();this.masks.push({mask,graphics});return mask;
        }
        text(x,y,value,size=16,color=this.palette.text.css,width) {
            return this.services.components.createText(this,x,y,value,{fontSize:size,color,renderScale:this.ratio,themeHost:this.host,
                ...(width?{wordWrap:{width,useAdvancedWrap:true}}:{})});
        }
        panel(rect) {
            this.add.rectangle(rect.x,rect.y,rect.width,rect.height,this.palette.panel.number).setOrigin(0).setStrokeStyle(1,this.palette.line.number);
            this.add.rectangle(rect.x+4,rect.y+4,rect.width-8,rect.height-8,0,0).setOrigin(0).setStrokeStyle(1,this.palette.line.number,.25);
        }
        focusRegion(area,rect,label) {
            const region=this.host.ownerDocument.createElement('div');region.tabIndex=0;region.setAttribute('role','region');region.setAttribute('aria-label',label);
            region.dataset.scenarioArea=area;region.dataset.scenarioControl='region-'+area;
            Object.assign(region.style,{position:'absolute',left:`${rect.x}px`,top:`${rect.y}px`,width:`${rect.width}px`,height:`${rect.height}px`,pointerEvents:'none',outline:'none',overflow:'hidden',color:'transparent',fontSize:'1px',whiteSpace:'pre-wrap'});
            if(area==='story')region.textContent=stringValue(this.model?.text);
            if(area==='context')region.textContent=scenarioContextLines(this.model).map(line=>line.text).join('\n');
            region.setAttribute('aria-busy',String(Boolean(this.callbacks.busy)));
            region.addEventListener('focus',()=>region.style.outline='1px solid var(--col-accent)');region.addEventListener('blur',()=>region.style.outline='none');
            this.host.append(region);this.regions.push(region);
            const sleep=()=>{region.hidden=true;},wake=()=>{region.hidden=false;};
            this.events.on('sleep',sleep);this.events.on('wake',wake);
            const remove=region.remove.bind(region);region.remove=()=>{this.events.off('sleep',sleep);this.events.off('wake',wake);remove();};
        }
        button(key,rect,label,onActivate,{disabled=false,area='choices'}={}) {
            const control=this.services.components.attachSemanticButton(this.host,{scene:this,label,rect,disabled,onActivate});
            control.element.dataset.scenarioControl=key;control.element.dataset.scenarioArea=area;this.controls.push(control);return control;
        }
        moveScroll(area,amount) {
            const property={story:'storyScroll',choices:'choiceScroll',context:'contextScroll'}[area];if(!property)return;
            const next=Math.max(0,Math.min(this.scrollLimits?.[area] || 0,this[property]+amount));
            if(next!==this[property]){this[property]=next;if(!this.frame)this.frame=requestAnimationFrame(()=>{this.frame=0;if(!this.dead&&this.sys.isActive())this.draw();});}
        }
        scrollControls(area,rect) {
            if(!this.scrollLimits[area])return;
            const property={story:'storyScroll',choices:'choiceScroll',context:'contextScroll'}[area];
            const names={story:'Текст',choices:'Ответы',context:'Сведения'},y=rect.y+rect.height+7,buttonWidth=Math.min(92,(rect.width-8)/2);
            for(const [index,[suffix,amount]] of [['выше',-Math.max(40,rect.height*.8)],['ниже',Math.max(40,rect.height*.8)]].entries()) {
                const x=rect.x+index*(buttonWidth+8),label=`${names[area]} ${suffix}`,disabled=amount<0?this[property]<=0:this[property]>=this.scrollLimits[area];
                this.add.rectangle(x,y,buttonWidth,25,this.palette.cell.number).setOrigin(0).setStrokeStyle(1,this.palette.line.number);
                this.text(x+buttonWidth/2,y+12,label,12,this.palette.dim.css).setOrigin(.5);
                this.button(`${area}-${suffix}`,{x,y,width:buttonWidth,height:25},label,()=>this.moveScroll(area,amount),{disabled,area});
            }
        }
        measure(value,width,size=16) {const text=this.text(0,0,value,size,this.palette.text.css,width).setVisible(false),height=text.height;text.destroy();return height;}
        draw() {
            if(this.dead || !this.services)return;
            const active=this.host.ownerDocument.activeElement,owned=this.host.contains(active),focus=owned?active?.dataset.scenarioControl:null,focusArea=owned?active?.dataset.scenarioArea:null;
            if(focus)this.pendingFocus={key:focus,area:focusArea};
            this.clearView();this.palette=themeColors(this.host);
            const bounds=this.host.getBoundingClientRect(),w=Math.max(1,bounds.width),h=Math.max(1,bounds.height);
            this.ratio=Math.max(1,this.scale.width/w);
            this.cameras.main.setViewport(0,0,this.scale.width,this.scale.height).setZoom(this.ratio).centerOn(w/2,h/2);
            this.add.rectangle(0,0,w,h,this.palette.bg.number).setOrigin(0);
            const model=this.model || {},pad=w<1000?18:26,gap=16,side=Math.min(290,Math.max(220,w*.24));
            const title=stringValue(model.extra_data?.quest_title) || stringValue(model.display_name) || 'Сценарий';
            this.text(pad,18,title,26,this.palette.accent.css,w-pad*2);
            if(model.speaker)this.text(pad,52,model.speaker,14,this.palette.dim.css,w-pad*2);
            let top=80;
            if(this.callbacks.error) {
                const error=typeof this.callbacks.error==='string'?this.callbacks.error:'Не удалось обновить сцену.';
                const errorWidth=Math.max(80,w-pad*2-200),height=Math.max(34,this.measure(error,errorWidth,14));
                this.text(pad,top,error,14,this.palette.accent.css,errorWidth);
                if(this.callbacks.onRefresh) {
                    const rect={x:w-pad-180,y:top,width:180,height:34};this.add.rectangle(rect.x,rect.y,rect.width,rect.height,this.palette.cell.number).setOrigin(0).setStrokeStyle(1,this.palette.line.number);
                    this.text(rect.x+90,rect.y+17,'Обновить состояние',13,this.palette.text.css).setOrigin(.5);
                    this.button('refresh',rect,'Обновить состояние',()=>this.callbacks.onRefresh?.(),{area:'story'});
                }
                top+=height+12;
            }
            const bodyHeight=Math.max(120,h-top-pad),mainWidth=Math.max(180,w-pad*2-side-gap),main={x:pad,y:top,width:mainWidth,height:bodyHeight},context={x:pad+mainWidth+gap,y:top,width:side,height:bodyHeight};
            this.panel(main);this.panel(context);
            const choices=Array.isArray(model.buttons)?model.buttons:[],innerWidth=main.width-36;
            const layout=layoutScenarioChoices(choices,innerWidth,{measure:(label,width)=>this.measure(label,width,16)});
            const choicesHeight=choices.length?Math.min(layout.height+20,Math.max(98,bodyHeight*.48)):44;
            const choiceBox={x:main.x+18,y:main.y+bodyHeight-choicesHeight-14,width:innerWidth,height:choicesHeight};
            const storyBox={x:main.x+18,y:main.y+16,width:innerWidth,height:Math.max(30,choiceBox.y-main.y-34)};
            const contextBox={x:context.x+17,y:context.y+17,width:context.width-34,height:Math.max(30,context.height-34)};
            const storyHeight=this.measure(stringValue(model.text),storyBox.width,17);
            const contextLines=scenarioContextLines(model),contextRecords=[];
            let contextHeight=0;
            for(const line of contextLines){const height=this.measure(line.text,contextBox.width,line.heading?14:15)+ (line.heading?13:10)+(Number.isFinite(line.percent)?9:0);contextRecords.push({...line,y:contextHeight,height});contextHeight+=height;}
            const storyOverflow=storyHeight>storyBox.height,choicesOverflow=layout.height>choiceBox.height-8,contextOverflow=contextHeight>contextBox.height;
            if(storyOverflow)storyBox.height=Math.max(25,storyBox.height-34);
            if(choicesOverflow)choiceBox.height=Math.max(30,choiceBox.height-34);
            if(contextOverflow)contextBox.height=Math.max(25,contextBox.height-34);
            this.areas={story:storyBox,choices:choiceBox,context:contextBox};
            this.scrollLimits={story:Math.max(0,storyHeight-storyBox.height),choices:Math.max(0,layout.height-choiceBox.height),context:Math.max(0,contextHeight-contextBox.height)};
            this.storyScroll=Math.min(this.storyScroll,this.scrollLimits.story);this.choiceScroll=Math.min(this.choiceScroll,this.scrollLimits.choices);this.contextScroll=Math.min(this.contextScroll,this.scrollLimits.context);
            this.text(storyBox.x,storyBox.y-this.storyScroll,stringValue(model.text) || 'Текст сцены не получен.',17,this.palette.text.css,storyBox.width).setMask(this.mask(storyBox));
            this.focusRegion('story',storyBox,'Текст сценария');
            const lineY=choiceBox.y-8;this.add.rectangle(main.x+18,lineY,innerWidth,1,this.palette.line.number).setOrigin(0);
            const choiceMask=this.mask(choiceBox),choiceContent=this.add.container(0,0).setMask(choiceMask);
            if(!choices.length)this.text(choiceBox.x,choiceBox.y+7,model.is_terminal?'Сцена завершена':'Нет доступных ответов',17,this.palette.dim.css,choiceBox.width);
            for(const cell of layout.cells) {
                const x=choiceBox.x+cell.x,y=choiceBox.y+cell.y-this.choiceScroll,bottom=Math.min(y+cell.height,choiceBox.y+choiceBox.height),visibleTop=Math.max(y,choiceBox.y);
                if(bottom<=visibleTop)continue;
                const graphics=this.add.graphics(),cut=7;
                const points=[{x:x+cut,y},{x:x+cell.width-cut,y},{x:x+cell.width,y:y+cut},{x:x+cell.width,y:y+cell.height-cut},{x:x+cell.width-cut,y:y+cell.height},{x:x+cut,y:y+cell.height},{x,y:y+cell.height-cut},{x,y:y+cut}];
                graphics.fillStyle(this.palette.cell.number).fillPoints(points,true).lineStyle(1,this.palette.line.number).strokePoints(points,true);
                graphics.lineStyle(1,this.palette.accent.number,.25).strokeRect(x+4,y+4,cell.width-8,cell.height-8);choiceContent.add(graphics);
                const label=String(cell.label ?? ''),caption=this.text(x+16,y+14,label,16,this.palette.text.css,cell.width-32);choiceContent.add(caption);
                const control=this.button('choice-'+cell.action_id,{x,y:visibleTop,width:cell.width,height:bottom-visibleTop},label || 'Ответ без подписи',()=>this.callbacks.onChoose?.(cell.action_id),{disabled:Boolean(this.callbacks.busy||this.callbacks.error||!label.trim())});
                control.element.addEventListener('pointerenter',()=>caption.setColor(this.palette.accent.css));control.element.addEventListener('pointerleave',()=>caption.setColor(this.palette.text.css));
            }
            this.focusRegion('choices',choiceBox,'Варианты ответа');
            const contextMask=this.mask(contextBox);
            if(!contextRecords.length)this.text(contextBox.x,contextBox.y,'Нет дополнительных сведений',15,this.palette.dim.css,contextBox.width).setMask(contextMask);
            for(const line of contextRecords) {
                const y=contextBox.y+line.y-this.contextScroll;
                if(y+line.height<contextBox.y || y>contextBox.y+contextBox.height)continue;
                this.text(contextBox.x,y,line.text,line.heading?14:15,line.heading?this.palette.accent.css:this.palette.text.css,contextBox.width).setMask(contextMask);
                if(Number.isFinite(line.percent)) {
                    const py=y+line.height-8;this.add.rectangle(contextBox.x,py,contextBox.width,3,this.palette.line.number).setOrigin(0).setMask(contextMask);
                    this.add.rectangle(contextBox.x,py,contextBox.width*Math.max(0,Math.min(100,line.percent))/100,3,this.palette.accent.number).setOrigin(0).setMask(contextMask);
                }
            }
            this.focusRegion('context',contextBox,'Сведения о сцене');
            this.scrollControls('story',storyBox);this.scrollControls('choices',choiceBox);this.scrollControls('context',contextBox);
            if(this.callbacks.busy)this.text(w-pad,h-pad+1,'Ожидаем ответ…',12,this.palette.dim.css).setOrigin(1,1);
            const document=this.host.ownerDocument,mayRestore=owned || (this.pendingFocus && document.activeElement===document.body);
            if(mayRestore && this.pendingFocus) {
                const candidates=[...this.controls.map(control=>control.element),...this.regions];
                const target=candidates.find(element=>element.dataset.scenarioControl===this.pendingFocus.key&&!element.disabled)
                    || candidates.find(element=>element.dataset.scenarioControl==='region-'+this.pendingFocus.area);
                target?.focus({preventScroll:true});
            }
        }
    };
}
