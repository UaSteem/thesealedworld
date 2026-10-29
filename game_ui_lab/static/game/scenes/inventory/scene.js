import {packInventory,inventoryFilters,filterItems,mockWeight} from './data.js';
// Reuse existing frontend SVGs and their existing attribution files.
const filterIcons={all:'/static/images/ui/inventory-icons/items.svg',weapons:'/static/images/ui/inventory-gear/weapon_sword.svg',armor:'/static/images/ui/inventory-gear/torso.svg',accessories:'/static/images/ui/inventory-gear/ring.svg',consumables:'/static/images/ui/inventory-gear/consumable.svg',resources:'/static/images/ui/inventory-gear/resource.svg',quest:'/static/images/ui/inventory-gear/quest.svg'};
// Presentation-only scene. Local selection never changes the frozen inventory.
export function inventoryScene(data, t, options={}) {
  const P=window.Phaser;
  return class InventoryScene extends P.Scene {
    constructor(){super('InventoryWorkspace');this.current=null;this.pinned=false;this.scroll=0;this.bagScroll=0;this.filter='all';this.notice=null;}
    preload(){data.items.forEach(item=>{if(!this.textures.exists(item.item_id))this.load.image(item.item_id,item.texture_url);});for(const [id,url] of Object.entries(filterIcons))if(!this.textures.exists(`filter-${id}`))this.load.svg(`filter-${id}`,url,{width:48,height:48});}
    create(){
      this.cameras.main.roundPixels=true;
      this.game.canvas.tabIndex=0;
      this.game.canvas.setAttribute('aria-label','Инвентарь: наведите на предмет, нажмите для закрепления. Стрелки выбирают предмет, Escape закрывает.');
      this.input.on('pointermove',p=>{p=this.pointerPoint(p);if(this.pinned||this.notice||this.tabs?.some(tab=>tab.bounds.contains(p.x,p.y))||this.footerBounds?.contains(p.x,p.y))return;const i=this.hit(p);if(i!==this.current){this.current=i;this.anchor={x:p.x,y:p.y};this.scroll=0;this.draw();}});
      this.input.on('pointerdown',p=>{p=this.pointerPoint(p);this.game.canvas.focus({preventScroll:true});if(this.notice){if(this.noticeClose?.contains(p.x,p.y)){this.notice=null;this.draw();}return;}if(this.pinned&&this.actionBounds?.contains(p.x,p.y)){this.notice=`${data.mainHandOccupied?'Замена':'Надевание'} «${this.current.name}»: макет, сервер не подключён.\nПредметы и экипировка сохраняются.`;this.draw();return;}if(this.pinned&&this.close?.contains(p.x,p.y)){this.clear();return;}if(this.pinned&&this.cardBounds?.contains(p.x,p.y)){this.pinned=true;this.draw();return;}const tab=this.tabs?.find(tab=>tab.bounds.contains(p.x,p.y));if(tab){this.filter=tab.id;this.bagScroll=0;this.clear();return;}const footer=this.footerActions?.find(action=>action.bounds.contains(p.x,p.y));if(footer){this.notice=`${footer.label}: локальный макет.\n${footer.id==='craft'?'Рецепты и изготовление':'Выбор предметов и разборка'} пока не подключены. Предметы сохраняются.`;this.draw();return;}if(this.footerBounds?.contains(p.x,p.y))return;const i=this.hit(p);if(i){this.current=i;this.pinned=true;this.anchor={x:p.x,y:p.y};this.scroll=0;this.draw();}else this.clear();});
      this.input.on('wheel',(p,_over,_dx,dy,_dz,event)=>{p=this.pointerPoint(p);if(this.notice){event?.preventDefault();return;}if(this.pinned&&this.cardBounds?.contains(p.x,p.y)){event?.preventDefault();this.scroll=P.Math.Clamp(this.scroll+dy,0,this.maxScroll||0);this.draw();}else if(this.bagBounds.contains(p.x,p.y)){event?.preventDefault();this.bagScroll=P.Math.Clamp(this.bagScroll+dy,0,this.maxBagScroll);this.draw();}});
      const leaveCanvas=()=>{if(this.scene.isActive()&&!this.pinned)this.clear();};
      this.game.canvas.addEventListener('pointerleave',leaveCanvas);
      const escapeCard=event=>{
        if(!this.scene.isActive())return;
        const target=event.target;
        const editing=target instanceof Element && (target.closest('input,textarea,select') || target.isContentEditable);
        if(event.key==='Escape' && !editing){if(this.notice){event.preventDefault();this.notice=null;this.draw();}else if(this.current){event.preventDefault();this.clear();}}
      };
      window.addEventListener('keydown',escapeCard);
      this.input.keyboard.on('keydown',event=>{if(!this.scene.isActive()||document.activeElement!==this.game.canvas||this.notice)return;const visible=filterItems(data.items,this.filter);if(!visible.length)return;if(['ArrowRight','ArrowLeft'].includes(event.key)){event.preventDefault();const index=visible.indexOf(this.current);this.current=visible[(index+(event.key==='ArrowRight'?1:visible.length-1))%visible.length];this.pinned=true;const bounds=this.placements.find(entry=>entry.item===this.current)?.bounds;this.anchor=bounds?{x:bounds.right,y:Math.max(this.bagBounds.y,bounds.y)}:{x:20,y:20};this.scroll=0;this.draw();}if(['ArrowDown','ArrowUp'].includes(event.key)&&this.current){event.preventDefault();this.scroll=P.Math.Clamp(this.scroll+(event.key==='ArrowDown'?36:-36),0,this.maxScroll||0);this.draw();}});
      this.scale.on('resize',this.draw,this);
      this.events.on('wake',this.draw,this);
      this.events.once('shutdown',()=>{
        window.removeEventListener('keydown',escapeCard);
        this.game.canvas.removeEventListener('pointerleave',leaveCanvas);
        this.scale.off('resize',this.draw,this);
        this.events.off('wake',this.draw,this);
      });
      this.draw();
    }
    pointerPoint(pointer){return options.viewport?this.cameras.main.getWorldPoint(pointer.x,pointer.y):pointer;}
    clear(){this.current=null;this.pinned=false;this.scroll=0;this.draw();}
    hit(p){if(!this.bagBounds?.contains(p.x,p.y))return null;return this.placements?.find(entry=>entry.bounds.contains(p.x,p.y))?.item||null;}
    text(x,y,value,size=13,color=t.text.css,wrap=0,display=false){return this.add.text(Math.round(x),Math.round(y),String(value),{fontFamily:display?t.display:t.font,fontSize:`${size}px`,color,lineSpacing:3,...(wrap?{wordWrap:{width:wrap,useAdvancedWrap:true}}:{})}).setResolution(Math.max(2,window.devicePixelRatio||1));}
    box(x,y,w,h,fill=t.panel.number,line=t.line.number,alpha=1){const g=this.add.graphics();g.fillStyle(fill,alpha).fillRoundedRect(x,y,w,h,5);g.lineStyle(1,line,.65).strokeRoundedRect(x+.5,y+.5,w-1,h-1,5);return g;}
    draw(){
      this.detailMask?.destroy();this.detailMask=null;this.bagMask?.destroy();this.bagMask=null;
      this.children.removeAll(true);
      const viewport=options.viewport?options.viewport():{width:this.scale.width,height:this.scale.height};
      const w=viewport.width,h=viewport.height;
      if(options.viewport){const renderScale=options.renderScale||1;this.cameras.main.setViewport(0,0,w*renderScale,h*renderScale).setZoom(renderScale).centerOn(w/2,h/2);}
      this.cameras.main.setBackgroundColor(t.bg.number);
      // Geometry follows available space, never selected art or name length.
      const pad=20,bagW=w-pad*2,top=18;
      const columns=Math.max(8,Math.floor((bagW+5)/57));
      const cell=Math.max(48,Math.min(64,Math.floor((bagW-(columns-1)*5)/columns))),step=cell+5,gridW=columns*step-5;
      this.cardBounds=null;this.close=null;this.actionBounds=null;
      const gx=pad+Math.floor((bagW-gridW)/2);
      const headingY=top,gy=headingY+85;
      const visible=filterItems(data.items,this.filter);
      this.text(gx,headingY,'Рюкзак',25,t.text.css,0,true);
      const countLabel=this.filter==='all'?`Всего: ${data.items.length} предметов`:`Показано: ${visible.length} из ${data.items.length}`;
      this.text(gx+gridW,headingY+9,`${countLabel}${data.mockCopies>1?' · MOCK ×'+data.mockCopies:''}`,11,t.dim.css).setOrigin(1,0);
      this.tabs=[];
      const tabW=gridW/inventoryFilters.length,tabY=headingY+35,baseY=tabY+38;
      const frame=this.add.graphics();
      frame.fillStyle(t.panel.number).fillRect(gx-8,baseY,gridW+16,h-baseY-12);
      frame.lineStyle(1,t.line.number).beginPath().moveTo(gx-7.5,baseY+.5).lineTo(gx-7.5,h-12.5).lineTo(gx+gridW+7.5,h-12.5).lineTo(gx+gridW+7.5,baseY+.5).strokePath();
      inventoryFilters.forEach((filter,index)=>{
        const tx=Math.round(gx+index*tabW),tw=Math.round(tabW)-3,active=this.filter===filter.id,ty=tabY+(active?0:4),th=baseY-ty;
        const shape=this.add.graphics();
        shape.fillStyle(active?t.panel.number:t.cell.number).fillRoundedRect(tx,ty,tw,th+2,{tl:6,tr:6,bl:0,br:0});
        shape.lineStyle(1,active?t.accent.number:t.line.number,active?.9:.6).beginPath().moveTo(tx+.5,baseY).lineTo(tx+.5,ty+6).lineTo(tx+6,ty+.5).lineTo(tx+tw-6,ty+.5).lineTo(tx+tw-.5,ty+6).lineTo(tx+tw-.5,baseY).strokePath();
        if(!active)shape.lineStyle(1,t.line.number).lineBetween(tx,baseY+.5,tx+tw,baseY+.5);
        else shape.lineStyle(2,t.accent.number,.8).lineBetween(tx+9,ty+1,tx+tw-9,ty+1);
        if(this.textures.exists(`filter-${filter.id}`))this.add.image(tx+19,ty+19,`filter-${filter.id}`).setDisplaySize(20,20).setTint(active?t.accent.number:t.dim.number);
        this.text(tx+35,ty+12,filter.label,11,active?t.text.css:t.dim.css);
        this.text(tx+tw-9,ty+12,filterItems(data.items,filter.id).length,10,active?t.accent.css:t.dim.css).setOrigin(1,0);
        this.tabs.push({id:filter.id,bounds:new P.Geom.Rectangle(tx,ty,tw,th)});
      });
      const viewportH=Math.max(20,h-gy-79);
      this.bagBounds=new P.Geom.Rectangle(gx,gy,gridW,viewportH);
      const packed=packInventory(visible,columns,0);
      const contentH=Math.max(0,packed.rows*step-5);
      // Fill the viewport with empty cells; only actual content creates overflow.
      packed.rows=Math.max(packed.rows,Math.ceil((viewportH+5)/step));
      const gridH=packed.rows*step-5;
      this.maxBagScroll=Math.max(0,contentH-viewportH);this.bagScroll=P.Math.Clamp(this.bagScroll,0,this.maxBagScroll);
      this.bagMask=this.make.graphics({x:0,y:0,add:false});this.bagMask.fillRect(gx,gy,gridW,viewportH);
      const bag=this.add.container(0,0);bag.setMask(this.bagMask.createGeometryMask());
      const add=object=>{bag.add(object);return object;};
      for(let row=0;row<packed.rows;row++)for(let col=0;col<columns;col++)add(this.box(gx+col*step,gy+row*step-this.bagScroll,cell,cell,t.cell.number,t.line.number));
      this.placements=[];
      for(const entry of packed.placements){
        const {item,col,row,width,height}=entry,x=gx+col*step,y=gy+row*step-this.bagScroll,iw=width*step-5,ih=height*step-5,selected=this.current===item;
        add(this.box(x,y,iw,ih,t.panel.number,selected?t.accent.number:t.tiers[item.tier].number));
        if(this.textures.exists(item.item_id)){const image=this.add.image(Math.round(x+iw/2),Math.round(y+ih/2),item.item_id);image.setScale(Math.min((iw-12)/image.width,(ih-14)/image.height));add(image);}
        add(this.text(x+5,y+ih-18,`T${item.tier}`,10,t.tiers[item.tier].css));
        if(selected){const g=this.add.graphics();g.lineStyle(2,t.accent.number).strokeRoundedRect(x+1,y+1,iw-2,ih-2,4);add(g);}
        this.placements.push({item,bounds:new P.Geom.Rectangle(x,y,iw,ih)});
      }
      if(this.maxBagScroll){const g=this.add.graphics(),thumb=Math.max(20,viewportH*viewportH/gridH);g.fillStyle(t.line.number,.35).fillRoundedRect(gx+gridW+6,gy,3,viewportH,1);g.fillStyle(t.accent.number,.8).fillRoundedRect(gx+gridW+6,gy+(viewportH-thumb)*this.bagScroll/this.maxBagScroll,3,thumb,1);}
      if(!visible.length){this.box(gx+20,gy+20,Math.min(420,gridW-40),76,t.panel.number);this.text(gx+36,gy+34,'В этой категории пока нет предметов',17,t.text.css);this.text(gx+36,gy+62,'В слепке стенда доступны только шесть мечей',11,t.dim.css);}
      const fy=h-69,weight=mockWeight(data.items),weightW=Math.max(190,gridW-310);
      this.footerBounds=new P.Geom.Rectangle(gx,fy,gridW,54);this.box(gx,fy,gridW,49,t.panel.number);
      this.text(gx+12,fy+5,`Вес · MOCK ${weight.value.toFixed(1)} / ${weight.limit} кг`,12,t.accent.css);
      this.text(gx+12,fy+27,`Включая надетое: ${weight.worn} кг (макет)`,9,t.dim.css);
      const bar=this.add.graphics();bar.fillStyle(t.line.number,.4).fillRoundedRect(gx+weightW-112,fy+19,100,5,2);bar.fillStyle(t.accent.number).fillRoundedRect(gx+weightW-112,fy+19,100*Math.min(1,weight.value/weight.limit),5,2);
      this.footerActions=[{id:'disassembly',label:'Разборка'},{id:'craft',label:'Крафт'}].map((action,index)=>{const x=gx+gridW-284+index*138;this.box(x,fy+8,128,32,t.cell.number,t.accent.number);this.text(x+64,fy+15,action.label,13,t.accent.css).setOrigin(.5,0);return {...action,bounds:new P.Geom.Rectangle(x,fy+8,128,32)};});
      if(this.current){
        const cardW=Math.min(380,w-24),cardH=Math.min(620,h-24),anchor=this.anchor||{x:gx+cell,y:gy};
        // Prefer the right of the anchor, then the left; clamp all four edges.
        const preferredX=anchor.x+18+cardW<=w-12?anchor.x+18:anchor.x-cardW-18;
        const cardX=Math.round(P.Math.Clamp(preferredX,12,w-cardW-12));
        const cardY=Math.round(P.Math.Clamp(anchor.y-30,12,h-cardH-12));
        this.cardBounds=new P.Geom.Rectangle(cardX,cardY,cardW,cardH);
        this.drawCard(cardX,cardY,cardW,cardH);
      }
      if(this.notice)this.drawNotice(w,h);
      window.inventoryLabState={filter:this.filter,visibleCount:visible.length,weight,notice:this.notice,action:this.pinned?(data.mainHandOccupied?'Заменить':'Надеть'):null,footerBounds:{x:gx,y:fy,width:gridW,height:49},selectedId:this.current?.item_id||null,pinned:this.pinned,width:w,height:h,textures:data.items.filter(i=>this.textures.exists(i.item_id)).length,cardScroll:this.scroll,bagScroll:this.bagScroll,bagRows:packed.rows,columns,popupBounds:this.cardBounds?{x:this.cardBounds.x,y:this.cardBounds.y,width:this.cardBounds.width,height:this.cardBounds.height}:null,itemCount:data.items.length,cellSize:cell,maxBagScroll:this.maxBagScroll,bagBounds:{x:gx,y:gy,width:gridW,height:viewportH},textResolution:Math.max(2,window.devicePixelRatio||1)};
    }
    drawNotice(w,h){
      this.box(0,0,w,h,t.bg.number,t.line.number,.85);
      const nw=Math.min(450,w-40),nh=Math.min(190,h-40),x=(w-nw)/2,y=(h-nh)/2;
      this.box(x,y,nw,nh,t.panel.number,t.accent.number);
      this.text(x+20,y+16,'Локальный макет',24,t.accent.css,nw-40,true);
      this.text(x+20,y+57,this.notice,13,t.text.css,nw-40);
      this.noticeClose=new P.Geom.Rectangle(x+nw-118,y+nh-42,98,30);
      this.box(this.noticeClose.x,this.noticeClose.y,98,30,t.cell.number,t.accent.number);
      this.text(this.noticeClose.x+49,this.noticeClose.y+6,'Закрыть',12,t.accent.css).setOrigin(.5,0);
    }
    drawCard(x,y,w,h){
      this.box(x,y,w,h,t.panel.number,t.line.number);
      if(this.pinned){this.actionBounds=new P.Geom.Rectangle(x+18,y+h-40,w-36,30);this.box(x+18,y+h-40,w-36,30,t.cell.number,t.accent.number);this.text(x+w/2,y+h-34,data.mainHandOccupied?'Заменить':'Надеть',13,t.accent.css).setOrigin(.5,0);}
      const i=this.current;
      this.text(x+18,y+13,this.pinned?'ПРОСМОТР ЗАКРЕПЛЁН':'ПРОСМОТР ПРЕДМЕТА',9,t.accent.css);
      this.text(x+w-19,y+11,'×',22,t.dim.css).setOrigin(.5,0);
      this.close=new P.Geom.Rectangle(x+w-38,y,38,40);
      const title=this.text(x+18,y+32,i.name,25,t.text.css,w-48,true);
      const subY=title.y+title.height+3;
      this.text(x+18,subY,`${i.rarity_label} · T${i.tier} · Одноручный меч`,11,t.tiers[i.tier].css,w-36);
      const bodyY=subY+30,footerH=this.pinned?67:25,bodyH=Math.max(20,y+h-footerH-bodyY),bodyW=w-36;
      const container=this.add.container(x+18,bodyY);
      const maskG=this.make.graphics({x:0,y:0,add:false});maskG.fillRect(x+18,bodyY,bodyW,bodyH);this.detailMask=maskG;container.setMask(maskG.createGeometryMask());
      // All content remains inside this fixed viewport; wheel/arrow keys scroll.
      const addText=(px,py,value,size=12,color=t.text.css,wrap=bodyW)=>{const text=this.text(px,py,value,size,color,wrap);container.add(text);return text;};
      const artW=Math.min(80,Math.floor(bodyW*.28)),artH=Math.min(190,Math.max(110,bodyH*.62));
      if(this.textures.exists(i.item_id)){const image=this.add.image(artW/2,artH/2,i.item_id);image.setScale(Math.min((artW-8)/image.width,artH/image.height));container.add(image);}
      let dy=0;
      const sx=artW+14,sw=bodyW-sx;
      i.details.forEach(line=>{const label=addText(sx,dy,line.label,11,t.dim.css,sw);dy+=label.height+2;addText(sx,dy,line.value,14,t.text.css,sw);dy+=24;});
      dy=Math.max(dy,artH)+15;
      if(i.affixes.length){addText(0,dy,'ОСОБЫЕ СВОЙСТВА',9,t.accent.css);dy+=24;i.affixes.forEach(line=>{const text=addText(0,dy,`${line.label}  ${line.value}`,12,t.success.css);dy+=text.height+9;});dy+=8;}
      addText(0,dy,'ОПИСАНИЕ',9,t.accent.css);dy+=24;
      const description=addText(0,dy,i.description,12,t.dim.css);dy+=description.height+16;
      this.maxScroll=Math.max(0,dy-bodyH);this.scroll=Math.min(this.scroll,this.maxScroll);
      container.y-=this.scroll;
      if(this.maxScroll){const track=this.add.graphics();track.fillStyle(t.line.number,.35).fillRoundedRect(x+w-7,bodyY,2,bodyH,1);const thumb=Math.max(20,bodyH*bodyH/dy);track.fillStyle(t.accent.number,.8).fillRoundedRect(x+w-7,bodyY+(bodyH-thumb)*(this.scroll/this.maxScroll),2,thumb,1);this.text(x+18,y+h-footerH+6,'Колесо / ↑ ↓ — подробности',9,t.dim.css);}
    }
  };
}
