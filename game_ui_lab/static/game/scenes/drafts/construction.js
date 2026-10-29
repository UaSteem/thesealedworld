// Lab-only sample values and deterministic proposals, not a city progression API.
const RESOURCES=['wood','stone','iron'];
const CATALOG=[
  {type:'trade',name:'Торговый квартал',cost:{wood:120,stone:90,iron:30}},
  {type:'craft',name:'Ремесленный квартал',cost:{wood:90,stone:120,iron:60}},
  {type:'housing',name:'Жилой квартал',cost:{wood:150,stone:90,iron:20}},
  {type:'arena',name:'Квартал арены',cost:{wood:100,stone:180,iron:70}},
];
const clone=value=>JSON.parse(JSON.stringify(value));

export function createConstructionDemo(){
  let state;
  function propose(cycle){
    // Rotation is deliberately only a reproducible visual-test fixture.
    // Repeated types represent additional district instances, not exclusions.
    return Array.from({length:3},(_,index)=>{
      const entry=CATALOG[(cycle-1+index)%CATALOG.length];
      return {id:`cycle-${cycle}-${entry.type}`,type:entry.type,name:entry.name,
        cost:{...entry.cost},progress:{wood:0,stone:0,iron:0}};
    });
  }
  function inspect(){return clone(state);}
  function reset(){
    state={cycle:1,inventory:{wood:5000,stone:5000,iron:5000},options:propose(1),built:[],lastCompletion:null};
    return inspect();
  }
  function contribute(optionId,resourceId,amount){
    if(!Number.isSafeInteger(amount)||amount<=0)return {ok:false,reason:'invalid-amount',accepted:0,completed:false};
    if(!RESOURCES.includes(resourceId))return {ok:false,reason:'unknown-resource',accepted:0,completed:false};
    const option=state.options.find(value=>value.id===optionId);
    if(!option)return {ok:false,reason:'unknown-option',accepted:0,completed:false};
    const accepted=Math.min(amount,option.cost[resourceId]-option.progress[resourceId],state.inventory[resourceId]);
    if(accepted<=0)return {ok:false,reason:'nothing-needed-or-available',accepted:0,completed:false};
    option.progress[resourceId]+=accepted;
    state.inventory[resourceId]-=accepted;
    const completed=RESOURCES.every(resource=>option.progress[resource]===option.cost[resource]);
    if(completed){
      const built={id:`district-${state.built.length+1}`,type:option.type,name:option.name,cycle:state.cycle};
      const discarded=state.options.filter(value=>value.id!==option.id).map(value=>({id:value.id,name:value.name,progress:{...value.progress}}));
      state.built.push(built);
      state.lastCompletion={...built,discarded};
      state.cycle++;
      state.options=propose(state.cycle);
    }
    return {ok:true,accepted,completed,cycle:state.cycle};
  }
  reset();
  return {inspect,contribute,reset};
}
