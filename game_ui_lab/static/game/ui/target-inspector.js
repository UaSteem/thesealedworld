/* Canvas-only demo inspector. Inspection never selects a combat target. */
(() => {
  const KEY='target-inspector-v1';
  const crops={panel:[1219,25,553,975],row:[22,1228,980,125],bar:[41,1435,943,88],
    attack:[26,1702,302,304],wait:[361,1702,303,304],defend:[696,1702,302,304]};
  function preload(scene){window.GameClientAssets.preload(scene,'combat-inspector');}
  function frames(scene){const texture=scene.textures.get(KEY);for(const [name,[x,y,w,h]] of Object.entries(crops))if(!texture.has(name))texture.add(name,0,x,y,w,h);}
  function create(scene,{top=12}={}){
    frames(scene);
    const root=scene.add.container(12,top).setDepth(900);
    const backing=scene.add.image(0,0,KEY,'panel').setOrigin(0).setInteractive();root.add(backing);
    const clip=scene.make.graphics({x:0,y:0,add:false}),mask=clip.createGeometryMask();
    let body=null,actor=null,width=230,height=470,scroll=0,total=0,hits=[],collapsed=false;
    const groups=new Set();
    const chrome=scene.add.container(0,0);root.add(chrome);
    const foldBg=scene.add.graphics().fillStyle(0x172029,.95).lineStyle(1,0x987d4a)
      .fillRect(-9,-8,18,16).strokeRect(-9,-8,18,16);chrome.add(foldBg);
    chrome.add(scene.add.text(0,-1,'−',{fontFamily:'Segoe UI',fontSize:'16px',color:'#ead3a2',resolution:3}).setOrigin(.5));
    const fold=scene.add.zone(0,0,22,22).setInteractive({useHandCursor:true});chrome.add(fold);
    const compact=scene.add.container(12,top).setDepth(901).setVisible(false);
    compact.add(scene.add.image(0,0,'control-zone-low-wide-v3','slot').setOrigin(0).setDisplaySize(44,44));
    const compactIcon=scene.add.image(22,22,KEY,'wait').setDisplaySize(32,32);compact.add(compactIcon);
    const expand=scene.add.zone(0,0,44,44).setOrigin(0).setInteractive({useHandCursor:true});compact.add(expand);
    const hover=scene.add.text(64,top,'',{fontFamily:'Segoe UI',fontSize:'13px',color:'#ead3a2',backgroundColor:'#111820',padding:{x:7,y:5},resolution:3}).setDepth(902).setVisible(false);
    function setCollapsed(value){collapsed=value;root.setVisible(!value);compact.setVisible(value);hover.setVisible(false);}
    fold.on('pointerdown',()=>setCollapsed(true));expand.on('pointerdown',()=>setCollapsed(false));
    expand.on('pointerover',()=>hover.setText(actor?.name||'Участник').setVisible(true));expand.on('pointerout',()=>hover.setVisible(false));
    const text=(x,y,value,size=12,color='#c5ced3',right=false)=>{
      const fontFamily=getComputedStyle(document.documentElement).getPropertyValue('--font-ui').trim()||'Segoe UI, sans-serif';
      const fontSize=size===11?13:size===12?14:size;
      const label=scene.add.text(Math.round(x),Math.round(y),String(value),{
        fontFamily,fontSize:`${fontSize}px`,fontStyle:'normal',color,
        resolution:3,padding:{x:0,y:1},
      }).setOrigin(right?1:0,0);
      body.add(label);return label;
    };
    function render(){
      body?.destroy();body=scene.add.container(0,0);root.add(body);body.setMask(mask);hits=[];
      if(!actor)return;
      const left=20,right=width-20,inner=right-left;
      text(left,22,actor.name,20,'#f0d8a2');text(left,49,`${actor.role} · Сила ${actor.power}`,11);
      const line=y=>{const g=scene.add.graphics().lineStyle(1,0x927446,.85).lineBetween(left,y,right,y);body.add(g);};
      line(72);
      [['Здоровье','hp',100,0xff252d],['Энергия','energy',40,0x299fea],['Стамина','stamina',50,0x62ca66]].forEach(([label,key,max,color],i)=>{
        const y=82+i*23,value=Math.round(actor.resources[key]*max);
        text(left,y,label);text(right,y,`${value} / ${max}`,12,'#f0d8a2',true);
      });
      line(154);
      [['Урон',actor.damage],['Точность',actor.accuracy],['Броня',actor.armor],['Уворот',actor.evasion]].forEach(([label,value],i)=>{
        text(left,166+i*21,label);text(right,166+i*21,value,12,'#edc87b',true);
      });
      line(256);text(left,267,`Намерение: ${actor.intentLabel}`,11,'#edc87b');
      text(left,288,'Нет активных эффектов',11,'#9caab3');
      const slot=Math.min(26,(inner-16)/5);
      for(let i=0;i<5;i++)body.add(scene.add.image(left+i*(slot+4),307,'control-zone-low-wide-v3','slot').setOrigin(0).setDisplaySize(slot,slot).setAlpha(.65));
      let y=307+slot+10;line(y);y+=10;
      const sections=[['attack','Атака',[['Урон',actor.damage],['Точность',actor.accuracy]]],
        ['defense','Защита',[['Броня',actor.armor],['Уворот',actor.evasion],['Парирование',actor.parry]]],
        ['other','Прочее',[['Сторона',actor.side==='enemy'?'Противник':'Союзник'],['Режим','Демонстрация']]]];
      for(const [id,title,rows] of sections){
        body.add(scene.add.image(left,y,KEY,'row').setOrigin(0).setDisplaySize(inner,27));
        text(left+10,y+6,`${groups.has(id)?'⌄':'›'} ${title}`,12,'#ead3a2');
        const rowY=y,zone=scene.add.zone(left,y,inner,27).setOrigin(0);
        zone.setInteractive(new Phaser.Geom.Rectangle(0,0,inner,27),(rect,x,py)=>rect.contains(x,py)&&rowY+py-scroll>=14&&rowY+py-scroll<=height-14);
        zone.input.cursor='pointer';body.add(zone);
        zone.on('pointerdown',()=>{groups.has(id)?groups.delete(id):groups.add(id);render();});
        hits.push({id,x:root.x+left+inner/2,y:root.y+y+13.5-scroll});y+=31;
        if(groups.has(id))for(const [label,value] of rows){text(left+5,y+2,label,11);text(right-5,y+2,value,11,'#edc87b',true);y+=23;}
      }
      total=y+12;scroll=Math.max(0,Math.min(scroll,Math.max(0,total-height+14)));body.y=-scroll;
      chrome.setPosition(width-30,26);root.bringToTop(chrome);
      compactIcon.setFrame(actor.intent||'wait');
    }
    function resize(w,h){width=Math.max(200,Math.min(230,w*.16));height=Math.max(80,Math.min(470,h-top-12));backing.setDisplaySize(width,height);
      clip.clear().fillStyle(0xffffff).fillRect(root.x+14,root.y+14,width-28,height-28);render();}
    const wheel=(pointer,objects,dx,dy)=>{if(collapsed||pointer.x<12||pointer.x>12+width||pointer.y<top||pointer.y>top+height)return;
      scroll=Math.max(0,Math.min(scroll+dy*.5,Math.max(0,total-height+14)));render();};
    scene.input.on('wheel',wheel);
    return {resize,show(value){if(actor?.id!==value.id)scroll=0;actor=value;render();},
      inspect:()=>({actorId:actor?.id,name:actor?.name,collapsed,foldPoint:{x:12+width-30,y:top+26},expandPoint:{x:34,y:top+22},groups:[...groups],scroll,total,width,height,hits:hits.map(h=>({...h}))}),
      destroy(){scene.input.off('wheel',wheel);root.destroy();compact.destroy();hover.destroy();mask.destroy();clip.destroy();}};
  }
  window.LabTargetInspector={preload,frames,create,key:KEY};
})();
