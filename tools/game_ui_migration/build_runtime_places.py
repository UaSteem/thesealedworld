"""Publish approved compressed place art, never the large working masters."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NAMES = ('arena-hall', 'administrative-quarter', 'trading-quarter', 'crafting-quarter')


def build():
    source = ROOT / 'assets/game_client_sources/places/painted'
    target = ROOT / 'src/frontend/static/images/game-client/places'
    target.mkdir(parents=True, exist_ok=True)
    records = []
    for name in NAMES:
        filename = name + '.webp'
        content = (source / filename).read_bytes()
        (target / filename).write_bytes(content)
        records.append({'file': filename, 'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()})
    (target / 'manifest.json').write_text(json.dumps({'images': records}, indent=2) + '\n', encoding='utf-8')
    return records


if __name__ == '__main__':
    print(json.dumps(build(), indent=2))
