from datetime import UTC, date, datetime, time
from decimal import Decimal
from uuid import uuid4

import pytest
from bson import ObjectId, json_util
from tools.monsters.export_legacy_catalog import (
    actor_filter,
    collect_assets,
    decode_cell,
    encode_cell,
    file_record,
    validate_archive,
    write_json,
)


@pytest.mark.parametrize("value", [
    uuid4(), datetime(2026, 10, 15, 12, 3, 4, 999999, tzinfo=UTC), date(2026, 10, 15),
    time(12, 4, 6, 999999), Decimal("12345678901234567890.12345000"), b"\x00\xff",
    None, True, 123456789012345678901234567890, 1.25,
    {"type": "datetime", "value": "legitimate JSON, not a date", "$uuid": "not a UUID"},
    {"nested": [{"a": 1}, None, "крыса"]},
])
def test_sql_cell_roundtrip_preserves_values_and_types(value):
    result = decode_cell(encode_cell(value))
    assert type(result) is type(value)
    assert result == value
    if isinstance(value, Decimal):
        assert result.as_tuple() == value.as_tuple()


def test_unsupported_cell_fails_instead_of_silently_stringifying():
    with pytest.raises(TypeError):
        encode_cell(object())


def test_mongo_filter_is_scoped_even_when_sql_empty():
    query = actor_filter([], [])
    assert query != {}
    assert all(list(clause.values())[0] == {"$in": []} for clause in query["$or"])
    query = actor_filter([{"id": "m1", "mongo_actor_key": "actor-1", "mongo_document_id": "d1"}], ["c1"])
    assert {"mongo_actor_key": {"$in": ["actor-1"]}} in query["$or"]
    assert {"member_id": {"$in": ["m1"]}} in query["$or"]
    assert {"clan_id": {"$in": ["c1"]}} in query["$or"]


def test_asset_manifest_collects_references_without_fetching():
    assert collect_assets({"art": ["https://example.invalid/wolf.png", "/static/wolf.svg"],
                           "name": "Wolf"}, source="monster:1") == [
        {"source": "monster:1", "field": "/art/0", "reference": "https://example.invalid/wolf.png"},
        {"source": "monster:1", "field": "/art/1", "reference": "/static/wolf.svg"},
    ]


def _archive(root):
    (root / "postgres").mkdir()
    (root / "mongo").mkdir()
    sql = root / "postgres/generated_clans.jsonl"
    sql.write_text('{"id":{"type":"uuid","value":"00000000-0000-0000-0000-000000000001"}}\n',
                   encoding="utf-8")
    mongo = root / "mongo/generated_monster_actors.jsonl"
    document = {"_id": ObjectId(), "created_at": datetime(2026, 10, 15, tzinfo=UTC),
                "snapshots": {"t1": {"gear_score": 123}}}
    mongo.write_text(json_util.dumps(document, json_options=json_util.CANONICAL_JSON_OPTIONS) + "\n",
                     encoding="utf-8")
    files = [file_record(root, sql, 1), file_record(root, mongo, 1)]
    manifest = {"format_version": 1, "status": "complete", "files": files}
    write_json(root / "manifest.json", manifest)
    return manifest, sql


def test_completed_archive_validation_checks_sql_and_bson(tmp_path):
    manifest, _ = _archive(tmp_path)
    assert validate_archive(tmp_path) == manifest


def test_archive_detects_file_corruption(tmp_path):
    _, sql = _archive(tmp_path)
    sql.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="checksum/size mismatch"):
        validate_archive(tmp_path)


def test_archive_refuses_incomplete_export(tmp_path):
    _archive(tmp_path)
    (tmp_path / ".partial").write_text("interrupted", encoding="utf-8")
    with pytest.raises(ValueError, match="incomplete"):
        validate_archive(tmp_path)


def test_archive_detects_wrong_row_count(tmp_path):
    manifest, _ = _archive(tmp_path)
    manifest["files"][0]["count"] = 2
    write_json(tmp_path / "manifest.json", manifest)
    with pytest.raises(ValueError, match="row count mismatch"):
        validate_archive(tmp_path)
