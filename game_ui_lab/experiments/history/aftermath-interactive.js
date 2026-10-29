// Aftermath presentation only: no claim/respawn request or authoritative losses.
const sampleSources=()=>[
  {id:'raider',name:'Налётчик',note:'После последнего размена',items:[
    {id:'sword',name:'Ржавый меч',amount:1,kind:'Снаряжение',description:'Потёртый клинок. Предмет для примерки карточки добычи.',details:'Одноручное оружие · состояние: изношено',art:true},
    {id:'iron',name:'Обломки железа',amount:6,kind:'Материал',description:'Небольшая связка металла, найденная среди вещей противника.',details:'Материал · количество: 6'}]},
  {id:'guard',name:'Страж прохода',note:'Найдено на поле боя',items:[
    {id:'hide',name:'Грубая кожа',amount:3,kind:'Материал',description:'Пример ресурса в списке добычи.',details:'Материал · количество: 3'},
    {id:'coins',name:'Монеты',amount:18,kind:'Валюта',description:'Демонстрационная запись. Баланс персонажа не меняется.',details:'Количество: 18'}]},
  {id:'cache',name:'Дорожный свёрток',note:'Осмотренное место',items:[
    {id:'ration',name:'Походные припасы',amount:2,kind:'Расходник',description:'Пример расходуемого предмета после осмотра источника.',details:'Количество: 2'}]},
];

