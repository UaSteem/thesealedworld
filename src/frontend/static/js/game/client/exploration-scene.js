/* Authoritative exploration presentation. Cell selection never issues a command. */
const value=v=>v==null?'':String(v);
export function explorationRows(model){
 const local=model?.local_map?.rows||[], details=new Map(local.flat().filter(Boolean).map(cell=>[String(cell.loc_id),cell]));
 return model?.city_map?.rows ? model.city_map.rows.map(row=>row.map(cell=>({...details.get(String(cell.loc_id)),...cell}))) : local;
}
export function explorationCells(model){return explorationRows(model).flat().filter(Boolean);}
export function encounterInformation(encounter){return [encounter.title||'Встреча',encounter.description,encounter.bypass_chance_percent!=null?'Шанс обхода: '+encounter.bypass_chance_percent+'%':null,...(encounter.enemies||[]).flatMap(enemy=>enemyInformation(enemy))].filter(Boolean);}
export function actionsForCell(model,locId){
 const current=explorationCells(model).find(c=>c.is_current)?.loc_id ?? model?.loc_id;
 return (model?.actions || []).filter(a=>{
  const target=a.params?.target_id ?? a.params?.loc_id;
  const movement=['move','movement','travel'].includes(a.kind);
  return movement ? target!=null&&String(target)===String(locId) : String(locId)===String(current);
 });
}
export function encounterActions(model){return (model?.encounter?.options || []).flatMap(o=>{
 const action=(model.actions || []).find(a=>a.id===o.action_id);
 return action?[{...action,label:o.label || action.label}]:[];
});}
export function contextPlacement(anchor,w,h,width=350,height=400){
 width=Math.min(width,Math.max(1,w-16));height=Math.min(height,Math.max(1,h-16));
 const right=anchor.x+anchor.width+10;
 return {x:Math.max(8,Math.min(right+width<=w-8?right:anchor.x-width-10,w-width-8)),y:Math.max(8,Math.min(anchor.y,h-height-8)),width,height};
}
export function sameOriginAsset(path,origin){if(typeof path!=='string'||!path.trim())return null;try{const u=new URL(path,origin);return u.origin===new URL(origin).origin&&['http:','https:'].includes(u.protocol)?u.href:null;}catch{return null;}}
const scalar=v=>typeof v==='string'||typeof v==='number'||typeof v==='boolean';
export function inspectionLines(model,cell){
 const lines=[cell.title||model.title,cell.description||(cell.is_current?model.description:'')||''];
 const threat=cell.threat??cell.threat_tier;if(threat!=null)lines.push('Опасность: '+value(threat));
 if(cell.corpse_count!=null)lines.push('Останки: '+value(cell.corpse_count));
 for(const marker of cell.service_markers||[])lines.push(marker.label||marker.title||marker.name||'');
 for(const label of cell.service_labels||[])if(!lines.includes(label))lines.push(label);
 const edgeSource=cell.render_edges||cell.edges||[];for(const [direction,edge]of Object.entries(edgeSource)){const state={open:'открыт',blocked:'закрыт',locked:'заперт',unknown:'неизвестно'}[edge.state]||edge.state;lines.push([edge.label||edge.direction||direction,state,edge.tooltip].filter(Boolean).join(' · '));}
 if(String(cell.loc_id)===String(model.loc_id))for(const object of model.objects||[])lines.push(scalar(object)?String(object):object.title||object.name||object.description||'');
 return lines.filter(Boolean);
}
export function enemyInformation(enemy){
 const lines=[[enemy.name,enemy.level!=null?'Уровень '+enemy.level:'',enemy.role,enemy.hp_percent!=null?'HP '+enemy.hp_percent+'%':'',enemy.threat_rating!=null?'Опасность '+enemy.threat_rating:''].filter(Boolean).join(' · '),enemy.description];
 if(enemy.intel?.danger_band!=null)lines.push('Опасность: '+value(enemy.intel.danger_band));
 for(const [key,label]of Object.entries({hp:'Здоровье',energy:'Энергия',concentration:'Концентрация'})){
  const vital=enemy.intel?.vitals?.[key];
  if(scalar(vital))lines.push(label+': '+String(vital));
  else if(vital)lines.push([label,vital.label,vital.percent!=null?value(vital.percent)+'%':null,scalar(vital.points)?String(vital.points):null].filter(v=>v!=null&&v!=='').join(' · '));
 }
 return lines.filter(Boolean);
}
function palette(host){const probe=host.ownerDocument.createElement('span');host.append(probe);const out={};
 for(const [name,token] of Object.entries({bg:'--col-bg-base',panel:'--col-bg-surface',cell:'--col-bg-darker',line:'--col-border',accent:'--col-accent',text:'--col-text-primary',dim:'--col-text-dim'})){
 probe.style.color=`var(${token})`;const css=getComputedStyle(probe).color,ch=css.match(/[\d.]+/g)?.slice(0,3).map(Number)||[20,24,30];out[name]={css,number:(ch[0]<<16)+(ch[1]<<8)+ch[2]};}probe.remove();return out;}
