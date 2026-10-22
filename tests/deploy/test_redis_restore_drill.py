"""Opt-in synthetic Redis Stack RDB restore into a new isolated process."""

import json
import os
import subprocess
import time
from uuid import uuid4

import pytest

pytestmark = [
    pytest.mark.external,
    pytest.mark.skipif(os.getenv("RUN_REDIS_RESTORE_DRILL") != "1", reason="Opt-in disposable Redis RDB drill"),
]


def test_redis_rdb_restores_types_stream_group_and_expiry(tmp_path):
    prefix = f"tbmm-redis-restore-drill-{uuid4().hex}"
    source, restored, corrupt = (f"{prefix}-{role}" for role in ("source", "restored", "corrupt"))
    image = "redis/redis-stack-server:7.2.0-v14"
    volumes = [f"{prefix}-good", f"{prefix}-bad"]
    writer = f"{prefix}-writer"
    archive = tmp_path / "dump.rdb"

    def docker(*args: str, check: bool = True):
        return subprocess.run(
            ["docker", *args], capture_output=True, text=True, encoding="utf-8", timeout=30, check=check
        )

    def cli(container: str, *args: str):
        result = docker("exec", container, "redis-cli", "--json", *args)
        assert not result.stderr.strip(), result.stderr
        return json.loads(result.stdout)

    def start(container: str, volume: str):
        docker(
            "run",
            "--detach",
            "--pull=never",
            "--name",
            container,
            "--network=none",
            "--mount",
            f"type=volume,source={volume},target=/data",
            "--env",
            "REDIS_ARGS=--save '' --appendonly no --dir /data --dbfilename dump.rdb",
            image,
        )

    def ready(container: str):
        for _ in range(60):
            probe = docker("exec", container, "redis-cli", "PING", check=False)
            if probe.returncode == 0 and probe.stdout.strip() == "PONG":
                assert cli(container, "JSON.SET", "probe", "$", '{"ready":true}') == "OK"
                assert cli(container, "JSON.GET", "probe") == '{"ready":true}'
                assert cli(container, "DEL", "probe") == 1
                return
            time.sleep(0.2)
        pytest.fail("Disposable Redis Stack did not become ready")

    def snapshot(container: str):
        return {
            "string": cli(container, "GET", "string"),
            "hash": cli(container, "HGETALL", "hash"),
            "set": sorted(cli(container, "SMEMBERS", "set")),
            "list": cli(container, "LRANGE", "list", "0", "-1"),
            "zset": cli(container, "ZRANGE", "zset", "0", "-1", "WITHSCORES"),
            "json": cli(container, "JSON.GET", "document"),
            "stream": cli(container, "XRANGE", "events", "-", "+"),
            "groups": cli(container, "XINFO", "GROUPS", "events"),
            # Elapsed pending delivery time intentionally excluded.
            "pending": [
                [row[0], row[1], row[3]] for row in cli(container, "XPENDING", "events", "workers", "-", "+", "10")
            ],
        }

    try:
        for volume in volumes:
            docker("volume", "create", volume)
        start(source, volumes[0])
        ready(source)
        assert cli(source, "SET", "string", "почта ✓") == "OK"
        cli(source, "HSET", "hash", "one", "1", "two", "雪")
        cli(source, "SADD", "set", "b", "a")
        cli(source, "RPUSH", "list", "first", "second")
        cli(source, "ZADD", "zset", "1.5", "a", "-2", "b")
        cli(source, "JSON.SET", "document", "$", '{"nested":{"values":[null,true,7]},"label":"雪"}')
        cli(source, "XADD", "events", "1-0", "type", "synthetic-one")
        cli(source, "XADD", "events", "2-0", "type", "synthetic-two")
        cli(source, "XGROUP", "CREATE", "events", "workers", "0-0")
        cli(source, "XREADGROUP", "GROUP", "workers", "consumer-a", "COUNT", "1", "STREAMS", "events", ">")
        before = snapshot(source)
        assert before["pending"] == [["1-0", "consumer-a", 1]]
        now = cli(source, "TIME")
        now_ms = int(now[0]) * 1000 + int(now[1]) // 1000
        deadline, expiry = now_ms + 120000, now_ms + 3000
        cli(source, "SET", "ttl", "keep-until-original-deadline")
        cli(source, "PEXPIREAT", "ttl", str(deadline))
        cli(source, "SET", "expired", "must-not-return")
        cli(source, "PEXPIREAT", "expired", str(expiry))
        assert cli(source, "PTTL", "expired") > 0
        assert cli(source, "SAVE") == "OK"
        assert cli(source, "PTTL", "expired") > 0, "Short-lived key must be live in the saved snapshot"
        # Freeze the exact SAVE artifact before source shutdown can rewrite it.
        docker("cp", f"{source}:/data/dump.rdb", str(archive))
        assert archive.read_bytes().startswith(b"REDIS")
        docker("stop", source)
        docker("cp", str(archive), f"{source}:/data/dump.rdb")
        time.sleep(3.1)
        start(restored, volumes[0])
        ready(restored)
        assert snapshot(restored) == before
        assert cli(restored, "GET", "ttl") == "keep-until-original-deadline"
        assert cli(restored, "PEXPIRETIME", "ttl") == deadline
        assert cli(restored, "EXISTS", "expired") == 0

        # Independent volume and process: an invalid RDB must not boot empty.
        docker(
            "run",
            "--rm",
            "--name",
            writer,
            "--pull=never",
            "--network=none",
            "--mount",
            f"type=volume,source={volumes[1]},target=/data",
            "--entrypoint",
            "sh",
            image,
            "-c",
            "printf 'deliberately corrupt RDB' > /data/dump.rdb",
        )
        start(corrupt, volumes[1])
        for _ in range(60):
            state = json.loads(docker("inspect", "--format", "{{json .State}}", corrupt).stdout)
            if not state["Running"]:
                break
            time.sleep(0.2)
        else:
            pytest.fail("Redis with corrupt RDB did not fail closed")
        assert state["ExitCode"] != 0
        probe = docker("exec", corrupt, "redis-cli", "PING", check=False)
        assert probe.returncode != 0 and probe.stdout.strip() != "PONG"
        logs = docker("logs", corrupt)
        assert "Wrong signature trying to load DB from file" in logs.stdout + logs.stderr
        assert "Fatal error loading the DB" in logs.stdout + logs.stderr
        assert snapshot(restored) == before
    finally:
        for container in (source, restored, corrupt, writer):
            docker("rm", "--force", "--volumes", container, check=False)
            assert not docker("ps", "--all", "--quiet", "--filter", f"name=^/{container}$").stdout.strip()
        for volume in volumes:
            docker("volume", "rm", volume, check=False)
            assert docker("volume", "inspect", volume, check=False).returncode != 0
        archive.unlink(missing_ok=True)
