(function(root){
  'use strict';
  const SIZE={width:1942,height:809};
  const tokenIds=['tempo','hit','crit','dodge','parry','block','pressure','blood','gift'];
  const tokenLabels=['Темп','Попадание','Крит','Уворот','Парирование','Блок','Натиск','Кровь','Дар'];
  const tokens=tokenIds.map((id,i)=>{const angle=(-70+i*40)*Math.PI/180;return{id,label:tokenLabels[i],x:1575+255*Math.cos(angle),y:400+255*Math.sin(angle),radius:49};});
  const feints=[{id:'sword_measured_line',label:'Точный удар',cost:{hit:3},x:960,y:215},{id:'sword_blade_bind',label:'Связать клинок',cost:{hit:3,parry:2},x:940,y:365},{id:'sword_low_angle',label:'Срезать уворот',cost:{hit:3,dodge:2},x:930,y:510}];
  const abilityIds=['basic_blood_hunger','basic_break_stance','basic_cleave_gift','basic_expose_weakness','basic_last_push','basic_slip_pain','basic_splinter_strike','basic_wipe_blood'];
  const abilityLabels=['Жажда крови','Сломать стойку','Рассекающий дар','Открыть слабость','Последний рывок','Скользнуть сквозь боль','Расщепляющий удар','Остановить кровь'];
  const abilities=abilityIds.map((id,i)=>({id,label:abilityLabels[i],x:[160,310,465,620,775,930,1085,1240][i],y:665,radius:56}));
  function compute(width,height){
    const displayWidth=Math.min(width>=1300?570:510,width-24),scale=displayWidth/SIZE.width;
    const displayHeight=SIZE.height*scale;
    return{x:width-displayWidth-12,y:height-displayHeight-10,scale,width:displayWidth,height:displayHeight};
  }
  function world(region,layout){return{x:layout.x+region.x*layout.scale,y:layout.y+region.y*layout.scale,width:(region.width||region.radius*2)*layout.scale,height:(region.height||region.radius*2)*layout.scale};}
  const api={SIZE,tokens,feints,abilities,attack:{x:1575,y:400,radius:145},compute,world};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  if(root)root.LabHudLayout=api;
})(typeof window==='undefined'?null:window);
