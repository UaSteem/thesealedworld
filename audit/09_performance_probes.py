from __future__ import annotations

import ast

# Bounded audit probes: source methods via AST, in-memory fakes, no network.
import json
import statistics
import time
from contextlib import suppress
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


def extract_class(path, class_name, methods, env):
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8-sig"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    cls.body = [n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in methods]
    cls.bases = []
    mod = ast.Module(
        body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), cls], type_ignores=[]
    )
    exec(compile(ast.fix_missing_locations(mod), path, "exec"), env)  # nosec B102 -- trusted repository AST in local audit probe
    return env[class_name]


class FakeRedis:
    def __init__(self, n, injured):
        self.n, self.injured, self.scans, self.gets = n, injured, 0, 0

    async def scan(self, cursor=0, match=None, count=100):
        self.scans += 1
        end = min(cursor + count, self.n)
        return (end if end < self.n else 0), [str(i) for i in range(cursor, end)]

    async def get(self, key, path):
        self.gets += 1
        return [{"char_id": int(key), "state": "exploration", "vitals": {"full": not self.injured}}]


async def main():
    env = {
        "CoreDomain": SimpleNamespace(
            **{k: SimpleNamespace(value=k.lower()) for k in ["EXPLORATION", "RIFT", "SCENARIO", "LOBBY"]}
        ),
        "CharacterSessionVitalsDTO": SimpleNamespace(model_validate=lambda d: d),
        "CharacterVitalsCalculator": SimpleNamespace(_is_full=lambda d: d["full"]),
    }
    cls = extract_class(
        "src/backend/infrastructure/actor_state/managers/session.py",
        "CharacterSessionManager",
        {"scan_vitals_regen_candidates"},
        env,
    )
    for injured in (False, True):
        for n in (100, 1000, 5000):
            fake = FakeRedis(n, injured)
            obj = cls()
            obj._redis_client = lambda bound=fake: bound
            obj.redis = SimpleNamespace(json_module=fake)
            obj._first = lambda a: a[0]
            a = await obj.scan_vitals_regen_candidates(limit=100)
            b = await obj.scan_vitals_regen_candidates(limit=100)
            print(
                json.dumps(
                    {
                        "probe": "actual_scan_method_mock_validation",
                        "n": n,
                        "injured": injured,
                        "SCAN_per_pass": fake.scans // 2,
                        "GET_per_pass": fake.gets // 2,
                        "selected": len(a),
                        "repeat_same": a == b,
                    }
                ),
                flush=True,
            )

    log_cls = extract_class(
        "src/backend/infrastructure/combat/managers/session.py",
        "CombatSessionManager",
        {"get_logs_by_turn", "_merge_logs_by_turn", "_group_logs_by_turn", "_log_turn", "_turn_sort_key"},
        {"json": json},
    )
    for turns in (100, 500, 1000):
        raw = {
            str(t): json.dumps([json.dumps({"global_turn": t, "text": "x" * 100}) for _ in range(5)])
            for t in range(turns)
        }

        async def hgetall(key, snapshot=raw):
            return snapshot

        obj = log_cls()
        obj._client = lambda: SimpleNamespace(hgetall=hgetall)
        obj.log_key = lambda s: s
        samples = []
        for _ in range(11):
            start = time.perf_counter()
            result = await obj._merge_logs_by_turn("synthetic", [{"global_turn": turns, "text": "x" * 100}])
            samples.append((time.perf_counter() - start) * 1000)
        print(
            json.dumps(
                {
                    "probe": "actual_log_methods_fake_redis",
                    "turns": turns,
                    "median_ms_10_warm": round(statistics.median(samples[1:]), 3),
                    "json_value_bytes": sum(len(v.encode()) for v in result.values()),
                }
            ),
            flush=True,
        )

    calls = []
    doc = {"sync_dirty": {"dirty": True, "targets": {"character": True}, "generation": 1}}

    async def get_session(cid):
        return doc

    async def clear_dirty(cid, **kw):
        doc["sync_dirty"] = None

    async def record(name, *args, **kw):
        calls.append(name)
        return {"state": "exploration", "location_id": "x"} if name == "character" else None

    def fn(name):
        async def call(*args, **kw):
            return await record(name, *args, **kw)

        return call

    dto = SimpleNamespace(
        char_id=7,
        state="exploration",
        location=SimpleNamespace(current="x"),
        attributes=SimpleNamespace(model_dump=lambda **kw: {"strength": 8}),
        progression=SimpleNamespace(free_xp=0),
        symbiote=SimpleNamespace(model_dump=lambda **kw: {}),
    )
    integrator = extract_class(
        "src/backend/features/character/integrations/system_integrator.py",
        "CharacterSystemIntegrator",
        {"__init__", "sync_active_session", "_dirty_targets", "_dirty_generation"},
        {"CharacterSessionDocumentDTO": SimpleNamespace(model_validate=lambda d: dto)},
    )
    obj = integrator(
        character_sessions=SimpleNamespace(get_session=get_session, clear_dirty=clear_dirty),
        character_repo=SimpleNamespace(sync_active_session_snapshot=fn("character")),
        attributes_repo=SimpleNamespace(upsert_attributes=fn("attributes")),
        skill_repo=None,
        progression_repo=SimpleNamespace(set_free_xp=fn("progression")),
        symbiote_repo=SimpleNamespace(upsert_from_session=fn("symbiote")),
    )

    async def sync_skills(dto):
        calls.append("skills")
        return []

    obj._sync_skills = sync_skills
    await obj.sync_active_session(7)
    print(json.dumps({"probe": "actual_sync_method_fakes", "dirty_target_character": list(calls)}), flush=True)
    calls.clear()
    await obj.sync_active_session(7)
    print(json.dumps({"probe": "actual_sync_method_fakes", "clean_repeat": list(calls)}), flush=True)

    ws_cls = extract_class(
        "src/backend/chat/services/connection_manager.py", "ChatConnectionManager", {"broadcast_topic"}, {"json": json}
    )
    ws_calls = []

    class Gate:
        def __await__(self):
            yield "blocked_first_socket"

    class Sink:
        def __init__(self, name, block=False):
            self.name, self.block = name, block

        async def send_text(self, data):
            ws_calls.append(self.name + "_start")
            if self.block:
                await Gate()
            ws_calls.append(self.name + "_end")

    obj = ws_cls()
    obj._by_topic = {"x": [Sink("slow", True), Sink("fast")]}
    co = obj.broadcast_topic("x", {"text": "probe"})
    token = co.send(None)
    print(
        json.dumps({"probe": "actual_broadcast_mock_gate", "yield": token, "calls_before_release": list(ws_calls)}),
        flush=True,
    )
    with suppress(StopIteration):
        co.send(None)
    print(json.dumps({"probe": "actual_broadcast_mock_gate", "calls_after_release": ws_calls}), flush=True)


if __name__ == "__main__":
    # All awaitables are immediate in-memory fakes; no event loop or sockets.
    with suppress(StopIteration):
        main().send(None)