export function createAftermathScenes(DraftPage){
  class LootDraft extends DraftPage{
    constructor(){super({key:'LootDraft'});this.sources=sampleSources();this.state={source:'all',detail:null,taken:0,notice:null};}
    preload(){
      super.preload();
      const fixture=document.getElementById('inventory-data');
      try{const item=JSON.parse(fixture?.textContent||'{}').items?.[0];if(item?.texture_url&&!this.textures.exists('loot-demo-sword'))this.load.image('loot-demo-sword',item.texture_url);}catch{/* art is optional, data stays local */}
    }
    allItems(){return this.sources.flatMap(source=>source.items.map(item=>({...item,sourceId:source.id,sourceName:source.name})));}
    visibleItems(){return this.allItems().filter(item=>this.state.source==='all'||item.sourceId===this.state.source);}
    claim(ids){
      const allowed=new Set(ids);let taken=0;
      for(const source of this.sources){source.items=source.items.filter(item=>{if(!allowed.has(item.id))return true;taken++;return false;});}
      this.state.taken+=taken;this.state.detail=null;
      this.state.notice=taken?`Забрано позиций: ${taken}. Только локальное демо, инвентарь не изменён.`:'Здесь уже ничего не осталось.';
      this.draw();
    }
    handleEscape(){if(this.state.detail){this.state.detail=null;this.draw();return true;}return false;}
    draw(){
      this.begin();const p=this.pad;this.heading('После боя','Осмотрите источники и выберите, что забрать');
      const top=p+92,foot=this.h-p-52,bodyH=foot-top-18,sourceW=255,detailsW=315,gap=20;
      const listX=p+sourceW+gap,listW=this.w-p*2-sourceW-detailsW-gap*2,detailX=listX+listW+gap;
      this.panel(p,top,sourceW,bodyH);this.panel(listX,top,listW,bodyH);this.panel(detailX,top,detailsW,bodyH);
      this.label(p+20,top+20,'Источники',22,this.theme.accent.css);
      this.button('source-all',p+17,top+65,sourceW-34,42,`Все · ${this.allItems().length}`,()=>{this.state.source='all';this.state.detail=null;this.draw();},{active:this.state.source==='all'});
      this.sources.forEach((source,i)=>{const y=top+125+i*94;this.button('source-'+source.id,p+17,y,sourceW-34,55,source.name,()=>{this.state.source=source.id;this.state.detail=null;this.draw();},{active:this.state.source===source.id});this.label(p+21,y+62,source.items.length?`${source.items.length} позиций`:'Осмотрено · пусто',14,this.theme.dim.css);});
      this.label(listX+22,top+20,this.state.source==='all'?'Вся добыча':this.sources.find(s=>s.id===this.state.source).name,22,this.theme.accent.css);
      const items=this.visibleItems(),rowH=Math.min(80,(bodyH-90)/5);
      if(!items.length){this.label(listX+listW/2,top+bodyH*.43,'Здесь пусто',25,this.theme.dim.css).setOrigin(.5);this.label(listX+listW/2,top+bodyH*.43+43,'Выберите другой источник или продолжите путь.',16,this.theme.dim.css).setOrigin(.5);}
      items.forEach((item,i)=>{const y=top+65+i*rowH;const active=this.state.detail===item.id;
        this.button('item-'+item.id,listX+15,y,listW-30,rowH-8,'',()=>{this.state.detail=item.id;this.draw();},{active});
        if(item.art&&this.textures.exists('loot-demo-sword')){const art=this.add.image(listX+46,y+(rowH-8)/2,'loot-demo-sword');const src=art.texture.getSourceImage();art.setDisplaySize(42*src.width/src.height,42);}
        else this.label(listX+43,y+(rowH-8)/2,'◇',24,this.theme.accent.css).setOrigin(.5);
        this.label(listX+77,y+10,item.name,18,active?this.theme.accent.css:this.theme.text.css,listW-185);
        this.label(listX+77,y+35,item.sourceName+' · '+item.kind,13,this.theme.dim.css,listW-185);
        this.label(listX+listW-33,y+19,'×'+item.amount,17,this.theme.accent.css).setOrigin(1,0);
      });
      const selected=this.allItems().find(item=>item.id===this.state.detail);
      this.label(detailX+20,top+20,'Осмотр предмета',22,this.theme.accent.css);
      if(selected){
        let y=top+71;
        if(selected.art&&this.textures.exists('loot-demo-sword')){const art=this.add.image(detailX+detailsW/2,top+132,'loot-demo-sword'),src=art.texture.getSourceImage();art.setDisplaySize(115*src.width/src.height,115);y=top+211;}
        this.label(detailX+20,y,selected.name,22,this.theme.text.css,detailsW-40);
        this.label(detailX+20,y+67,selected.description,16,this.theme.dim.css,detailsW-40,{lineSpacing:7});
        this.label(detailX+20,y+173,selected.details,15,this.theme.accent.css,detailsW-40);
        this.button('take-one',detailX+20,top+bodyH-68,detailsW-40,44,'Забрать предмет',()=>this.claim([selected.id]));
      }else this.label(detailX+20,top+80,'Нажмите на предмет, чтобы посмотреть описание.',18,this.theme.dim.css,detailsW-40,{lineSpacing:10});
      this.label(p,foot-23,this.state.notice||'Демо добычи · реальные предметы и награды не выдаются',14,this.theme.dim.css,this.w-p*2-560);
      this.button('take-all',this.w-p-520,foot,242,45,this.state.source==='all'?'Забрать всё':'Забрать источник',()=>this.claim(this.visibleItems().map(item=>item.id)));
      this.button('continue',this.w-p-262,foot,262,45,'Продолжить · в город',()=>window.GameClientRuntime.openDraft('city'),{active:true});
      this.button('reset-loot',p,foot+4,170,36,'Восстановить демо',()=>{this.sources=sampleSources();this.state={source:'all',detail:null,taken:0,notice:null};this.draw();});
    }
    inspect(){return {...super.inspect(),sources:this.sources.map(s=>({...s,items:s.items.map(item=>({...item}))})),items:this.allItems()};}
  }

  class DeathDraft extends DraftPage{
    constructor(){super({key:'DeathDraft'});this.state={confirm:false,respawns:0};}
    handleEscape(){if(this.state.confirm){this.state.confirm=false;this.draw();return true;}return false;}
    draw(){
      this.begin();const w=Math.min(1110,this.w-100),h=Math.min(615,this.h-100),x=(this.w-w)/2,y=(this.h-h)/2;
      const g=this.add.graphics();g.fillStyle(0x24171b,.55);g.fillCircle(x+w*.22,y+h*.45,170);g.lineStyle(1,this.theme.line.number,.6);g.strokeCircle(x+w*.22,y+h*.45,145);g.lineStyle(2,this.theme.accent.number,.28);g.strokeCircle(x+w*.22,y+h*.45,158);
      this.label(x+w*.22,y+h*.45-58,'×',100,'#bc7f77',undefined,{fontFamily:this.theme.display}).setOrigin(.5);
      this.label(x+w*.22,y+h*.45+39,'Поход завершён',25,this.theme.accent.css,undefined,{fontFamily:this.theme.display}).setOrigin(.5);
      this.label(x+w*.22,y+h*.45+88,'Возвращение к точке возрождения',15,this.theme.dim.css,260,{align:'center'}).setOrigin(.5);
      const px=x+w*.44,pw=w*.56;this.panel(px,y,pw,h);
      this.label(px+30,y+27,'Вы погибли',34,this.theme.text.css,undefined,{fontFamily:this.theme.display});
      this.label(px+30,y+81,'Пример итогов незавершённого похода',17,this.theme.dim.css,pw-60);
      this.line(px+30,y+126,pw-60);
      const losses=[['Неподтверждённый опыт','240'],['Затронутые навыки','2'],['Найденные предметы','3'],['Найденные ресурсы','18']];
      losses.forEach(([name,value],i)=>{const yy=y+151+i*57;this.label(px+30,yy,name,18,this.theme.dim.css,pw-140);this.label(px+pw-30,yy,value,22,'#d99d8f').setOrigin(1,0);if(i<3)this.line(px+30,yy+40,pw-60);});
      this.label(px+30,y+h-193,'Числа условные. Окончательные потери и место возрождения определяет сервер. Экипировка персонажа в демо не меняется.',15,this.theme.dim.css,pw-60,{lineSpacing:6});
      if(!this.state.confirm)this.button('respawn',px+30,y+h-93,pw-60,52,'Вернуться в город · демо',()=>{this.state.confirm=true;this.draw();},{active:true});
      else{
        this.label(px+30,y+h-111,'Вернуться к городской точке возрождения?',17,this.theme.accent.css,pw-60);
        this.button('cancel-respawn',px+30,y+h-69,(pw-72)/2,42,'Остаться',()=>{this.state.confirm=false;this.draw();});
        this.button('confirm-respawn',px+42+(pw-72)/2,y+h-69,(pw-72)/2,42,'Вернуться',()=>{this.state.confirm=false;this.state.respawns++;window.GameClientRuntime.openDraft('city');},{active:true});
      }
      this.label(x,y+h+15,'Локальная сцена · не выполняет смерть, списание ресурсов или серверное воскрешение',14,this.theme.dim.css,w);
    }
    inspect(){return {...super.inspect(),losses:{pendingXp:240,skillCount:2,itemCount:3,resourceCount:18}};}
  }
  return [LootDraft,DeathDraft];
}
