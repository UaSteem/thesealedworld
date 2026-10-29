import {createConstructionDemo} from './construction.js';

const root='/ui-static/game/assets/places/painted/';
const districts={
  administrative:{name:'Административный',file:'administrative-quarter.webp',subtitle:'Начало поселения · общий вклад в развитие',spots:[
    ['clerk','Представитель фракции',.16,.64,[.01,.48,.31,.92]],['hall','Общинный дом',.44,.43,[.34,.25,.54,.63]],
    ['construction','Три проекта',.69,.51,[.57,.36,.83,.65]],['store','Склад ресурсов',.91,.70,[.84,.42,.99,.87]]]},
  trading:{name:'Торговый',file:'trading-quarter.webp',subtitle:'Торговцы, аукцион и лавки жителей',spots:[
    ['merchant','Торговец',.16,.60,[.01,.36,.29,.88]],['auction','Аукционная доска',.55,.49,[.42,.31,.66,.68]],
    ['shops','Лавки игроков',.84,.58,[.70,.39,.99,.80]]]},
  crafting:{name:'Ремесленный',file:'crafting-quarter.webp',subtitle:'Мастера и услуги общего двора',spots:[
    ['forge','Кузнечный горн',.16,.61,[.01,.36,.31,.86]],['master','Стойка мастера',.54,.49,[.43,.34,.64,.66]],
    ['leather','Кожевенная мастерская',.74,.53,[.66,.34,.82,.68]],['wood','Столярная мастерская',.92,.55,[.85,.32,.99,.73]]]},
  residential:{name:'Жилой',file:'residential-quarter.webp',subtitle:'Участки и дома жителей',spots:[
    ['steward','Распорядитель участков',.12,.61,[.01,.36,.25,.87]],['house','Жилые дома',.48,.45,[.32,.29,.66,.59]],
    ['lot','Свободный участок',.85,.63,[.71,.43,.99,.83]]]},
};
const resources={wood:'Древесина',stone:'Камень',iron:'Железо'};

