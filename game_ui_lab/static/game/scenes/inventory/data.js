export function expandMock(data, copies = 1) {
  if (!Number.isSafeInteger(copies) || copies < 1 || copies > 100) throw new Error('copies must be 1–100');
  const originals=data.items;
  return {...data, mockCopies:copies, items:Array.from({length:copies},(_,copy)=>originals.map(item=>({...item,item_id:copy?`${item.item_id}:mock-${copy+1}`:item.item_id}))).flat()};
}

// Row-major footprint packing; rows grow to hold content, never a capacity rule.
export function packInventory(items, columns=8, minimumRows=5) {
  const occupied=new Set(),placements=[];
  let rows=minimumRows;
  for(const item of items){
    const width=Math.floor(Number(item.grid_w)),height=Math.floor(Number(item.grid_h));
    if(width<1 || width>columns || height<1) throw new Error('Invalid item footprint');
    let placed=false;
    for(let row=0;!placed;row++)for(let col=0;col<=columns-width;col++){
      let free=true;
      for(let y=0;y<height;y++)for(let x=0;x<width;x++)if(occupied.has(`${row+y}:${col+x}`))free=false;
      if(!free)continue;
      for(let y=0;y<height;y++)for(let x=0;x<width;x++)occupied.add(`${row+y}:${col+x}`);
      placements.push({item,col,row,width,height});rows=Math.max(rows,row+height);placed=true;break;
    }
  }
  return {placements,rows};
}

export function readInventory() {
  const data = JSON.parse(document.getElementById('inventory-data').textContent);
  if (data.columns !== 8 || !Array.isArray(data.items) || !data.items.length) throw new Error('Invalid frozen inventory fixture');
  const ids = new Set();
  for (const item of data.items) {
    if (!item.item_id || ids.has(item.item_id) || !Array.isArray(item.details) || !Array.isArray(item.affixes)) throw new Error('Invalid inventory item');
    ids.add(item.item_id);
  }
  const query=new URLSearchParams(location.search);
  return expandMock(annotateFixture(data),query.has('copies')?Number(query.get('copies')):1);
}

// UI grouping follows current ItemType; no category is inferred from rarity.
export const inventoryFilters=[
  {id:'all',label:'Все'}, {id:'weapons',label:'Оружие',types:['weapon']},
  {id:'armor',label:'Броня',types:['armor','garment']},
  {id:'accessories',label:'Аксессуары',types:['accessory']},
  {id:'consumables',label:'Расходники',types:['consumable']},
  {id:'resources',label:'Ресурсы',types:['resource','material']},
  {id:'quest',label:'Квестовые',types:['quest']},
];
export function filterItems(items,id){
  const filter=inventoryFilters.find(entry=>entry.id===id);
  if(!filter)throw new Error('Unknown inventory filter');
  return id==='all'?items:items.filter(item=>filter.types.includes(item.item_type));
}
export function mockWeight(items){return {value:items.reduce((sum,item)=>sum+(item.lab_weight_kg||0),0)+4,limit:30,worn:4,mock:true};}
export function annotateFixture(data){return {...data,items:data.items.map(item=>({...item,item_type:'weapon',lab_weight_kg:2}))};}
