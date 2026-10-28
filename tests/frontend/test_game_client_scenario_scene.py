"""Scenario presentation keeps server choices, proportions and real context values."""
import shutil
import subprocess
from pathlib import Path


def test_scenario_mapping_and_two_column_layout():
    source = Path('src/frontend/static/js/game/client/scenario-scene.js').resolve()
    script = r"""
const fs=require('fs'),assert=require('node:assert/strict');
(async()=>{
const {layoutScenarioChoices,scenarioContextLines}=await import('data:text/javascript;base64,'+fs.readFileSync(process.argv[1]).toString('base64'));
for(const count of [1,3,6,9]){
 const choices=Array.from({length:count},(_,i)=>({label:'Ответ '+i,action_id:'actual-'+i}));
 const before=JSON.stringify(choices),layout=layoutScenarioChoices(choices,610,{measure:()=>38});
 assert.equal(layout.cells.length,count);assert.equal(JSON.stringify(choices),before);
 assert.equal(layout.cells[0].width,300);
 for(let i=0;i<count;i++){assert.equal(layout.cells[i].action_id,'actual-'+i);assert.equal(layout.cells[i].x,i%2*310);}
 if(count%2)assert.equal(layout.cells.at(-1).width,300);
}
const long=layoutScenarioChoices([{label:'long',action_id:'a'},{label:'short',action_id:'b'},{label:'next',action_id:'c'}],610,{measure:s=>s==='long'?120:20});
assert.equal(long.cells[0].height,long.cells[1].height);assert.ok(long.cells[2].y>=long.cells[0].height+10);
const model={status_bar:['Голод: 0'],system_messages:['Только серверное сообщение'],extra_data:{npc_reputation:0,npc_affinity:false,reputation:{npc:0,faction:false},right_panel:{widgets:[{type:'key_value',title:'Запасы',items:[{label:'Время',value:0},{label:'Проход',value:false}]},{type:'meter_list',title:'Профиль',items:[{label:'Путь',display_value:'0 / 10',value:0}]},{type:'text',data:{text:'Наблюдение'}},{type:'key_value',visible:false,title:'Скрыт',items:[{label:'Нельзя',value:999}]}]}}};
const lines=scenarioContextLines(model);const text=lines.map(line=>line.text).join('\n');
for(const expected of ['Голод: 0','Только серверное сообщение','NPC: 0','Фракция: false','Время: 0','Проход: false','Путь: 0 / 10','Наблюдение','Репутация NPC: 0','Отношение NPC: false'])assert.ok(text.includes(expected),expected);
assert.ok(!text.includes('Нельзя'));assert.deepEqual(scenarioContextLines({}),[]);
})().catch(e=>{console.error(e);process.exit(1)});
"""
    node = shutil.which('node')
    assert node, 'Node.js is required for scenario mapping checks'
    result = subprocess.run([node, '-e', script, str(source)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
