from uuid import UUID

import pytest
from bson import ObjectId, json_util
from tools.monsters.export_legacy_catalog import (
    COLLECTION,
    TABLES,
    encode_cell,
    file_record,
    write_json,
)
from tools.monsters.retire_legacy_catalog import (
    assert_same_records,
    check_external_dependencies,
    ensure_unique_ids,
    load_snapshot,
    retire_archive,
    validate_local_targets,
)


@pytest.mark.parametrize("host,mongo_host", [("127.0.0.1", "localhost"), ("postgres", "mongo")])
def test_only_known_local_databases_allowed(host, mongo_host):
    validate_local_targets(f"postgresql+asyncpg://{host}:5432/tbmmorpg_game",
                           f"mongodb://{mongo_host}:27017", "tbmmorpg_analytics")


@pytest.mark.parametrize("sql,mongo,database", [
    ("postgresql://prod.example/tbmmorpg_game", "mongodb://localhost", "tbmmorpg_analytics"),
    ("postgresql://localhost/other", "mongodb://localhost", "tbmmorpg_analytics"),
    ("postgresql://localhost/tbmmorpg_game", "mongodb://remote", "tbmmorpg_analytics"),
    ("postgresql://localhost/tbmmorpg_game", "mongodb://localhost", "other"),
    ("postgresql://localhost/tbmmorpg_game", "mongodb://localhost,remote", "tbmmorpg_analytics"),
    ("postgresql://localhost/tbmmorpg_game", "mongodb://localhost/?replicaSet=remote", "tbmmorpg_analytics"),
])
def test_refuses_remote_and_other_targets_without_echoing_credentials(sql, mongo, database):
    with pytest.raises(ValueError) as exc:
        validate_local_targets(sql, mongo, database)
    assert "u:p" not in str(exc.value)


def test_full_sql_contents_and_typed_values_compared_not_only_ids():
    identity = UUID(int=1)
    original = [{"id": identity, "stats": {"hp": 10}}]
    assert_same_records(original, list(reversed(original)), "test")
    for changed in ([{"id": identity, "stats": {"hp": 11}}],
                    [{"id": str(identity), "stats": {"hp": 10}}], []):
        with pytest.raises(ValueError, match="differs"):
            assert_same_records(original, changed, "test")


def test_mongo_comparison_is_canonical_full_document_and_order_independent():
    identity = ObjectId()
    original = [{"_id": identity, "snapshots": {"t1": {"gear_score": 10}}}]
    assert_same_records(original, [{"snapshots": {"t1": {"gear_score": 10}}, "_id": identity}],
                        "actors", mongo=True)
    with pytest.raises(ValueError, match="differs"):
        assert_same_records(original, [{"_id": identity, "snapshots": {}}], "actors", mongo=True)


@pytest.mark.parametrize("records", [[{}], [{"id": "a"}, {"id": "a"}]])
def test_missing_duplicate_ids_block_deletion(records):
    with pytest.raises(ValueError):
        ensure_unique_ids(records, "test")


def test_load_archive_requires_all_scope_files_and_checks_hashes(tmp_path):
    (tmp_path / "postgres").mkdir()
    (tmp_path / "mongo").mkdir()
    files = []
    for table in TABLES:
        path = tmp_path / "postgres" / f"{table}.jsonl"
        path.write_text(__import__("json").dumps({"id": encode_cell(UUID(int=1))}) + "\n", encoding="utf-8")
        files.append(file_record(tmp_path, path, 1))
    path = tmp_path / "mongo" / f"{COLLECTION}.jsonl"
    path.write_text(json_util.dumps({"_id": ObjectId()}) + "\n", encoding="utf-8")
    files.append(file_record(tmp_path, path, 1))
    manifest = {"format_version": 1, "status": "complete", "content_kind": "legacy_monster_catalog",
                "scope": {"postgres_tables": list(TABLES), "mongo_collection": COLLECTION}, "files": files}
    write_json(tmp_path / "manifest.json", manifest)
    rows, documents = load_snapshot(tmp_path)
    assert len(rows) == 3 and len(documents) == 1
    path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="checksum"):
        load_snapshot(tmp_path)


@pytest.mark.asyncio
async def test_apply_without_explicit_local_confirmation_opens_no_databases(tmp_path):
    with pytest.raises(ValueError, match="confirm-local"):
        await retire_archive(tmp_path, apply=True)


@pytest.mark.asyncio
async def test_external_fk_rows_refuse_cleanup():
    class Result:
        def scalar_one(self):
            return 1

    class Preparer:
        def quote(self, name):
            return name

    class Dialect:
        identifier_preparer = Preparer()

    class Connection:
        dialect = Dialect()

        async def execute(self, query):
            assert "generated_monsters" in str(query)
            return Result()

    with pytest.raises(ValueError, match="generated_monsters"):
        await check_external_dependencies(Connection(), [{"table": "generated_monsters"}])