let instance=0;
export function createExplorationScene(P){return class ExplorationScene extends P.Scene{
 constructor(){super({key:'GameClientExploration'});this.controls=[];this.assets=new Map();this.serial=++instance;this.assetSequence=0;this.selected=null;this.open=false;}
 create(options={}){
  this.services=options.services||this.services;this.model=options.model||this.model||{};this.callbacks={...this.callbacks};
  for(const k of ['onAction','busy','error','onRefresh'])if(options[k]!==undefined)this.callbacks[k]=options[k];
  this.host=document.getElementById('game-client-canvas-host');this.dead=false;
  this.loadComplete=(key)=>{const entry=[...this.assets.values()].find(a=>a.key===key);if(entry){entry.state='ready';if(!this.dead&&this.sys.isActive())this.draw();}else if(key.startsWith(`exploration-${this.serial}-`)&&this.textures.exists(key))this.textures.remove(key);};
  this.loadError=file=>{const entry=[...this.assets.values()].find(a=>a.key===file.key);if(entry)entry.state='failed';};
  this.load.on('filecomplete',this.loadComplete);this.load.on('loaderror',this.loadError);
  this.resize=()=>{if(this.sys.isActive())this.draw();};this.scale.on('resize',this.resize);this.events.on('wake',this.resize);
  this.events.once('shutdown',()=>{this.dead=true;this.load.off('filecomplete',this.loadComplete);this.load.off('loaderror',this.loadError);this.load.reset();this.scale.off('resize',this.resize);this.events.off('wake',this.resize);this.clear();for(const entry of this.assets.values())if(this.textures.exists(entry.key))this.textures.remove(entry.key);this.assets.clear();});this.draw();
 }
 present(model,callbacks={}){if(this.model?.loc_id!==model?.loc_id){this.selected=null;this.open=false;this.scroll=0;}this.model=model||{};this.callbacks={...this.callbacks,...callbacks};if(this.host&&this.services&&this.sys.isActive())this.draw();}
 clear(){for(const c of this.controls)c.destroy();this.controls=[];this.context?.remove();this.context=null;this.children.removeAll(true);}
 text(x,y,label,size=16,color=this.colors.text.css,width){return this.services.components.createText(this,x,y,value(label),{fontSize:size,color,renderScale:this.ratio,themeHost:this.host,...(width?{wordWrap:{width,useAdvancedWrap:true}}:{})});}
 button(key,rect,label,callback,disabled=false){const c=this.services.components.attachSemanticButton(this.host,{scene:this,label,rect,onActivate:callback,disabled});c.element.dataset.explorationControl=key;this.controls.push(c);return c;}
 asset(path){if(!path)return null;const url=sameOriginAsset(path,location.origin);if(!url)return null;this.needed.add(url);let entry=this.assets.get(url);
  if(!entry){entry={key:`exploration-${this.serial}-${++this.assetSequence}`,state:'loading'};this.assets.set(url,entry);
   this.load.image(entry.key,url);if(!this.load.isLoading())this.load.start();
  }return entry.state==='ready'?entry.key:null;
 }
 draw(){
  const focused=this.host.contains(document.activeElement)?document.activeElement.dataset.explorationControl:null;
  this.scroll=this.context?.scrollTop||this.scroll||0;this.clear();this.colors=palette(this.host);this.needed=new Set();
  const {width:w,height:h}=this.host.getBoundingClientRect();if(w<2||h<2)return;this.ratio=Math.max(1,this.scale.width/w);this.cameras.main.setViewport(0,0,this.scale.width,this.scale.height).setZoom(this.ratio).centerOn(w/2,h/2);
  this.add.rectangle(0,0,w,h,this.colors.bg.number).setOrigin(0);const bg=this.asset(this.model.background_url);if(bg){const source=this.textures.get(bg).getSourceImage(),scale=Math.max(w/source.width,h/source.height);this.add.image(w/2,h/2,bg).setScale(scale).setAlpha(.45);}
  this.text(16,12,this.model.title||'Исследование',20,this.colors.text.css,w-150);const refresh={x:w-110,y:8,width:100,height:32};this.text(refresh.x+8,refresh.y+7,'Обновить',14);this.button('refresh',refresh,'Обновить',()=>this.callbacks.onRefresh?.(),this.callbacks.busy);
  const summary=this.callbacks.error||this.model.description||'';this.text(16,42,summary.length>140?summary.slice(0,137)+'…':summary,15,this.colors.dim.css,w-36);
  const hud=this.model.hud||{},facts=[hud.message,hud.is_safe_zone?'Безопасная зона':null,hud.threat_tier!=null?'Опасность: '+hud.threat_tier:null,hud.players_count!=null?'Игроки: '+hud.players_count:null,hud.battles_count!=null?'Бои: '+hud.battles_count:null].filter(Boolean);this.text(16,78,facts.join(' · '),14,this.colors.accent.css,w-32);
  const providedRows=explorationRows(this.model);
  const rows=providedRows?.length?providedRows:(this.model.loc_id?[[{loc_id:this.model.loc_id,title:this.model.title,description:this.model.description,is_current:true}]]:[]),cols=Math.max(1,...rows.map(r=>r.length)),count=Math.max(1,rows.length);
  const top=Math.min(116,h*.22),side=Math.max(1,Math.min((w-32)/cols,(h-top-16)/count)),mx=(w-side*cols)/2,my=top+(h-top-16-side*count)/2;
  let anchor={x:w/2,y:h/2,width:1,height:1},selectedCell=null;
  rows.forEach((row,y)=>row.forEach((cell,x)=>{
   const rect={x:mx+x*side,y:my+y*side,width:side,height:side},tile=this.asset(cell.tile_url),selected=String(cell.loc_id)===String(this.selected);
   this.add.rectangle(rect.x,rect.y,side,side,this.colors.cell.number,.9).setOrigin(0).setStrokeStyle(selected?2:1,selected?this.colors.accent.number:this.colors.line.number);
   if(tile)this.add.image(rect.x+side/2,rect.y+side/2,tile).setDisplaySize(side-2,side-2);
   if(!tile)this.text(rect.x+6,rect.y+6,cell.is_known===false?'?':cell.title||cell.terrain||'',Math.max(11,Math.min(15,side/6)),this.colors.dim.css,side-12);
   if(cell.is_current){this.add.circle(rect.x+side/2,rect.y+side/2,Math.max(5,side*.09),this.colors.accent.number).setStrokeStyle(2,this.colors.text.number);if(!this.selected){anchor=rect;selectedCell=cell;}}
   const markers=(cell.service_markers||[]).map(m=>m.label||m.title||m.name||m.service).filter(Boolean);if(markers.length)this.text(rect.x+5,rect.y+side-22,markers.join(' · '),12,this.colors.accent.css,side-10);
   if(selected){anchor=rect;selectedCell=cell;}
   this.button('cell-'+cell.loc_id,rect,`${cell.is_current?'Вы здесь. ':''}${cell.title||'Клетка '+value(cell.loc_id)}${markers.length?'. '+markers.join(', '):''}`,()=>{this.selected=cell.loc_id;this.open=true;this.scroll=0;this.draw();});
  }));
  if(this.model.encounter){this.encounterPanel(w,h);}else if(this.open&&selectedCell)this.contextPanel(anchor,w,h,selectedCell);
  else this.text(16,h-26,'Выберите клетку для осмотра. Действия открываются на вашей позиции.',13,this.colors.dim.css,w-32);
  for(const [url,entry]of this.assets)if(!this.needed.has(url)){if(this.textures.exists(entry.key))this.textures.remove(entry.key);this.assets.delete(url);}
  if(focused)this.host.querySelector(`[data-exploration-control="${CSS.escape(focused)}"]`)?.focus({preventScroll:true});
 }
 contextPanel(anchor,w,h,cell){const r=contextPlacement(anchor,w,h,Math.min(390,w*.48),Math.min(440,h-90));this.domPanel(r,inspectionLines(this.model,cell),actionsForCell(this.model,cell.loc_id));}
 encounterPanel(w,h){const e=this.model.encounter;const lines=encounterInformation(e);this.domPanel({x:Math.max(16,(w-Math.min(620,w-32))/2),y:90,width:Math.min(620,w-32),height:Math.max(80,h-110)},lines,encounterActions(this.model));}
 domPanel(rect,lines,actions){
  const el=this.host.ownerDocument.createElement('section');this.context=el;el.tabIndex=0;el.setAttribute('aria-busy',String(Boolean(this.callbacks.busy)));el.dataset.explorationControl='context';el.setAttribute('aria-label',this.model.encounter?'Встреча':'Сведения о клетке');
  Object.assign(el.style,{position:'absolute',left:rect.x+'px',top:rect.y+'px',width:rect.width+'px',maxHeight:rect.height+'px',boxSizing:'border-box',overflowY:'auto',padding:'16px',background:'var(--col-bg-surface)',color:'var(--col-text-primary)',border:'1px solid var(--col-accent)',font:'16px var(--font-ui)',lineHeight:'1.45',scrollbarWidth:'thin'});
  for(const enemy of this.model.encounter?.enemies||[]){const url=sameOriginAsset(enemy.image||enemy.visual?.image_url,location.origin);if(url){const image=el.ownerDocument.createElement('img');image.src=url;image.alt=enemy.name||'';image.loading='lazy';Object.assign(image.style,{width:'80px',height:'80px',objectFit:'contain',marginRight:'8px'});el.append(image);}}
  for(const [i,line]of lines.entries()){const p=el.ownerDocument.createElement(i?'p':'h3');p.textContent=line;p.style.margin='0 0 12px';el.append(p);}
  if(!this.model.encounter){const close=el.ownerDocument.createElement('button');close.type='button';close.textContent='Закрыть';close.addEventListener('click',()=>{this.open=false;this.draw();});el.append(close);}
  for(const action of actions){const b=el.ownerDocument.createElement('button');b.type='button';b.textContent=action.label;b.disabled=action.enabled===false||Boolean(this.callbacks.busy)||Boolean(this.callbacks.error);b.title=action.tooltip||'';b.dataset.explorationControl='action-'+action.id;Object.assign(b.style,{display:'block',width:'100%',padding:'10px',marginTop:'8px',color:'var(--col-text-primary)',background:'var(--col-bg-darker)',border:'1px solid var(--col-border)',font:'inherit',textAlign:'left'});b.addEventListener('click',()=>this.callbacks.onAction?.(action.id));el.append(b);}
  if(!actions.length){const p=el.ownerDocument.createElement('p');p.textContent='Нет доступных действий';el.append(p);}
  el.addEventListener('keydown',event=>{if(event.key==='Escape'&&!this.model.encounter){event.preventDefault();this.open=false;this.draw();this.host.querySelector(`[data-exploration-control="cell-${CSS.escape(value(this.selected))}"]`)?.focus();}});
  this.host.append(el);el.scrollTop=this.scroll||0;const sleep=()=>{el.hidden=true;},wake=()=>{el.hidden=false;};this.events.on('sleep',sleep);this.events.on('wake',wake);const remove=el.remove.bind(el);el.remove=()=>{this.events.off('sleep',sleep);this.events.off('wake',wake);remove();};
 }
};}
