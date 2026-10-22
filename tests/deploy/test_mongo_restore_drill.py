"""Opt-in synthetic MongoDB archive drill without application data or networking."""

import json
import os
import subprocess
import time
from uuid import uuid4

import pytest

pytestmark = [
    pytest.mark.external,
    pytest.mark.skipif(os.getenv("RUN_MONGO_RESTORE_DRILL") != "1", reason="Opt-in disposable MongoDB drill"),
]


def test_mongo_archive_restores_bson_documents_and_indexes():
    container = f"tbmm-mongo-restore-drill-{uuid4().hex}"
    source, target = "drill_source", "drill_restored"

    def docker(*args: str, input_text: str | None = None, check: bool = True):
        return subprocess.run(
            ["docker", *args],
            input=input_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
            check=check,
        )

    def mongo(statement: str):
        return docker("exec", container, "mongosh", "--quiet", "--norc", "--eval", statement).stdout.strip()

    def snapshot(database: str):
        return mongo(
            f"const d=db.getSiblingDB('{database}'); "
            "print(EJSON.stringify({names:d.getCollectionNames().sort(), "
            "docs:d.documents.find().sort({_id:1}).toArray(), "
            "indexes:d.documents.getIndexes().sort((a,b)=>a.name.localeCompare(b.name))}, "
            "{relaxed:false}));"
        )

    try:
        docker(
            "run",
            "--detach",
            "--pull=never",
            "--name",
            container,
            "--network=none",
            "--tmpfs",
            "/data/db:rw",
            "--tmpfs",
            "/data/configdb:rw",
            "mongo:8",
            "--bind_ip",
            "127.0.0.1",
        )
        for _ in range(60):
            ready = docker(
                "exec",
                container,
                "mongosh",
                "--quiet",
                "--norc",
                "--eval",
                "quit(db.adminCommand({ping:1}).ok===1?0:1)",
                check=False,
            )
            if ready.returncode == 0:
                break
            time.sleep(0.5)
        else:
            pytest.fail("Disposable MongoDB did not become ready")

        mongo(
            f"const d=db.getSiblingDB('{source}'); "
            "d.documents.insertMany(["
            "{_id:ObjectId('0123456789abcdef01234567'), tenant:'a', code:'雪', label:'почта ✓', "
            "nested:{values:[null,{enabled:true}]}, createdAt:ISODate('2026-01-02T03:04:05.678Z'), "
            "amount:Long('9007199254740993')},"
            "{_id:ObjectId('0123456789abcdef01234568'), tenant:'b', code:'雪', label:null, "
            "nested:{values:[]}, createdAt:ISODate('2026-02-03T04:05:06.789Z'), amount:Long('-7')}]);"
            "d.documents.createIndex({tenant:1,code:1},{name:'tenant_code_unique',unique:true});"
            "d.documents.createIndex({expiresAt:1},{name:'expiry',expireAfterSeconds:3600});"
        )
        before = snapshot(source)
        first = json.loads(before)["docs"][0]
        assert first["_id"] == {"$oid": "0123456789abcdef01234567"}
        assert first["amount"] == {"$numberLong": "9007199254740993"}
        assert first["createdAt"] == {"$date": {"$numberLong": "1767323045678"}}
        assert first["label"] == "почта ✓"
        assert first["nested"] == {"values": [None, {"enabled": True}]}
        assert target not in mongo(
            "print(JSON.stringify(db.adminCommand({listDatabases:1,nameOnly:true}).databases.map(x=>x.name)))"
        )
        docker("exec", container, "mongodump", f"--db={source}", "--archive=/tmp/synthetic.archive", "--gzip")
        docker(
            "exec",
            container,
            "mongorestore",
            "--archive=/tmp/synthetic.archive",
            "--gzip",
            "--stopOnError",
            f"--nsInclude={source}.*",
            f"--nsFrom={source}.*",
            f"--nsTo={target}.*",
        )
        assert snapshot(target) == before
        duplicate = mongo(
            f"const d=db.getSiblingDB('{target}'); "
            "let rejected=false; try {d.documents.insertOne({tenant:'a',code:'雪'});} "
            "catch(e) {if(e.code!==11000) throw e; rejected=true;} "
            "if(!rejected) throw new Error('Restored unique index accepted duplicate'); print('rejected');"
        )
        assert duplicate == "rejected"
        assert snapshot(target) == before
        assert snapshot(source) == before
        assert (
            mongo(
                f"print(db.getSiblingDB('{target}').documents.getIndexes().find(x=>x.name==='expiry').expireAfterSeconds)"
            )
            == "3600"
        )

        docker(
            "exec", "-i", container, "sh", "-c", "cat > /tmp/corrupt.archive", input_text="deliberately corrupt archive"
        )
        failed = docker(
            "exec",
            container,
            "mongorestore",
            "--archive=/tmp/corrupt.archive",
            "--stopOnError",
            f"--nsFrom={source}.*",
            "--nsTo=drill_corrupt_target.*",
            check=False,
        )
        assert failed.returncode != 0, "Corrupt archive must not be reported as restored"
        assert mongo("print(db.getSiblingDB('drill_corrupt_target').getCollectionNames().length)") == "0"
        assert snapshot(source) == before
        assert snapshot(target) == before
    finally:
        docker("rm", "--force", "--volumes", container, check=False)
        remaining = docker("ps", "--all", "--quiet", "--filter", f"name=^/{container}$")
        assert not remaining.stdout.strip(), "Disposable drill container cleanup failed"
