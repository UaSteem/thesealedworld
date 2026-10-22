import asyncio
import copy
from unittest.mock import AsyncMock

import pytest

from src.backend.features.combat.runtime.services.experience_finalizer import CombatExperienceFinalizer
from src.backend.features.combat.workers.tasks.finalization_recovery_task import combat_finalization_recovery_task
from src.backend.features.combat.workers.tasks.victory_finalizer_task import victory_finalizer_task
from tests.backend.features.combat.finalization_fakes import MemoryFinalizationJournal
from tests.backend.features.combat.test_experience_finalizer import FakeCombatDataService
from tests.backend.features.combat.test_victory_finalizer_task import FakeCharacterSessions, FakeEvents, FakeQueue
from tests.backend.features.combat.test_victory_finalizer_task import FakeCombatDataService as FullData


@pytest.mark.asyncio
async def test_combat_progression_carries_identity_to_owning_operation():
    class Recorder:
        def __init__(self):
            self.applied = set()
            self.total = 0

        async def apply_progress(self, char_id, rewards, *, combat_id):
            key = (combat_id, char_id)
            if key not in self.applied:
                self.applied.add(key)
                self.total += sum(rewards.values())
            return True

    recorder = Recorder()
    finalizer = CombatExperienceFinalizer()
    await finalizer.finalize(FakeCombatDataService(), "combat-1", "team_1", progression_recorder=recorder)
    first = recorder.total
    await finalizer.finalize(FakeCombatDataService(), "combat-1", "team_1", progression_recorder=recorder)
    assert first > 0
    assert recorder.total == first


@pytest.mark.asyncio
async def test_finalizer_failure_is_visible_to_worker():
    class FailingData:
        async def get_meta(self, *args):
            raise RuntimeError("injected failure")

    with pytest.raises(RuntimeError):
        await victory_finalizer_task(
            {"combat_data_service": FailingData(), "combat_finalization_journal": MemoryFinalizationJournal()},
            {"session_id": "combat-1"},
        )


class DeduplicatingSessions(FakeCharacterSessions):
    def __init__(self):
        super().__init__()
        self.receipts = set()
        self.combat_id = "combat-1"

    async def get_session(self, char_id):
        return {"sessions": {"combat_id": self.combat_id}}

    async def apply_skill_progress(self, char_id, rewards, *, combat_id=None):
        if (char_id, combat_id) not in self.receipts:
            self.receipts.add((char_id, combat_id))
            self.progress.append((char_id, copy.deepcopy(rewards)))


def context(journal):
    return {
        "combat_data_service": FullData(),
        "combat_finalization_journal": journal,
        "character_sessions": DeduplicatingSessions(),
        "redis": FakeQueue(),
        "events": FakeEvents(),
        "combat_progression_checkpoint": AsyncMock(),
    }


@pytest.mark.asyncio
async def test_sequential_and_concurrent_delivery_apply_progression_once():
    journal = MemoryFinalizationJournal()
    ctx = context(journal)
    payload = {"session_id": "combat-1", "winner": "team_1"}
    await asyncio.gather(*(victory_finalizer_task(ctx, payload) for _ in range(5)))
    await victory_finalizer_task(ctx, payload)
    assert len(ctx["character_sessions"].progress) == 1
    assert journal.rows["combat-1"]["completed"][-1] == "complete"
    assert len(ctx["redis"].jobs) == 1


@pytest.mark.asyncio
async def test_crash_after_progression_replays_frozen_rewards_without_runtime():
    journal = MemoryFinalizationJournal()
    journal.fail_checkpoint.add("progression")
    ctx = context(journal)
    payload = {"session_id": "combat-1", "winner": "team_1"}
    with pytest.raises(RuntimeError, match="injected crash"):
        await victory_finalizer_task(ctx, payload)
    frozen = copy.deepcopy(journal.rows["combat-1"]["payload"])
    assert await journal.pending() == [payload]
    ctx["combat_data_service"].get_meta = AsyncMock(side_effect=AssertionError("runtime must not be read"))
    await combat_finalization_recovery_task(ctx)
    assert ctx["redis"].jobs == [("victory_finalizer_task", payload)]
    await victory_finalizer_task(ctx, {**payload, "winner": "changed-untrusted-retry"})
    assert len(ctx["character_sessions"].progress) == 1
    assert journal.rows["combat-1"]["payload"] == frozen
    assert await journal.pending() == []


