from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from src.backend.features.character import events
from src.backend.features.character.integrations.character_state_integrator import CharacterStateIntegrator
from src.backend.features.character.runtime.gear_score import GEAR_SCORE_VERSION
from src.backend.features.character.schemas.session import CharacterSessionDocumentDTO, CharacterSessionMetricsDTO
from src.backend.features.combat.services.view_service import CombatViewService


def document():
    return CharacterSessionDocumentDTO(
        char_id=7,
        user_id=uuid4(),
        bio={"name": "GS test", "gender": "male", "created_at": datetime.now(UTC)},
        updated_at=datetime.now(UTC),
    )


def calculator():
    return Mock(calculate_breakdown_from_active_character=Mock(return_value={"total": 35.789, "offense": 12.345}))


def test_session_metrics_preserve_fractional_gear_score():
    metric = CharacterSessionMetricsDTO.model_validate({"gear_score": 35.789, "gear_score_version": GEAR_SCORE_VERSION})
    assert metric.model_dump()["gear_score"] == 35.789
    assert metric.model_dump()["gear_score_version"] == GEAR_SCORE_VERSION


def test_combat_card_preserves_fractional_character_metric():
    card = CombatViewService()._map_actor(
        "7", {"meta": {"hp": 10}, "metrics": {"gear_score": 35.789}}, is_target=False, dead_actor_ids=set()
    )
    assert card.gear_score == 35.789


@pytest.mark.asyncio
async def test_naked_character_receives_attribute_gear_score_without_inventory_repository():
    doc = document()
    service = CharacterStateIntegrator(
        character_sessions=Mock(), character_repo=Mock(), skill_repo=Mock(), gear_score_calculator=calculator()
    )
    await service._hydrate_items_and_gear_score(doc)
    assert doc.metrics.gear_score == 35.789
    assert doc.metrics.gear_score_version == GEAR_SCORE_VERSION


@pytest.mark.asyncio
async def test_existing_session_with_invalidated_metric_recalculates_from_current_inputs():
    doc = document()
    sessions = Mock(get_session=AsyncMock(return_value=doc.model_dump(mode="json")), update_session=AsyncMock())
    service = CharacterStateIntegrator(
        character_sessions=sessions,
        character_repo=Mock(get_by_id_and_user_id=AsyncMock(return_value=SimpleNamespace())),
        skill_repo=Mock(),
        gear_score_calculator=calculator(),
    )
    service._repair_session_from_persisted_actor_state = Mock(side_effect=lambda value, _: (value, False))
    result = await service._get_or_initialize_session_doc(doc.user_id, 7)
    assert result.metrics.gear_score == 35.789
    assert sessions.update_session.await_args.args[1]["metrics"]["gear_score_version"] == GEAR_SCORE_VERSION
    service.gear_score_calculator.calculate_breakdown_from_active_character.assert_called_once()


@pytest.mark.asyncio
async def test_recalculation_event_transports_and_stores_exact_new_scale(monkeypatch):
    sessions = Mock(get_sessions_batch=AsyncMock(return_value={7: document().model_dump(mode="json")}))
    sessions.patch_fields = AsyncMock()
    producer = Mock(publish=AsyncMock(), publish_reply=AsyncMock())
    monkeypatch.setattr(events, "_app", SimpleNamespace(state=SimpleNamespace(character_sessions=sessions, events=producer)))
    monkeypatch.setattr(events, "CharacterGearScoreCalculator", calculator)
    await events.on_gear_score_recalculate_requested({"char_ids": [7, 8], "correlation_id": "gs-test"})
    patch = sessions.patch_fields.await_args.args[1]
    assert patch["$.metrics.gear_score"] == 35.789
    assert patch["$.metrics.gear_score_version"] == GEAR_SCORE_VERSION
    response = producer.publish_reply.await_args.args[1]
    assert response["gear_scores"] == {"7": 35.789}
    assert response["failed"] == [8]
