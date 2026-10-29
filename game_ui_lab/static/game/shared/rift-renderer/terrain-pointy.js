/* Live pointy display. Logical q/r and mask bit identities remain server-owned. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.RiftTerrain=api;})(globalThis,()=>{
 'use strict';
 const radius=128,height=256,perspectiveY=1,cliffDepth=92,orientation='pointy-top';
 const vertex=i=>({x:radius*Math.cos(-Math.PI/2+i*Math.PI/3),y:radius*Math.sin(-Math.PI/2+i*Math.PI/3)});
 const point=(q,r)=>({x:Math.sqrt(3)*radius*(q+r/2),y:1.5*radius*r*perspectiveY});
 const bitForEdge=edge=>(edge+5)%6,edgePoints=edge=>[vertex(edge),vertex(edge+1)];
 const boundary=()=>Array.from({length:6},(_,i)=>vertex(i));
 const contains=(x,y,gutter=0)=>Math.abs(x)<=Math.sqrt(3)*radius/2-gutter+1e-8&&Math.abs(x)+Math.sqrt(3)*Math.abs(y)<=Math.sqrt(3)*radius-2*gutter+1e-8;
 const containsLocal=(x,y)=>contains(x-radius,y-height/2),unproject=(x,y)=>({x,y:y/perspectiveY});
 function cliffFaces(mask){return[2,3].filter(edge=>mask&(1<<bitForEdge(edge))).map(edge=>{const a=vertex(edge),b=vertex(edge+1),top=[{x:a.x,y:a.y*perspectiveY},{x:b.x,y:b.y*perspectiveY}],bottom=[{x:b.x,y:b.y*perspectiveY+84},{x:a.x+(b.x-a.x)*.70,y:(a.y+(b.y-a.y)*.70)*perspectiveY+92},{x:a.x+(b.x-a.x)*.35,y:(a.y+(b.y-a.y)*.35)*perspectiveY+76},{x:a.x,y:a.y*perspectiveY+84}];return{edge,top,bottom,polygon:top.concat(bottom)};});}
 const variantIndex=(q,r,count)=>((Math.imul(q,73856093)^Math.imul(r,19349663))>>>0)%count;
 return{radius,height,perspectiveY,cliffDepth,orientation,vertex,point,bitForEdge,edgePoints,boundary,contains,containsLocal,unproject,cliffFaces,variantIndex};
});
