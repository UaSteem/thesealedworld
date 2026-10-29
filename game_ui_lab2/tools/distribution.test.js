import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {join} from 'node:path';
const root=fileURLToPath(new URL('../',import.meta.url));
const local=url=>join(root,'public',url.replace(/^\//,''));
test('distribution contains every catalog image, fixture image and font without sibling repositories',()=>{
 const catalog=JSON.parse(readFileSync(join(root,'public/ui-static/game/assets/catalog.json')));
 const inventory=JSON.parse(readFileSync(join(root,'src/mocks/inventory.json')));
 const character=JSON.parse(readFileSync(join(root,'src/mocks/character.json')));
 const urls=[...catalog.assets.map(a=>a.url),character.avatar_url,...inventory.items.flatMap(i=>[i.image_url,i.thumbnail_url,i.texture_url])];
 const fonts=readFileSync(join(root,'public/static/css/fonts.css'),'utf8');
 urls.push(...[...fonts.matchAll(/url\(['"]?([^)'"\s]+)['"]?\)/g)].map(m=>m[1]));
 for(const url of urls){assert.ok(url.startsWith('/'),url);assert.ok(existsSync(local(url)),`Missing packaged resource: ${url}`);}
});
test('active rift textures match their selected 1024/512 manifest and hashes',async()=>{
 const {createHash}=await import('node:crypto');
 const base=join(root,'public/ui-static/game/assets/rift');
 const manifest=JSON.parse(readFileSync(join(base,'manifest.json')));
 for(const file of manifest.files){
  const bytes=readFileSync(join(base,file.path));assert.equal(createHash('sha256').update(bytes).digest('hex'),file.sha256);
  assert.deepEqual([bytes.readUInt32BE(16),bytes.readUInt32BE(20)],file.dimensions);
 }
});