export function createDistrictDraft(DraftPage){
  return class DistrictDraft extends DraftPage{
    constructor(){super({key:'DistrictDraft'});this.state={district:'administrative',path:[],showPlaces:true,notice:null,lotOwned:false,houseBuilt:false};this.construction=createConstructionDemo();}
    init(data={}){if(districts[data.district])this.state.district=data.district;this.state.path=[];this.state.notice=null;}
    setDistrict(id){if(!districts[id])return;return window.GameClientRuntime.openDraft('districts',{district:id});}
    preload(){super.preload();const id=this.state.district,d=districts[id];if(!this.textures.exists('district-'+id))this.load.image('district-'+id,root+d.file);}
    create(){
      super.create();
      this.events.once('shutdown',()=>{this.children.removeAll(true);const key='district-'+this.state.district;if(this.textures.exists(key))this.textures.remove(key);});
    }
    go(id){this.state.path.push(id);this.state.notice=null;this.draw();}
    back(){this.state.path.pop();this.state.notice=null;this.draw();}
    handleEscape(){if(this.state.path.length){this.back();return true;}return false;}
    draw(){
      this.begin();const d=districts[this.state.district],key='district-'+this.state.district;
      const source=this.textures.get(key).getSourceImage(),cover=Math.max(this.w/source.width,this.h/source.height),fit=Math.min(this.w/source.width,this.h/source.height);
      this.add.image(this.w/2,this.h/2,key).setDisplaySize(source.width*cover,source.height*cover).setTint(0x34383f);
      const bw=source.width*fit,bh=source.height*fit,ox=(this.w-bw)/2,oy=(this.h-bh)/2;
      this.add.image(ox,oy,key).setOrigin(0).setDisplaySize(bw,bh).setTint(0xbfc0c2);
      this.sceneSpots=[];
      for(const [id,name,px,py,b]of d.spots){
        const x=ox+px*bw,y=oy+py*bh,rx=ox+b[0]*bw,ry=oy+b[1]*bh,rw=(b[2]-b[0])*bw,rh=(b[3]-b[1])*bh;
        const glow=this.add.graphics().setDepth(2);
        const label=this.label(x,y,name,18,'#f5e9d3',undefined,{backgroundColor:'#10141ae8',padding:{x:12,y:7}}).setOrigin(.5).setDepth(3).setAlpha(this.state.showPlaces?1:0);
        const zone=this.add.zone(rx,ry,rw,rh).setOrigin(0).setInteractive({useHandCursor:true});
        zone.on('pointerover',()=>{glow.lineStyle(2,this.theme.accent.number,.65).strokeRoundedRect(rx,ry,rw,rh,9);glow.fillStyle(this.theme.accent.number,.07).fillRoundedRect(rx,ry,rw,rh,9);label.setAlpha(1);this.hint.setText(name+' · нажмите, чтобы войти');});
        zone.on('pointerout',()=>{glow.clear();label.setAlpha(this.state.showPlaces?1:0);this.hint.setText('Наведите на объект квартала · все действия — локальная демонстрация');});
        zone.on('pointerdown',()=>this.go(id));this.sceneSpots.push({id,name,x,y});
      }
      this.add.rectangle(0,0,this.w,88,0x10141a,.91).setOrigin(0).setDepth(4);
      this.label(25,13,d.name+' квартал',28,'#efe5d5',undefined,{fontFamily:this.theme.display}).setDepth(4);
      this.label(26,52,d.subtitle,15,'#b7c1ca').setDepth(4);
      const before=new Set(this.children.list);
      this.button('district-exit',this.w-145,23,120,39,'В город',()=>window.GameClientRuntime.openDraft('city'));
      for(const c of this.children.list)if(!before.has(c))c.setDepth(5);
      this.add.rectangle(0,this.h-47,this.w,47,0x10141a,.9).setOrigin(0).setDepth(4);
      this.hint=this.label(25,this.h-32,'Наведите на объект квартала · все действия — локальная демонстрация',15,'#cbd0d3').setDepth(4);
      if(this.state.path.length)this.drawInterior();
    }
    drawInterior(){
      this.add.rectangle(0,0,this.w,this.h,0x080b10,.72).setOrigin(0).setInteractive().setDepth(10);
      const children=new Set(this.children.list),path=this.state.path,id=path.at(-1),construction=id==='construction';
      const w=Math.min(construction?1190:900,this.w-70),h=Math.min(construction?665:590,this.h-90),x=(this.w-w)/2,y=(this.h-h)/2;
      this.modal={x,y,width:w,height:h};this.panel(x,y,w,h);
      const titles={clerk:'Представитель фракции',hall:'Общинный дом',construction:'Развитие поселения',store:'Склад ресурсов',merchant:'Лавка торговца',auction:'Аукционная доска',shops:'Торговые ряды игроков',forge:'Кузнечный горн',master:'Услуги мастерских',leather:'Кожевенная мастерская',wood:'Столярная мастерская',steward:'Распорядитель участков',house:'Жилые дома',lot:'Свободный участок',shop0:'Лавка «Походные припасы»',shop1:'Лавка «Стальной клинок»',shop2:'Лавка «Травник»'};
      this.label(x+25,y+17,titles[id]||'Разговор',27,this.theme.accent.css);
      this.label(x+25,y+56,districts[this.state.district].name+' квартал'+(path.length>1?' / '+(titles[path[0]]||''):'')+' · вложение '+path.length,14,this.theme.dim.css);
      this.button('back',x+w-151,y+19,90,33,'Назад',()=>this.back());
      this.button('close-place',x+w-51,y+19,28,33,'×',()=>{this.state.path=[];this.draw();});
      this.line(x+25,y+87,w-50);
      if(construction)this.drawConstruction(x,y,w,h);
      else this.drawService(id,x,y,w,h);
      for(const c of this.children.list)if(!children.has(c))c.setDepth(11);
    }
    drawConstruction(x,y,w,h){
      const data=this.construction.inspect(),gap=16,cw=(w-50-gap*2)/3;
      this.label(x+25,y+103,'Куда сдаём ресурсы — то строим. Завершение одного проекта обнуляет ВСЕ три вклада.',16,this.theme.text.css,w-50);
      this.label(x+25,y+133,`Цикл ${data.cycle} · при себе: древесина ${data.inventory.wood}, камень ${data.inventory.stone}, железо ${data.inventory.iron}`,15,this.theme.dim.css);
      for(const [i,option]of data.options.entries()){
        const cx=x+25+i*(cw+gap),cy=y+171,ch=h-295;this.panel(cx,cy,cw,ch);
        this.label(cx+15,cy+13,option.name,20,this.theme.accent.css,cw-30);
        for(const [j,[resource,name]]of Object.entries(resources).entries()){
          const yy=cy+61+j*76,need=option.cost[resource],got=option.progress[resource];
          this.label(cx+15,yy,name,15,this.theme.dim.css);this.label(cx+cw-15,yy,`${got} / ${need}`,15).setOrigin(1,0);
          this.add.rectangle(cx+15,yy+25,cw-30,5,this.theme.cell.number).setOrigin(0);
          this.add.rectangle(cx+15,yy+25,(cw-30)*(need?got/need:1),5,this.theme.accent.number).setOrigin(0);
          const contribute=amount=>{const result=this.construction.contribute(option.id,resource,amount);this.state.notice=result.completed?'Квартал построен. Вклады всех проектов сброшены. Предложены три следующих проекта.':result.accepted?`Внесено: ${name.toLowerCase()} ${result.accepted}`:'Для этого взноса нет доступных ресурсов или потребности.';this.draw();};
          this.button(`give-${i}-${resource}`,cx+15,yy+36,(cw-38)/2,29,'Сдать 10',()=>contribute(10));
          this.button(`fill-${i}-${resource}`,cx+23+(cw-38)/2,yy+36,(cw-38)/2,29,'Доложить',()=>contribute(Math.max(1,need-got)));
        }
      }
      const built=data.built.map(v=>v.name).join(', ')||'пока нет';
      this.label(x+25,y+h-110,'Построено в демо: '+built,15,this.theme.dim.css,w-210);
      this.label(x+25,y+h-77,this.state.notice||'Числа и порядок предложений пробные. Сервер и реальные ресурсы не затрагиваются.',15,this.theme.accent.css,w-50);
      this.button('reset-demo',x+w-175,y+h-119,150,31,'Сбросить демо',()=>{this.construction.reset();this.state.notice=null;this.draw();});
    }
    drawService(id,x,y,w,h){
      const left=x+25,top=y+108,inner=w-50;
      const descriptions={clerk:'Здесь жители получают поручения и узнают, что требуется поселению.',hall:'Общий дом поселения. Городской совет и полномочия главы появятся позднее.',store:'Ресурсы можно направлять в один из трёх проектов на строительной доске.',merchant:'Ассортимент NPC. Цены и товары ниже — образцы для компоновки.',auction:'Общая торговая доска. Поиск и выставление лотов будут подключены к серверу.',shops:'Каждая лавка принадлежит отдельному игроку. Выберите лавку, чтобы посмотреть её ассортимент.',forge:'Ремонт и работа со снаряжением. Услуги показаны как локальные примеры.',master:'Выберите мастерскую. Её набор услуг будет зависеть от развития этого квартала.',leather:'Рабочее место кожевника: материалы и изделия.',wood:'Столярная мастерская: обработка дерева и заказы.',steward:'Здесь можно узнать о свободных участках и перейти к оформлению своего дома.',house:this.state.houseBuilt?'Ваш дом готов в демонстрационном состоянии.':'Входы в дома жителей. Покупка участка начинается у распорядителя.',lot:this.state.lotOwned?'Участок закреплён за вами в демо. Можно показать следующий шаг строительства.':'Свободный участок внутри жилого квартала. Городская карта показывает общий квартал.'};
      this.label(left,top,descriptions[id]||'Ассортимент выбранной лавки игрока.',18,undefined,inner,{lineSpacing:9});
      if(id==='shops'){
        ['Походные припасы','Стальной клинок','Травник'].forEach((name,i)=>{const yy=top+98+i*83;this.panel(left,yy,inner,69);this.label(left+17,yy+12,name,20,this.theme.accent.css);this.label(left+17,yy+40,['Владелец: Следопыт · 12 товаров','Владелец: Кузнец · 8 товаров','Владелец: Лиственница · 15 товаров'][i],14,this.theme.dim.css);this.button('shop-'+i,left+inner-145,yy+16,128,36,'Войти',()=>this.go('shop'+i));});
      }else if(['merchant','shop0','shop1','shop2'].includes(id)){
        const names=id==='shop1'?['Железный меч','Щит','Наконечники']:id==='shop2'?['Лечебные травы','Настой','Сухой сбор']:['Походный паёк','Верёвка','Фляга'];
        names.forEach((name,i)=>{const yy=top+85+i*74;this.line(left,yy-8,inner);this.label(left+10,yy+9,name,19);this.label(left+inner-185,yy+12,[12,25,8][i]+' монет',16,this.theme.accent.css);this.button('buy-'+i,left+inner-118,yy,118,39,'Купить',()=>{this.state.notice='Покупка — демонстрация. Товар и деньги не меняются.';this.draw();});});
      }else{
        const actions={clerk:[['Разговор о нуждах поселения','talk'],['К строительной доске','construction']],store:[['Открыть строительные проекты','construction']],hall:[],auction:[['Посмотреть лоты',null],['Выставить предмет',null]],forge:[['Ремонт снаряжения',null],['Заказы кузнецу',null]],master:[['Кожевенная мастерская','leather'],['Столярная мастерская','wood']],leather:[['Ассортимент изделий',null],['Обработка материалов',null]],wood:[['Заказы мастерской',null]],steward:[['Посмотреть свободный участок','lot']],house:this.state.houseBuilt?[['Войти в свой дом','home']]:[['К распорядителю','steward']],lot:this.state.lotOwned?[['Построить дом (демо)','build-house']]:[['Приобрести участок (демо)','buy-lot']],talk:[['Какие ресурсы сейчас нужны?','construction']],home:[]}[id]||[];
        actions.forEach(([name,next],i)=>this.button('service-'+i,left,top+118+i*60,inner,47,name,()=>{
          if(next==='buy-lot'){this.state.lotOwned=true;this.state.notice='Участок приобретён только в демо.';this.draw();}
          else if(next==='build-house'){this.state.houseBuilt=true;this.state.notice='Дом построен только в демо.';this.draw();}
          else if(next)this.go(next);else{this.state.notice='Пробный экран услуги. Серверное действие не отправляется.';this.draw();}
        }));
        if(id==='hall')this.label(left,top+135,'Совет пока недоступен · будущая функция',20,this.theme.dim.css,inner);
        if(id==='home')this.label(left,top+130,'Личное пространство · следующий уровень вложенной сцены',21,this.theme.accent.css,inner);
      }
      this.label(left,y+h-65,this.state.notice||'Демо-данные · реальные предметы, деньги и участки не изменяются',15,this.theme.dim.css,inner);
    }
    inspect(){return {...super.inspect(),spots:this.sceneSpots,modal:this.modal,construction:this.construction.inspect()};}
  };
}
