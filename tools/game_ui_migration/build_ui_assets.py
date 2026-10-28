"""Reproducible, pixel-preserving UI crops from shared, versioned masters."""
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SPECS = {
    'controls': ('control-zone-v3.png', {
        'frame': ('combat-control', [52, 330, 920, 350]),
        'plate': ('combat-control', [1076, 394, 920, 286]),
        'feint': ('ui-buttons', [92, 1290, 840, 106]),
        'attack': ('ui-buttons', [92, 1580, 840, 116]),
        'slot': ('ui-slot', [1216, 1216, 640, 640]),
    }),
    'inspector': ('target-inspector-v1.png', {
        'panel': ('ui-inspector', [1219, 25, 553, 975]),
        'row': ('ui-inspector', [22, 1228, 980, 125]),
        'bar': ('ui-inspector', [41, 1435, 943, 88]),
        'attack': ('combat-intents', [26, 1702, 302, 304]),
        'wait': ('combat-intents', [361, 1702, 303, 304]),
        'defend': ('combat-intents', [696, 1702, 302, 304]),
    }),
}


def build():
    destination = ROOT / 'src/frontend/static/images/game-client'
    destination.mkdir(parents=True, exist_ok=True)
    assets = []
    png_bytes = 0
    rgba_bytes = 0
    for prefix, (filename, frames) in SPECS.items():
        source = ROOT / 'assets/game_client_sources/combat/ui' / filename
        master_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        with Image.open(source) as master:
            for name, (group, (x, y, width, height)) in frames.items():
                if x + width > master.width or y + height > master.height:
                    raise ValueError(f'Crop outside master: {name}')
                from io import BytesIO
                buffer = BytesIO()
                master.crop((x, y, x + width, y + height)).save(buffer, format='PNG', optimize=True)
                content = buffer.getvalue()
                png_bytes += len(content)
                rgba_bytes += width * height * 4
                digest = hashlib.sha256(content).hexdigest()
                output = f'{prefix}-{name}.{digest[:12]}.png'
                (destination / output).write_bytes(content)
                assets.append({'key': f'ui-{prefix}-{name}', 'group': group,
                    'url': '/static/images/game-client/' + output, 'width': width, 'height': height,
                    'bytes': len(content), 'sha256': digest,
                    'source': {'master': filename, 'sha256': master_hash, 'crop': [x, y, width, height]}})
    canonical = json.dumps(assets, sort_keys=True, separators=(',', ':')).encode()
    catalog = {'schema_version': 1, 'revision': hashlib.sha256(canonical).hexdigest()[:16], 'assets': assets}
    (destination / 'catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{len(assets)} crops; {png_bytes} PNG bytes; '
          f'{rgba_bytes} decoded RGBA bytes')


if __name__ == '__main__':
    build()
