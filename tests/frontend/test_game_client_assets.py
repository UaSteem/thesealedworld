"""Exercise texture leases and failed-load cleanup without a game server."""
import shutil
import subprocess
from pathlib import Path


def test_asset_leases_and_retry():
    source = Path('src/frontend/static/js/game/client/assets.js').resolve()
    script = r"""
const fs=require('fs'),assert=require('node:assert/strict');
(async()=>{
const {createAssetManager,validateCatalog}=await import('data:text/javascript;base64,'+fs.readFileSync(process.argv[1]).toString('base64'));
const catalog={schema_version:1,assets:[{key:'ui-test',group:'ui',url:'/static/images/game-client/a.123456789abc.png',width:8,height:4,bytes:12,sha256:'a'.repeat(64),frames:{slot:[0,0,4,4]}}]};
assert.throws(()=>validateCatalog({...catalog,assets:[{...catalog.assets[0],frames:{bad:[7,0,4,4]}}]}));
assert.throws(()=>validateCatalog({...catalog,assets:[{...catalog.assets[0],url:'/ui-static/dev.png'}]}));
let loads=0,closed=0,fail=false;
const cache=new Map(),textures={exists:k=>cache.has(k),addImage:(k,img)=>{const t={has:()=>false,add:()=>{}};cache.set(k,t);return t},remove:k=>cache.delete(k)};
const manager=createAssetManager({textures,catalog,loadImage:async()=>{loads++;await Promise.resolve();if(fail)throw Error('network');return {width:8,height:4,close:()=>closed++}}});
const [a,b]=await Promise.all([manager.acquire('ui'),manager.acquire('ui')]);assert.equal(loads,1);assert.equal(manager.inspect().residentBytes,128);
a.release();assert.equal(cache.size,1);a.release();assert.equal(cache.size,1);b.release();assert.equal(cache.size,0);assert.equal(closed,1);
fail=true;await assert.rejects(manager.acquire('ui'),/network/);assert.equal(manager.inspect().residentBytes,0);assert.equal(cache.size,0);
fail=false;const c=await manager.acquire('ui');assert.equal(loads,3);c.release();assert.equal(cache.size,0);
await assert.rejects(manager.acquire('missing'),/Unknown/);

let rejectedClose=0;
const broken=createAssetManager({catalog,textures:{exists:()=>false,addImage:()=>null},loadImage:async()=>({width:8,height:4,close:()=>rejectedClose++})});
await assert.rejects(broken.acquire('ui'),/Cannot create/);assert.equal(rejectedClose,1);assert.equal(broken.inspect().textures,0);
let collisionLoads=0;
const two={...catalog,assets:[...catalog.assets,{...catalog.assets[0],key:'occupied'}]};
const collision=createAssetManager({catalog:two,textures:{exists:k=>k==='occupied'},loadImage:async()=>{collisionLoads++;throw Error('unexpected load')}});
await assert.rejects(collision.acquire('ui'),/already owned/);assert.equal(collisionLoads,0);
let finish,lateClose=0;
const late=createAssetManager({catalog,textures,loadImage:()=>new Promise(resolve=>{finish=resolve})});
const waiting=late.acquire('ui');await Promise.resolve();late.dispose();finish({width:8,height:4,close:()=>lateClose++});
await assert.rejects(waiting,/disposed/);assert.equal(lateClose,1);assert.equal(late.inspect().textures,0);
manager.dispose();await assert.rejects(manager.acquire('ui'),/disposed/);

})().catch(e=>{console.error(e);process.exit(1)});
"""
    result = subprocess.run([shutil.which('node'), '-e', script, str(source)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_runtime_catalog_matches_crops_and_hash_urls():
    import hashlib
    import json

    from PIL import Image

    root = Path('src/frontend/static/images/game-client')
    catalog = json.loads((root / 'catalog.json').read_text(encoding='utf-8'))
    assert len(catalog['assets']) == 11
    decoded = 0
    for entry in catalog['assets']:
        path = root / entry['url'].rsplit('/', 1)[1]
        content = path.read_bytes()
        assert len(content) == entry['bytes']
        assert hashlib.sha256(content).hexdigest() == entry['sha256']
        assert entry['sha256'][:12] in path.name
        with Image.open(path) as image:
            assert image.size == (entry['width'], entry['height'])
            master_path = Path('assets/game_client_sources/combat/ui') / entry['source']['master']
            assert hashlib.sha256(master_path.read_bytes()).hexdigest() == entry['source']['sha256']
            with Image.open(master_path) as master:
                x, y, w, h = entry['source']['crop']
                assert image.tobytes() == master.crop((x, y, x + w, y + h)).tobytes()
        decoded += entry['width'] * entry['height'] * 4
    assert decoded == 8_806_348


def test_shared_game_client_sources_match_provenance_manifest():
    import hashlib
    import json

    source_root = Path('assets/game_client_sources')
    manifest = json.loads((source_root / 'manifest.json').read_text(encoding='utf-8'))
    records = manifest['files']
    assert len(records) == 12
    assert len({record['path'] for record in records}) == len(records)
    for record in records:
        content = (source_root / record['path']).read_bytes()
        assert len(content) == record['bytes']
        assert hashlib.sha256(content).hexdigest() == record['sha256']
    residential = next(record for record in records if record['path'].endswith('residential-quarter.jpg'))
    assert residential['role'] == 'art_master_only'
    assert residential['runtime_copy'] is None


def test_runtime_places_match_shared_compressed_sources():
    import hashlib
    import json

    runtime_root = Path('src/frontend/static/images/game-client/places')
    manifest = json.loads((runtime_root / 'manifest.json').read_text(encoding='utf-8'))
    assert {record['file'] for record in manifest['images']} == {
        'arena-hall.webp', 'administrative-quarter.webp', 'trading-quarter.webp', 'crafting-quarter.webp',
    }
    for record in manifest['images']:
        content = (runtime_root / record['file']).read_bytes()
        shared = (Path('assets/game_client_sources/places/painted') / record['file']).read_bytes()
        assert content == shared
        assert len(content) == record['bytes']
        assert hashlib.sha256(content).hexdigest() == record['sha256']


def test_runtime_art_builders_use_shared_sources_without_labs(monkeypatch):
    import hashlib
    import json
    from io import BytesIO

    from PIL import Image
    from tools.game_ui_migration import build_runtime_places, build_ui_assets

    real_read_bytes = Path.read_bytes
    writes = {}

    def read_without_labs(path):
        assert 'game_ui_lab' not in path.parts and 'rift_lab' not in path.parts
        return real_read_bytes(path)

    def capture_bytes(path, content):
        writes[path] = content
        return len(content)

    def capture_text(path, content, *args, **kwargs):
        writes[path] = content.encode('utf-8')
        return len(content)

    monkeypatch.setattr(Path, 'read_bytes', read_without_labs)
    monkeypatch.setattr(Path, 'mkdir', lambda *args, **kwargs: None)
    monkeypatch.setattr(Path, 'write_bytes', capture_bytes)
    monkeypatch.setattr(Path, 'write_text', capture_text)
    build_ui_assets.build()
    build_runtime_places.build()

    root = Path.cwd() / 'src/frontend/static/images/game-client'
    catalog = json.loads(writes[root / 'catalog.json'])
    assert len(catalog['assets']) == 11
    for entry in catalog['assets']:
        content = writes[root / entry['url'].rsplit('/', 1)[1]]
        assert hashlib.sha256(content).hexdigest() == entry['sha256']
        with Image.open(BytesIO(content)) as image:
            assert image.size == (entry['width'], entry['height'])
    places = json.loads(writes[root / 'places/manifest.json'])
    assert len(places['images']) == 4
    for record in places['images']:
        content = writes[root / 'places' / record['file']]
        assert hashlib.sha256(content).hexdigest() == record['sha256']
    assert len(writes) == 17
