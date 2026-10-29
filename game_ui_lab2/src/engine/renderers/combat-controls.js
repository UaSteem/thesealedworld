import Phaser from 'phaser';
import {assets} from '../assets.js';
/* Local demo controls. No backend calls or combat-target mutation. */

  'use strict';
  const KEY = 'control-zone-low-wide-v3';
  const CONTENT_INSET = 12;
  const PANEL_Y = 64, FRAME_W = 920, FRAME_H = 350, ARC_R = 286, PAGE_SIZE = 10;
  const CROPS = {
    frame: [52,330,920,350], plate: [1076,394,920,286],
    feint: [92,1290,840,106], attack: [92,1580,840,116], slot: [1216,1216,640,640],
  };
  const tabs = [
    {id:'attack',label:'Атака',from:182.5,to:207.5},
    {id:'items',label:'Итемы',from:211.5,to:236.5},
    {id:'abilities',label:'Абилки',from:240.5,to:265.5},
  ];
  const abilityNames = ['Жажда крови','Сломать стойку','Рассекающий дар','Открыть слабость','Последний рывок','Скользнуть мимо','Расщепляющий удар','Остановить кровь'];
  const abilities = Array.from({length:24},(_,i)=>({id:`ability-${i+1}`,label:abilityNames[i%8]+(i>=8?` ${Math.floor(i/8)+1}`:''),icon:i%8}));
  const feints = ['Точный удар','Связать клинок','Срезать уворот'];
  const feintCosts = ['Попадание 3','Попадание 3 · Парирование 2','Попадание 3 · Уворот 2'];
  const tokenIds = ['tempo','hit','crit','dodge','parry','block','pressure','blood','gift'];
  const tokenLabels = ['Темп','Попадание','Крит','Уворот','Парирование','Блок','Натиск','Кровь','Дар'];
  const iconIds = ['basic_blood_hunger','basic_break_stance','basic_cleave_gift','basic_expose_weakness','basic_last_push','basic_slip_pain','basic_splinter_strike','basic_wipe_blood'];
  function preload(scene) {
    assets.preload(scene,'combat-controls');
    tokenIds.forEach(id=>scene.load.svg(`cz-token-${id}`,`/static/images/ui/combat-icons/token-${id}.svg`,{width:96,height:96}));
    iconIds.forEach((id,i)=>scene.load.svg(`cz-ability-${i}`,`/static/images/ui/combat-icons/abilities/${id}.svg`,{width:96,height:96}));
  }
  function create(scene, options) {
    const onAttack=options.onAttack;
    const texture=scene.textures.get(KEY);
    for(const [name,[x,y,w,h]] of Object.entries(CROPS)) if(!texture.has(name))texture.add(name,0,x,y,w,h);
    let currentTab='attack',requestedTab='attack',transitioning=false,page=0,attackCount=0;
    let selectedFeints=new Set(),quickSlots=Array(8).fill(null),layout,hits=[],quickRects=[],quickRoot=null;
    let content=null,tween=null,ghost=null,closed=false;
    const root=scene.add.container(0,0).setDepth(1000);
    // Rotate the backing plate around the fixed corner medallion.
    const rotor=scene.add.container(FRAME_W,FRAME_H);root.add(rotor);
    const pane=scene.add.container(-FRAME_W,PANEL_Y-FRAME_H);rotor.add(pane);
    const clip=scene.make.graphics({x:0,y:0,add:false});
    const paneMask=clip.createGeometryMask();rotor.setMask(paneMask);
    pane.add(scene.add.image(0,0,KEY,'plate').setOrigin(0).setDisplaySize(920,286));
    const frame=scene.add.image(0,0,KEY,'frame').setOrigin(0);root.add(frame);
    const fixed=scene.add.container(0,0);root.add(fixed);
    const tooltip=scene.add.text(0,0,'',{fontFamily:'Segoe UI, sans-serif',fontSize:'13px',color:'#e5edf2',backgroundColor:'#12212af5',padding:{x:9,y:6},resolution:3}).setDepth(1100).setVisible(false);
    const font=()=>getComputedStyle(document.documentElement).getPropertyValue('--font-ui').trim()||'Arial';
    function text(parent,x,y,label,pixels=12,color='#e5edf2'){
      const item=scene.add.text(x,y,label,{fontFamily:font(),fontSize:`${pixels/layout.scale}px`,fontStyle:'normal',color,align:'center',resolution:3,padding:{x:0,y:1}}).setOrigin(.5);
      parent.add(item);return item;
    }
    function world(x,y){return{x:layout.x+x*layout.scale,y:layout.y+y*layout.scale};}
    function tip(label,x,y){const p=world(x,y);tooltip.setText(label);tooltip.setPosition(Math.max(8,Math.min(options.width-tooltip.width-8,p.x-tooltip.width/2)),Math.max(8,p.y-tooltip.height-12));tooltip.setVisible(true);}
    function localHit(parent,id,kind,x,y,w,h,label,callback){
      const z=scene.add.zone(x,y,w,h);
      const area=new Phaser.Geom.Rectangle(0,0,w,h);
      z.setInteractive(area,(rect,lx,ly)=>{
        if(!rect.contains(lx,ly))return false;
        if(parent!==content)return true;
        const px=x-w/2+lx,py=y-h/2+ly+PANEL_Y+CONTENT_INSET;
        return Math.hypot(px-FRAME_W,py-FRAME_H)>=ARC_R;
      });
      z.input.cursor='pointer';parent.add(z);
      const dy=parent===content?PANEL_Y+CONTENT_INSET:0;
      z.on('pointerover',()=>tip(label,x,y+dy));z.on('pointerout',()=>tooltip.setVisible(false));
      z.on('pointerdown',()=>{if(!transitioning)callback?.();});
      const p=world(x,y+dy);hits.push({id,kind,x:p.x-w*layout.scale/2,y:p.y-h*layout.scale/2,width:w*layout.scale,height:h*layout.scale,center:p});
      return z;
    }
    function rebuildFixed(){
      fixed.removeAll(true);hits=hits.filter(h=>!['tab','token'].includes(h.kind));
      const counts=[2,5,1,3,2,0,1,0,2];
      tokenIds.forEach((id,i)=>{
        const x=24+i*98,y=12;
        fixed.add(scene.add.image(x+23,y+20,`cz-token-${id}`).setDisplaySize(26,26).setTint(0xe4cd9b));
        text(fixed,x+63,y+20,String(counts[i]),12);
        localHit(fixed,id,'token',x+44,y+20,88,40,`${tokenLabels[i]}: ${counts[i]}`);
      });
      tabs.forEach(tab=>{
        const angle=(tab.from+tab.to)/2*Math.PI/180;
        const x=FRAME_W+208*Math.cos(angle),y=FRAME_H+208*Math.sin(angle);
        const zone=scene.add.zone(0,0,FRAME_W,FRAME_H).setOrigin(0).setInteractive(new Phaser.Geom.Rectangle(0,0,FRAME_W,FRAME_H),(area,lx,ly)=>{
          const dx=lx-FRAME_W,dy=ly-FRAME_H,r=Math.hypot(dx,dy),a=(Math.atan2(dy,dx)*180/Math.PI+360)%360;
          return r>=148&&r<=268&&a>=tab.from&&a<=tab.to;
        });
        fixed.add(zone);zone.input.cursor='pointer';
        zone.on('pointerdown',()=>switchTab(tab.id));zone.on('pointerover',()=>tip(tab.label,x,y));zone.on('pointerout',()=>tooltip.setVisible(false));
        const p=world(x,y);hits.push({id:tab.id,kind:'tab',center:p,x:p.x-12,y:p.y-12,width:24,height:24});
      });
    }
    function buildContent(){
      if(content)content.destroy();hits=hits.filter(h=>!['feint','attack','item','ability','page'].includes(h.kind));
      content=scene.add.container(0,CONTENT_INSET);pane.add(content);
      if(currentTab==='attack'){
        const rows=[{id:'feint-0',label:feints[0],frame:'feint'},{id:'feint-1',label:feints[1],frame:'feint'},{id:'feint-2',label:feints[2],frame:'feint'},{id:'attack',label:'Обычная атака',frame:'attack'}];
        const rowWidth=450,gap=6,centerX=317;
        const heights=rows.map(row=>rowWidth*CROPS[row.frame][3]/CROPS[row.frame][2]);
        let top=(286-heights.reduce((sum,h)=>sum+h,0)-gap*(rows.length-1))/2-CONTENT_INSET;
        rows.forEach((row,i)=>{
          const h=heights[i],x=centerX;
          row.w=rowWidth;row.y=top+h/2;top+=h+gap;
          content.add(scene.add.image(x,row.y,KEY,row.frame).setDisplaySize(row.w,h));
          const active=selectedFeints.has(i);
          const chosen=[...selectedFeints][0];
          const label=i===3&&chosen!==undefined?`Атака с приёмом: ${feints[chosen]}`:row.label;
          text(content,x,row.y,(i<3&&active?'✓ ':'')+label,13,active?'#a4ead9':'#e5edf2');
          localHit(content,row.id,i<3?'feint':'attack',x,row.y,row.w,h,i<3?`${row.label}\nМодификатор следующего удара (демо).\nСтоимость: ${feintCosts[i]}`:'Обычный удар · демонстрация',()=>{
            if(i<3){const wasSelected=selectedFeints.has(i);selectedFeints.clear();if(!wasSelected)selectedFeints.add(i);buildContent();}
            else{if(onAttack?.({feint:chosen})===false)return;attackCount++;selectedFeints.clear();buildContent();}
          });
        });
      }else{
        const list=currentTab==='items'?Array.from({length:8},(_,i)=>({id:`item-${i+1}`,label:`Ячейка пояса ${i+1}`,icon:i})):abilities.slice(page*PAGE_SIZE,page*PAGE_SIZE+PAGE_SIZE);
        list.forEach((item,i)=>{
          const columns=currentTab==='items'?4:5;
          const stepX=currentTab==='items'?140:112;
          const x=317+((i%columns)-(columns-1)/2)*stepX;
          const y=(currentTab==='items'?77:57)+Math.floor(i/columns)*108,size=90;
          const image=scene.add.image(x,y,KEY,'slot').setDisplaySize(size,size);content.add(image);
          const locked=currentTab==='items'&&i>=6;
          if(currentTab==='items') {
            image.setAlpha(locked?.45:1);
            text(content,x,y,locked?'×':'+',30,locked?'#716d68':'#71838b');
          } else content.add(scene.add.image(x,y,`cz-ability-${item.icon}`).setDisplaySize(54,54).setTint(0xe8d5b2));
          const z=localHit(content,item.id,currentTab==='items'?'item':'ability',x,y,size,size,item.label+(currentTab==='abilities'?'\nПеретащите в быстрый доступ':locked?'\nНедоступно · требуется подходящий пояс':'\nПустой слот пояса'),()=>tip(currentTab==='items'?(locked?'Слот недоступен · демо':'Пустой слот пояса'):item.label+' · демо',x,y+PANEL_Y+CONTENT_INSET));
          if(currentTab==='abilities'){z.setData('controlAbility',item.id);scene.input.setDraggable(z);}
        });
        if(currentTab==='abilities'){
          text(content,317,240,`${page+1} / ${Math.ceil(abilities.length/PAGE_SIZE)}`,12);
          for(const [id,label,x,delta] of [['prev','‹',227,-1],['next','›',407,1]]){
            text(content,x,240,label,22);
            localHit(content,id,'page',x,240,65,44,label,()=>{page=(page+delta+Math.ceil(abilities.length/PAGE_SIZE))%Math.ceil(abilities.length/PAGE_SIZE);buildContent();});
          }
        }
      }
    }
    function rebuildQuick(){
      if(quickRoot)quickRoot.destroy();hits=hits.filter(h=>h.kind!=='quick');quickRects=[];
      const count=quickSlots.length;
      const slotSize=Math.max(36,Math.min(54,(layout.x-40)/ (count+.7)));
      const start=Math.max(12,layout.x-count*(slotSize+5)-20),y=options.height-slotSize-12;
      quickRoot=scene.add.container(0,0).setDepth(1005);
      for(let i=0;i<count;i++){
        const x=start+i*(slotSize+5),id=quickSlots[i],ability=abilities.find(a=>a.id===id);
        quickRoot.add(scene.add.image(x,y,KEY,'slot').setOrigin(0).setDisplaySize(slotSize,slotSize));
        if(ability)quickRoot.add(scene.add.image(x+slotSize/2,y+slotSize/2,`cz-ability-${ability.icon}`).setDisplaySize(slotSize*.66,slotSize*.66));
        const number=scene.add.text(x+4,y+3,String(i+1),{fontFamily:font(),fontSize:'12px',color:'#c1d2df',resolution:3});quickRoot.add(number);
        const z=scene.add.zone(x,y,slotSize,slotSize).setOrigin(0).setInteractive();quickRoot.add(z);
        z.on('pointerover',()=>{tooltip.setText(ability?.label||'Перетащите сюда способность');tooltip.setPosition(x,Math.max(8,y-tooltip.height-8)).setVisible(true);});
        z.on('pointerout',()=>tooltip.setVisible(false));
        z.on('pointerdown',()=>{if(ability){tooltip.setText(ability.label+' · демо');tooltip.setPosition(x,y-tooltip.height-8).setVisible(true);}});
        const rect={index:i,x,y,width:slotSize,height:slotSize};quickRects.push(rect);hits.push({...rect,id:`quick-${i}`,kind:'quick',center:{x:x+slotSize/2,y:y+slotSize/2}});
      }
    }
    function switchTab(id){
      if(!tabs.some(t=>t.id===id))return;
      requestedTab=id;tooltip.setVisible(false);rebuildFixed();
      if(transitioning||currentTab===id)return;
      transitioning=true;
      tween=scene.tweens.add({targets:rotor,angle:-90,duration:220,ease:'Sine.easeIn',onComplete:()=>{
        currentTab=requestedTab;page=0;buildContent();
        rotor.angle=90;
        tween=scene.tweens.add({targets:rotor,angle:0,duration:280,ease:'Sine.easeOut',onComplete:()=>{
          transitioning=false;tween=null;if(requestedTab!==currentTab)switchTab(requestedTab);
        }});
      }});
    }
    function pointerWorld(pointer){return scene.cameras.main.getWorldPoint(pointer.x,pointer.y);}
    const onDragStart=(pointer,object)=>{
      const id=object.getData('controlAbility');if(!id||transitioning)return;
      const a=abilities.find(a=>a.id===id),p=pointerWorld(pointer);
      ghost=scene.add.image(p.x,p.y,`cz-ability-${a.icon}`).setDisplaySize(48,48).setAlpha(.9).setDepth(1200);
      tooltip.setVisible(false);
    };
    const onDrag=(pointer,object)=>{if(object.getData('controlAbility')&&ghost){const p=pointerWorld(pointer);ghost.setPosition(p.x,p.y);}};
    const onDragEnd=(pointer,object)=>{
      const id=object.getData('controlAbility');if(!id)return;
      const p=pointerWorld(pointer),slot=quickRects.find(r=>p.x>=r.x&&p.x<=r.x+r.width&&p.y>=r.y&&p.y<=r.y+r.height);
      if(slot&&!transitioning){quickSlots[slot.index]=id;rebuildQuick();}
      ghost?.destroy();ghost=null;
    };
    scene.input.on('dragstart',onDragStart);scene.input.on('drag',onDrag);scene.input.on('dragend',onDragEnd);
    function resize(width,height){
      options={width,height};tween?.stop();tween=null;transitioning=false;currentTab=requestedTab;
      const scale=Math.max(.05,Math.min(.60*(width-32)/(1597-32),(height-30)/FRAME_H));
      layout={x:width-FRAME_W*scale-12,y:height-FRAME_H*scale-10,scale,width:FRAME_W*scale,height:FRAME_H*scale};
      root.setPosition(layout.x,layout.y).setScale(scale);rotor.angle=0;tooltip.setVisible(false);
      clip.clear().fillStyle(0xffffff).fillRect(layout.x,layout.y+PANEL_Y*scale,FRAME_W*scale,(FRAME_H-PANEL_Y)*scale);
      rebuildFixed();buildContent();rebuildQuick();
    }
    resize(options.width,options.height);
    return {
      resize,
      inspect:()=>({currentTab,requestedTab,transitioning,transitionAngle:rotor.angle,transitionStyle:'corner-rotation',page,attackCount,feints:[...selectedFeints],quickSlots:[...quickSlots],layout:{...layout},hits:hits.map(h=>({...h})),quickRects:quickRects.map(r=>({...r})),tokenCount:9,abilityCount:abilities.length,pageSize:PAGE_SIZE,dragonInteractive:false,profile:'low-wide-v3',crops:Object.fromEntries(Object.entries(CROPS).map(([name,rect])=>[name,[...rect]]))}),
      destroy(){if(closed)return;closed=true;tween?.stop();ghost?.destroy();root.destroy();paneMask.destroy();clip.destroy();quickRoot?.destroy();tooltip.destroy();scene.input.off('dragstart',onDragStart);scene.input.off('drag',onDrag);scene.input.off('dragend',onDragEnd);},
    };
  }
export default {preload,create};
