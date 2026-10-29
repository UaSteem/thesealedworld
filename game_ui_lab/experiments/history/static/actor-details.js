(() => {
  const host=document.getElementById('combat-stage'),panel=document.getElementById('actor-details');
  const openGroups=new Set();
  const node=(tag,text)=>{const n=document.createElement(tag);n.textContent=text;return n;};
  function rows(items){const dl=document.createElement('dl');for(const [label,value] of items){const row=document.createElement('div');row.append(node('dt',label),node('dd',value));dl.append(row);}return dl;}
  host.addEventListener('lab-actor-preview',({detail})=>{
    const a=detail.actor;if(!a)return;
    const id=a.actor_id||a.id,scroll=panel.dataset.actorId===id?panel.scrollTop:0;
    panel.dataset.actorId=id;
    panel.replaceChildren(node('small',detail.pinned?'ВЫБРАННЫЙ УЧАСТНИК':'ОСМОТР УЧАСТНИКА'),node('h3',a.name));
    panel.append(node('p',[a.role,a.power_score!=null?`Сила ${a.power_score}`:null].filter(Boolean).join(' · ')));
    const v=a.vitals;
    panel.append(rows([['Здоровье',`${v?.hp_current??a.hp} / ${v?.hp_max??a.maxHp}`],['Энергия',`${v?.energy_current??a.en??0} / ${v?.energy_max??a.maxEn??0}`],['Стамина',`${v?.stamina_current??a.conc??a.stamina??0} / ${v?.stamina_max??a.maxConc??a.maxStamina??0}`]]));
    const sections=a.stat_sheet?.sections||[];
    const damage=sections.flatMap(s=>s.items).find(item=>item.key.endsWith('_damage')||item.key==='damage');
    const accuracy=sections.flatMap(s=>s.items).find(item=>item.key.endsWith('_accuracy')||item.key==='accuracy');
    const danger=[];if(damage)danger.push(['Урон',damage.value_text]);if(accuracy)danger.push(['Точность',accuracy.value_text]);
    if(danger.length){const summary=rows(danger);summary.className='actor-damage';panel.append(summary);}
    panel.append(node('p',a.intentLabel||(a.acted?'Уже действовал против вас':'Ожидает размена')));
    const effects=a.active_effects?.map(e=>[e.title||e.effect_id,e.duration_label].filter(Boolean).join(' · '))||a.effects||[];
    panel.append(node('p',effects.join(' · ')||'Нет активных эффектов'));
    for(const section of sections){
      const group=document.createElement('details');group.dataset.section=section.key;group.open=openGroups.has(section.key);
      group.append(node('summary',section.label),rows(section.items.map(item=>[item.label,item.value_text])));
      group.addEventListener('toggle',()=>{if(group.open)openGroups.add(section.key);else openGroups.delete(section.key);});
      panel.append(group);
    }
    panel.scrollTop=scroll;
  });
})();
