import Phaser from 'phaser';
import controls from './combat-controls.js';
import inspector from './target-inspector.js';
import geometry from './hex-layout.js';
import {assets} from '../assets.js';
export function createCombatScene(host, exchange){
  'use strict';
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  // Channel geometry in the source sheet's 1600px preview coordinates.
  const resourceProfiles={
    player:{crop:[94,148],mirror:800,top:[[300,179],[319,162],[480,162],[499,179],[480,194],[319,194]],left:[[153,351],[239,211],[259,205],[267,224],[180,369],[157,375]]},
    monster:{crop:[1110,124],mirror:2400,top:[[1109,179],[1128,162],[1273,162],[1292,179],[1273,194],[1128,194]],left:[[949,350],[1035,210],[1055,205],[1063,224],[978,368],[957,374]]},
    boss:{crop:[39,1121],mirror:800,top:[[302,982],[321,967],[479,967],[498,982],[480,997],[320,997]],left:[[167,1148],[238,1017],[260,1010],[266,1029],[192,1165],[174,1161]]},
  };
  function clipResource(points,axis,threshold,greater){
    const result=[];
    for(let i=0;i<points.length;i++){
      const a=points[i],b=points[(i+1)%points.length];
      const inside=p=>greater?p[axis]>=threshold:p[axis]<=threshold;
      if(inside(a))result.push(a);
      if(inside(a)!==inside(b)){
        const t=(threshold-a[axis])/(b[axis]-a[axis]);
        result.push({x:a.x+(b.x-a.x)*t,y:a.y+(b.y-a.y)*t});
      }
    }
    return result;
  }
  class HexCombatWorkspace extends Phaser.Scene {
    constructor() { super('HexCombatWorkspace'); }
    preload() {
      controls.preload(this);
      inspector.preload(this);

      assets.preload(this,'combat-core');

    }
    create() {
      inspector.frames(this);
      const newSheet = this.textures.get('hex-three-frames');
      newSheet.add('player', 0, 94, 148, 836, 729);
      newSheet.add('monster', 0, 1110, 124, 852, 772);
      newSheet.add('boss', 0, 39, 1121, 946, 822);
      newSheet.add('tile', 0, 1133, 1180, 806, 705);
      const brokenSheet=this.textures.get('broken-hexes');
      for(const [name,x,y] of [['two-thirds',0,0],['half',1024,0],['third',0,1024],['whole',1024,1024]])
        brokenSheet.add(name,0,x,y,1024,1024);
      this.artwork = [];
      this.selectedId = 'boss';
      this.demoActive={id:'boss',variant:'boss'};
      this.demoQueue=[8,9,10,31,21].map(number=>({id:`enemy-${number}`,variant:'monster',number}));
      this.demoResources=new Map();
      this.exchangeTweens=[];
      this.exchangeBusy=false;
      this.exchangeEpoch=0;
      this.inspectionId='boss';
      this.overflowCounts = {enemy: 0, ally: 0};
      this.domEvents=new AbortController();

      this.showGrid = true;
      document.getElementById('show-hex-grid').checked = true;
      this.cells = [];
      this.lines = this.add.graphics().setDepth(10);
      this.numberLabels = [];
      this.showNumbers = false;
      document.getElementById('show-hex-numbers').addEventListener('change', event => {
        this.showNumbers = event.target.checked;
        this.numberLabels.forEach(label => label.setVisible(this.showNumbers));
      },{signal:this.domEvents.signal});
      this.spaceBackdrop=host.closest('.stage-shell');
      this.spaceMotion=window.matchMedia('(prefers-reduced-motion: reduce)');
      this.spaceOffset={x:0,y:0};
      this.spacePhase=.6;
      this.spaceLayer=document.createElement('div');
      this.spaceLayer.setAttribute('aria-hidden','true');
      Object.assign(this.spaceLayer.style,{
        position:'absolute',left:'50%',top:'50%',pointerEvents:'none',
        backgroundImage:getComputedStyle(this.spaceBackdrop).backgroundImage,
        backgroundSize:'100% 100%',backgroundRepeat:'no-repeat',willChange:'transform',
      });
      this.spaceBackdrop.prepend(this.spaceLayer);
      this.spaceBackdrop.style.backgroundImage='none';
      host.style.zIndex='1';
      document.getElementById('show-hex-grid').addEventListener('change', event => {
        this.showGrid = event.target.checked;
        this.drawMap();
      },{signal:this.domEvents.signal});
      this.scale.on('resize', this.drawMap, this);
      this.events.once('shutdown', () => {
        this.domEvents.abort();
        this.scale.off('resize',this.drawMap,this);
        this.exchangeEpoch++;
        this.exchangeTweens.forEach(tween=>tween.stop());
        this.spaceBackdrop.style.removeProperty('background-position');
        this.spaceBackdrop.style.removeProperty('background-size');
        this.spaceBackdrop.style.removeProperty('background-image');
        this.spaceLayer.remove();host.style.removeProperty('z-index');
        this.controlZone?.destroy();
        this.targetInspector?.destroy();
        this.controlZone = null;
        this.targetInspector = null;
        this.runeAngle=this.runeGlow?.rotation??this.runeAngle??0;
        this.runeGlow=null;
      });
      this.drawMap();
    }
    update(time,delta) {
      if (!this.spaceBackdrop) return;
      if (this.spaceMotion.matches) {
        this.spaceLayer.style.transform='translate3d(0px,0px,0px)';
        return;
      }
      const width=host.clientWidth,height=host.clientHeight;
      const pointer=this.input.activePointer;
      const inside=pointer.x>=0&&pointer.x<=width&&pointer.y>=0&&pointer.y<=height;
      const px=inside?(pointer.x/width-.5)*10:0;
      const py=inside?(pointer.y/height-.5)*8:0;
      const smoothing=1-Math.exp(-Math.min(delta,100)/650);
      this.spaceOffset.x+=(px-this.spaceOffset.x)*smoothing;
      this.spaceOffset.y+=(py-this.spaceOffset.y)*smoothing;
      // Arc-length stepping: turn continuously without stopping at the bounds.
      const phase=this.spacePhase;
      const tangent=Math.hypot(this.spaceTravel.x*Math.sin(phase),this.spaceTravel.y*Math.cos(phase));
      this.spacePhase=(phase+5*Math.min(delta,50)/1000/Math.max(1,tangent))%(Math.PI*2);
      const x=Math.cos(this.spacePhase)*this.spaceTravel.x+this.spaceOffset.x;
      const y=Math.sin(this.spacePhase)*this.spaceTravel.y+this.spaceOffset.y;
      this.spaceLayer.style.transform=`translate3d(${x.toFixed(3)}px,${y.toFixed(3)}px,0px)`;
    }
    drawMap() {
      this.exchangeEpoch++;
      this.exchangeTweens.forEach(tween=>tween.stop());
      this.exchangeTweens=[];this.exchangeBusy=false;
      const width = host.clientWidth, height = host.clientHeight;
      // Cover with a small overscan so drifting never exposes an empty edge.
      const backgroundScale=Math.max((width+120)/5376,(height+120)/3072)*1.12;
      this.spaceBaseSize={width:5376*backgroundScale,height:3072*backgroundScale};
      this.spaceTravel={x:Math.min(180,(this.spaceBaseSize.width-width)/2-12),y:Math.min(120,(this.spaceBaseSize.height-height)/2-12)};
      Object.assign(this.spaceLayer.style,{
        width:`${this.spaceBaseSize.width}px`,height:`${this.spaceBaseSize.height}px`,
        marginLeft:`${-this.spaceBaseSize.width/2}px`,marginTop:`${-this.spaceBaseSize.height/2}px`,
      });
      this.cameras.main.setViewport(0, 0, width * dpr, height * dpr).setZoom(dpr).centerOn(width / 2, height / 2);
      this.lines.clear();
      this.lines.y=0;
      this.platformOffset=0;
      this.numberLabels.forEach(label => label.destroy());
      this.numberLabels = [];
      this.runeAngle=this.runeGlow?.rotation??this.runeAngle??0;
      this.runePulse?.stop();
      this.artwork.forEach(object => object.destroy());
      this.artwork = [];
      // Chat resizing changes the vertical origin, never the scene scale.
      const radius = Math.max(1, (width - 32) / 17);
      const rowStep = Math.sqrt(3) * radius;
      this.cells = [];
      for (let q = -6; q <= 4; q++) {
        const column = q + 6;
        const maxR = column % 2 === 0 ? 3 : 2;
        for (let r = -2; r <= maxR; r++) {
          const x = width / 2 + 1.5 * radius * (q + 1);
          const y = height / 2 + Math.sqrt(3) * radius * (r + (column % 2) / 2 - .5);
          const vertices = geometry.vertices(x, y, radius);
          const central = q === -1 && r === 0;
          const meeting = (q === -1 && Math.abs(r) <= 1)
            || ((q === -2 || q === 0) && (r === 0 || r === 1));
          const zone = q < -4 ? 'inspection' : q <= 2 ? 'field' : 'actions';
          this.cells.push({ q, r, x, y, radius, central, meeting, vertices, zone, terrain: zone === 'field' });
          if (this.showGrid) {
            this.lines.lineStyle(central ? 2 : 1, central ? 0xf3cc83 : 0x8c9b9d, central ? 1 : .55);
            this.lines.strokePoints(vertices, true);
          }
        }
      }
      // Row-major numbering stays independent of tile visibility and canvas resizing.
      const numbered = [...this.cells].sort((a, b) => a.r - b.r || a.q - b.q);
      numbered.forEach((cell, index) => {
        cell.number = index + 1;
        const label = this.add.text(cell.x, cell.y, String(cell.number), {
          fontFamily: 'Arial', fontSize: '18px', fontStyle: 'bold', color: '#ffffff',
          backgroundColor: '#101820', padding: {x: 5, y: 3},
        }).setOrigin(.5).setDepth(100).setResolution(dpr).setVisible(this.showNumbers);
        this.numberLabels.push(label);
      });
      const center = this.cells.find(cell => cell.central);
      // Continuous tiled surface; cut only the opposite corner wedges.
      const hiddenTileNumbers = new Set([4, 5, 7, 14, 43, 52, 53, 58, 59, 22, 33, 32, 42, 25, 24, 34, 45]);
      const tiles = this.cells.filter(cell => {
        const upperLeftCorner = cell.q + cell.r < -5;
        const lowerRightCorner = cell.q + cell.r > 4;
        return [11,56].includes(cell.number) || (!upperLeftCorner && !lowerRightCorner && !hiddenTileNumbers.has(cell.number));
      });
      // Shared edges cancel: illuminate only the silhouette of the platform.
      const edges=new Map();
      const vertexKey=point=>`${point.x.toFixed(2)},${point.y.toFixed(2)}`;
      for(const cell of tiles)for(let i=0;i<6;i++){
        const a=cell.vertices[i],b=cell.vertices[(i+1)%6];
        const key=[vertexKey(a),vertexKey(b)].sort().join('|');
        if(edges.has(key))edges.delete(key);else edges.set(key,[a,b]);
      }
      const rim=this.add.graphics().setDepth(-1);
      for(const [strokeWidth,alpha] of [[22,.025],[14,.045],[8,.075],[3,.2]]){
        rim.lineStyle(strokeWidth,0x66c9d2,alpha);
        for(const [a,b] of edges.values())rim.lineBetween(a.x,a.y,b.x,b.y);
      }
      this.artwork.push(rim);
      for (const cell of tiles) {
        const tile = this.add.image(cell.x, cell.y, 'broken-hexes', 'whole')
          .setScale(radius/450).setDepth(0);
        this.artwork.push(tile);
      }
      this.fragments=[];
      // Decorative neighbours do not participate in grid numbering or sizing.
      const perimeterCandidates=[];
      for(let q=-7;q<=5;q++)for(let r=-3;r<=4;r++){
        if(tiles.some(cell=>cell.q===q&&cell.r===r))continue;
        const existing=this.cells.find(cell=>cell.q===q&&cell.r===r);
        const parity=((q+6)%2+2)%2;
        perimeterCandidates.push(existing||{q,r,x:width/2+1.5*radius*(q+1),y:height/2+Math.sqrt(3)*radius*(r+parity/2-.5)});
      }
      for(const cell of perimeterCandidates){
        const touching=tiles.filter(other=>Math.abs(Math.hypot(other.x-cell.x,other.y-cell.y)-Math.sqrt(3)*radius)<.01);
        const edges=touching.map(other=>(Math.round((Math.atan2(other.y-cell.y,other.x-cell.x)*180/Math.PI-30)/60)+6)%6);
        if(!edges.length||edges.length>3)continue;
        const base=edges.length===3?[5,0,1]:edges.length===2?[0,1]:[0];
        const turns=[0,1,2,3,4,5].find(turn=>base.every(edge=>edges.includes((edge+turn)%6)));
        if(turns===undefined)continue;
        const variant=edges.length===3?'two-thirds':edges.length===2?'half':'third';
        const fragment=this.add.image(cell.x,cell.y,'broken-hexes',variant)
          .setScale(radius/450).setAngle(turns*60).setDepth(0);
        this.artwork.push(fragment);
        this.fragments.push({number:cell.number??null,q:cell.q,r:cell.r,variant,angle:turns*60,edges});
      }
      for (const [number, side, label] of [[11,'enemy','Противников'],[56,'ally','Союзников']]) {
        const count=this.overflowCounts[side],cell=tiles.find(cell=>cell.number===number);
        if (!count || !cell) continue;
        const size=radius*1.05;
        const plaque=this.add.graphics().setDepth(6);
        plaque.fillStyle(0x111a20,.96).lineStyle(1.5,0xb89a61)
          .fillRoundedRect(cell.x-size/2,cell.y-size/2,size,size,4)
          .strokeRoundedRect(cell.x-size/2,cell.y-size/2,size,size,4);
        const caption=this.add.text(cell.x,cell.y,`${label}\nещё +${count}`,{
          fontFamily:'Arial',fontSize:`${Math.max(10,radius*.15)}px`,color:'#ead8b8',align:'center',
        }).setOrigin(.5).setDepth(7).setResolution(dpr);
        this.artwork.push(plaque,caption);
      }
      const showCircle = true;
      const circleRadius = radius * 4.5;
      if (showCircle) {
        const textureScale = circleRadius * 2 / 1024;
        const underglow = this.add.graphics().setDepth(1);
        const segments = 180;
        const inner = 350 * textureScale, outer = 385 * textureScale;
        // One procedural rainbow annulus; rotate it under the stationary rune cutouts.
        underglow.setPosition(center.x, center.y).setRotation(this.runeAngle||0);
        this.runeGlow=underglow;
        for (let index = 0; index < segments; index++) {
          const start = index / segments * Math.PI * 2;
          const end = (index + 1.15) / segments * Math.PI * 2;
          const color = Phaser.Display.Color.HSVToRGB(index / segments, .82, 1).color;
          underglow.fillStyle(color, 1).fillPoints([
            {x: Math.cos(start) * inner, y: Math.sin(start) * inner},
            {x: Math.cos(start) * outer, y: Math.sin(start) * outer},
            {x: Math.cos(end) * outer, y: Math.sin(end) * outer},
            {x: Math.cos(end) * inner, y: Math.sin(end) * inner},
          ], true);
        }
        this.runePulse = this.tweens.add({
          targets: underglow, rotation: (this.runeAngle||0)+Math.PI * 2, duration: 10000,
          ease: 'Linear', repeat: -1,
        });
        const circle = this.add.image(center.x, center.y, 'duel-circle-rune-cutout')
          .setDisplaySize(circleRadius * 2, circleRadius * 2).setDepth(2);
        this.artwork.push(underglow, circle);
      }
      this.cards = [];
      this.cardViews=new Map();
      const bossCell = this.cells.find(cell => cell.number === 29);
      const playerCell = this.cells.find(cell => cell.number === 38);
      if (bossCell && playerCell) {
        const versus=this.add.text((bossCell.x+playerCell.x)/2,(bossCell.y+playerCell.y)/2,'VS',{
          fontFamily:'Georgia, Times New Roman, serif',fontSize:`${radius*.56}px`,
          fontStyle:'bold italic',color:'#f3d58c',stroke:'#66451c',strokeThickness:2,
          shadow:{offsetX:0,offsetY:3,color:'#000000',blur:5,fill:true,stroke:true},
        }).setOrigin(.5).setDepth(8).setResolution(dpr);
        this.artwork.push(versus);
      }
      const placements=[
        [this.demoActive.variant,bossCell,'enemy',true,this.demoActive.id],['player',playerCell,'ally',true,'player'],
        // 20 and 47 stay vacant as the arena entry / return lanes.
        ...this.demoQueue.map(actor=>[actor.variant,this.cells.find(cell=>cell.number===actor.number),'enemy',false,actor.id]),
        ...[48,57,46,36,35].map(number=>['player',this.cells.find(cell=>cell.number===number),'ally',false]),
      ];
      for (const [variant,cell,side,active,actorId] of placements) {
        if (!cell) continue;
        const source = this.textures.getFrame('hex-three-frames',variant);
        const imageScale = variant === 'boss' ? 1.18 : 1;
        const frameRatio = active ? 1.2 : .94;
        const frameWidth = 2*radius*frameRatio*imageScale;
        const frameHeight = frameWidth*source.height/source.width;
        const profile=resourceProfiles[variant],resourceScale=frameWidth/source.width;
        const id=actorId||(active?variant:`${side}-${cell.number}`);
        if(!this.demoResources.has(id))this.demoResources.set(id,{hp:active?(side==='ally'?.82:.64):.4+(cell.number%6)*.1,energy:.35+(cell.number%4)*.16,stamina:.3+(cell.number%5)*.14});
        const resources=this.demoResources.get(id);
        const bars=this.add.graphics().setDepth(4);
        const right=profile.left.map(([x,y])=>[profile.mirror-x,y]);
        for(const [name,path,color,axis] of [['hp',profile.top,0xff252d,'x'],['energy',profile.left,0x299fea,'y'],['stamina',right,0x62ca66,'y']]){
          const points=path.map(([x,y])=>({x:cell.x-frameWidth/2+(x*1.28-profile.crop[0])*resourceScale,y:cell.y-frameHeight/2+(y*1.28-profile.crop[1])*resourceScale}));
          const min=Math.min(...points.map(p=>p[axis])),max=Math.max(...points.map(p=>p[axis]));
          const threshold=axis==='x'?min+(max-min)*resources[name]:max-(max-min)*resources[name];
          bars.fillStyle(0x424850).fillPoints(points,true);
          bars.fillStyle(color).fillPoints(clipResource(points,axis,threshold,axis==='y'),true);
        }
        const frame = this.add.image(cell.x,cell.y,'hex-three-frames',variant)
          .setDisplaySize(frameWidth,frameHeight).setDepth(5);
        const view=this.add.container(cell.x,cell.y).setDepth(5);
        bars.setPosition(-cell.x,-cell.y);frame.setPosition(0,0);view.add([bars,frame]);
        const intent=['attack','wait','defend'][Number(id.replace(/\D/g,''))%3||0];
        if(side==='enemy'){
          const medalSize=Math.min(32,frameWidth*.23);
          const medal=this.add.image(0,frameHeight*(variant==='boss'?.27:variant==='player'?.4:.38),inspector.key,intent)
            .setDisplaySize(medalSize,medalSize);
          view.add(medal);
        }
        frame.setInteractive({useHandCursor:true}).on('pointerdown',()=>{
          this.inspectionId=id;this.targetInspector.show(this.demoActor(id));
        });
        this.cardViews.set(id,view);this.artwork.push(view);
        this.cards.push({id,variant,side,active,intent,resources,q:cell.q,r:cell.r,number:cell.number,x:cell.x,y:cell.y,width:frameWidth,height:frameHeight,tileWidth:2*radius,ratio:frameRatio*imageScale});
      }
      if (!this.controlZone) this.controlZone = controls.create(this, {width, height,onAttack:()=>this.demoExchange()});
      else this.controlZone.resize(width, height);
      if(!this.targetInspector)this.targetInspector=inspector.create(this,{top:130});
      this.targetInspector.resize(width,height);
      this.targetInspector.show(this.demoActor(this.inspectionId));
      this.wheelInfo = null;
      this.sceneArt = {rowStep, removedRow: 0, fragments:this.fragments, overflowCounts:{...this.overflowCounts}, tiles: tiles.map(({number,q, r, x, y}) => ({number,q, r, x, y})), meeting: {
        x: center.x, y: center.y, radius: circleRadius, texture: 'duel-circle-rune-cutout', underglow: 'rainbow', animated: true, direction: 'clockwise', cycleMs: 10000,
      }};
    }

    demoActor(id){
      const card=this.cards.find(card=>card.id===id)||this.cards.find(card=>card.id===this.demoActive.id);
      const boss=card.variant==='boss',index=Number(card.id.replace(/\D/g,''))||0;
      return {id:card.id,name:card.side==='ally'?(card.active?'Ada Guard':'Союзник'):boss?'Главарь':['Налётчик','Костолом','Дозорный'][index%3],
        role:card.side==='ally'?'Воин':boss?'Главарь разбойников':'Воин',power:boss?48:32+index%9,
        side:card.side,resources:card.resources,damage:boss?'24 — 38':'18 — 26',accuracy:boss?'86%':'78%',
        armor:boss?'24':'14',evasion:'12%',parry:boss?'18%':'9%',
        intent:card.intent,intentLabel:{attack:'Готовит удар',wait:'Ожидает',defend:'Защищается'}[card.intent]};
    }

    demoExchange() {
      if(this.exchangeBusy||!this.demoQueue.length)return false;
      const outgoing=this.demoActive,incoming=this.demoQueue.shift();
      const oldView=this.cardViews.get(outgoing.id),newView=this.cardViews.get(incoming.id);
      const home=this.cells.find(cell=>cell.number===incoming.number);
      const portal=this.cells.find(cell=>cell.number===20),arena=this.cells.find(cell=>cell.number===29);
      this.demoResources.get(outgoing.id).hp=exchange().hp;
      this.demoQueue.push({...outgoing,number:incoming.number});
      this.demoActive={id:incoming.id,variant:incoming.variant};
      this.selectedId=incoming.id;
      if(this.inspectionId===outgoing.id)this.inspectionId=incoming.id;
      if(this.spaceMotion.matches){this.drawMap();return true;}
      this.exchangeBusy=true;
      const epoch=this.exchangeEpoch;
      const animate=(view,config,next)=>{
        if(epoch!==this.exchangeEpoch)return;
        this.exchangeTweens.push(this.tweens.add({targets:view,...config,ease:'Sine.easeInOut',onComplete:()=>{if(epoch===this.exchangeEpoch)next?.();}}));
      };
      oldView.setDepth(9);newView.setDepth(10);
      animate(oldView,{x:portal.x,y:portal.y,scale:.94/1.2,duration:420},()=>{
        animate(oldView,{x:home.x,y:home.y,duration:360});
        animate(newView,{x:portal.x,y:portal.y,duration:420},()=>{
          animate(newView,{x:arena.x,y:arena.y,scale:1.2/.94,duration:440},()=>this.drawMap());
        });
      });
      return true;
    }

    setOverflowCounts(enemy=0,ally=0) {
      const count=value=>Number.isFinite(value)?Math.max(0,Math.floor(value)):0;
      this.overflowCounts={enemy:count(enemy),ally:count(ally)};
      this.drawMap();
    }

    inspect() { return { mode: 'transparent-hex-grid', columns: 11, rows: 5, showGrid: this.showGrid, cells: this.cells, artwork: this.sceneArt, cards: this.cards, controls: this.controlZone?.inspect() || null,inspector:this.targetInspector?.inspect()||null, selectedId: this.selectedId,exchangeBusy:this.exchangeBusy,activeEnemy:this.demoActive.id,queue:this.demoQueue.map(actor=>({...actor})), teamSize: 5, websocket: false }; }
  }
  return HexCombatWorkspace;
}
