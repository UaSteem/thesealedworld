(() => {
  'use strict';
  const host=document.getElementById('combat-stage');
  const styles=getComputedStyle(document.documentElement);
  const value=name=>styles.getPropertyValue(name).trim();
  const color=name=>Phaser.Display.Color.HexStringToColor(value(name)).color;
  const Demo=()=>window.LabCombatDemo;
  class CombatWorkspace extends Phaser.Scene {
    constructor(){super('CombatWorkspace');}
    preload(){
      const sample=new(Demo().Model)({enemyCount:30,allyCount:4,seed:1});this.assetKeys=new Map();
      const load=url=>{if(!url||this.assetKeys.has(url))return;const key=`demo-asset-${this.assetKeys.size}`;this.assetKeys.set(url,key);if(url.endsWith('.svg'))this.load.svg(key,url,{width:128,height:128});else this.load.image(key,url);};
      sample.snapshot().actors.forEach(actor=>load(actor.portraitUrl));
      [...Demo().TOKEN_TYPES,...Demo().FEINTS,...Demo().ABILITIES].forEach(item=>load(item.iconUrl));
      load('/static/images/ui/arena-icons/sword-clash.svg');this.load.image('battle-grass','/ui-static/assets/grass.png');
    }
    create(){
      this.cards=new Map();this.pendingTimers=new Set();this.cleanupTimers=new Set();this.fx=new Set();this.fxEvents=[];this.pinned=new Map();this.pinOrder=new Map();this.pinSequence=0;this.deferredOutcomes=new Map();this.deadUntil=new Map();this.seed=1;
      this.prepareTextures();
      this.ground=this.add.container(0,0).setDepth(-100);this.nativeKeys=new Set();
      this.grid=this.add.graphics();this.hud=this.add.container(0,0).setDepth(100);this.labels=this.add.container(0,0).setDepth(80);
      this.rowLabels=['ОЖИДАЮТ РАЗМЕНА','БЕЗ ДЕЙСТВИЯ','ИГРОК И СОЮЗНИКИ'].map(label=>this.text(0,0,label,11,'--col-text-dim').setAlpha(.8));
      this.rowLabels.forEach(label=>this.labels.add(label));
      this.overflowLabel=this.text(0,0,'',11).setOrigin(1,0);this.labels.add(this.overflowLabel);
      this.targetLabel=this.text(0,0,'ВЫБРАННАЯ ЦЕЛЬ',9,'--col-accent').setOrigin(.5);this.labels.add(this.targetLabel);
      this.scale.on('resize',this.layout,this);this.events.once('shutdown',()=>this.scale.off('resize',this.layout,this));
      const generate=document.getElementById('generate-battle');
      if(generate){generate.disabled=false;generate.addEventListener('click',()=>this.regenerate());}
      document.fonts?.ready.then(()=>{if(this.scene.isActive())this.layout();});this.regenerate();
    }
    prepareTextures(){this.portraitKeys=new Map();}
    dpr(){return Math.round(Math.min(2,Math.max(1,window.devicePixelRatio||1))*4)/4;}
    terrainTexture(radius){
      const dpr=this.dpr(),key=`terrain-${radius}-${dpr}`;
      if(this.textures.exists(key))return key;
      const R=radius*dpr,h=Math.sqrt(3)*R;
      const texture=this.textures.createCanvas(key,Math.ceil(2*R),Math.ceil(h*.65));
      const ctx=texture.getContext();ctx.scale(R/128,R/128*.65);
      RiftTerrain.drawGround(ctx,this.textures.get('battle-grass').getSourceImage(),0);texture.refresh();this.nativeKeys.add(key);return key;
    }
    portraitTexture(actor,width,height){
      const dpr=this.dpr(),key=`portrait-${this.assetKeys.get(actor.portraitUrl)}-${width}-${height}-${dpr}`;
      if(this.textures.exists(key))return key;
      const source=this.textures.get(this.assetKeys.get(actor.portraitUrl)).getSourceImage();
      const t=this.textures.createCanvas(key,Math.ceil(width*dpr),Math.ceil(height*dpr)),ctx=t.getContext();
      if(actor.portraitUrl.includes('/monsters/catalog/'))ctx.drawImage(source,source.width*.3,source.height*.02,source.width*.45,source.height*.39,0,0,t.width,t.height);
      else ctx.drawImage(source,0,0,source.width,source.height,0,0,t.width,t.height);
      t.refresh();this.nativeKeys.add(key);return key;
    }
    options(){return{enemyCount:Number(document.getElementById('demo-enemy-count')?.value||10),allyCount:4,seed:this.seed++};}
    regenerate(options){
      this.pendingTimers.forEach(timer=>timer.remove(false));this.pendingTimers.clear();this.tweens.killAll();
      this.cleanupTimers.forEach(timer=>timer.remove(false));this.cleanupTimers.clear();
      this.fx.forEach(object=>object.destroy());this.fx.clear();this.cards.forEach(record=>record.container.destroy());this.cards.clear();
      this.pinned.clear();this.pinOrder.clear();this.deferredOutcomes.clear();this.deadUntil.clear();this.fxEvents=[];
      if(this.model)this.model.reset(options||this.options());else this.model=new(Demo().Model)(options||this.options());this.layout();
    }
    text(x,y,content,size=11,tint='--col-text-world'){return this.add.text(x,y,content,{fontFamily:value('--font-ui'),fontSize:`${size}px`,color:value(tint)}).setResolution(this.dpr()).setPosition(Math.round(x),Math.round(y));}
    hex(g,x,y,width,fill,alpha,stroke,selected=false){
      const points=[{x:x-width/2,y},{x:x-width/4,y:y-width*.19},{x:x+width/4,y:y-width*.19},{x:x+width/2,y},{x:x+width/4,y:y+width*.19},{x:x-width/4,y:y+width*.19}];
      g.fillStyle(fill,alpha).fillPoints(points,true);g.lineStyle(selected?2:1,stroke,selected?.95:.55).strokePoints(points,true);
    }
    createCard(actor){
      const container=this.add.container(0,0),art=this.add.graphics(),portrait=this.add.image(0,0,this.assetKeys.get(actor.portraitUrl)),bars=this.add.graphics();container.add([art,portrait,bars]);
      const numbers=[0,1,2].map(()=>this.text(0,0,'',10).setOrigin(.5));container.add(numbers);
      const name=this.text(0,0,'',11).setOrigin(.5),status=this.text(0,0,'',11,'--col-accent').setOrigin(.5);container.add([name,status]);
      const hit=this.add.rectangle(0,0,58,72,0xffffff,0).setInteractive({useHandCursor:actor.side==='enemy'});container.add(hit);
      hit.on('pointerdown',()=>{if(this.model.selectTarget(actor.id))this.sync(true);});
      const record={id:actor.id,container,art,portrait,bars,numbers,name,status,hit};this.cards.set(actor.id,record);return record;
    }
    updateCard(record,actor,selected){
      const factor=selected?2:1,w=56*factor,portraitH=selected?88:28,top=selected?-126:-49;
      record.art.clear();record.art.fillStyle(color('--col-bg-darker'),.84).fillRoundedRect(-w/2-2,top-3,w+4,portraitH+25*factor,3);
      record.art.lineStyle(selected?2:1,color(selected?'--col-accent':'--col-border'),.9).strokeRoundedRect(-w/2-2,top-3,w+4,portraitH+25*factor,3);
      record.portrait.setTexture(this.portraitTexture(actor,w,portraitH)).setDisplaySize(w,portraitH).setPosition(0,top+(selected?38:14)+portraitH/2);
      record.bars.clear();[[actor.hp,actor.maxHp,'--col-danger'],[actor.en,actor.maxEn,'--col-energy'],[actor.conc,actor.maxConc,'--col-stamina']].forEach(([current,max,tint],i)=>{
        const barHeight=selected?8:3,barPitch=selected?12:4,y=top+i*barPitch;record.bars.fillStyle(color('--col-bg-base'),1).fillRect(-w/2,y,w,barHeight);record.bars.fillStyle(color(tint),1).fillRect(-w/2,y,w*Math.max(0,Math.min(1,current/Math.max(1,max))),barHeight);
        record.numbers[i].setPosition(0,y+3*factor).setFontSize(11).setText(`${['HP','EN','CONC'][i]} ${current}/${max}`).setVisible(selected);
      });
      record.name.setPosition(0,selected?14:0).setFontSize(selected?14:11).setText(actor.name.length>11&&!selected?actor.name.slice(0,10)+'…':actor.name);
      record.status.setPosition(0,selected?30:20).setFontSize(11).setText(actor.hp<=0?'ПОВЕРЖЕН':actor.lastEvent?.effect?.label||(selected?'ЦЕЛЬ':'')).setVisible(selected);
      const hitHeight=selected?162:55;record.hit.setPosition(0,selected?-45:-21.5).setSize(w,hitHeight);
      record.hit.input.hitArea.setTo(0,0,w,hitHeight);record.container.setAlpha(actor.hp<=0?.58:1).setScale(1);
    }
    visible(snapshot){
      const now=this.time.now,enemies=snapshot.actors.filter(actor=>actor.side==='enemy'&&(actor.hp>0||(this.deadUntil.get(actor.id)||0)>now));
      const priorities=new Map([...this.pinned].filter(([,until])=>until>now).map(([id])=>[id,this.pinOrder.get(id)||0]));
      const set=window.LabBattleLayout.selectBands(enemies,snapshot.selectedId,priorities,this.board.near.length,this.board.far.length,this.board.visibleLimit);
      return{...set,allies:snapshot.actors.filter(actor=>actor.side==='ally'&&actor.hp>0).slice(0,10)};
    }
    sync(animate=false){
      if(!this.model)return;const snapshot=this.model.snapshot(),set=this.visible(snapshot),b=this.board;
      this.updateHero(snapshot);
      const positions=new Map();
      set.allies.forEach((actor,i)=>{const p=b.allies[i];if(p)positions.set(actor.id,{...p,row:'allies'});});
      [['acted',b.near],['waiting',b.far]].forEach(([intent,slots])=>{
        set.shown.filter(a=>(a.intent==='acted'?'acted':'waiting')===intent).forEach((actor,i)=>{
          const p=slots[i];if(p)positions.set(actor.id,{...p,row:intent});
        });
      });
      if(set.target)positions.set(set.target.id,{...b.center,row:'target'});
      const byId=new Map(snapshot.actors.map(actor=>[actor.id,actor]));
      this.cards.forEach((record,id)=>{if(!positions.has(id)){
        this.tweens.killTweensOf(record.container);
        this.fx.forEach(effect=>{if(effect.parentContainer===record.container){this.tweens.killTweensOf(effect);this.fx.delete(effect);effect.destroy();}});
        record.container.destroy();this.cards.delete(id);
      }});
      positions.forEach((p,id)=>{
        p.x=Math.round(p.x);p.y=Math.round(p.y);
        const actor=byId.get(id),existed=this.cards.has(id),record=this.cards.get(id)||this.createCard(actor);record.slot=p;this.updateCard(record,actor,id===snapshot.selectedId);
        this.tweens.killTweensOf(record.container);record.container.setDepth(id===snapshot.selectedId?50:10+p.y/1000);
        if(animate&&existed)this.tweens.add({targets:record.container,x:p.x,y:p.y,duration:320,ease:'Cubic.easeOut'});
        else record.container.setPosition(p.x,p.y).setScale(1);
      });
      this.targetLabel.setVisible(false);
      this.overflowLabel.setText(set.hidden?`Ещё ${set.hidden} противников в бою`:`${snapshot.actors.filter(a=>a.side==='enemy'&&a.hp>0).length} противников`);this.drawHud(snapshot);
      positions.forEach((_,id)=>{if(this.deferredOutcomes.has(id)){const event=this.deferredOutcomes.get(id);this.deferredOutcomes.delete(id);this.animateOutcome(event);}});
    }
    updateHero(snapshot){
      const hero=snapshot.actors.find(actor=>actor.side==='ally');if(!hero)return;
      [['hp','hp','maxHp'],['energy','en','maxEn'],['stamina','conc','maxConc']].forEach(([variant,current,maximum])=>{
        const row=document.querySelector(`.character-panel .cp-vital--${variant}`);if(!row)return;
        const meter=row.querySelector('meter'),label=row.querySelector('b');
        if(meter){meter.max=hero[maximum];meter.value=hero[current];meter.textContent=`${hero[current]} / ${hero[maximum]}`;}
        if(label)label.textContent=`${hero[current]} / ${hero[maximum]}`;
      });
    }
    layout(){
      if(!this.ground)return;this.board=window.LabBattleLayout.compute(host.clientWidth,host.clientHeight);const b=this.board;
      this.cameras.main.setViewport(0,0,this.scale.width,this.scale.height).setZoom(this.dpr()).centerOn(b.width/2,b.height/2);
      this.ground.removeAll(true);this.grid.clear();
      // Every material is generated independently at its final physical size.
      const used=new Set();[...b.cells,b.center].forEach(p=>{
        const key=this.terrainTexture(p.radius);used.add(key);
        this.ground.add(this.add.image(p.x,p.y,key).setDisplaySize(p.radius*2,Math.sqrt(3)*p.radius*.65));
        const points=Array.from({length:6},(_,i)=>({x:p.x+p.radius*Math.cos(i*Math.PI/3),y:p.y+p.radius*Math.sin(i*Math.PI/3)*.65}));
        this.grid.lineStyle(p===b.center?2:1,p===b.center?0xd1b776:0x253a1f,p===b.center?.9:.65).strokePoints(points,true);
      });
      for(const key of this.nativeKeys)if(key.startsWith('terrain-')&&!used.has(key)){this.textures.remove(key);this.nativeKeys.delete(key);}
      [b.near,b.far,b.allies].forEach((slots,i)=>{
        const label=this.rowLabels[i],x=Math.min(...slots.map(p=>p.x))-28,y=Math.min(...slots.map(p=>p.y))-76;
        label.setPosition(Math.round(x),Math.round(Math.max(26,y))).setVisible(y>=26);
      });
      this.overflowLabel.setPosition(b.width-14,8);this.sync(false);
    }
    button(parent,x,y,width,height,label,enabled,callback,iconUrl){
      const container=this.add.container(x,y);parent.add(container);const background=this.add.rectangle(0,0,width,height,color('--col-bg-darker'),1).setStrokeStyle(1,color(enabled?'--col-border-strong':'--col-border'),enabled?.9:.4);container.add(background);
      let textX=0;if(iconUrl&&this.assetKeys.has(iconUrl)){container.add(this.add.image(-width/2+17,0,this.assetKeys.get(iconUrl)).setDisplaySize(22,22).setTint(color('--col-accent')));textX=9;}
      container.add(this.text(textX,0,label,10,enabled?'--col-text-world':'--col-text-dim').setOrigin(.5));container.setAlpha(enabled?1:.48);background.setInteractive({useHandCursor:enabled});
      background.on('pointerdown',()=>{if(enabled)callback();});background.on('pointerover',()=>{if(enabled)background.setFillStyle(color('--col-bg-surface-light'));});background.on('pointerout',()=>background.setFillStyle(color('--col-bg-darker')));return container;
    }
    drawHud(snapshot){
      this.hud.removeAll(true);const b=this.board,y=b.hudY,h=b.hudHeight,w=b.width;this.hud.add(this.add.rectangle(0,y,w,h,color('--col-bg-surface'),1).setOrigin(0).setStrokeStyle(1,color('--col-border')));
      this.hud.add(this.text(18,y+8,'СПОСОБНОСТИ · ДЕМО',9,'--col-text-dim'));const aw=Math.min(112,Math.max(72,(w-490)/4));
      Demo().ABILITIES.forEach((item,i)=>{const enabled=this.model.canUseAbility?this.model.canUseAbility(item.id):!!snapshot.selectedId;
        this.button(this.hud,20+aw/2+i*(aw+7),y+h*.65,aw,h*.46,`${item.label}\n${item.cost?.amount||0} ${(item.cost?.resource||'en').toUpperCase()}`,enabled,()=>this.perform('ability',item.id),item.iconUrl);});
      const tokenStart=Math.max(335,w-565),pitch=Math.min(37,(w-tokenStart-205)/9);
      Demo().TOKEN_TYPES.forEach((token,i)=>{const x=tokenStart+i*pitch;this.hud.add(this.add.image(x,y+24,this.assetKeys.get(token.iconUrl)).setDisplaySize(18,18).setTint(color('--col-accent')));this.hud.add(this.text(x,y+37,String(snapshot.tokens[token.id]||0),10).setOrigin(.5));});
      const sx=w-56,sy=y+h*.63,circle=this.add.circle(sx,sy,Math.min(34,h*.29),color('--col-bg-darker'),1).setStrokeStyle(2,color('--col-accent'));this.hud.add(circle);
      this.hud.add(this.add.image(sx,sy-3,this.assetKeys.get('/static/images/ui/arena-icons/sword-clash.svg')).setDisplaySize(34,34).setTint(color('--col-accent')));this.hud.add(this.text(sx,sy+24,'АТАКА',8,'--col-accent').setOrigin(.5));
      circle.setInteractive({useHandCursor:!!snapshot.selectedId});circle.on('pointerdown',()=>this.attack());circle.on('pointerover',()=>circle.setFillStyle(color('--col-bg-surface-light')));circle.on('pointerout',()=>circle.setFillStyle(color('--col-bg-darker')));
      Demo().FEINTS.forEach((item,i)=>this.button(this.hud,w-155,y+16+i*(h-28)/3,82,Math.min(25,(h-26)/3-3),item.label,this.model.canUseFeint?this.model.canUseFeint(item.id):false,()=>this.perform('feint',item.id)));
      this.attackPoint={x:sx,y:sy};
    }
    attack(){return this.perform('attack');}
    perform(kind,id){
      const result=kind==='ability'?this.model.useAbility(id):kind==='feint'?this.model.useFeint(id):this.model.attack();if(!result)return null;const event=result.event;
      this.pinned.set(event.actorId,this.time.now+1800);this.pinOrder.set(event.actorId,++this.pinSequence);this.sync(true);
      const timer=this.time.delayedCall(result.delayMs,()=>{
        this.pendingTimers.delete(timer);if(!this.model.applyEvent(event))return;
        const actor=this.model.snapshot().actors.find(a=>a.id===event.actorId);if(actor?.hp<=0)this.deadUntil.set(event.actorId,this.time.now+1100);
        this.pinned.set(event.actorId,this.time.now+1400);this.pinOrder.set(event.actorId,++this.pinSequence);this.sync(true);this.animateOutcome(event);
      });this.pendingTimers.add(timer);return result;
    }
    animateOutcome(event){
      const record=this.cards.get(event.actorId);
      if(!record){
        const previous=this.deferredOutcomes.get(event.actorId);
        this.deferredOutcomes.set(event.actorId,previous?{...event,damage:previous.damage+event.damage,healing:previous.healing+event.healing}:event);
        return;
      }
      this.fxEvents.push({actorId:event.actorId,eventId:event.eventId,sessionId:event.sessionId,at:this.time.now});this.fxEvents=this.fxEvents.slice(-32);
      const parts=[];if(event.damage)parts.push({text:`−${event.damage}`,tint:'--col-danger'});if(event.healing)parts.push({text:`+${event.healing}`,tint:'--col-success'});if(event.blocked)parts.push({text:'БЛОК',tint:'--col-energy'});if(event.effect?.label)parts.push({text:event.effect.label,tint:'--col-accent'});
      parts.forEach((part,i)=>{const text=this.text(0,-42-i*14,part.text,i===0?18:10,part.tint).setOrigin(.5).setStroke(value('--col-bg-base'),3);record.container.add(text);this.fx.add(text);
        this.tweens.add({targets:text,y:text.y-25,alpha:0,duration:1050,delay:i*90,ease:'Cubic.easeOut',onComplete:()=>{this.fx.delete(text);text.destroy();}});});
      const cleanup=this.time.delayedCall(1200,()=>{this.cleanupTimers.delete(cleanup);if(this.model.snapshot().sessionId===event.sessionId)this.sync(true);});this.cleanupTimers.add(cleanup);
    }
    inspect(){const s=this.model.snapshot();return{sessionId:s.sessionId,selectedId:s.selectedId,actors:s.actors,tokens:s.tokens,cards:[...this.cards.values()].map(c=>({id:c.id,row:c.slot.row,x:c.container.x,y:c.container.y,scale:c.container.scaleX,bounds:c.container.getBounds()})),fxEvents:[...this.fxEvents],deferredOutcomes:this.deferredOutcomes.size,transientActive:this.fx.size,pending:this.pendingTimers.size,attackPoint:this.attackPoint,boardHeight:this.board.boardHeight,terrain:{radius:this.board.radius,perspectiveY:RiftTerrain.perspectiveY,cells:this.board.cells.length,targetRadius:this.board.center.radius,textureKeys:[...this.nativeKeys].filter(key=>key.startsWith('terrain-'))},pixelRatio:this.dpr(),cameraZoom:this.cameras.main.zoom};}
  }
  const pixelRatio=Math.min(2,Math.max(1,window.devicePixelRatio||1));
  const game=new Phaser.Game({type:Phaser.AUTO,parent:host,transparent:true,resolution:Math.min(2,window.devicePixelRatio||1),width:host.clientWidth*pixelRatio,height:host.clientHeight*pixelRatio,scale:{zoom:1/pixelRatio,mode:Phaser.Scale.NONE,autoCenter:Phaser.Scale.CENTER_BOTH},scene:[CombatWorkspace],render:{antialias:true}});
  const observer=new ResizeObserver(()=>{const width=host.clientWidth*pixelRatio,height=host.clientHeight*pixelRatio;if(width>0&&height>0&&(game.scale.width!==width||game.scale.height!==height))game.scale.resize(width,height);});
  observer.observe(host);window.gameUiLab={game,sceneName:'CombatWorkspace'};
})();
