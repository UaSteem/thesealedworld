"""Offline shared authoring and read-only catalog integrity."""

from pathlib import Path

import pytest
from tools.monsters import prepare_goblin_equipment as tool


def test_generated_definitions_match_all_saved_shared_items():
    generated = tool.build_definitions()
    index = tool.read_data(tool.DEFAULT_OUTPUT / "prepared/index.py")
    assert len(generated) == len(index) == 138
    for key, module in index.items():
        assert generated[key] == tool.read_data(tool.DEFAULT_OUTPUT / "prepared" / (module.replace(".", "/") + ".py"))


def test_saved_catalog_validates_without_generation(monkeypatch):
    def forbidden():
        raise AssertionError("Validation must not generate items")

    monkeypatch.setattr(tool, "build_definitions", forbidden)
    assert tool.validate(tool.DEFAULT_OUTPUT) == {"definitions": 138, "sets": 72, "assignments": 282}


def test_writing_never_overwrites_and_validation_detects_edits(tmp_path):
    output = tmp_path / "shared"
    counts = tool.write_prepared(output)
    assert tool.validate(output) == counts
    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        tool.write_prepared(output)
    index = tool.read_data(output / "prepared/index.py")
    first = output / "prepared" / (next(iter(index.values())).replace(".", "/") + ".py")
    first.write_text(first.read_text(encoding="utf-8") + "\n# edited\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Manual changes detected"):
        tool.validate(output)


def test_read_data_does_not_execute_python(tmp_path):
    path = tmp_path / "unsafe.py"
    path.write_text("DATA = __import__('os').getcwd()", encoding="utf-8")
    with pytest.raises(ValueError):
        tool.read_data(path)


def test_existing_output_refuses_before_generation(tmp_path, monkeypatch):
    (tmp_path / "prepared").mkdir()

    def forbidden():
        raise AssertionError("Must not generate over existing edits")

    monkeypatch.setattr(tool, "build_definitions", forbidden)
    with pytest.raises(FileExistsError):
        tool.write_prepared(Path(tmp_path))
