import asyncio
import copy


class MemoryFinalizationJournal:
    """Flow double only; real PostgreSQL locking is tested separately."""

    def __init__(self):
        self.rows = {}
        self.locks = {}
        self.fail_checkpoint = set()

    async def load(self, combat_id):
        row = self.rows.get(combat_id)
        return copy.deepcopy(row["payload"]) if row else None

    async def freeze(self, payload):
        row = self.rows.setdefault(payload["combat_id"], {"payload": copy.deepcopy(payload), "completed": []})
        return copy.deepcopy(row["payload"])

    async def run_step(self, combat_id, step, action):
        async with self.locks.setdefault(combat_id, asyncio.Lock()):
            row = self.rows[combat_id]
            if step in row["completed"]:
                return
            await action(copy.deepcopy(row["payload"]))
            if step in self.fail_checkpoint:
                self.fail_checkpoint.remove(step)
                raise RuntimeError("injected crash after applying step")
            row["completed"].append(step)

    async def block_retired(self, combat_id):
        self.rows[combat_id]["status"] = "blocked_retired"

    async def pending(self, *, after_combat_id=""):
        return [
            {"session_id": key, "winner": value["payload"]["winner_team"]}
            for key, value in self.rows.items()
            if "complete" not in value["completed"]
            and value.get("status") != "blocked_retired"
            and key > after_combat_id
        ]

    async def pending_archives(self, *, after_combat_id=""):
        return []
