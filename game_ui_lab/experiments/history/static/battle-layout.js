(function (root) {
  'use strict';
  function compute(width,height){
    const hudHeight=Math.max(96,Math.min(140,height*.24)),boardHeight=height-hudHeight;
    const radius=Math.min(60,Math.max(48,Math.floor((width-80)/17.5)));
    const dy=Math.sqrt(3)*radius*.65,ox=radius+24,oy=Math.round(boardHeight/2-dy/2);
    const point=(q,r)=>({x:ox+1.5*radius*q,y:oy+dy*(r+q/2)});
    const slot=(q,r,big=false)=>({...point(q,r),q,r,radius:radius*(big?2:1),scale:1});
    const hero=slot(1,0),center=slot(6,-2,true);
    const flower=[[1,0],[0,0],[2,-1],[0,1],[1,-1],[1,1],[2,0]];
    const allies=flower.map(([q,r])=>slot(q,r));
    const acted=[[8,-5],[8,-4],[8,-3],[9,-5],[9,-4]];
    const waiting=[[10,-6],[10,-5],[10,-4],[11,-6],[11,-5]];
    const cells=[];for(let q=0;q<=11;q++)for(let r=-7;r<=2;r++){
      const p=point(q,r);if(p.y<45||p.y>boardHeight-18||p.x+radius>=width)continue;
      if(Math.hypot((p.x-center.x)/2,(p.y-center.y)/(.65*2))<radius*1.45)continue;
      cells.push(slot(q,r));
    }
    const valid=list=>list.map(([q,r])=>slot(q,r)).filter(p=>p.x+radius<width&&p.y>64&&p.y<boardHeight-20);
    const near=valid(acted),far=valid(waiting);
    // In short stages the queue uses fewer readable slots, never tiny cards.
    return{width,height,boardHeight,hudHeight,hudY:boardHeight,radius,point,hero,center,allies,cells,
      cardWidth:58,cardHeight:72,scale:1,visibleLimit:Math.min(10,1+near.length+far.length),
      enemySlots:[...near,...far],near,far};
  }
  function selectVisible(enemies, selectedId, priorities, limit=10) {
    const target=enemies.find(actor=>actor.id===selectedId);
    const shown=enemies.filter(actor=>actor.id!==selectedId).map((actor,index)=>({actor,index}))
      .sort((a,b)=>(priorities.get(b.actor.id)||0)-(priorities.get(a.actor.id)||0)||a.index-b.index)
      .slice(0,target?limit-1:limit).map(item=>item.actor);
    return {target,shown,hidden:Math.max(0,enemies.filter(a=>a.hp>0).length-shown.filter(a=>a.hp>0).length-(target?.hp>0?1:0))};
  }
  function selectBands(enemies,selectedId,priorities,nearCapacity,farCapacity,limit=10){
    const target=enemies.find(a=>a.id===selectedId),rest=enemies.filter(a=>a.id!==selectedId);
    const near=selectVisible(rest.filter(a=>a.intent==='acted'),null,priorities,nearCapacity).shown;
    const far=selectVisible(rest.filter(a=>a.intent!=='acted'),null,priorities,farCapacity).shown;
    const result=selectVisible([...(target?[target]:[]),...near,...far],selectedId,priorities,limit);
    result.hidden=Math.max(0,enemies.filter(a=>a.hp>0).length-result.shown.filter(a=>a.hp>0).length-(target?.hp>0?1:0));
    return result;
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = {compute,selectVisible,selectBands};
  if (root) root.LabBattleLayout = {compute,selectVisible,selectBands};
})(typeof window === 'undefined' ? null : window);
