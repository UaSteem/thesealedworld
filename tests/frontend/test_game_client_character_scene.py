"""Character presentation uses provided actor/panel values without game simulation."""
import shutil
import subprocess
from pathlib import Path


def test_character_scene_rows_preserve_authoritative_values():
    script = r"""
const fs=require('fs'),assert=require('node:assert/strict');
(async()=>{
const {characterRows,createCharacterScene}=await import('data:text/javascript;base64,'+fs.readFileSync(process.argv[1]).toString('base64'));
const model={bio:{name:'Real'},attributes:{strength:0,agility:9,unknown:false,missing:null},skills:{skill_swords:{xp:.33}},active_quest:'quest-real-9',panel:{widgets:[
{type:'attribute_grid',visible:true,data:{groups:[{title:'Тело',items:[{label:'Сила',value:0},{label:'Ловкость',value:9},{label:'Неизвестно',value:null},{label:'Флаг',value:false}]}]}},
{type:'skill_groups',visible:true,data:{groups:[{title:'Оружие',items:[{label:'Мечи',value:'33%'},{label:'Нет значения'}]}]}}
]}};
const before=JSON.stringify(model);
assert.deepEqual(characterRows(model,'attributes'),[{group:'Тело',label:'Сила',value:'0'},{group:'Тело',label:'Ловкость',value:'9'}]);
assert.deepEqual(characterRows(model,'skills'),[{group:'Оружие',label:'Мечи',value:'33%'}]);
assert.equal(JSON.stringify(model),before);
assert.deepEqual(characterRows({},'attributes'),[]);assert.deepEqual(characterRows({},'skills'),[]);
assert.deepEqual(characterRows({attributes:{strength:0,unknown:false,missing:null}},'attributes'),[{group:'Характеристики',label:'Сила',value:'0'}]);
assert.deepEqual(characterRows({skills:{swords:{xp:.33},archery:null}},'skills'),[]);
assert(characterRows(model,'builds').some(r=>r.unavailable));
assert(characterRows(model,'quests').some(r=>r.label==='Текущий квест'&&r.value==='quest-real-9'));
assert(characterRows({},'quests').every(r=>r.unavailable));
assert.equal(typeof createCharacterScene,'function');
})().catch(e=>{console.error(e);process.exit(1)});
"""
    node = shutil.which('node')
    assert node
    result = subprocess.run([node, '-e', script, str(Path('src/frontend/static/js/game/client/character-scene.js').resolve())], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
