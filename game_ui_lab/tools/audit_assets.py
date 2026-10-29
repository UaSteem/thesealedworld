"""Inventory observed client dependencies; never resize or rewrite image assets.

Run from the repository: python -m game_ui_lab.tools.audit_assets
Browser observations must be refreshed when the UI changes its dependencies.
"""
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

from PIL import Image

from game_ui_lab.app import LAB_ROOT, resolve_asset


def build_inventory():
    observations = json.loads((LAB_ROOT / 'docs/asset-render-observations.json').read_text())
    observed = {item['url'] for item in observations['requests']}
    lazy_observations = LAB_ROOT / 'docs/inventory-load-observations.json'
    lazy = set()
    if lazy_observations.is_file():
        lazy = {item['url'] for item in json.loads(lazy_observations.read_text())['requests']
                if item.get('phase') == 'inventory-first-open'} - observed
    urls = observed | lazy
    pending = [url for url in urls if url.endswith('.css')]
    while pending:
        url = pending.pop()
        source = resolve_asset(url)
        if source is None:
            raise FileNotFoundError(url)
        for match in re.finditer(r'url\(\s*[\'"]?([^\)\'"\s]+)', source.read_text(encoding='utf-8')):
            reference = match.group(1)
            if reference.startswith(('data:', 'http:', 'https:', '#')):
                continue
            dependency = unquote(urlsplit(urljoin(url, reference)).path)
            if dependency not in urls:
                urls.add(dependency)
                if dependency.endswith('.css'):
                    pending.append(dependency)
    records = []
    for url in sorted(urls):
        source = resolve_asset(url)
        if source is None:
            raise FileNotFoundError(url)
        record = {
            'path': source.relative_to(LAB_ROOT.parent).as_posix(), 'url': url,
            'bytes': source.stat().st_size,
            'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'observed_on_initial_load': url in observed,
            'observed_on_inventory_open': url in lazy,
        }
        if source.suffix.lower() in ('.png', '.webp', '.jpg'):
            with Image.open(source) as image:
                record.update(width=image.width, height=image.height,
                              decoded_rgba_bytes=image.width * image.height * 4)
        records.append(record)
    return {
        'interface': 'game_ui_lab', 'status': 'development-inventory-not-production-loader',
        'entry_url': 'http://127.0.0.1:8879/',
        'measured_file_requests': len(observed),
        'measured_file_bytes': sum(row['bytes'] for row in records if row['observed_on_initial_load']),
        'observed_lazy_file_requests': len(lazy),
        'observed_lazy_file_bytes': sum(row['bytes'] for row in records if row['observed_on_inventory_open']),
        'files': records,
    }


if __name__ == '__main__':
    inventory = build_inventory()
    target = LAB_ROOT / 'asset-manifest.json'
    target.write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"{inventory['measured_file_requests']} observed files, "
          f"{inventory['measured_file_bytes']} bytes; {len(inventory['files'])} with CSS dependencies")
