"""Retire only an exactly archived LOCAL legacy monster catalog; dry-run by default.

No TRUNCATE, CASCADE, Redis cleanup or other game data deletion. SQL and Mongo
cannot share a transaction: a separate receipt records partial failures. Pause
all legacy writers before applying. A receipt is never proof of a restorable DB.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4

from tools.monsters.export_legacy_catalog import (
    COLLECTION,
    TABLES,
    _json,
    _reflect,
    actor_filter,
    decode_cell,
    encode_cell,
    validate_archive,
    write_json,
)


def validate_local_targets(database_url: str, mongo_url: str, mongo_database: str) -> None:
    """Allow only this project's local development databases; never echo DSNs."""
    from sqlalchemy.engine import make_url

    sql = make_url(database_url)
    mongo = urlsplit(mongo_url)
    if (sql.drivername not in {"postgresql", "postgresql+asyncpg"}
            or sql.host not in {"localhost", "127.0.0.1", "::1", "postgres"}
            or sql.database != "tbmmorpg_game"
            or sql.port not in {None, 5432}):
        raise ValueError("Refusing non-local or unexpected PostgreSQL target")
    if (mongo.scheme != "mongodb"
            or mongo.hostname not in {"localhost", "127.0.0.1", "::1", "mongo"}
            or mongo.port not in {None, 27017}
            or mongo_database != "tbmmorpg_analytics"
            or mongo.path not in {"", "/", "/tbmmorpg_analytics"}
            or "," in mongo.netloc
            or mongo.query):
        raise ValueError("Refusing non-local or unexpected MongoDB target")


def load_snapshot(root: Path) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    from bson import json_util

    manifest = validate_archive(root)
    if (manifest.get("content_kind") != "legacy_monster_catalog"
            or manifest.get("scope", {}).get("postgres_tables") != list(TABLES)
            or manifest.get("scope", {}).get("mongo_collection") != COLLECTION):
        raise ValueError("Archive is not the expected legacy monster catalog scope")
    required = {f"postgres/{name}.jsonl" for name in TABLES} | {f"mongo/{COLLECTION}.jsonl"}
    if not required.issubset({entry["path"] for entry in manifest["files"]}):
        raise ValueError("Archive manifest omits a required data file")
    rows = {
        name: [{key: decode_cell(cell) for key, cell in json.loads(line).items()}
               for line in (root / "postgres" / f"{name}.jsonl").read_text(encoding="utf-8").splitlines()]
        for name in TABLES
    }
    documents = [json_util.loads(line) for line in
                 (root / "mongo" / f"{COLLECTION}.jsonl").read_text(encoding="utf-8").splitlines()]
    for name, records in rows.items():
        ensure_unique_ids(records, name)
    ensure_unique_ids(documents, COLLECTION, key="_id")
    return rows, documents


def ensure_unique_ids(records: list[dict[str, Any]], label: str, *, key: str = "id") -> None:
    ids = [record.get(key) for record in records]
    if any(value is None for value in ids) or len({str(value) for value in ids}) != len(ids):
        raise ValueError(f"Missing or duplicate archive identities: {label}")


def sql_fingerprint(rows: list[dict[str, Any]]) -> list[str]:
    return sorted(_json({key: encode_cell(value) for key, value in row.items()}) for row in rows)


def mongo_fingerprint(documents: list[dict[str, Any]]) -> list[str]:
    from bson import json_util

    return sorted(hashlib.sha256(json_util.dumps(
        document, json_options=json_util.CANONICAL_JSON_OPTIONS,
        ensure_ascii=False, sort_keys=True,
    ).encode("utf-8")).hexdigest() for document in documents)


def assert_same_records(expected: list[dict[str, Any]], actual: list[dict[str, Any]],
                        label: str, *, mongo: bool = False) -> None:
    fingerprint = mongo_fingerprint if mongo else sql_fingerprint
    if fingerprint(expected) != fingerprint(actual):
        raise ValueError(f"Live data differs from verified archive: {label}; take a new snapshot")


async def check_external_dependencies(connection: Any, dependencies: list[dict[str, Any]]) -> None:
    """Refuse even populated unrelated referencing tables, rather than cascading."""
    from sqlalchemy import text

    preparer = connection.dialect.identifier_preparer
    for dependency in dependencies:
        name = dependency["table"]
        result = await connection.execute(text(
            f"SELECT count(*) FROM public.{preparer.quote(name)}"
        ))
        if result.scalar_one():
            raise ValueError(f"External referencing table is not empty: {name}")


