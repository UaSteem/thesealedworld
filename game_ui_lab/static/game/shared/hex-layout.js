(function(root){
  'use strict';
  const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
  function vertices(x,y,r){return Array.from({length:6},(_,i)=>{const a=i*Math.PI/3;return{x:x+r*Math.cos(a),y:y+r*Math.sin(a)};});}
  function edge(x,y,r,from,to,fraction){const p=vertices(x,y,r),a=p[from],b=p[to],inset=.12,start={x:a.x+(b.x-a.x)*inset,y:a.y+(b.y-a.y)*inset},end={x:b.x-(b.x-a.x)*inset,y:b.y-(b.y-a.y)*inset};return{from,to,start,end,fillEnd:{x:start.x+(end.x-start.x)*clamp(fraction,0,1),y:start.y+(end.y-start.y)*clamp(fraction,0,1)},fraction:clamp(fraction,0,1)};}
  function overlaps(a,b,pad=5){return a.x<b.x+b.width+pad&&a.x+a.width+pad>b.x&&a.y<b.y+b.height+pad&&a.y+a.height+pad>b.y;}
  function bounds(x,y,r){return{x:x-r-2,y:y-Math.sqrt(3)*r/2-2,width:2*r+4,height:Math.sqrt(3)*r+10};}
  function slots(width,height){
    const primary=clamp(Math.round(width*.077),76,94),queue=clamp(Math.round(width*.029),29,44),ally=clamp(Math.round(width*.036),38,58);
    return{hero:{x:width*.41,y:height*.53,radius:primary},target:{x:width*.66,y:height*.30,radius:Math.round(primary*.87)},enemies:Array.from({length:5},(_,i)=>({x:width*(.52+i*.10),y:Math.max(queue*.87+12,height*.10),radius:queue})),allies:Array.from({length:3},(_,i)=>({x:width*(.085+i*.10),y:height*.83,radius:ally}))};
  }
  const api={vertices,edge,bounds,overlaps,slots};if(typeof module!=='undefined'&&module.exports)module.exports=api;if(root)root.HexCardLayout=api;
})(typeof window==='undefined'?null:window);
