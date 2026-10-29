/* Local illustrative combat state. No game formulas, transport or persistence. */
(function(root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.LabCombatDemo = api;
})(typeof window === 'undefined' ? null : window, function() {
  'use strict';
  const icon = name => `/static/images/ui/combat-icons/${name}.svg`;
  const TOKEN_TYPES = Object.freeze([
    ['tempo','Темп'],['hit','Попадание'],['crit','Крит'],['dodge','Уклонение'],
    ['parry','Парирование'],['block','Блок'],['pressure','Натиск'],['blood','Кровь'],['gift','Дар'],
  ].map(([id,label]) => Object.freeze({id,label,iconUrl:icon(`token-${id}`)})));
  const FEINTS = Object.freeze([
    {id:'rush',label:'Натиск',iconUrl:icon('feints/group-basic'),cost:{tempo:2}},
    {id:'break',label:'Пробой',iconUrl:icon('feints/group-weapon'),cost:{hit:2}},
    {id:'guard',label:'Контрход',iconUrl:icon('feints/group-tactical'),cost:{parry:2}},
  ].map(Object.freeze));
  const ABILITIES = Object.freeze([
    {id:'energy-strike',label:'Силовой удар',iconUrl:icon('ability-debug-rays'),cost:{resource:'en',amount:8}},
    {id:'frost',label:'Сковать',iconUrl:icon('ability-debug-swirl'),cost:{resource:'conc',amount:6}},
    {id:'heal',label:'Восстановить',iconUrl:icon('ability-debug-shield'),cost:{resource:'en',amount:10}},
    {id:'gift',label:'Дар',iconUrl:icon('gift-token'),cost:{resource:'gift',amount:1}},
  ].map(Object.freeze));
  const portraits = [
    ['Налётчик','bandit_gang.bandit_raider'],['Страж','bandit_gang.bandit_blackguard'],
    ['Разведчик','bandit_gang.bandit_lookout'],['Головорез','bandit_gang.bandit_thug'],
    ['Капитан','bandit_gang.bandit_captain'],['Колдун','bandit_gang.bandit_hedge_wizard'],
    ['Стрелок','bandit_gang.bandit_poacher'],['Разбойник','bandit_gang.bandit_cutthroat'],
  ];
  let sessionSerial = 0;
  const clone = value => JSON.parse(JSON.stringify(value));
  const clamp = (value,min,max) => Math.max(min,Math.min(max,value));
  function randomSource(seed) {
    let state = 2166136261;
    for (const char of String(seed)) state = Math.imul(state ^ char.charCodeAt(0),16777619) >>> 0;
    return () => { state = (Math.imul(state,1664525) + 1013904223) >>> 0; return state / 4294967296; };
  }
  class Model {
    constructor(options = {}) { this.reset(options); }
    reset(options = {}) {
      this.options = {...{seed:1,enemyCount:10,allyCount:4},...options};
      this.random = randomSource(this.options.seed);
      this.sessionId = `demo-${++sessionSerial}`;
      this.revision = 0;this.sequence = 0;this.pending = new Map();
      const count = (value,fallback,max) => clamp(Number.isFinite(Number(value)) ? Math.floor(Number(value)) : fallback,1,max);
      const enemies = count(this.options.enemyCount,10,60), allies = count(this.options.allyCount,4,10);
      this.actors = [];
      for (let index=0; index<enemies; index++) {
        const [name,portrait] = portraits[index % portraits.length];
        const hp = 70 + Math.floor(this.random()*60);
        this.actors.push({id:`enemy-${index+1}`,side:'enemy',name:`${name} ${index+1}`,
          portraitUrl:`/static/images/monsters/catalog/${portrait}.png`,hp,maxHp:hp,en:28,maxEn:40,
          conc:35,maxConc:50,intent:index<Math.ceil(enemies/2)?'waiting':'acted',lastEvent:null});
      }
      const avatars=['rook7.webp','veil4.webp','silhouette_f.webp','silhouette_m.webp'];
      for (let index=0; index<allies; index++) this.actors.push({id:`ally-${index+1}`,side:'ally',
        name:index===0?'Ada Guard':`Союзник ${index+1}`,portraitUrl:`/static/images/avatars/${avatars[index%avatars.length]}`,
        hp:90,maxHp:117,en:31,maxEn:40,conc:42,maxConc:54,intent:'waiting',
        // Illustrative fixture intentions, not authoritative combat history.
        actedAgainstIds:[`enemy-${index%Math.min(3,enemies)+1}`],lastEvent:null});
      this.queue = this.actors.filter(a=>a.side==='enemy').map(a=>a.id);
      this.selectedId = this.queue[0];
      this.tokens = Object.fromEntries(TOKEN_TYPES.map((token,index)=>[token.id,index===8?2:index%4]));
      return this.snapshot();
    }
    snapshot() {
      const actors=this.actors.map(actor=>actor.side==='ally'?
        {...actor,intent:actor.actedAgainstIds.includes(this.selectedId)?'acted':'waiting'}:actor);
      return clone({sessionId:this.sessionId,revision:this.revision,actors,selectedId:this.selectedId,tokens:this.tokens});
    }
    selectTarget(id) {
      if (!this.actors.some(a=>a.id===id&&a.side==='enemy'&&a.hp>0)) return false;
      this.selectedId=id;this.revision++;return true;
    }
    _next(id) {
      const start=this.queue.indexOf(id);
      for(let step=1;step<=this.queue.length;step++) {
        const next=this.queue[(start+step)%this.queue.length];
        if(this.actors.some(a=>a.id===next&&a.hp>0))return next;
      }
      return null;
    }
    _outcome(actor,kind='attack',rotate=true) {
      if (!actor || actor.hp<=0 || this.pending.size>=128) return null;
      const previousTargetId=this.selectedId;
      const number=++this.sequence;
      const effect = kind==='heal'?{id:'renew',label:'Восстановление',kind:'healing'}:
        kind==='frost'?{id:'slow',label:'Замедление',kind:'control'}:
        number%3===0?{id:'bleed',label:'Кровотечение',kind:'damage'}:
        {id:'guard',label:'Блок',kind:'block'};
      const event={sessionId:this.sessionId,eventId:`${this.sessionId}:event-${number}`,
        exchangeId:number,actorId:actor.id,damage:kind==='heal'?0:12+Math.floor(this.random()*12),
        healing:kind==='heal'?18:number%5===0?5:0,blocked:kind==='heal'?0:number%2===0?6:0,effect};
      this.pending.set(event.eventId,clone(event));
      if (rotate) {actor.intent='acted';this.selectedId=this._next(actor.id);}
      this.revision++;
      return {event:clone(event),delayMs:480+(number%3)*90,previousTargetId,nextTargetId:this.selectedId};
    }
    attack() {
      const actor=this.actors.find(a=>a.id===this.selectedId&&a.side==='enemy');
      const outcome=this._outcome(actor);
      if(outcome) {this.tokens.tempo=clamp(this.tokens.tempo+1,0,999);this.tokens.hit=clamp(this.tokens.hit+1,0,999);}
      return outcome;
    }
    canUseAbility(id) {
      const ability=ABILITIES.find(a=>a.id===id),hero=this.actors.find(a=>a.side==='ally');
      if(!ability||!hero||hero.hp<=0||this.pending.size>=128)return false;
      const {resource,amount}=ability.cost;
      return (resource==='gift'?this.tokens.gift:hero[resource])>=amount &&
        (id==='heal'||this.actors.some(a=>a.id===this.selectedId&&a.hp>0));
    }
    useAbility(id) {
      if(!this.canUseAbility(id))return null;
      const ability=ABILITIES.find(a=>a.id===id),hero=this.actors.find(a=>a.side==='ally');
      const actor=id==='heal'?hero:this.actors.find(a=>a.id===this.selectedId);
      const result=this._outcome(actor,id,id!=='heal');
      if(result){const {resource,amount}=ability.cost;if(resource==='gift')this.tokens.gift-=amount;else hero[resource]-=amount;}
      return result;
    }
    canUseFeint(id) {
      const feint=FEINTS.find(f=>f.id===id);
      return !!feint&&this.pending.size<128&&this.actors.some(a=>a.id===this.selectedId&&a.hp>0)&&
        Object.entries(feint.cost).every(([key,amount])=>this.tokens[key]>=amount);
    }
    useFeint(id) {
      if(!this.canUseFeint(id))return null;
      const result=this._outcome(this.actors.find(a=>a.id===this.selectedId),id);
      if(result)for(const [key,amount]of Object.entries(FEINTS.find(f=>f.id===id).cost))this.tokens[key]-=amount;
      return result;
    }
    applyEvent(event) {
      if(!event||event.sessionId!==this.sessionId)return false;
      const pending=this.pending.get(event.eventId);
      if(!pending||pending.actorId!==event.actorId||pending.exchangeId!==event.exchangeId)return false;
      const actor=this.actors.find(a=>a.id===pending.actorId);
      if(!actor)return false;
      this.pending.delete(event.eventId);
      actor.hp=clamp(actor.hp-pending.damage+pending.healing,0,actor.maxHp);
      if(!actor.lastEvent||actor.lastEvent.exchangeId<pending.exchangeId)actor.lastEvent=clone(pending);
      if(this.selectedId===actor.id&&actor.hp===0)this.selectedId=this._next(actor.id);
      this.revision++;return true;
    }
  }
  return {Model,TOKEN_TYPES,FEINTS,ABILITIES};
});