async def retire_archive(root: Path, *, apply: bool = False, confirm_local: bool = False,
                         receipt_path: Path | None = None) -> dict[str, Any]:
    if apply and not confirm_local:
        raise ValueError("--apply requires --confirm-local")
    root = root.resolve()
    sql_rows, documents = load_snapshot(root)
    from sqlalchemy import delete, func, select, text
    from sqlalchemy.ext.asyncio import create_async_engine

    from src.backend.config.settings import settings
    from src.backend.features.monsters.runtime_retirement import LEGACY_MONSTER_RUNTIME_RETIRED
    from src.backend.infrastructure.mongo.client import MongoClientProvider

    if apply and not LEGACY_MONSTER_RUNTIME_RETIRED:
        raise ValueError("Legacy monster runtime must be retired before cleanup")
    validate_local_targets(settings.database_url, settings.mongo_url, settings.mongo_database)
    receipt_path = receipt_path or root.parent.parent / "cleanup-receipts" / f"{root.name}-{uuid4().hex}.json"
    receipt_path = receipt_path.resolve()
    if receipt_path.is_relative_to(root) or receipt_path.exists():
        raise ValueError("Receipt must be a new file outside the immutable archive")
    receipt: dict[str, Any] = {
        "archive": str(root), "started_at": datetime.now(UTC).isoformat(),
        "archive_manifest_sha256": hashlib.sha256((root / "manifest.json").read_bytes()).hexdigest(),
        "apply": apply, "status": "checking", "sql_committed": False,
        "mongo_deleted": 0, "counts": {name: len(rows) for name, rows in sql_rows.items()},
        "mongo_count": len(documents),
    }
    engine = create_async_engine(settings.database_url, echo=False)
    provider = MongoClientProvider()
    try:
        async with engine.connect() as connection:
            async with connection.begin():
                # Keep SQL rows stable through comparison, deletion and commit.
                if apply:
                    await connection.execute(text("LOCK TABLE " + ", ".join(
                        f"public.{name}" for name in TABLES) + " IN EXCLUSIVE MODE"))
                metadata, _, dependencies = await connection.run_sync(_reflect)
                await check_external_dependencies(connection, dependencies)
                for name in TABLES:
                    table = metadata.tables[f"public.{name}"]
                    result = await connection.execute(select(table))
                    assert_same_records(sql_rows[name], [dict(row) for row in result.mappings()], name)
                collection = provider.database()[COLLECTION]
                query = actor_filter(sql_rows["generated_clan_members"],
                                     [str(row["id"]) for row in sql_rows["generated_clans"]])
                live_documents = [document async for document in collection.find(query)]
                assert_same_records(documents, live_documents, COLLECTION, mongo=True)
                receipt["status"] = "verified_dry_run"
                if apply:
                    receipt["status"] = "deleting"
                    receipt_path.parent.mkdir(parents=True, exist_ok=True)
                    write_json(receipt_path, receipt)
                    # Delete child SQL rows first. Mongo failures roll the SQL transaction back.
                    for name in (TABLES[2], TABLES[1], TABLES[0]):
                        table = metadata.tables[f"public.{name}"]
                        for row in sql_rows[name]:
                            result = await connection.execute(delete(table).where(table.c.id == row["id"]))
                            if result.rowcount != 1:
                                raise ValueError(f"Unexpected SQL delete count: {name}")
                    for document in documents:
                        current = await collection.find_one({"_id": document["_id"]})
                        assert_same_records([document], [current] if current else [], COLLECTION, mongo=True)
                        result = await collection.delete_one({"_id": document["_id"]})
                        if result.deleted_count != 1:
                            raise ValueError("Unexpected Mongo delete count")
                        receipt["mongo_deleted"] += 1
                        write_json(receipt_path, receipt)
                    for name in TABLES:
                        table = metadata.tables[f"public.{name}"]
                        if (await connection.execute(select(func.count()).select_from(table))).scalar_one():
                            raise ValueError(f"SQL table not empty after cleanup: {name}")
                    if await collection.count_documents(query):
                        raise ValueError("Linked Mongo actors remain after cleanup")
            if apply:
                receipt["sql_committed"] = True
                receipt["status"] = "complete"
    except Exception as exc:
        receipt["status"] = "failed_partial_mongo" if receipt["mongo_deleted"] else "failed"
        # Do not serialize database exception messages: they can contain credentials/data.
        receipt["error_type"] = type(exc).__name__
        raise
    finally:
        if apply:
            receipt["finished_at"] = datetime.now(UTC).isoformat()
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            write_json(receipt_path, receipt)
        await provider.close()
        await engine.dispose()
    if apply:
        receipt["receipt_path"] = str(receipt_path)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-local", action="store_true")
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    print(_json(asyncio.run(retire_archive(args.archive, apply=args.apply,
                                         confirm_local=args.confirm_local, receipt_path=args.receipt))))


if __name__ == "__main__":
    main()
