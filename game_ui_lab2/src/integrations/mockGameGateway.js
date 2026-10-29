import {createModifierSheet} from './modifierSheet.js';
import character from '../mocks/character.json' with {type:'json'};
import inventory from '../mocks/inventory.json' with {type:'json'};
const clone=value=>structuredClone(value);
// Provisional presentation snapshots: not claimed as the production API schema.
export function createMockGameGateway(){return {
 async loadCharacter(){const model=clone(character);model.modifier_sheet=createModifierSheet(model.modifier_values,{name:model.name,context:model.modifier_context});return model;},
 async loadInventory(){return clone(inventory);},
 async action(){return {ok:false,notice:'Макет: серверное действие не отправлено. Предметы не изменены.'};},
};}
