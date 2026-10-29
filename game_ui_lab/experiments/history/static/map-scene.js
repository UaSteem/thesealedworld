(() => {
  'use strict';
  const host=document.getElementById('combat-stage');
  const dpr=Math.min(2,window.devicePixelRatio||1);
  const portraits=['bandit_raider','bandit_blackguard','bandit_lookout','bandit_thug','bandit_captain','bandit_hedge_wizard'];
  const names=['Налётчик','Страж','Разведчик','Головорез','Капитан','Колдун'];
  const enemies=portraits.map((p,i)=>({id:`enemy-${i+1}`,side:'enemy',name:names[i],portraitUrl:`/static/images/monsters/catalog/bandit_gang.${p}.png`,hp:[74,91,58,85,62,79][i],maxHp:100,en:28,maxEn:40,stamina:35,maxStamina:50,actedAgainstViewer:i===2||i===4,deadlineMs:[9000,6500,11000,4500,13000,8000][i],effects:i===2?['Ослабление']:[],demoIntent:['thinking','thinking','decided','imminent','decided','imminent'][i]}));
  const allies=['rook7.webp','veil4.webp','silhouette_f.webp','silhouette_m.webp'].map((p,i)=>({id:`ally-${i+1}`,side:'ally',name:i?'Союзник '+i:'Ada Guard',portraitUrl:`/static/images/avatars/${p}`,hp:90-i*12,maxHp:117,en:31,maxEn:40,stamina:42,maxStamina:54,effects:[]}));
  // Local display fixtures only: these are not calculated combat statistics.
  [...enemies,...allies].forEach((actor,i)=>{
    actor.role=actor.side==='enemy'?['Воин','Защитник','Разведчик','Боец','Командир','Заклинатель'][i]:i===6?'Воин':'Союзник';
    actor.power_score=[32,38,26,35,45,40,32,28,24,27][i];
    const damage=['18 — 26','14 — 22','12 — 19','20 — 29','24 — 34','16 — 30','17 — 25','15 — 23','12 — 20','14 — 21'][i];
    actor.stat_sheet={sections:[
      {key:'offense',label:'Атака',items:[{key:'main_hand_damage',label:'Урон',value_text:damage},{key:'main_hand_accuracy',label:'Точность',value_text:'78%'},{key:'main_hand_crit_chance',label:'Крит',value_text:'12%'}]},
      {key:'defense',label:'Защита',items:[{key:'armor',label:'Броня',value_text:'24'},{key:'evasion',label:'Уклонение',value_text:'8%'},{key:'parry',label:'Парирование',value_text:'10%'}]},
      {key:'attributes',label:'Прочее',items:[{key:'strength',label:'Сила',value_text:'18'},{key:'agility',label:'Ловкость',value_text:'14'},{key:'endurance',label:'Выносливость',value_text:'16'}]}
    ]};
  });
  class MapWorkspace extends Phaser.Scene {
    constructor(){super('MapWorkspace');}
    preload(){[...enemies,...allies].forEach(a=>this.load.image(a.id,a.portraitUrl));window.LabCombatHud.preload(this);}
    create(){
      this.selectedId='enemy-1';this.pinnedDetailsId='enemy-1';this.objects=[];this.nativeKeys=[];this.cards=[];this.outcomeSequence=0;
      this.demoReady=true;this.projectionMode='flat';
      document.querySelectorAll('[data-projection]').forEach(button=>button.addEventListener('click',()=>{this.projectionMode=button.dataset.projection;document.querySelectorAll('[data-projection]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));this.drawMap();}));
      this.scale.on('resize',this.drawMap,this);this.drawMap();
      document.fonts?.ready.then(()=>{if(this.scene.isActive())this.drawMap();});
    }
    text(x,y,label,size=12,color='#e9e1cd'){
      const t=this.add.text(Math.round(x),Math.round(y),label,{fontFamily:getComputedStyle(document.documentElement).getPropertyValue('--font-ui').trim(),fontSize:`${size}px`,color}).setResolution(dpr);
      this.objects.push(t);return t;
    }
    emit(actor,pinned=false){host.dispatchEvent(new CustomEvent('lab-actor-preview',{detail:{actor:{...actor,conc:actor.stamina,maxConc:actor.maxStamina,acted:actor.actedAgainstViewer,intentLabel:({thinking:'Думает над действием',decided:'Выбрал действие против вас',imminent:'Удар по вам скоро'})[actor.demoIntent]},pinned}}));}
    selectActor(id){const actor=[...enemies,...allies].find(a=>a.id===id);if(!actor)return;if(actor.side==='enemy')this.selectedId=id;this.pinnedDetailsId=id;this.drawMap();this.emit(actor,true);}
    drawMap(){
      const width=host.clientWidth,height=host.clientHeight;
      this.cameras.main.setViewport(0,0,width*dpr,height*dpr).setZoom(dpr).centerOn(width/2,height/2);
      this.objects.forEach(o=>o.destroy());this.objects=[];this.cards=[];
      const layout=window.StandeeLayout.gridForFrame(width,height);
      const {radius,perspectiveY}=layout;
      const g=this.add.graphics();this.objects.push(g);
      const polygon=(x,y,offset=0)=>Array.from({length:6},(_,i)=>{
        const a=(i*60-90)*Math.PI/180;
        return{x:x+radius*Math.cos(a),y:y+radius*Math.sin(a)*perspectiveY+offset};
      });
      const project=({x,y})=>{
        if(this.projectionMode==='flat')return{x,y};
        const cx=width/2,cy=height/2,angle=50*Math.PI/180,focal=height*1.5;
        const depth=focal-(y-cy)*Math.sin(angle),scale=focal/depth;
        return{x:cx+(x-cx)*scale,y:cy+(y-cy)*Math.cos(angle)*scale};
      };
      const tiles=layout.cells.map(p=>({top:polygon(p.x,p.y).map(project),side:polygon(p.x,p.y,6).map(project)}));
      const all=tiles.flatMap(t=>[...t.top,...t.side]);
      const minX=Math.min(...all.map(p=>p.x)),maxX=Math.max(...all.map(p=>p.x)),minY=Math.min(...all.map(p=>p.y)),maxY=Math.max(...all.map(p=>p.y));
      const intentHeadroom=this.projectionMode==='perspective'?40:0;
      const fit=Math.min((width-32)/(maxX-minX),(height-32-intentHeadroom)/(maxY-minY));
      const align=p=>({x:width/2+(p.x-(minX+maxX)/2)*fit,y:height/2+intentHeadroom/2+(p.y-(minY+maxY)/2)*fit});
      tiles.forEach(tile=>{
        g.fillStyle(0x222a22,1).fillPoints(tile.side.map(align),true);
        g.fillStyle(0x64765a,1).fillPoints(tile.top.map(align),true);
        g.lineStyle(1,0x8d9c76,.72).strokePoints(tile.top.map(align),true);
      });
      const cells=layout.cells.map((cell,i)=>({...cell,center:align(project(cell)),polygon:tiles[i].top.map(align)}));
      const nearest=(x,y,exclude=[])=>cells.filter(c=>!exclude.includes(c)).sort((a,b)=>Math.hypot(a.center.x-x,a.center.y-y)-Math.hypot(b.center.x-x,b.center.y-y))[0];
      const heroPrevCell=nearest(width*(this.projectionMode==='flat'?.48:.43),height*.60);
      const heroCell=this.projectionMode==='flat'?heroPrevCell:(cells.find(c=>c.row===heroPrevCell.row&&c.col===heroPrevCell.col-1)||heroPrevCell);
      const targetCell=(this.projectionMode==='flat'?cells.find(c=>c.row===heroCell.row-1&&c.col===heroCell.col+(heroCell.row%2===0?1:0)):null)||nearest(width*.73,height*.48,[heroCell]);
      const occupied=[heroCell,targetCell];
      const enemyRows=[0].map(row=>cells.filter(c=>!occupied.includes(c)&&c.row===row).sort((a,b)=>b.col-a.col));
      const enemyCells=[];for(let i=0;i<Math.max(...enemyRows.map(r=>r.length));i++)enemyRows.forEach(row=>{if(row[i])enemyCells.push(row[i]);});
      const allyCells=cells.filter(c=>!occupied.includes(c)&&c.row>=4&&c.col<=3).sort((a,b)=>b.row-a.row||a.col-b.col);
      const primarySize=Math.max(96,Math.min(120,Math.round(Math.min(width*.108,height*.25))));
      // Reserve primary bounds first; queue standees may never cover them.
      this.card(enemies.find(a=>a.id===this.selectedId),targetCell,true,Math.round(primarySize*.87));
      this.card(allies[0],heroCell,true,primarySize);
      const waiting=window.StandeeLayout.prioritize(enemies.filter(a=>a.id!==this.selectedId));
      let enemyIndex=0,allyIndex=1;
      enemyCells.forEach(cell=>{if(waiting[enemyIndex]&&this.card(waiting[enemyIndex],cell,false,primarySize))enemyIndex++;});
      allyCells.forEach(cell=>{if(allies[allyIndex]&&this.card(allies[allyIndex],cell,false,primarySize))allyIndex++;});
      this.mapInfo={projectionMode:this.projectionMode,projectionAngle:this.projectionMode==='flat'?0:50,projectedTiles:cells.map(c=>c.polygon),projectedCellCenters:cells.map(c=>({col:c.col,row:c.row,...c.center})),mode:'static-standees',heroPrevCell:{col:heroPrevCell.col,row:heroPrevCell.row},heroBeforeCell:{col:heroPrevCell.col,row:heroPrevCell.row},heroCell:{col:heroCell.col,row:heroCell.row},targetSize:Math.round(primarySize*.87),heroSize:primarySize,hiddenEnemies:waiting.length-enemyIndex,hiddenAllies:allies.length-allyIndex,columns:7,rows:6,coreColumns:7,coreRows:6,cells:layout.cells.length,cellCoordinates:layout.cells,orientation:'pointy-top',perspectiveY,radius,fieldWidth:layout.bounds.width,fieldHeight:layout.bounds.height,bounds:layout.bounds};
      this.drawIntentMarkers();
      const hud=window.LabCombatHud.draw(this,{width,height,selectedId:this.selectedId,ready:this.demoReady,onAttack:()=>{
        if(!this.demoReady)return;
        const index=enemies.findIndex(a=>a.id===this.selectedId);
        this.selectActor(enemies[(index+1)%enemies.length].id);
      },onFeint:id=>{this.demoFeintId=id;},onAbility:id=>{this.demoAbilityId=id;}});
      this.objects.push(...hud.objects);this.hudInfo=hud.inspect;
      this.emit([...enemies,...allies].find(a=>a.id===this.pinnedDetailsId),true);
    }
    card(actor,cell,big,primarySize){
      if(this.projectionMode==='flat')return this.tableCard(actor,cell,big);

      const polygon=cell.polygon,minY=Math.min(...polygon.map(p=>p.y)),maxY=Math.max(...polygon.map(p=>p.y)),minX=Math.min(...polygon.map(p=>p.x)),maxX=Math.max(...polygon.map(p=>p.x));
      let size=big?primarySize:Math.min(actor.side==='ally'?76:60,Math.floor((maxY-minY)*.9));
      let p={x:cell.center.x,y:cell.center.y+(big?17:0)},queueContainmentPoints=[];
      if(!big){
        const inside=(x,y)=>{
          let sign=0;
          for(let i=0;i<polygon.length;i++){
            const a=polygon[i],b=polygon[(i+1)%polygon.length],cross=(b.x-a.x)*(y-a.y)-(b.y-a.y)*(x-a.x);
            if(Math.abs(cross)<.01)continue;
            if(sign&&Math.sign(cross)!==sign)return false;sign=Math.sign(cross);
          }return true;
        };
        let found=false;
        for(;size>=16&&!found;size--){
          for(let shift=-8;shift<=Math.ceil((maxY-minY)/2);shift++){
            const anchor=cell.center.y+shift,half=(size+8)/2+.5,top=anchor-size-9,bottom=anchor+2.5;
            const points=[[-half,top],[half,top],[-half,bottom],[half,bottom],[-half-2,anchor-3],[half+2,anchor-3]];
            for(let i=0;i<16;i++){const a=i*Math.PI/8;points.push([((size+14)/2+.5)*Math.cos(a),anchor+4+4*Math.sin(a)]);}
            if(points.every(([x,y])=>inside(cell.center.x+x,y))){p.y=anchor;queueContainmentPoints=points.map(([x,y])=>({x:cell.center.x+x,y}));found=true;break;}
          }
          if(found)break;
        }
        if(!found)return false;
      }
      const width=size+8,baseWidth=big?size+34:size+14,baseHeight=big?23:7;
      const top=p.y-size-(big?12:6),selected=actor.id===this.selectedId,isHero=actor.id==='ally-1';
      const bottom=p.y+4+baseHeight/2;
      const bounds={x:p.x-Math.max(baseWidth,width)/2,y:top-3,width:Math.max(baseWidth,width),height:bottom-top+3};
      const overlaps=(a,b)=>a.x<b.x+b.width+5&&a.x+a.width+5>b.x&&a.y<b.y+b.height+5&&a.y+a.height+5>b.y;
      if(!big&&this.cards.some(card=>overlaps(bounds,card.bounds)))return false;
      const edge=selected?0xf4cc80:isHero?0x83d7cf:0xb8aa8c;
      const body=this.add.graphics();this.objects.push(body);
      body.fillStyle(0x000000,.38).fillEllipse(p.x+3,p.y+8,baseWidth+8,baseHeight+7);
      body.fillStyle(0x282e31,1).fillRoundedRect(p.x-width/2,top-2,width,size+(big?14:8),3);
      body.lineStyle(big?2:1,edge,.95).strokeRoundedRect(p.x-width/2,top-2,width,size+(big?14:8),3);
      const source=this.textures.get(actor.id).getSourceImage();
      const ratio=Math.min(size/source.width,size/source.height),renderWidth=source.width*ratio,renderHeight=source.height*ratio;
      // The GPU samples the original texture directly. No cropped/intermediate raster.
      const portrait=this.add.image(p.x,top+size/2+(big?6:3),actor.id).setDisplaySize(renderWidth,renderHeight).setFlipX(actor.side==='enemy');this.objects.push(portrait);
      const detail=this.add.graphics();this.objects.push(detail);
      detail.fillStyle(0x989b92,1).fillRect(p.x-size/2,top+1,size,big?6:3);
      detail.fillStyle(0xff2020,1).fillRect(p.x-size/2,top+1,size*actor.hp/actor.maxHp,big?6:3);
      detail.fillStyle(0x252c30,1).fillEllipse(p.x,p.y+4,baseWidth,baseHeight);
      detail.lineStyle(big?2:1,edge,1).strokeEllipse(p.x,p.y+4,baseWidth,baseHeight);
      detail.fillStyle(0x51574f,1).fillEllipse(p.x,p.y,baseWidth,baseHeight*.8);
      detail.fillStyle(0x252c30,1).fillRoundedRect(p.x-width/2-2,p.y-3,width+4,big?8:5,2);
      detail.lineStyle(1,edge,.9).lineBetween(p.x-width/2-1,p.y-3,p.x+width/2+1,p.y-3);
      const hit=this.add.rectangle(p.x,(top+bottom)/2,Math.max(baseWidth,width),bottom-top+4,0,0).setInteractive({useHandCursor:true});this.objects.push(hit);
      hit.on('pointerover',()=>this.emit(actor));hit.on('pointerout',()=>this.emit([...enemies,...allies].find(a=>a.id===this.pinnedDetailsId),true));hit.on('pointerdown',()=>this.selectActor(actor.id));
      this.cards.push({id:actor.id,big,x:p.x,y:p.y,hexCenter:{...cell.center},cell:{col:cell.col,row:cell.row},size,queueContainmentPoints,flipX:actor.side==='enemy',selected,hpRatio:actor.hp/actor.maxHp,bounds,textureKey:actor.id,textureSource:{width:source.width,height:source.height},renderDimensions:{width:renderWidth,height:renderHeight},fullOriginal:true,queueHexBounds:{x:minX,y:minY,width:maxX-minX,height:maxY-minY}});
      return true;
    }
    drawIntentMarkers(){
      const descriptions={thinking:'Думает над действием',decided:'Выбрал действие против вас',imminent:'Удар по вам скоро'};
      this.cards.filter(c=>!c.big&&c.id.startsWith('enemy')).forEach(card=>{
        const actor=enemies.find(a=>a.id===card.id),stage=actor.demoIntent;
        const x=card.x,y=card.bounds.y-18,r=12;
        const color=stage==='thinking'?0xb8c5cf:stage==='decided'?0xe4b85e:0xff9642;
        const g=this.add.graphics().setDepth(200);this.objects.push(g);
        g.fillStyle(0x111b24,.98).fillCircle(x,y,r);
        g.lineStyle(1,color,1).strokeCircle(x,y,r);
        if(stage==='thinking'){
          g.fillStyle(color,1);[-5,0,5].forEach(dx=>g.fillCircle(x+dx,y,1.7));
        }else{
          const icon=this.add.image(x,y,'hud-attack-art').setDisplaySize(18,18).setDepth(201);this.objects.push(icon);
          if(stage==='imminent')g.lineStyle(3,color,1).beginPath().arc(x,y,r+4,-Math.PI/2,Math.PI*.95).strokePath();
        }
        const hit=this.add.circle(x,y,16,0,0).setDepth(202).setInteractive({useHandCursor:true});this.objects.push(hit);
        hit.on('pointerover',()=>this.emit(actor));hit.on('pointerout',()=>this.emit(enemies.find(a=>a.id===this.selectedId),true));
        card.intent={stage,label:descriptions[stage],x,y,radius:stage==='imminent'?17:13};
      });
    }
    tableCard(actor,cell,big){
      const polygon=cell.polygon,x=cell.center.x;
      const hexWidth=Math.max(...polygon.map(p=>p.x))-Math.min(...polygon.map(p=>p.x));
      const hexHeight=Math.max(...polygon.map(p=>p.y))-Math.min(...polygon.map(p=>p.y));
      const w=Math.round(hexWidth*(big?.88:.58)),h=Math.round(hexHeight*(big?.91:.61));
      const clearance=big?Math.max(12,(h+16-hexHeight*.75)/2):0;
      const y=cell.center.y+(big?(actor.id==='ally-1'?clearance:-clearance):0);
      const bounds={x:x-w/2,y:y-h/2,width:w,height:h};
      const overlaps=(a,b)=>a.x<b.x+b.width+4&&a.x+a.width+4>b.x&&a.y<b.y+b.height+4&&a.y+a.height+4>b.y;
      if(!big&&this.cards.some(c=>overlaps(bounds,c.bounds)))return false;
      const selected=actor.id===this.selectedId,hero=actor.id==='ally-1';
      const edge=selected?0xf4cc80:hero?0x83d7cf:0xb8aa8c;
      const frame=this.add.graphics();this.objects.push(frame);
      frame.fillStyle(0x000000,.35).fillRoundedRect(bounds.x+3,bounds.y+4,w,h,4);
      frame.fillStyle(0x131b23,1).fillRoundedRect(bounds.x,bounds.y,w,h,4);
      frame.lineStyle(big?2:1,edge,1).strokeRoundedRect(bounds.x,bounds.y,w,h,4);
      frame.lineStyle(1,edge,.25).strokeRoundedRect(bounds.x+4,bounds.y+4,w-8,h-8,2);
      const source=this.textures.get(actor.id).getSourceImage();
      const ratio=Math.min((w-10)/source.width,(h-15)/source.height),renderWidth=source.width*ratio,renderHeight=source.height*ratio;
      const art=this.add.image(x,y+3,actor.id).setDisplaySize(renderWidth,renderHeight).setFlipX(actor.side==='enemy');this.objects.push(art);
      const hp=this.add.graphics();this.objects.push(hp);
      hp.fillStyle(0x989b92,1).fillRect(bounds.x+5,bounds.y+5,w-10,big?5:3);
      hp.fillStyle(0xff2020,1).fillRect(bounds.x+5,bounds.y+5,(w-10)*actor.hp/actor.maxHp,big?5:3);
      const hit=this.add.rectangle(x,y,w,h,0,0).setInteractive({useHandCursor:true});this.objects.push(hit);
      hit.on('pointerover',()=>this.emit(actor));hit.on('pointerout',()=>this.emit([...enemies,...allies].find(a=>a.id===this.pinnedDetailsId),true));hit.on('pointerdown',()=>this.selectActor(actor.id));
      this.cards.push({id:actor.id,big,style:'tabletop',hasStand:false,x,y,hexCenter:{...cell.center},cell:{col:cell.col,row:cell.row},size:h,bounds,selected,hpRatio:actor.hp/actor.maxHp,flipX:actor.side==='enemy',textureKey:actor.id,textureSource:{width:source.width,height:source.height},renderDimensions:{width:renderWidth,height:renderHeight},fullOriginal:true,queueContainmentPoints:big?[]:[{x:bounds.x,y:bounds.y},{x:bounds.x+w,y:bounds.y},{x:bounds.x+w,y:bounds.y+h},{x:bounds.x,y:bounds.y+h}]});
      return true;
    }
    inspect(){return{hud:this.hudInfo,demoReady:this.demoReady,demoFeintId:this.demoFeintId,demoAbilityId:this.demoAbilityId,...this.mapInfo,actors:[...enemies,...allies].map(a=>({...a})),cards:this.cards.map(c=>({...c})),selectedId:this.selectedId,pinnedDetailsId:this.pinnedDetailsId,websocket:false};}
  }
  const game=new Phaser.Game({type:Phaser.AUTO,parent:host,transparent:true,width:host.clientWidth*dpr,height:host.clientHeight*dpr,scale:{zoom:1/dpr,mode:Phaser.Scale.NONE},scene:[MapWorkspace],render:{antialias:true}});
  const observer=new ResizeObserver(()=>{const w=host.clientWidth*dpr,h=host.clientHeight*dpr;if(w>0&&h>0&&(game.scale.width!==w||game.scale.height!==h))game.scale.resize(w,h);});
  observer.observe(host);window.gameUiLab={game,sceneName:'MapWorkspace'};
})();