@pytest.mark.asyncio
async def test_failed_durability_remains_pending_and_recovers():
    journal = MemoryFinalizationJournal()
    ctx = context(journal)
    ctx["events"].request = AsyncMock(return_value={"status": "error"})
    payload = {"session_id": "combat-1", "winner": "team_1"}
    with pytest.raises(RuntimeError, match="durability request failed"):
        await victory_finalizer_task(ctx, payload)
    assert "durability" not in journal.rows["combat-1"]["completed"]
    ctx["events"].request = AsyncMock(return_value={"status": "ok"})
    ctx["character_sessions"].combat_id = "combat-2"
    await victory_finalizer_task(ctx, payload)
    assert ctx["character_sessions"].patches == []
    assert len(ctx["character_sessions"].progress) == 1


@pytest.mark.asyncio
async def test_enqueue_uncertain_response_retries_without_resetting_later_session():
    journal = MemoryFinalizationJournal()
    journal.fail_checkpoint.add("complete")
    ctx = context(journal)
    payload = {"session_id": "combat-1", "winner": "team_1"}
    with pytest.raises(RuntimeError, match="injected crash"):
        await victory_finalizer_task(ctx, payload)
    sessions = ctx["character_sessions"]
    before = copy.deepcopy((sessions.updated, sessions.patches))
    sessions.combat_id = "combat-2"
    await victory_finalizer_task(ctx, payload)
    assert (sessions.updated, sessions.patches) == before
    assert len(sessions.progress) == 1


@pytest.mark.asyncio
async def test_attachment_retries_corpse_after_death_pending_clears_combat(monkeypatch):
    import importlib
    from contextlib import asynccontextmanager
    from types import SimpleNamespace

    from src.backend.features.expedition.service import ExpeditionService

    module = importlib.import_module("src.backend.features.combat.workers.tasks.victory_finalizer_task")
    document = {"state": "combat", "sessions": {"combat_id": "combat-1"}}

    class Sessions:
        async def get_session(self, char_id):
            return copy.deepcopy(document)

        async def patch_fields(self, char_id, updates):
            for path, value in updates.items():
                parts = path.removeprefix("$.").split(".")
                target = document
                for part in parts[:-1]:
                    target = target.setdefault(part, {})
                target[parts[-1]] = value

        mark_dirty = AsyncMock()

    sessions = Sessions()
    expedition = SimpleNamespace(status="active", run_id="run-1", corpse_id=None)
    service = ExpeditionService(session=object(), character_sessions=sessions)
    service.get_active_run = AsyncMock(return_value=expedition)
    service.refresh_session_risk = AsyncMock()
    service._maybe_commit = AsyncMock()
    service.finalize_death_corpse = AsyncMock(side_effect=[RuntimeError("corpse unavailable"), {"status": "finalized"}])

    @asynccontextmanager
    async def db():
        yield object()

    monkeypatch.setattr(module, "get_session_context", db)
    monkeypatch.setattr(module, "ExpeditionService", lambda **kwargs: service)
    monkeypatch.setattr(module.CombatPostBattleRouter, "build_outcomes", AsyncMock(return_value={}))
    facts = {"combat_id": "combat-1", "participant_char_ids": [7], "actors": {"7": {"char_id": 7, "is_dead": True}}}
    with pytest.raises(RuntimeError, match="corpse unavailable"):
        await module._attach_finalization_to_active_sessions({"character_sessions": sessions}, "combat-1", facts)
    assert document["sessions"]["combat_id"] is None
    assert expedition.status == "death_pending"
    await module._attach_finalization_to_active_sessions({"character_sessions": sessions}, "combat-1", facts)
    assert service.finalize_death_corpse.await_count == 2


@pytest.mark.asyncio
async def test_attachment_retries_dirty_checkpoint_after_result_patch(monkeypatch):
    import importlib

    module = importlib.import_module("src.backend.features.combat.workers.tasks.victory_finalizer_task")
    document = {"state": "combat", "sessions": {"combat_id": "combat-1"}}

    class Sessions:
        async def get_session(self, char_id):
            return copy.deepcopy(document)

        async def patch_fields(self, char_id, updates):
            document["state"] = updates["$.state"]
            document["sessions"].update({"combat_id": None, "combat_finalization_id": "combat-1"})

        mark_dirty = AsyncMock(side_effect=[RuntimeError("checkpoint unavailable"), None])

    sessions = Sessions()
    monkeypatch.setattr(module.CombatPostBattleRouter, "build_outcomes", AsyncMock(return_value={}))
    facts = {"combat_id": "combat-1", "participant_char_ids": [7], "actors": {}}
    with pytest.raises(RuntimeError):
        await module._attach_finalization_to_active_sessions({"character_sessions": sessions}, "combat-1", facts)
    await module._attach_finalization_to_active_sessions({"character_sessions": sessions}, "combat-1", facts)
    assert sessions.mark_dirty.await_count == 2
