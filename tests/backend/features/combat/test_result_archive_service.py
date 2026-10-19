from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.backend.features.combat.services import result_archive_service as module
from src.backend.infrastructure.combat.models import CombatFinalization


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "winner,win,expected", [("players", True, "victory"), ("monsters", False, "defeat"), ("draw", False, "draw")]
)
async def test_sql_summary_preserves_known_solo_outcome(monkeypatch, winner, win, expected):
    row = CombatFinalization(
        combat_id="c1",
        winner_team=winner,
        player_win=win,
        participant_char_ids=[7],
        turns=8,
        battle_type="pve",
        metadata_={},
    )

    @asynccontextmanager
    async def session():
        yield object()

    monkeypatch.setattr(module, "get_session_context", session)
    monkeypatch.setattr(
        module, "CombatFinalizationRepository", lambda _: SimpleNamespace(get_by_combat_id=AsyncMock(return_value=row))
    )
    service = module.CombatResultArchiveService()
    data = await service._load_from_db(7, combat_id="c1")
    result = service.build_result_from_finalization(data, char_id=7, reason="expired", target_state="exploration")
    assert result.combat_id == "c1"
    assert result.outcome == expected
    assert result.report["last_turn"] == 8
    assert result.metadata["battle_type"] == "pve"


def test_sql_summary_never_invents_pvp_player_team():
    data = {"winner_team": "red", "participant_char_ids": [7, 8], "player_win": True}
    assert module.CombatResultArchiveService._outcome_for_actor(data, char_id=7) == "unknown"
