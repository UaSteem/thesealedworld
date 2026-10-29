(function(root){
  'use strict';
  function radiusForFrame(width,height=Infinity){return Math.min(92,Math.max(76,Math.min(Math.floor((width-248-12)/(Math.sqrt(3)*5.5)),Math.floor((height-40)/4.75))));}
  function prioritize(actors){return [...actors].sort((a,b)=>Number(b.actedAgainstViewer)-Number(a.actedAgainstViewer)||a.deadlineMs-b.deadlineMs);}
  function rowsForFrame(height,radius){
    const pitch=1.5*radius*.95;
    return [5,3].find(rows=>(rows-1)*pitch+2*radius*.95+40<=height)||3;
  }
  function containsPoint(radius,x,y){
    const v=Math.abs(y)/.95;
    return Math.abs(x)<=Math.sqrt(3)*radius/2+.01 && v<=radius-Math.abs(x)/Math.sqrt(3)+.01;
  }
  function gridForFrame(width,height){
    const perspectiveY=1;
    const radius=Math.min(92,Math.floor((width-48)/(Math.sqrt(3)*7.5)),Math.floor((height-32)/(9.5*perspectiveY)));
    const dx=Math.sqrt(3)*radius,dy=1.5*radius*perspectiveY;
    const removed=new Set(['0:0','0:1','1:0','1:1','2:0','3:0','2:6','3:6','4:5','4:6','5:5','5:6']);
    const raw=[];
    for(let row=0;row<6;row++)for(let col=0;col<7;col++){if(removed.has(`${row}:${col}`))continue;raw.push({col,row,zone:'grid',x:dx*(col+((row+1)%2)/2),y:dy*row});}
    const minX=Math.min(...raw.map(p=>p.x))-dx/2,maxX=Math.max(...raw.map(p=>p.x))+dx/2;
    const minY=Math.min(...raw.map(p=>p.y))-radius*perspectiveY,maxY=Math.max(...raw.map(p=>p.y))+radius*perspectiveY;
    const ox=(width-(maxX-minX))/2-minX,oy=(height-(maxY-minY))/2-minY;
    return{radius,perspectiveY,coreColumns:7,coreRows:6,cells:raw.map(p=>({...p,x:Math.round(p.x+ox),y:Math.round(p.y+oy)})),bounds:{x:minX+ox,y:minY+oy,width:maxX-minX,height:maxY-minY}};
  }
  const api={radiusForFrame,prioritize,rowsForFrame,containsPoint,gridForFrame};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  if(root)root.StandeeLayout=api;
})(typeof window==='undefined'?null:window);
