import pytest
from tools.game_ui_migration import baseline


@pytest.fixture
def captured(tmp_path, monkeypatch):
    source = tmp_path / 'src/frontend/templates/game/session.html'
    source.parent.mkdir(parents=True)
    source.write_bytes(b'original source\r\n')
    image = tmp_path / 'src/frontend/static/images/city.webp'
    image.parent.mkdir(parents=True)
    image.write_bytes(b'retained asset')
    monkeypatch.setattr(baseline, 'git', lambda *_: 'test-reference')
    destination = tmp_path / 'archive/game_ui_migration/stage-0'
    manifest = baseline.snapshot(tmp_path, destination)
    return tmp_path, destination, source, image, manifest


def test_snapshot_keeps_active_bytes_and_includes_uncommitted_source(captured):
    root, destination, source, image, manifest = captured
    assert source.read_bytes() == b'original source\r\n'
    assert (destination / 'source' / source.relative_to(root)).read_bytes() == source.read_bytes()
    assert len(manifest['source']) == 1
    assert len(manifest['retained_dependencies']) == 1
    assert not (destination / 'source' / image.relative_to(root)).exists()
    assert baseline.verify(root, destination, compare_live=True)['ok']


def test_existing_snapshot_cannot_be_overwritten(captured):
    root, destination, *_ = captured
    before = (destination / 'manifest.json').read_bytes()
    with pytest.raises(FileExistsError):
        baseline.snapshot(root, destination)
    assert (destination / 'manifest.json').read_bytes() == before


def test_live_changes_do_not_destroy_archived_reference(captured):
    root, destination, source, *_ = captured
    source.write_bytes(b'new implementation')
    assert baseline.verify(root, destination)['ok']
    assert not baseline.verify(root, destination, compare_live=True)['ok']


def test_corrupt_archive_and_missing_dependency_are_detected(captured):
    root, destination, source, image, _ = captured
    (destination / 'source' / source.relative_to(root)).write_bytes(b'corrupt')
    image.unlink()
    result = baseline.verify(root, destination)
    assert not result['ok']
    assert len(result['errors']) == 2


def test_destination_and_manifest_paths_cannot_escape_roots(tmp_path):
    with pytest.raises(ValueError):
        baseline.snapshot(tmp_path, tmp_path / 'src/accidental-archive')
    with pytest.raises(ValueError):
        baseline.contained(tmp_path, '../outside')


def test_transitive_shared_template_is_captured_without_rendering(tmp_path):
    templates = tmp_path / 'src/frontend/templates'
    (templates / 'game').mkdir(parents=True)
    (templates / 'shared').mkdir()
    main = templates / 'game/main.html'
    main.write_text('{% include "shared/chat.html" %}', encoding='utf-8')
    chat = templates / 'shared/chat.html'
    chat.write_text('{% include "shared/csrf.html" %}', encoding='utf-8')
    csrf = templates / 'shared/csrf.html'
    csrf.write_text('{{ csrf_token }}', encoding='utf-8')
    assert baseline.template_dependencies(tmp_path, {main}) == {chat, csrf}


def test_missing_literal_template_is_not_silently_omitted(tmp_path):
    main = tmp_path / 'src/frontend/templates/game/main.html'
    main.parent.mkdir(parents=True)
    main.write_text('{% include "shared/missing.html" %}', encoding='utf-8')
    with pytest.raises(FileNotFoundError):
        baseline.template_dependencies(tmp_path, {main})
