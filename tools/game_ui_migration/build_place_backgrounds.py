"""Build painted place backgrounds for the 1600px-wide logical game viewport."""
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]


def build():
    source = ROOT / 'assets/game_client_sources/places/originals'
    target = ROOT / 'assets/game_client_sources/places/painted'
    originals = json.loads((source / 'source-manifest.json').read_text(encoding='utf-8'))
    images = []
    for record in originals['images']:
        master = source / record['file']
        content = master.read_bytes()
        if hashlib.sha256(content).hexdigest() != record['sha256']:
            raise ValueError(f'Master changed: {master}')
        name = master.stem + '.webp'
        with Image.open(master) as opened:
            image = ImageOps.exif_transpose(opened).convert('RGB')
            width = min(1920, image.width)
            height = round(image.height * width / image.width)
            image = image.resize((width, height), Image.Resampling.LANCZOS)
            image.save(target / name, 'WEBP', quality=86, method=6)
        webp = (target / name).read_bytes()
        images.append({'file': name, 'width': width, 'height': height, 'bytes': len(webp),
                       'sha256': hashlib.sha256(webp).hexdigest(), 'source_master': record['file'],
                       'source_sha256': record['sha256'], 'source_bytes': record['bytes']})
    manifest = {'style': 'painted-medieval-fantasy', 'runtime_width': 1920,
                'webp_quality': 86, 'webp_method': 6, 'images': images}
    (target / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    before, after = sum(i['source_bytes'] for i in images), sum(i['bytes'] for i in images)
    print(f'{before} JPEG bytes -> {after} WebP bytes ({100 * (1 - after / before):.1f}% smaller)')
    for record in images:
        print(record['file'], record['width'], record['height'], record['bytes'])


if __name__ == '__main__':
    build()
