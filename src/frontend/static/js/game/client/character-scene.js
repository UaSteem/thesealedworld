/* Character inspection only. All values originate in an existing actor projection. */
const ATTRIBUTE_LABELS = {
    strength:'Сила',agility:'Ловкость',endurance:'Выносливость',intellect:'Интеллект',
    memory:'Память',mental:'Ментальность',perception:'Восприятие',projection:'Проекция',prediction:'Предвидение',
};
const TABS = [['attributes','Характеристики'],['skills','Навыки'],['builds','Билды'],['quests','Квесты']];
const provided = value => (typeof value === 'number' && Number.isFinite(value)) || (typeof value === 'string' && value.trim() !== '' && value !== 'DATA_MISSING');

/** Prefer server-labelled widgets; absent values are never converted to zero. */
export function characterRows(model, tab) {
    if (tab === 'builds') return [{unavailable:true,label:'Билды пока недоступны',value:'Управление сборками ещё не подключено.'}];
    if (tab === 'quests') {
        const rows = [];
        if (provided(model?.active_quest)) rows.push({group:'Квесты',label:'Текущий квест',value:String(model.active_quest)});
        rows.push({unavailable:true,label:'Журнал квестов пока недоступен',value:'Полный список заданий ещё не подключён.'});
        return rows;
    }
    const widgetType = tab === 'skills' ? 'skill_groups' : 'attribute_grid';
    const widget = model?.panel?.widgets?.find(item => item.type === widgetType);
    if (widget) {
        if (widget.visible === false) return [];
        return (widget.data?.groups || []).flatMap(group => (group.items || [])
            .filter(item => typeof item.label === 'string' && item.label.trim() && provided(item.value))
            .map(item => ({group:String(group.title || ''),label:item.label,value:String(item.value)})));
    }
    const values = tab === 'skills' ? model?.skills : model?.attributes;
    return Object.entries(values || {}).filter(([,value]) => provided(value)).map(([key,value]) => ({
        group:tab === 'skills'?'Навыки':'Характеристики',label:ATTRIBUTE_LABELS[key] || key,value:String(value),
    }));
}

function themeColors(host) {
    const probe = host.ownerDocument.createElement('span');
    host.append(probe);
    const colors = {};
    for (const [name,token] of Object.entries({bg:'--col-bg-base',panel:'--col-bg-surface',cell:'--col-bg-darker',line:'--col-border',accent:'--col-accent',text:'--col-text-primary',dim:'--col-text-dim'})) {
        probe.style.color = `var(${token})`;
        const css = getComputedStyle(probe).color;
        const channels = css.match(/[\d.]+/g)?.slice(0,3).map(Number);
        colors[name] = {css,number:channels?.length === 3 ? (channels[0]<<16)+(channels[1]<<8)+channels[2] : 0};
    }
    probe.remove();
    return colors;
}

