import assert from 'node:assert/strict';
import test from 'node:test';
import {createNavigation} from './navigation.js';
import {createGameClient} from './gameClient.js';
import {createMockGameGateway} from '../integrations/mockGameGateway.js';
test('management returns to its origin; battle forbids all management screens',()=>{
 const nav=createNavigation();nav.go('arena');nav.go('character');nav.go('quests');nav.close();assert.equal(nav.screen.value,'arena');
 nav.go('combat');nav.close();assert.equal(nav.screen.value,'combat');for(const id of ['character','quests','settings']){assert.equal(nav.go(id),false);assert.equal(nav.screen.value,'combat');}
 nav.go('rift');assert.equal(nav.go('character'),true);
});
test('game use case propagates failures and keeps mock snapshots isolated',async()=>{
 const gateway=createMockGameGateway(),client=createGameClient(gateway),first=await client.load();first.character.hp=0;
 assert.notEqual((await client.load()).character.hp,0);
 const notice=await client.action({action:'equip'});assert.equal(notice.ok,false);
 const failed=createGameClient({loadCharacter:()=>Promise.reject(new Error('offline')),loadInventory:async()=>({})});
 await assert.rejects(failed.load(),/offline/);
});
