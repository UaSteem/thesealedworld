/* Shared pure geometry/material helpers: no Phaser state, no tree placement. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.RiftTerrain=api;})(globalThis,()=>{
  'use strict';
  const radius=128,perspectiveY=.65,height=Math.sqrt(3)*radius;
  const vertex=i=>({x:radius*Math.cos(i*Math.PI/3),y:radius*Math.sin(i*Math.PI/3)});
  const point=(q,r)=>({x:radius*1.5*q,y:height*(r+q/2)*perspectiveY});
  const unproject=(x,y)=>({x,y:y/perspectiveY});
  function edgePoints(edge,voidMask){
    const a=vertex(edge),b=vertex((edge+1)%6);
    if(!(voidMask&(1<<edge)))return[a,b];
    const result=[a],mid={x:(a.x+b.x)/2,y:(a.y+b.y)/2},length=Math.hypot(mid.x,mid.y);
    // Endpoints remain fixed so adjoining terrain never acquires a random fissure.
    for(let i=1;i<5;i++){
      const t=i/5,chip=[0,4,11,8,3][i];
      result.push({x:a.x+(b.x-a.x)*t-mid.x/length*chip,y:a.y+(b.y-a.y)*t-mid.y/length*chip});
    }
    result.push(b);return result;
  }
  function boundary(voidMask=0){return Array.from({length:6},(_,edge)=>edgePoints(edge,voidMask).slice(0,-1)).flat();}
  function containsLocal(x,y){
    const dx=Math.abs(x-radius),dy=Math.abs(y-height/2);
    return dx<=radius&&dy<=height/2&&Math.sqrt(3)*dx+dy<=height+1e-8;
  }
  function drawGround(ctx,source,voidMask=0){
    ctx.save();ctx.beginPath();boundary(voidMask).forEach((p,i)=>{const x=p.x+radius,y=p.y+height/2;if(i)ctx.lineTo(x,y);else ctx.moveTo(x,y);});ctx.closePath();ctx.clip();
    // Preserve original source; crop only its black padding outside the source hex.
    const scale=radius*2/source.width;
    ctx.drawImage(source,0,-(source.height*scale-height)/2,radius*2,source.height*scale);ctx.restore();
  }
  const cliffDepth=90;
  function cliffFaces(voidMask){
    const faces=[];
    for(let edge=0;edge<3;edge++){
      if(!(voidMask&(1<<edge)))continue;
      const top=edgePoints(edge,voidMask).map(v=>({x:v.x,y:v.y*perspectiveY}));
      const bottom=top.map((v,i)=>({x:v.x,y:v.y+(i===0||i===top.length-1?72:[0,61,83,69,88][i])}));
      faces.push({edge,top,bottom,polygon:top.concat([...bottom].reverse())});
    }
    return faces;
  }
  function drawCliffs(ctx,source,voidMask){
    for(const face of cliffFaces(voidMask)){
      ctx.save();ctx.beginPath();face.polygon.forEach((p,i)=>{const x=p.x+radius,y=p.y+height*perspectiveY/2;if(i)ctx.lineTo(x,y);else ctx.moveTo(x,y);});ctx.closePath();ctx.clip();
      ctx.drawImage(source,0,0,radius*2,height*perspectiveY+cliffDepth);
      ctx.fillStyle=face.edge===0?'#111b2526':face.edge===2?'#09111f55':'#14233718';ctx.fill();ctx.restore();
    }
  }
  function variantIndex(q,r,count){return ((Math.imul(q,73856093)^Math.imul(r,19349663))>>>0)%count;}
  return{radius,height,perspectiveY,vertex,point,unproject,edgePoints,boundary,containsLocal,drawGround,cliffDepth,cliffFaces,drawCliffs,variantIndex};
});