export function createCharacterScene(P) {
    return class CharacterClientScene extends P.Scene {
        constructor() {super({key:'GameClientCharacter'});this.tab='attributes';this.scroll=0;this.controls=[];}
        create({services,model,onClose} = {}) {
            this.services=services;this.host=document.getElementById('game-client-canvas-host');
            this.model=model || {};this.onClose=onClose;
            this.resizeHandler=()=>{if(this.sys.isActive())this.draw();};
            this.wheelHandler=(_pointer,_objects,_dx,dy)=>this.moveScroll(dy);
            this.keyHandler=event=>{
                if(event.key==='Escape'){event.preventDefault();event.stopPropagation();this.onClose?.();return;}
                const movement={ArrowDown:42,ArrowUp:-42,PageDown:this.listHeight,PageUp:-this.listHeight,Home:-Infinity,End:Infinity}[event.key];
                if(movement!==undefined){event.preventDefault();this.moveScroll(movement);}
            };
            this.scale.on('resize',this.resizeHandler);this.events.on('wake',this.resizeHandler);
            this.input.on('wheel',this.wheelHandler);this.host.addEventListener('keydown',this.keyHandler);
            this.events.once('shutdown',()=>{
                this.scale.off('resize',this.resizeHandler);this.events.off('wake',this.resizeHandler);
                this.input.off('wheel',this.wheelHandler);this.host.removeEventListener('keydown',this.keyHandler);
                this.clearControls();
            });
            this.draw();
        }
        present(model,{onClose} = {}) {
            this.model=model || {};if(onClose)this.onClose=onClose;
            if(this.sys.isActive())this.draw();
        }
        clearControls() {for(const control of this.controls)control.destroy();this.controls=[];}
        moveScroll(amount) {
            const next=Math.max(0,Math.min(this.maxScroll || 0,this.scroll+amount));
            if(next!==this.scroll){this.scroll=next;this.draw();}
        }
        text(x,y,label,size=15,color=this.palette.text.css,width) {
            return this.services.components.createText(this,x,y,label,{fontSize:size,color,renderScale:this.ratio,
                themeHost:this.host,...(width ? {wordWrap:{width,useAdvancedWrap:true}} : {})});
        }
        panel(x,y,width,height) {
            this.add.rectangle(x,y,width,height,this.palette.panel.number).setOrigin(0).setStrokeStyle(1,this.palette.line.number);
            if(width>12&&height>12)this.add.rectangle(x+4,y+4,width-8,height-8,0,0).setOrigin(0).setStrokeStyle(1,this.palette.line.number,.3);
        }
        button(x,y,width,height,label,callback,active=false,disabled=false) {
            this.add.rectangle(x,y,width,height,active?this.palette.cell.number:this.palette.panel.number)
                .setOrigin(0).setStrokeStyle(1,active?this.palette.accent.number:this.palette.line.number);
            this.text(x+width/2,y+height/2,label,14,active?this.palette.accent.css:this.palette.text.css).setOrigin(.5);
            this.controls.push(this.services.components.attachSemanticButton(this.host,{label,rect:{x,y,width,height},scene:this,
                disabled,onActivate:callback}));
        }
        draw() {
            if(!this.host?.isConnected || !this.services?.components)return;
            const previousFocus=this.host.contains(document.activeElement)?document.activeElement?.getAttribute('aria-label'):null;
            this.clearControls();this.children.removeAll(true);this.palette=themeColors(this.host);
            const rect=this.host.getBoundingClientRect(),w=Math.max(1,rect.width),h=Math.max(1,rect.height);
            this.ratio=Math.max(1,this.scale.width/w);
            this.cameras.main.setViewport(0,0,this.scale.width,this.scale.height).setZoom(this.ratio).centerOn(w/2,h/2);
            this.add.rectangle(0,0,w,h,this.palette.bg.number).setOrigin(0);
            const pad=w<1000?18:28,compact=w<900,header=compact?76:84;
            this.text(pad,18,'Персонаж',27,this.palette.accent.css);
            this.text(pad,53,'Характеристики и развитие',14,this.palette.dim.css);
            this.button(w-pad-112,20,112,36,'Закрыть',()=>this.onClose?.());
            const gap=8,tabW=(w-pad*2-gap*3)/4;
            for(const [index,[id,label]] of TABS.entries())this.button(pad+index*(tabW+gap),header,tabW,36,label,()=>{this.tab=id;this.scroll=0;this.draw();},this.tab===id);
            const top=header+52,bottom=h-pad,bodyHeight=Math.max(40,bottom-top),side=compact?210:260;
            const mainX=pad+side+18,mainWidth=Math.max(40,w-mainX-pad);
            this.panel(pad,top,side,bodyHeight);this.panel(mainX,top,mainWidth,bodyHeight);
            const bio=this.model.bio || {},sx=pad+16,sw=side-32;
            this.text(sx,top+19,provided(bio.name)?String(bio.name):'Имя не получено',22,this.palette.accent.css,sw);
            let summaryY=top+78;
            for(const [key,label] of [['hp','Здоровье'],['energy','Энергия'],['stamina','Стамина']]) {
                const vital=this.model.vitals?.[key];
                this.text(sx,summaryY,label,13,this.palette.dim.css);
                const value=provided(vital?.cur)&&provided(vital?.max)?`${vital.cur} / ${vital.max}`:'Нет данных';
                this.text(sx+sw,summaryY+20,value,15,this.palette.text.css).setOrigin(1,0);summaryY+=54;
            }
            if(provided(this.model.metrics?.gear_score)&&summaryY+38<bottom){
                this.text(sx,summaryY,'Сила снаряжения',13,this.palette.dim.css);
                this.text(sx+sw,summaryY+20,String(this.model.metrics.gear_score),17,this.palette.accent.css).setOrigin(1,0);
            }
            const rows=characterRows(this.model,this.tab),rowHeight=48;
            const listTop=top+22,listBottom=bottom-58,listHeight=Math.max(0,listBottom-listTop);
            this.listHeight=listHeight;this.maxScroll=Math.max(0,rows.length*rowHeight-listHeight);
            this.scroll=Math.min(this.scroll,this.maxScroll);
            if(!rows.length)this.text(mainX+18,listTop,'Данные этого раздела не получены',16,this.palette.dim.css,mainWidth-36);
            for(let index=0;index<rows.length;index++){
                const y=listTop+index*rowHeight-this.scroll;
                if(y<listTop||y+rowHeight>listBottom)continue;
                const row=rows[index],x=mainX+18,inner=mainWidth-36;
                this.add.rectangle(x,y+rowHeight-1,inner,1,this.palette.line.number,.5).setOrigin(0);
                if(row.unavailable){
                    this.text(x,y,row.label,16,this.palette.accent.css,inner);
                    this.text(x,y+24,row.value,12,this.palette.dim.css,inner);
                }else{
                    const labelWidth=Math.max(40,inner*.68);
                    this.text(x,y,row.label,15,this.palette.text.css,labelWidth);
                    if(row.group)this.text(x,y+24,row.group,11,this.palette.dim.css,labelWidth);
                    this.text(x+inner,y,row.value,17,this.palette.accent.css,inner*.28).setOrigin(1,0);
                }
            }
            if(this.maxScroll>0){
                const y=bottom-42;
                this.button(mainX+18,y,86,28,'Выше',()=>this.moveScroll(-Math.max(rowHeight,listHeight)),false,this.scroll===0);
                this.button(mainX+112,y,86,28,'Ниже',()=>this.moveScroll(Math.max(rowHeight,listHeight)),false,this.scroll>=this.maxScroll);
                this.text(mainX+mainWidth-18,y+7,`${Math.min(rows.length,Math.floor(this.scroll/rowHeight)+1)}–${Math.min(rows.length,Math.floor((this.scroll+listHeight)/rowHeight))} / ${rows.length}`,12,this.palette.dim.css).setOrigin(1,0);
            }
            if(previousFocus)this.controls.find(control=>control.element.getAttribute('aria-label')===previousFocus)?.element.focus({preventScroll:true});
        }
    };
}
