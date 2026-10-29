// Interactive place study: all actions are local demonstrations.
export function createArenaDraft(DraftPage){
  const spots=[
    {id:'registrar',name:'Распорядитель',hint:'Регистрация, правила и бой с тенью',point:[.19,.70],poly:[[.01,.58],[.13,.50],[.32,.61],[.32,.87],[.01,.97]]},
    {id:'duel',name:'Зал поединков',hint:'Схватки один на один',point:[.255,.43],poly:[[.14,.54],[.15,.30],[.22,.20],[.31,.20],[.355,.30],[.355,.59]]},
    {id:'main',name:'Главная арена',hint:'Командные бои и турнирные встречи',point:[.51,.42],poly:[[.435,.61],[.435,.23],[.47,.14],[.53,.14],[.573,.24],[.573,.60]]},
    {id:'board',name:'Турнирная доска',hint:'Объявления и предстоящие соревнования',point:[.765,.51],poly:[[.66,.39],[.835,.36],[.843,.73],[.659,.69]]},
    {id:'exit',name:'В город',hint:'Выход из здания арены',point:[.945,.56],poly:[[.87,.32],[.99,.27],[1,.77],[.87,.72]]},
  ];
  class ArenaDraft extends DraftPage{
    constructor(){super({key:'ArenaDraft'});this.state={place:null,showPlaces:true,notice:null};}
    preload(){super.preload();if(!this.textures.exists('arena-hall'))this.load.image('arena-hall','/ui-static/game/assets/places/painted/arena-hall.webp');}
    create(){super.create();this.events.once('shutdown',()=>{this.children.removeAll(true);if(this.textures.exists('arena-hall'))this.textures.remove('arena-hall');});}
    handleEscape(){if(this.state.place){this.state.place=null;this.draw();return true;}return false;}
    draw(){
      this.begin();this.cameras.main.setBackgroundColor('#10141a');
      const source=this.textures.get('arena-hall').getSourceImage(),scale=Math.min(this.w/source.width,this.h/source.height);
      const cover=Math.max(this.w/source.width,this.h/source.height);
      this.add.image(this.w/2,this.h/2,'arena-hall').setDisplaySize(source.width*cover,source.height*cover).setTint(0x34383f);
      const bw=source.width*scale,bh=source.height*scale,ox=(this.w-bw)/2,oy=(this.h-bh)/2;
      this.add.image(ox,oy,'arena-hall').setOrigin(0).setDisplaySize(bw,bh).setTint(0xb8b9bd);
      const pos=([x,y])=>({x:ox+x*bw,y:oy+y*bh});
      this.sceneSpots=[];
      for(const spot of spots){
        const pts=spot.poly.map(pos),center=pos(spot.point);
        const glow=this.add.graphics().setDepth(2);
        const drawGlow=(on)=>{glow.clear();if(on){glow.fillStyle(this.theme.accent.number,.10).fillPoints(pts,true);glow.lineStyle(3,this.theme.accent.number,.75).strokePoints(pts,true);glow.lineStyle(12,this.theme.accent.number,.07).strokePoints(pts,true);}};
        const shape=new Phaser.Geom.Polygon(pts);
        const zone=this.add.zone(0,0,this.w,this.h).setOrigin(0).setInteractive(shape,Phaser.Geom.Polygon.Contains);
        zone.input.cursor='pointer';
        const label=this.label(center.x,center.y,spot.name,19,'#f6e9cf',undefined,{backgroundColor:'#10141ae8',padding:{x:13,y:7}}).setOrigin(.5).setDepth(3).setAlpha(this.state.showPlaces?.92:0);
        const dot=this.add.circle(center.x,center.y-24,4,this.theme.accent.number).setStrokeStyle(1,0xf3e2ba).setDepth(3).setAlpha(this.state.showPlaces?1:0);
        zone.on('pointerover',()=>{drawGlow(true);label.setAlpha(1);dot.setAlpha(1);this.hoverText.setText(spot.hint);});
        zone.on('pointerout',()=>{drawGlow(false);label.setAlpha(this.state.showPlaces?.92:0);dot.setAlpha(this.state.showPlaces?1:0);this.hoverText.setText('Наведите на объект, чтобы узнать действие');});
        zone.on('pointerdown',()=>{this.state.place=spot.id;this.state.notice=null;this.draw();});
        this.sceneSpots.push({id:spot.id,...center});
      }
      this.add.rectangle(0,0,this.w,84,0x10141a,.83).setOrigin(0).setDepth(4);
      this.label(28,15,'Городская арена',29,'#f1e6d2',undefined,{fontFamily:this.theme.display}).setDepth(4);
      this.label(29,54,'Вестибюль · открыты залы и регистрация',15,'#b8c1c7').setDepth(4);
      const headerChildren=new Set(this.children.list);
      this.button('places',this.w-230,23,200,37,this.state.showPlaces?'Скрыть подписи':'Показать объекты',()=>{this.state.showPlaces=!this.state.showPlaces;this.draw();});
      for(const child of this.children.list)if(!headerChildren.has(child))child.setDepth(5);
      this.add.rectangle(0,this.h-47,this.w,47,0x10141a,.87).setOrigin(0).setDepth(4);
      this.hoverText=this.label(28,this.h-33,'Наведите на объект, чтобы узнать действие',16,'#ddd8cb').setDepth(4);
      if(this.state.place)this.drawPlace();
    }
    drawPlace(){
      const id=this.state.place,spot=spots.find(s=>s.id===id);
      // Modal blocks scene objects, but leaves the building visible around it.
      this.add.rectangle(0,0,this.w,this.h,0x090c10,.65).setOrigin(0).setInteractive().setDepth(10);
      const w=Math.min(660,this.w-90),h=Math.min(535,this.h-100),x=(this.w-w)/2,y=(this.h-h)/2;
      const before=new Set(this.children.list);
      this.panel(x,y,w,h);this.label(x+29,y+26,spot.name,29,this.theme.accent.css);
      this.button('close-place',x+w-60,y+24,32,32,'×',()=>{this.state.place=null;this.draw();});
      const descriptions={registrar:'Распорядитель откладывает журнал заявок.\n«Сначала выберите испытание. Я объясню правила и помогу подготовиться».',duel:'За дверью слышен звон клинков. Здесь принимают заявки на поединки один на один.',main:'Проход ведёт на большую арену. Здесь собираются команды и проходят турнирные встречи.',board:'На доске — объявления местных устроителей и приглашения на будущие межфракционные турниры.',exit:'За воротами — городская площадь. В этом черновике город ещё не собран.'};
      this.label(x+29,y+86,descriptions[id],18,undefined,w-58,{lineSpacing:10});
      const actions={registrar:['Узнать правила','Тренировка с тенью'],duel:['Подать заявку 1×1','Посмотреть текущие бои'],main:['Командные заявки','Условия участия'],board:['Местный турнир','Межфракционные встречи'],exit:['Вернуться в вестибюль']}[id];
      actions.forEach((name,i)=>this.button('place-action-'+i,x+29,y+240+i*59,w-58,48,name,()=>{if(id==='exit'){this.state.place=null;}else this.state.notice=`${name}: демонстрация. Серверное действие не отправлено.`;this.draw();}));
      this.label(x+29,y+h-85,this.state.notice||'Пробная сцена · действия пока демонстрационные',15,this.theme.dim.css,w-58);
      for(const child of this.children.list)if(!before.has(child))child.setDepth(11);
    }
    inspect(){return {...super.inspect(),spots:this.sceneSpots};}
  }
  return ArenaDraft;
}
