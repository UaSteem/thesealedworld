// Offline contracts for mock expansion and variable-footprint placement.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const source=await readFile(new URL('./static/game/scenes/inventory/data.js',import.meta.url),'utf8');
const {expandMock,packInventory,filterItems,mockWeight,annotateFixture,inventoryFilters}=await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
const fixture=JSON.parse(await readFile(new URL('./data/inventory.json',import.meta.url),'utf8'));
const expanded=expandMock(fixture,12);
assert.equal(fixture.items.length,6);
assert.equal(expanded.items.length,72);
assert.equal(new Set(expanded.items.map(i=>i.item_id)).size,72);
assert.equal(packInventory(fixture.items).rows,5);
for(const items of [expanded.items,Array.from({length:72},(_,i)=>({item_id:`mixed-${i}`,grid_w:1+i%3,grid_h:1+i%4}))]){
  const packed=packInventory(items),occupied=new Set();
  assert.equal(packed.placements.length,items.length);
  assert(packed.rows>5);
  for(const p of packed.placements){
    assert(p.col>=0&&p.col+p.width<=8&&p.row>=0&&p.row+p.height<=packed.rows);
    for(let y=0;y<p.height;y++)for(let x=0;x<p.width;x++){
      const key=`${p.row+y}:${p.col+x}`;
      assert(!occupied.has(key),'overlapping footprint');occupied.add(key);
    }
  }
}
assert.throws(()=>expandMock(fixture,0));
assert.throws(()=>packInventory([{grid_w:9,grid_h:1}]));
console.log('Inventory placement: fixture + 72 repeated + 72 mixed footprints pass');

const annotated=annotateFixture(fixture);
assert.equal(filterItems(annotated.items,'weapons').length,6);
assert.equal(filterItems(annotated.items,'all').length,6);
for(const filter of inventoryFilters.filter(f=>!['all','weapons'].includes(f.id)))assert.equal(filterItems(annotated.items,filter.id).length,0);
assert.equal(filterItems([{item_type:'garment'},{item_type:'accessory'}],'armor').length,1);
assert.equal(filterItems([{item_type:'material'},{item_type:'resource'},{item_type:'weapon'}],'resources').length,2);
assert.equal(mockWeight(annotated.items).value,16);
assert.equal(mockWeight(filterItems(annotated.items,'armor')).mock,true);
assert.equal(fixture.items[0].lab_weight_kg,undefined);
assert.throws(()=>filterItems(annotated.items,'special'));
console.log('Inventory filters, empty categories, grouping and explicit mock weight pass');
