"""Read-only, lossless JSONL export of retired monster definitions (never deletes).

Run as a module from the checkout: python -m tools.monsters.export_legacy_catalog
--out archive/data_retirement/<unique-name>. Pause writers before taking a snapshot:
PostgreSQL is repeatable-read, but PostgreSQL and MongoDB have no shared transaction.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import json
import math
from datetime import UTC, date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

TABLES = ("generated_clans", "generated_clan_members", "monster_habitat_clan_pool_entries")
COLLECTION = "generated_monster_actors"


def encode_cell(value: Any) -> dict[str, Any]:
    """Tag the whole SQL cell, leaving JSON objects free of reserved-key collisions."""
    for cls, label in ((datetime, "datetime"), (date, "date"), (time, "time")):
        if isinstance(value, cls):
            return {"type": label, "value": value.isoformat()}
    if isinstance(value, UUID):
        return {"type": "uuid", "value": str(value)}
    if isinstance(value, Decimal):
        return {"type": "decimal", "value": str(value)}
    if isinstance(value, (bytes, memoryview)):
        return {"type": "bytes", "value": base64.b64encode(bytes(value)).decode("ascii")}
    if isinstance(value, float) and not math.isfinite(value):
        return {"type": "float", "value": repr(value)}
    # allow_nan=False rejects non-JSON nested values rather than silently losing them.
    json.dumps(value, allow_nan=False)
    return {"type": "json", "value": value}


def decode_cell(cell: dict[str, Any]) -> Any:
    decoders = {
        "datetime": datetime.fromisoformat, "date": date.fromisoformat,
        "time": time.fromisoformat, "uuid": UUID, "decimal": Decimal,
        "bytes": base64.b64decode, "float": float, "json": lambda value: value,
    }
    return decoders[cell["type"]](cell["value"])


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def file_record(root: Path, path: Path, count: int) -> dict[str, Any]:
    return {"path": path.relative_to(root).as_posix(), "count": count,
            "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def actor_filter(rows: list[dict[str, Any]], clan_ids: list[str]) -> dict[str, Any]:
    """Only documents linked to exported SQL identities; never an unrestricted find."""
    keys = sorted({str(row["mongo_actor_key"]) for row in rows if row.get("mongo_actor_key")})
    members = sorted({str(row["id"]) for row in rows})
    pointers = sorted({str(row["mongo_document_id"]) for row in rows if row.get("mongo_document_id")})
    return {"$or": [{"mongo_actor_key": {"$in": keys}}, {"member_id": {"$in": members}},
                    {"clan_id": {"$in": clan_ids}}, {"_id": {"$in": pointers}}]}


def collect_assets(value: Any, *, source: str, pointer: str = "") -> list[dict[str, str]]:
    result = []
    if isinstance(value, dict):
        for key, item in value.items():
            result.extend(collect_assets(item, source=source, pointer=f"{pointer}/{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            result.extend(collect_assets(item, source=source, pointer=f"{pointer}/{index}"))
    elif isinstance(value, str) and value.startswith(("https://", "http://", "s3://", "/static/")):
        result.append({"source": source, "field": pointer, "reference": value})
    return result


def validate_archive(root: Path) -> dict[str, Any]:
    """Verify completed manifest, byte hashes, JSON readability and typed SQL cells."""
    if (root / ".partial").exists():
        raise ValueError("Archive is incomplete (.partial exists)")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("format_version") != 1 or manifest.get("status") != "complete":
        raise ValueError("Unsupported or incomplete archive")
    for entry in manifest["files"]:
        path = (root / entry["path"]).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("Archive file escapes root")
        actual = file_record(root.resolve(), path, entry["count"])
        if actual != entry:
            raise ValueError(f"Archive checksum/size mismatch: {entry['path']}")
        if path.suffix == ".jsonl":
            count = 0
            for line in path.read_text(encoding="utf-8").splitlines():
                payload = json.loads(line)
                if entry["path"].startswith("postgres/"):
                    for cell in payload.values():
                        decode_cell(cell)
                else:
                    from bson import json_util
                    json_util.loads(line)
                count += 1
            if count != entry["count"]:
                raise ValueError(f"Archive row count mismatch: {entry['path']}")
        else:
            json.loads(path.read_text(encoding="utf-8"))
    return manifest


def _reflect(connection: Any) -> tuple[Any, dict[str, Any], list[dict[str, Any]]]:
    from sqlalchemy import MetaData, inspect

    metadata = MetaData()
    metadata.reflect(bind=connection, schema="public", only=list(TABLES))
    inspector = inspect(connection)
    dependencies = []
    for table_name in inspector.get_table_names(schema="public"):
        for fk in inspector.get_foreign_keys(table_name, schema="public"):
            if fk["referred_table"] in TABLES and table_name not in TABLES:
                dependencies.append({"table": table_name, "constraint": fk["name"],
                                     "columns": fk["constrained_columns"],
                                     "target_table": fk["referred_table"],
                                     "target_columns": fk["referred_columns"],
                                     "options": fk.get("options", {})})
    schema = {}
    for name in TABLES:
        schema[name] = {
            "columns": [{"name": column.name, "sql_type": str(column.type),
                         "nullable": column.nullable, "primary_key": column.primary_key}
                        for column in metadata.tables[f"public.{name}"].columns],
            "foreign_keys": inspector.get_foreign_keys(name, schema="public"),
            "unique_constraints": inspector.get_unique_constraints(name, schema="public"),
        }
    return metadata, schema, dependencies


async def export_archive(root: Path) -> dict[str, Any]:
    from bson import json_util
    from sqlalchemy import select, text
    from sqlalchemy.ext.asyncio import create_async_engine

    from src.backend.config.settings import settings
    from src.backend.infrastructure.mongo.client import MongoClientProvider

    # mkdir(exist_ok=False) prevents overwriting even an incomplete prior export.
    root.mkdir(parents=True, exist_ok=False)
    marker = root / ".partial"
    marker.write_text("Incomplete export. Do not use for deletion or restoration.\n", encoding="utf-8")
    (root / "postgres").mkdir()
    (root / "mongo").mkdir()
    engine = create_async_engine(settings.database_url, echo=False)
    provider = MongoClientProvider()
    files, assets, sql_rows = [], [], {}
    try:
        async with engine.connect() as raw:
            connection = await raw.execution_options(isolation_level="REPEATABLE READ")
            async with connection.begin():
                await connection.execute(text("SET TRANSACTION READ ONLY"))
                metadata, schema, dependencies = await connection.run_sync(_reflect)
                for name in TABLES:
                    table = metadata.tables[f"public.{name}"]
                    result = await connection.execute(select(table).order_by(*table.primary_key.columns))
                    rows = [dict(row) for row in result.mappings()]
                    sql_rows[name] = rows
                    path = root / "postgres" / f"{name}.jsonl"
                    with path.open("x", encoding="utf-8", newline="\n") as stream:
                        for row in rows:
                            stream.write(_json({key: encode_cell(value) for key, value in row.items()}) + "\n")
                            assets.extend(collect_assets(row, source=f"postgres.{name}:{row.get('id')}"))
                    files.append(file_record(root, path, len(rows)))
        write_json(root / "postgres/schema.json", schema)
        files.append(file_record(root, root / "postgres/schema.json", len(TABLES)))
        query = actor_filter(sql_rows["generated_clan_members"],
                             [str(row["id"]) for row in sql_rows["generated_clans"]])
        path = root / "mongo" / f"{COLLECTION}.jsonl"
        found_keys, document_count = set(), 0
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            async for document in provider.database()[COLLECTION].find(query).sort("_id", 1):
                stream.write(json_util.dumps(document, json_options=json_util.CANONICAL_JSON_OPTIONS,
                                            ensure_ascii=False, sort_keys=True) + "\n")
                document_count += 1
                found_keys.add(document.get("mongo_actor_key"))
                assets.extend(collect_assets(document, source=f"mongo.{COLLECTION}:{document['_id']}"))
        files.append(file_record(root, path, document_count))
        missing = sorted({row["mongo_actor_key"] for row in sql_rows["generated_clan_members"]} - found_keys)
        if missing:
            write_json(root / "missing-actor-keys.json", missing)
            raise ValueError(f"Missing {len(missing)} linked actor documents; archive remains incomplete")
        write_json(root / "assets-manifest.json", {"mode": "references_only", "binaries_copied": False,
                                                 "references": assets})
        files.append(file_record(root, root / "assets-manifest.json", len(assets)))
        manifest = {
            "format_version": 1, "status": "complete", "content_kind": "legacy_monster_catalog",
            "exported_at": datetime.now(UTC).isoformat(), "files": files,
            "sql_encoding": "tagged-cells-v1", "mongo_encoding": "canonical-extended-json",
            "scope": {"postgres_tables": list(TABLES), "mongo_collection": COLLECTION,
                      "mongo_filter": query},
            "external_foreign_keys": dependencies, "missing_actor_keys": missing,
            "database_mutations": False,
            "deletion_performed": False,
            "retirement_status": "copied_only_active_consumers_remain",
            "consistency": "SQL repeatable-read; Mongo separate read; pause writers before export",
            "excluded": ["AI generation tasks", "runtime actors", "combat", "rifts", "asset binaries"],
        }
        write_json(root / "manifest.json", manifest)
        marker.unlink()
        try:
            validate_archive(root)
        except Exception:
            marker.write_text("Export validation failed.\n", encoding="utf-8")
            raise
        return manifest
    finally:
        await provider.close()
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", "--output", type=Path, required=True)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    manifest = validate_archive(args.out) if args.validate_only else asyncio.run(export_archive(args.out))
    print(_json({"status": manifest["status"], "files": manifest["files"],
                 "missing_actor_count": len(manifest["missing_actor_keys"]),
                 "external_foreign_keys": manifest["external_foreign_keys"]}))


if __name__ == "__main__":
    main()
