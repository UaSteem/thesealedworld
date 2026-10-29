// Transitional donor map. Square world addresses are preserved, not converted to hexes.
const tiles='/static/images/exploration/city/d4/map/v1/tiles_17x17_256/';
const services=[
  {x:8,y:8,name:'Портальная площадь',service:'svc_portal_hub',icon:'portal'},
  {x:7,y:7,name:'Арена',service:'svc_arena_main',target:'arena',icon:'arena'},
  {x:9,y:7,name:'Торговый квартал',service:'svc_market_hub',district:'trading',icon:'market'},
  {x:7,y:9,name:'Административный квартал',service:'svc_town_hall_hub',district:'administrative',icon:'default'},
  {x:9,y:9,name:'Постоялый двор',service:'svc_tavern_hub',icon:'tavern'},
  {x:6,y:10,name:'Ремесленный квартал',service:'svc_blacksmith_repair',district:'crafting',icon:'blacksmith'},
];
export function createCityDraft(DraftPage){
  return class CityDraft extends DraftPage{
    constructor(){super({key:'CityDraft'});this.state={selected:{x:8,y:8},player:{x:8,y:8},zoom:1,notice:null};}
    preload(){super.preload();for(let y=0;y<17;y++)for(let x=0;x<17;x++){
      const key=`old-city-${x}-${y}`;
      if(!this.textures.exists(key))this.load.image(key,tiles+`d4_${String(x).padStart(2,'0')}_${String(y).padStart(2,'0')}.webp`);
    }for(const icon of new Set(services.map(s=>s.icon)))if(!this.textures.exists('city-icon-'+icon))this.load.svg('city-icon-'+icon,`/static/images/ui/service-icons/${icon}.svg`,{width:40,height:40});}
    create(){super.create();this.wheel=(pointer,objects,dx,dy)=>{
      if(!this.sys.isActive())return;const p=this.cameras.main.getWorldPoint(pointer.x,pointer.y),b=this.mapBounds;
      if(p.x<b.x||p.x>b.x+b.width||p.y<b.y||p.y>b.y+b.height)return;
      this.state.zoom=Phaser.Math.Clamp(this.state.zoom+(dy<0?.12:-.12),.6,1.8);this.draw();
    };this.input.on('wheel',this.wheel);this.events.once('shutdown',()=>{this.input.off('wheel',this.wheel);this.mapMask?.destroy();this.mapMask=null;this.children.removeAll(true);for(const key of this.textures.getTextureKeys())if(key.startsWith('old-city-')||key.startsWith('city-icon-'))this.textures.remove(key);});}
    async enter(service){
      if(service.district){await window.GameClientRuntime.openDraft('districts',{district:service.district});}
      else if(service.target)await window.GameClientRuntime.openDraft(service.target);
      else{this.state.notice=service.name+': отдельная новая сцена ещё не подключена.';this.draw();}
    }
    draw(){
      this.mapMask?.destroy();this.mapMask=null;this.begin();const p=26,top=112,bottom=this.h-28,side=310,gap=20,mapW=this.w-p*2-side-gap,mapH=bottom-top;
      this.heading('Город · временная карта','Старая графика и адреса D4 · новый Phaser-клиент');
      this.panel(p,top,mapW,mapH);const sx=p+mapW+gap;this.panel(sx,top,side,mapH);
      const b={x:p+3,y:top+3,width:mapW-6,height:mapH-6};this.mapBounds=b;
      const maskGraphics=this.make.graphics({add:false});maskGraphics.fillStyle(0xffffff).fillRect(b.x,b.y,b.width,b.height);this.mapMask=maskGraphics.createGeometryMask();this.mapMask.geometryMask=maskGraphics;
      // Explicitly destroy the source Graphics with the mask at redraw.
      const destroyMask=this.mapMask.destroy.bind(this.mapMask);this.mapMask.destroy=()=>{destroyMask();maskGraphics.destroy();};
      const cell=Math.min(mapW/7,mapH/7)*this.state.zoom,cx=b.x+b.width/2,cy=b.y+b.height/2;
      const ox=cx-(this.state.selected.x+.5)*cell,oy=cy-(this.state.selected.y+.5)*cell;
      this.tilePoints=[];
      for(let y=0;y<17;y++)for(let x=0;x<17;x++){
        const tx=ox+x*cell,ty=oy+y*cell;
        this.add.image(tx,ty,`old-city-${x}-${y}`).setOrigin(0).setDisplaySize(cell+.2,cell+.2).setMask(this.mapMask);
        const center={x:tx+cell/2,y:ty+cell/2};
        if(center.x>=b.x&&center.x<=b.x+b.width&&center.y>=b.y&&center.y<=b.y+b.height)this.tilePoints.push({x,y,...{screenX:center.x,screenY:center.y}});
      }
      for(const s of services){const x=ox+(s.x+.5)*cell,y=oy+(s.y+.5)*cell;
        this.add.circle(x,y,16,this.theme.cell.number,.95).setStrokeStyle(1,this.theme.accent.number).setMask(this.mapMask);
        this.add.image(x,y,'city-icon-'+s.icon).setDisplaySize(23,23).setTint(this.theme.accent.number).setMask(this.mapMask);
      }
      const selected=this.state.selected,player=this.state.player;
      this.add.rectangle(ox+selected.x*cell,oy+selected.y*cell,cell,cell,0,0).setOrigin(0).setStrokeStyle(3,this.theme.accent.number).setMask(this.mapMask);
      this.add.circle(ox+(player.x+.5)*cell,oy+(player.y+.5)*cell,8,0x8ae6e6).setStrokeStyle(2,0x111a24).setMask(this.mapMask);
      const zone=this.add.zone(b.x,b.y,b.width,b.height).setOrigin(0).setInteractive({useHandCursor:true});zone.on('pointerdown',pointer=>{
        const world=this.cameras.main.getWorldPoint(pointer.x,pointer.y),x=Math.floor((world.x-ox)/cell),y=Math.floor((world.y-oy)/cell);
        if(x>=0&&x<17&&y>=0&&y<17){this.state.selected={x,y};this.state.notice=null;this.draw();}
      });
      const x=sx+20,inner=side-40;
      this.label(x,top+21,'Выбранное место',23,this.theme.accent.css);
      this.label(x,top+60,`Адрес: ${selected.x+44}_${selected.y+44}`,17);
      this.label(x,top+92,`Игрок: ${player.x+44}_${player.y+44}`,15,this.theme.dim.css);
      this.line(x,top+128,inner);
      const here=services.filter(s=>s.x===selected.x&&s.y===selected.y);
      this.label(x,top+146,here[0]?.name||(selected.x===0||selected.y===0||selected.x===16||selected.y===16?'Контур городской стены':'Городские улицы'),20,undefined,inner);
      here.forEach((s,i)=>this.button('enter-'+s.service,x,top+218+i*52,inner,42,'Войти',()=>this.enter(s)));
      const movable=selected.x>0&&selected.x<16&&selected.y>0&&selected.y<16;
      if(movable)this.button('place-player',x,top+284,inner,42,'Маркер сюда · демо',()=>{this.state.player={...selected};this.state.notice='Изменено только локальное положение маркера. Это не серверное перемещение.';this.draw();});
      this.label(x,top+348,this.state.notice||'Клик по тайлу — осмотр. Колёсико — масштаб. Доступность дорог и переходов здесь не проверяется сервером.',15,this.theme.dim.css,inner);
      this.label(x,bottom-70,'Бирюзовая точка — игрок.\nЗолотые знаки — старые сервисы.',14,this.theme.dim.css,inner);
      this.button('center-city',this.w-363,30,155,36,'К игроку',()=>{this.state.selected={...this.state.player};this.draw();});
      this.button('overview-city',this.w-195,30,168,36,'Обзор города',()=>{this.state.zoom=.6;this.draw();});
    }
    inspect(){return {...super.inspect(),services,mapBounds:this.mapBounds,tilePoints:this.tilePoints};}
  };
}
