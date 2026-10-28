"""Immutable, explicit-scope frontend source snapshot; never moves active files."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from jinja2 import Environment, meta

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOTS = (
    'src/frontend/templates/game', 'src/frontend/game_features',
    'src/frontend/integrations/backend_api', 'src/frontend/static/js/core',
    'src/frontend/static/js/game', 'src/frontend/static/css/game',
    'src/shared/schemas', 'tests/frontend',
)
SOURCE_FILES = (
    'src/frontend/static/js/game.js', 'src/frontend/static/js/csrf.js',
    'src/frontend/static/css/game.css', 'src/frontend/static/css/theme.css',
    'src/frontend/static/css/theme_bundle.css', 'src/frontend/static/css/fonts.css',
    'src/frontend/static/css/game_bundle.css', 'src/frontend/static/css/compiler_config.json',
    'src/frontend/static/css/vendor.css',
    'src/frontend/core/static.py',
)
EXTENSIONS = {'.py', '.js', '.css', '.html', '.json', '.md'}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(['git', '-c', f'safe.directory={root.as_posix()}', *args], cwd=root).decode().strip()


def contained(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f'Path escapes root: {relative}')
    return path


def source_paths(root: Path) -> list[Path]:
    paths = {contained(root, name) for name in SOURCE_FILES if contained(root, name).is_file()}
    for name in SOURCE_ROOTS:
        paths.update(p for p in contained(root, name).rglob('*')
                     if p.is_file() and p.suffix in EXTENSIONS and '__pycache__' not in p.parts)
    paths.update(template_dependencies(root, paths))
    for path in paths:
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError(f'Symlink escapes repository: {path}')
    return sorted(paths)


def template_dependencies(root: Path, paths: set[Path]) -> set[Path]:
    """Follow literal Jinja inheritance/includes without executing templates."""
    templates = root / 'src/frontend/templates'
    environment = Environment(extensions=['jinja2.ext.do', 'jinja2.ext.loopcontrols'])
    found: set[Path] = set()
    pending = [p for p in paths if p.suffix == '.html']
    seen: set[Path] = set()
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        seen.add(path)
        ast = environment.parse(path.read_text(encoding='utf-8-sig'))
        for name in meta.find_referenced_templates(ast):
            # A variable-built name is not guessed. Runtime inventory documents
            # those call sites; the captured game template tree includes widgets.
            if name is None:
                continue
            dependency = contained(templates, name)
            if not dependency.is_file():
                raise FileNotFoundError(f'Template dependency missing: {path}: {name}')
            found.add(dependency)
            pending.append(dependency)
    return found


def snapshot(root: Path, destination: Path) -> dict:
    root = root.resolve()
    destination = destination.resolve()
    archive = (root / 'archive/game_ui_migration').resolve()
    if not destination.is_relative_to(archive) or destination == archive:
        raise ValueError('Destination must be a new child of archive/game_ui_migration')
    if destination.exists():
        raise FileExistsError('Immutable snapshot already exists')
    paths = source_paths(root)
    if not paths:
        raise ValueError('No frontend source files found')
    revision, branch = git(root, 'rev-parse', 'HEAD'), git(root, 'branch', '--show-current')
    status = git(root, 'status', '--porcelain=v1', '--untracked-files=all', '--', 'src/frontend', 'src/shared/schemas', 'tests/frontend')
    destination.mkdir(parents=True)
    entries = []
    for path in paths:
        relative = path.relative_to(root).as_posix()
        data = path.read_bytes()
        target = contained(destination / 'source', relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        if target.read_bytes() != data or path.read_bytes() != data:
            raise RuntimeError(f'Source changed during snapshot: {relative}')
        entries.append({'path': relative, 'bytes': len(data), 'sha256': digest(data)})
    # Large retained dependencies are indexed, not copied or retired. Missing/mutated
    # files must be detected before restoring this source package in the future.
    retained = []
    for name in ('src/frontend/static/images', 'src/frontend/static/fonts', 'src/frontend/static/js/vendor', 'src/frontend/static/css/vendor'):
        for path in sorted(contained(root, name).rglob('*')):
            if path.is_file():
                if not path.resolve().is_relative_to(root):
                    raise ValueError(f'Dependency escapes repository: {path}')
                data = path.read_bytes()
                retained.append({'path': path.relative_to(root).as_posix(), 'bytes': len(data), 'sha256': digest(data)})
    manifest = {'schema_version': 1, 'created_at': datetime.now(UTC).isoformat(),
                'branch': branch, 'revision': revision, 'scope': list(SOURCE_ROOTS) + list(SOURCE_FILES),
                'git_status_scoped': status.splitlines(), 'source': entries,
                'retained_dependencies': retained,
                'note': 'Source-only reference snapshot plus retained dependency index. Not a DB backup or deploy bundle. Active files remain in place.'}
    (destination / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return manifest


def verify(root: Path, destination: Path, compare_live: bool = False) -> dict:
    manifest = json.loads((destination / 'manifest.json').read_text(encoding='utf-8'))
    errors = []
    for entry in manifest['source']:
        archived = contained(destination / 'source', entry['path'])
        if not archived.is_file() or digest(archived.read_bytes()) != entry['sha256']:
            errors.append('archive:' + entry['path'])
        if compare_live:
            path = contained(root, entry['path'])
            if not path.is_file() or digest(path.read_bytes()) != entry['sha256']:
                errors.append('source:' + entry['path'])
    for entry in manifest['retained_dependencies']:
        path = contained(root, entry['path'])
        if not path.is_file() or digest(path.read_bytes()) != entry['sha256']:
            errors.append('dependency:' + entry['path'])
    return {'ok': not errors, 'archived_sources': len(manifest['source']),
            'retained_dependencies': len(manifest['retained_dependencies']), 'errors': errors}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['snapshot', 'verify'])
    parser.add_argument('destination', type=Path)
    parser.add_argument('--compare-live', action='store_true')
    args = parser.parse_args()
    if args.command == 'snapshot':
        value = snapshot(ROOT, args.destination)
        print(json.dumps({'source_files': len(value['source']), 'retained_dependencies': len(value['retained_dependencies'])}))
    else:
        value = verify(ROOT, args.destination.resolve(), args.compare_live)
        print(json.dumps(value, ensure_ascii=False))
        raise SystemExit(0 if value['ok'] else 1)
