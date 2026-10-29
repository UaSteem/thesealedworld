(() => {
  'use strict';
  const iconRoot='/static/images/ui/combat-icons/';
  function preload(scene){
    scene.load.image('combat-controls-v1','/ui-static/assets/combat-controls-v1.png');
    const L=window.LabHudLayout;
    L.tokens.forEach(t=>scene.load.svg(`hud-token-${t.id}`,`${iconRoot}token-${t.id}.svg`,{width:128,height:128}));
    L.abilities.forEach(a=>scene.load.svg(`hud-ability-${a.id}`,`${iconRoot}abilities/${a.id}.svg`,{width:128,height:128}));
    scene.load.image('hud-attack-art','/ui-static/assets/combat-attack-v1.png');
    scene.load.image('hud-wait-art','/ui-static/assets/combat-wait-v1.png');
  }
  function draw(scene,options){
    const L=window.LabHudLayout,layout=L.compute(options.width,options.height),scale=layout.scale;
    const root=scene.add.container(layout.x,layout.y).setScale(scale).setDepth(10000);
    const skin=scene.add.image(0,0,'combat-controls-v1').setOrigin(0);root.add(skin);
    const hits=[],labels=[],counts={tempo:2,hit:5,crit:1,dodge:3,parry:2,block:0,pressure:1,blood:0,gift:2};
    const text=(x,y,label,screenSize=12,color='#f0e1bd')=>{
      const t=scene.add.text(x,y,label,{fontFamily:getComputedStyle(document.documentElement).getPropertyValue('--font-ui').trim(),fontSize:`${screenSize/scale}px`,color,align:'center'}).setOrigin(.5).setResolution(Math.min(2,window.devicePixelRatio||1));root.add(t);return t;
    };
    const tooltip=text(970,30,'',12);tooltip.setBackgroundColor('#142027ee').setPadding(12,8).setVisible(false);
    const hideTip=()=>tooltip.setVisible(false);
    scene.game.canvas.addEventListener('pointerleave',hideTip);
    root.once('destroy',()=>scene.game.canvas.removeEventListener('pointerleave',hideTip));
    const showTip=(label)=>{tooltip.setText(label).setVisible(true);root.bringToTop(tooltip);};
    const outline=scene.add.graphics();root.add(outline);
    const interactive=(id,kind,region,label,callback)=>{
      const circle=!!region.radius;
      const hit=scene.add.zone(region.x,region.y,circle?region.radius*2:region.width,circle?region.radius*2:region.height);
      if(circle)hit.setInteractive(new Phaser.Geom.Circle(region.radius,region.radius,region.radius),Phaser.Geom.Circle.Contains);else hit.setInteractive();
      hit.input.cursor='pointer';root.add(hit);
      hit.on('pointerover',()=>showTip(label));hit.on('pointerout',()=>tooltip.setVisible(false));
      hit.on('pointerdown',()=>callback?.());
      const world=L.world(region,layout);
      hits.push({id,kind,local:{...region},world:{x:world.x-world.width/2,y:world.y-world.height/2,width:world.width,height:world.height},center:{x:world.x,y:world.y}});
    };
    const ready=options.ready!==false;
    const attackIcon=ready?'hud-attack-art':'hud-wait-art';
    root.add(scene.add.image(L.attack.x,L.attack.y,attackIcon).setDisplaySize(220,220));
    interactive('attack','attack',L.attack,ready?'Атака по выбранной цели':'Ожидание готовности',()=>{if(ready)options.onAttack?.();});
    L.tokens.forEach(token=>{
      root.add(scene.add.image(token.x,token.y-7,`hud-token-${token.id}`).setDisplaySize(70,70).setTint(0xe7c98d));
      text(token.x,token.y+42,String(counts[token.id]),12);
      interactive(token.id,'token',token,`${token.label}: ${counts[token.id]}`);
    });
    L.feints.forEach(feint=>{
      const cost=Object.entries(feint.cost).map(([id,n])=>`${L.tokens.find(t=>t.id===id).label} ${n}`).join(' · ');
      text(feint.x,feint.y,feint.label,13);
      const descriptions={sword_measured_line:'Повышает точность следующего удара.',sword_blade_bind:'Снижает шанс парирования следующего удара целью.',sword_low_angle:'Снижает шанс уклонения цели от следующего удара.'};
      const cardText=`${feint.label}\n${descriptions[feint.id]}\n\nСтоимость: ${cost}`;
      const region={x:feint.x,y:feint.y,width:480,height:100};
      interactive(feint.id,'feint',region,cardText,()=>{outline.clear().lineStyle(5,0xf5d996,1).strokeRoundedRect(feint.x-240,feint.y-50,480,100,12);showTip(cardText);options.onFeint?.(feint.id);});
      labels.push({id:feint.id,label:feint.label,cost:feint.cost,costVisible:false,tooltip:cardText});
    });
    L.abilities.forEach(ability=>{
      root.add(scene.add.image(ability.x,ability.y,`hud-ability-${ability.id}`).setDisplaySize(92,92).setTint(0xe7c98d));
      interactive(ability.id,'ability',ability,ability.label,()=>{outline.clear().lineStyle(5,0xf5d996,1).strokeCircle(ability.x,ability.y,ability.radius);showTip(ability.label);options.onAbility?.(ability.id);});
    });
    return{objects:[root],inspect:{nativeSize:{...L.SIZE},layout,ready,attackIcon,waitingIcon:!ready,selectedId:options.selectedId,attack:L.attack,tokens:L.tokens.map(t=>({...t,count:counts[t.id]})),feints:labels,abilities:L.abilities.map(a=>({...a})),hits}};
  }
  window.LabCombatHud={preload,draw};
})();
